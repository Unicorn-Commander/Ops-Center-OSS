import React, { useEffect, useRef } from 'react';

/**
 * Galaxy Background Component
 * Renders an animated gradient background that shifts between purple-blue space colors
 */
export function GalaxyBackground() {
  return (
    <div
      className="fixed inset-0 -z-50"
      style={{
        background: 'linear-gradient(135deg, #1a0033 0%, #220044 25%, #0a1929 50%, #3a0e5a 75%, #1a0033 100%)',
        backgroundSize: '400% 400%',
        animation: 'galaxyShift 20s ease infinite'
      }}
    />
  );
}

/**
 * Stars Container Component
 * Generates and animates twinkling stars that float across the screen
 */
export function StarsContainer() {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const starCount = 30;

    // Create stars
    for (let i = 0; i < starCount; i++) {
      const star = document.createElement('div');
      star.className = 'absolute bg-white';

      // Star shape using clip-path (10-pointed star)
      star.style.clipPath = 'polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)';

      // Random size
      const size = Math.random() * 15 + 10;
      star.style.width = size + 'px';
      star.style.height = size + 'px';

      // Random position (starts off-screen left)
      star.style.top = Math.random() * 100 + '%';
      star.style.left = '-100px';

      // Random animation delay and duration for natural movement
      star.style.animationDelay = Math.random() * 20 + 's';
      star.style.animationDuration = Math.random() * 10 + 15 + 's';

      // Add twinkle animation
      star.style.animation = `twinkle 3s infinite ${Math.random() * 3}s, floatStar ${star.style.animationDuration} infinite linear ${star.style.animationDelay}`;

      container.appendChild(star);
    }

    // Cleanup
    return () => {
      container.innerHTML = '';
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 -z-40 pointer-events-none"
    />
  );
}

/**
 * Neural Network Component
 * Renders animated nodes and connections resembling a neural network
 */
export function NeuralNetwork() {
  const networkRef = useRef(null);

  useEffect(() => {
    if (!networkRef.current) return;

    const network = networkRef.current;
    const nodeCount = 20;

    // Create pulsing nodes
    for (let i = 0; i < nodeCount; i++) {
      const node = document.createElement('div');
      node.className = 'absolute w-[3px] h-[3px] rounded-full';

      // Purple gradient glow
      node.style.background = 'radial-gradient(circle, rgba(138, 43, 226, 0.8) 0%, transparent 70%)';

      // Random position
      node.style.left = Math.random() * 100 + '%';
      node.style.top = Math.random() * 100 + '%';

      // Add pulse animation with random delay
      node.style.animation = `neuralPulse 4s infinite ${Math.random() * 4}s`;

      network.appendChild(node);
    }

    // Create flowing connections between nodes
    for (let i = 0; i < nodeCount / 2; i++) {
      const connection = document.createElement('div');
      connection.className = 'absolute h-[1px] opacity-50';

      // Gradient line
      connection.style.background = 'linear-gradient(90deg, transparent, rgba(138, 43, 226, 0.3), transparent)';

      // Random position and length
      connection.style.left = Math.random() * 100 + '%';
      connection.style.top = Math.random() * 100 + '%';
      connection.style.width = Math.random() * 200 + 100 + 'px';

      // Random rotation
      connection.style.transform = `rotate(${Math.random() * 360}deg)`;

      // Add flow animation
      connection.style.animation = `connectionFlow 3s infinite ${Math.random() * 3}s`;

      network.appendChild(connection);
    }

    // Cleanup
    return () => {
      network.innerHTML = '';
    };
  }, []);

  return (
    <div
      ref={networkRef}
      className="fixed inset-0 -z-30 opacity-10 pointer-events-none"
    />
  );
}

/**
 * Combined Background Effects
 * Convenience component that renders all background layers
 */
export default function BackgroundEffects() {
  return (
    <>
      <GalaxyBackground />
      <StarsContainer />
      <NeuralNetwork />
    </>
  );
}
