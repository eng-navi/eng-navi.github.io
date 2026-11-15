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
  nile: [[[32.9, 22.0], [32.9, 24.1], [32.6, 25.7], [31.7, 26.6], [31.2, 27.2], [30.8, 28.5], [31.24, 30.04], [30.9, 31.4]],
         [[31.24, 30.04], [31.8, 31.4]]],
};
const OVERLAY_COLOR: Record<string, string> = { nile: "#2a7fd8" };  // 指定がなければ赤

export type MapSpec = {
  from: [number, number, number]; to?: [number, number, number];  // [経度, 緯度, 倍率(1で世界の横幅が画面いっぱい)]
  style?: "sat" | "political";         // sat:衛星写真 / political:国を色で塗り分けた地図(Knowledgia 風)
  colors?: Record<string, string>;     // political:国ごとの色(ISO 数字コード → 色)
  glow?: string[];                     // フチが白く光る国
  hl?: string[];                       // 黄色く光らせる国(ISO 数字コード。日本=392)
  overlay?: string;                    // OVERLAYS の名前(線が描かれていく)
  arrows?: [number, number, number, number][];  // [経度1, 緯度1, 経度2, 緯度2]
  labels?: [number, number, string][];
  icons?: [number, number, string][];  // 地図の上の絵文字や国旗(ポンと出る)
  dots?: [number, number][];           // 地震などの波紋
  shake?: boolean;
};

const ease = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const pop = (x: number) => (x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.2 * Math.pow(x - 1, 3) + 1.2 * Math.pow(x - 1, 2));  // 少し行き過ぎて戻る

