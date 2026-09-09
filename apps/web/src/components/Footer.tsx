import { Brand } from './Brand';

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="shell site-footer__inner">
        <div>
          <Brand />
          <p>WorkbookCare는 무료 정적 진단과 정밀 검증 안내를 검증하는 베타 프로토타입입니다. 결제와 실제 수정은 제공하지 않습니다.</p>
        </div>
        <div className="site-footer__links">
          <a href="#file-handling-principles">파일 처리 원칙</a>
          <a href="#faq">FAQ</a>
          <a href="/privacy">개인정보 처리 안내</a>
          <a href="/terms">Beta Notice</a>
          <span>© 2026 WorkbookCare</span>
        </div>
      </div>
    </footer>
  );
}
