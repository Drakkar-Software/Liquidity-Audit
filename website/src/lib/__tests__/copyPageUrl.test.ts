import { afterEach, describe, expect, it, vi } from 'vitest';
import { copyPageUrl } from '../copyPageUrl';

describe('copyPageUrl', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('rejects when the Clipboard API is not available', async () => {
    vi.stubGlobal('navigator', { clipboard: undefined });

    await expect(copyPageUrl('https://example.com/pairs/mexc/sol_usdt')).rejects.toThrow(
      'Clipboard API is not available',
    );
  });

  it('resolves when clipboard write succeeds', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { clipboard: { writeText } });

    await copyPageUrl('https://example.com/report');

    expect(writeText).toHaveBeenCalledWith('https://example.com/report');
  });

  it('rejects when clipboard write fails', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('Permission denied'));
    vi.stubGlobal('navigator', { clipboard: { writeText } });

    await expect(copyPageUrl('https://example.com/report')).rejects.toThrow('Permission denied');
  });
});
