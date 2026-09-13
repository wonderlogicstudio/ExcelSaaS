import type { FindingUserStatus } from '../types';
// UI wording only. Stored status keys and the existing CSV contract do not change.
export const reviewNoteLabel: Record<FindingUserStatus, string> = {
  UNREVIEWED: '메모 없음', REVIEWED: '내용을 읽어봄', PLANNED_REPAIR: '직접 수정 예정',
  IGNORED: '무시하기로 판단', MARKED_NORMAL: '정상으로 판단',
};
