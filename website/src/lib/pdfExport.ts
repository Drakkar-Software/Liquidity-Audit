import type { TokenViewModel } from '../types';

function formatPdfExportDate(date: Date): string {
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatPdfFilenameDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function sanitizeFilenamePart(value: string): string {
  return value
    .trim()
    .replace(/\//g, '-')
    .replace(/[^\w.-]+/g, '_');
}

/** Meta line shown in the PDF print header. */
export function buildPdfMetaLine(vm: TokenViewModel): string {
  const generatedOn = formatPdfExportDate(new Date());
  const parts = [vm.pair, vm.exchange, `Analysis as of ${generatedOn}`];
  if (vm.updatedAgo) {
    parts.push(`(fetched ${vm.updatedAgo})`);
  }
  return parts.join(' · ');
}

/** Suggested save-as filename for browser print-to-PDF (via document.title). */
export function buildPdfDownloadTitle(vm: TokenViewModel): string {
  const exchangePart = sanitizeFilenamePart(vm.exchange.toUpperCase());
  const pairPart = sanitizeFilenamePart(vm.pair);
  const datePart = formatPdfFilenameDate(new Date());
  return `Liquidity-Audit_${exchangePart}_${pairPart}_${datePart}`;
}

/** Opens the browser print dialog for saving the token report as PDF. */
export function exportTokenReportPdf(vm: TokenViewModel): void {
  const previousTitle = document.title;
  document.title = buildPdfDownloadTitle(vm);

  const restoreTitle = () => {
    document.title = previousTitle;
    window.removeEventListener('afterprint', restoreTitle);
  };

  window.addEventListener('afterprint', restoreTitle);
  window.print();
}
