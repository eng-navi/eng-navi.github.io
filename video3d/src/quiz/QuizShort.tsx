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
export const JP = "'Hiragino Maru Gothic ProN', 'Hiragino Sans', sans-serif";
export const JPB = "'Hiragino Sans', 'Hiragino Kaku Gothic ProN', sans-serif";  // 問題文用の太いゴシック
const EN = "'Avenir Next', 'Helvetica Neue', Arial, sans-serif";

const BG = { office: Office, bedroom: Bedroom, lab: Lab };

// 画面全体にかける効果の部品
const Defs = () => (
  <defs>
    <filter id="soft"><feGaussianBlur stdDeviation="8" /></filter>
    <filter id="glow"><feGaussianBlur stdDeviation="30" /></filter>
    <linearGradient id="bodyShade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stopColor="#ffffff" stopOpacity={0.18} /><stop offset="0.6" stopColor="#000" stopOpacity={0} /><stop offset="1" stopColor="#000" stopOpacity={0.3} />
    </linearGradient>
    <radialGradient id="rim" cx="0.72" cy="0.3" r="0.75">
      <stop offset="0.75" stopColor="#ffd9a0" stopOpacity={0} /><stop offset="1" stopColor="#ffd9a0" stopOpacity={0.55} />
    </radialGradient>
    <radialGradient id="vig" cx="0.5" cy="0.5" r="0.75">
      <stop offset="0.55" stopColor="#000" stopOpacity={0} /><stop offset="1" stopColor="#000" stopOpacity={0.7} />
    </radialGradient>
    <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={3} /><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.08 0" /></filter>
  </defs>
);

// 窓から差す光の筋とほこり
const Atmos = ({ f, warm }: { f: number; warm: boolean }) => (
  <g>
    <polygon points="140,260 480,260 900,1400 300,1400" fill={warm ? "#ffc98a" : "#bcd8ff"} opacity={0.10} filter="url(#glow)" />
    {[...Array(18)].map((_, i) => {
      const x = (i * 157 + f * (0.6 + (i % 3) * 0.3)) % 1080;
      const y = 300 + ((i * 263 + f * 0.8) % 1100);
      return <circle key={i} cx={x} cy={y} r={2 + (i % 3)} fill="#fff" opacity={0.25 + (i % 4) * 0.08} />;
    })}
  </g>
);

// 英文の中の単語に色をつける
const Highlight = ({ text, words }: { text: string; words: string[] }) => (
  <>{text.split(" ").map((t, i) => {
    const core = t.toLowerCase().replace(/[^a-z]/g, "");
    const hit = words.some((w) => core.startsWith(w.toLowerCase().slice(0, 5)));
    return <span key={i} style={{ color: hit ? "#f2b33d" : "white" }}>{t} </span>;
  })}</>
);

