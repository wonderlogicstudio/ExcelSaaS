import { FileSearch, ListChecks, ShieldCheck, Files } from 'lucide-react';

export function CoreJourney() {
  return <section className="core-journey shell" aria-label="진단에서 수정본까지">
    {[['01', '무료 진단', '위치와 근거 확인', FileSearch], ['02', '수정 의뢰 범위', '선택 후 지원 여부 확인', ListChecks],
      ['03', '정확한 변경 승인', '이용 권리와 승인은 별도', ShieldCheck], ['04', '세 파일 수령', '수정본 · 변경내역 · 재검증', Files]].map(([n,title,copy,Icon]) => {
        const Symbol = Icon as typeof FileSearch;
        return <div key={String(n)}><span>{String(n)}</span><Symbol size={20}/><strong>{String(title)}</strong><small>{String(copy)}</small></div>;
      })}
  </section>;
}

export function ServiceIntro({ kind, patterns, delivery, onStart }: { kind: 'precision' | 'compare' | 'automation' | 'repair'; patterns: boolean; delivery: boolean; onStart: () => void }) {
  const content = {
    precision: ['정밀 검증', '수식이 다른 이유를 확인하세요.', '무료 진단에서 발견한 수식 후보의 근거를 살펴보고, 아직 확인하지 않은 범위를 구분합니다.'],
    compare: ['비교·대사', '두 자료의 차이를 확인하세요.', '두 파일의 일치·금액 차이·누락·중복·자료 오류를 비교 보고서로 받습니다. B는 비교 자료이며 정답으로 간주하지 않습니다.'],
    automation: ['업무 자동화', '반복 업무를 줄이는 다음 단계.', '매출·재고·원가·미수금·반복 보고서의 자동화를 위한 서비스 방향입니다. 현재 주문이나 상담 접수는 제공하지 않습니다.'],
    repair: ['수정 의뢰', '먼저 고칠 범위를 확인하세요.', '무료 진단 결과에서 수정 검토할 항목을 선택하세요. 지원 가능 여부와 정확한 변경계획을 확인하고 별도로 승인한 뒤 사본을 생성합니다.'],
  }[kind];
  return <section className="service-intro shell"><span className="section-kicker">{content[0]}</span><h1 tabIndex={-1}>{content[1]}</h1><p>{content[2]}</p>
    {kind === 'precision' && <><div className="service-detail-grid">
      <article><span className="service-status">{patterns ? '현재 보호 베타에서 제공' : '내부 검증 · 일반 제공 준비 중'}</span><h2>수식 패턴 확인</h2><p>주변 수식과 다른 참조·함수, 반복 수식의 빈 셀·상수 대체 후보를 정적으로 분석합니다. 후보는 무료 진단의 같은 결과 목록에서 확인합니다.</p><p>원본 수식 계산이나 업무적 정답 판정은 포함하지 않습니다.</p></article>
      <article><span className="service-status service-status--pending">준비 중</span><h2>업무 기준에 따른 추가 검증</h2><p>복합 수식 설명, 계산 흐름 설명, 고객 기대값 대조, 업무 규칙 검증은 현재 신청·구매·실행할 수 없습니다.</p><p>수정 엔진의 제한된 계산 검증과 범용 업무 검증은 다릅니다.</p></article>
    </div><button type="button" className="button button--primary" onClick={onStart}>{patterns ? '무료 진단에서 수식 후보 확인' : '무료 구조 진단 시작'}</button></>}
    {kind === 'automation' && <div className="service-detail-grid"><article><span className="service-status service-status--pending">준비 중 · 구매 불가</span><h2>표준 업무 자동화</h2><p>반복 보고서와 매출·재고·원가·미수금 관리의 정형 작업을 대상으로 합니다. 현재 제공 중인 자동화 상품은 없습니다.</p></article><article><span className="service-status service-status--pending">준비 중 · 상담 접수 전</span><h2>맞춤 제작·상담</h2><p>사용자 업무에 맞는 Excel·프로그램 제작 방향입니다. 납품 담당자·가격·지원 정책은 아직 확정되지 않았습니다.</p></article></div>}
    {kind === 'compare' && <p className="service-status">{delivery ? '등록된 합성 자료로 비교·보고서 시험 가능 · 일반 구매 준비 중' : '비교 보고서 준비 중 · 현재 실행·구매 불가'}</p>}
    {kind === 'repair' && <><p>{delivery ? '등록된 합성 파일에서 승인·납품을 시험합니다. 일반 구매와 실제 결제는 준비 중입니다.' : '승인 기반 수정은 준비 중입니다.'}</p><button type="button" className="button button--primary" onClick={onStart}>무료 진단 후 수정 범위 선택</button></>}
  </section>;
}
