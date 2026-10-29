import '@testing-library/jest-dom';

if (typeof window !== 'undefined') {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };

  if (window.HTMLElement) {
    window.HTMLElement.prototype.scrollIntoView = function () {};
    window.HTMLElement.prototype.hasPointerCapture = function () {
      return false;
    };
    window.HTMLElement.prototype.setPointerCapture = function () {};
    window.HTMLElement.prototype.releasePointerCapture = function () {};
  }

  if (typeof HTMLCanvasElement !== 'undefined') {
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      contextId: string
    ): CanvasRenderingContext2D | null {
      if (contextId === '2d') {
        return {
          clearRect: () => {},
          fillRect: () => {},
          strokeRect: () => {},
          fillText: () => {},
          save: () => {},
          restore: () => {},
          scale: () => {},
          translate: () => {},
          beginPath: () => {},
          stroke: () => {},
          fill: () => {},
          moveTo: () => {},
          lineTo: () => {},
          measureText: () => ({ width: 50 } as TextMetrics),
        } as unknown as CanvasRenderingContext2D;
      }
      return null;
    } as unknown as typeof HTMLCanvasElement.prototype.getContext;
  }
}
