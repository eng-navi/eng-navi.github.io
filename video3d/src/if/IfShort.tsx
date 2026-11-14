import { AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Choices, Intro, JP, JPB, QuizProps, fitJP } from "../quiz/QuizShort";
import { Body, Eyes, Hat, Head, Lens, Mouth } from "./Face";
import { Backdrop, Defs, Insert, OceanFX } from "./Sets";

// 1カット(2〜3秒)の指定。type で構図、cam でカメラ、wipe で切り替え方を変える
export type Shot = {
  type: "face" | "eyes" | "full" | "two" | "insert" | "wide" | "lens" | "split" | "silhouette" | "ots";
  start: number; dur: number; bg: string;
  eyes?: Eyes; mouth?: Mouth; color?: string; rim?: string; det?: boolean; sci?: boolean;  // det:探偵 / sci:博士の見た目
  eyes2?: Eyes; mouth2?: Mouth; color2?: string;
  insert?: string; value?: string; hud?: string;
  cam?: "push" | "pull" | "pan" | "shake" | "whip" | "tilt" | "snap" | "rise";
  wipe?: "iris" | "slide";
  stamp?: string;              // 「CLUE 1/3」などのスタンプ
  mark?: [number, number, number];  // 赤丸で囲む位置 [x, y, 半径]
  left?: string; right?: string;    // split の左右の文字
  focus?: [number, number];         // lens でのぞく位置
  zoom?: number;                    // 絵の拡大率(正体を隠したいときに大きく)
  sonar?: string;                   // ソナー風の枠とラベル
};
export type Word = { text: string; start: number; end: number; hl?: boolean; ja?: string };
export type IfProps = QuizProps & { shots: Shot[]; words: Word[]; story: string; sfx: string;
  kicker?: string; title?: string; caseNo?: string; endText?: string; bg1?: string; bg2?: string;
  no?: string; mystery?: string; mysteryBg?: string; jaHints?: boolean;
  hook?: string; coverShot?: Shot; badge?: string };  // カバー画像用  // no:シリーズ番号 / mystery:冒頭とループの謎の絵 / jaHints:字幕に単語の日本語

const W = 1080, H = 1920;
const EN = "'Avenir Next', 'Helvetica Neue', Arial, sans-serif";

