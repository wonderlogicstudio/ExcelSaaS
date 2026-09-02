import { Brand } from './Brand';

interface HeaderProps {
  onStart: () => void;
}

export function Header({ onStart }: HeaderProps) {
  return (
    <header className="site-header">
      <div className="shell site-header__inner">
        <Brand />
        <nav className="site-nav" aria-label="주요 메뉴">
          <a href="#free-diagnosis">무료 진단</a>
          <a href="#precision-verification">정밀 검증</a>
          <a href="#automation-consultation">자동화 의뢰</a>
          <a href="#file-handling-principles">파일 처리 원칙</a>
          <a href="#faq">FAQ</a>
        </nav>
        <button className="button button--small button--outline" onClick={onStart} type="button">
          진단 시작
        </button>
      </div>
    </header>
  );
}
