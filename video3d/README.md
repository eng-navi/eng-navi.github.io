# video3d — 3D animated reels (Three.js + Remotion)

- 3D: Three.js via @react-three/fiber, inside Remotion's `<ThreeCanvas>` (@remotion/three)
- Captions / audio / rendering: Remotion (1080×1920, 30fps)

```
cd ~/insta-quiz/video3d
npm run studio                       # preview in the browser (http://localhost:3000)
npx remotion render src/index.ts PenScene out/test.mp4 --props='{"caption":"Hello!","audio":"test.mp3"}'
npx remotion still  src/index.ts PenScene out/test.png --frame=45
```

- Audio files go in `public/` and are referenced by file name (`staticFile`)
- `src/Penguin.tsx`: Pen built from primitives (spheres/cones). Navi and the boss can be built the same way
- `remotion.config.ts`: OpenGL renderer "angle" (stable WebGL on Mac), concurrency 2 (8GB RAM)
- License: Remotion is free for individuals and companies with up to 3 employees
