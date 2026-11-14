import { Config } from "@remotion/cli/config";

// 3D(WebGL)をレンダリングするための設定。Mac では "angle" が安定
Config.setChromiumOpenGlRenderer("angle");
Config.setVideoImageFormat("jpeg");
Config.setConcurrency(2); // メモリ 8GB の Mac 向けに控えめ
