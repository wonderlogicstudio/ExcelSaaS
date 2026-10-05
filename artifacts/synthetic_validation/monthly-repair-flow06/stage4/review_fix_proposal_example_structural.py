from pathlib import Path
p=Path('apps/web/src/components/ProposalExample.tsx')
s=p.read_text(encoding='utf-8')
start=s.index('      const calculated = detail.impact.find')
end=s.index('      </article>', start)
old=s[start:end]
# Preserve existing localized/mojibake fallback strings by slicing them from the old block where possible.
new="""      const calculated = detail.impact.find(i => i.sheet === patch.sheet && i.cell === patch.cell);
      const kind = patch.profile_version ?? patch.change_kind;
      const monthly = kind === 'RP03_MONTHLY_SHEET_FORMULA_REPLACEMENT_V1' || patch.change_kind === 'MONTHLY_FORMULA_REPLACEMENT';
      const before = monthly ? calculated?.before ?? patch.before : patch.before;
      const after = patch.after.type === 'formula' ? calculated?.after : patch.after;
      return <article className=\"proposal-example-item\" key={`${patch.sheet}:${patch.cell}`}><p><strong>{patch.sheet} · {patch.cell}</strong> · {patchType(patch)} 대표 예시</p>
        <div className=\"proposal-before-after\"><div><span>현재</span><strong data-proposal-before={patch.cell}>{label(before)}</strong></div><span aria-hidden=\"true\">→</span><div><span>{monthly ? '서버가 검증하면' : patch.after.type === 'formula' ? '이 방식으로 채우면' : '숫자로 바꾸면'}</span><strong data-proposal-after={patch.cell}>{after ? label(after) : '계산 결과를 확인하지 못함'}</strong></div></div>
        <p>{monthly
          ? calculated ? '서버가 원본 수식과 실제 오류를 확인한 뒤 계산한 결과입니다.' : '서버가 원본 수식과 실제 오류를 확인해야 계산 결과를 보여줄 수 있습니다.'
          : patch.after.type === 'formula'
            ? calculated ? '선택한 기준 수식을 해당 행으로 옮긴 뒤 지원 엔진이 계산한 실제 결과입니다.' : '선택한 기준 수식을 해당 행으로 옮길 계획입니다. 이 예시 셀의 계산 결과는 아직 확인하지 못했습니다.'
            : '문자 표기를 계산할 수 있는 숫자 타입으로 바꾼 예시입니다. 합계 등에 미치는 영향을 함께 검사했습니다.'}</p>
"""
s=s[:start]+new+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')