// 0〜3秒:時計のカウントダウン+問題
export const Intro = ({ p }: { p: QuizProps }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const n = Math.max(1, 3 - Math.floor(t));
  const a = (t % 1) * 360;
  const pop = spring({ frame: f % fps, fps, config: { damping: 9 } });
  // 0秒で「クイズ」がドンと落ちてくる→揺れ→光の帯。時計と問題は少し遅れて出す
  const slam = spring({ frame: f, fps, config: { damping: 8, mass: 0.6 } });
  const shake = f < 10 ? Math.sin(f * 2.4) * (10 - f) * 2 : 0;
  const wob = Math.sin(t * 5) * 3;
  const rays = t * 25;
  const inQ = spring({ frame: f - 8, fps, config: { damping: 12 } });
  const inC = spring({ frame: f - 4, fps, config: { damping: 10 } });
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 30%, #3a2f7a, #12142a)", alignItems: "center", transform: `translateX(${shake}px)` }}>
      <svg width={1080} height={1080} viewBox="-540 -540 1080 1080" style={{ position: "absolute", top: 60, opacity: 0.16 }}>
        {[...Array(16)].map((_, i) => <polygon key={i} points="0,0 -60,-560 60,-560" fill="#f2b33d" transform={`rotate(${i * 22.5 + rays})`} />)}
      </svg>
      <div style={{ marginTop: 340, textAlign: "center", transform: `scale(${(2.6 - 1.6 * slam) * (1 + 0.04 * Math.sin(t * 9))}) rotate(${-4 + wob}deg)`, opacity: Math.min(1, slam * 2) }}>
        <div style={{ fontFamily: JP, fontSize: 84, fontWeight: 900, color: "white", letterSpacing: 8, WebkitTextStroke: "10px #12142a", paintOrder: "stroke fill" }}>リスニング</div>
        <div style={{ fontFamily: JP, fontSize: 260, fontWeight: 900, color: "#ffd23f", lineHeight: 1.05,
                      WebkitTextStroke: "22px #12142a", paintOrder: "stroke fill", textShadow: "0 16px 0 #c2410c, 0 30px 50px rgba(0,0,0,0.6)" }}>
          クイズ
        </div>
      </div>
      <svg width={300} height={300} viewBox="-210 -210 420 420" style={{ marginTop: 40, transform: `scale(${inC})` }}>
        <circle r={180} fill="#fffaf0" stroke="#f2b33d" strokeWidth={16} />
        {[...Array(12)].map((_, i) => <line key={i} x1={0} y1={-150} x2={0} y2={-165} stroke="#1d1d22" strokeWidth={8} transform={`rotate(${i * 30})`} />)}
        <path d={`M0 0 L0 -180 A180 180 0 ${a > 180 ? 1 : 0} 1 ${180 * Math.sin((a * Math.PI) / 180)} ${-180 * Math.cos((a * Math.PI) / 180)} Z`} fill="#f2b33d" opacity={0.35} />
        <line x1={0} y1={0} x2={0} y2={-140} stroke="#e0533c" strokeWidth={10} strokeLinecap="round" transform={`rotate(${a})`} />
        <text y={45} textAnchor="middle" fontSize={150 * (0.8 + 0.2 * pop)} fontWeight={900} fontFamily={EN} fill="#1d1d22">{n}</text>
      </svg>
      <div style={{ marginTop: 40, width: 860, padding: "32px 36px", borderRadius: 40, background: "#e0533c", textAlign: "center",
                    transform: `translateY(${(1 - inQ) * 500}px)`, opacity: inQ }}>
        <div style={{ fontFamily: JPB, fontWeight: 800, fontSize: 58, color: "white", lineHeight: 1.35, letterSpacing: 2, whiteSpace: "pre-line" }}>Q. {p.q_ja}</div>
        <div style={{ fontFamily: EN, fontWeight: 800, fontSize: 44, color: "#fff1ec", marginTop: 16, lineHeight: 1.2 }}>{p.q}</div>
      </div>
      <div style={{ marginTop: 44, fontFamily: JP, fontSize: 36, color: "#c9cbe6", opacity: inQ }}>全文と和訳はコメント欄にあります</div>
    </AbsoluteFill>
  );
};