// 1カットを描く。words は口パク用(ナレーション中は口が動く)
const ShotView = ({ s, words }: { s: Shot; words: Word[] }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const len = s.dur * fps;
  const pop = spring({ frame: f, fps, config: { damping: 13, mass: 0.6 } });
  const cam = s.cam ?? "push";
  let scale = { push: interpolate(f, [0, len], [1, 1.12]), pull: interpolate(f, [0, len], [1.18, 1]), pan: 1.06, shake: 1.05, whip: 1.04,
    tilt: interpolate(f, [0, len], [1.02, 1.1]), snap: f < len * 0.45 ? 1 : 1.35, rise: 1.08 }[cam];
  scale *= 0.94 + 0.06 * pop;
  scale *= s.zoom ?? 1;
  let sx = cam === "pan" ? interpolate(f, [0, len], [-50, 50]) : cam === "shake" ? Math.sin(f * 2.3) * 12 * Math.max(0, 1 - t * 2) : 0;
  if (cam === "whip") sx = interpolate(f, [0, 6], [900, 0], { extrapolateRight: "clamp", easing: (x) => 1 - Math.pow(1 - x, 3) });
  const sy = cam === "rise" ? interpolate(f, [0, len], [80, -40]) : 0;
  const rot = cam === "tilt" ? interpolate(f, [0, len], [-4, -8]) : 0;
  const blurWhip = cam === "whip" && f < 6 ? (6 - f) * 4 : 0;
  const snapFlash = cam === "snap" && Math.abs(f - Math.round(len * 0.45)) < 2 ? 0.5 : 0;
  // 口パク:ナレーションの単語が鳴っている間、4フレームごとに口を開け閉め
  const gt = s.start + t;
  const talking = words.some((w) => gt >= w.start && gt <= w.end);
  const mouth = talking && Math.floor(f / 4) % 2 === 0 ? ("o" as Mouth) : s.mouth;
  const blink = (f % 75) < 3 && s.eyes !== "happy" && s.eyes !== "squint";
  const eyes = blink ? ("happy" as Eyes) : s.eyes;
  const bob = Math.sin(f / 6) * 6;
  const close = ["face", "eyes", "ots", "silhouette"].includes(s.type);
  const iris = s.wipe === "iris" ? interpolate(f, [0, 9], [0, 1300], { extrapolateRight: "clamp" }) : 2000;
  const slideX = s.wipe === "slide" ? interpolate(f, [0, 7], [W, 0], { extrapolateRight: "clamp" }) : 0;
  const markK = s.mark ? interpolate(f, [len * 0.25, len * 0.55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;
  const stampK = spring({ frame: f - 6, fps, config: { damping: 9, mass: 0.5 } });
  const [fx, fy] = s.focus ?? [540, 900];
  const settle = interpolate(f, [0, 18], [1, 0.15], { extrapolateRight: "clamp" });
  const lensX = fx + Math.sin(t * 2.2) * 260 * settle, lensY = fy + Math.cos(t * 1.7) * 140 * settle;
  const det = s.det;
  return (
    <AbsoluteFill style={{ transform: `translateX(${slideX}px)` }}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
           style={{ transform: `translate(${sx}px, ${sy}px) scale(${scale}) rotate(${rot}deg)`, transformOrigin: "50% 55%", filter: blurWhip ? `blur(${blurWhip}px)` : undefined }}>
        <Defs />
        <clipPath id="iris"><circle cx={540} cy={900} r={iris} /></clipPath>
        <clipPath id="lensClip"><circle cx={lensX} cy={lensY} r={210} /></clipPath>
        <g clipPath="url(#iris)">
        <Backdrop kind={s.bg} blur={close ? 14 : s.type === "insert" || s.type === "lens" ? 18 : 0} />
        {s.bg === "ocean" && <OceanFX t={t} />}
        {s.type === "face" && <g transform={`translate(540 ${1080 + bob})`}><Head r={330} eyes={eyes} mouth={mouth} rim={s.rim} detective={det} sci={s.sci} />
          <path d="M-330 360 Q0 260 330 360 L380 900 L-380 900 Z" fill={s.color ?? "#2f6fd6"} />
          {det && <path d="M-200 330 L0 520 L200 330 L150 900 L-150 900 Z" fill="#1d3f35" />}</g>}
        {s.type === "eyes" && <g transform="translate(540 960)"><Head r={720} eyes={eyes} mouth="none" rim={s.rim} /></g>}
        {s.type === "full" && <g transform={`translate(540 ${1560})`}><Body color={s.color} rim={s.rim} eyes={eyes} mouth={mouth} detective={det} sci={s.sci} pose={det ? "lens" : "stand"} /></g>}
        {s.type === "wide" && <g transform="translate(540 1500) scale(0.55)"><Body color={s.color} rim={s.rim} eyes={eyes} mouth={s.mouth} pose="run" step={f / 3} detective={det} sci={s.sci} /></g>}
        {s.type === "two" && <>
          <g transform="translate(300 1600) scale(0.95)"><Body color={s.color} rim={s.rim} eyes={eyes} mouth={mouth} pose={det ? "lens" : "point"} detective={det} sci={s.sci} /></g>
          <g transform="translate(800 1620) scale(0.85)"><Body color={s.color2 ?? "#c0392b"} rim="#ffffff" eyes={s.eyes2} mouth={s.mouth2} /></g></>}
        {s.type === "ots" && <>  {/* 肩越し:手前に主人公の後頭部、奥に相手 */}
          <g transform="translate(560 1640) scale(0.95)"><Body color={s.color2 ?? "#c0392b"} rim="#ffffff" eyes={s.eyes2} mouth={s.mouth2} /></g>
          <g transform={`translate(250 ${1500 + bob})`}><circle r={330} fill="#0f0f12" />{det && <g transform="scale(1.65)"><Hat /></g>}
            <path d="M-360 300 Q0 200 360 300 L420 900 L-420 900 Z" fill={s.color ?? "#2f6fd6"} /></g></>}
        {s.type === "silhouette" && <>  {/* 逆光のシルエット */}
          <circle cx={540} cy={900} r={520} fill="#fff4d6" opacity={0.9} />
          <g transform="translate(540 1560)" style={{ filter: "brightness(0)" }}><Body color={s.color} eyes={eyes} mouth="none" detective={det} sci={s.sci} pose={det ? "lens" : "stand"} /></g>
          <g transform="translate(540 1060)"><Eye2 kind={eyes} /></g></>}
        {(s.type === "insert" || s.type === "lens") && s.insert && <Insert kind={s.insert} value={s.value} t={t} />}
        {s.type === "lens" && s.insert && <>  {/* 虫めがねでのぞいた部分だけ拡大 */}
          <g clipPath="url(#lensClip)"><rect width={W} height={H} fill="#fbf7ee" />
            <g transform={`translate(${lensX} ${lensY}) scale(1.45) translate(${-lensX} ${-lensY})`}><Insert kind={s.insert} value={s.value} t={t} /></g></g>
          <Lens x={lensX} y={lensY} r={210} rot={-30} /></>}
        {s.type === "split" && <>  {/* 画面を左右に分けて比べる */}
          <rect x={0} y={0} width={540} height={H} fill="#1f3b5c" /><rect x={540} y={0} width={540} height={H} fill="#5c1f2b" />
          <rect x={530} y={0} width={20} height={H} fill="#fff" />
          <g transform={`translate(270 ${1400 + bob}) scale(0.7)`}><Body color={s.color} eyes={eyes} mouth={s.mouth} detective={det} sci={s.sci} /></g>
          <g transform={`translate(810 ${1400 - bob}) scale(0.7)`}><Body color={s.color2 ?? "#c0392b"} rim="#fff" eyes={s.eyes2} mouth={s.mouth2} /></g>
          <text x={270} y={720} textAnchor="middle" fontSize={96} fontWeight={900} fill="#fff" fontFamily={EN}>{s.left}</text>
          <text x={810} y={720} textAnchor="middle" fontSize={96} fontWeight={900} fill="#ffd23f" fontFamily={EN}>{s.right}</text></>}
        {s.mark && <circle cx={s.mark[0]} cy={s.mark[1]} r={s.mark[2]} fill="none" stroke="#ff3b30" strokeWidth={16} strokeLinecap="round"
          strokeDasharray={2 * Math.PI * s.mark[2]} strokeDashoffset={(1 - markK) * 2 * Math.PI * s.mark[2]} transform={`rotate(-90 ${s.mark[0]} ${s.mark[1]})`} />}
        </g>
        <rect width={W} height={H} fill="url(#vig)" />
        <rect width={W} height={H} filter="url(#grain)" opacity={0.6} />
        {snapFlash > 0 && <rect width={W} height={H} fill="#fff" opacity={snapFlash} />}
      </svg>
      {s.hud && (
        <div style={{ position: "absolute", top: 480, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
          <div style={{ padding: "14px 34px", borderRadius: 40, background: "rgba(20,20,26,0.82)", color: "#f2b33d", fontFamily: EN, fontWeight: 900,
                        fontSize: 54, letterSpacing: 2, transform: `scale(${0.85 + 0.15 * pop})` }}>{s.hud}</div>
        </div>
      )}
      {s.sonar && (  /* ソナー風:四隅の枠、走査線、ラベル */
        <div style={{ position: "absolute", top: 520, bottom: 560, left: 110, right: 110 }}>
          {[[0, 0], [1, 0], [0, 1], [1, 1]].map(([x, y], i) => <div key={i} style={{ position: "absolute", [x ? "right" : "left"]: 0, [y ? "bottom" : "top"]: 0, width: 70, height: 70,
            [`border${y ? "Bottom" : "Top"}`]: "6px solid #bdf3ff", [`border${x ? "Right" : "Left"}`]: "6px solid #bdf3ff", opacity: 0.85 }} />)}
          <div style={{ position: "absolute", left: 0, right: 0, top: `${(t * 40) % 100}%`, height: 3, background: "rgba(189,243,255,0.45)" }} />
          <div style={{ position: "absolute", top: -64, left: 0, fontFamily: EN, fontWeight: 800, fontSize: 40, letterSpacing: 6, color: "#bdf3ff" }}>● {s.sonar}</div>
        </div>
      )}
      {s.stamp && (
        <div style={{ position: "absolute", top: 560, right: 110, padding: "10px 28px", border: "8px solid #ff3b30", borderRadius: 16, color: "#ff3b30",
                      fontFamily: EN, fontWeight: 900, fontSize: 64, letterSpacing: 4, background: "rgba(255,244,230,0.92)",
                      transform: `scale(${2.2 - 1.2 * stampK}) rotate(-12deg)`, opacity: Math.min(1, stampK * 2) }}>{s.stamp}</div>
      )}
    </AbsoluteFill>
  );
};

// シルエットの白い目だけ
const Eye2 = ({ kind }: { kind?: Eyes }) => (
  <g>{[-50, 50].map((x) => kind === "squint" || kind === "smug"
    ? <path key={x} d={`M${x - 24} 0 Q${x} -14 ${x + 24} 0`} stroke="#fff" strokeWidth={12} fill="none" strokeLinecap="round" />
    : <ellipse key={x} cx={x} cy={0} rx={18} ry={22} fill="#fff" />)}</g>
);

// 1〜3語ずつの字幕(ナレーションの単語のタイミングに合わせる)
const Captions = ({ words, offset, jaHints = false }: { words: Word[]; offset: number; jaHints?: boolean }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps - offset;
  const groups: Word[][] = [];
  let cur: Word[] = [];
  words.forEach((w) => { cur.push(w); if (cur.length === 3 || /[.,?!]$/.test(w.text)) { groups.push(cur); cur = []; } });
  if (cur.length) groups.push(cur);
  const g = groups.find((gr) => t >= gr[0].start - 0.05 && t <= gr[gr.length - 1].end + 0.15);
  if (!g) return null;
  const k = spring({ frame: Math.round((t - g[0].start) * fps), fps, config: { damping: 12 } });
  return (
    <div style={{ position: "absolute", bottom: 380, left: 140, right: 140, textAlign: "center", fontFamily: EN, fontWeight: 900, fontSize: 76,
                  textTransform: "uppercase", lineHeight: 1.1, WebkitTextStroke: "4px #0b0b10", textShadow: "0 8px 20px rgba(0,0,0,0.6)",
                  transform: `scale(${0.85 + 0.15 * k})` }}>
      {g.map((w, i) => <span key={i} style={{ color: w.hl ? "#f2c14a" : "white" }}>{w.text} </span>)}
      {jaHints && g.some((w) => w.ja) && <div style={{ fontFamily: JPB, fontSize: 40, fontWeight: 800, color: "#fff4c2", WebkitTextStroke: "0px", marginTop: 10,
                                                       textTransform: "none", textShadow: "0 3px 10px rgba(0,0,0,0.8)" }}>
        {g.filter((w) => w.ja).map((w) => `${w.text.replace(/[^A-Za-z'-]/g, "")} = ${w.ja}`).join("  ")}</div>}
    </div>
  );
};

// 科学の冒頭:謎の絵の超アップに「?」。文字は小さく添える
const MysteryIntro = ({ p }: { p: IfProps }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const q = spring({ frame: f - 3, fps, config: { damping: 7, mass: 0.5 } });
  const box = spring({ frame: f - 10, fps, config: { damping: 12 } });
  return (
    <AbsoluteFill style={{ backgroundColor: "#0d0f18", alignItems: "center" }}>
      <MysteryImage p={p} t={t} />
      <div style={{ position: "absolute", top: 560, fontFamily: EN, fontWeight: 900, fontSize: 420, color: "#ffd23f", WebkitTextStroke: "18px #12142a",
                    paintOrder: "stroke fill", textShadow: "0 20px 50px rgba(0,0,0,0.6)", transform: `scale(${q}) rotate(${(1 - q) * -30}deg)` }}>?</div>
      <div style={{ position: "absolute", top: 230, padding: "10px 30px", borderRadius: 40, background: "rgba(13,15,24,0.85)", color: "#ffd23f",
                    fontFamily: JPB, fontWeight: 800, fontSize: 44, letterSpacing: 2 }}>{p.kicker ?? ""}{p.title ?? ""} {p.no ?? ""}</div>
      <div style={{ position: "absolute", bottom: 420, width: 860, padding: "26px 32px", borderRadius: 36, background: "#e0533c", textAlign: "center",
                    transform: `translateY(${(1 - box) * 400}px)`, opacity: box }}>
        <div style={{ fontFamily: JPB, fontWeight: 800, fontSize: fitJP(p.q_ja, 58, 760), color: "white", whiteSpace: "pre-line" }}>Q. {p.q_ja}</div>
        <div style={{ fontFamily: EN, fontWeight: 800, fontSize: 44, color: "#fff1ec", marginTop: 8 }}>{p.q}</div>
      </div>
    </AbsoluteFill>
  );
};

// 謎の絵(冒頭とループの最後で同じ絵を使い、最初に自然につなげる)
const MysteryImage = ({ p, t }: { p: IfProps; t: number }) => (
  <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", transform: `scale(${3.2 + t * 0.15})`, transformOrigin: "50% 50%", filter: "blur(2px)" }}>
    <Defs /><Backdrop kind={p.mysteryBg ?? "dark"} />{p.mystery && <Insert kind={p.mystery} t={2} />}
    <rect width={W} height={H} fill="url(#vig)" />
  </svg>
);

// 画面の上の残り時間のバーと、シリーズ番号
const Progress = ({ p }: { p: IfProps }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const left = Math.max(0, 1 - f / fps / p.total);
  return (
    <div style={{ position: "absolute", top: 150, left: 110, right: 110, display: "flex", alignItems: "center", gap: 18 }}>
      {p.no && <div style={{ fontFamily: EN, fontWeight: 900, fontSize: 34, color: "#ffd23f" }}>{p.no}</div>}
      <div style={{ flex: 1, height: 10, borderRadius: 5, background: "rgba(255,255,255,0.22)" }}>
        <div style={{ width: `${left * 100}%`, height: 10, borderRadius: 5, background: "#ffd23f" }} />
      </div>
    </div>
  );
};

// 最後の0.4秒で冒頭の謎の絵に戻す(気づかずにもう1回見てもらうため)
const LoopBack = ({ p }: { p: IfProps }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ opacity: Math.min(1, f / 12) }}><MysteryImage p={p} t={0} /></AbsoluteFill>;
};

export const IfShort = (p: IfProps) => {
  const { fps } = useVideoConfig();
  const fr = (s: number) => Math.round(s * fps);
  return (
    <AbsoluteFill style={{ backgroundColor: "#0d0f18" }}>
      <Sequence durationInFrames={fr(p.intro)}>{p.mystery ? <MysteryIntro p={p} /> : <Intro p={p} />}<Audio src={staticFile(p.tick)} /></Sequence>
      {p.shots.map((s, i) => <Sequence key={i} from={fr(s.start)} durationInFrames={fr(s.dur)}><ShotView s={s} words={p.words} /></Sequence>)}
      <Sequence from={fr(p.intro)} durationInFrames={fr(p.choiceAt - p.intro)}>
        <div style={{ position: "absolute", top: 220, left: 110, right: 110, padding: "16px 22px", borderRadius: 28, background: "rgba(224,83,60,0.94)", color: "white", textAlign: "center",
                      boxShadow: "0 10px 30px rgba(0,0,0,0.35)" }}>
          <div style={{ fontFamily: JPB, fontWeight: 800, whiteSpace: "nowrap", letterSpacing: 1,
                        fontSize: Math.min(48, Math.floor(790 / (p.q_ja.replace("\n", "").length + 2))) }}>Q. {p.q_ja.replace("\n", "")}</div>
          <div style={{ fontFamily: EN, fontWeight: 800, fontSize: 34, color: "#fff1ec", marginTop: 6, lineHeight: 1.15 }}>{p.q}</div></div>
        <Captions words={p.words} offset={0} jaHints={p.jaHints} />
        <Audio src={staticFile(p.story)} />
      </Sequence>
      <Sequence from={fr(p.choiceAt)} durationInFrames={fr(p.answerAt - p.choiceAt)}><Choices p={p} end={false} /><Audio src={staticFile(p.tick)} /></Sequence>
      <Sequence from={fr(p.answerAt)}><Choices p={p} end={true} /></Sequence>
      {p.mystery && <Sequence from={fr(p.total) - 12}><LoopBack p={p} /></Sequence>}
      <Progress p={p} />
      <Audio src={staticFile(p.sfx)} />
      <Audio src={staticFile(p.bgm)} volume={0.08} />
    </AbsoluteFill>
  );
};

// リールのカバー画像(1枚)。その回で一番目を引くカット+大きなつかみの一言。プロフィールの一覧で切れないよう真ん中に寄せる
export const IfCover = (p: IfProps) => (
  <AbsoluteFill style={{ backgroundColor: "#0d0f18" }}>
    {p.coverShot && <Sequence from={-4}>{/* 静止画は1秒1コマなので、dur を長くしてカメラの動きを止める */}
      <ShotView s={{ ...p.coverShot, start: 0, dur: 100, cam: "push", wipe: undefined, stamp: undefined, hud: undefined }} words={[]} /></Sequence>}
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 45%, rgba(0,0,0,0) 70%, rgba(0,0,0,0.5) 100%)" }} />
    <div style={{ position: "absolute", top: 330, left: 90, right: 90, display: "flex", flexDirection: "column", alignItems: "center", gap: 22 }}>
      {p.badge && <div style={{ padding: "8px 26px", border: "7px solid #ff3b30", borderRadius: 14, color: "#ff3b30", background: "rgba(255,244,230,0.95)",
                                fontFamily: EN, fontWeight: 900, fontSize: 52, letterSpacing: 3, transform: "rotate(-6deg)" }}>{p.badge}</div>}
      <div style={{ fontFamily: JPB, fontWeight: 900, fontSize: Math.min(124, Math.floor(860 / Math.max(5, ...(p.hook ?? "").split("\n").map((l) => [...l].length)))), lineHeight: 1.25,
                    color: "#ffd23f", textAlign: "center", WebkitTextStroke: "14px #12142a", paintOrder: "stroke fill",
                    textShadow: "0 12px 0 #c2410c, 0 24px 40px rgba(0,0,0,0.6)", whiteSpace: "pre-line" }}>{p.hook}</div>
    </div>
  </AbsoluteFill>
);
