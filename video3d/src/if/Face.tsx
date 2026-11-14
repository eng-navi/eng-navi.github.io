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

// 頭と顔。r は頭の半径。rim はふち取りの色(右下にずらしたシール風)
export const Head = ({ r = 200, eyes = "normal", mouth = "smile", rim = "#f2a65a", look = 0 }: { r?: number; eyes?: Eyes; mouth?: Mouth; rim?: string; look?: number }) => {
  const k = r / 200;
  return (
    <g>
      <circle cx={10 * k} cy={8 * k} r={r + 10 * k} fill={rim} />
      <circle cx={0} cy={0} r={r} fill="#0f0f12" />
      <ellipse cx={-70 * k} cy={-90 * k} rx={40 * k} ry={22 * k} fill="rgba(255,255,255,0.08)" />
      <g transform={`translate(${look * 30 * k} ${-10 * k}) scale(${k})`}>
        <Eye x={-62} kind={eyes} /><Eye x={62} kind={eyes} />
        {eyes === "glasses" && <path d="M-24 0 L24 0" stroke="#e8f6ff" strokeWidth={6} />}
        <MouthShape kind={mouth} />
      </g>
    </g>
  );
};

// 全身(小さめのショット用)。服はパーカー風
export const Body = ({ color = "#2f6fd6", rim = "#f2a65a", eyes = "normal" as Eyes, mouth = "smile" as Mouth, pose = "stand", step = 0 }:
  { color?: string; rim?: string; eyes?: Eyes; mouth?: Mouth; pose?: "stand" | "run" | "point"; step?: number }) => {
  const sw = pose === "run" ? Math.sin(step) * 40 : 0;
  return (
    <g>
      <ellipse cx={0} cy={8} rx={110} ry={20} fill="rgba(0,0,0,0.35)" />
      <path d={`M-20 -170 L${-34 - sw} 0 M20 -170 L${34 + sw} 0`} stroke="#0f0f12" strokeWidth={30} strokeLinecap="round" />
      <path d={`M-20 -170 L${-34 - sw} 0 M20 -170 L${34 + sw} 0`} stroke={rim} strokeWidth={6} strokeLinecap="round" transform="translate(6 4)" opacity={0.6} />
      <rect x={-66} y={-380} width={132} height={220} rx={52} fill={color} />
      <rect x={-66} y={-380} width={132} height={220} rx={52} fill="url(#shadeR)" />
      <path d="M-18 -380 L0 -340 L18 -380" stroke="rgba(255,255,255,0.6)" strokeWidth={8} fill="none" />
      <path d={pose === "point" ? "M-58 -340 L-90 -220 M58 -340 L170 -400" : `M-58 -340 L${-92 + sw} -210 M58 -340 L${92 - sw} -210`} stroke={color} strokeWidth={34} strokeLinecap="round" fill="none" />
      <g transform="translate(0 -500)"><Head r={120} eyes={eyes} mouth={mouth} rim={rim} /></g>
    </g>
  );
};
