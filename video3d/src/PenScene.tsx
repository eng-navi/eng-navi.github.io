import { ThreeCanvas } from "@remotion/three";
import { AbsoluteFill, Audio, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Penguin } from "./Penguin";

type Props = { caption: string; audio: string };

// 3D のペン+字幕+(あれば)音声。字幕・音声は Remotion、3D は Three.js(react-three-fiber)
export const PenScene = ({ caption, audio }: Props) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 12 } }); // 出てくるときにぽよんと
  const hop = Math.abs(Math.sin(frame / 6)) * 0.15;
  const turn = interpolate(frame, [0, 150], [-0.4, 0.4]);
  return (
    <AbsoluteFill style={{ backgroundColor: "#f4ece2" }}>
      <ThreeCanvas width={width} height={height} camera={{ position: [0, 0.4, 9.5], fov: 40 }}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[3, 5, 5]} intensity={1.4} />
        <group scale={enter} rotation={[0, turn, 0]} position={[0, -0.6, 0]}>
          <Penguin hop={hop} />
        </group>
        <mesh position={[0, -1.95, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <circleGeometry args={[2.2, 48]} />
          <meshStandardMaterial color="#c7dccb" />
        </mesh>
      </ThreeCanvas>
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 420 }}>
        <div style={{ background: "#fffcf5", border: "6px solid #282828", borderRadius: 40, padding: "28px 48px",
                      fontSize: 64, fontFamily: "sans-serif", fontWeight: 700, color: "#282828",
                      opacity: interpolate(frame, [10, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
          {caption}
        </div>
      </AbsoluteFill>
      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};
