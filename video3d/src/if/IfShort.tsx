import { AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Choices, Intro, QuizProps } from "../quiz/QuizShort";
import { Body, Eyes, Head, Mouth } from "./Face";
import { Backdrop, Defs, Insert } from "./Sets";

// 1カット(2〜3秒)の指定。type で構図を変える
export type Shot = {
  type: "face" | "eyes" | "full" | "two" | "insert" | "wide";
  start: number; dur: number; bg: string;
  eyes?: Eyes; mouth?: Mouth; color?: string; rim?: string;
  eyes2?: Eyes; mouth2?: Mouth; color2?: string;
  insert?: string; value?: string; hud?: string; cam?: "push" | "pull" | "pan" | "shake";
};
export type Word = { text: string; start: number; end: number; hl?: boolean };
export type IfProps = QuizProps & { shots: Shot[]; words: Word[]; story: string; sfx: string };

const W = 1080, H = 1920;
const EN = "'Avenir Next', 'Helvetica Neue', Arial, sans-serif";

// 1カットを描く
const ShotView = ({ s }: { s: Shot }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const len = s.dur * fps;
  const pop = spring({ frame: f, fps, config: { damping: 13, mass: 0.6 } }); // カットの入りで少し寄る
  const camMove = { push: interpolate(f, [0, len], [1, 1.12]), pull: interpolate(f, [0, len], [1.14, 1]), pan: 1.06, shake: 1.05 }[s.cam ?? "push"];
  const sx = s.cam === "pan" ? interpolate(f, [0, len], [-40, 40]) : s.cam === "shake" ? Math.sin(f * 2.3) * 10 * Math.max(0, 1 - t * 2) : 0;
  const scale = camMove * (0.94 + 0.06 * pop);
  const blink = (f % 75) < 3 && s.eyes !== "happy" && s.eyes !== "squint";
  const eyes = blink ? ("happy" as Eyes) : s.eyes;
  const bob = Math.sin(f / 6) * 6;
  const close = s.type === "face" || s.type === "eyes";
  return (
    <AbsoluteFill>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ transform: `translateX(${sx}px) scale(${scale})`, transformOrigin: "50% 55%" }}>
        <Defs />
        <Backdrop kind={s.bg} blur={close ? 14 : s.type === "insert" ? 18 : 0} />
        {s.type === "face" && <g transform={`translate(540 ${1080 + bob})`}><Head r={330} eyes={eyes} mouth={s.mouth} rim={s.rim} />
          <path d="M-330 360 Q0 260 330 360 L380 900 L-380 900 Z" fill={s.color ?? "#2f6fd6"} /></g>}
        {s.type === "eyes" && <g transform="translate(540 960)"><Head r={720} eyes={eyes} mouth="none" rim={s.rim} /></g>}
        {s.type === "full" && <g transform={`translate(540 ${1560})`}><Body color={s.color} rim={s.rim} eyes={eyes} mouth={s.mouth} /></g>}
        {s.type === "wide" && <g transform="translate(540 1500) scale(0.55)"><Body color={s.color} rim={s.rim} eyes={eyes} mouth={s.mouth} pose="run" step={f / 3} /></g>}
        {s.type === "two" && <>
          <g transform="translate(300 1600) scale(0.95)"><Body color={s.color} rim={s.rim} eyes={eyes} mouth={s.mouth} pose="point" /></g>
          <g transform="translate(800 1620) scale(0.85)"><Body color={s.color2 ?? "#c0392b"} rim="#ffffff" eyes={s.eyes2} mouth={s.mouth2} /></g></>}
        {s.type === "insert" && s.insert && <Insert kind={s.insert} value={s.value} t={t} />}
        <rect width={W} height={H} fill="url(#vig)" />
        <rect width={W} height={H} filter="url(#grain)" opacity={0.6} />
      </svg>
      {s.hud && (
        <div style={{ position: "absolute", top: 480, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
          <div style={{ padding: "14px 34px", borderRadius: 40, background: "rgba(20,20,26,0.82)", color: "#f2b33d", fontFamily: EN, fontWeight: 900,
                        fontSize: 54, letterSpacing: 2, transform: `scale(${0.85 + 0.15 * pop})` }}>{s.hud}</div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// 1〜3語ずつの字幕(ナレーションの単語のタイミングに合わせる)
const Captions = ({ words, offset }: { words: Word[]; offset: number }) => {
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
    <div style={{ position: "absolute", bottom: 380, left: 40, right: 40, textAlign: "center", fontFamily: EN, fontWeight: 900, fontSize: 92,
                  textTransform: "uppercase", lineHeight: 1.1, WebkitTextStroke: "4px #0b0b10", textShadow: "0 8px 20px rgba(0,0,0,0.6)",
                  transform: `scale(${0.85 + 0.15 * k})` }}>
      {g.map((w, i) => <span key={i} style={{ color: w.hl ? "#f2c14a" : "white" }}>{w.text} </span>)}
    </div>
  );
};

export const IfShort = (p: IfProps) => {
  const { fps } = useVideoConfig();
  const fr = (s: number) => Math.round(s * fps);
  return (
    <AbsoluteFill style={{ backgroundColor: "#0d0f18" }}>
      <Sequence durationInFrames={fr(p.intro)}><Intro p={p} /><Audio src={staticFile(p.tick)} /></Sequence>
      {p.shots.map((s, i) => <Sequence key={i} from={fr(s.start)} durationInFrames={fr(s.dur)}><ShotView s={s} /></Sequence>)}
      <Sequence from={fr(p.intro)} durationInFrames={fr(p.choiceAt - p.intro)}>
        <div style={{ position: "absolute", top: 230, left: 60, right: 60, padding: "16px 26px", borderRadius: 28, background: "rgba(224,83,60,0.92)",
                      fontFamily: EN, fontWeight: 800, fontSize: 38, color: "white", textAlign: "center" }}>Q. {p.q}</div>
        <Captions words={p.words} offset={0} />
        <Audio src={staticFile(p.story)} />
      </Sequence>
      <Sequence from={fr(p.choiceAt)} durationInFrames={fr(p.answerAt - p.choiceAt)}><Choices p={p} end={false} /><Audio src={staticFile(p.tick)} /></Sequence>
      <Sequence from={fr(p.answerAt)}><Choices p={p} end={true} /></Sequence>
      <Audio src={staticFile(p.sfx)} />
      <Audio src={staticFile(p.bgm)} volume={0.08} />
    </AbsoluteFill>
  );
};
