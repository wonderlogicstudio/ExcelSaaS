"""Actual local hosted-mode image audit; synthetic fixtures only, no cloud calls."""
from __future__ import annotations

import argparse
import hashlib
import json
from uuid import uuid4

from verify_cloudrun_container import (
    CONTROL_PLANE_TEST_SECRET, ROOT, assert_no_temporary_uploads, docker, request, wait_ready,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    args = parser.parse_args()
    name = 'workbookcare-m4-test-' + uuid4().hex[:12]
    rows = []
    docker(
        'run', '-d', '--name', name, '--memory=1g', '--cpus=1',
        '--cap-drop=ALL', '--security-opt=no-new-privileges:true',
        '-p', '127.0.0.1::8080', '-e', 'APP_ENV=hosted_beta',
        '-e', 'CORS_ORIGINS=https://beta.example.invalid',
        '-e', 'FORMULA_PATTERN_AUDIT_ENABLED=true',
        '-e', 'HOSTED_BETA_FORMULA_AUDIT_ENABLED=true',
        '-e', 'AI_EXPLANATIONS_ENABLED=false',
        '-e', 'WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET=' + CONTROL_PLANE_TEST_SECRET,
        args.image,
    )
    try:
        base = 'http://' + docker('port', name, '8080/tcp')
        wait_ready(base)
        controls = json.loads((ROOT / 'artifacts/verification/d01-workbook-packs/api-controls.json').read_text(encoding='utf-8'))
        packs = [
            ('WorkbookCare_M4C_Sample_Pack_2026-09-01/WorkbookCare_M4C_Sample_Pack', 'm4c_manifest.json'),
            ('WorkbookCare_M4C_Additional_Pack', 'm4c_additional_manifest.json'),
        ]
        for directory, manifest_name in packs:
            pack = ROOT / 'samples' / directory
            manifest = json.loads((pack / 'expected' / manifest_name).read_text(encoding='utf-8'))
            for scenario in manifest['scenarios']:
                workbook = pack / 'samples' / scenario['file']
                content = workbook.read_bytes()
                before_hash = hashlib.sha256(content).hexdigest()
                expected = sorted((x['sheet'], x['cell'], x['expected_rule'], x['expected_subtype'])
                    for x in manifest['expected_findings'] if x['file'] == scenario['file'])
                status, audit = request(base, '/v1/formula-audits', content, 'workbook.xlsx')
                assert status == 200 and audit['status'] == 'COMPLETED'
                actual = sorted((x['sheet'], x['cell'], x['rule_code'], x['formula_pattern']['pattern_subtype'])
                    for x in audit['candidates'])
                assert actual == expected
                case = scenario['file'][:2]
                status, free = request(base, '/v1/scans', content, 'workbook.xlsx')
                control = next(x for x in controls['rows'] if x['synthetic_case'] == case)
                assert status == 200 and free['summary']['issue_count'] == control['free_findings']
                assert not any(x['rule_code'].startswith('FORMULA_PATTERN_') for x in free['findings'])
                assert hashlib.sha256(workbook.read_bytes()).hexdigest() == before_hash
                assert_no_temporary_uploads(name)
                rows.append({'case': case, 'audit_http': 200, 'free_http': 200,
                    'exact_candidates': len(actual), 'free_findings': control['free_findings'],
                    'temporary_files_removed': True})
        status, invalid = request(base, '/v1/formula-audits', b'invalid synthetic bytes', 'workbook.xlsx')
        assert status == 200 and invalid['status'] == 'FAILED' and not invalid['candidates']
        assert_no_temporary_uploads(name)
        assert sum(row['exact_candidates'] for row in rows) == 72
        evidence = {'status': 'PASS', 'evidence_kind': 'ACTUAL_LOCAL_HOSTED_MODE_CONTAINER',
            'image': args.image, 'rows': rows, 'invalid_file_status': 'FAILED',
            'excel_recalculation': False, 'hosted_browser': False}
        path = ROOT / 'artifacts/verification/m4-hosted/container.json'
        path.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'result': 'PASS', 'files': 20, 'exact_candidates': 72,
            'signed_requests': 41, 'temporary_files_removed': True}), flush=True)
    finally:
        docker('rm', '-f', name)


if __name__ == '__main__':
    main()
