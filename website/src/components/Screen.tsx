import React from 'react';
import { colors } from '../theme';
import { Nav } from './Nav';
import type { NavProps } from './Nav';
import { Footer } from './Footer';

export interface ScreenProps extends NavProps {
  children: React.ReactNode;
  /** Render the footer bar. Default true. */
  footer?: boolean;
}

/**
 * The window-chrome shell every page sits inside:
 * rounded dark card with the nav on top and the footer at the bottom.
 */
export function Screen({ children, footer = true, ...nav }: ScreenProps) {
  return (
    <div
      className="screen-shell"
      style={{
        display: 'flex',
        flexDirection: 'column',
        background: colors.screen,
        border: `1px solid ${colors.line2}`,
        overflow: 'hidden',
        boxShadow: '0 30px 70px rgba(0,0,0,.5)',
      }}
    >
      <div className="no-print">
        <Nav {...nav} />
      </div>
      <main className="screen-content" id="main-content" style={{ flex: 1, minHeight: 0 }}>
        {children}
      </main>
      {footer ? (
        <div className="no-print">
          <Footer />
        </div>
      ) : null}
    </div>
  );
}
