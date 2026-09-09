import { ArrowLeft, FileSearch, ShieldCheck } from 'lucide-react';

type LegalPageKind = 'privacy' | 'terms';

interface LegalPageProps {
  kind: LegalPageKind;
}

const sharedNotice = (
  <aside className="legal-page__notice" aria-label="베타 운영 상태">
    <ShieldCheck size={20} />
    <p>
      이 페이지는 외부 사용자 초대 전 Hosted Beta 검토용 안내입니다. 법률 자문이나
      확정된 개인정보처리방침·이용약관이 아니며, 초대 전 운영자와 법률 검토를 거쳐야 합니다.
    </p>
  </aside>
);

function PrivacyDraft() {
  return (
    <>
      <span className="card-label">Hosted Beta · 검토용 초안</span>
      <h1>개인정보 처리 안내 초안</h1>
      <p className="legal-page__lead">
        WorkbookCare는 지원되는 Excel 파일을 정적으로 검사해 구조와 수식 참조의 위험 신호를
        보여주는 베타 서비스입니다. 현재 외부 사용자 초대는 시작하지 않았습니다.
      </p>
      {sharedNotice}

      <section>
        <h2>처리하는 정보와 목적</h2>
        <dl>
          <div><dt>Excel 파일</dt><dd>선택한 지원 파일의 구조와 수식 참조를 정적으로 검사해 진단 결과를 만들기 위해 처리합니다.</dd></div>
          <div><dt>운영 로그</dt><dd>고정된 상태·오류 코드, 버전, 파일 크기·처리시간 등의 구간값으로 장애·비용·안전 제한을 점검하기 위해 처리합니다.</dd></div>
          <div><dt>수식 패턴 정밀검사 의견</dt><dd>도움이 됨, 오탐 의심, 설명 부족 중 하나의 범주만 향후 승인된 범위에서 처리합니다.</dd></div>
        </dl>
      </section>

      <section>
        <h2>파일 처리와 삭제</h2>
        <p>
          파일은 Access로 보호된 Worker를 거쳐 비공개 R2 임시 객체와 Cloud Run 검사 경로에서만
          처리하도록 구성되어 있습니다. 원본 파일은 수정하지 않으며, VBA·매크로, 수식 계산,
          외부 연결과 쿼리는 실행하지 않습니다.
        </p>
        <p>
          분석이 끝나거나 실패하면 임시 객체 삭제를 시도하고, 비공개 저장소에는 1일 자동삭제
          규칙을 백업 안전장치로 설정했습니다. 자동삭제의 실제 만료 관측은 외부 초대 전에
          완료해야 하는 검증 항목이며, 이 안내는 무보관 또는 즉시 삭제를 보장한다고 주장하지 않습니다.
        </p>
      </section>

      <section>
        <h2>저장하지 않는 정보</h2>
        <p>
          운영 로그와 범주형 의견 저장에는 파일명, 시트명, 셀 위치, Finding key, 수식, 셀 값,
          파일 내용, 이메일, 회사명, 자유입력 의견, 접근 URL을 포함하지 않습니다.
        </p>
      </section>

      <section>
        <h2>의견 저장</h2>
        <p>
          향후 승인된 수식 패턴 정밀검사 의견은 무작위 식별자, 허용된 규칙 코드·하위유형,
          의견 범주, 서버 생성 시각과 배포 버전만 전용 저장소에 최대 30일 보관하도록 설계했습니다.
          수식 패턴 정밀검사는 기본 Hosted Beta에서 공개하지 않으며, 이 저장 설계는 법률·운영
          검토 전 외부 사용자에게 제공되지 않습니다.
        </p>
      </section>

      <section>
        <h2>클라우드와 문의</h2>
        <p>
          현재 설계는 Cloudflare Worker·R2와 Google Cloud Run을 사용합니다. 특정 국가 내 저장,
          인증, 완전한 보안 또는 무보관을 약속하지 않습니다. 문의 및 삭제 요청을 받을 공식 연락처는
          외부 초대 전에 운영자가 확정·게시해야 합니다.
        </p>
      </section>
    </>
  );
}

function BetaNotice() {
  return (
    <>
      <span className="card-label">Hosted Beta · 검토용 초안</span>
      <h1>이용 안내 및 Beta Notice</h1>
      <p className="legal-page__lead">
        WorkbookCare는 검토 중인 베타 서비스입니다. 결과를 중요한 업무 결정이나 수정의 유일한
        근거로 사용해서는 안 됩니다.
      </p>
      {sharedNotice}

      <section>
        <h2>현재 제공 범위</h2>
        <p>
          지원되는 `.xlsx`와 `.xlsm` 파일의 구조와 수식 참조를 정적으로 검사합니다. 결과는
          위험 신호와 확인 방법을 안내하는 참고 정보이며, 업무 규칙의 정답이나 계산 결과를 판정하지 않습니다.
        </p>
      </section>

      <section>
        <h2>제공하지 않는 기능</h2>
        <p>
          Formula Pattern Candidate는 확정 오류가 아닙니다. Excel 계산, 매크로·VBA·외부 연결의
          실행, 원본 파일 변경, 자동 수정, 결제 및 실제 수정 서비스는 현재 제공하지 않습니다.
        </p>
      </section>

      <section>
        <h2>사용자 확인</h2>
        <p>
          중요한 파일을 사용하거나 공유하기 전에는 결과, 원본 파일, 수식과 업무 규칙을 사용자가
          직접 확인해야 합니다. 지원되지 않는 통합문서 기능이나 서비스 장애로 인해 일부 항목이
          검사되지 않거나 결과가 달라질 수 있습니다.
        </p>
      </section>

      <section>
        <h2>금지된 사용과 문의</h2>
        <p>
          법령·계약·안전상 추가 검증이 필요한 의사결정을 이 서비스 결과만으로 내리지 마세요.
          실제 이용 허용 범위, 책임 조항, 문의 채널과 삭제 요청 절차는 외부 초대 전에 운영자와
          법률 검토를 거쳐 확정해야 합니다.
        </p>
      </section>
    </>
  );
}

export function LegalPage({ kind }: LegalPageProps) {
  const title = kind === 'privacy' ? '개인정보 처리 안내' : '이용 안내 및 Beta Notice';
  return (
    <main className="legal-page">
      <div className="shell legal-page__inner">
        <a className="legal-page__back" href="/">
          <ArrowLeft size={17} /> 서비스로 돌아가기
        </a>
        <div className="legal-page__heading">
          <FileSearch size={28} aria-hidden="true" />
          <span>WorkbookCare</span>
        </div>
        <article aria-labelledby="legal-page-title">
          <span className="sr-only" id="legal-page-title">{title}</span>
          {kind === 'privacy' ? <PrivacyDraft /> : <BetaNotice />}
        </article>
      </div>
    </main>
  );
}