export const MapView = ({ m, f, len }: { m: MapSpec; f: number; len: number }) => {
  const pol = m.style === "political";
  const k = ease(Math.min(1, f / (len * 0.7)));
  const to = m.to ?? m.from;
  const [lon, lat, z0] = [0, 1, 2].map((i) => interpolate(k, [0, 1], [m.from[i], to[i]]));
  const z = z0 * (1 + 0.04 * Math.max(0, f / len - 0.7));  // 止まった後もゆっくり寄り続ける
  const s = Math.max((z * SW) / WW, SH / WH);  // 地図の高さが画面より小さくならないように
  const [cx, cy] = proj([lon, lat]) as [number, number];
  const shx = m.shake ? Math.sin(f * 2.1) * 14 * Math.max(0, 1 - f / 30) + Math.sin(f * 1.3) * 4 : 0;
  const toScreen = (lo: number, la: number) => { const [x, y] = proj([lo, la]) as [number, number]; return [(x - cx) * s + SW / 2 + shx, (y - cy) * s + SH * 0.47]; };
  const draw = Math.min(1, f / (len * 0.6));
  const sw = 1.6 / s;  // 線の太さを画面上で一定に
  const tf = `translate(${SW / 2 + shx} ${SH * 0.47}) scale(${s}) translate(${-cx} ${-cy})`;
  const imgTf = `translate(${SW / 2 + shx}px, ${SH * 0.47}px) scale(${s}) translate(${-cx}px, ${-cy}px)`;
  const red = pol ? "#e8332a" : "#ff4d4d";
  return (
    <div style={{ position: "absolute", width: SW, height: SH, overflow: "hidden", background: pol ? "#b9dde8" : "#06131f" }}>
      {!pol && (  /* 衛星写真(画像は Img で読み込みを待つ) */
        <div style={{ position: "absolute", left: 0, top: 0, width: WW, height: WH, transformOrigin: "0 0", transform: imgTf }}>
          <Img src={staticFile("geo/world.jpg")} style={{ position: "absolute", left: 0, top: 0, width: WW, height: WH }} />
          {z > 3.5 && <Img src={staticFile("geo/eastasia.jpg")} style={{ position: "absolute", left: EA.x, top: EA.y, width: EA.w, height: EA.h,
                                                                         opacity: Math.min(1, (z - 3.5) / 2.5) }} />}
        </div>
      )}
      {pol && (<>  {/* 塗り分け:国の色 → 山の陰影(乗算)の順に重ねる */}
        <svg width={SW} height={SH} viewBox={`0 0 ${SW} ${SH}`} style={{ position: "absolute" }}>
          <g transform={tf} stroke="#ffffff" strokeWidth={sw * 1.1} strokeLinejoin="round">
            {countries.map((c, i) => <path key={i} d={path(c as never) ?? ""} fill={m.colors?.[c.id] ?? "#efe7cf"} />)}
          </g>
        </svg>
        <div style={{ position: "absolute", left: 0, top: 0, width: WW, height: WH, transformOrigin: "0 0", transform: imgTf, mixBlendMode: "multiply", opacity: 0.9 }}>
          <Img src={staticFile("geo/relief.jpg")} style={{ position: "absolute", left: 0, top: 0, width: WW, height: WH }} />
        </div>
      </>)}
    <svg width={SW} height={SH} viewBox={`0 0 ${SW} ${SH}`} style={{ position: "absolute" }}>
      <defs>
        <marker id="ah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill={red} /></marker>
        <radialGradient id="mvig" cx="0.5" cy="0.47" r="0.75"><stop offset="0.5" stopColor="#000" stopOpacity={0} /><stop offset="1" stopColor="#000" stopOpacity={pol ? 0.45 : 0.7} /></radialGradient>
        <filter id="glw" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" /></filter>
      </defs>
      <g transform={tf}>
        {!pol && <g fill="none" stroke="rgba(255,255,255,0.55)" strokeWidth={sw * 0.8}>
          {countries.map((c, i) => <path key={i} d={path(c as never) ?? ""} />)}
        </g>}
        {(m.hl ?? []).map((id) => {
          const c = countries.find((x) => x.id === id);
          return c ? <path key={id} d={path(c as never) ?? ""} fill={`rgba(255,210,63,${0.25 + 0.15 * Math.sin(f / 6)})`} stroke="#ffd23f" strokeWidth={sw * 2.2} /> : null;
        })}
        {(m.glow ?? []).map((id) => {
          const c = countries.find((x) => x.id === id), gk = Math.min(1, f / 12);
          return c ? <g key={id}><path d={path(c as never) ?? ""} fill="none" stroke="#fff" strokeWidth={sw * 9 * gk} opacity={0.55 + 0.25 * Math.sin(f / 5)} filter="url(#glw)" />
            <path d={path(c as never) ?? ""} fill="none" stroke="#fff" strokeWidth={sw * 3.2} /></g> : null;
        })}
        {m.overlay && (OVERLAYS[m.overlay] ?? []).map((line, i) => (
          <path key={i} d={"M" + line.map(([lo, la]) => (proj([lo, la]) as number[]).join(" ")).join(" L")} fill="none" stroke={OVERLAY_COLOR[m.overlay!] ?? red}
                strokeWidth={sw * (m.overlay === "nile" ? 7 : 3)} strokeDasharray="1" pathLength={1} strokeDashoffset={1 - draw} strokeLinecap="round" />
        ))}
      </g>
      {(m.arrows ?? []).map(([a, b, c, d], i) => {
        const [x1, y1] = toScreen(a, b), [x2, y2] = toScreen(c, d);
        const g = ease(Math.min(1, Math.max(0, (f - 8 - i * 7) / 18)));
        const ex = x1 + (x2 - x1) * g, ey = y1 + (y2 - y1) * g;
        return <g key={i} opacity={g > 0 ? 1 : 0}>
          {pol && <line x1={x1} y1={y1} x2={ex} y2={ey} stroke="#fff" strokeWidth={24} strokeLinecap="round" />}
          <line x1={x1} y1={y1} x2={ex} y2={ey} stroke={red} strokeWidth={14} strokeLinecap="round" markerEnd="url(#ah)" /></g>;
      })}
      {(m.dots ?? []).map(([a, b], i) => {
        const [x, y] = toScreen(a, b), p = ((f + i * 9) % 30) / 30;
        return <g key={i}><circle cx={x} cy={y} r={10} fill={red} /><circle cx={x} cy={y} r={10 + p * 60} fill="none" stroke={red} strokeWidth={5} opacity={1 - p} /></g>;
      })}
      {(m.icons ?? []).map(([a, b, t], i) => {
        const [x, y] = toScreen(a, b), q = pop(Math.min(1, Math.max(0, (f - 10 - i * 6) / 10)));
        return <text key={i} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize={96} transform={`translate(${x} ${y}) scale(${q}) translate(${-x} ${-y})`}>{t}</text>;
      })}
      {(m.labels ?? []).map(([a, b, t], i) => {
        const [x, y] = toScreen(a, b), q = pop(Math.min(1, Math.max(0, (f - 6 - i * 5) / 9)));
        return <text key={i} x={x} y={y} textAnchor="middle" fontSize={pol ? 66 : 46} fontWeight={900} fill="#fff" stroke={pol ? "#1b1b1f" : "#06131f"}
                     strokeWidth={pol ? 13 : 10} paintOrder="stroke" fontFamily="'Avenir Next', Arial" letterSpacing={pol ? 4 : 3} opacity={q > 0 ? 1 : 0}
                     transform={`translate(${x} ${y}) scale(${q}) translate(${-x} ${-y})`}>{t}</text>;
      })}
      <rect width={SW} height={SH} fill="url(#mvig)" />
    </svg>
    </div>
  );
};
