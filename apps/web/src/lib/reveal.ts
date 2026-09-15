export function revealElement(element: HTMLElement | null, block: ScrollLogicalPosition = 'start', shouldReveal?: () => boolean) {
  if (!element) return;
  const frame = window.requestAnimationFrame(() => {
    if (!element.isConnected || element.closest('[hidden]') || shouldReveal?.() === false) return;
    const behavior: ScrollBehavior = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    element.focus({ preventScroll: true });
    element.scrollIntoView({ behavior, block });
  });
  return () => window.cancelAnimationFrame(frame);
}
