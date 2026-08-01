import { motion } from "motion/react";

export function LatticeMark({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden>
      <path
        d="M3 8 L21 8 M3 16 L21 16 M8 3 L8 21 M16 3 L16 21"
        stroke="currentColor"
        strokeWidth="1.2"
        opacity="0.55"
      />
      <path d="M3 3 L21 21 M21 3 L3 21" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

interface Strut {
  id: string;
  label: string;
  attribute: string;
  strength: number;
}

/**
 * The trellis: one strut pair per identity marker.
 * Warm amber struts = recent evidence. Muted struts = decayed evidence.
 */
export function Lattice({
  struts,
  pulsed,
}: {
  struts: Strut[];
  pulsed: string[];
}) {
  const cols = struts.length || 1;
  const cellW = 96;
  const height = 132;
  const width = cols * cellW;

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height + 26}`}
        className="h-[168px] w-full min-w-[520px]"
        role="img"
        aria-label="Identity lattice: evidence strength per marker"
      >
        {/* rails */}
        {[0, height / 2, height].map((y) => (
          <line
            key={y}
            x1={0}
            x2={width}
            y1={y}
            y2={y}
            stroke="currentColor"
            strokeOpacity={0.12}
            strokeWidth={1}
          />
        ))}
        {struts.map((s, i) => {
          const x = i * cellW;
          const isPulsed = pulsed.includes(s.id);
          const strength = Math.max(0.04, Math.min(1, s.strength));
          return (
            <g key={s.id}>
              <line
                x1={x + 6}
                y1={height}
                x2={x + cellW - 6}
                y2={0}
                stroke="currentColor"
                strokeOpacity={0.08}
                strokeWidth={1}
              />
              <line
                x1={x + cellW - 6}
                y1={height}
                x2={x + 6}
                y2={0}
                stroke="currentColor"
                strokeOpacity={0.08}
                strokeWidth={1}
              />
              <motion.line
                x1={x + 6}
                y1={height}
                x2={x + cellW - 6}
                y2={0}
                stroke="#D97706"
                strokeWidth={isPulsed ? 3 : 2}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{
                  pathLength: strength,
                  opacity: isPulsed ? 1 : 0.45 + strength * 0.5,
                }}
                transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                style={{ filter: isPulsed ? "drop-shadow(0 0 6px rgba(217, 119, 6, 0.5))" : "none" }}
              />
              <motion.line
                x1={x + cellW - 6}
                y1={height}
                x2={x + 6}
                y2={0}
                stroke="#475569"
                strokeWidth={isPulsed ? 3 : 2}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{
                  pathLength: strength * 0.85,
                  opacity: isPulsed ? 1 : 0.3 + strength * 0.4,
                }}
                transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.05 }}
              />
              <text
                x={x + cellW / 2}
                y={height + 18}
                textAnchor="middle"
                fill="#666666"
                className="font-mono text-[9px] font-medium tracking-wider"
              >
                {s.label.split(" ").slice(0, 2).join(" ").toUpperCase()}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
