import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useThree, type ThreeEvent } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { keyOf } from "../lib/derive";
import { reduceMotion } from "../lib/jump";
import type { Deck, TimelinePoint } from "../types";

/* The call as ground: time runs east, each speaker is a ridge, and how much was said
   raises the ridge. Flat materials, no bloom, no particles — the same pens as the strip
   chart above it, read a second way. */

const SPAN = 12; // world units the whole call is drawn across
const HEIGHT = 2.4; // world units the longest turn stands
const LANE = 1.05; // spacing between one speaker's ridge and the next

/** The palette, resolved from CSS so the scene follows the page's theme. */
function usePalette() {
  const read = () => {
    const cs = getComputedStyle(document.documentElement);
    const v = (name: string) => cs.getPropertyValue(name).trim() || "#888";
    return {
      penA: v("--pen-a"),
      penB: v("--pen-b"),
      grid: v("--grid"),
      soft: v("--ink-soft"),
      paper: v("--paper-2"),
    };
  };
  const [palette, setPalette] = useState(read);
  useEffect(() => {
    const update = () => setPalette(read());
    const mo = new MutationObserver(update);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", update);
    return () => {
      mo.disconnect();
      mq.removeEventListener("change", update);
    };
  }, []);
  return palette;
}

/** One speaker's ridge: a skyline of their turns, given a little depth. */
function ridgeGeometry(points: TimelinePoint[], duration: number, maxWords: number) {
  const shape = new THREE.Shape();
  const x = (s: number) => (s / duration) * SPAN - SPAN / 2;
  const y = (w: number) => Math.max(0.012, (w / maxWords) * HEIGHT);
  shape.moveTo(-SPAN / 2, 0);
  const bar = Math.max(0.035, SPAN / Math.max(24, points.length * 2.4));
  for (const p of points) {
    const left = x(p.s);
    shape.lineTo(left, 0);
    shape.lineTo(left, y(p.words));
    shape.lineTo(left + bar, y(p.words));
    shape.lineTo(left + bar, 0);
  }
  shape.lineTo(SPAN / 2, 0);
  const geo = new THREE.ExtrudeGeometry(shape, { depth: 0.34, bevelEnabled: false });
  geo.translate(0, 0, -0.17);
  return geo;
}

const TARGET = 0.9;

/** Frames the whole call however wide the stage happens to be. */
function Fit() {
  const { camera, size } = useThree();
  useEffect(() => {
    const cam = camera as THREE.PerspectiveCamera;
    const half = Math.tan(((cam.fov * Math.PI) / 180) / 2);
    const distance = Math.max(
      (SPAN * 1.1) / (2 * half * (size.width / size.height)),
      (HEIGHT * 2.1) / (2 * half),
    );
    const dir = new THREE.Vector3(0.14, 0.36, 1).normalize().multiplyScalar(distance);
    cam.position.set(dir.x, TARGET + dir.y, dir.z);
    cam.updateProjectionMatrix();
  }, [camera, size]);
  return null;
}

function Floor({ color, ticks, reach }: { color: string; ticks: number[]; reach: number }) {
  const geometry = useMemo(() => {
    const pts: number[] = [];
    const half = SPAN / 2;
    for (const t of ticks) {
      const x = t * SPAN - half;
      pts.push(x, 0, -reach, x, 0, reach);
    }
    for (let i = -2; i <= 2; i++) {
      const z = (i / 2) * reach;
      pts.push(-half, 0, z, half, 0, z);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
    return g;
  }, [ticks, reach]);
  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={0.9} />
    </lineSegments>
  );
}

function Terrain({
  deck,
  onHover,
}: {
  deck: Deck;
  onHover: (point: TimelinePoint | null) => void;
}) {
  const palette = usePalette();
  const timeline = deck.metrics.timeline ?? [];
  const maxWords = timeline.reduce((m, t) => Math.max(m, t.words), 1) || 1;

  const lanes = useMemo(() => {
    const byKey = new Map<string, TimelinePoint[]>();
    for (const p of timeline) {
      const key = keyOf(deck, p.spk);
      if (!byKey.has(key)) byKey.set(key, []);
      byKey.get(key)!.push(p);
    }
    // one ridge per speaker, in the order the pens are assigned, centred on the floor
    const ordered = [...byKey.entries()]
      .sort((a, b) => deck.keys.indexOf(a[0]) - deck.keys.indexOf(b[0]))
      .slice(0, 4);
    const pens = [palette.penA, palette.penB];
    return ordered.map(([key, points], i) => ({
      key,
      points,
      z: ((ordered.length - 1) / 2 - i) * LANE,
      color: pens[i] ?? palette.soft,
      geometry: ridgeGeometry(points, deck.duration, maxWords),
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeline, deck.duration, maxWords, palette.penA, palette.penB, palette.soft]);

  useEffect(() => () => lanes.forEach((l) => l.geometry.dispose()), [lanes]);

  const ticks = useMemo(() => Array.from({ length: 9 }, (_, i) => i / 8), []);
  const reach = Math.max(1.6, (lanes.length / 2) * LANE + 0.7);

  /** The x of the hit tells the time; the time tells the turn. */
  const pick = (lane: (typeof lanes)[number]) => (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    const seconds = ((e.point.x + SPAN / 2) / SPAN) * deck.duration;
    let best: TimelinePoint | null = null;
    let bd = Infinity;
    for (const p of lane.points) {
      const d = Math.abs(p.s - seconds);
      if (d < bd) {
        bd = d;
        best = p;
      }
    }
    onHover(best);
  };

  return (
    <>
      <Fit />
      <ambientLight intensity={1} />
      <Floor color={palette.grid} ticks={ticks} reach={reach} />
      {lanes.map((lane) => (
        <group key={lane.key} position={[0, 0, lane.z]}>
          <mesh
            geometry={lane.geometry}
            onPointerMove={pick(lane)}
            onPointerOut={() => onHover(null)}
          >
            <meshBasicMaterial color={lane.color} />
          </mesh>
        </group>
      ))}
      <OrbitControls
        enablePan={false}
        enableZoom={false}
        autoRotate={!reduceMotion()}
        autoRotateSpeed={0.32}
        minPolarAngle={0.75}
        maxPolarAngle={1.35}
        target={[0, TARGET, 0]}
      />
    </>
  );
}

/** WebGL is not guaranteed. If it is missing the section simply is not there. */
function hasWebGL(): boolean {
  try {
    const c = document.createElement("canvas");
    return Boolean(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

export default function CallTerrain({ deck }: { deck: Deck }) {
  const [hover, setHover] = useState<TimelinePoint | null>(null);
  const [failed, setFailed] = useState(false);
  const ok = useRef(hasWebGL());

  if (!ok.current || failed || !(deck.metrics.timeline ?? []).length) return null;

  return (
    <div className="terrain">
      <div className="terrain-head">
        <h3 className="subhead" style={{ margin: 0 }}>
          The same call as ground
        </h3>
        <p className="terrain-note">
          Time runs east, each speaker is a ridge, and a ridge rises with how much was said
          there. Drag to look around.
        </p>
      </div>
      <div className="terrain-stage">
        <Canvas
          camera={{ position: [1.2, 3.2, 9], fov: 32 }}
          dpr={[1, 2]}
          gl={{ antialias: true, alpha: true }}
          onError={() => setFailed(true)}
        >
          <Terrain deck={deck} onHover={setHover} />
        </Canvas>
        {hover && (
          <div className="terrain-read">
            {hover.ts} / {hover.spk} / {hover.words} words
          </div>
        )}
      </div>
    </div>
  );
}