// 物語の場面:背景+棒人間+字幕。カメラはゆっくり寄る
const Story = ({ p, s }: { p: QuizProps; s: Scene }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const len = s.dur * fps;
  const zoom = interpolate(f, [0, len], [1.0, 1.1]);
  const pan = interpolate(f, [0, len], [-14, 14]);
  const Bg = BG[s.bg];
  const bob = Math.sin(f / 5) * 4;
  const appear = interpolate(f, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const fade = interpolate(f, [0, 5, len - 5, len], [0, 1, 1, 0.6], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const warm = s.bg !== "lab";
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <svg width={W} height={1920} viewBox="0 0 1080 1920" style={{ transform: `scale(${zoom})`, transformOrigin: "50% 60%" }}>
        <Defs />
        {/* 奥(背景)はゆっくり、手前(人物)は少し速く動かして奥行きを出す */}
        <g transform={`translate(${pan * 0.5} 0)`}><Bg /><Atmos f={f} warm={warm} /></g>
        <g transform={`translate(${pan * 1.4} 0)`}>
          {s.people.map((pp, i) => <Stickman key={i} {...pp} bob={i === 0 ? bob : 0} />)}
          {s.think && (
            <g opacity={appear}>
              <circle cx={720} cy={760} r={22} fill="white" /><circle cx={770} cy={690} r={32} fill="white" />
              <ellipse cx={850} cy={570} rx={150} ry={100} fill="white" />
              <text x={850} y={600} textAnchor="middle" fontSize={90} fontWeight={900} fontFamily={EN} fill="#e0533c">{s.think}</text>
            </g>
          )}
        </g>
        <rect width={1080} height={1920} fill={warm ? "#ff9a4a" : "#3ad0ff"} opacity={0.05} />
        <rect width={1080} height={1920} fill="url(#vig)" />
        <rect width={1080} height={1920} filter="url(#grain)" opacity={0.6} />
      </svg>
      {/* 上に問題を出しっぱなし */}
      <div style={{ position: "absolute", top: 230, left: 60, right: 60, padding: "18px 28px", borderRadius: 30, background: "rgba(224,83,60,0.92)",
                    boxShadow: "0 10px 30px rgba(0,0,0,0.35)", fontFamily: EN, fontWeight: 800, fontSize: 40, color: "white", textAlign: "center" }}>Q. {p.q}</div>
      {/* 字幕:白い太字に黒いふち(参考動画ふう) */}
      <div style={{ position: "absolute", bottom: 340, left: 50, right: 50, textAlign: "center", fontFamily: EN, fontWeight: 900, fontSize: 66, lineHeight: 1.25,
                    WebkitTextStroke: "3px #0b0b10", textShadow: "0 6px 18px rgba(0,0,0,0.6)", opacity: appear,
                    transform: `translateY(${(1 - appear) * 20}px)` }}>
        <Highlight text={s.text} words={p.words} />
      </div>
      <Audio src={staticFile(s.audio)} />
    </AbsoluteFill>
  );
};

// 2択+カウントダウン → 「正解はコメント欄で」(答えは画面では言わない)
export const Choices = ({ p, end }: { p: QuizProps; end: boolean }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const left = Math.max(0, 4 - Math.floor(f / fps));
  const pulse = 1 + Math.sin(f / 4) * 0.03;
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 30%, #333a73, #0f1124)", alignItems: "center" }}>
      <div style={{ marginTop: 280, width: 820, padding: "30px 34px", borderRadius: 34, background: "#e0533c", textAlign: "center",
                    boxShadow: "0 14px 40px rgba(0,0,0,0.45)", fontFamily: JPB, fontWeight: 800, fontSize: 52, color: "white", lineHeight: 1.35, letterSpacing: 2, whiteSpace: "pre-line" }}>Q. {p.q_ja}
        <div style={{ fontFamily: EN, fontWeight: 800, fontSize: 40, color: "#fff1ec", marginTop: 12, lineHeight: 1.2 }}>{p.q}</div></div>
      {p.choices.map((c, i) => {
        const slide = spring({ frame: f - i * 5, fps, config: { damping: 14 } });
        return (
          <div key={i} style={{ marginTop: 50, width: 820, padding: "36px 40px", borderRadius: 36, display: "flex", gap: 30, alignItems: "center",
                                background: "linear-gradient(180deg, #fffdf7, #f1e9d8)", boxShadow: "0 12px 30px rgba(0,0,0,0.35)",
                                transform: `translateX(${(1 - (end ? 1 : slide)) * 400}px)`, fontFamily: EN, fontWeight: 800, fontSize: 46, color: "#1d1d22" }}>
            <span style={{ fontSize: 70, fontWeight: 900, color: "#e0533c" }}>{"AB"[i]}</span>{c}
          </div>
        );
      })}
      {!end && left > 0 && <div style={{ marginTop: 80, width: 180, height: 180, borderRadius: 90, background: "#f2b33d", display: "flex",
                                         boxShadow: "0 0 50px rgba(242,179,61,0.6)", alignItems: "center", justifyContent: "center",
                                         fontFamily: EN, fontWeight: 900, fontSize: 110, color: "#1d1d22" }}>{left}</div>}
      {end && <div style={{ marginTop: 80, textAlign: "center", transform: `scale(${pulse})` }}>
        <div style={{ fontFamily: JP, fontSize: 64, fontWeight: 800, color: "#f2b33d" }}>正解はコメント欄で👇</div>
        <div style={{ fontFamily: JP, fontSize: 38, color: "#c9cbe6", marginTop: 24 }}>英文と和訳もコメント欄にあります📌</div>
      </div>}
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
      <Sequence from={fr(p.choiceAt)} durationInFrames={fr(p.answerAt - p.choiceAt)}><Choices p={p} end={false} /><Audio src={staticFile(p.tick)} /></Sequence>
      <Sequence from={fr(p.answerAt)}><Choices p={p} end={true} /></Sequence>
      <Audio src={staticFile(p.bgm)} volume={0.06} />
    </AbsoluteFill>
  );
};
