// Ifverse 風の棒人間:黒い丸い頭+色つきの体。頭の上に数字のバッジ(レベルなど)
type Props = { x: number; y: number; s?: number; color?: string; badge?: string; pose?: "stand" | "sit" | "lie" | "think"; bob?: number; flip?: boolean };

export const Stickman = ({ x, y, s = 1, color = "#2f6fd6", badge, pose = "stand", bob = 0, flip = false }: Props) => {
  const lie = pose === "lie";
  return (
    <g transform={`translate(${x} ${y + bob}) scale(${flip ? -s : s} ${s}) rotate(${lie ? -90 : 0})`}>
      {/* 影 */}
      {!lie && <ellipse cx={0} cy={6} rx={70} ry={14} fill="rgba(0,0,0,0.18)" />}
      {/* 脚 */}
      {pose === "sit" ? (
        <path d="M-18 -120 L-20 -60 L40 -60 L40 0 M18 -120 L20 -60 L70 -60 L70 0" stroke="#1d1d22" strokeWidth={20} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      ) : (
        <path d="M-16 -120 L-26 0 M16 -120 L26 0" stroke="#1d1d22" strokeWidth={22} fill="none" strokeLinecap="round" />
      )}
      {/* 体(服) */}
      <rect x={-44} y={-250} width={88} height={140} rx={34} fill={color} />
      {/* 腕 */}
      {pose === "think" ? (
        <path d="M-40 -220 L-70 -150 M40 -220 L60 -180 L30 -280" stroke={color} strokeWidth={22} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      ) : (
        <path d="M-40 -225 L-62 -130 M40 -225 L62 -130" stroke={color} strokeWidth={22} fill="none" strokeLinecap="round" />
      )}
      {/* 頭 */}
      <circle cx={0} cy={-320} r={70} fill="#141418" />
      <circle cx={-22} cy={-338} r={14} fill="rgba(255,255,255,0.12)" />
      {/* バッジ */}
      {badge && (
        <g transform={`rotate(${lie ? 90 : 0} 0 -440) scale(${flip ? -1 : 1} 1)`}>
          <rect x={-58} y={-482} width={116} height={64} rx={32} fill="#f2b33d" stroke="#1d1d22" strokeWidth={6} />
          <text x={0} y={-438} textAnchor="middle" fontSize={40} fontWeight={800} fontFamily="Arial" fill="#1d1d22">{badge}</text>
        </g>
      )}
    </g>
  );
};
