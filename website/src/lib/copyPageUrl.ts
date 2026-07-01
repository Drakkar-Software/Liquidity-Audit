/** Copies a URL to the system clipboard. Rejects when the Clipboard API is unavailable or the write fails. */
export function copyPageUrl(url: string): Promise<void> {
  if (!navigator.clipboard?.writeText) {
    return Promise.reject(new Error('Clipboard API is not available'));
  }

  return navigator.clipboard.writeText(url).catch((clipboardError: unknown) => {
    const message =
      clipboardError instanceof Error ? clipboardError.message : 'Clipboard write failed';
    throw new Error(message);
  });
}
