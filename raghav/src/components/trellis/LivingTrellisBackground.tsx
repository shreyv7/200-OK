import React, { useEffect, useRef } from "react";

// Fast, deterministic 2D Simplex Noise for procedural fluid particle motion
class SimplexNoise {
  private perm: number[] = [];
  constructor(seed = 4242) {
    const p: number[] = [];
    for (let i = 0; i < 256; i++) p[i] = i;
    let s = seed;
    for (let i = 255; i > 0; i--) {
      s = (s * 16807) % 2147483647;
      const j = Math.floor((s / 2147483647) * (i + 1));
      [p[i]!, p[j]!] = [p[j]!, p[i]!];
    }
    this.perm = new Array(512);
    for (let i = 0; i < 512; i++) this.perm[i] = p[i & 255]!;
  }

  noise2D(xin: number, yin: number): number {
    const F2 = 0.5 * (Math.sqrt(3.0) - 1.0);
    const G2 = (3.0 - Math.sqrt(3.0)) / 6.0;
    const s = (xin + yin) * F2;
    const i = Math.floor(xin + s);
    const j = Math.floor(yin + s);
    const t = (i + j) * G2;
    const X0 = i - t;
    const Y0 = j - t;
    const x0 = xin - X0;
    const y0 = yin - Y0;
    let i1: number, j1: number;
    if (x0 > y0) {
      i1 = 1;
      j1 = 0;
    } else {
      i1 = 0;
      j1 = 1;
    }
    const x1 = x0 - i1 + G2;
    const y1 = y0 - j1 + G2;
    const x2 = x0 - 1.0 + 2.0 * G2;
    const y2 = y0 - 1.0 + 2.0 * G2;
    const ii = i & 255;
    const jj = j & 255;
    const gi0 = this.perm[ii + (this.perm[jj] || 0)]! % 8;
    const gi1 = this.perm[ii + i1 + (this.perm[jj + j1] || 0)]! % 8;
    const gi2 = this.perm[ii + 1 + (this.perm[jj + 1] || 0)]! % 8;
    let t0 = 0.5 - x0 * x0 - y0 * y0;
    let n0 = 0,
      n1 = 0,
      n2 = 0;
    if (t0 > 0) {
      t0 *= t0;
      n0 = t0 * t0 * this.grad(gi0, x0, y0);
    }
    let t1 = 0.5 - x1 * x1 - y1 * y1;
    if (t1 > 0) {
      t1 *= t1;
      n1 = t1 * t1 * this.grad(gi1, x1, y1);
    }
    let t2 = 0.5 - x2 * x2 - y2 * y2;
    if (t2 > 0) {
      t2 *= t2;
      n2 = t2 * t2 * this.grad(gi2, x2, y2);
    }
    return 70.0 * (n0 + n1 + n2);
  }

  private grad(hash: number, x: number, y: number) {
    const h = hash & 7;
    const u = h < 4 ? x : y;
    const v = h < 4 ? y : x;
    return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
  }
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  layer: 1 | 2 | 3; // 3 Depth Layers
  radius: number;
  baseAlpha: number;
  noiseOffset: number;
  clusterTargetX: number;
  clusterTargetY: number;
  isElectricPulseNode?: boolean;
}

interface EnergyPulse {
  fromIndex: number;
  toIndex: number;
  progress: number;
  speed: number;
}

