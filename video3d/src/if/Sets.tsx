import React from "react";
// 背景と物のアップ(インサート)。暗めの色+スポットライト+ぼかしで奥行きを出す
const W = 1080, H = 1920;

export const Backdrop = ({ kind, blur = 0 }: { kind: string; blur?: number }) => {
  const sets: Record<string, React.ReactElement> = {
    room: (
      <g>
        <rect width={W} height={H} fill="#1c2033" />
        <rect x={620} y={300} width={360} height={560} fill="#e9946a" opacity={0.9} />
        <rect x={620} y={300} width={360} height={560} fill="url(#dusk)" />
        {[0, 1].map((i) => <rect key={i} x={620 + i * 180} y={300} width={12} height={560} fill="#14172a" />)}
        <rect x={0} y={1250} width={W} height={H - 1250} fill="#141726" />
        <rect x={60} y={1050} width={360} height={30} rx={8} fill="#6b5240" />
      </g>
    ),
    street: (
      <g>
        <rect width={W} height={H} fill="url(#sunset)" />
        <circle cx={760} cy={900} r={160} fill="#ffe9b8" opacity={0.9} />
        {[[0, 1080, 220], [180, 1000, 160], [760, 1040, 260], [920, 960, 200]].map(([x, y, w], i) => <rect key={i} x={x} y={y} width={w} height={H} fill="#3a2d4a" opacity={0.8} />)}
        <rect x={0} y={1300} width={W} height={H - 1300} fill="#2a2235" />
        <path d="M540 1300 L480 1920 L600 1920 Z" fill="#f4e3c0" opacity={0.25} />
      </g>
    ),
    bank: (
      <g>
        <rect width={W} height={H} fill="#13261f" />
        {[...Array(5)].map((_, i) => <rect key={i} x={80 + i * 200} y={380} width={60} height={760} fill="#1e3a30" />)}
        <rect x={0} y={1140} width={W} height={60} fill="#2c5244" />
        <rect x={0} y={1200} width={W} height={H - 1200} fill="#0e1c17" />
        <text x={540} y={330} textAnchor="middle" fontSize={70} fontWeight={900} fill="#d7b25a" fontFamily="Georgia" letterSpacing={12}>BANK</text>
      </g>
    ),
    office: (
      <g>
        <rect width={W} height={H} fill="#1d2a38" />
        {[0, 1, 2].map((i) => <rect key={i} x={90 + i * 320} y={360} width={260} height={420} fill="#9cc3d9" opacity={0.35} />)}
        <rect x={0} y={1180} width={W} height={H - 1180} fill="#16202b" />
        <rect x={40} y={1080} width={1000} height={40} rx={10} fill="#8a6a4c" />
        <rect x={700} y={900} width={240} height={170} rx={12} fill="#0f141b" /><rect x={715} y={915} width={210} height={140} fill="#3a6ea5" opacity={0.7} />
      </g>
    ),
    bedroom: (
      <g>
        <rect width={W} height={H} fill="#141a33" />
        <rect x={620} y={300} width={340} height={480} fill="#0b1026" /><circle cx={820} cy={460} r={70} fill="#f4ecc8" opacity={0.85} />
        <rect x={0} y={1300} width={W} height={H - 1300} fill="#10142a" />
        <rect x={80} y={1180} width={640} height={160} rx={30} fill="#3d4a8a" /><rect x={100} y={1130} width={180} height={80} rx={30} fill="#e8e4f4" />
      </g>
    ),
    lab: (
      <g>
        <rect width={W} height={H} fill="#10262c" />
        {[...Array(4)].map((_, i) => <rect key={i} x={80} y={420 + i * 170} width={920} height={14} fill="#2b4d55" />)}
        {[...Array(7)].map((_, i) => <rect key={i} x={120 + i * 125} y={340 + (i % 4) * 170} width={50} height={80} rx={12} fill={["#4fd1c5", "#f6ad55", "#9f7aea"][i % 3]} opacity={0.7} />)}
        <rect x={0} y={1220} width={W} height={H - 1220} fill="#0b1c20" />
      </g>
    ),
    ocean: (
      <g>
        <rect width={W} height={H} fill="url(#sea)" />
        <path d="M0 1700 Q270 1640 540 1690 T1080 1670 L1080 1920 L0 1920 Z" fill="#05121d" />
        {[120, 380, 760, 960].map((x, i) => <path key={i} d={`M${x} 1700 q-20 -${120 + i * 40} 10 -${220 + i * 50}`} stroke="#0f5132" strokeWidth={18} fill="none" strokeLinecap="round" />)}
      </g>
    ),
    dark: (
      <g>
        <rect width={W} height={H} fill="#0d0f18" />
        <polygon points="420,0 660,0 900,1600 180,1600" fill="#fff" opacity={0.06} />
        <ellipse cx={540} cy={1560} rx={360} ry={70} fill="#fff" opacity={0.06} />
      </g>
    ),
  };
  return <g style={{ filter: blur ? `blur(${blur}px)` : undefined }}>{sets[kind] ?? sets.dark}</g>;
};

