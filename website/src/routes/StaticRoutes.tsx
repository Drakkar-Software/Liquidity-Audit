import { Methodology } from '../pages/Methodology';
import { About } from '../pages/About';
import { Learn } from '../pages/Learn';
import { CaseStudies } from '../pages/CaseStudies';
import { NotFound } from '../pages/NotFound';
import { METHODOLOGY_FAQS } from '../lib/methodologyFaqs';
import { useStaticPageMeta } from '../lib/pageMetaHooks';

export function MethodologyRoute() {
  useStaticPageMeta('methodology', '/methodology', 'Methodology', { faqs: METHODOLOGY_FAQS });
  return <Methodology />;
}

export function AboutRoute() {
  useStaticPageMeta('about', '/about', 'About');
  return <About />;
}

export function LearnRoute() {
  useStaticPageMeta('learn', '/learn', 'Learn');
  return <Learn />;
}

export function CaseStudiesRoute() {
  useStaticPageMeta('caseStudies', '/case-studies', 'Case studies');
  return <CaseStudies />;
}

export { NotFound };
