import {
  ArrowRight,
  BadgeCheck,
  Bot,
  Check,
  FileDiff,
  Fingerprint,
  LockKeyhole,
  MousePointerClick,
  ShieldCheck,
  Sparkles,
  UserRoundCheck,
} from 'lucide-react';

import type { ProductOffering } from '../types';
import { ProductCards } from './ProductCards';

interface StaticSectionsProps {
  products?: ProductOffering[];
  onCompare?: () => void;
  onStart: () => void;
  onDemo: () => void;
}

export function StaticSections({ onStart, onDemo, products, onCompare }: StaticSectionsProps) {
  return (
    <>
      <section className="section section--tinted " id="service-scope" aria-labelledby="service-scope-title">
        <div className="shell">
          <div className="section-heading section-heading--center">
            <span className="section-kicker">서비스 범위와 현재 상태</span>
            <h2 id="service-scope-title">문제를 찾고, 검증 후 수정 여부를 결정하세요.</h2>
            <p>무료 진단, 두 자료 비교 보고서, 승인 기반 수정 패키지의 범위와 받을 파일을 구분합니다. {onCompare ? '무료 진단과 합성 자료의 비교·수정 사전 확인을 사용할 수 있습니다. 일반 구매는 준비 중입니다.' : '현재는 무료 정적 진단만 사용할 수 있습니다.'}</p>
          </div>
          <ProductCards products={products} onStart={onStart} onCompare={onCompare} />
        </div>
      </section>

      <section className="section section--tinted " aria-labelledby="difference-title">
        <div className="shell comparison-layout">
          <div className="comparison-copy">
            <span className="section-kicker">일반 AI와 다른 점</span>
            <h2 id="difference-title">답변보다, 수정 판단의 근거를 확인하세요.</h2>
            <p>
              일반 AI는 질문에 답을 얻는 데 유용합니다. WorkbookCare는 파일 전체를 같은 기준으로 점검하고,
              발견 항목의 위치·위험도·수정 가능 여부와 추후 수정 제공 시 예상 범위를 보여드리는 데 집중합니다.
            </p>
            <button className="text-link" type="button" onClick={onDemo}>
              샘플 진단에서 결과 보기 <ArrowRight size={17} />
            </button>
          </div>
          <div className="comparison-cards">
            <article className="comparison-card comparison-card--muted">
              <div>
                <Bot size={21} />
                <h3>질문형 AI 도구</h3>
              </div>
              <ul>
                <li>사용자가 문제 상황을 설명해 질문</li>
                <li>파일 점검 기준과 결과 형식은 도구마다 다름</li>
                <li>수정 범위와 가격은 별도로 정해야 함</li>
                <li>파일을 바꿨다면 변경 내역도 별도로 확인</li>
              </ul>
            </article>
            <article className="comparison-card comparison-card--accent">
              <div>
                <BadgeCheck size={21} />
                <h3>WorkbookCare</h3>
              </div>
              <ul>
                <li><Check size={16} /> 파일 구조와 수식 참조를 같은 규칙으로 검사</li>
                <li><Check size={16} /> 시트·셀·규칙 코드와 발견 이유를 함께 표시</li>
                <li><Check size={16} /> 수정 가능성과 권장 정밀검증, 베타 가격 범위를 안내</li>
                <li><Check size={16} /> {onCompare?'등록된 합성 샘플의 승인·납품을 베타에서 시험':'현재는 진단과 범위 미리보기만 제공'}</li>
              </ul>
            </article>
          </div>
        </div>
      </section>

      <section className="section " id="file-handling-principles" aria-labelledby="trust-title">
        <div className="shell trust-layout">
          <div className="trust-visual" aria-hidden="true">
            <div className="trust-visual__orbit trust-visual__orbit--one" />
            <div className="trust-visual__orbit trust-visual__orbit--two" />
            <span className="trust-visual__center">
              <ShieldCheck size={44} />
            </span>
            <span className="trust-tag trust-tag--one"><LockKeyhole size={15} /> 실행하지 않음</span>
              <span className="trust-tag trust-tag--two"><Fingerprint size={15} /> AI API 미사용</span>
            <span className="trust-tag trust-tag--three"><FileDiff size={15} /> 원본 파일 미변경</span>
          </div>
          <div className="trust-copy">
            <span className="section-kicker">파일 처리 원칙</span>
            <h2 id="trust-title">파일은 건드리지 않고 확인합니다.</h2>
            <p>
              무료 진단은 파일 구조를 읽으며, 수식·매크로·외부 연결을 실행하지 않습니다. 진단은
              원본 파일을 변경하지 않으며, 무료 진단에는 AI API를 사용하지 않습니다.
            </p>
            <div className="trust-list">
              <p><ShieldCheck size={18} /><span><strong>원본 파일 미변경</strong> 진단은 원본 파일을 수정하거나 다시 저장하지 않습니다.</span></p>
              <p><LockKeyhole size={18} /><span><strong>무료 진단은 정적 검사</strong> 무료 진단에서 VBA, 수식 계산, 외부 연결과 쿼리를 실행하지 않습니다.</span></p>
              <p><Sparkles size={18} /><span><strong>무료 진단에서 AI API 미사용</strong> 무료 진단은 AI 호출 없이 규칙 기반으로 수행합니다.</span></p>
              <p><UserRoundCheck size={18} /><span><strong>정적 검사 범위</strong> 계산 결과와 업무 규칙은 현재 무료 진단에서 검증하지 않습니다.</span></p>
            </div>
          </div>
        </div>
      </section>

      <section className="section section--faq " id="faq" aria-labelledby="faq-title">
        <div className="shell faq-layout">
          <div className="section-heading">
            <span className="section-kicker">FAQ</span>
            <h2 id="faq-title">시작 전, 검사 범위를 확인하세요.</h2>
            <p>현재 검사 범위와 지원하지 않는 작업을 먼저 알려드립니다.</p>
          </div>
          <div className="faq-list">
            <details open>
              <summary>모든 Excel 오류를 찾을 수 있나요?</summary>
              <p>
                아닙니다. 현재 검사는 수식과 구조에서 발견 가능한 위험을 찾습니다. 업무 의미가 틀린 수식처럼
                계산 결과만으로 판단하기 어려운 문제는 전문가 검토가 필요할 수 있습니다.
              </p>
            </details>
            <details>
              <summary>원본 파일이 바뀌나요?</summary>
              <p>{onCompare ? '무료 진단은 원본을 변경하지 않습니다. 등록된 합성 파일의 수정 시험은 별도 변경 승인 후 원본과 분리된 사본만 생성합니다.' : '진단은 원본 파일을 수정하거나 다시 저장하지 않습니다. 승인 기반 수정은 준비 중입니다.'}</p>
            </details>
            <details>
              <summary>VBA나 Power Query도 수정하나요?</summary>
              <p>
                초기 서비스는 이를 실행하거나 자동 수정하지 않습니다. 존재 여부만 감지하고 전문가 검토로
                분류합니다.
              </p>
            </details>
            <details>
              <summary>언제 비용을 내나요?</summary>
              <p>
                현재 테스트 버전에서는 비용을 받지 않습니다. 화면의 금액은 정밀 검증의 예상 작업 수준을 설명하는
                베타 가격 가설이며, 결제 금액이 아닙니다.
              </p>
            </details>
            <details>
              <summary>무료 진단에서 AI를 사용하나요?</summary>
              <p>
                현재 무료 정적 진단은 AI API나 LLM 호출 없이 동작합니다. 향후 기능의 데이터 처리 정책은 별도 구현과
                검토 전에는 약속하지 않습니다.
              </p>
            </details>
          </div>
        </div>
      </section>

      <section className="final-cta" aria-label="무료 검사 시작">
        <div className="shell final-cta__inner">
          <div>
            <span className="section-kicker">무료로 확인하는 첫 단계</span>
            <h2>문제를 찾고, 다음 단계를 결정하세요.</h2>
            <p>{onCompare?'테스트용 .xlsx 또는 .xlsm 파일로 무료 진단을 시작하세요. 등록된 합성 XLSX는 지원 범위를 확인하고 별도 승인 후 수정본을 받을 수 있습니다. 일반 구매·실제 결제는 제공하지 않습니다.':'현재는 샘플 결과와 테스트용 .xlsx 또는 .xlsm 파일로 진단 흐름을 확인할 수 있습니다. 결제와 실제 수정은 제공하지 않습니다.'}</p>
          </div>
          <div className="final-cta__actions">
            <button className="button button--light" type="button" onClick={onStart}>
              <MousePointerClick size={18} />
              테스트용 파일 진단 시작
            </button>
            <button className="button button--dark-outline" type="button" onClick={onDemo}>
              샘플 보기
            </button>
          </div>
        </div>
      </section>
    </>
  );
}
