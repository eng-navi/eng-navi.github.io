// 背景(コードで描く。色・光・奥行きで安っぽく見えないように)
const W = 1080, H = 1920;

export const Office = ({ dusk = true }: { dusk?: boolean }) => (
  <g>
    <defs>
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor={dusk ? "#3b3f6e" : "#9cc6e8"} />
        <stop offset="0.6" stopColor={dusk ? "#e58a6a" : "#d8ecf7"} />
        <stop offset="1" stopColor={dusk ? "#f6c98b" : "#eef6fb"} />
      </linearGradient>
    </defs>
    <rect width={W} height={H} fill="#2a2d3a" />
    {/* 大きな窓と街 */}
    <rect x={60} y={260} width={960} height={760} fill="url(#sky)" />
    {[80, 210, 330, 470, 600, 740, 860].map((x, i) => (
      <rect key={x} x={x} y={620 - (i % 3) * 90} width={110} height={400 + (i % 3) * 90} fill={dusk ? "#2b2f4f" : "#7a93ad"} opacity={0.9} />
    ))}
    {[0, 1, 2].map((i) => <rect key={i} x={60 + i * 320} y={260} width={14} height={760} fill="#1e2029" />)}
    <rect x={60} y={1010} width={960} height={16} fill="#1e2029" />
    {/* 床と机 */}
    <rect x={0} y={1180} width={W} height={H - 1180} fill="#3a3d4b" />
    <rect x={120} y={1230} width={840} height={36} rx={8} fill="#c9a77c" />
    <rect x={160} y={1266} width={24} height={240} fill="#8a6e4f" />
    <rect x={896} y={1266} width={24} height={240} fill="#8a6e4f" />
    <rect x={560} y={1090} width={260} height={150} rx={12} fill="#20232c" />
    <rect x={574} y={1104} width={232} height={122} rx={6} fill={dusk ? "#7fb6ff" : "#bfe0ff"} opacity={0.85} />
  </g>
);

export const Bedroom = () => (
  <g>
    <defs>
      <radialGradient id="lamp" cx="0.75" cy="0.55" r="0.5">
        <stop offset="0" stopColor="#f7d79a" stopOpacity={0.55} />
        <stop offset="1" stopColor="#f7d79a" stopOpacity={0} />
      </radialGradient>
    </defs>
    <rect width={W} height={H} fill="#1d2140" />
    <rect x={120} y={300} width={360} height={440} fill="#2c3466" />
    <circle cx={360} cy={420} r={50} fill="#f4f1d0" />
    {[[170, 380], [240, 560], [420, 620], [200, 680]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r={5} fill="#f4f1d0" />)}
    <rect x={120} y={300} width={360} height={440} fill="none" stroke="#141733" strokeWidth={16} />
    <rect x={0} y={1180} width={W} height={H - 1180} fill="#262b52" />
    {/* ベッド */}
    <rect x={140} y={1080} width={800} height={160} rx={30} fill="#e9e3d6" />
    <rect x={140} y={1180} width={800} height={200} rx={20} fill="#5f6fb0" />
    <rect x={160} y={1040} width={220} height={90} rx={40} fill="#ffffff" />
    {/* ランプ */}
    <rect x={820} y={860} width={20} height={220} fill="#3b3f63" />
    <path d="M760 860 L900 860 L870 780 L790 780 Z" fill="#f2c776" />
    <rect width={W} height={H} fill="url(#lamp)" />
  </g>
);

export const Lab = () => (
  <g>
    <defs>
      <linearGradient id="lab" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#0f3b4a" />
        <stop offset="1" stopColor="#1b6d7c" />
      </linearGradient>
    </defs>
    <rect width={W} height={H} fill="url(#lab)" />
    {[...Array(9)].map((_, i) => <circle key={i} cx={120 + i * 110} cy={300 + (i % 2) * 60} r={6} fill="#7fe3e8" opacity={0.5} />)}
    {/* 脳のアイコン */}
    <g transform="translate(540 760)" opacity={0.95}>
      <circle cx={0} cy={0} r={260} fill="#ffffff10" stroke="#7fe3e8" strokeWidth={6} />
      <path d="M-120 -40 C-160 -140 -40 -190 0 -120 C40 -190 160 -140 120 -40 C200 20 120 140 40 110 C20 170 -20 170 -40 110 C-120 140 -200 20 -120 -40 Z" fill="#f29bb5" stroke="#1d1d22" strokeWidth={8} />
      <path d="M0 -120 L0 120 M-70 -60 C-40 -20 -90 20 -50 60 M70 -60 C40 -20 90 20 50 60" stroke="#1d1d22" strokeWidth={6} fill="none" />
    </g>
    <rect x={0} y={1180} width={W} height={H - 1180} fill="#0b2a35" />
  </g>
);
