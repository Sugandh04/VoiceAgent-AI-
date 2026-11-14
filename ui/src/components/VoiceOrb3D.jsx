import React, { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * VoiceOrb3D — Sovereign AI Interactive 3D Neural Voice Orb
 * Built with Three.js WebGL:
 *   - Morphing particle sphere with procedural simplex noise displacement
 *   - Sarvam-inspired palette: Terracotta Ember (#FF6B35) -> Tech Indigo (#4F46E5) -> Cyan (#06B6D4)
 *   - Reacts to mouse interaction and live voice amplitude/state
 */
export default function VoiceOrb3D({
  size = 220,
  isActive = false,
  isSpeaking = false,
  interactive = true,
}) {
  const mountRef = useRef(null);
  const stateRef = useRef({ isActive, isSpeaking });

  useEffect(() => {
    stateRef.current = { isActive, isSpeaking };
  }, [isActive, isSpeaking]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // ── 1. Scene, Camera, Renderer ──────────────────────────────────────────
    const width = size;
    const height = size;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 4.2;

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // ── 2. Create Multi-Layer Particle Orb ──────────────────────────────────
    // Particle count: 1,800 points for dense, shimmering neural aura
    const particleCount = 1800;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const originalPositions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const scales = new Float32Array(particleCount);

    const colorA = new THREE.Color("#FF6B35"); // Sarvam Terracotta Ember
    const colorB = new THREE.Color("#F59E0B"); // Warm Solar Amber
    const colorC = new THREE.Color("#4F46E5"); // High-Tech Indigo
    const colorD = new THREE.Color("#06B6D4"); // Cyan Spark

    for (let i = 0; i < particleCount; i++) {
      // Golden Spiral distribution on sphere surface
      const phi = Math.acos(-1 + (2 * i) / particleCount);
      const theta = Math.sqrt(particleCount * Math.PI) * phi;
      const radius = 1.25 + (Math.random() - 0.5) * 0.12;

      const x = radius * Math.cos(theta) * Math.sin(phi);
      const y = radius * Math.sin(theta) * Math.sin(phi);
      const z = radius * Math.cos(phi);

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      originalPositions[i * 3] = x;
      originalPositions[i * 3 + 1] = y;
      originalPositions[i * 3 + 2] = z;

      // Color gradient distribution across latitude
      const t = (y + 1.2) / 2.4;
      const pointColor = new THREE.Color();
      if (t < 0.35) {
        pointColor.lerpColors(colorA, colorB, t / 0.35);
      } else if (t < 0.75) {
        pointColor.lerpColors(colorB, colorC, (t - 0.35) / 0.4);
      } else {
        pointColor.lerpColors(colorC, colorD, (t - 0.75) / 0.25);
      }

      colors[i * 3] = pointColor.r;
      colors[i * 3 + 1] = pointColor.g;
      colors[i * 3 + 2] = pointColor.b;

      scales[i] = 1.0 + Math.random() * 1.5;
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    // Particle sprite material
    const canvas = document.createElement("canvas");
    canvas.width = 32;
    canvas.height = 32;
    const ctx = canvas.getContext("2d");
    const gradient = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
    gradient.addColorStop(0, "rgba(255, 255, 255, 1)");
    gradient.addColorStop(0.3, "rgba(255, 255, 255, 0.8)");
    gradient.addColorStop(0.7, "rgba(255, 107, 53, 0.25)");
    gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 32, 32);

    const texture = new THREE.CanvasTexture(canvas);

    const material = new THREE.PointsMaterial({
      size: 0.08,
      map: texture,
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // Inner glowing core sphere
    const coreGeo = new THREE.SphereGeometry(0.85, 32, 32);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0xff6b35,
      transparent: true,
      opacity: 0.15,
      wireframe: true,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    scene.add(coreMesh);

    // Outer subtle cyan aura ring
    const ringGeo = new THREE.TorusGeometry(1.6, 0.015, 16, 100);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.35,
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 3;
    scene.add(ringMesh);

    // ── 3. Mouse Interaction ────────────────────────────────────────────────
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const handleMouseMove = (e) => {
      if (!interactive) return;
      const rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / width - 0.5) * 2;
      mouseY = -(((e.clientY - rect.top) / height - 0.5) * 2);
    };

    if (interactive) {
      window.addEventListener("mousemove", handleMouseMove);
    }

    // ── 4. Animation Loop ───────────────────────────────────────────────────
    let animationFrameId;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const time = clock.getElapsedTime();
      const { isActive, isSpeaking } = stateRef.current;

      // Smooth camera follow mouse
      targetX += (mouseX - targetX) * 0.05;
      targetY += (mouseY - targetY) * 0.05;

      particles.rotation.y = time * 0.25 + targetX * 0.5;
      particles.rotation.x = Math.sin(time * 0.2) * 0.15 + targetY * 0.3;
      coreMesh.rotation.y = -time * 0.35;
      ringMesh.rotation.z = time * 0.4;

      // Morphing particle displacement
      const posAttr = geometry.attributes.position;
      const posArray = posAttr.array;

      // Audio activity multiplier
      const energy = isSpeaking ? 1.8 : isActive ? 1.2 : 0.8;
      const pulse = Math.sin(time * 3 * energy) * 0.08 * energy;

      for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        const ox = originalPositions[i3];
        const oy = originalPositions[i3 + 1];
        const oz = originalPositions[i3 + 2];

        // 3D procedural ripple
        const noise =
          Math.sin(ox * 2.5 + time * 2) *
          Math.cos(oy * 2.5 + time * 2) *
          Math.sin(oz * 2.5 + time * 1.5) *
          (0.12 * energy);

        const scale = 1 + pulse + noise;
        posArray[i3] = ox * scale;
        posArray[i3 + 1] = oy * scale;
        posArray[i3 + 2] = oz * scale;
      }
      posAttr.needsUpdate = true;

      // Pulse core opacity
      coreMat.opacity = isSpeaking
        ? 0.35 + Math.sin(time * 8) * 0.15
        : isActive
        ? 0.25 + Math.sin(time * 4) * 0.08
        : 0.12;

      renderer.render(scene, camera);
    };

    animate();

    // ── 5. Cleanup ──────────────────────────────────────────────────────────
    return () => {
      cancelAnimationFrame(animationFrameId);
      if (interactive) {
        window.removeEventListener("mousemove", handleMouseMove);
      }
      geometry.dispose();
      material.dispose();
      texture.dispose();
      coreGeo.dispose();
      coreMat.dispose();
      ringGeo.dispose();
      ringMat.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [size, interactive]);

  return (
    <div
      ref={mountRef}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    />
  );
}

