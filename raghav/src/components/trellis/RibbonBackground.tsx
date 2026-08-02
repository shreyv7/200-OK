/*
 * Site-wide ambient background: soft grey / charcoal ribbons drifting
 * slowly over the white canvas. Motion is CSS-driven.
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
        style={{ filter: "blur(26px) saturate(0.2)" }}
      >
        <defs>
          <linearGradient id="ribbon-a" x1="0%" y1="0%" x2="100%" y2="20%">
            <stop offset="0%" stopColor="#111111" stopOpacity="0.22" />
            <stop offset="40%" stopColor="#3B3B3B" stopOpacity="0.16" />
            <stop offset="100%" stopColor="#707070" stopOpacity="0.12" />
          </linearGradient>
          <linearGradient id="ribbon-b" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#2A2A2A" stopOpacity="0.14" />
            <stop offset="50%" stopColor="#5A5A5A" stopOpacity="0.1" />
            <stop offset="100%" stopColor="#111111" stopOpacity="0.18" />
          </linearGradient>
          <linearGradient id="ribbon-c" x1="0%" y1="0%" x2="100%" y2="10%">
            <stop offset="0%" stopColor="#4A4A4A" stopOpacity="0.12" />
            <stop offset="50%" stopColor="#111111" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#6B6B6B" stopOpacity="0.1" />
          </linearGradient>
          <linearGradient id="ribbon-d" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#111111" stopOpacity="0.16" />
            <stop offset="50%" stopColor="#3B3B3B" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#8A8A8A" stopOpacity="0.08" />
          </linearGradient>
        </defs>

        <g className="ribbon-float ribbon-float-a">
          <path
            d="M -140 300 C 340 110, 900 30, 1580 350"
            stroke="url(#ribbon-a)"
            strokeWidth={140}
            strokeLinecap="round"
            fill="none"
            opacity={0.7}
          />
        </g>

        <g className="ribbon-float ribbon-float-b">
          <path
            d="M -140 250 C 380 180, 880 80, 1580 420"
            stroke="url(#ribbon-b)"
            strokeWidth={72}
            strokeLinecap="round"
            fill="none"
            opacity={0.55}
          />
        </g>

        <g className="ribbon-float ribbon-float-c">
          <path
            d="M -140 640 C 440 500, 900 720, 1580 540"
            stroke="url(#ribbon-c)"
            strokeWidth={110}
            strokeLinecap="round"
            fill="none"
            opacity={0.6}
          />
        </g>

        <g className="ribbon-float ribbon-float-d">
          <path
            d="M -140 900 C 480 770, 1000 950, 1580 790"
            stroke="url(#ribbon-d)"
            strokeWidth={150}
            strokeLinecap="round"
            fill="none"
            opacity={0.5}
          />
        </g>
      </svg>

      <div className="absolute inset-0 bg-white/35" />
    </div>
  );
}
