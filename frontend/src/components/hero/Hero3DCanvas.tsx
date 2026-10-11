import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface Hero3DCanvasProps {
  currentBeat: number;
  scrollProgress: number;
  ambientTemp: number;
}

export const Hero3DCanvas: React.FC<Hero3DCanvasProps> = ({
  currentBeat,
  scrollProgress,
  ambientTemp,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const beatRef = useRef(currentBeat);
  const tempRef = useRef(ambientTemp);

  useEffect(() => {
    beatRef.current = currentBeat;
    tempRef.current = ambientTemp;
  }, [currentBeat, ambientTemp]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // Check WebGL availability safely (prevents noisy jsdom warnings during headless unit tests)
    try {
      const testCanvas = document.createElement('canvas');
      const gl = testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl');
      if (!gl) return;
    } catch {
      return;
    }

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    } catch {
      return;
    }

    const width = mount.clientWidth || window.innerWidth;
    const height = mount.clientHeight || window.innerHeight;

    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0xf3fbfa, 0.015);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 4, 14);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfffaed, 2.0);
    sunLight.position.set(8, 14, 10);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 1024;
    sunLight.shadow.mapSize.height = 1024;
    scene.add(sunLight);

    // Dynamic temperature light (warms on failure, cools on rescue)
    const tempLight = new THREE.PointLight(0x6ec8ff, 1.5, 25);
    tempLight.position.set(0, 3, 2);
    scene.add(tempLight);

    // 1. Road & Ground
    const groundGeo = new THREE.PlaneGeometry(60, 120);
    const groundMat = new THREE.MeshStandardMaterial({ color: 0xe6f7f5, roughness: 0.8 });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.05;
    ground.receiveShadow = true;
    scene.add(ground);

    const roadGeo = new THREE.PlaneGeometry(7, 120);
    const roadMat = new THREE.MeshStandardMaterial({ color: 0x243b4a, roughness: 0.6 });
    const road = new THREE.Mesh(roadGeo, roadMat);
    road.rotation.x = -Math.PI / 2;
    road.receiveShadow = true;
    scene.add(road);

    // Road dash stripes
    const stripesGroup = new THREE.Group();
    const stripeGeo = new THREE.PlaneGeometry(0.3, 3);
    const stripeMat = new THREE.MeshBasicMaterial({ color: 0x19d3c5 });
    for (let z = -50; z < 50; z += 6) {
      const stripe = new THREE.Mesh(stripeGeo, stripeMat);
      stripe.rotation.x = -Math.PI / 2;
      stripe.position.set(0, 0.01, z);
      stripesGroup.add(stripe);
    }
    scene.add(stripesGroup);

    // 2. Stylized Low-Poly Reefer Truck (TRUCK-104)
    const truckGroup = new THREE.Group();
    truckGroup.position.set(0, 0, 0);

    // Cabin
    const cabinGeo = new THREE.BoxGeometry(2.4, 2.2, 2.2);
    const cabinMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 });
    const cabin = new THREE.Mesh(cabinGeo, cabinMat);
    cabin.position.set(0, 1.4, -2.5);
    cabin.castShadow = true;
    truckGroup.add(cabin);

    // Windshield
    const glassGeo = new THREE.BoxGeometry(2.2, 1.0, 0.1);
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x6ec8ff, roughness: 0.1, metalness: 0.8, transparent: true, opacity: 0.8 });
    const glass = new THREE.Mesh(glassGeo, glassMat);
    glass.position.set(0, 1.6, -3.61);
    truckGroup.add(glass);

    // Refrigerated Container
    const reeferGeo = new THREE.BoxGeometry(2.6, 2.8, 5.8);
    const reeferMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.3 });
    const reefer = new THREE.Mesh(reeferGeo, reeferMat);
    reefer.position.set(0, 1.9, 1.6);
    reefer.castShadow = true;
    truckGroup.add(reefer);

    // Chiller Unit on top of Cabin
    const chillerGeo = new THREE.BoxGeometry(1.6, 0.8, 1.2);
    const chillerMat = new THREE.MeshStandardMaterial({ color: 0x19d3c5, roughness: 0.4 });
    const chiller = new THREE.Mesh(chillerGeo, chillerMat);
    chiller.position.set(0, 3.2, -1.0);
    truckGroup.add(chiller);

    // Rear Doors
    const leftDoorGeo = new THREE.BoxGeometry(1.25, 2.6, 0.1);
    const doorMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.3 });
    const leftDoor = new THREE.Mesh(leftDoorGeo, doorMat);
    leftDoor.position.set(-0.65, 1.9, 4.5);
    truckGroup.add(leftDoor);

    const rightDoorGeo = new THREE.BoxGeometry(1.25, 2.6, 0.1);
    const rightDoor = new THREE.Mesh(rightDoorGeo, doorMat);
    rightDoor.position.set(0.65, 1.9, 4.5);
    truckGroup.add(rightDoor);

    // Wheels
    const wheelGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.4, 16);
    const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.8 });
    wheelGeo.rotateZ(Math.PI / 2);

    const wheelPositions = [
      [-1.3, 0.5, -2.5],
      [1.3, 0.5, -2.5],
      [-1.3, 0.5, 1.8],
      [1.3, 0.5, 1.8],
      [-1.3, 0.5, 3.4],
      [1.3, 0.5, 3.4],
    ];

    wheelPositions.forEach((pos) => {
      const w = new THREE.Mesh(wheelGeo, wheelMat);
      w.position.set(pos[0], pos[1], pos[2]);
      w.castShadow = true;
      truckGroup.add(w);
    });

    scene.add(truckGroup);

    // 3. Instanced Produce (Tomatoes, Oranges, Carrots, Milk Cartons)
    const PRODUCE_COUNT = 90;
    const produceGeo = new THREE.DodecahedronGeometry(0.22, 1);
    const produceMat = new THREE.MeshStandardMaterial({
      color: 0xff5a36, // Vibrant tomato red/orange
      roughness: 0.4,
    });
    const produceMesh = new THREE.InstancedMesh(produceGeo, produceMat, PRODUCE_COUNT);
    produceMesh.castShadow = true;

    // Produce particle trajectories
    const produceData: Array<{
      origin: THREE.Vector3;
      velocity: THREE.Vector3;
      rotationSpeed: THREE.Vector3;
      color: THREE.Color;
    }> = [];

    const dummy = new THREE.Object3D();
    const colors = [
      new THREE.Color(0xff5a36), // Tomato
      new THREE.Color(0xffb627), // Citrus Orange
      new THREE.Color(0xb8f24a), // Lime/Lettuce
      new THREE.Color(0x6ec8ff), // Milk Carton / Frost
    ];

    for (let i = 0; i < PRODUCE_COUNT; i++) {
      const origin = new THREE.Vector3(
        (Math.random() - 0.5) * 1.6,
        1.2 + Math.random() * 1.5,
        3.5 + (Math.random() - 0.5) * 1.5
      );
      const angle = (Math.random() - 0.5) * Math.PI * 0.8;
      const speed = 2.5 + Math.random() * 4.5;
      const velocity = new THREE.Vector3(
        Math.sin(angle) * speed * 0.8,
        1.0 + Math.random() * 3.5,
        Math.cos(angle) * speed * 1.4 + 2.0
      );
      const rotationSpeed = new THREE.Vector3(
        (Math.random() - 0.5) * 6,
        (Math.random() - 0.5) * 6,
        (Math.random() - 0.5) * 6
      );
      const col = colors[i % colors.length];

      produceData.push({ origin, velocity, rotationSpeed, color: col });
      produceMesh.setColorAt(i, col);

      dummy.position.copy(origin);
      dummy.updateMatrix();
      produceMesh.setMatrixAt(i, dummy.matrix);
    }
    produceMesh.instanceColor!.needsUpdate = true;
    produceMesh.instanceMatrix.needsUpdate = true;
    scene.add(produceMesh);

    // 4. Glowing Reroute Line on Road (drawn in Beat 5)
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0, 0.05, 0),
      new THREE.Vector3(0.5, 0.05, -10),
      new THREE.Vector3(2.5, 0.05, -25),
      new THREE.Vector3(3.2, 0.05, -45),
    ]);
    const routeGeo = new THREE.TubeGeometry(curve, 40, 0.12, 8, false);
    const routeMat = new THREE.MeshBasicMaterial({ color: 0x19d3c5, transparent: true, opacity: 0.0 });
    const routeLine = new THREE.Mesh(routeGeo, routeMat);
    scene.add(routeLine);

    // Handle Resize
    const handleResize = () => {
      if (!mount) return;
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const time = clock.getElapsedTime();

      // Road texture / stripes looping motion
      stripesGroup.children.forEach((stripe) => {
        stripe.position.z += 12 * delta;
        if (stripe.position.z > 50) stripe.position.z -= 100;
      });

      // Story-driven choreography based on scrollProgress (0.0 to 1.0)
      const p = Math.max(0, Math.min(1, scrollProgress));

      // Beat 1: Cruise (0 - 0.18)
      // Beat 2: Failure (0.18 - 0.36)
      // Beat 3: The Burst (0.36 - 0.54)
      // Beat 4: Freeze & Think (0.54 - 0.72)
      // Beat 5: Reverse Rescue (0.72 - 0.90)
      // Beat 6: Launch (0.90 - 1.0)

      let burstProgress = 0;
      if (p < 0.36) {
        // Doors closed, truck driving nominal
        burstProgress = 0;
        leftDoor.rotation.y = 0;
        rightDoor.rotation.y = 0;
        camera.position.set(0, 3.8, 12);
        camera.lookAt(0, 2, 0);

        // Color temperature shift (Beat 2 warming)
        if (p > 0.18) {
          const warmFactor = (p - 0.18) / 0.18;
          tempLight.color.setRGB(1.0, 0.35 + 0.3 * (1 - warmFactor), 0.2 * (1 - warmFactor));
          scene.fog!.color.setRGB(0.98, 0.95 - 0.1 * warmFactor, 0.92 - 0.15 * warmFactor);
        } else {
          tempLight.color.setHex(0x6ec8ff);
          scene.fog!.color.setHex(0xf3fbfa);
        }
      } else if (p < 0.54) {
        // Beat 3: The Burst forward explosion
        const burstT = (p - 0.36) / 0.18;
        burstProgress = burstT;

        // Doors swing open
        leftDoor.rotation.y = -Math.min(Math.PI * 0.7, burstT * Math.PI * 0.75);
        rightDoor.rotation.y = Math.min(Math.PI * 0.7, burstT * Math.PI * 0.75);

        // Camera pushes in close to the cargo erupting toward lens
        camera.position.set(0, 2.6 + burstT * 0.4, 12 - burstT * 4.5);
        camera.lookAt(0, 2.2, 0);

        tempLight.color.setHex(0xff5a36); // Tomato heat flare
      } else if (p < 0.72) {
        // Beat 4: Freeze & Think (produce suspended mid-air)
        burstProgress = 0.85; // Frozen mid-flight
        leftDoor.rotation.y = -Math.PI * 0.7;
        rightDoor.rotation.y = Math.PI * 0.7;

        // Subtle gentle breathing float
        camera.position.set(Math.sin(time * 0.8) * 0.4, 3.2, 8.2);
        camera.lookAt(0, 2.3, 0);

        tempLight.color.setHex(0x19d3c5); // Analytical aqua thinking pulse
      } else if (p < 0.90) {
        // Beat 5: REVERSE RESCUE (Music-video reverse collapse!)
        const reverseT = (p - 0.72) / 0.18;
        burstProgress = Math.max(0, 0.85 * (1 - reverseT));

        // Doors slam shut in reverse
        leftDoor.rotation.y = -Math.PI * 0.7 * (1 - reverseT);
        rightDoor.rotation.y = Math.PI * 0.7 * (1 - reverseT);

        // Route line illuminates in brilliant cyan
        routeMat.opacity = Math.min(1.0, reverseT * 1.5);

        // Truck tilts toward exit route to FreshMart A
        truckGroup.position.x = reverseT * 1.8;
        truckGroup.rotation.y = -reverseT * 0.12;

        camera.position.set(2.0 * reverseT, 3.5, 9.5 - reverseT * 1.0);
        camera.lookAt(truckGroup.position.x, 2.0, 0);

        tempLight.color.setHex(0xb8f24a); // Verification success lime/aqua
      } else {
        // Beat 6: Launch (Camera pulls back wide)
        burstProgress = 0;
        leftDoor.rotation.y = 0;
        rightDoor.rotation.y = 0;
        routeMat.opacity = 0.8;

        camera.position.set(1.5, 5.5, 14.5);
        camera.lookAt(0, 2.0, 0);
        tempLight.color.setHex(0x19d3c5);
      }

      // Update instanced produce positions based on burstProgress
      for (let i = 0; i < PRODUCE_COUNT; i++) {
        const item = produceData[i];
        if (burstProgress <= 0.01) {
          // Inside truck container
          dummy.position.copy(item.origin);
          dummy.scale.set(0.7, 0.7, 0.7);
        } else {
          // Exploding out or reversing
          const t = burstProgress;
          dummy.position.set(
            item.origin.x + item.velocity.x * t,
            item.origin.y + item.velocity.y * t - 0.5 * 9.8 * (t * t * 0.35),
            item.origin.z + item.velocity.z * t
          );
          dummy.rotation.x = item.rotationSpeed.x * t * 4;
          dummy.rotation.y = item.rotationSpeed.y * t * 4;
          dummy.rotation.z = item.rotationSpeed.z * t * 4;
          dummy.scale.set(1.0, 1.0, 1.0);
        }
        dummy.updateMatrix();
        produceMesh.setMatrixAt(i, dummy.matrix);
      }
      produceMesh.instanceMatrix.needsUpdate = true;

      // Subtle truck suspension vibration
      truckGroup.position.y = Math.sin(time * 14) * 0.015;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animId);
      if (mount && renderer.domElement) {
        mount.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [scrollProgress]);

  return (
    <div
      ref={mountRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 1,
      }}
      aria-hidden="true"
    />
  );
};
