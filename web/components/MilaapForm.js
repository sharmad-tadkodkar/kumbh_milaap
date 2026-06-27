"use client";

import { useRef, useState } from "react";

export default function MilaapForm({ onSubmit, onCancel }) {
  const [preview, setPreview] = useState(null);
  const [photoName, setPhotoName] = useState(null);
  const fileRef = useRef(null);
  const [form, setForm] = useState({
    name: "",
    age: "",
    gender: "",
    lat: "19.9837",
    lon: "73.7118",
    lastSeenTime: "",
    reportee: "",
    contact: "",
  });

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  function onFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    setPhotoName(f.name);
    setPreview(URL.createObjectURL(f));
  }

  function submit(e) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) {
      alert("Please upload a photo of the missing person.");
      return;
    }
    onSubmit({ ...form, file });
  }

  return (
    <form className="card fade-in" onSubmit={submit}>
      <p className="eyebrow">Report a missing person</p>
      <h1 className="title" style={{ fontSize: 34 }}>
        Tell us about <span className="accent">them</span>
      </h1>
      <p className="subtitle" style={{ fontSize: 15 }}>
        We&apos;ll scan the nearest cameras to the last-seen location first.
      </p>

      <div className="form-grid">
        {/* photo */}
        <label className="dropzone" htmlFor="photo">
          <div className="ph">
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={preview} alt="preview" />
            ) : (
              <span>📷</span>
            )}
          </div>
          <div className="dz-text">
            <b>{photoName || "Upload a clear face photo"}</b>
            <span>JPG / PNG — front-facing works best</span>
          </div>
          <input
            id="photo"
            ref={fileRef}
            type="file"
            accept="image/*"
            onChange={onFile}
            style={{ display: "none" }}
          />
        </label>

        <div className="field">
          <label>
            Full name <span className="req">*</span>
          </label>
          <input required value={form.name} onChange={set("name")} placeholder="e.g. Aarav Sharma" />
        </div>

        <div className="field">
          <label>Age</label>
          <input
            type="number"
            min="0"
            max="120"
            value={form.age}
            onChange={set("age")}
            placeholder="e.g. 9"
          />
        </div>

        <div className="field">
          <label>Gender</label>
          <select value={form.gender} onChange={set("gender")}>
            <option value="">Select…</option>
            <option>Male</option>
            <option>Female</option>
            <option>Other</option>
          </select>
        </div>

        <div className="field">
          <label>Last seen — time</label>
          <input type="datetime-local" value={form.lastSeenTime} onChange={set("lastSeenTime")} />
        </div>

        <div className="field">
          <label>
            Last-seen latitude <span className="req">*</span>
          </label>
          <input required value={form.lat} onChange={set("lat")} placeholder="19.9837" />
        </div>

        <div className="field">
          <label>
            Last-seen longitude <span className="req">*</span>
          </label>
          <input required value={form.lon} onChange={set("lon")} placeholder="73.7118" />
        </div>

        <div className="field full">
          <span className="hint">
            📍 Tip: the lat/long marks the zone the search starts from (e.g.
            19.9837, 73.7118 → Ramkund ghat area).
          </span>
        </div>

        <div className="field">
          <label>
            Reportee name <span className="req">*</span>
          </label>
          <input required value={form.reportee} onChange={set("reportee")} placeholder="Your name" />
        </div>

        <div className="field">
          <label>
            Contact number <span className="req">*</span>
          </label>
          <input
            required
            value={form.contact}
            onChange={set("contact")}
            placeholder="+91 …"
          />
        </div>
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          ← Back
        </button>
        <span className="spacer" />
        <button type="submit" className="btn btn-primary">
          Search footage 🔍
        </button>
      </div>
    </form>
  );
}
