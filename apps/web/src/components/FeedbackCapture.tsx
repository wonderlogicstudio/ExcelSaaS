import { type FormEvent, useState } from 'react';
import { MessageSquareText, Trash2 } from 'lucide-react';
import {
  type FeedbackCategory,
  type FeedbackRepository,
  type FeedbackScope,
} from '../lib/feedback';

const resultCategories: Array<{ value: FeedbackCategory; label: string }> = [
  { value: 'EXPECTED_ISSUE_NOT_FOUND', label: '찾고 싶은 문제를 발견하지 못함' },
  { value: 'EXPLANATION_DIFFICULT', label: '설명이 어려움' },
  { value: 'POSSIBLE_FALSE_POSITIVE', label: '정상 항목이 문제로 표시된 것 같음' },
  { value: 'POSSIBLE_MISSED_ISSUE', label: '중요한 문제가 누락된 것 같음' },
  { value: 'NEEDS_MORE_REPAIR_GUIDANCE', label: '수정 방법을 더 자세히 알고 싶음' },
  { value: 'NEEDS_REPAIR_OR_REVIEW_COPY', label: '검토 표시본 또는 수정 지원이 필요함' },
];

const findingCategories: Array<{ value: FeedbackCategory; label: string }> = [
  { value: 'HELPFUL', label: '도움이 됨' },
  { value: 'NOT_HELPFUL', label: '도움이 안 됨' },
  { value: 'POSSIBLE_FALSE_POSITIVE', label: '잘못 탐지된 것 같음' },
  { value: 'EXPLANATION_INSUFFICIENT', label: '설명이 부족함' },
];

interface FeedbackFormProps {
  scope: FeedbackScope;
  repository: FeedbackRepository;
  scannerVersion: string;
  ruleCode?: string;
  opaqueFindingId?: string;
  compact?: boolean;
}

function feedbackRating(category: FeedbackCategory) {
  if (category === 'HELPFUL') return 'POSITIVE' as const;
  if (category === 'NOT_HELPFUL') return 'NEGATIVE' as const;
  return null;
}

function FeedbackForm({
  scope,
  repository,
  scannerVersion,
  ruleCode,
  opaqueFindingId,
  compact = false,
}: FeedbackFormProps) {
  const categories = scope === 'RESULT' ? resultCategories : findingCategories;
  const [category, setCategory] = useState<FeedbackCategory | ''>('');
  const [saved, setSaved] = useState(false);
  const name = scope === 'RESULT' ? '결과 의견 유형' : 'Finding 의견 유형';

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!category) return;
    repository.save({
      feedback_scope: scope,
      feedback_category: category,
      rating: feedbackRating(category),
      rule_code: ruleCode ?? null,
      opaque_finding_id: opaqueFindingId ?? null,
      scanner_version: scannerVersion,
    });
    setSaved(true);
  };

  return (
    <form className={`feedback-form${compact ? ' feedback-form--compact' : ''}`} onSubmit={submit}>
      <label>
        <span>{compact ? '이 Finding에 대한 의견' : '결과에 대한 의견'}</span>
        <select aria-label={name} value={category} onChange={(event) => {
          setCategory(event.target.value as FeedbackCategory);
          setSaved(false);
        }}>
          <option value="">선택하세요</option>
          {categories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
      </label>
      <p className="feedback-form__notice">의견 유형만 현재 브라우저에 저장합니다. 메모·파일 내용·개인정보는 입력하거나 서버로 전송할 수 없습니다.</p>
      <button type="submit" className="button button--ghost" disabled={!category}>의견 저장</button>
      {saved && <p className="feedback-form__saved" role="status">이 브라우저에만 저장했습니다.</p>}
    </form>
  );
}

export function FindingFeedbackControl(props: Omit<FeedbackFormProps, 'scope' | 'compact'>) {
  return <FeedbackForm {...props} scope="FINDING" compact />;
}

export function ResultFeedbackPanel({
  repository,
  scannerVersion,
}: Pick<FeedbackFormProps, 'repository' | 'scannerVersion'>) {
  const [cleared, setCleared] = useState(false);

  return (
    <section className="feedback-panel" aria-labelledby="feedback-title">
      <div>
        <span className="card-label"><MessageSquareText size={15} />테스트 의견</span>
        <h3 id="feedback-title">결과가 충분히 이해되었나요?</h3>
        <p>이 기능은 개발·테스트용입니다. 의견은 서버로 전송하지 않고 현재 브라우저에만 저장됩니다.</p>
      </div>
      <FeedbackForm scope="RESULT" repository={repository} scannerVersion={scannerVersion} />
      <button
        type="button"
        className="feedback-panel__clear"
        onClick={() => {
          repository.clear();
          setCleared(true);
        }}
      >
        <Trash2 size={15} />이 브라우저의 테스트 의견 삭제
      </button>
      {cleared && <p className="feedback-form__saved" role="status">저장된 테스트 의견을 삭제했습니다.</p>}
    </section>
  );
}
