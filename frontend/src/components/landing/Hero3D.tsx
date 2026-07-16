import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Html, Icosahedron, MeshDistortMaterial, OrbitControls } from '@react-three/drei'
import type { Group } from 'three'

function Core() {
  const ref = useRef<Group>(null)
  useFrame((_, delta) => {
    if (!ref.current) return
    ref.current.rotation.y += delta * 0.28
    ref.current.rotation.x += delta * 0.07
  })
  return (
    <group ref={ref}>
      <Icosahedron args={[1.7, 6]}>
        <MeshDistortMaterial
          color="#0e7490"
          emissive="#0891b2"
          emissiveIntensity={0.55}
          roughness={0.15}
          metalness={0.7}
          distort={0.32}
          speed={1.4}
        />
      </Icosahedron>
      <Icosahedron args={[1.92, 1]}>
        <meshBasicMaterial color="#22d3ee" wireframe transparent opacity={0.16} />
      </Icosahedron>
    </group>
  )
}

function Tag({ position, label, conf }: { position: [number, number, number]; label: string; conf: string }) {
  return (
    <Float speed={2.2} rotationIntensity={0} floatIntensity={1.1}>
      <Html position={position} center style={{ pointerEvents: 'none' }}>
        <div className="flex items-center gap-1.5 whitespace-nowrap rounded-md border border-brand/40 bg-surface/80 px-2 py-1 text-[11px] font-medium text-brand-glow backdrop-blur">
          <span className="h-1.5 w-1.5 rounded-full bg-brand" />
          {label}
          <span className="font-mono text-ink-faint">{conf}</span>
        </div>
      </Html>
    </Float>
  )
}

export function Hero3D() {
  return (
    <Canvas camera={{ position: [0, 0, 6], fov: 50 }} dpr={[1, 2]} gl={{ antialias: true }}>
      <ambientLight intensity={0.85} />
      <directionalLight position={[4, 5, 6]} intensity={1.6} color="#22d3ee" />
      <directionalLight position={[-5, -3, 2]} intensity={0.7} color="#f5a623" />
      <Core />
      <Tag position={[2.3, 1.35, 0]} label="scratches" conf="92%" />
      <Tag position={[-2.5, 0.35, 0.4]} label="inclusion" conf="87%" />
      <Tag position={[1.5, -1.7, 0.2]} label="crazing" conf="80%" />
      <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.6} />
    </Canvas>
  )
}
