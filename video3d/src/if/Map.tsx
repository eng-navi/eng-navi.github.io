import { geoEquirectangular, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import { Img, interpolate, staticFile } from "remotion";
import world50 from "world-atlas/countries-50m.json";

// 地理クイズの地図。衛星写真(パブリックドメイン)+国境。カメラは [経度, 緯度, 倍率] で動かす
// 世界の座標:world.jpg と同じ 4800×2400(正距円筒図法)
const WW = 4800, WH = 2400, SW = 1080, SH = 1920;
const proj = geoEquirectangular().scale(WW / (2 * Math.PI)).translate([WW / 2, WH / 2]);
const path = geoPath(proj);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const countries = (feature(world50 as any, (world50 as any).objects.countries) as any).features as { id: string; properties: { name: string } }[];
const EA = { x: 3733.33, y: 400, w: 933.33, h: 666.67 };  // eastasia.jpg(東経100〜170、北緯10〜60)の位置

// 日本周辺のプレート境界(おおよそ)
const OVERLAYS: Record<string, [number, number][][]> = {
  jp_plates: [
    [[156, 50], [150, 46], [146, 42.5], [143.5, 39], [142.5, 35.5]],          // 千島・日本海溝(太平洋プレート)
    [[142.5, 35.5], [142.3, 31], [143, 26], [145, 18]],                      // 伊豆・小笠原海溝
    [[139.3, 34.8], [137, 33.4], [134, 32.6], [131.5, 30.5], [128.5, 27.5], [124, 24.5]],  // 南海トラフ・琉球海溝
    [[139.3, 34.8], [140.5, 34.6], [142.5, 35.5]],                           // 相模トラフ
    [[138.5, 35], [138, 37.2], [139.2, 40.5], [139.8, 44], [141.5, 48]],      // 北米(オホーツク)とユーラシア(アムール)の境
  ],
};

export type MapSpec = {
  from: [number, number, number]; to?: [number, number, number];  // [経度, 緯度, 倍率(1で世界の横幅が画面いっぱい)]
  hl?: string[];                       // 光らせる国(ISO 数字コード。日本=392)
  overlay?: string;                    // OVERLAYS の名前(線が描かれていく)
  arrows?: [number, number, number, number][];  // [経度1, 緯度1, 経度2, 緯度2]
  labels?: [number, number, string][];
  dots?: [number, number][];           // 地震などの波紋
  shake?: boolean;
};

const ease = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

export const MapView = ({ m, f, len }: { m: MapSpec; f: number; len: number }) => {
  const k = ease(Math.min(1, f / (len * 0.75)));
  const to = m.to ?? m.from;
  const [lon, lat, z] = [0, 1, 2].map((i) => interpolate(k, [0, 1], [m.from[i], to[i]]));
  const s = Math.max((z * SW) / WW, SH / WH);  // 地図の高さが画面より小さくならないように
  const [cx, cy] = proj([lon, lat]) as [number, number];
  const shx = m.shake ? Math.sin(f * 2.1) * 14 * Math.max(0, 1 - f / 30) + Math.sin(f * 1.3) * 4 : 0;
  const toScreen = (lo: number, la: number) => { const [x, y] = proj([lo, la]) as [number, number]; return [(x - cx) * s + SW / 2 + shx, (y - cy) * s + SH * 0.47]; };
  const draw = Math.min(1, f / (len * 0.6));
  const sw = 1.6 / s;  // 線の太さを画面上で一定に
  const tf = `translate(${SW / 2 + shx} ${SH * 0.47}) scale(${s}) translate(${-cx} ${-cy})`;
  return (
    <div style={{ position: "absolute", width: SW, height: SH, overflow: "hidden", background: "#06131f" }}>
      {/* 衛星写真(画像は Img で読み込みを待つ) */}
      <div style={{ position: "absolute", left: 0, top: 0, width: WW, height: WH, transformOrigin: "0 0",
                    transform: `translate(${SW / 2 + shx}px, ${SH * 0.47}px) scale(${s}) translate(${-cx}px, ${-cy}px)` }}>
        <Img src={staticFile("geo/world.jpg")} style={{ position: "absolute", left: 0, top: 0, width: WW, height: WH }} />
        {z > 3.5 && <Img src={staticFile("geo/eastasia.jpg")} style={{ position: "absolute", left: EA.x, top: EA.y, width: EA.w, height: EA.h,
                                                                       opacity: Math.min(1, (z - 3.5) / 2.5) }} />}
      </div>
    <svg width={SW} height={SH} viewBox={`0 0 ${SW} ${SH}`} style={{ position: "absolute" }}>
      <defs>
        <marker id="ah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#ff4d4d" /></marker>
        <radialGradient id="mvig" cx="0.5" cy="0.47" r="0.75"><stop offset="0.5" stopColor="#000" stopOpacity={0} /><stop offset="1" stopColor="#000" stopOpacity={0.7} /></radialGradient>
      </defs>
      <g transform={tf}>
        <g fill="none" stroke="rgba(255,255,255,0.55)" strokeWidth={sw * 0.8}>
          {countries.map((c, i) => <path key={i} d={path(c as never) ?? ""} />)}
        </g>
        {(m.hl ?? []).map((id) => {
          const c = countries.find((x) => x.id === id);
          return c ? <path key={id} d={path(c as never) ?? ""} fill={`rgba(255,210,63,${0.25 + 0.15 * Math.sin(f / 6)})`} stroke="#ffd23f" strokeWidth={sw * 2.2} /> : null;
        })}
        {m.overlay && (OVERLAYS[m.overlay] ?? []).map((line, i) => (
          <path key={i} d={"M" + line.map(([lo, la]) => (proj([lo, la]) as number[]).join(" ")).join(" L")} fill="none" stroke="#ff4d4d"
                strokeWidth={sw * 3} strokeDasharray="1" pathLength={1} strokeDashoffset={1 - draw} strokeLinecap="round" />
        ))}
      </g>
      {(m.arrows ?? []).map(([a, b, c, d], i) => {
        const [x1, y1] = toScreen(a, b), [x2, y2] = toScreen(c, d);
        const g = Math.min(1, Math.max(0, (f - 8 - i * 6) / 20));
        return <line key={i} x1={x1} y1={y1} x2={x1 + (x2 - x1) * g} y2={y1 + (y2 - y1) * g} stroke="#ff4d4d" strokeWidth={14} strokeLinecap="round" markerEnd="url(#ah)" opacity={g > 0 ? 1 : 0} />;
      })}
      {(m.dots ?? []).map(([a, b], i) => {
        const [x, y] = toScreen(a, b), p = ((f + i * 9) % 30) / 30;
        return <g key={i}><circle cx={x} cy={y} r={10} fill="#ff4d4d" /><circle cx={x} cy={y} r={10 + p * 60} fill="none" stroke="#ff4d4d" strokeWidth={5} opacity={1 - p} /></g>;
      })}
      {(m.labels ?? []).map(([a, b, t], i) => {
        const [x, y] = toScreen(a, b), o = Math.min(1, Math.max(0, (f - 6 - i * 5) / 8));
        return <text key={i} x={x} y={y} textAnchor="middle" fontSize={46} fontWeight={900} fill="#fff" stroke="#06131f" strokeWidth={10} paintOrder="stroke"
                     fontFamily="'Avenir Next', Arial" letterSpacing={3} opacity={o}>{t}</text>;
      })}
      <rect width={SW} height={SH} fill="url(#mvig)" />
    </svg>
    </div>
  );
};
