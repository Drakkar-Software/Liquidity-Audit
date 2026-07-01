import React, { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { colors, fonts } from '../theme';

export const TOOLTIP_MIN_WIDTH_PX = 280;
export const TOOLTIP_MAX_WIDTH_PX = 320;
const TOOLTIP_GAP_PX = 6;
const TOOLTIP_Z_INDEX = 10000;
const VIEWPORT_PADDING_PX = 8;

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
}

interface TooltipPosition {
  top: number;
  left: number;
}

function isEmptyContent(content: React.ReactNode): boolean {
  return content === null || content === undefined || content === false;
}

function prefersTapToggle(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false;
  }
  return window.matchMedia('(hover: none), (pointer: coarse)').matches;
}

function measureTooltipPosition(trigger: HTMLElement): TooltipPosition {
  const rect = trigger.getBoundingClientRect();
  let left = rect.left + rect.width / 2 - TOOLTIP_MAX_WIDTH_PX / 2;
  const maxLeft = window.innerWidth - TOOLTIP_MAX_WIDTH_PX - VIEWPORT_PADDING_PX;
  left = Math.max(VIEWPORT_PADDING_PX, Math.min(left, maxLeft));
  return {
    top: rect.top - TOOLTIP_GAP_PX,
    left,
  };
}

export function Tooltip({ content, children }: TooltipProps) {
  const tooltipId = useId();
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tapPinnedRef = useRef(false);
  const lastPointerTypeRef = useRef<string | null>(null);
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState<TooltipPosition | null>(null);
  const empty = isEmptyContent(content);

  const syncPosition = () => {
    if (!triggerRef.current) {
      return;
    }
    setPosition(measureTooltipPosition(triggerRef.current));
  };

  const show = () => {
    syncPosition();
    setVisible(true);
  };

  const hide = () => {
    setVisible(false);
    setPosition(null);
    tapPinnedRef.current = false;
  };

  const toggle = () => {
    if (visible) {
      hide();
      return;
    }
    show();
  };

  useLayoutEffect(() => {
    if (empty || !visible) {
      return;
    }
    syncPosition();
    const handleReposition = () => syncPosition();
    window.addEventListener('scroll', handleReposition, true);
    window.addEventListener('resize', handleReposition);
    return () => {
      window.removeEventListener('scroll', handleReposition, true);
      window.removeEventListener('resize', handleReposition);
    };
  }, [visible, empty]);

  useEffect(() => {
    if (empty || !visible) {
      return;
    }
    const handleOutsidePointerDown = (event: PointerEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) {
        return;
      }
      if (triggerRef.current?.contains(target)) {
        return;
      }
      hide();
    };
    const handleOutsideClick = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) {
        return;
      }
      if (triggerRef.current?.contains(target)) {
        return;
      }
      hide();
    };
    document.addEventListener('pointerdown', handleOutsidePointerDown);
    document.addEventListener('click', handleOutsideClick);
    return () => {
      document.removeEventListener('pointerdown', handleOutsidePointerDown);
      document.removeEventListener('click', handleOutsideClick);
    };
  }, [visible, empty]);

  if (empty) {
    return <>{children}</>;
  }

  const handlePointerDown = (event: React.PointerEvent<HTMLSpanElement>) => {
    lastPointerTypeRef.current = event.pointerType;
    if (event.pointerType !== 'touch') {
      return;
    }
    event.stopPropagation();
    tapPinnedRef.current = true;
    toggle();
  };

  const handleClick = (event: React.MouseEvent<HTMLSpanElement>) => {
    if (lastPointerTypeRef.current === 'touch') {
      return;
    }
    if (!prefersTapToggle()) {
      return;
    }
    event.stopPropagation();
    tapPinnedRef.current = true;
    toggle();
  };

  const tooltipPanel =
    visible && position ? (
      <span
        id={tooltipId}
        role="tooltip"
        style={{
          position: 'fixed',
          top: position.top,
          left: position.left,
          transform: 'translateY(-100%)',
          zIndex: TOOLTIP_Z_INDEX,
          boxSizing: 'border-box',
          width: TOOLTIP_MAX_WIDTH_PX,
          minWidth: TOOLTIP_MIN_WIDTH_PX,
          maxWidth: TOOLTIP_MAX_WIDTH_PX,
          padding: '8px 10px',
          borderRadius: 6,
          border: `1px solid ${colors.line}`,
          background: colors.panel2,
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
          font: `400 12px/1.45 ${fonts.sans}`,
          color: colors.ink2,
          pointerEvents: 'none',
          whiteSpace: 'normal',
          overflowWrap: 'normal',
          wordBreak: 'normal',
        }}
      >
        {content}
      </span>
    ) : null;

  return (
    <>
      <span
        ref={triggerRef}
        style={{ display: 'inline-flex' }}
        tabIndex={0}
        aria-describedby={visible ? tooltipId : undefined}
        onMouseEnter={show}
        onMouseLeave={() => {
          if (!tapPinnedRef.current) {
            hide();
          }
        }}
        onFocus={show}
        onBlur={() => {
          if (!tapPinnedRef.current) {
            hide();
          }
        }}
        onPointerDown={handlePointerDown}
        onClick={handleClick}
      >
        {children}
      </span>
      {tooltipPanel && typeof document !== 'undefined'
        ? createPortal(tooltipPanel, document.body)
        : null}
    </>
  );
}
