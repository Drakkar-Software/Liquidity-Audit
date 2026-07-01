import { Outlet, ScrollRestoration, type RouteObject } from 'react-router-dom';
import { AppErrorBoundary } from './components/AppErrorBoundary';
import { PostHogPageView } from './components/PostHogPageView';
import { ScrollToTop } from './components/ScrollToTop';
import { colors, fonts } from './theme';
import { ComparisonRoute } from './routes/ComparisonRoute';
import { TokenReportRoute } from './routes/TokenReportRoute';
import {
  AboutRoute,
  CaseStudiesRoute,
  LearnRoute,
  MethodologyRoute,
  NotFound,
} from './routes/StaticRoutes';
import {
  BidAskSpreadRoute,
  CryptoLiquidityRoute,
  LiquidityScoreRoute,
  OrderBookAnalysisRoute,
} from './routes/PillarRoutes';

function RootLayout() {
  return (
    <div
      className="app-shell"
      style={{
        minHeight: '100vh',
        background: colors.canvas,
        fontFamily: fonts.sans,
        WebkitFontSmoothing: 'antialiased',
      }}
    >
      <ScrollRestoration getKey={(location) => location.pathname} />
      <ScrollToTop />
      <PostHogPageView />
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <div className="app-container">
        <AppErrorBoundary>
          <Outlet />
        </AppErrorBoundary>
      </div>
    </div>
  );
}

export function createAppRoutes(): RouteObject[] {
  return [
    {
      element: <RootLayout />,
      children: [
        { path: '/', element: <ComparisonRoute /> },
        { path: '/pairs/:exchange/:symbolSlug', element: <TokenReportRoute /> },
        { path: '/methodology', element: <MethodologyRoute /> },
        { path: '/crypto-liquidity', element: <CryptoLiquidityRoute /> },
        { path: '/order-book-analysis', element: <OrderBookAnalysisRoute /> },
        { path: '/bid-ask-spread', element: <BidAskSpreadRoute /> },
        { path: '/liquidity-score', element: <LiquidityScoreRoute /> },
        { path: '/about', element: <AboutRoute /> },
        { path: '/learn', element: <LearnRoute /> },
        { path: '/case-studies', element: <CaseStudiesRoute /> },
        { path: '*', element: <NotFound /> },
      ],
    },
  ];
}
