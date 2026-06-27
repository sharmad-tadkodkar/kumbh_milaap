"use client";

import { useState } from "react";
import Landing from "@/components/Landing";
import MilaapForm from "@/components/MilaapForm";
import Loading from "@/components/Loading";
import Result from "@/components/Result";

export default function Home() {
  const [step, setStep] = useState("landing"); // landing | form | loading | result
  const [person, setPerson] = useState("");
  const [result, setResult] = useState(null);

  async function handleSubmit(payload) {
    setPerson(payload.name);
    setStep("loading");

    const fd = new FormData();
    fd.append("photo", payload.file);
    fd.append("name", payload.name);
    fd.append("age", payload.age);
    fd.append("gender", payload.gender);
    fd.append("lat", payload.lat);
    fd.append("lon", payload.lon);
    fd.append("lastSeenTime", payload.lastSeenTime);
    fd.append("reportee", payload.reportee);
    fd.append("contact", payload.contact);

    const startedAt = Date.now();
    try {
      // In split deploys (Vercel frontend + Render backend) the browser calls
      // the Render API directly via NEXT_PUBLIC_API_URL — this avoids Vercel's
      // 60s function timeout on long face scans. Unset = same-origin (local dev).
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
      const res = await fetch(`${apiBase}/api/search`, {
        method: "POST",
        body: fd,
      });
      const data = await res.json();
      // keep the loading animation visible for a graceful minimum duration
      const elapsed = Date.now() - startedAt;
      const wait = Math.max(0, 2600 - elapsed);
      setTimeout(() => {
        setResult(data);
        setStep("result");
      }, wait);
    } catch (e) {
      setTimeout(() => {
        setResult({
          found: false,
          cameras: [],
          error: "Could not reach the search service.",
        });
        setStep("result");
      }, 1500);
    }
  }

  function reset() {
    setResult(null);
    setPerson("");
    setStep("landing");
  }

  return (
    <main className="shell">
      {step === "landing" && <Landing onStart={() => setStep("form")} />}
      {step === "form" && (
        <MilaapForm onSubmit={handleSubmit} onCancel={reset} />
      )}
      {step === "loading" && <Loading personName={person} />}
      {step === "result" && (
        <Result data={result} personName={person} onClose={reset} />
      )}
    </main>
  );
}
