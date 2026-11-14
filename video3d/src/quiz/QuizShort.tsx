import { AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Bedroom, Lab, Office } from "./Backgrounds";
import { Stickman } from "./Stickman";

// 台本(Python の quiz_short.py が作る props)
export type Scene = { bg: "office" | "bedroom" | "lab"; text: string; audio: string; start: number; dur: number;
                      people: { x: number; y: number; color?: string; badge?: string; pose?: "stand" | "sit" | "lie" | "think"; flip?: boolean }[];
                      think?: string };
export type QuizProps = { q: string; q_ja: string; choices: string[]; answer: number; words: string[];
                          intro: number; scenes: Scene[]; choiceAt: number; answerAt: number; total: number; tick: string; bgm: string };

const W = 1080;
const JP = "'Hiragino Maru Gothic ProN', 'Hiragino Sans', sans-serif";
const EN = "'Avenir Next', 'Helvetica Neue', Arial, sans-serif";

const BG = { office: Office, bedroom: Bedroom, lab: Lab };

// 英文の中の単語に色をつける
const Highlight = ({ text, words }: { text: string; words: string[] }) => (
  <>{text.split(" ").map((t, i) => {
    const core = t.toLowerCase().replace(/[^a-z]/g, "");
    const hit = words.some((w) => core.startsWith(w.toLowerCase().slice(0, 5)));
    return <span key={i} style={{ color: hit ? "#f2b33d" : "white" }}>{t} </span>;
  })}</>
);

// 0〜3秒:時計のカウントダウン+問題
const Intro = ({ p }: { p: QuizProps }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const n = Math.max(1, 3 - Math.floor(t));
  const a = (t % 1) * 360;
  const pop = spring({ frame: f % fps, fps, config: { damping: 9 } });
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 40%, #2b3160, #12142a)", alignItems: "center" }}>
      <div style={{ marginTop: 300, fontFamily: JP, fontSize: 54, color: "#f2b33d", fontWeight: 800, letterSpacing: 4 }}>LISTENING QUIZ</div>
      <svg width={420} height={420} viewBox="-210 -210 420 420" style={{ marginTop: 50 }}>
        <circle r={180} fill="#fffaf0" stroke="#f2b33d" strokeWidth={16} />
        {[...Array(12)].map((_, i) => <line key={i} x1={0} y1={-150} x2={0} y2={-165} stroke="#1d1d22" strokeWidth={8} transform={`rotate(${i * 30})`} />)}
        <path d={`M0 0 L0 -180 A180 180 0 ${a > 180 ? 1 : 0} 1 ${180 * Math.sin((a * Math.PI) / 180)} ${-180 * Math.cos((a * Math.PI) / 180)} Z`} fill="#f2b33d" opacity={0.35} />
        <line x1={0} y1={0} x2={0} y2={-140} stroke="#e0533c" strokeWidth={10} strokeLinecap="round" transform={`rotate(${a})`} />
        <text y={45} textAnchor="middle" fontSize={150 * (0.8 + 0.2 * pop)} fontWeight={900} fontFamily={EN} fill="#1d1d22">{n}</text>
      </svg>
      <div style={{ marginTop: 70, width: 920, padding: "36px 40px", borderRadius: 40, background: "#e0533c", textAlign: "center" }}>
        <div style={{ fontFamily: EN, fontWeight: 800, fontSize: 58, color: "white", lineHeight: 1.25 }}>Q. {p.q}</div>
        <div style={{ fontFamily: JP, fontSize: 40, color: "#ffe6df", marginTop: 14 }}>{p.q_ja}</div>
      </div>
      <div style={{ marginTop: 60, fontFamily: JP, fontSize: 38, color: "#c9cbe6" }}>全文と和訳はコメント欄にあります</div>
    </AbsoluteFill>
  );
};