export const Defs = () => (
  <defs>
    <linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#3b3f6e" stopOpacity={0.6} /><stop offset="1" stopColor="#f6c98b" stopOpacity={0} /></linearGradient>
    <linearGradient id="sunset" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#3d3566" /><stop offset="0.55" stopColor="#e5866a" /><stop offset="1" stopColor="#f7c98e" /></linearGradient>
    <linearGradient id="shadeR" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#fff" stopOpacity={0.15} /><stop offset="0.6" stopColor="#000" stopOpacity={0} /><stop offset="1" stopColor="#000" stopOpacity={0.35} /></linearGradient>
    <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1b8ab0" /><stop offset="0.45" stopColor="#0b4f74" /><stop offset="1" stopColor="#031a2c" /></linearGradient>
    <radialGradient id="vig" cx="0.5" cy="0.5" r="0.75"><stop offset="0.55" stopColor="#000" stopOpacity={0} /><stop offset="1" stopColor="#000" stopOpacity={0.75} /></radialGradient>
    <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={5} /><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.07 0" /></filter>
  </defs>
);

// 海の動き:ゆれる光の筋、のぼる泡、ただよう粒
export const OceanFX = ({ t }: { t: number }) => (
  <g>
    {[0, 1, 2, 3, 4].map((i) => {
      const x = 120 + i * 220 + Math.sin(t * 0.8 + i) * 40;
      return <polygon key={i} points={`${x - 30},0 ${x + 30},0 ${x + 160},1400 ${x - 60},1400`} fill="#bfefff" opacity={0.06 + 0.03 * Math.sin(t * 1.3 + i * 2)} />;
    })}
    {[...Array(14)].map((_, i) => {
      const x = (i * 157) % 1080 + Math.sin(t * 2 + i) * 14, y = 1800 - ((t * (60 + (i % 4) * 25) + i * 140) % 1800);
      return <circle key={i} cx={x} cy={y} r={6 + (i % 3) * 5} fill="none" stroke="#dff7ff" strokeWidth={3} opacity={0.5} />;
    })}
    {[...Array(24)].map((_, i) => <circle key={`p${i}`} cx={(i * 263 + t * 12) % 1080} cy={(i * 331 + Math.sin(t + i) * 20) % 1600} r={2.5} fill="#e8fbff" opacity={0.35} />)}
  </g>
);

