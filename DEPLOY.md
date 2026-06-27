# Deploying Milaap (free) — Vercel + Render

Split architecture: the Next.js UI runs on **Vercel** (free), and the Python
face-search API runs on **Render** (free Docker web service). The browser calls
the Render API directly, so long (>60 s) face scans aren't cut off by Vercel's
serverless timeout.

```
Browser ──multipart(photo, lat, lon)──> Render  POST /api/search ──> JSON result
   ▲ served by
Vercel (Next.js UI)        NEXT_PUBLIC_API_URL → Render service URL
```

## 1. Backend → Render

The repo root has everything Render needs: `Dockerfile`, `server.py`,
`requirements-server.txt`, the footage in `assets/footage/`, `cctv_zones.json`,
and `render.yaml`. The two ONNX face models are **downloaded during the Docker
build** (they're gitignored), so nothing extra to upload.

1. Render → **New → Web Service** → connect this GitHub repo.
2. Render detects the root `Dockerfile`. Choose the **Free** instance type.
3. Deploy. First build downloads the 37 MB SFace model (~adds 10–20 s).
4. Verify: `curl https://<your-service>.onrender.com/health` → `{"ok":true}`.

## 2. Frontend → Vercel

1. Vercel → **New Project** → import this repo.
2. Set **Root Directory = `web`**.
3. Add an environment variable:
   `NEXT_PUBLIC_API_URL = https://<your-service>.onrender.com`
4. Deploy, then open the Vercel URL and run the full flow.

## Notes

- **Cold start:** Render's free tier sleeps after ~15 min idle; the first request
  after waking takes ~50 s. The in-app loading animation covers this.
- **RAM:** Render free is 512 MB — fine for single-request demo use; heavy
  concurrency may OOM.
- **Local dev:** leave `NEXT_PUBLIC_API_URL` unset and the UI uses its built-in
  `/api/search` route (which runs `python3` directly). Or run the API standalone:
  `pip install -r requirements-server.txt && uvicorn server:app --port 8000`.

## Alternative: single container on Hugging Face Spaces

If two deploys is a hassle, a single Docker container (Node + Python) on
**Hugging Face Spaces** (free, 16 GB RAM, no per-request timeout) is the simplest
one-deploy option and the best raw-resource fit for the OpenCV inference.
