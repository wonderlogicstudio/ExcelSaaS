export const FEEDBACK_STORAGE_KEY = 'workbookcare.feedback.v1';

export type FeedbackScope = 'RESULT' | 'FINDING';
export type ResultFeedbackCategory =
  | 'EXPECTED_ISSUE_NOT_FOUND'
  | 'EXPLANATION_DIFFICULT'
  | 'POSSIBLE_FALSE_POSITIVE'
  | 'POSSIBLE_MISSED_ISSUE'
  | 'NEEDS_MORE_REPAIR_GUIDANCE'
  | 'NEEDS_REPAIR_OR_REVIEW_COPY'
  | 'OTHER';
export type FindingFeedbackCategory =
  | 'HELPFUL'
  | 'NOT_HELPFUL'
  | 'POSSIBLE_FALSE_POSITIVE'
  | 'EXPLANATION_INSUFFICIENT';
export type FeedbackCategory = ResultFeedbackCategory | FindingFeedbackCategory;
export type FeedbackRating = 'POSITIVE' | 'NEGATIVE' | null;

export interface FeedbackRecord {
  feedback_id: string;
  feedback_scope: FeedbackScope;
  feedback_category: FeedbackCategory;
  rating: FeedbackRating;
  rule_code: string | null;
  opaque_finding_id: string | null;
  scanner_version: string;
  created_at: string;
}

export interface FeedbackDraft {
  feedback_scope: FeedbackScope;
  feedback_category: FeedbackCategory;
  rating?: FeedbackRating;
  rule_code?: string | null;
  opaque_finding_id?: string | null;
  subtype?: string | null;
  scanner_version: string;
}

export interface FeedbackRepository {
  readonly storageMode?: 'local' | 'hosted';
  list(): FeedbackRecord[];
  save(draft: FeedbackDraft): FeedbackRecord | Promise<FeedbackRecord>;
  clear(): void;
}

function getBrowserStorage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function createFeedbackId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `feedback-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export class LocalFeedbackRepository implements FeedbackRepository {
  readonly storageMode = 'local' as const;

  constructor(
    private readonly storage: Storage | null = getBrowserStorage(),
  ) {}

  list(): FeedbackRecord[] {
    if (!this.storage) return [];
    try {
      const stored = this.storage.getItem(FEEDBACK_STORAGE_KEY) ?? '[]';
      const parsed: unknown = JSON.parse(stored);
      if (!Array.isArray(parsed)) return [];
      const records = parsed.map((record) => {
        const value = record as Partial<FeedbackRecord>;
        return {
          feedback_id: value.feedback_id ?? createFeedbackId(),
          feedback_scope: value.feedback_scope ?? 'RESULT',
          feedback_category: value.feedback_category ?? 'OTHER',
          rating: value.rating ?? null,
          rule_code: value.rule_code ?? null,
          opaque_finding_id: value.opaque_finding_id ?? null,
          scanner_version: value.scanner_version ?? 'unknown',
          created_at: value.created_at ?? new Date().toISOString(),
        } satisfies FeedbackRecord;
      });
      // Strip legacy local free-text feedback, rather than merely hiding it.
      if (JSON.stringify(records) !== stored) {
        this.storage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify(records));
      }
      return records;
    } catch {
      return [];
    }
  }

  save(draft: FeedbackDraft): FeedbackRecord {
    const record: FeedbackRecord = {
      feedback_id: createFeedbackId(),
      feedback_scope: draft.feedback_scope,
      feedback_category: draft.feedback_category,
      rating: draft.rating ?? null,
      rule_code: draft.rule_code ?? null,
      opaque_finding_id: draft.opaque_finding_id ?? null,
      scanner_version: draft.scanner_version,
      created_at: new Date().toISOString(),
    };
    if (this.storage) {
      this.storage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify([...this.list(), record]));
    }
    return record;
  }

  clear(): void {
    this.storage?.removeItem(FEEDBACK_STORAGE_KEY);
  }
}

const hostedFeedbackCategories = new Set<FeedbackCategory>([
  'HELPFUL',
  'POSSIBLE_FALSE_POSITIVE',
  'EXPLANATION_INSUFFICIENT',
]);
const hostedFeedbackSubtypesByRule: Record<string, ReadonlySet<string>> = {
  FORMULA_PATTERN_OUTLIER: new Set([
    'FUNCTION_PATTERN_DRIFT',
    'REFERENCE_SHEET_DRIFT',
    'REFERENCE_CELL_DRIFT',
    'RELATIVE_REFERENCE_DRIFT',
    'ABSOLUTE_REFERENCE_DRIFT',
    'RANGE_BOUNDARY_DRIFT',
  ]),
  FORMULA_PATTERN_GAP: new Set([
    'CONSTANT_OVERRIDE_CANDIDATE',
    'BLANK_GAP_CANDIDATE',
  ]),
};

function opaqueSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  throw new Error('HOSTED_FEEDBACK_UNAVAILABLE');
}

/**
 * H3's server-backed repository intentionally supports Formula Audit candidate
 * categories only. It does not cache records or send any browser-side finding
 * identifier, filename, location, formula, value, or free text.
 */
export class HostedFormulaAuditFeedbackRepository implements FeedbackRepository {
  readonly storageMode = 'hosted' as const;
  private readonly feedbackSessionId = opaqueSessionId();

  constructor(
    private readonly send: typeof fetch = fetch,
    private readonly endpoint = '/api/v1/feedback',
  ) {}

  list(): FeedbackRecord[] {
    return [];
  }

  clear(): void {
    // Nothing is cached in this browser by the hosted repository.
  }

  async save(draft: FeedbackDraft): Promise<FeedbackRecord> {
    const ruleCode = draft.rule_code ?? '';
    const subtype = draft.subtype ?? '';
    if (!hostedFeedbackCategories.has(draft.feedback_category)
      || !hostedFeedbackSubtypesByRule[ruleCode]?.has(subtype)) {
      throw new Error('INVALID_HOSTED_FEEDBACK');
    }
    const response = await this.send(this.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        feedback_session_id: this.feedbackSessionId,
        feedback_category: draft.feedback_category,
        rule_code: ruleCode,
        subtype,
      }),
    });
    if (!response.ok) {
      throw new Error('HOSTED_FEEDBACK_UNAVAILABLE');
    }
    return {
      feedback_id: 'server-recorded',
      feedback_scope: draft.feedback_scope,
      feedback_category: draft.feedback_category,
      rating: draft.rating ?? null,
      rule_code: ruleCode,
      opaque_finding_id: null,
      scanner_version: draft.scanner_version,
      created_at: new Date().toISOString(),
    };
  }
}

export const feedbackCaptureEnabled = import.meta.env.VITE_FEEDBACK_CAPTURE_ENABLED === 'true';
export const hostedFormulaAuditFeedbackEnabled =
  import.meta.env.VITE_HOSTED_BETA_FEEDBACK_ENABLED === 'true';
