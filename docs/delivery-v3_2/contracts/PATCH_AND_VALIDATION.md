# 사본 수정·파일 보존·후검증

## 원본은 불변

원본 blob은 immutable하고 patcher는 별도 destination에만 쓴다. overwrite=true 옵션이나 기존 경로에 save하는 우회가 없어야 한다. 고객 원본의 digest는 실행 전후 동일해야 한다. 최종 파일은 원본의 사본이라는 의미이지 byte-for-byte 동일하다는 의미는 아니다.

openpyxl의 범용 load/save가 미지원 요소를 잃을 수 있다는 공식 경고를 고려한다.[S2](../research/SOURCES.md#s2) 첫 profile은 지원 inventory를 엄격히 제한하고 다음 방식 중 검증된 것을 사용한다.

권장: 필요한 OOXML part만 파싱해 patch, 나머지 part의 **압축 해제 bytes** hash를 보존. ZIP 압축 bytes가 달라진 것을 업무 변경으로 오판하지 않는다. 패치한 XML도 비대상 셀·서식·노드가 의미상 동일한지 검증한다. 미지원 확장·서명·관계가 발견되면 우회하지 말고 거부한다. 라이브러리 roundtrip을 택한다면 같은 강도의 inventory/semantic 보존 시험이 선행되어야 한다.

계산용 사본의 engine 저장 결과를 그대로 고객 납품본으로 사용하지 않는다. 원본에서 검증된 patch path로 만든 사본에 필요한 formula cache만 typed value로 안전하게 갱신하고 검증한다. sharedStrings 사용 셀의 값을 바꿀 때 다른 공유 셀을 함께 바꾸지 않는다.

## 승인 외 변경과 기술적 부수 변경

수정 대상 셀 외의 **업무 값/수식/서식** 변경은 0이어야 한다. 계산 결과 cache·calc settings·명시된 chain 관계 갱신은 계획에 포함된 기술적 allowlist로 별도 검사한다. ‘승인 외 변화 0’이라고 말하면서 내부적으로 셀 전체를 다시 쓰면 안 된다. 원본에 변경 시트·표식을 추가하지 않는다. 변경내역은 별도 파일이다.

## 후검증 단계

1. 원본 digest와 계획 스냅샷 재확인.
2. approved patch set = actual business patch set.
3. 모든 archive member·relationship·content type·금지 part·비대상 셀/서식 보존.
4. output 재개봉, 수식/참조 validity, 오류/반복참조 탐지.
5. 전후 실제 계산과 expected delta, 새 오류/미지원/타입 변경 점검.
6. 신규 정적 finding·잔여 finding의 원인 분리. 미검출만으로 업무정답 PASS 금지.
7. change log와 verification/manifest의 source/output/plan/engine 참조 일치.
8. 대상 Excel 버전의 fixture 호환성+재개봉 수용 근거 확인.

각 check는 `PASS/FAIL/NOT_RUN/NOT_APPLICABLE`과 범위·근거를 가진다. 필수 NOT_RUN/FAIL이면 `QUARANTINED`, 고객 수정본 다운로드 차단. 실제 원본에 있던 무관 오류가 남을 수 있는지 상품 profile에서 정한다. 이 첫 strict profile은 필요 계산 실패/불명 오류가 있으면 preflight 차단한다. 결제 후 잔여 항목을 몰래 정책에서 제외하지 않는다.

## atomic 납품

실행별 scratch 공간 → patch → 검증 → artifact 묶음 검증 → 권리 재검사 → manifest와 READY 원자적 게시. 중간 파일은 공개 경로에 두지 않는다. worker 두 개가 같은 plan을 실행해도 CAS/lease/idempotency로 하나의 논리 결과만 게시한다.

취소/환불/삭제가 처리 중 발생하면 `publication_fence`를 바꾸고 늦게 끝난 결과는 게시하지 않는다. 실행 중 실제 kill/cleanup이 완료되기 전 '취소 완료'로 말하지 않는다. 실패 뒤 같은 snapshot 재실행은 재과금하지 않는다. 안전하게 재현 불가이면 보상 경로로 보낸다.
