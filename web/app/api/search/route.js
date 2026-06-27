import { NextResponse } from "next/server";
import { spawn } from "node:child_process";
import { writeFile, mkdir } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Project root = parent of the Next.js `web/` directory.
const PROJECT_ROOT = path.resolve(process.cwd(), "..");

/**
 * Parse the stdout of search_missing_person.py.
 * Looks for the closing block:
 *   RESULT: FOUND on 1 camera(s):
 *     - Z1-C29 (zone 1, 22m from last-seen): first appears at 00:00:00.000
 */
function parseOutput(stdout) {
  const cameras = [];
  const lineRe =
    /-\s*([\w-]+)\s*\(zone\s*(\d+),\s*([\d.]+)m from last-seen\):\s*first appears at\s*([\d:.]+)/gi;
  let m;
  while ((m = lineRe.exec(stdout)) !== null) {
    cameras.push({
      id: m[1],
      zone: m[2],
      distance: Math.round(parseFloat(m[3])),
      firstAppears: m[4],
    });
  }

  const found = /RESULT:\s*FOUND/i.test(stdout) && cameras.length > 0;

  // Pull the "Checked X camera(s), skipped Y" summary if present.
  const sum = stdout.match(/Checked \d+ camera\(s\)[^\n]*/i);
  return { found, cameras, summary: sum ? sum[0] : null };
}

function demoResult(extra = {}) {
  return {
    found: true,
    demo: true,
    cameras: [
      { id: "Z1-C29", zone: "1", distance: 22, firstAppears: "00:00:00.000" },
    ],
    summary: "Checked 2 camera(s), skipped 1 (no footage).",
    ...extra,
  };
}

export async function POST(req) {
  let photoPath = null;
  try {
    const fd = await req.formData();
    const photo = fd.get("photo");
    const lat = (fd.get("lat") || "19.9837").toString();
    const lon = (fd.get("lon") || "73.7118").toString();

    if (!photo || typeof photo === "string") {
      return NextResponse.json(
        { found: false, cameras: [], error: "No photo provided." },
        { status: 400 }
      );
    }

    // Persist the uploaded photo to a temp file for the CLI to read.
    const bytes = Buffer.from(await photo.arrayBuffer());
    const tmpDir = path.join(os.tmpdir(), "milaap");
    await mkdir(tmpDir, { recursive: true });
    const safe = (photo.name || "upload.jpg").replace(/[^\w.-]/g, "_");
    photoPath = path.join(tmpDir, `${Date.now()}-${safe}`);
    await writeFile(photoPath, bytes);

    const args = [
      "search_missing_person.py",
      "--photo",
      photoPath,
      "--lat",
      lat,
      "--lon",
      lon,
      "--footage-dir",
      path.join("assets", "footage"),
    ];

    const data = await new Promise((resolve) => {
      let stdout = "";
      let stderr = "";
      let settled = false;

      const py = spawn("python3", args, { cwd: PROJECT_ROOT });

      // Safety timeout — face scanning can hang without models.
      const killer = setTimeout(() => {
        if (!settled) {
          settled = true;
          py.kill("SIGKILL");
          resolve(demoResult({ error: "Search timed out — showing sample." }));
        }
      }, 120000);

      py.stdout.on("data", (d) => (stdout += d.toString()));
      py.stderr.on("data", (d) => (stderr += d.toString()));

      py.on("error", () => {
        if (settled) return;
        settled = true;
        clearTimeout(killer);
        // python3 not installed / not runnable → demo mode
        resolve(demoResult());
      });

      py.on("close", (code) => {
        if (settled) return;
        settled = true;
        clearTimeout(killer);
        const parsed = parseOutput(stdout);
        if (parsed.cameras.length > 0 || /RESULT:/i.test(stdout)) {
          resolve({ ...parsed, raw: stdout });
        } else {
          // Backend ran but produced nothing parseable (likely missing deps).
          resolve(
            demoResult({
              error:
                stderr.trim().split("\n").slice(-1)[0] ||
                "Face engine unavailable.",
            })
          );
        }
      });
    });

    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(demoResult({ error: String(e?.message || e) }));
  }
}
