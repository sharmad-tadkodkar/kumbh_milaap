"use client";

/**
 * A friendly Indian figure in traditional attire performing namaste.
 * The gentle bow + bob is driven by CSS (.figure-svg in globals.css);
 * a soft glow blooms between the palms at the bottom of each bow.
 */
export default function NamasteFigure() {
  return (
    <svg
      className="figure-svg"
      viewBox="0 0 200 200"
      role="img"
      aria-label="A figure greeting you with a namaste"
    >
      <defs>
        <linearGradient id="skin" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#e8a979" />
          <stop offset="1" stopColor="#cf8d5d" />
        </linearGradient>
        <linearGradient id="kurta" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ff8c2a" />
          <stop offset="1" stopColor="#e85d04" />
        </linearGradient>
        <linearGradient id="shawl" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#ffce5c" />
          <stop offset="1" stopColor="#f9a825" />
        </linearGradient>
        <radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#ffe6a7" stopOpacity="0.9" />
          <stop offset="1" stopColor="#ffce5c" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* soft halo behind */}
      <circle cx="100" cy="84" r="70" fill="url(#halo)" opacity="0.7" />

      {/* shawl / drape over shoulders */}
      <path
        d="M58 120 Q100 96 142 120 L150 178 Q100 168 50 178 Z"
        fill="url(#shawl)"
      />
      {/* body kurta */}
      <path
        d="M66 122 Q100 104 134 122 L142 182 Q100 174 58 182 Z"
        fill="url(#kurta)"
      />
      {/* decorative neckline trim */}
      <path d="M84 110 L100 128 L116 110" fill="none" stroke="#7a1e1e" strokeWidth="3" strokeLinecap="round" />

      {/* neck */}
      <rect x="92" y="92" width="16" height="20" rx="6" fill="url(#skin)" />

      {/* head */}
      <circle cx="100" cy="74" r="26" fill="url(#skin)" />
      {/* hair */}
      <path
        d="M74 72 Q72 44 100 44 Q128 44 126 72 Q120 58 100 56 Q80 58 74 72 Z"
        fill="#2b1a12"
      />
      {/* tilak */}
      <path d="M100 52 L100 66" stroke="#c0392b" strokeWidth="3" strokeLinecap="round" />
      <circle cx="100" cy="50" r="2.4" fill="#c0392b" />
      {/* eyes */}
      <circle cx="91" cy="74" r="2.6" fill="#2b1a12" />
      <circle cx="109" cy="74" r="2.6" fill="#2b1a12" />
      {/* gentle smile */}
      <path d="M91 84 Q100 91 109 84" fill="none" stroke="#7a1e1e" strokeWidth="2.4" strokeLinecap="round" />

      {/* arms folding inward to namaste */}
      <path d="M70 126 Q78 150 96 150" fill="none" stroke="url(#kurta)" strokeWidth="14" strokeLinecap="round" />
      <path d="M130 126 Q122 150 104 150" fill="none" stroke="url(#kurta)" strokeWidth="14" strokeLinecap="round" />

      {/* glow between palms */}
      <circle className="namaste-glow" cx="100" cy="142" r="16" fill="url(#halo)" />

      {/* praying hands (pranam mudra) */}
      <g>
        <path
          d="M100 120 Q92 122 90 136 Q89 148 100 152 Z"
          fill="url(#skin)"
        />
        <path
          d="M100 120 Q108 122 110 136 Q111 148 100 152 Z"
          fill="#dd9468"
        />
        <line x1="100" y1="122" x2="100" y2="150" stroke="#b97a4e" strokeWidth="1.6" />
      </g>
    </svg>
  );
}
