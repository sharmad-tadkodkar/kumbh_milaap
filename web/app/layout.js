import "./globals.css";

export const metadata = {
  title: "Milaap · Kumbh 2027",
  description:
    "Milaap — reuniting families at Kumbh Mela 2027, Nashik. CCTV-powered missing person search.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="bg-rays" aria-hidden="true" />
        <div className="brandbar">
          <span className="kalash">🕉️</span>
          <b>Kumbh&nbsp;2027</b>
          <span style={{ opacity: 0.8 }}>· Nashik</span>
          <span className="tag">Milaap · मिलाप</span>
        </div>
        {children}
      </body>
    </html>
  );
}
