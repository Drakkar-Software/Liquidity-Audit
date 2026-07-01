import { AnalysisFetchError } from './loader';

function isMissingAnalysisError(error: unknown): boolean {
  if (error instanceof AnalysisFetchError) {
    return error.status === 404 || error.invalidJson;
  }
  if (error instanceof SyntaxError) {
    return true;
  }
  return false;
}

function exchangeLabel(exchange: string): string {
  return exchange.toUpperCase();
}

/** User-facing detail for pair report load failures. */
export function pairAnalysisErrorMessage(exchange: string, pair: string, error?: unknown): string {
  if (!exchange || !pair || error === undefined) {
    return 'The report URL is invalid.';
  }

  const labeledExchange = exchangeLabel(exchange);
  if (isMissingAnalysisError(error)) {
    return `No analysis for ${pair} on ${labeledExchange}. No analysis available for this pair on this exchange.`;
  }

  return `No analysis for ${pair} on ${labeledExchange}. The report could not be loaded right now.`;
}

/** User-facing detail for rankings load failures. */
export function rankingsErrorMessage(exchange: string, error: unknown): string {
  if (isMissingAnalysisError(error)) {
    return `Could not load rankings for ${exchangeLabel(exchange)}.`;
  }

  return 'Rankings data could not be loaded.';
}
