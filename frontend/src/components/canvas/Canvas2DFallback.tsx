import React, { useEffect, useRef, useState } from 'react';
import type { CanvasAssetLayer } from '../../types/studio';

export interface Canvas2DFallbackProps {
  layers: CanvasAssetLayer[];
  zoomLevel: number;
  className?: string;
}

export const Canvas2DFallback: React.FC<Canvas2DFallbackProps> = ({
  layers,
  zoomLevel,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [fps, setFps] = useState(60);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let ctx: CanvasRenderingContext2D | null = null;
    try {
      ctx = canvas.getContext('2d');
    } catch {
      ctx = null;
    }
    if (!ctx) return;

    let animationFrameId: number;
    let lastTime = performance.now();
    let frameCount = 0;

    const render = (time: number) => {
      frameCount++;
      if (time - lastTime >= 1000) {
        setFps(Math.round((frameCount * 1000) / (time - lastTime)));
        frameCount = 0;
        lastTime = time;
      }

      const width = canvas.width;
      const height = canvas.height;

      // Clear frame
      ctx.clearRect(0, 0, width, height);

      // Save context state for transform
      ctx.save();

      // Transform according to zoom level
      const scale = zoomLevel / 100;
      ctx.translate(width / 2, height / 2);
      ctx.scale(scale, scale);
      ctx.translate(-width / 2, -height / 2);

      // Draw subtle background grid
      ctx.strokeStyle = '#E2E8F0';
      ctx.lineWidth = 1;
      const gridSize = 40;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Draw active layers
      layers.forEach((layer, idx) => {
        const x = 60 + (idx % 3) * 220;
        const y = 50 + Math.floor(idx / 3) * 140;
        const w = 200;
        const h = 110;

        // Card background
        ctx.fillStyle =
          layer.type === 'mesh_3d'
            ? 'rgba(238, 242, 255, 0.95)'
            : layer.type === 'video'
            ? 'rgba(243, 232, 255, 0.95)'
            : 'rgba(241, 245, 249, 0.95)';
        ctx.strokeStyle =
          layer.type === 'mesh_3d' ? '#6366F1' : layer.type === 'video' ? '#9333EA' : '#64748B';
        ctx.lineWidth = 2;

        ctx.beginPath();
        ctx.roundRect ? ctx.roundRect(x, y, w, h, 8) : ctx.rect(x, y, w, h);
        ctx.fill();
        ctx.stroke();

        // Layer Title
        ctx.fillStyle = '#0F172A';
        ctx.font = 'bold 12px ui-sans-serif, system-ui, sans-serif';
        const truncatedName = layer.name.length > 22 ? `${layer.name.slice(0, 20)}...` : layer.name;
        ctx.fillText(truncatedName, x + 12, y + 26);

        // Layer Metadata Badge
        ctx.fillStyle =
          layer.type === 'mesh_3d' ? '#4F46E5' : layer.type === 'video' ? '#7E22CE' : '#475569';
        ctx.font = '10px ui-monospace, monospace';
        ctx.fillText(`[${layer.type.toUpperCase()}] · ${layer.taskId.slice(0, 8)}`, x + 12, y + 46);

        // Simulation wireframe / visual placeholder
        if (layer.type === 'mesh_3d') {
          ctx.strokeStyle = '#818CF8';
          ctx.strokeRect(x + 12, y + 56, 40, 40);
          ctx.beginPath();
          ctx.moveTo(x + 12, y + 56);
          ctx.lineTo(x + 52, y + 96);
          ctx.moveTo(x + 52, y + 56);
          ctx.lineTo(x + 12, y + 96);
          ctx.stroke();
        } else {
          ctx.fillStyle = '#CBD5E1';
          ctx.fillRect(x + 12, y + 56, 40, 40);
        }

        ctx.fillStyle = '#64748B';
        ctx.font = '10px ui-sans-serif, system-ui, sans-serif';
        ctx.fillText('Rendu Canvas2D Actif', x + 60, y + 80);
      });

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [layers, zoomLevel]);

  return (
    <div className={`relative w-full h-full flex flex-col items-center justify-center ${className}`}>
      <canvas
        ref={canvasRef}
        data-testid="canvas-2d-surface"
        width={960}
        height={540}
        className="w-full h-full rounded-xl shadow-inner border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 object-contain"
      />
      <div className="absolute bottom-3 right-3 px-2 py-1 bg-black/75 backdrop-blur-xs text-white rounded text-[10px] font-mono flex items-center space-x-1.5 shadow-sm">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
        <span>Canvas2D Fallback ({fps} FPS)</span>
      </div>
    </div>
  );
};
