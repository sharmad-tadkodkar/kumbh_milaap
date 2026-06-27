"use client";

import { useEffect, useState } from "react";

const STEPS = [
  "Resolving last-seen location to a zone…",
  "Selecting nearest CCTV cameras (batched)…",
  "Loading the reference face…",
  "Scanning footage frame by frame…",
];

export default function Loading({ personName }) {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const t = setInterval(() => {
      setActive((a) => Math.min(a + 1, STEPS.length - 1));
    }, 1400);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="card fade-in">
      <div className="loading-wrap">
        <div className="diya">
          <span className="ripple" />
          <span className="ripple" />
          <span className="ripple" />
          <span className="flame" />
        </div>
        <p className="eyebrow">Searching</p>
        <h1 className="title" style={{ fontSize: 28 }}>
          Looking for{" "}
          <span className="accent">{personName || "your loved one"}</span>
        </h1>
        <div className="scan-line" />

        <ul className="loading-steps">
          {STEPS.map((s, i) => (
            <li
              key={i}
              className={i < active ? "done" : i === active ? "active" : ""}
            >
              <span className="mark">{i < active ? "✓" : i + 1}</span>
              {s}
            </li>
          ))}
        </ul>
        <p className="footer-note">Hold on — every camera is checked nearest-first.</p>
      </div>
    </div>
  );
}
