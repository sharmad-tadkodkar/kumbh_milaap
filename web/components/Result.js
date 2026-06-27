"use client";

export default function Result({ data, personName, onClose }) {
  const found = data?.found && data.cameras?.length > 0;

  return (
    <div className="card fade-in">
      <span className={`result-badge ${found ? "found" : "notfound"}`}>
        <span className="dot" />
        {found ? "MATCH FOUND" : "NOT FOUND YET"}
      </span>

      {found ? (
        <>
          <h2 className="result-title">
            {personName ? `${personName} was spotted!` : "Person spotted!"}
          </h2>
          <p className="subtitle" style={{ fontSize: 15 }}>
            RESULT: FOUND on {data.cameras.length} camera(s):
          </p>

          <div className="cam-list">
            {data.cameras.map((c, i) => (
              <div
                className="cam-card"
                key={c.id}
                style={{ animationDelay: `${i * 0.08}s` }}
              >
                <div className="cam-icon">📹</div>
                <div className="cam-meta">
                  <b>{c.id}</b>
                  <div className="row">
                    Zone {c.zone} · {c.distance}m from last-seen
                  </div>
                  <span className="ts">first appears at {c.firstAppears}</span>
                </div>
              </div>
            ))}
          </div>

          {data.summary && <div className="summary-line">{data.summary}</div>}
        </>
      ) : (
        <>
          <h2 className="result-title">No match in checked footage</h2>
          <p className="subtitle" style={{ fontSize: 15 }}>
            {data?.summary ||
              "The person was not found in the cameras checked. Try widening the search or adjusting the last-seen location."}
          </p>
          {data?.error && <div className="error-box">⚠️ {data.error}</div>}
        </>
      )}

      <div className="form-actions">
        <span className="spacer" />
        <button className="btn btn-teal" onClick={onClose}>
          Close ✕
        </button>
      </div>

      {data?.demo && (
        <p className="footer-note">
          Demo mode — backend face engine unavailable, showing a sample result.
        </p>
      )}
    </div>
  );
}
