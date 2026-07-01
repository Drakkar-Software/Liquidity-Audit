import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Link, Outlet, RouterProvider, createMemoryRouter } from 'react-router-dom';
import { ScrollToTop } from '../ScrollToTop';

function TestLayout() {
  return (
    <>
      <ScrollToTop />
      <Outlet />
    </>
  );
}

function HomePage() {
  return <Link to="/about">Go to About</Link>;
}

function AboutPage() {
  return <div>About page</div>;
}

function renderScrollRouter(initialPath = '/') {
  const testRouter = createMemoryRouter(
    [
      {
        element: <TestLayout />,
        children: [
          { path: '/', element: <HomePage /> },
          { path: '/about', element: <AboutPage /> },
        ],
      },
    ],
    { initialEntries: [initialPath] },
  );

  return render(<RouterProvider router={testRouter} />);
}

describe('ScrollToTop', () => {
  let scrollToSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    scrollToSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  });

  afterEach(() => {
    scrollToSpy.mockRestore();
  });

  it('scrolls to top when navigating via link', async () => {
    const user = userEvent.setup();
    renderScrollRouter();

    scrollToSpy.mockClear();

    await user.click(screen.getByRole('link', { name: 'Go to About' }));

    expect(screen.getByText('About page')).toBeInTheDocument();
    expect(scrollToSpy).toHaveBeenCalledWith(0, 0);
  });
});
