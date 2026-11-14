import { Composition } from "remotion";
import { PenScene } from "./PenScene";

// リールと同じ縦長 1080×1920・30fps
export const Root = () => (
  <Composition
    id="PenScene"
    component={PenScene}
    durationInFrames={150}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{ caption: "You look exhausted!", audio: "" }}
  />
);
