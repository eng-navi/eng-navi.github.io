import React from "react";
import { useVideoConfig } from "remotion";

// Vox 風のコラージュ。紙の背景+光の筋の上に、白フチと影のついた切り抜きが少し回転しながら貼られていく
// 人物は似顔絵(写真は使わない)。座標は 1080×1920 の画面
const W = 1080, H = 1920;
const SERIF = "Georgia, 'Times New Roman', serif";
const SANS = "'Avenir Next', 'Helvetica Neue', Arial, sans-serif";

export type CItem = {
  kind: "person" | "figure" | "books" | "garage" | "box" | "bank" | "money" | "chart" | "doc" | "news" | "label" | "stamp" | "coin" | "house" | "arrow";
  x: number; y: number; w?: number; rot?: number; at?: number;  // at:出てくるまでのフレーム数
  text?: string; who?: string; color?: string; x2?: number; y2?: number;
};
export type CollageSpec = { bg?: "grid" | "parchment" | "gray"; items: CItem[]; push?: number };

const ease = (x: number) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
const pop = (x: number) => (x <= 0 ? 0 : x >= 1 ? 1 : 1 + 2.2 * Math.pow(x - 1, 3) + 1.2 * Math.pow(x - 1, 2));

// 白フチ+影の切り抜き台紙
const Cut = ({ w, h, children, fill = "#fff" }: { w: number; h: number; children: React.ReactNode; fill?: string }) => (
  <g>
    <rect x={-w / 2 + 14} y={-h / 2 + 20} width={w} height={h} rx={10} fill="rgba(0,0,0,0.28)" filter="url(#csh)" />
    <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={10} fill={fill} />
    {children}
  </g>
);
const Tape = ({ x, y, r = -12 }: { x: number; y: number; r?: number }) => (
  <rect x={x - 55} y={y - 18} width={110} height={36} fill="rgba(240,226,180,0.85)" transform={`rotate(${r} ${x} ${y})`} />
);

// 似顔絵(写真ではないイラスト)
const Face = ({ who }: { who?: string }) => {
  if (who === "bezos") return (
    <g>
      <path d="M-170 300 Q0 200 170 300 L190 420 L-190 420 Z" fill="#22252b" />
      <path d="M-40 230 L0 300 L40 230 Z" fill="#f4f4f4" /><path d="M-12 250 L0 330 L12 250 Z" fill="#3b5ea8" />
      <ellipse cx={0} cy={40} rx={150} ry={175} fill="#e9b892" />
      <ellipse cx={-150} cy={50} rx={22} ry={38} fill="#dca37c" /><ellipse cx={150} cy={50} rx={22} ry={38} fill="#dca37c" />
      <ellipse cx={-40} cy={-90} rx={70} ry={30} fill="#fff" opacity={0.35} />
      <path d="M-85 -10 Q-55 -40 -25 -12" stroke="#5b3a29" strokeWidth={10} fill="none" strokeLinecap="round" />
      <path d="M25 -12 Q55 -40 85 -10" stroke="#5b3a29" strokeWidth={10} fill="none" strokeLinecap="round" />
      <path d="M-80 20 Q-55 0 -30 20" stroke="#2a1d16" strokeWidth={9} fill="none" strokeLinecap="round" />
      <path d="M30 20 Q55 0 80 20" stroke="#2a1d16" strokeWidth={9} fill="none" strokeLinecap="round" />
      <path d="M-10 40 Q0 80 14 80" stroke="#c68b67" strokeWidth={7} fill="none" />
      <path d="M-80 110 Q0 190 80 110 Z" fill="#fff" stroke="#7a3b2b" strokeWidth={8} />
    </g>
  );
  return (  // 白い人形(実在しない人物)
    <g>
      <path d="M-160 300 Q0 200 160 300 L180 420 L-180 420 Z" fill="#e4e4e6" stroke="#9a9aa0" strokeWidth={8} />
      <ellipse cx={0} cy={40} rx={140} ry={160} fill="#f4f4f5" stroke="#9a9aa0" strokeWidth={8} />
      <ellipse cx={-40} cy={-40} rx={60} ry={34} fill="#fff" />
      <ellipse cx={30} cy={90} rx={120} ry={90} fill="#000" opacity={0.05} />
    </g>
  );
};

