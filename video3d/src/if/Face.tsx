// Ifverse 風のキャラ:黒い丸い頭+表情豊かな白い目+口。ふち取り(シール風)で背景から浮かせる
export type Eyes = "normal" | "shock" | "worried" | "smug" | "happy" | "squint" | "angry" | "glasses";
export type Mouth = "smile" | "o" | "flat" | "grin" | "wavy" | "none";

const Eye = ({ x, kind }: { x: number; kind: Eyes }) => {
  switch (kind) {
    case "shock":
      return <g><circle cx={x} cy={0} r={34} fill="#fff" /><circle cx={x} cy={0} r={14} fill="#111" /><circle cx={x} cy={0} r={22} fill="none" stroke="#111" strokeWidth={6} /></g>;
    case "worried":
      return <g><ellipse cx={x} cy={6} rx={26} ry={30} fill="#fff" /><circle cx={x} cy={14} r={12} fill="#111" />
        <path d={`M${x - 34} ${-38 + (x > 0 ? 14 : 0)} L${x + 34} ${-38 + (x > 0 ? 0 : 14)}`} stroke="#fff" strokeWidth={10} strokeLinecap="round" /></g>;
    case "smug":
      return <g><path d={`M${x - 30} 0 Q${x} -8 ${x + 30} 0 L${x + 26} 14 Q${x} 20 ${x - 26} 14 Z`} fill="#fff" /><circle cx={x + 8} cy={8} r={8} fill="#111" /></g>;
    case "happy":
      return <path d={`M${x - 28} 8 Q${x} -26 ${x + 28} 8`} stroke="#fff" strokeWidth={12} fill="none" strokeLinecap="round" />;
    case "squint":
      return <path d={x < 0 ? `M${x - 24} -18 L${x + 22} 0 L${x - 24} 18` : `M${x + 24} -18 L${x - 22} 0 L${x + 24} 18`} stroke="#fff" strokeWidth={12} fill="none" strokeLinecap="round" strokeLinejoin="round" />;
    case "angry":
      return <g><path d={`M${x - 30} -6 L${x + 30} ${x < 0 ? 10 : -22} L${x + 30} 20 L${x - 30} 20 Z`} fill="#fff" transform={x > 0 ? `scale(-1 1) translate(${-2 * x} 0)` : ""} /><circle cx={x} cy={8} r={9} fill="#111" /></g>;
    case "glasses":
      return <g><rect x={x - 38} y={-24} width={76} height={50} rx={14} fill="#bfe9ff" stroke="#e8f6ff" strokeWidth={6} />
        <path d={`M${x - 20} -12 L${x - 6} -18`} stroke="#fff" strokeWidth={6} /></g>;
    default:
      return <g><ellipse cx={x} cy={0} rx={24} ry={28} fill="#fff" /><circle cx={x + 4} cy={4} r={11} fill="#111" /></g>;
  }
};

const MouthShape = ({ kind }: { kind: Mouth }) => {
  switch (kind) {
    case "o": return <ellipse cx={0} cy={70} rx={20} ry={26} fill="#fff" />;
    case "flat": return <path d="M-26 72 L26 72" stroke="#fff" strokeWidth={10} strokeLinecap="round" />;
    case "grin": return <path d="M-40 58 Q0 108 40 58 Z" fill="#fff" />;
    case "wavy": return <path d="M-34 74 q11 -12 22 0 t22 0 t22 0" stroke="#fff" strokeWidth={8} fill="none" strokeLinecap="round" />;
    case "none": return null;
    default: return <path d="M-30 62 Q0 90 30 62" stroke="#fff" strokeWidth={10} fill="none" strokeLinecap="round" />;
  }
};

// 探偵の鹿撃ち帽(ツイード柄)と、肩までの赤茶の髪
const Hair = ({ color }: { color: string }) => (
  <path d="M-205 -40 Q-235 120 -170 210 L-120 200 Q-170 90 -150 -40 Z M205 -40 Q235 120 170 210 L120 200 Q170 90 150 -40 Z" fill={color} />
);
export const Hat = () => (
  <g>
    <path d="M-230 -70 Q-120 -40 0 -45 Q120 -40 230 -70 L210 -40 Q0 -10 -210 -40 Z" fill="#4a3520" />
    <path d="M-195 -60 Q-205 -250 0 -255 Q205 -250 195 -60 Q0 -30 -195 -60 Z" fill="#7a5a35" />
    {[-140, -70, 0, 70, 140].map((x) => <path key={x} d={`M${x} -250 Q${x * 1.1} -150 ${x * 1.05} -45`} stroke="#5e4427" strokeWidth={8} fill="none" />)}
    {[-200, -150, -100].map((y) => <path key={y} d={`M-190 ${y} Q0 ${y - 25} 190 ${y}`} stroke="#5e4427" strokeWidth={6} fill="none" />)}
    <path d="M-195 -60 Q0 -30 195 -60" stroke="#2d6a4f" strokeWidth={22} fill="none" />
    <circle cx={0} cy={-258} r={16} fill="#5e4427" />
  </g>
);
export const Lens = ({ x = 0, y = 0, r = 70, rot = -30 }: { x?: number; y?: number; r?: number; rot?: number }) => (
  <g transform={`translate(${x} ${y}) rotate(${rot})`}>
    <rect x={-12} y={r} width={24} height={r * 1.4} rx={10} fill="#5a3b1e" />
    <circle r={r} fill="rgba(200,235,255,0.25)" stroke="#d9a63a" strokeWidth={r * 0.2} />
    <path d={`M${-r * 0.5} ${-r * 0.3} Q${-r * 0.3} ${-r * 0.6} 0 ${-r * 0.6}`} stroke="#fff" strokeWidth={r * 0.1} fill="none" opacity={0.7} strokeLinecap="round" />
  </g>
);

