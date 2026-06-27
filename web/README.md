# Milaap · Kumbh 2027 — Web UI

An attractive Next.js front-end for `search_missing_person.py`. It wraps the
CLI flow:

```bash
python3 search_missing_person.py \
    --photo assets/face2.jpeg --lat 19.9837 --lon 73.7118 \
    --footage-dir assets/footage
```

## Flow

1. **Landing** — "Welcome to Kumbh 2027" with an animated figure doing namaste.
2. The figure asks *"Finding someone?"* → **Use Milaap** button.
3. **Milaap form** — upload the missing person's photo + details (name, age,
   gender, last-seen lat/long, time, reportee name, contact).
4. **Loading** — diya/scan animation while the search runs.
5. **Result** — `RESULT: FOUND on N camera(s)` with each camera, zone, distance
   and first-appearance timestamp.
6. **Close** — returns to the landing page.

## Run

```bash
cd web
npm install
npm run dev          # http://localhost:3000
```

The `/api/search` route shells out to `python3 search_missing_person.py` in the
project root, parses its stdout, and returns structured JSON. If `python3` or
the face-recognition models aren't available, it falls back to a **demo result**
(`Z1-C29`, zone 1, 22m, `00:00:00.000`) so the UI is always demonstrable.

## Theme

Kumbh Nashik palette — saffron, marigold gold, deep maroon, and Godavari teal,
on a warm cream background, with sun-ray, diya, and lotus motifs.
