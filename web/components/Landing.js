"use client";

import NamasteFigure from "./NamasteFigure";

export default function Landing({ onStart }) {
  return (
    <div className="card fade-in" style={{ textAlign: "center" }}>
      <div className="figure-wrap">
        <NamasteFigure />
        <div className="speech">Finding someone? 🙏</div>
      </div>

      <p className="eyebrow">Welcome to</p>
      <h1 className="title">
        Kumbh <span className="accent">2027</span>
      </h1>
      <p className="subtitle">
        Nashik · Trimbakeshwar — the world&apos;s largest gathering of faith.
        <br />
        If a loved one has gone missing in the crowd, <b>Milaap</b> helps bring
        them back.
      </p>

      <div style={{ marginTop: 28 }}>
        <button className="btn btn-primary" onClick={onStart}>
          <span className="pulse-dot" />
          Use Milaap
        </button>
      </div>

      <p className="footer-note">
        मिलाप · &ldquo;reunion&rdquo; — powered by zone-aware CCTV face search
      </p>
    </div>
  );
}
