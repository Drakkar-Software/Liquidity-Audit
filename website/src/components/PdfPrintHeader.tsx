import type { TokenViewModel } from '../types';
import { buildPdfMetaLine } from '../lib/pdfExport';
import { SITE_NAME } from '../lib/siteMeta';

export interface PdfPrintHeaderProps {
  vm: TokenViewModel;
}

/** Print-only header injected at the top of token report exports. */
export function PdfPrintHeader({ vm }: PdfPrintHeaderProps) {
  return (
    <div className="print-only pdf-print-header">
      <p className="pdf-print-title">{SITE_NAME}</p>
      <p className="pdf-print-meta">{buildPdfMetaLine(vm)}</p>
      <p className="pdf-print-disclaimer">Independent analysis · Not financial advice</p>
    </div>
  );
}
