/**
 * IdentityNodeGraph — Scientific identity network visualization.
 *
 * Refined IABTM theme:
 * - Burnt Amber (#C8892B) accent particles & active rings
 * - Neutral typography (#707070)
 * - Meticulously architectural, zero glowing cyberpunk
 */
import { useEffect, useRef, useCallback } from "react";

interface NodeDef {
  id: string;
  label: string;
  x: number;
  y: number;
  confidence: number;  // 0..1 — controls ring size and brightness
  role: "core" | "input" | "output";
}

interface EdgeDef {
  from: string;
  to: string;
  weight: number;  // 0..1
}

const NODES: NodeDef[] = [
  { id: "declared",  label: "Declared Identity",   x: 0.12, y: 0.25, confidence: 0.95, role: "input"  },
  { id: "revealed",  label: "Revealed Behaviour",  x: 0.36, y: 0.78, confidence: 0.72, role: "input"  },
  { id: "stack",     label: "Today's Stack",        x: 0.64, y: 0.25, confidence: 0.88, role: "input"  },
  { id: "engine",    label: "Identity Engine",      x: 0.50, y: 0.48, confidence: 1.00, role: "core"   },
  { id: "drift",     label: "Drift Guardian",       x: 0.24, y: 0.52, confidence: 0.60, role: "output" },
  { id: "ledger",    label: "Trust Ledger",          x: 0.88, y: 0.52, confidence: 0.50, role: "output" },
];

const EDGES: EdgeDef[] = [
  { from: "declared", to: "engine",  weight: 0.90 },
  { from: "revealed", to: "engine",  weight: 0.80 },
  { from: "stack",    to: "engine",  weight: 0.85 },
  { from: "engine",   to: "drift",   weight: 0.62 },
  { from: "engine",   to: "ledger",  weight: 0.50 },
  { from: "declared", to: "drift",   weight: 0.38 },
  { from: "revealed", to: "drift",   weight: 0.70 },
  { from: "stack",    to: "ledger",  weight: 0.44 },
];

interface Particle {
  edgeIdx: number;
  t: number;
  speed: number;
  alpha: number;
  r: number;
  reverse: boolean;
}

// Engine "sweep" state — periodically the engine node activates and sends a wave outward
interface SweepState {
  active: boolean;
  t: number;        // 0..1 progress of sweep
  speed: number;    // progress per ms
}

