/*
 * Site-wide ambient background: iridescent metallic ribbons drifting slowly
 * over the white canvas. Motion is CSS-driven so it starts immediately and
 * doesn't depend on Framer path morphing.
 */

export function RibbonBackground() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-background"
    >
      <svg
        className="h-full w-full"
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMid slice"
        style={{ filter: "blur(22px) saturate(1.45)" }}
      >
        <defs>
          <linearGradient id="ribbon-a" x1="0%" y1="0%" x2="100%" y2="20%">
            <stop offset="0%" stopColor="#38BDF8" />
            <stop offset="35%" stopColor="#6366F1" />
            <stop offset="65%" stopColor="#E879F9" />
            <stop offset="100%" stopColor="#FB7185" />
          </linearGradient>
          <linearGradient id="ribbon-b" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#A5B4FC" />
            <stop offset="50%" stopColor="#22D3EE" />
            <stop offset="100%" stopColor="#F472B6" />
          </linearGradient>
          <linearGradient id="ribbon-c" x1="0%" y1="0%" x2="100%" y2="10%">
            <stop offset="0%" stopColor="#FBBF24" />
            <stop offset="50%" stopColor="#F472B6" />
            <stop offset="100%" stopColor="#60A5FA" />
          </linearGradient>
          <linearGradient id="ribbon-d" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#34D399" />
            <stop offset="50%" stopColor="#38BDF8" />
            <stop offset="100%" stopColor="#A78BFA" />
          </linearGradient>
        </defs>

        <g className="ribbon-float ribbon-float-a">
          <path
            d="M -140 300 C 340 110, 900 30, 1580 350"
            stroke="url(#ribbon-a)"
            strokeWidth={140}
            strokeLinecap="round"
            fill="none"
            opacity={0.55}
          />
        </g>

        <g className="ribbon-float ribbon-float-b">
          <path
            d="M -140 250 C 380 180, 880 80, 1580 420"
            stroke="url(#ribbon-b)"
            strokeWidth={72}
            strokeLinecap="round"
            fill="none"
            opacity={0.48}
          />
        </g>

        <g className="ribbon-float ribbon-float-c">
          <path
            d="M -140 640 C 440 500, 900 720, 1580 540"
            stroke="url(#ribbon-c)"
            strokeWidth={110}
            strokeLinecap="round"
            fill="none"
            opacity={0.42}
          />
        </g>

        <g className="ribbon-float ribbon-float-d">
          <path
            d="M -140 900 C 480 770, 1000 950, 1580 790"
            stroke="url(#ribbon-d)"
            strokeWidth={150}
            strokeLinecap="round"
            fill="none"
            opacity={0.4}
          />
        </g>
      </svg>

      <div className="absolute inset-0 bg-white/20" />
    </div>
  );
}
