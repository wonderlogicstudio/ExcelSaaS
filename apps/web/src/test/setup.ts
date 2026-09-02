import '@testing-library/jest-dom/vitest';

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

if (!window.requestAnimationFrame) {
  window.requestAnimationFrame = (callback: FrameRequestCallback) => window.setTimeout(callback, 0);
}

if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => undefined;
}
