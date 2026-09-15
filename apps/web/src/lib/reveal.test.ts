import { afterEach, describe, expect, it, vi } from 'vitest';
import { revealElement } from './reveal';

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  document.body.replaceChildren();
});

describe('revealElement', () => {
  it('does not scroll a stale target removed before the animation frame', async () => {
    vi.useFakeTimers();
    const scroll = vi.spyOn(Element.prototype, 'scrollIntoView');
    const button = document.createElement('button');
    document.body.append(button);
    revealElement(button);
    button.remove();
    await vi.runOnlyPendingTimersAsync();
    expect(scroll).not.toHaveBeenCalled();
  });

  it('uses non-animated scrolling when reduced motion is requested', async () => {
    vi.useFakeTimers();
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })));
    const scroll = vi.spyOn(Element.prototype, 'scrollIntoView');
    const button = document.createElement('button');
    document.body.append(button);
    revealElement(button);
    await vi.runOnlyPendingTimersAsync();
    expect(scroll).toHaveBeenCalledWith({ behavior: 'auto', block: 'start' });
  });
});
