import type { PageMetaTags } from './siteMeta';
import { DEFAULT_OG_IMAGE_HEIGHT, DEFAULT_OG_IMAGE_WIDTH, isDefaultOgImage, PAGE_JSON_LD_ID, SITE_NAME } from './siteMeta';

function upsertMetaByName(name: string, content: string): void {
  let element = document.querySelector(`meta[name="${name}"]`);
  if (!element) {
    element = document.createElement('meta');
    element.setAttribute('name', name);
    document.head.appendChild(element);
  }
  element.setAttribute('content', content);
}

function upsertMetaByProperty(property: string, content: string): void {
  let element = document.querySelector(`meta[property="${property}"]`);
  if (!element) {
    element = document.createElement('meta');
    element.setAttribute('property', property);
    document.head.appendChild(element);
  }
  element.setAttribute('content', content);
}

function upsertCanonical(href: string): void {
  let element = document.querySelector('link[rel="canonical"]');
  if (!element) {
    element = document.createElement('link');
    element.setAttribute('rel', 'canonical');
    document.head.appendChild(element);
  }
  element.setAttribute('href', href);
}

function removeJsonLdScript(): void {
  document.getElementById(PAGE_JSON_LD_ID)?.remove();
}

function upsertJsonLd(jsonLd: Record<string, unknown> | Record<string, unknown>[] | undefined): void {
  removeJsonLdScript();
  if (!jsonLd) {
    return;
  }
  const script = document.createElement('script');
  script.id = PAGE_JSON_LD_ID;
  script.type = 'application/ld+json';
  script.textContent = JSON.stringify(jsonLd);
  document.head.appendChild(script);
}

export function applyPageMetaToDocument(meta: PageMetaTags): void {
  const siteName = meta.siteName ?? SITE_NAME;
  const ogType = meta.ogType ?? 'website';
  const ogImage = meta.ogImage ?? '';
  const robotsContent = meta.noIndex ? 'noindex, nofollow' : 'index, follow';

  document.title = meta.title;
  upsertMetaByName('description', meta.description);
  upsertMetaByName('robots', robotsContent);
  upsertCanonical(meta.canonicalUrl);
  upsertMetaByProperty('og:title', meta.title);
  upsertMetaByProperty('og:description', meta.description);
  upsertMetaByProperty('og:url', meta.canonicalUrl);
  upsertMetaByProperty('og:type', ogType);
  upsertMetaByProperty('og:site_name', siteName);
  if (ogImage) {
    upsertMetaByProperty('og:image', ogImage);
    upsertMetaByName('twitter:image', ogImage);
    if (isDefaultOgImage(ogImage)) {
      upsertMetaByProperty('og:image:width', String(DEFAULT_OG_IMAGE_WIDTH));
      upsertMetaByProperty('og:image:height', String(DEFAULT_OG_IMAGE_HEIGHT));
    }
  }
  if (meta.ogImageAlt) {
    upsertMetaByProperty('og:image:alt', meta.ogImageAlt);
    upsertMetaByName('twitter:image:alt', meta.ogImageAlt);
  }
  upsertMetaByName('twitter:card', 'summary_large_image');
  upsertMetaByName('twitter:title', meta.title);
  upsertMetaByName('twitter:description', meta.description);
  upsertJsonLd(meta.jsonLd);
}

export function clearRoutePageMeta(): void {
  removeJsonLdScript();
}
