import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent as ReactKeyboardEvent } from 'react';
import { colors, fonts } from '../theme';
import { EXCHANGES, exchangeLabel } from '../lib/data/exchanges';

export interface ExchangeSelectProps {
  value: string;
  onChange: (exchange: string) => void;
  variant?: 'nav' | 'search';
}

const NAV_TRIGGER_STYLE: CSSProperties = {
  font: `500 11px ${fonts.mono}`,
  color: colors.ink2,
  background: colors.navBg,
  border: `1px solid ${colors.line2}`,
  borderRadius: 5,
  padding: '5px 10px',
  cursor: 'pointer',
};

const SEARCH_TRIGGER_STYLE: CSSProperties = {
  font: `500 13px ${fonts.mono}`,
  color: colors.ink2,
  background: 'transparent',
  border: 'none',
  borderLeft: `1px solid ${colors.line}`,
  padding: '0 14px',
  cursor: 'pointer',
  outline: 'none',
};

/** Exchange picker — themed custom dropdown for nav chrome or search bar. */
export function ExchangeSelect({ value, onChange, variant = 'nav' }: ExchangeSelectProps) {
  const [open, setOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const listboxId = `exchange-select-listbox-${variant}`;
  const selectedSlug = value.toLowerCase();
  const triggerStyle = variant === 'search' ? SEARCH_TRIGGER_STYLE : NAV_TRIGGER_STYLE;

  useEffect(() => {
    if (!open) {
      setHighlightedIndex(-1);
    }
  }, [open]);

  useEffect(() => {
    if (highlightedIndex >= EXCHANGES.length) {
      setHighlightedIndex(EXCHANGES.length > 0 ? EXCHANGES.length - 1 : -1);
    }
  }, [highlightedIndex]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const handlePointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  const selectExchange = (exchangeSlug: string) => {
    setOpen(false);
    if (exchangeSlug !== selectedSlug) {
      onChange(exchangeSlug);
    }
  };

  const moveHighlight = (direction: 1 | -1) => {
    setOpen(true);
    setHighlightedIndex((currentIndex) => {
      if (currentIndex < 0) {
        return direction === 1 ? 0 : EXCHANGES.length - 1;
      }
      const nextIndex = currentIndex + direction;
      if (nextIndex < 0) {
        return EXCHANGES.length - 1;
      }
      if (nextIndex >= EXCHANGES.length) {
        return 0;
      }
      return nextIndex;
    });
  };

  const handleTriggerKeyDown = (event: ReactKeyboardEvent<HTMLButtonElement>) => {
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
    if (event.key === 'Enter' && open && highlightedIndex >= 0) {
      event.preventDefault();
      selectExchange(EXCHANGES[highlightedIndex]);
      return;
    }
    if (event.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        display: variant === 'search' ? 'flex' : undefined,
        alignSelf: variant === 'search' ? 'stretch' : undefined,
      }}
    >
      <button
        type="button"
        aria-label="Exchange"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        onClick={() => setOpen((wasOpen) => !wasOpen)}
        onKeyDown={handleTriggerKeyDown}
        style={{
          ...triggerStyle,
          ...(variant === 'search'
            ? {
                display: 'flex',
                alignItems: 'center',
                alignSelf: 'stretch',
                height: '100%',
                margin: 0,
                lineHeight: 1,
              }
            : { margin: 0 }),
        }}
      >
        {exchangeLabel(selectedSlug)} ▾
      </button>

      {open ? (
        <div
          id={listboxId}
          role="listbox"
          aria-label="Exchange options"
          style={{
            position: 'absolute',
            top: variant === 'search' ? 'calc(100% + 6px)' : 'calc(100% + 4px)',
            right: 0,
            minWidth: '100%',
            background: colors.panel,
            border: `1px solid ${colors.line2}`,
            borderRadius: 8,
            overflow: 'hidden',
            zIndex: 20,
            boxShadow: '0 12px 32px rgba(0,0,0,.45)',
          }}
        >
          {EXCHANGES.map((exchangeSlug, optionIndex) => {
            const isSelected = exchangeSlug === selectedSlug;
            const isHighlighted = optionIndex === highlightedIndex;
            return (
              <button
                key={exchangeSlug}
                type="button"
                role="option"
                aria-selected={isSelected}
                onMouseEnter={() => setHighlightedIndex(optionIndex)}
                onClick={() => selectExchange(exchangeSlug)}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: variant === 'search' ? '10px 16px' : '8px 12px',
                  background: isSelected ? colors.accent : isHighlighted ? colors.panel2 : 'transparent',
                  border: 'none',
                  borderBottom:
                    optionIndex < EXCHANGES.length - 1 ? `1px solid ${colors.line}` : 'none',
                  font: `600 11px ${fonts.mono}`,
                  color: isSelected ? colors.accentInk : colors.ink2,
                  textAlign: 'left',
                  cursor: 'pointer',
                }}
              >
                {exchangeLabel(exchangeSlug)}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