export function LivingTrellisBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = 0;
    let height = 0;
    let dpr = 1;

    // Mouse coordinates (smooth lerp)
    let mouseX = -2000;
    let mouseY = -2000;
    let targetMouseX = -2000;
    let targetMouseY = -2000;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      targetMouseX = e.clientX - rect.left;
      targetMouseY = e.clientY - rect.top;
    };

    const handleMouseLeave = () => {
      targetMouseX = -2000;
      targetMouseY = -2000;
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseleave", handleMouseLeave);

    // Scroll state tracking (0.0 to 1.0)
    let scrollRatio = 0;
    const handleScroll = () => {
      const docHeight = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight
      ) - window.innerHeight;
      scrollRatio = docHeight > 0 ? Math.min(1, Math.max(0, window.scrollY / docHeight)) : 0;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();

    const simplex = new SimplexNoise(777);
    let particles: Particle[] = [];
    let pulses: EnergyPulse[] = [];

    // Initialize 3-layer particle system
    const initParticles = () => {
      dpr = window.devicePixelRatio || 1;
      width = window.innerWidth;
      height = window.innerHeight;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);

      const totalCount = Math.min(240, Math.floor((width * height) / 6000));
      particles = [];
      pulses = [];

      // Define stable target cluster hubs for final scroll state (Refined Identity Graph)
      const hubs = [
        { x: width * 0.2, y: height * 0.25 },
        { x: width * 0.8, y: height * 0.22 },
        { x: width * 0.5, y: height * 0.5 },
        { x: width * 0.25, y: height * 0.78 },
        { x: width * 0.75, y: height * 0.82 },
      ];

      for (let i = 0; i < totalCount; i++) {
        // Layer distribution: 30% background (blurred), 60% midground, 10% foreground pulse nodes
        let layer: 1 | 2 | 3 = 2;
        const rand = Math.random();
        if (rand < 0.3) layer = 1;
        else if (rand > 0.88) layer = 3;

        let x = Math.random() * width;
        let y = Math.random() * height;

        // Density bias towards upper-right (Hero area)
        if (Math.random() < 0.4) {
          x = width * 0.45 + Math.random() * width * 0.5;
          y = Math.random() * height * 0.6;
        }

        const hub = hubs[i % hubs.length];
        const angle = Math.random() * Math.PI * 2;
        const rOffset = 40 + Math.random() * 110;

        particles.push({
          x,
          y,
          vx: (Math.random() - 0.5) * (layer === 1 ? 0.15 : 0.35),
          vy: (Math.random() - 0.5) * (layer === 1 ? 0.15 : 0.35),
          layer,
          radius: layer === 1 ? 1.8 : layer === 3 ? 2.4 : 1.2,
          baseAlpha: layer === 1 ? 0.18 : layer === 3 ? 0.85 : 0.45,
          noiseOffset: Math.random() * 5000,
          clusterTargetX: (hub?.x ?? width / 2) + Math.cos(angle) * rOffset,
          clusterTargetY: (hub?.y ?? height / 2) + Math.sin(angle) * rOffset,
          isElectricPulseNode: layer === 3,
        });
      }
    };

    initParticles();
    window.addEventListener("resize", initParticles);

    // Subtle paper grain canvas
    const grainCanvas = document.createElement("canvas");
    grainCanvas.width = 128;
    grainCanvas.height = 128;
    const grainCtx = grainCanvas.getContext("2d");
    if (grainCtx) {
      const imgData = grainCtx.createImageData(128, 128);
      for (let k = 0; k < imgData.data.length; k += 4) {
        const v = Math.floor(Math.random() * 255);
        imgData.data[k] = v;
        imgData.data[k + 1] = v;
        imgData.data[k + 2] = v;
        imgData.data[k + 3] = 10; // 3.8% tactile paper grain
      }
      grainCtx.putImageData(imgData, 0, 0);
    }

    let startTime = performance.now();

    const render = (time: number) => {
      const elapsed = (time - startTime) / 1000;

      // Smooth mouse lerp
      mouseX += (targetMouseX - mouseX) * 0.06;
      mouseY += (targetMouseY - mouseY) * 0.06;

      ctx.clearRect(0, 0, width, height);

      const isDark = document.documentElement.classList.contains("dark");

      // Color System: Pure monochrome base + subtle electric blue accent for AI energy pulses
      const particleBaseColor = isDark ? "255, 255, 255" : "18, 18, 22";
      const lineBaseColor = isDark ? "240, 240, 248" : "30, 30, 35";
      const electricBlueAccent = "56, 189, 248"; // Soft electric blue pulse (#38bdf8)

      // Connection threshold grows with scroll state
      const connectDist = 90 + scrollRatio * 40;
      const connectDistSq = connectDist * connectDist;

      // --- LAYER 1: Background Particles (Soft Blurred Depth) ---
      ctx.save();
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        if (!p || p.layer !== 1) continue;

        // Slow organic noise drift
        const n = simplex.noise2D(
          p.x * 0.001 + p.noiseOffset,
          p.y * 0.001 + elapsed * 0.02
        );
        const angle = n * Math.PI * 2;
        p.vx += Math.cos(angle) * 0.008;
        p.vy += Math.sin(angle) * 0.008;

        p.vx *= 0.96;
        p.vy *= 0.96;
        p.x += p.vx;
        p.y += p.vy;

        // Wrap around
        if (p.x < -30) p.x = width + 30;
        if (p.x > width + 30) p.x = -30;
        if (p.y < -30) p.y = height + 30;
        if (p.y > height + 30) p.y = -30;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${particleBaseColor}, ${p.baseAlpha * 0.6})`;
        ctx.fill();
      }
      ctx.restore();

      // --- LAYER 2: Primary Particles & Connections ---
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        if (!p || p.layer === 1) continue;

        // 1. Procedural Simplex noise drift
        const n = simplex.noise2D(
          p.x * 0.0012 + p.noiseOffset,
          p.y * 0.0012 + elapsed * 0.035
        );
        const angle = n * Math.PI * 2;
        p.vx += Math.cos(angle) * 0.015;
        p.vy += Math.sin(angle) * 0.015;

        // 2. Scroll State Morphing:
        // Scroll 0-0.3: Loose field
        // Scroll 0.3-0.7: Clear connections & active pulses
        // Scroll 0.7-1.0: Converge into refined identity graph clusters
        if (scrollRatio > 0.55) {
          const structWeight = (scrollRatio - 0.55) * 2.2;
          const dxTarget = p.clusterTargetX - p.x;
          const dyTarget = p.clusterTargetY - p.y;
          p.vx += dxTarget * 0.0006 * structWeight;
          p.vy += dyTarget * 0.0006 * structWeight;
        }

        // 3. Mouse Physics (Gentle attraction & smooth repulsion deflection)
        if (mouseX > 0 && mouseY > 0) {
          const mdx = p.x - mouseX;
          const mdy = p.y - mouseY;
          const mdist = Math.sqrt(mdx * mdx + mdy * mdy);

          if (mdist < 160 && mdist > 0) {
            const force = (1 - mdist / 160) * 0.22;
            if (mdist < 50) {
              p.vx += (mdx / mdist) * force * 0.7;
              p.vy += (mdy / mdist) * force * 0.7;
            } else {
              p.vx -= (mdx / mdist) * force * 0.15;
              p.vy -= (mdy / mdist) * force * 0.15;
            }
          }
        }

        p.vx *= 0.95;
        p.vy *= 0.95;
        p.x += p.vx;
        p.y += p.vy;

        // Wrap around
        if (p.x < -30) p.x = width + 30;
        if (p.x > width + 30) p.x = -30;
        if (p.y < -30) p.y = height + 30;
        if (p.y > height + 30) p.y = -30;
      }

      // Draw Connections (Low opacity temporary links)
      ctx.lineWidth = 0.75;
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        if (!p1 || p1.layer === 1) continue;

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          if (!p2 || p2.layer === 1) continue;

          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const distSq = dx * dx + dy * dy;

          if (distSq < connectDistSq) {
            const dist = Math.sqrt(distSq);
            const fade = 1 - dist / connectDist;
            const lineAlpha = (0.035 + scrollRatio * 0.045) * fade * fade;

            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(${lineBaseColor}, ${lineAlpha})`;
            ctx.stroke();

            // Spawn Electric Blue Signal Pulses during middle/late scroll states (Intervention / Identity)
            if (
              scrollRatio > 0.35 &&
              pulses.length < 14 &&
              Math.random() < 0.02 + scrollRatio * 0.03
            ) {
              pulses.push({
                fromIndex: i,
                toIndex: j,
                progress: 0,
                speed: 0.014 + Math.random() * 0.02,
              });
            }
          }
        }
      }

      // --- LAYER 3: Render Electric Blue Signal Pulses Traveling Across Graph ---
      for (let k = pulses.length - 1; k >= 0; k--) {
        const pulse = pulses[k];
        if (!pulse) continue;
        pulse.progress += pulse.speed;

        if (pulse.progress >= 1) {
          pulses.splice(k, 1);
          continue;
        }

        const p1 = particles[pulse.fromIndex];
        const p2 = particles[pulse.toIndex];
        if (!p1 || !p2) continue;

        const currX = p1.x + (p2.x - p1.x) * pulse.progress;
        const currY = p1.y + (p2.y - p1.y) * pulse.progress;

        // Pulse Core with soft electric blue bloom
        ctx.beginPath();
        ctx.arc(currX, currY, 1.8, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${electricBlueAccent}, 0.9)`;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(currX, currY, 4, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${electricBlueAccent}, 0.25)`;
        ctx.fill();
      }

      // Render Midground & Foreground Particles (Layer 2 & Layer 3)
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        if (!p || p.layer === 1) continue;

        const alphaPulse = 0.85 + Math.sin(elapsed * 2 + p.noiseOffset) * 0.15;
        const currentAlpha = p.baseAlpha * alphaPulse;

        if (p.layer === 3) {
          // Brighter temporary node with subtle electric blue tint
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${particleBaseColor}, ${currentAlpha})`;
          ctx.fill();

          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius * 2.5, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${electricBlueAccent}, ${currentAlpha * 0.25})`;
          ctx.fill();
        } else {
          // Standard Layer 2 Particle
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${particleBaseColor}, ${currentAlpha})`;
          ctx.fill();
        }
      }

      // --- Paper Texture / Invisible Grain Overlay ---
      if (grainCtx) {
        ctx.save();
        const pattern = ctx.createPattern(grainCanvas, "repeat");
        if (pattern) {
          ctx.fillStyle = pattern;
          ctx.fillRect(0, 0, width, height);
        }
        ctx.restore();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", initParticles);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden opacity-90">
      <canvas ref={canvasRef} className="block h-full w-full" />
    </div>
  );
}
