import { useEffect, useRef, useState } from 'react';
import { colors, fonts } from '../theme';
import type { RankingsViewModel } from '../types';
import { EXCHANGES } from '../lib/data/exchanges';
import { filterPairCatalog, normalizePairInput } from '../lib/data/loader';
import { Screen } from '../components/Screen';
import { ExchangeSelect } from '../components/ExchangeSelect';
import { GuidesSection } from '../components/GuidesSection';
import { QuickLinksSkeleton, RankingsTableSkeleton } from '../components/RankingsSkeleton';
import { SiteTextLink } from '../components/SiteTextLink';

export interface ComparisonProps {
  rankings: RankingsViewModel | null;
  exchange: string;
  pairCatalog: string[];
  rankingsError?: string | null;
  onExchangeChange: (exchange: string) => void;
  onOpenReport: (pair: string) => void;
}

const WHY = [
  { title: 'Price stability', body: 'Deep books absorb orders without violent moves.' },
  { title: 'Investor confidence', body: 'Allocators size in only when exit cost is low.' },
  { title: 'Exchange attractiveness', body: 'Liquidity keeps a listing healthy and visible.' },
  { title: 'Less execution waste', body: 'Deep books mean less capital lost to spread on each trade.' },
];

const GRADES: { label: string; color: string; bg: string }[] = [
  { label: 'A 85+', color: colors.green, bg: 'rgba(70,196,106,.12)' },
  { label: 'B 70+', color: colors.green, bg: 'rgba(70,196,106,.1)' },
  { label: 'C 55+', color: colors.amber, bg: 'rgba(224,168,58,.12)' },
  { label: 'D 40+', color: colors.red, bg: 'rgba(240,88,77,.1)' },
  { label: 'F <40', color: colors.red, bg: 'rgba(240,88,77,.12)' },
];

const REPORT_CONTENTS = [
  'Summary & issue checks',
  'Health dashboard vs exchange avg',
  'Peer comparison table & chart',
  'Investor simulator (overpay)',
  'Lost opportunity estimate',
  'Root cause analysis',
  'Improvement potential & roadmap',
  'Implementation options',
];

const scoreColor = (score: number): string =>
  score >= 70 ? colors.green : score >= 55 ? colors.amber : colors.red;

