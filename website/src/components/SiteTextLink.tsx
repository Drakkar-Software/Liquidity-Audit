import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { Link, type LinkProps } from 'react-router-dom';

function linkClassName(className?: string): string {
  return className ? `site-text-link ${className}` : 'site-text-link';
}

type InternalSiteTextLinkProps = LinkProps & {
  external?: false;
};

type ExternalSiteTextLinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  external: true;
  href: string;
  children: ReactNode;
};

export type SiteTextLinkProps = InternalSiteTextLinkProps | ExternalSiteTextLinkProps;

/** Inline internal or external link with shared hover style. */
export function SiteTextLink(props: SiteTextLinkProps) {
  if (props.external) {
    const { external: _external, className, children, href, ...anchorProps } = props;
    return (
      <a
        href={href}
        className={linkClassName(className)}
        rel="noopener noreferrer"
        target="_blank"
        {...anchorProps}
      >
        {children}
      </a>
    );
  }

  const { external: _external, className, ...linkProps } = props;
  return <Link className={linkClassName(className)} {...linkProps} />;
}
