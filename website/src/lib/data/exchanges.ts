export const EXCHANGES = ['mexc', 'coinex', 'bingx', 'weex'] as const;

/** Legacy exchanges kept loadable for archived pair report URLs (e.g. email campaigns). */
export const LEGACY_EXCHANGE_SLUGS = ['bitmart'] as const;

export type ExchangeSlug = (typeof EXCHANGES)[number];

export type LoadableExchangeSlug = ExchangeSlug | (typeof LEGACY_EXCHANGE_SLUGS)[number];

export const DEFAULT_EXCHANGE: ExchangeSlug = 'mexc';

export function isExchangeSlug(value: string): value is LoadableExchangeSlug {
  return (
    (EXCHANGES as readonly string[]).includes(value) ||
    (LEGACY_EXCHANGE_SLUGS as readonly string[]).includes(value)
  );
}

export function isActiveExchangeSlug(value: string): value is ExchangeSlug {
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
