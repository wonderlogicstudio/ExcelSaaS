import { useEffect, useState } from 'react';
import { Menu, X } from 'lucide-react';
import { Brand } from './Brand';

export function Header({ onStart, path = '/' }: { onStart: () => void; path?: string }) {
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [path]);
  return <header className="site-header" onKeyDown={event => { if (open && event.key === 'Escape') { setOpen(false); document.querySelector<HTMLButtonElement>('.nav-toggle')?.focus(); } }}><a className="skip-link" href="#main-content">본문으로 이동</a>
    <div className="shell site-header__inner"><Brand />
      <button type="button" className="nav-toggle" aria-expanded={open} aria-controls="product-navigation"
        aria-label={open ? '메뉴 닫기' : '메뉴 열기'} onClick={() => setOpen(!open)}>{open ? <X/> : <Menu/>}</button>
      <nav id="product-navigation" className={`site-nav ${open ? 'site-nav--open' : ''}`} aria-label="주요 메뉴">
        {[['/', '무료 진단'], ['/precision-verification', '정밀 검증'], ['/compare', '비교·대사'], ['/automation', '업무 자동화'], ['/help', '도움말']].map(([href, title]) =>
          <a key={href} href={href} aria-current={path === href || (href === '/' && path === '/diagnosis') ? 'page' : undefined} onClick={() => setOpen(false)}>{title}</a>)}
      </nav>
      <button className="button button--small button--primary" onClick={() => { setOpen(false); onStart(); }} type="button">무료 진단 시작</button>
    </div>
  </header>;
}