const Item = ({ it, k }: { it: CItem; k: number }) => {
  const w = it.w ?? 360;
  const t = it.text ?? "";
  switch (it.kind) {
    case "person": return <Cut w={w} h={w * 1.25}><g transform={`translate(0 ${-w * 0.05}) scale(${w / 460})`}><Face who={it.who} /></g></Cut>;
    case "figure": return <g transform={`scale(${w / 460})`}><Face who="" /></g>;
    case "books": return <Cut w={w} h={w * 0.8}>{[0, 1, 2, 3].map((i) => <rect key={i} x={-w * 0.36} y={w * 0.22 - i * w * 0.14} width={w * 0.72 - i * 12} height={w * 0.12} rx={6}
      fill={["#c0392b", "#2c6fbb", "#d4a017", "#2f8f5b"][i]} />)}<text y={-w * 0.3} textAnchor="middle" fontFamily={SERIF} fontSize={w * 0.13} fontWeight={700} fill="#222">{t || "BOOKS"}</text></Cut>;
    case "garage": return <Cut w={w} h={w * 0.85}><path d={`M${-w * 0.4} ${w * 0.3} L${-w * 0.4} ${-w * 0.05} L0 ${-w * 0.3} L${w * 0.4} ${-w * 0.05} L${w * 0.4} ${w * 0.3} Z`} fill="#c9a77a" />
      <rect x={-w * 0.26} y={0} width={w * 0.52} height={w * 0.3} fill="#8a6a4c" />{[0, 1, 2].map((i) => <line key={i} x1={-w * 0.26} x2={w * 0.26} y1={w * 0.08 + i * w * 0.08} y2={w * 0.08 + i * w * 0.08} stroke="#6d523a" strokeWidth={6} />)}</Cut>;
    case "box": return <Cut w={w} h={w * 0.8}><path d={`M${-w * 0.32} ${-w * 0.12} L0 ${-w * 0.26} L${w * 0.32} ${-w * 0.12} L${w * 0.32} ${w * 0.26} L0 ${w * 0.36} L${-w * 0.32} ${w * 0.26} Z`} fill="#c8955a" />
      <path d={`M0 ${-w * 0.0} L0 ${w * 0.36} M${-w * 0.32} ${-w * 0.12} L0 0 L${w * 0.32} ${-w * 0.12}`} stroke="#9c6f3d" strokeWidth={6} fill="none" />
      <text x={-w * 0.16} y={w * 0.16} textAnchor="middle" fontFamily={SANS} fontSize={w * 0.09} fontWeight={900} fill="#5c3f1f">{t}</text></Cut>;
    case "bank": return <Cut w={w} h={w * 0.85}><path d={`M${-w * 0.38} ${-w * 0.12} L0 ${-w * 0.34} L${w * 0.38} ${-w * 0.12} Z`} fill="#556070" />
      {[-0.27, -0.09, 0.09, 0.27].map((p) => <rect key={p} x={w * p - w * 0.04} y={-w * 0.1} width={w * 0.08} height={w * 0.34} fill="#8a96a8" />)}<rect x={-w * 0.4} y={w * 0.24} width={w * 0.8} height={w * 0.07} fill="#556070" />
      <text y={-w * 0.17} textAnchor="middle" fontFamily={SERIF} fontSize={w * 0.08} fontWeight={700} fill="#fff">BANK</text></Cut>;
    case "money": return <g>{[0, 1, 2].map((i) => <g key={i} transform={`translate(${i * 18} ${-i * 22}) rotate(${-8 + i * 6})`}><rect x={-w / 2} y={-w * 0.22} width={w} height={w * 0.44} rx={8} fill="#7fbf7a" stroke="#3d7a3a" strokeWidth={6} filter="url(#csh2)" />
      <circle r={w * 0.13} fill="#5c9c58" /><text y={w * 0.06} textAnchor="middle" fontFamily={SERIF} fontSize={w * 0.18} fontWeight={700} fill="#e8f5e6">$</text></g>)}</g>;
    case "coin": return <g><circle r={w / 2} fill="#d9a63a" filter="url(#csh2)" /><circle r={w * 0.42} fill="#f2c45a" stroke="#b9862a" strokeWidth={6} />
      <text y={w * 0.13} textAnchor="middle" fontFamily={SERIF} fontSize={w * 0.4} fontWeight={700} fill="#b9862a">$</text></g>;
    case "house": return <Cut w={w} h={w * 0.85}><path d={`M${-w * 0.32} ${-w * 0.02} L0 ${-w * 0.3} L${w * 0.32} ${-w * 0.02} Z`} fill="#d35400" /><rect x={-w * 0.25} y={-w * 0.02} width={w * 0.5} height={w * 0.3} fill="#f0d9b5" />
      <rect x={-w * 0.06} y={w * 0.1} width={w * 0.12} height={w * 0.18} fill="#8a5a3c" /></Cut>;
    case "chart": return <Cut w={w} h={w * 0.75}>{[0, 1, 2, 3].map((i) => <line key={i} x1={-w * 0.4} x2={w * 0.4} y1={-w * 0.22 + i * w * 0.14} y2={-w * 0.22 + i * w * 0.14} stroke="#e3e3e3" strokeWidth={4} />)}
      <polyline points={[...Array(8)].map((_, i) => `${-w * 0.38 + i * w * 0.108},${w * 0.24 - Math.pow(1.45, i) * w * 0.022 * Math.min(1, k * 1.4)}`).join(" ")} fill="none" stroke={it.color ?? "#2fa36b"} strokeWidth={12} strokeLinecap="round" strokeLinejoin="round" />
      {t && <text y={-w * 0.27} textAnchor="middle" fontFamily={SANS} fontSize={w * 0.09} fontWeight={900} fill="#222">{t}</text>}</Cut>;
    case "doc": return <Cut w={w} h={w * 1.25} fill="#fbf8f0">{[...Array(7)].map((_, i) => <rect key={i} x={-w * 0.36} y={-w * 0.25 + i * w * 0.11} width={w * (i % 3 === 2 ? 0.45 : 0.72)} height={w * 0.03} fill="#c9c3b6" />)}
      <text y={-w * 0.4} textAnchor="middle" fontFamily={SERIF} fontSize={w * 0.11} fontWeight={700} fill="#222">{t}</text></Cut>;
    case "news": return <Cut w={w} h={w * 0.95} fill="#efe9dc"><text y={-w * 0.32} textAnchor="middle" fontFamily={SERIF} fontSize={w * 0.075} fill="#333" letterSpacing={2}>THE DAILY NEWS</text>
      <line x1={-w * 0.42} x2={w * 0.42} y1={-w * 0.27} y2={-w * 0.27} stroke="#333" strokeWidth={3} /><text y={-w * 0.13} textAnchor="middle" fontFamily={SERIF} fontSize={w * 0.1} fontWeight={700} fill="#111">{t}</text>
      {[...Array(5)].map((_, i) => <rect key={i} x={-w * 0.42} y={-w * 0.02 + i * w * 0.08} width={w * 0.84} height={w * 0.025} fill="#bdb6a6" />)}</Cut>;
    case "label": return <g><rect x={-w / 2 + 10} y={-50 + 12} width={w} height={100} fill="rgba(0,0,0,0.3)" filter="url(#csh)" /><rect x={-w / 2} y={-50} width={w} height={100} fill="#111" />
      <rect x={-w / 2 + 14} y={-34} width={(w - 28) * Math.min(1, k * 1.3)} height={68} fill={it.color ?? "#ffd23f"} />
      <text y={22} textAnchor="middle" fontFamily={SANS} fontSize={60} fontWeight={900} fill="#111" letterSpacing={2}>{t}</text></g>;
    case "stamp": return <g opacity={0.92}><rect x={-w / 2} y={-55} width={w} height={110} rx={10} fill="none" stroke="#d62828" strokeWidth={10} />
      <text y={24} textAnchor="middle" fontFamily={SANS} fontSize={66} fontWeight={900} fill="#d62828" letterSpacing={6}>{t}</text></g>;
    case "arrow": {
      const x2 = (it.x2 ?? it.x + 200) - it.x, y2 = ((it.y2 ?? it.y) - it.y) * 0.82, g = Math.min(1, k * 1.2);
      return <g><line x1={0} y1={0} x2={x2 * g} y2={y2 * g} stroke="#d62828" strokeWidth={16} strokeLinecap="round" markerEnd="url(#cah)" /></g>;
    }
  }
  return null;
};

