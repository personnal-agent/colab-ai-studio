import '@testing-library/jest-dom';

// Polyfills / mocks for jsdom if needed
if (typeof window !== 'undefined') {
  window.HTMLElement.prototype.scrollIntoView = () => {};
}