export function IdentityNodeGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const sweepRef = useRef<SweepState>({ active: false, t: 0, speed: 0 });
  const rafRef = useRef<number>(0);
  const activeNodeRef = useRef<string | null>(null);

  const getPos = useCallback((nodeId: string, w: number, h: number) => {
    const n = NODES.find((x) => x.id === nodeId)!;
    return { x: n.x * w, y: n.y * h };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Seed particles — more on high-weight edges, bidirectional
    const particles: Particle[] = [];
    EDGES.forEach((edge, i) => {
      const count = Math.round(edge.weight * 3) + 1;
      for (let j = 0; j < count; j++) {
        particles.push({
          edgeIdx: i,
          t: j / count + Math.random() * 0.15,
          speed: 0.0005 + edge.weight * 0.0008 + Math.random() * 0.0003,
          alpha: 0.3 + edge.weight * 0.5,
          r: 1.2 + edge.weight * 0.8,
          reverse: j % 3 === 0, // 1/3 go backwards (return signals)
        });
      }
    });
    particlesRef.current = particles;

    // Schedule sweep every 18–30s
    const scheduleSweep = () => {
      const delay = 18_000 + Math.random() * 12_000;
      setTimeout(() => {
        sweepRef.current = { active: true, t: 0, speed: 0.0004 + Math.random() * 0.0002 };
        activeNodeRef.current = "engine";
        setTimeout(() => { activeNodeRef.current = null; }, 2_000);
        scheduleSweep();
      }, delay);
    };
    scheduleSweep();

    let lastTime = 0;
    let pulsePhase = 0;

    function draw(timestamp: number) {
      if (!canvas || !ctx) return;
      const dt = Math.min(timestamp - lastTime, 50);
      lastTime = timestamp;
      pulsePhase += dt * 0.0008;

      const dpr = window.devicePixelRatio || 1;
      const w = canvas.width  / dpr;
      const h = canvas.height / dpr;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.scale(dpr, dpr);

      // ── Advance sweep ──────────────────────────────────────────────
      const sweep = sweepRef.current;
      if (sweep.active) {
        sweep.t += sweep.speed * dt;
        if (sweep.t >= 1) {
          sweep.active = false;
          sweep.t = 0;
        }
      }

      // ── Draw edges ────────────────────────────────────────────────
      EDGES.forEach((edge) => {
        const from = getPos(edge.from, w, h);
        const to   = getPos(edge.to,   w, h);

        // Sweep effect: edge briefly brightens as the wave passes
        let edgeBoost = 0;
        if (sweep.active) {
          const centerX = from.x + (to.x - from.x) * 0.5;
          const centerY = from.y + (to.y - from.y) * 0.5;
          const enginePos = getPos("engine", w, h);
          const distToEngine = Math.hypot(centerX - enginePos.x, centerY - enginePos.y);
          const sweepRadius = sweep.t * Math.max(w, h) * 0.9;
          const rippleWidth = 60;
          const diff = Math.abs(distToEngine - sweepRadius);
          if (diff < rippleWidth) {
            edgeBoost = (1 - diff / rippleWidth) * 0.15;
          }
        }

        const baseAlpha = 0.04 + edge.weight * 0.06;
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.strokeStyle = `rgba(17,17,17,${baseAlpha + edgeBoost})`;
        ctx.lineWidth = 0.75;
        ctx.stroke();
      });

      // ── Draw particles ─────────────────────────────────────────────
      particlesRef.current.forEach((p) => {
        const edge = EDGES[p.edgeIdx]!;
        const from = getPos(edge.from, w, h);
        const to   = getPos(edge.to,   w, h);

        const t = p.reverse ? 1 - p.t : p.t;
        const px = from.x + (to.x - from.x) * t;
        const py = from.y + (to.y - from.y) * t;

        // Fade at ends
        const fadeT = Math.min(p.t, 1 - p.t) * 4;
        const alpha = p.alpha * Math.min(1, fadeT);

        ctx.beginPath();
        ctx.arc(px, py, p.r, 0, Math.PI * 2);
        // Input edges: burnt amber #C8892B (200, 137, 43); output edges: dark neutral
        const isInput = NODES.find((n) => n.id === edge.from)?.role === "input";
        ctx.fillStyle = isInput
          ? `rgba(200,137,43,${alpha})`
          : `rgba(112,112,112,${alpha * 0.7})`;
        ctx.fill();

        p.t += p.speed * dt;
        if (p.t > 1) p.t = 0;
      });

      // ── Draw nodes ────────────────────────────────────────────────
      NODES.forEach((node) => {
        const nx = node.x * w;
        const ny = node.y * h;
        const isActive = node.id === activeNodeRef.current;
        const isCore   = node.role === "core";

        // Gentle breath cycle — each node has a slightly different phase
        const phase = pulsePhase + node.x * 8 + node.y * 5;
        const breathe = 0.5 + 0.5 * Math.sin(phase * (isCore ? 1.4 : 1.0));

        // Confidence ring — radius scales with node.confidence
        const ringR = 7 + node.confidence * 8;
        const ringAlpha = isCore
          ? 0.12 + breathe * 0.08
          : 0.05 + breathe * 0.04;

        ctx.beginPath();
        ctx.arc(nx, ny, ringR, 0, Math.PI * 2);
        ctx.strokeStyle = isCore
          ? `rgba(200,137,43,${ringAlpha})`
          : `rgba(17,17,17,${ringAlpha})`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Active burst (during sweep)
        if (isActive) {
          const burstAlpha = 0.12 * (1 - sweepRef.current.t);
          ctx.beginPath();
          ctx.arc(nx, ny, ringR * 2, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(200,137,43,${burstAlpha})`;
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        // Core dot
        const dotR = isCore ? 4 : 3;
        ctx.beginPath();
        ctx.arc(nx, ny, dotR, 0, Math.PI * 2);
        ctx.fillStyle = isCore ? "#111111" : `rgba(17,17,17,${0.35 + node.confidence * 0.45})`;
        ctx.fill();

        // Label
        ctx.font = `500 8px ui-monospace, monospace`;
        ctx.textAlign = "center";
        const labelY = node.y < 0.38 ? ny - 16 : ny + 20;
        const labelAlpha = 0.35 + node.confidence * 0.35;
        ctx.fillStyle = `rgba(17,17,17,${labelAlpha})`;
        ctx.fillText(node.label.toUpperCase(), nx, labelY);

        // Confidence % under label for non-core nodes
        if (!isCore) {
          ctx.font = `400 7px ui-monospace, monospace`;
          ctx.fillStyle = `rgba(112,112,112,${labelAlpha * 0.7})`;
          ctx.fillText(`${Math.round(node.confidence * 100)}%`, nx, labelY + 10);
        }
      });

      ctx.restore();
      rafRef.current = requestAnimationFrame(draw);
    }

    function resize() {
      if (!canvas) return;
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width  = rect.width  * dpr;
      canvas.height = rect.height * dpr;
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    rafRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
    };
  }, [getPos]);

  return (
    <div className="relative w-full">
      {/* Live indicator row */}
      <div className="mb-2 flex items-center justify-between font-mono text-[10px] text-[#707070]">
        <span className="uppercase tracking-[0.18em]">IDENTITY NETWORK · LIVE</span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-[#C8892B]" />
            Input signal
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-[#707070]" />
            Output signal
          </span>
          <span className="flex items-center gap-1.5">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#C8892B] opacity-50" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[#C8892B]" />
            </span>
            MONITORING
          </span>
        </div>
      </div>
      <canvas
        ref={canvasRef}
        className="w-full"
        style={{ height: 110 }}
        aria-hidden
      />
    </div>
  );
}