export function Comparison({
  rankings,
  exchange,
  pairCatalog,
  rankingsError = null,
  onExchangeChange,
  onOpenReport,
}: ComparisonProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const pairSearchListboxId = 'pair-search-listbox';
  const quickLinks = rankings?.rows.slice(0, 4).map((row) => row.symbol) ?? [];
  const suggestions = filterPairCatalog(pairCatalog, searchQuery);
  const suggestionsVisible = suggestionsOpen && suggestions.length > 0;

  useEffect(() => {
    if (highlightedIndex >= suggestions.length) {
      setHighlightedIndex(suggestions.length > 0 ? suggestions.length - 1 : -1);
    }
  }, [highlightedIndex, suggestions.length]);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (!searchContainerRef.current?.contains(event.target as Node)) {
        setSuggestionsOpen(false);
        setHighlightedIndex(-1);
      }
    };
    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, []);

  const closeSuggestions = () => {
    setSuggestionsOpen(false);
    setHighlightedIndex(-1);
  };

  const openSuggestions = () => {
    setSuggestionsOpen(true);
  };

  const moveHighlight = (direction: 1 | -1) => {
    if (suggestions.length === 0) {
      return;
    }
    openSuggestions();
    setHighlightedIndex((currentIndex) => {
      if (currentIndex < 0) {
        return direction === 1 ? 0 : suggestions.length - 1;
      }
      const nextIndex = currentIndex + direction;
      if (nextIndex < 0) {
        return suggestions.length - 1;
      }
      if (nextIndex >= suggestions.length) {
        return 0;
      }
      return nextIndex;
    });
  };

  const resolveSuggestionForSubmit = (): string | undefined => {
    if (suggestionsVisible) {
      if (highlightedIndex >= 0) {
        return suggestions[highlightedIndex];
      }
      return suggestions[0];
    }
    return undefined;
  };

  const submitSearch = (pairInput?: string) => {
    const normalized = normalizePairInput(pairInput ?? searchQuery);
    if (!normalized) {
      return;
    }
    closeSuggestions();
    onOpenReport(normalized);
  };

  return (
    <Screen active="Comparison">
      <div
        className="page-section comparison-hero"
        style={{
          textAlign: 'center',
          borderBottom: `1px solid ${colors.line}`,
          background: 'radial-gradient(900px 300px at 50% -40%,rgba(54,214,195,.08),transparent)',
        }}
      >
        <h1
          className="page-hero-title"
          style={{
            margin: '0 0 10px',
            font: `600 38px ${fonts.sans}`,
            color: colors.ink,
            letterSpacing: '-.01em',
          }}
        >
          Token Liquidity Ranking
        </h1>
        <p
          style={{
            margin: '0 auto 28px',
            maxWidth: 640,
            font: `400 16px/1.5 ${fonts.sans}`,
            color: colors.ink2,
          }}
        >
          Crypto liquidity analysis from one visible order-book snapshot per pair: liquidity score,
          spread, depth, and slippage for a liquidity audit crypto teams can share with investors.
        </p>

        <div ref={searchContainerRef} style={{ maxWidth: 680, margin: '0 auto', position: 'relative' }}>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              const suggestion = resolveSuggestionForSubmit();
              if (suggestion) {
                submitSearch(suggestion);
                return;
              }
              submitSearch();
            }}
          >
            <div
              className="comparison-search-row"
              style={{
                border: `1px solid ${colors.line2}`,
                borderRadius: 10,
                background: colors.panel,
                padding: 8,
              }}
            >
              <input
                id="pair-search-input"
                role="combobox"
                aria-label="Search trading pair"
                aria-autocomplete="list"
                aria-expanded={suggestionsVisible}
                aria-controls={pairSearchListboxId}
                aria-activedescendant={
                  highlightedIndex >= 0 ? `pair-suggestion-${highlightedIndex}` : undefined
                }
                value={searchQuery}
                onChange={(event) => {
                  setSearchQuery(event.target.value);
                  setHighlightedIndex(-1);
                  openSuggestions();
                }}
                onFocus={openSuggestions}
                onKeyDown={(event) => {
                  if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    moveHighlight(1);
                    return;
                  }
                  if (event.key === 'ArrowUp') {
                    event.preventDefault();
                    moveHighlight(-1);
                    return;
                  }
                  if (event.key === 'Enter') {
                    const suggestion = resolveSuggestionForSubmit();
                    if (suggestion) {
                      event.preventDefault();
                      submitSearch(suggestion);
                    }
                    return;
                  }
                  if (event.key === 'Escape') {
                    closeSuggestions();
                  }
                }}
                placeholder="TOKEN/USDT"
                style={{
                  flex: 1,
                  alignSelf: 'center',
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  font: `500 15px ${fonts.mono}`,
                  color: colors.ink,
                  padding: '0 14px',
                }}
              />
              <ExchangeSelect variant="search" value={exchange} onChange={onExchangeChange} />
              <button
                type="submit"
                style={{
                  font: `600 13px ${fonts.mono}`,
                  color: colors.accentInk,
                  background: colors.accent,
                  borderRadius: 7,
                  padding: '12px 22px',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                Open report
              </button>
            </div>
          </form>

          {suggestionsVisible ? (
            <div
              id={pairSearchListboxId}
              role="listbox"
              style={{
                position: 'absolute',
                top: 'calc(100% + 6px)',
                left: 0,
                right: 0,
                background: colors.panel,
                border: `1px solid ${colors.line2}`,
                borderRadius: 8,
                overflow: 'hidden',
                zIndex: 10,
                textAlign: 'left',
              }}
            >
              {suggestions.map((symbol, suggestionIndex) => {
                const isHighlighted = suggestionIndex === highlightedIndex;
                return (
                  <button
                    key={symbol}
                    id={`pair-suggestion-${suggestionIndex}`}
                    type="button"
                    role="option"
                    aria-selected={isHighlighted}
                    onMouseEnter={() => setHighlightedIndex(suggestionIndex)}
                    onClick={() => submitSearch(symbol)}
                    style={{
                      display: 'block',
                      width: '100%',
                      padding: '10px 16px',
                      background: isHighlighted ? colors.panel2 : 'transparent',
                      border: 'none',
                      borderBottom: `1px solid ${colors.line}`,
                      font: `500 13px ${fonts.mono}`,
                      color: colors.ink,
                      textAlign: 'left',
                      cursor: 'pointer',
                    }}
                  >
                    {symbol}
                  </button>
                );
              })}
            </div>
          ) : null}
        </div>

        {rankings ? (
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 22, flexWrap: 'wrap' }}>
            <span style={{ font: `500 11px ${fonts.sans}`, color: colors.ink3, alignSelf: 'center' }}>
              Quick links:
            </span>
            {quickLinks.map((symbol) => (
              <button
                key={symbol}
                type="button"
                onClick={() => onOpenReport(symbol)}
                style={{
                  font: `500 12px ${fonts.mono}`,
                  color: colors.ink2,
                  border: `1px solid ${colors.line2}`,
                  borderRadius: 20,
                  padding: '6px 13px',
                  background: 'transparent',
                  cursor: 'pointer',
                }}
              >
                {symbol}
              </button>
            ))}
          </div>
        ) : rankingsError ? null : (
          <QuickLinksSkeleton />
        )}
      </div>

      <div className="page-section" style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
        <p
          style={{
            margin: 0,
            font: `400 14px/1.6 ${fonts.sans}`,
            color: colors.ink2,
          }}
        >
          Use exchange liquidity comparison to rank token liquidity on each venue. Each report is
          order book liquidity analysis from one snapshot: pick an exchange, search a pair, open the
          report. See <SiteTextLink to="/methodology">Methodology</SiteTextLink> or the guides below for
          definitions.
        </p>

        <div>
          <h2 style={{ margin: '0 0 14px', font: `600 16px ${fonts.sans}`, color: colors.ink }}>
            Why liquidity matters
          </h2>
          <div className="grid-why">
            {WHY.map((item) => (
              <div
                key={item.title}
                style={{
                  border: `1px solid ${colors.line}`,
                  borderRadius: 8,
                  background: colors.panel,
                  padding: 16,
                }}
              >
                <div style={{ font: `600 13px ${fonts.sans}`, color: colors.ink, marginBottom: 6 }}>
                  {item.title}
                </div>
                <div style={{ font: `400 12px/1.5 ${fonts.sans}`, color: colors.ink2 }}>
                  {item.body}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid-score-report">
          <div
            style={{
              border: `1px solid ${colors.line}`,
              borderRadius: 8,
              background: colors.panel,
              padding: 20,
            }}
          >
            <h2 style={{ margin: '0 0 12px', font: `600 16px ${fonts.sans}`, color: colors.ink }}>
              The liquidity score
            </h2>
            <p style={{ margin: '0 0 14px', font: `400 13px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
              A single 0–100 number with an A–F grade: half from order-book shape, half from how
              spread, depth, and slippage compare to similar pairs on the same exchange.
            </p>
            <div className="grades-row">
              {GRADES.map((grade) => (
                <span
                  key={grade.label}
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    font: `600 12px ${fonts.mono}`,
                    color: grade.color,
                    background: grade.bg,
                    borderRadius: 5,
                    padding: '8px 0',
                  }}
                >
                  {grade.label}
                </span>
              ))}
            </div>
            <div style={{ marginTop: 14 }}>
              <SiteTextLink to="/methodology">How scoring works → Methodology</SiteTextLink>
            </div>
          </div>

          <div
            style={{
              border: `1px solid ${colors.line}`,
              borderRadius: 8,
              background: colors.panel,
              padding: 20,
            }}
          >
            <h2 style={{ margin: '0 0 12px', font: `600 16px ${fonts.sans}`, color: colors.ink }}>
              What&apos;s in a report
            </h2>
            <div
              className="grid-two"
              style={{
                font: `400 12px ${fonts.sans}`,
                color: colors.ink2,
              }}
            >
              {REPORT_CONTENTS.map((content) => (
                <span key={content}>· {content}</span>
              ))}
            </div>
          </div>
        </div>

        <Rankings
          rankings={rankings}
          rankingsError={rankingsError}
          exchange={exchange}
          onExchangeChange={onExchangeChange}
          onOpenReport={onOpenReport}
        />

        <GuidesSection />
      </div>
    </Screen>
  );
}

interface RankingsProps {
  rankings: RankingsViewModel | null;
  rankingsError?: string | null;
  exchange: string;
  onExchangeChange: (exchange: string) => void;
  onOpenReport: (pair: string) => void;
}

function Rankings({
  rankings,
  rankingsError = null,
  exchange,
  onExchangeChange,
  onOpenReport,
}: RankingsProps) {
  return (
    <div>
      <div className="rankings-header">
        <h2 style={{ margin: 0, font: `600 16px ${fonts.sans}`, color: colors.ink }}>
          Public rankings
        </h2>
        <div style={{ display: 'flex', gap: 6 }}>
          {EXCHANGES.map((exchangeSlug) => {
            const active = exchange === exchangeSlug;
            return (
              <button
                key={exchangeSlug}
                type="button"
                onClick={() => onExchangeChange(exchangeSlug)}
                style={{
                  font: `600 11px ${fonts.mono}`,
                  color: active ? colors.accentInk : colors.ink2,
                  background: active ? colors.accent : 'transparent',
                  border: active ? 'none' : `1px solid ${colors.line2}`,
                  borderRadius: 5,
                  padding: '6px 12px',
                  cursor: 'pointer',
                }}
              >
                {exchangeSlug.toUpperCase()}
              </button>
            );
          })}
        </div>
      </div>

      {rankingsError ? (
        <p
          role="alert"
          style={{ margin: '12px 0 0', font: `400 13px/1.5 ${fonts.sans}`, color: colors.red }}
        >
          {rankingsError}
        </p>
      ) : null}

      {rankings ? (
        <>
          <p style={{ margin: '0 0 12px', font: `400 12px ${fonts.sans}`, color: colors.ink3 }}>
            Top 20 spot pairs by liquidity score (24h volume ≥ $1k). Updated {rankings.updatedLabel}.
          </p>

          <div className="rankings-scroll" style={{ borderColor: colors.line }}>
            <div className="rankings-table">
              <div
                className="rankings-grid"
                style={{
                  background: colors.tableHead,
                  borderBottom: `1px solid ${colors.line}`,
                  font: `500 10px ${fonts.mono}`,
                  letterSpacing: '.08em',
                  color: colors.ink3,
                }}
              >
                <span style={{ padding: '10px 16px' }}>#</span>
                <span style={{ padding: '10px 16px' }}>PROJECT</span>
                <span style={{ padding: '10px 16px', textAlign: 'right' }}>SCORE</span>
                <span style={{ padding: '10px 16px', textAlign: 'right' }}>24H VOL</span>
              </div>
              {rankings.rows.map((row, rowIndex) => (
                <button
                  key={row.symbol}
                  type="button"
                  onClick={() => onOpenReport(row.symbol)}
                  className="rankings-grid"
                  style={{
                    width: '100%',
                    border: 'none',
                    borderBottom: rowIndex < rankings.rows.length - 1 ? `1px solid ${colors.line}` : 'none',
                    borderLeft: row.highlight ? `3px solid ${colors.red}` : 'none',
                    background: row.highlight ? 'rgba(240,88,77,.06)' : 'transparent',
                    font: `${row.highlight ? 600 : 500} 13px ${fonts.mono}`,
                    color: colors.ink2,
                    textAlign: 'left',
                    cursor: 'pointer',
                    padding: 0,
                  }}
                >
                  <span style={{ padding: '10px 16px', color: colors.ink3 }}>{row.rank}</span>
                  <span style={{ padding: '10px 16px', color: colors.ink }}>{row.symbol}</span>
                  <span style={{ padding: '10px 16px', textAlign: 'right', color: scoreColor(row.score) }}>
                    {row.score}
                  </span>
                  <span style={{ padding: '10px 16px', textAlign: 'right' }}>{row.vol}</span>
                </button>
              ))}
            </div>
          </div>
        </>
      ) : rankingsError ? null : (
        <RankingsTableSkeleton />
      )}
    </div>
  );
}
