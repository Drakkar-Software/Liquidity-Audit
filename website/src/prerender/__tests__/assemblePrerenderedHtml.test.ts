import { describe, expect, it } from 'vitest';
import {
  assemblePrerenderedHtml,
  injectHydrationScript,
  injectRootHtml,
} from '../assemblePrerenderedHtml';

const shellHtml = `<!DOCTYPE html>
<html>
  <head>
    <link rel="stylesheet" href="/assets/index-abc.css" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/assets/index-abc.js"></script>
  </body>
</html>`;

describe('injectRootHtml', () => {
  it('replaces the empty root placeholder with rendered markup', () => {
    const output = injectRootHtml(shellHtml, '<main>Methodology</main>');
    expect(output).toContain('<div id="root"><main>Methodology</main></div>');
    expect(output).not.toContain('<div id="root"></div>');
  });

  it('throws when the shell is missing the root placeholder', () => {
    expect(() => injectRootHtml('<html><body></body></html>', '<main />')).toThrow(
      'missing <div id="root"></div>',
    );
  });
});

describe('injectHydrationScript', () => {
  it('serializes hydration data before the closing body tag', () => {
    const output = injectHydrationScript(shellHtml, { loaderData: {} });
    expect(output).toContain('window.__staticRouterHydrationData=');
    expect(output).toContain('</body>');
    expect(output.indexOf('window.__staticRouterHydrationData')).toBeLessThan(output.indexOf('</body>'));
  });

  it('escapes angle brackets in serialized hydration data', () => {
    const output = injectHydrationScript(shellHtml, {
      errors: { 'route-0': { message: '<script>alert(1)</script>' } as Error },
    });
    expect(output).not.toContain('<script>alert(1)</script>');
    expect(output).toContain('\\u003c');
  });
});

describe('assemblePrerenderedHtml', () => {
  it('keeps asset links and injects root markup plus hydration script', () => {
    const output = assemblePrerenderedHtml(shellHtml, '<h1>Methodology</h1>', { loaderData: {} });
    expect(output).toContain('/assets/index-abc.css');
    expect(output).toContain('/assets/index-abc.js');
    expect(output).toContain('<div id="root"><h1>Methodology</h1></div>');
    expect(output).toContain('window.__staticRouterHydrationData=');
  });
});
