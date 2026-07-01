import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Nav } from '../Nav';

function renderNav(initialPath = '/', active?: Parameters<typeof Nav>[0]['active']) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Nav active={active} />
    </MemoryRouter>,
  );
}

function getMenuButton() {
  return document.querySelector('.site-nav-menu-btn') as HTMLButtonElement;
}

describe('Nav', () => {
  it('toggles aria-expanded when the menu button is clicked', async () => {
    const user = userEvent.setup();
    renderNav();

    const menuButton = getMenuButton();
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');

    await user.click(menuButton);
    expect(menuButton).toHaveAttribute('aria-expanded', 'true');
  });

  it('closes the menu when Escape is pressed', async () => {
    const user = userEvent.setup();
    renderNav();

    const menuButton = getMenuButton();
    await user.click(menuButton);
    await user.keyboard('{Escape}');

    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('closes the menu after navigation', async () => {
    const user = userEvent.setup();
    renderNav('/');

    const menuButton = getMenuButton();
    await user.click(menuButton);
    expect(menuButton).toHaveAttribute('aria-expanded', 'true');

    const mobileAboutLink = document.querySelector('#site-nav-menu-panel a[href="/about"]') as HTMLAnchorElement;
    await user.click(mobileAboutLink);
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('does not highlight Comparison on token report paths', () => {
    renderNav('/pairs/mexc/sol_usdt');

    const comparisonLink = document.querySelector('.site-nav-links-desktop a[href="/"]') as HTMLAnchorElement;
    expect(comparisonLink.style.color).not.toBe('rgb(232, 237, 242)');
  });

  it('ignores active=Comparison on token report paths', () => {
    renderNav('/pairs/mexc/sol_usdt', 'Comparison');

    const comparisonLink = document.querySelector('.site-nav-links-desktop a[href="/"]') as HTMLAnchorElement;
    expect(comparisonLink.style.color).not.toBe('rgb(232, 237, 242)');
  });
});