// 物のアップ
export const Insert = ({ kind, value, t }: { kind: string; value?: string; t: number }) => {
  if (kind === "coin") {
    const spin = Math.cos(t * 6);
    return (
      <g transform="translate(540 900)">
        <ellipse cx={0} cy={330} rx={260} ry={40} fill="rgba(0,0,0,0.4)" />
        <g transform={`scale(${Math.max(0.15, Math.abs(spin))} 1)`}>
          <circle r={260} fill="#d9a63a" /><circle r={225} fill="#f2c45a" stroke="#b9862a" strokeWidth={10} />
          <text y={70} textAnchor="middle" fontSize={210} fontWeight={900} fill="#b9862a" fontFamily="Georgia">$</text>
        </g>
        {value && <text x={0} y={-330} textAnchor="middle" fontSize={150} fontWeight={900} fill="#f2b33d" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "chart") {
    const n = Math.min(1, t / 1.2);
    const pts = [...Array(21)].map((_, i) => [140 + i * 40, 1500 - Math.pow(2, i / 2.2) * 2.2]).filter((_, i) => i / 20 <= n);
    return (
      <g>
        <rect x={100} y={500} width={880} height={1060} rx={30} fill="#f7f1e3" />
        {[...Array(6)].map((_, i) => <line key={i} x1={140} y1={600 + i * 180} x2={940} y2={600 + i * 180} stroke="#d8cfbb" strokeWidth={3} />)}
        <polyline points={pts.map((p) => p.join(",")).join(" ")} fill="none" stroke="#2fa36b" strokeWidth={18} strokeLinecap="round" strokeLinejoin="round" />
        <text x={540} y={590} textAnchor="middle" fontSize={64} fontWeight={900} fill="#1d1d22" fontFamily="Arial">{value ?? ""}</text>
      </g>
    );
  }
  if (kind === "phone") {
    return (
      <g transform="translate(540 1000) rotate(-8)">
        <rect x={-230} y={-430} width={460} height={860} rx={60} fill="#15161c" />
        <rect x={-200} y={-390} width={400} height={780} rx={36} fill="#22314a" />
        <text y={-150} textAnchor="middle" fontSize={44} fill="#9fb3d1" fontFamily="Arial" fontWeight={700}>BALANCE</text>
        <text y={-40} textAnchor="middle" fontSize={92} fill="#fff" fontFamily="Arial" fontWeight={900}>{value}</text>
        <rect x={-150} y={60} width={300} height={90} rx={45} fill="#2fa36b" /><text y={120} textAnchor="middle" fontSize={44} fill="#fff" fontFamily="Arial" fontWeight={800}>+ INTEREST</text>
      </g>
    );
  }
  if (kind === "brain") {
    const pulse = 0.5 + 0.5 * Math.sin(t * 8);
    return (
      <g transform="translate(540 960)">
        <ellipse cx={0} cy={0} rx={330} ry={260} fill="#f2a7b8" stroke="#c46a82" strokeWidth={14} />
        <path d="M-250 -60 Q-150 -170 -40 -80 T180 -90 M-260 70 Q-120 -10 0 80 T250 40 M0 -250 Q-40 0 20 250" fill="none" stroke="#c46a82" strokeWidth={12} strokeLinecap="round" />
        {[[-180, -120], [120, -40], [-60, 120], [200, 110], [-220, 40]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r={20 + 14 * pulse} fill="#fff6a8" opacity={0.4 + 0.6 * ((pulse + i * 0.3) % 1)} />)}
        {value && <text y={-340} textAnchor="middle" fontSize={96} fontWeight={900} fill="#f2b33d" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "clock") {
    const a = t * 240;
    return (
      <g transform="translate(540 980)">
        <circle r={300} fill="#fbf7ee" stroke="#e0533c" strokeWidth={26} />
        {[...Array(12)].map((_, i) => <line key={i} x1={0} y1={-250} x2={0} y2={-220} stroke="#1d1d22" strokeWidth={10} transform={`rotate(${i * 30})`} />)}
        <line x1={0} y1={0} x2={0} y2={-200} stroke="#1d1d22" strokeWidth={16} strokeLinecap="round" transform={`rotate(${a})`} />
        <line x1={0} y1={0} x2={0} y2={-130} stroke="#1d1d22" strokeWidth={20} strokeLinecap="round" transform={`rotate(${a / 12})`} />
        {value && <text y={-370} textAnchor="middle" fontSize={130} fontWeight={900} fill="#f2b33d" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "menu") {  // 値段表。value は "SMALL $3|MEDIUM $6.50|LARGE $7"。2つ目以降は時間差で出る
    const rows = (value ?? "").split("|");
    return (
      <g>
        <rect x={140} y={520} width={800} height={160 + rows.length * 190} rx={30} fill="#2b1d14" stroke="#d9a63a" strokeWidth={10} />
        <text x={540} y={630} textAnchor="middle" fontSize={70} fontWeight={900} fill="#ffd23f" fontFamily="Arial" letterSpacing={6}>POPCORN</text>
        {rows.map((r, i) => {
          const [name, price] = r.split(" ");
          const show = Math.min(1, Math.max(0, (t - i * 0.35) * 4));
          return <g key={i} opacity={show} transform={`translate(0 ${(1 - show) * 30})`}>
            <text x={210} y={790 + i * 190} fontSize={72} fontWeight={800} fill="#fbf7ee" fontFamily="Arial">{name}</text>
            <text x={870} y={790 + i * 190} textAnchor="end" fontSize={80} fontWeight={900} fill={i === rows.length - 1 ? "#ffd23f" : "#fbf7ee"} fontFamily="Arial">{price}</text>
          </g>;
        })}
      </g>
    );
  }
  if (kind === "strawberry") {  // イチゴの表面(種つき)。超アップでも絵になるように
    return (
      <g transform="translate(540 980)">
        <path d="M0 -330 C230 -330 330 -120 300 60 C270 240 120 380 0 400 C-120 380 -270 240 -300 60 C-330 -120 -230 -330 0 -330 Z" fill="#e0263b" />
        <path d="M-120 -250 C-40 -300 60 -300 140 -250" stroke="#ff6b7a" strokeWidth={30} fill="none" opacity={0.5} strokeLinecap="round" />
        {[...Array(46)].map((_, i) => {
          const a = i * 2.39996, rr = 40 * Math.sqrt(i + 1);
          const x = Math.cos(a) * rr * 1.05, y = Math.sin(a) * rr * 1.15 + 20;
          return Math.abs(x) < 270 - Math.abs(y) * 0.25 && y < 350 ? <ellipse key={i} cx={x} cy={y} rx={11} ry={16} fill="#ffd23f" transform={`rotate(${a * 57} ${x} ${y})`} /> : null;
        })}
        <path d="M-150 -320 L-60 -380 L0 -440 L60 -380 L150 -320 L60 -330 L0 -300 L-60 -330 Z" fill="#2fa36b" />
      </g>
    );
  }
  if (kind === "flamingo") {  // フラミンゴ(片足立ち、首がゆれる)
    const sw = Math.sin(t * 1.5) * 8;
    return (
      <g transform="translate(560 900)">
        <path d="M-20 160 L-30 520 M20 160 L60 330 L-10 380" stroke="#e86a92" strokeWidth={14} fill="none" strokeLinecap="round" strokeLinejoin="round" />
        <ellipse cx={0} cy={80} rx={190} ry={120} fill="#ff7aa8" />
        <path d="M-150 60 Q-60 10 60 60 Q-40 110 -150 60 Z" fill="#ff5c95" />
        <path d={`M150 40 C230 -60 120 -170 140 -260 C150 -330 ${230 + sw} -360 ${250 + sw} -300`} stroke="#ff7aa8" strokeWidth={42} fill="none" strokeLinecap="round" />
        <circle cx={250 + sw} cy={-300} r={46} fill="#ff7aa8" />
        <path d={`M${280 + sw} -300 L${360 + sw} -270 Q${340 + sw} -230 ${290 + sw} -250 Z`} fill="#222" />
        <circle cx={250 + sw} cy={-310} r={9} fill="#111" />
        {value && <text x={-40} y={-420} textAnchor="middle" fontSize={100} fontWeight={900} fill="#ffd23f" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "onion") {  // タマネギ(切ると気体がもわっと上がる)
    return (
      <g transform="translate(540 1000)">
        <path d="M0 -330 C40 -250 20 -220 10 -200 C200 -180 300 -40 270 100 C240 250 120 320 0 320 C-120 320 -240 250 -270 100 C-300 -40 -200 -180 -10 -200 C-20 -220 -40 -250 0 -330 Z" fill="#c77dbb" />
        {[-150, -70, 0, 70, 150].map((x) => <path key={x} d={`M${x * 0.2} -190 Q${x * 1.3} 60 ${x * 0.3} 315`} stroke="#a05a96" strokeWidth={8} fill="none" />)}
        {[0, 1, 2].map((i) => <path key={i} d={`M${-80 + i * 80} -360 q30 -60 0 -120 q-30 -60 0 -120`} stroke="#d7f2c4" strokeWidth={14} fill="none" strokeLinecap="round"
          opacity={0.6} transform={`translate(0 ${-((t * 120 + i * 60) % 180)})`} />)}
        {value && <text y={-560} textAnchor="middle" fontSize={100} fontWeight={900} fill="#ffd23f" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "sunflower") {  // ヒマワリ(太陽のほうへ向きを変える)
    const turn = Math.sin(t * 0.8) * 18;
    return (
      <g transform="translate(540 1000)">
        <path d="M0 0 Q20 300 0 620" stroke="#3f8f3a" strokeWidth={30} fill="none" />
        <path d="M5 330 Q120 260 200 320 Q110 380 5 330 Z" fill="#4caf50" />
        <g transform={`rotate(${turn})`}>
          {[...Array(16)].map((_, i) => <ellipse key={i} cx={0} cy={-230} rx={50} ry={110} fill="#ffcc1a" transform={`rotate(${i * 22.5})`} />)}
          <circle r={170} fill="#6b3f1d" />
          {[...Array(30)].map((_, i) => { const a = i * 2.4, r = 14 * Math.sqrt(i + 1); return <circle key={i} cx={Math.cos(a) * r} cy={Math.sin(a) * r} r={9} fill="#4a2a12" />; })}
        </g>
        {value && <text y={-450} textAnchor="middle" fontSize={100} fontWeight={900} fill="#ffd23f" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "jellyfish") {  // クラゲ(ふわふわ上下、足がゆれる)
    const b = Math.sin(t * 1.6) * 30, p = 1 + Math.sin(t * 3.2) * 0.05;
    return (
      <g transform={`translate(540 ${880 + b})`}>
        {[...Array(7)].map((_, i) => { const x = -150 + i * 50, w = Math.sin(t * 2.5 + i) * 30;
          return <path key={i} d={`M${x} 40 C${x + w} 200 ${x - w} 320 ${x + w * 0.5} 470`} stroke="#ffb3e6" strokeWidth={10} fill="none" opacity={0.8} strokeLinecap="round" />; })}
        <path d={`M-210 40 C-210 ${-230 * p} 210 ${-230 * p} 210 40 Q105 80 0 40 Q-105 80 -210 40 Z`} fill="#ff9ad5" opacity={0.85} />
        <path d="M-140 -40 C-120 -150 120 -150 140 -40" stroke="#fff" strokeWidth={10} fill="none" opacity={0.5} />
        <circle cx={0} cy={-20} r={40} fill="#ffd6f0" opacity={0.9} />
        {value && <text y={-330} textAnchor="middle" fontSize={100} fontWeight={900} fill="#ffd23f" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "seahorse") {  // タツノオトシゴ(ゆらゆら上下)
    const b = Math.sin(t * 2) * 20;
    return (
      <g transform={`translate(540 ${930 + b})`}>
        <path d="M-20 -330 C90 -360 140 -260 90 -190 C60 -150 20 -150 30 -100 C50 0 120 60 90 170 C60 280 -40 300 -60 230 C-80 170 -10 170 0 220 C10 250 50 230 40 180 C20 100 -60 60 -50 -60 C-45 -130 -120 -150 -110 -220 C-100 -290 -70 -320 -20 -330 Z" fill="#f6a623" />
        <path d="M80 -250 L190 -230 L185 -205 L80 -215 Z" fill="#f6a623" />
        <circle cx={20} cy={-260} r={22} fill="#fff" /><circle cx={26} cy={-256} r={11} fill="#111" />
        {[-60, -10, 40, 90].map((y) => <path key={y} d={`M-30 ${y} q40 -12 70 4`} stroke="#d4860f" strokeWidth={9} fill="none" strokeLinecap="round" />)}
        <path d="M-60 -60 q-60 30 -40 90 q30 -20 40 -50" fill="#ffd27a" opacity={0.8} />
        {value && <text y={-400} textAnchor="middle" fontSize={96} fontWeight={900} fill="#ffd23f" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "dolphin" || kind === "orca") {  // イルカ/シャチ(泳いで横切る)
    const orca = kind === "orca";
    const x = 540 + Math.sin(t * 0.9) * 120, y = 960 + Math.sin(t * 2) * 30;
    return (
      <g transform={`translate(${x} ${y}) rotate(${Math.cos(t * 2) * 6})`}>
        {orca ? <path d="M-380 0 C-300 -150 150 -170 330 -40 C380 -10 380 30 330 40 C150 120 -250 110 -380 0 Z" fill="#14161c" />
              : <path d="M-380 0 C-300 -140 120 -160 300 -50 C340 -30 360 -20 450 -8 C470 -2 470 12 450 16 C360 24 340 34 300 44 C150 120 -250 100 -380 0 Z" fill="#7fb3d5" />}
        {orca ? <path d="M-20 -120 L60 -300 L120 -110 Z" fill="#14161c" /> : <path d="M-60 -120 Q-10 -250 90 -140 Q40 -150 30 -110 Z" fill="#6aa0c4" />}
        {!orca && <path d="M330 20 Q380 40 430 14" stroke="#3d6f8f" strokeWidth={6} fill="none" strokeLinecap="round" />}
        <path d="M-370 0 L-470 -90 L-440 0 L-470 90 Z" fill={orca ? "#14161c" : "#4f7fa1"} />
        {orca ? <><ellipse cx={210} cy={-40} rx={60} ry={24} fill="#fff" /><path d="M-60 60 C60 110 200 80 300 30 C200 40 60 40 -60 60 Z" fill="#fff" /></>
              : <path d="M-220 45 C0 95 200 70 330 30 C200 50 0 45 -220 45 Z" fill="#e3f0f8" />}
        {orca ? <circle cx={250} cy={-30} r={8} fill="#111" /> : <><circle cx={270} cy={-22} r={13} fill="#fff" /><circle cx={273} cy={-20} r={7} fill="#111" /></>}
        {value && <text x={0} y={-340} textAnchor="middle" fontSize={96} fontWeight={900} fill="#ffd23f" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "octopus") {  // タコ(8本の足がゆらゆら)
    return (
      <g transform="translate(540 900)">
        {[...Array(8)].map((_, i) => {
          const x0 = -175 + i * 50, w = Math.sin(t * 3 + i) * 40;
          return <path key={i} d={`M${x0} 120 C${x0 + w} 260 ${x0 - w - (i - 3.5) * 30} 380 ${x0 + (i - 3.5) * 60} 480`} stroke="#9b59b6" strokeWidth={46} fill="none" strokeLinecap="round" />;
        })}
        <ellipse cx={0} cy={-40} rx={230} ry={250} fill="#a463c7" />
        <ellipse cx={-70} cy={-150} rx={60} ry={34} fill="#fff" opacity={0.15} />
        <circle cx={-80} cy={20} r={42} fill="#fff" /><circle cx={80} cy={20} r={42} fill="#fff" />
        <circle cx={-72} cy={28} r={20} fill="#111" /><circle cx={88} cy={28} r={20} fill="#111" />
        {value && <text y={-340} textAnchor="middle" fontSize={110} fontWeight={900} fill="#ffd23f" fontFamily="Arial" stroke="#1d1d22" strokeWidth={8} paintOrder="stroke">{value}</text>}
      </g>
    );
  }
  if (kind === "prism") {  // 白い光がプリズムで7色に分かれる。青が四方に散る
    const cols = ["#ff3b30", "#ff9500", "#ffd60a", "#34c759", "#0a84ff", "#5e5ce6", "#bf5af2"];
    const n = Math.min(1, t / 0.8);
    return (
      <g>
        <path d={`M60 960 L${60 + 420 * n} 960`} stroke="#fff" strokeWidth={26} />
        <polygon points="480,760 640,1100 320,1100" fill="rgba(200,235,255,0.35)" stroke="#e8f6ff" strokeWidth={8} />
        {n >= 1 && cols.map((c, i) => <path key={c} d={`M560 960 L1080 ${820 + i * 45}`} stroke={c} strokeWidth={22} opacity={0.9} />)}
        {n >= 1 && [...Array(10)].map((_, i) => <circle key={i} cx={700 + ((i * 97) % 340)} cy={500 + ((i * 173) % 300) - (t % 1) * 60} r={12} fill="#0a84ff" opacity={0.8} />)}
      </g>
    );
  }
  if (kind === "card") {
    return (
      <g transform={`translate(540 960) rotate(${-4 + 2 * Math.sin(t * 3)})`}>
        <rect x={-400} y={-220} width={800} height={440} rx={40} fill="#fbf7ee" />
        <rect x={-400} y={-220} width={800} height={90} rx={40} fill="#e0533c" />
        <text y={60} textAnchor="middle" fontSize={value && value.length > 12 ? 74 : 100} fontWeight={900} fill="#1d1d22" fontFamily="Arial">{value}</text>
      </g>
    );
  }
  return null;
};