// 頭と顔。r は頭の半径。rim はふち取りの色(右下にずらしたシール風)。detective で帽子と髪
// 博士のぼさぼさの白い髪
const SciHair = () => (
  <g fill="#f4f4f0">
    {[-170, -110, -50, 10, 70, 130].map((x, i) => <path key={x} d={`M${x} -150 q${20 + (i % 2) * 10} -${90 + (i % 3) * 25} ${60} 0 Z`} />)}
    <ellipse cx={-205} cy={-20} rx={55} ry={75} /><ellipse cx={205} cy={-20} rx={55} ry={75} />
  </g>
);

// 帽子(中折れ帽・キャップ)
const OtherHat = ({ kind }: { kind: string }) => kind === "fedora" ? (
  <g><ellipse cx={0} cy={-150} rx={280} ry={46} fill="#1d1d22" /><path d="M-160 -150 Q-170 -330 0 -320 Q170 -330 160 -150 Z" fill="#26262c" />
    <path d="M-160 -175 Q0 -150 160 -175 L160 -150 Q0 -128 -160 -150 Z" fill="#8a2b2b" /><path d="M-60 -315 Q0 -280 60 -315" stroke="#1d1d22" strokeWidth={14} fill="none" /></g>
) : (
  <g><path d="M-190 -110 Q-200 -300 0 -300 Q200 -300 190 -110 Z" fill="#e8332a" /><path d="M150 -120 Q330 -110 360 -70 Q250 -60 140 -90 Z" fill="#c62828" />
    <circle cx={0} cy={-298} r={16} fill="#c62828" /></g>
);

export const Head = ({ r = 200, eyes = "normal", mouth = "smile", rim = "#f2a65a", look = 0, detective = false, sci = false, hat, glint = -1 }:
  { r?: number; eyes?: Eyes; mouth?: Mouth; rim?: string; look?: number; detective?: boolean; sci?: boolean; hat?: string; glint?: number }) => {
  const k = r / 200;
  return (
    <g>
      {detective && <g transform={`scale(${k})`}><Hair color="#8c3b22" /></g>}
      <circle cx={10 * k} cy={8 * k} r={r + 10 * k} fill={rim} />
      <circle cx={0} cy={0} r={r} fill="#0f0f12" />
      <ellipse cx={-70 * k} cy={-90 * k} rx={40 * k} ry={22 * k} fill="rgba(255,255,255,0.08)" />
      <g transform={`translate(${look * 30 * k} ${-10 * k}) scale(${k})`}>
        <Eye x={-62} kind={eyes} /><Eye x={62} kind={eyes} />
        {eyes === "glasses" && <path d="M-24 0 L24 0" stroke="#e8f6ff" strokeWidth={6} />}
        <MouthShape kind={mouth} />
      </g>
      {detective && <g transform={`scale(${k})`}><Hat /></g>}
      {hat && <g transform={`scale(${k})`}><OtherHat kind={hat} /></g>}
      {(eyes === "glasses" || sci) && glint >= 0 && glint < 0.35 && (  /* めがねがピカーン */
        <g transform={`scale(${k}) translate(${look * 30} -10)`}>
          {[-62, 62].map((x) => <g key={x}><clipPath id={`gl${x}`}><circle cx={x} cy={0} r={46} /></clipPath>
            <rect x={x - 120 + glint * 680} y={-60} width={34} height={120} fill="#fff" opacity={0.9} transform={`skewX(-25)`} clipPath={`url(#gl${x})`} /></g>)}
          <path d={`M${80 + glint * 200} -40 l10 -26 l10 26 l26 10 l-26 10 l-10 26 l-10 -26 l-26 -10 Z`} fill="#fff" opacity={1 - glint * 2.5} />
        </g>)}
      {sci && <g transform={`scale(${k})`}><SciHair />
        <g transform={`translate(${look * 30} -10)`} fill="none" stroke="#d9a63a" strokeWidth={9}><circle cx={-62} cy={0} r={46} /><circle cx={62} cy={0} r={46} /><path d="M-16 0 L16 0" /></g></g>}
    </g>
  );
};

