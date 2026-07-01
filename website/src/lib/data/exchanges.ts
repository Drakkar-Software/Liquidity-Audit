export const EXCHANGES = ['mexc', 'bitmart'] as const;

export type ExchangeSlug = (typeof EXCHANGES)[number];

export const DEFAULT_EXCHANGE: ExchangeSlug = 'mexc';

export function isExchangeSlug(value: string): value is ExchangeSlug {
  return (EXCHANGES as readonly string[]).includes(value);
}

export function capitalizeExchange(exchange: string): string {
  if (!exchange) {
    return '';
  }
  return exchange.charAt(0).toUpperCase() + exchange.slice(1);
}

export function exchangeLabel(exchange: string): string {
  return exchange.toUpperCase();
}
