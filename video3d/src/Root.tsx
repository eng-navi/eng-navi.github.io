import { Composition, Still } from "remotion";
import { QuizShort, QuizProps } from "./quiz/QuizShort";
import { IfCover, IfShort, IfProps } from "./if/IfShort";
import { PenScene } from "./PenScene";

// リールと同じ縦長 1080×1920・30fps
export const Root = () => (
  <>
  <Composition
    id="IfShort"
    component={IfShort}
    durationInFrames={600}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{} as IfProps}
    calculateMetadata={({ props }) => ({ durationInFrames: Math.round((props as IfProps).total * 30) })}
  />
  <Still id="IfCover" component={IfCover} width={1080} height={1920} defaultProps={{} as IfProps} />
  <Composition
    id="QuizShort"
    component={QuizShort}
    durationInFrames={600}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{} as QuizProps}
    calculateMetadata={({ props }) => ({ durationInFrames: Math.round((props as QuizProps).total * 30) })}
  />
  <Composition
    id="PenScene"
    component={PenScene}
    durationInFrames={150}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{ caption: "You look exhausted!", audio: "" }}
  />
  </>
);
