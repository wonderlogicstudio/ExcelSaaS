import { useEffect, useRef, useState, type MouseEvent } from 'react';

export const routeTitles: Record<string, string> = {
  '/': '무료 진단', '/diagnosis': '무료 진단', '/precision-verification': '정밀 검증',
  '/compare': '비교·대사', '/automation': '업무 자동화', '/help': '도움말',
  '/repair': '수정 의뢰', '/orders': '베타 주문 확인', '/privacy': '개인정보 처리 안내', '/terms': '이용 안내',
};
const legacy: Record<string, string> = {
  '#two-file-comparison': '/compare', '#comparison-workspace': '/compare',
  '#precision-verification': '/precision-verification', '#automation-consultation': '/automation',
  '#file-handling-principles': '/help#file-handling-principles', '#faq': '/help#faq',
  '#service-scope': '/help#service-scope',
};
const current = () => window.location.pathname + window.location.hash;
export function useProductNavigation() {
  const [location, setLocation] = useState(current);
  const scrolls = useRef(new Map<string, number>());
  const locationRef = useRef(location);
  const navigate = (href: string, back = false) => {
    const url = new URL(href, window.location.origin);
    scrolls.current.set(locationRef.current, window.scrollY);
    let next = url.pathname + url.hash;
    if ((url.pathname === '/' || url.pathname === '/diagnosis') && legacy[url.hash]) next = legacy[url.hash];
    if (!back && next !== current()) window.history.pushState({}, '', next);
    else if (back && next !== current()) window.history.replaceState({}, '', next);
    locationRef.current = next;
    setLocation(next);
    requestAnimationFrame(() => {
      const hash = next.split('#')[1];
      let anchor: HTMLElement | null = null;
      try { anchor = hash ? document.getElementById(decodeURIComponent(hash)) : null; } catch { /* Invalid URL escape: use the page heading. */ }
      if (anchor && !anchor.hasAttribute('tabindex')) anchor.tabIndex = -1;
      const page = document.querySelector<HTMLElement>('[data-product-page]:not([hidden])');
      const focusTarget = anchor ?? page?.querySelector<HTMLElement>('h1, h2');
      if (focusTarget && !back) { focusTarget.tabIndex = -1; focusTarget.focus({ preventScroll: true }); }
      if (back) window.scrollTo(0, scrolls.current.get(next) ?? 0);
      else if (anchor) anchor.scrollIntoView({ block: 'start', behavior: 'instant' });
      else window.scrollTo(0, 0);
    });
  };
  useEffect(() => {
    const onHistory = () => navigate(current(), true);
    const prior = window.history.scrollRestoration;
    window.history.scrollRestoration = 'manual';
    window.addEventListener('popstate', onHistory);
    window.addEventListener('hashchange', onHistory);
    if (legacy[window.location.hash]) onHistory();
    return () => { window.removeEventListener('popstate', onHistory); window.removeEventListener('hashchange', onHistory); window.history.scrollRestoration = prior; };
  }, []);
  const path = location.split('#')[0];
  useEffect(() => { document.title = `${routeTitles[path] ?? '페이지를 찾을 수 없습니다'} | WorkbookCare`; }, [path]);
  const onLink = (event: MouseEvent<HTMLElement>) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const anchor = (event.target as Element).closest('a');
    if (!anchor || anchor.target || anchor.hasAttribute('download')) return;
    const url = new URL(anchor.href);
    if (url.origin !== window.location.origin) return;
    event.preventDefault(); navigate(url.pathname + url.hash);
  };
  return { path, navigate, onLink };
}