// 全身(小さめのショット用)。服はパーカー風
export const Body = ({ color = "#2f6fd6", rim = "#f2a65a", eyes = "normal" as Eyes, mouth = "smile" as Mouth, pose = "stand", step = 0, detective = false, sci = false,
  act, t = 0, hat, glint = -1, prop }:
  { color?: string; rim?: string; eyes?: Eyes; mouth?: Mouth; pose?: "stand" | "run" | "point" | "lens"; step?: number; detective?: boolean; sci?: boolean;
    act?: string; t?: number; hat?: string; glint?: number; prop?: string }) => {
  const sw = pose === "run" ? Math.sin(step) * 40 : 0;
  return (
    <g>
      <ellipse cx={0} cy={8} rx={110} ry={20} fill="rgba(0,0,0,0.35)" />
      <path d={`M-20 -170 L${-34 - sw} 0 M20 -170 L${34 + sw} 0`} stroke="#0f0f12" strokeWidth={30} strokeLinecap="round" />
      <path d={`M-20 -170 L${-34 - sw} 0 M20 -170 L${34 + sw} 0`} stroke={rim} strokeWidth={6} strokeLinecap="round" transform="translate(6 4)" opacity={0.6} />
      <rect x={-66} y={-380} width={132} height={220} rx={52} fill={color} />
      <rect x={-66} y={-380} width={132} height={220} rx={52} fill="url(#shadeR)" />
      <path d="M-18 -380 L0 -340 L18 -380" stroke="rgba(255,255,255,0.6)" strokeWidth={8} fill="none" />
      {detective && <path d="M-80 -370 L-110 -120 L110 -120 L80 -370 Z" fill={color} opacity={0.9} />}
      {detective && <rect x={-70} y={-250} width={140} height={22} fill="#3b2a1a" />}
      {sci && <><path d="M-78 -375 L-104 -120 L104 -120 L78 -375 Z" fill="#f4f4f0" /><path d="M-30 -380 L0 -300 L30 -380 M0 -300 L0 -130" stroke="#c9c9c2" strokeWidth={8} fill="none" />
        <rect x={30} y={-300} width={34} height={40} rx={6} fill="#4fd1c5" /></>}
      {act && (() => {  // 手振り(wave/think/shrug/hold/cheer)。holdはスマホ・マグを持つ
        const w = Math.sin(t * 9);
        const R = act === "wave" ? [150 + w * 30, -500] : act === "think" ? [30, -440] : act === "shrug" ? [150, -400 - w * 10] : act === "hold" ? [70, -430] : act === "cheer" ? [120 + w * 10, -560] : [92, -210];
        const L = act === "shrug" ? [-150, -400 - w * 10] : act === "cheer" ? [-120 - w * 10, -560] : [-92, -210];
        return <g><path d={`M-58 -340 L${L[0]} ${L[1]} M58 -340 L${R[0]} ${R[1]}`} stroke={color} strokeWidth={34} strokeLinecap="round" fill="none" />
          <circle cx={R[0]} cy={R[1]} r={22} fill="#0f0f12" /><circle cx={L[0]} cy={L[1]} r={22} fill="#0f0f12" />
          {act === "hold" && prop === "phone" && <g transform={`translate(${R[0] + 10} ${R[1] - 60})`}><rect x={-34} y={-60} width={68} height={120} rx={12} fill="#15161c" /><rect x={-28} y={-52} width={56} height={100} rx={8} fill="#5b8fd6" /></g>}
          {act === "hold" && prop === "mug" && <g transform={`translate(${R[0] + 16} ${R[1] - 30})`}><rect x={-30} y={-40} width={60} height={70} rx={10} fill="#f4f4f0" /><path d="M30 -25 Q60 -10 30 15" stroke="#f4f4f0" strokeWidth={10} fill="none" />
            {[0, 1].map((i) => <path key={i} d={`M${-10 + i * 20} -50 q10 -20 0 -40`} stroke="#fff" strokeWidth={5} fill="none" opacity={0.5 + 0.4 * Math.sin(t * 4 + i)} />)}</g>}
        </g>;
      })()}
      {!act && <path d={pose === "point" || pose === "lens" ? "M-58 -340 L-90 -220 M58 -340 L170 -400" : `M-58 -340 L${-92 + sw} -210 M58 -340 L${92 - sw} -210`} stroke={color} strokeWidth={34} strokeLinecap="round" fill="none" />}
      <g transform="translate(0 -500)"><Head r={120} eyes={eyes} mouth={mouth} rim={rim} detective={detective} sci={sci} hat={hat} glint={glint} /></g>
      {pose === "lens" && <Lens x={200} y={-470} r={60} rot={-20} />}
    </g>
  );
};
