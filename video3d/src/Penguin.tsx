// ペン(ペンギン)を基本の形(球・円すい)だけで組み立てた3Dモデル
export const Penguin = ({ hop = 0 }: { hop?: number }) => (
  <group position={[0, hop, 0]}>
    {/* 体(紺)とおなか(白) */}
    <mesh position={[0, 0, 0]} scale={[1, 1.25, 0.95]}>
      <sphereGeometry args={[1, 48, 48]} />
      <meshStandardMaterial color="#2c3e66" roughness={0.6} />
    </mesh>
    <mesh position={[0, -0.1, 0.35]} scale={[0.75, 1, 0.7]}>
      <sphereGeometry args={[1, 48, 48]} />
      <meshStandardMaterial color="#fbf9f4" roughness={0.7} />
    </mesh>
    {/* 目 */}
    {[-0.3, 0.3].map((x) => (
      <mesh key={x} position={[x, 0.55, 0.85]}>
        <sphereGeometry args={[0.1, 24, 24]} />
        <meshStandardMaterial color="#1b1b1b" />
      </mesh>
    ))}
    {/* くちばし */}
    <mesh position={[0, 0.35, 0.98]} rotation={[Math.PI / 2, 0, 0]}>
      <coneGeometry args={[0.13, 0.3, 24]} />
      <meshStandardMaterial color="#f39c45" />
    </mesh>
    {/* ほっぺ */}
    {[-0.45, 0.45].map((x) => (
      <mesh key={x} position={[x, 0.3, 0.8]} scale={[1, 0.6, 0.4]}>
        <sphereGeometry args={[0.1, 16, 16]} />
        <meshStandardMaterial color="#f2a3a3" />
      </mesh>
    ))}
    {/* 足 */}
    {[-0.35, 0.35].map((x) => (
      <mesh key={x} position={[x, -1.22, 0.3]} scale={[1, 0.35, 1.4]}>
        <sphereGeometry args={[0.22, 24, 24]} />
        <meshStandardMaterial color="#f39c45" />
      </mesh>
    ))}
  </group>
);
