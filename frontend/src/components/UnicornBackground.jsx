// components/UnicornBackground.jsx
// PURPOSE: Unicorn Studio-inspired dynamic WebGL/Canvas background animation.
// Creates aurora orbs, floating particles, mouse-reactive glowing clusters,
// and a subtle starfield — all via the HTML5 Canvas API.

import { useEffect, useRef } from "react";

export default function UnicornBackground() {
  const canvasRef = useRef(null);
  const animRef   = useRef(null);
  const mouseRef  = useRef({ x: 0.5, y: 0.5 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const handleMouse = (e) => {
      mouseRef.current = {
        x: e.clientX / window.innerWidth,
        y: e.clientY / window.innerHeight,
      };
    };
    window.addEventListener("mousemove", handleMouse);

    const STAR_COUNT = 180;
    const stars = Array.from({ length: STAR_COUNT }, () => ({
      x: Math.random(),
      y: Math.random(),
      r: Math.random() * 1.2 + 0.2,
      a: Math.random(),
      speed: Math.random() * 0.0004 + 0.0001,
    }));

    const orbs = [
      { x: 0.2,  y: 0.3,  r: 0.45, color: [109, 76, 255],  speed: 0.00012, phase: 0 },
      { x: 0.8,  y: 0.2,  r: 0.38, color: [168, 85, 247],  speed: 0.00009, phase: 2.1 },
      { x: 0.5,  y: 0.75, r: 0.42, color: [6, 182, 212],   speed: 0.00015, phase: 1.3 },
      { x: 0.15, y: 0.8,  r: 0.28, color: [244, 114, 182], speed: 0.0001,  phase: 3.7 },
      { x: 0.85, y: 0.65, r: 0.32, color: [99, 102, 241],  speed: 0.00013, phase: 0.8 },
    ];

    const PARTICLE_COUNT = 55;
    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.00018,
      vy: (Math.random() - 0.5) * 0.00018,
      r: Math.random() * 2.5 + 0.5,
      a: Math.random() * 0.6 + 0.2,
      color: [[109,76,255],[168,85,247],[6,182,212],[244,114,182]][Math.floor(Math.random()*4)],
    }));

    let t = 0;

    const draw = () => {
      const W = canvas.width;
      const H = canvas.height;
      t += 1;

      ctx.clearRect(0, 0, W, H);

      const bgGrad = ctx.createRadialGradient(W*0.5, H*0.5, 0, W*0.5, H*0.5, Math.max(W,H)*0.9);
      bgGrad.addColorStop(0, "#0a0a18");
      bgGrad.addColorStop(1, "#050508");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, W, H);

      ctx.strokeStyle = "rgba(109,76,255,0.04)";
      ctx.lineWidth = 1;
      const GRID = 50;
      for (let gx = 0; gx < W; gx += GRID) {
        ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, H); ctx.stroke();
      }
      for (let gy = 0; gy < H; gy += GRID) {
        ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(W, gy); ctx.stroke();
      }

      stars.forEach(s => {
        s.a += s.speed;
        const alpha = 0.3 + 0.5 * Math.abs(Math.sin(s.a));
        ctx.beginPath();
        ctx.arc(s.x * W, s.y * H, s.r, 0, Math.PI*2);
        ctx.fillStyle = `rgba(240,238,255,${alpha})`;
        ctx.fill();
      });

      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;
      orbs.forEach(orb => {
        const px = orb.x + 0.04 * Math.sin(t * orb.speed * 1000 + orb.phase);
        const py = orb.y + 0.04 * Math.cos(t * orb.speed * 800  + orb.phase);
        const cx = (px + mx * 0.06) * W;
        const cy = (py + my * 0.06) * H;
        const radius = orb.r * Math.min(W, H) * 0.9;

        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
        const [r, g, b] = orb.color;
        grad.addColorStop(0,   `rgba(${r},${g},${b},0.18)`);
        grad.addColorStop(0.4, `rgba(${r},${g},${b},0.10)`);
        grad.addColorStop(1,   `rgba(${r},${g},${b},0)`);

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI*2);
        ctx.fill();
      });

      particles.forEach(p => {
        p.x += p.vx + (mx - 0.5) * 0.00008;
        p.y += p.vy + (my - 0.5) * 0.00008;
        if (p.x < 0) p.x = 1; if (p.x > 1) p.x = 0;
        if (p.y < 0) p.y = 1; if (p.y > 1) p.y = 0;
        const [r, g, b] = p.color;
        ctx.beginPath();
        ctx.arc(p.x * W, p.y * H, p.r, 0, Math.PI*2);
        ctx.fillStyle = `rgba(${r},${g},${b},${p.a})`;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(p.x * W, p.y * H, p.r * 4, 0, Math.PI*2);
        ctx.fillStyle = `rgba(${r},${g},${b},0.06)`;
        ctx.fill();
      });

      const cgGrad = ctx.createRadialGradient(mx*W, my*H, 0, mx*W, my*H, 220);
      cgGrad.addColorStop(0,   "rgba(109,76,255,0.12)");
      cgGrad.addColorStop(0.5, "rgba(168,85,247,0.06)");
      cgGrad.addColorStop(1,   "rgba(109,76,255,0)");
      ctx.fillStyle = cgGrad;
      ctx.beginPath();
      ctx.arc(mx*W, my*H, 220, 0, Math.PI*2);
      ctx.fill();

      const vGrad = ctx.createRadialGradient(W*0.5, H*0.5, H*0.3, W*0.5, H*0.5, H*0.9);
      vGrad.addColorStop(0, "rgba(5,5,8,0)");
      vGrad.addColorStop(1, "rgba(5,5,8,0.7)");
      ctx.fillStyle = vGrad;
      ctx.fillRect(0, 0, W, H);

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouse);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 0,
      }}
    />
  );
}