// 物語の場面:背景+棒人間+字幕。カメラはゆっくり寄る
const Story = ({ p, s }: { p: QuizProps; s: Scene }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(f, [0, s.dur * fps], [1.0, 1.08]);
  const Bg = BG[s.bg];
  const bob = Math.sin(f / 5) * 4;
  const appear = interpolate(f, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <svg width={W} height={1920} viewBox="0 0 1080 1920" style={{ transform: `scale(${zoom})`, transformOrigin: "50% 60%" }}>
        <Bg />
        {s.people.map((pp, i) => <Stickman key={i} {...pp} bob={i === 0 ? bob : 0} />)}
        {s.think && (
          <g opacity={appear}>
            <circle cx={720} cy={760} r={22} fill="white" /><circle cx={770} cy={690} r={32} fill="white" />
            <ellipse cx={850} cy={570} rx={150} ry={100} fill="white" />
            <text x={850} y={600} textAnchor="middle" fontSize={90} fontWeight={900} fontFamily={EN} fill="#e0533c">{s.think}</text>
          </g>
        )}
      </svg>
      {/* 上に問題を出しっぱなし */}
      <div style={{ position: "absolute", top: 230, left: 60, right: 60, padding: "18px 28px", borderRadius: 30, background: "rgba(224,83,60,0.95)",
                    fontFamily: EN, fontWeight: 800, fontSize: 40, color: "white", textAlign: "center" }}>Q. {p.q}</div>
      {/* 字幕 */}
      <div style={{ position: "absolute", bottom: 330, left: 60, right: 60, padding: "26px 34px", borderRadius: 30, background: "rgba(10,12,24,0.78)",
                    fontFamily: EN, fontWeight: 700, fontSize: 56, lineHeight: 1.3, textAlign: "center", opacity: appear }}>
        <Highlight text={s.text} words={p.words} />
      </div>
      <Audio src={staticFile(s.audio)} />
    </AbsoluteFill>
  );
};

// 3択+カウントダウン → 答え
const Choices = ({ p, reveal }: { p: QuizProps; reveal: boolean }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const left = Math.max(0, 3 - Math.floor(f / fps));
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 30%, #2b3160, #12142a)", alignItems: "center" }}>
      <div style={{ marginTop: 260, width: 940, padding: "26px 34px", borderRadius: 34, background: "#e0533c", textAlign: "center",
                    fontFamily: EN, fontWeight: 800, fontSize: 48, color: "white" }}>Q. {p.q}</div>
      {p.choices.map((c, i) => {
        const ok = reveal && i + 1 === p.answer;
        const dim = reveal && !ok;
        const slide = spring({ frame: f - i * 4, fps, config: { damping: 14 } });
        return (
          <div key={i} style={{ marginTop: 40, width: 920, padding: "34px 40px", borderRadius: 34, display: "flex", gap: 28, alignItems: "center",
                                background: ok ? "#3cb371" : "#fffaf0", opacity: dim ? 0.35 : 1, transform: `translateX(${(1 - (reveal ? 1 : slide)) * 400}px)`,
                                fontFamily: EN, fontWeight: 700, fontSize: 46, color: ok ? "white" : "#1d1d22" }}>
            <span style={{ fontSize: 60, fontWeight: 900, color: ok ? "white" : "#e0533c" }}>{"ABC"[i]}</span>{c}
          </div>
        );
      })}
      {!reveal && left > 0 && <div style={{ marginTop: 70, width: 170, height: 170, borderRadius: 85, background: "#f2b33d", display: "flex",
                                            alignItems: "center", justifyContent: "center", fontFamily: EN, fontWeight: 900, fontSize: 100, color: "#1d1d22" }}>{left}</div>}
      {reveal && <div style={{ marginTop: 70, fontFamily: JP, fontSize: 44, color: "white", textAlign: "center", lineHeight: 1.6 }}>
        正解は {"ABC"[p.answer - 1]}!<br /><span style={{ fontSize: 36, color: "#c9cbe6" }}>英文と和訳はコメント欄で見返してね📌</span></div>}
    </AbsoluteFill>
  );
};

export const QuizShort = (p: QuizProps) => {
  const { fps } = useVideoConfig();
  const fr = (s: number) => Math.round(s * fps);
  return (
    <AbsoluteFill style={{ backgroundColor: "#12142a" }}>
      <Sequence durationInFrames={fr(p.intro)}><Intro p={p} /><Audio src={staticFile(p.tick)} /></Sequence>
      {p.scenes.map((s, i) => (
        <Sequence key={i} from={fr(s.start)} durationInFrames={fr(s.dur)}><Story p={p} s={s} /></Sequence>
      ))}
      <Sequence from={fr(p.choiceAt)} durationInFrames={fr(p.answerAt - p.choiceAt)}><Choices p={p} reveal={false} /><Audio src={staticFile(p.tick)} /></Sequence>
      <Sequence from={fr(p.answerAt)}><Choices p={p} reveal={true} /></Sequence>
      <Audio src={staticFile(p.bgm)} volume={0.06} />
    </AbsoluteFill>
  );
};