export const CollageView = ({ c, f }: { c: CollageSpec; f: number }) => {
  const { fps } = useVideoConfig();
  const still = fps < 5;  // カバー画像(1秒1コマ)では全部出した状態で描く
  const zoom = 1 + (c.push ?? 0.06) * Math.min(1, f / 90);
  const bg = c.bg ?? "grid";
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute" }}>
      <defs>
        <filter id="csh" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="10" /></filter>
        <filter id="csh2" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="10" dy="14" stdDeviation="8" floodOpacity="0.3" /></filter>
        <filter id="paper"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves={3} seed={3} /><feColorMatrix values="0 0 0 0 0.4  0 0 0 0 0.35  0 0 0 0 0.3  0 0 0 0.12 0" /></filter>
        <marker id="cah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="3.5" markerHeight="3.5" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#d62828" /></marker>
        <linearGradient id="ray" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#fff" stopOpacity={0.35} /><stop offset="1" stopColor="#fff" stopOpacity={0} /></linearGradient>
      </defs>
      <g transform={`translate(${W / 2} ${H / 2}) scale(${zoom}) translate(${-W / 2} ${-H / 2})`}>
        <rect width={W} height={H} fill={bg === "parchment" ? "#e9dcc0" : bg === "gray" ? "#cfcfcf" : "#f6f6f2"} />
        {bg === "grid" && [...Array(40)].map((_, i) => <g key={i}><line x1={i * 54} y1={0} x2={i * 54} y2={H} stroke="#dfe3e8" strokeWidth={2} /><line x1={0} y1={i * 54} x2={W} y2={i * 54} stroke="#dfe3e8" strokeWidth={2} /></g>)}
        <rect width={W} height={H} filter="url(#paper)" />
        <polygon points="-200,0 380,0 1300,1920 700,1920" fill="url(#ray)" />
        {c.items.map((it, i) => {
          const at = it.at ?? 4 + i * 7;
          const k = still ? 1 : ease((f - at) / 9);
          const p = still ? 1 : pop((f - at) / 9);
          if (k <= 0) return null;
          const r = (it.rot ?? 0) + (1 - k) * 14;
          const dy = (1 - k) * -120;
          const yy = 300 + (it.y - 300) * 0.82;  // 下の字幕と重ならないよう、少し上に寄せる
          return <g key={i} transform={`translate(${it.x} ${yy + dy}) rotate(${it.kind === "arrow" ? 0 : r}) scale(${it.kind === "arrow" ? 1 : 0.6 + 0.4 * p})`} opacity={Math.min(1, k * 2)}>
            <Item it={it} k={k} />
            {(it.kind === "person" || it.kind === "doc" || it.kind === "news") && <Tape x={0} y={-(it.w ?? 360) * (it.kind === "person" ? 0.62 : 0.6)} />}
          </g>;
        })}
      </g>
      <rect width={W} height={H} fill="none" stroke="#000" strokeOpacity={0.15} strokeWidth={120} filter="url(#csh)" />
    </svg>
  );
};
