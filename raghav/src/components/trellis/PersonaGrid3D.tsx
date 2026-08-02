import { useEffect, useRef, useState, type MouseEvent } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { cn } from "@/lib/utils";

const POOL = [
  "/6.jpg",
  "/7.jpg",
  "/8.jpg",
  "/9.jpg",
  "/10.jpg",
  "/11.jpg",
  "/12.jpg",
] as const;

const FRAME_COUNT = 4;
const CYCLE_MS = 3000;
const MAX_TILT = 32;

/** Per-slot depth / offset so the grid reads as layered in 3D space. */
const SLOT_3D = [
  { z: 70, x: -10, y: -8, rot: -4 },
  { z: 18, x: 12, y: -14, rot: 5 },
  { z: 40, x: -14, y: 12, rot: 3 },
  { z: 90, x: 10, y: 10, rot: -6 },
] as const;

function shuffleInPlace<T>(items: T[]): T[] {
  for (let i = items.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    const tmp = items[i]!;
    items[i] = items[j]!;
    items[j] = tmp;
  }
  return items;
}

/** Always returns exactly 4 distinct images from the pool. */
function pickFrames(prev: string[]): string[] {
  const prevSet = new Set(prev);
  const unused = shuffleInPlace(POOL.filter((src) => !prevSet.has(src)));
  const used = shuffleInPlace(POOL.filter((src) => prevSet.has(src)));
  // Prefer images not currently on screen, then fill from the rest — never duplicates.
  const next: string[] = [];
  for (const src of [...unused, ...used]) {
    if (next.length >= FRAME_COUNT) break;
    if (!next.includes(src)) next.push(src);
  }
  // Safety: if pool were ever short, pad from full shuffle without repeats
  if (next.length < FRAME_COUNT) {
    for (const src of shuffleInPlace([...POOL])) {
      if (next.length >= FRAME_COUNT) break;
      if (!next.includes(src)) next.push(src);
    }
  }
  return next;
}

export function PersonaGrid3D({ className }: { className?: string }) {
  const reduceMotion = useReducedMotion();
  const stageRef = useRef<HTMLDivElement>(null);
  const [frames, setFrames] = useState<string[]>(() => pickFrames([]));
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [hovering, setHovering] = useState(false);

  useEffect(() => {
    for (const src of POOL) {
      const img = new window.Image();
      img.src = src;
    }
  }, []);

  useEffect(() => {
    const id = window.setInterval(() => {
      setFrames((prev) => pickFrames(prev));
    }, CYCLE_MS);
    return () => window.clearInterval(id);
  }, []);

  const onMove = (event: MouseEvent<HTMLDivElement>) => {
    if (reduceMotion || !stageRef.current) return;
    const rect = stageRef.current.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width - 0.5;
    const py = (event.clientY - rect.top) / rect.height - 0.5;
    setTilt({
      x: -(py * MAX_TILT),
      y: px * MAX_TILT,
    });
  };

  const onLeave = () => {
    setTilt({ x: 0, y: 0 });
    setHovering(false);
  };

  return (
    <div className={cn("relative w-full", className)}>
      {/* Soft ground shadow that sells the floating stack */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-6 bottom-2 h-10 rounded-[100%] bg-black/20 blur-2xl"
      />

      <div
        ref={stageRef}
        onMouseMove={onMove}
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={onLeave}
        className="relative aspect-[4/5] w-full [perspective:700px]"
      >
        <motion.div
          className="absolute inset-2 grid grid-cols-2 grid-rows-2 gap-4 [transform-style:preserve-3d]"
          animate={
            reduceMotion
              ? undefined
              : {
                  rotateX: tilt.x,
                  rotateY: tilt.y,
                  scale: hovering ? 1.06 : 1,
                  z: hovering ? 40 : 0,
                }
          }
          transition={{ type: "spring", stiffness: 140, damping: 16, mass: 0.55 }}
        >
          {frames.map((src, i) => {
            const slot = SLOT_3D[i]!;
            const parallaxX = tilt.y * (0.18 + i * 0.05);
            const parallaxY = tilt.x * (0.18 + i * 0.05);

            return (
              <motion.div
                key={`slot-${i}`}
                className="relative overflow-hidden rounded-[1.4rem] border border-white/40 bg-[#F4F4F2] [transform-style:preserve-3d]"
                style={{
                  boxShadow:
                    "0 28px 60px rgba(17,17,17,0.18), 0 8px 20px rgba(17,17,17,0.1), inset 0 1px 0 rgba(255,255,255,0.35)",
                }}
                animate={
                  reduceMotion
                    ? undefined
                    : {
                        x: slot.x + parallaxX,
                        y: slot.y - parallaxY,
                        z: slot.z,
                        rotateZ: slot.rot + tilt.y * 0.08,
                        rotateY: tilt.y * 0.35,
                        rotateX: tilt.x * 0.35,
                      }
                }
                transition={{ type: "spring", stiffness: 160, damping: 18, mass: 0.6 }}
              >
                <AnimatePresence mode="sync" initial={false}>
                  <motion.img
                    key={src}
                    src={src}
                    alt=""
                    draggable={false}
                    className="absolute inset-0 h-full w-full object-cover select-none"
                    initial={
                      reduceMotion
                        ? { opacity: 0 }
                        : { opacity: 0, scale: 1.12, filter: "blur(12px)" }
                    }
                    animate={
                      reduceMotion
                        ? { opacity: 1 }
                        : { opacity: 1, scale: 1.04, filter: "blur(0px)" }
                    }
                    exit={
                      reduceMotion
                        ? { opacity: 0 }
                        : { opacity: 0, scale: 0.94, filter: "blur(10px)" }
                    }
                    transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                  />
                </AnimatePresence>
                <div
                  aria-hidden
                  className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/30 via-transparent to-black/25"
                />
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </div>
  );
}
