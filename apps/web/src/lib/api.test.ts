import { describe, expect, it } from 'vitest';

import { resolveApiBaseUrl } from './api';

describe('resolveApiBaseUrl', () => {
  it('keeps the existing local development default', () => {
    expect(resolveApiBaseUrl(undefined, false)).toBe('http://localhost:8000');
  });

  it('fails closed to the same-origin Worker API in a hosted build', () => {
    expect(resolveApiBaseUrl(undefined, true)).toBe('/api');
    expect(resolveApiBaseUrl('/api/', true)).toBe('/api');
  });
});
