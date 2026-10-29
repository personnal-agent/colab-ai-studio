/**
 * Graphics capability detection service.
 * Determines if hardware WebGPU is supported or gracefully falls back to Canvas2D (Intel HD Graphics 520 target).
 */

export interface GraphicsCapabilityResult {
  supported: boolean;
  renderer: 'webgpu' | 'canvas2d';
  adapterInfo?: string;
  reason?: string;
}

interface WebGPUAdapterInfo {
  vendor?: string;
  architecture?: string;
  device?: string;
  description?: string;
}

interface WebGPUAdapter {
  info?: WebGPUAdapterInfo;
}

interface NavigatorGPU {
  requestAdapter: (options?: { powerPreference?: string }) => Promise<WebGPUAdapter | null>;
}

export async function detectGraphicsCapability(): Promise<GraphicsCapabilityResult> {
  if (typeof navigator === 'undefined' || !('gpu' in navigator) || !navigator.gpu) {
    return {
      supported: false,
      renderer: 'canvas2d',
      reason: 'WebGPU non supporté par ce navigateur ou environnement hôte.',
    };
  }

  try {
    const gpu = navigator.gpu as unknown as NavigatorGPU;
    const adapter = await gpu.requestAdapter({
      powerPreference: 'high-performance',
    });

    if (!adapter) {
      return {
        supported: false,
        renderer: 'canvas2d',
        reason: 'Aucun adaptateur GPU compatible WebGPU détecté (repli Canvas2D Intel HD 520).',
      };
    }

    let adapterInfo = 'GPU Accéléré';
    if ('info' in adapter && adapter.info) {
      const info = adapter.info;
      adapterInfo = `${info.vendor || 'GPU'} ${info.architecture || ''}`.trim();
    }

    return {
      supported: true,
      renderer: 'webgpu',
      adapterInfo,
    };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    return {
      supported: false,
      renderer: 'canvas2d',
      reason: `Échec d'initialisation WebGPU: ${errorMsg}`,
    };
  }
}
