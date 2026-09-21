from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from .schema import DatasetManifest, write_json


def write_html_report(*, manifest: DatasetManifest, summary: dict[str, Any], run_root: Path) -> Path:
    reports = run_root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    rows = []
    for item in summary.get("by_scope", []):
        rows.append(
            "<tr>"
            f"<td>{html.escape(item.get('business_domain', ''))}</td>"
            f"<td>{html.escape(item.get('structural_family', ''))}</td>"
            f"<td>{html.escape(item.get('mutation_type', ''))}</td>"
            f"<td>{html.escape(item.get('split', ''))}</td>"
            f"<td>{item.get('tp', 0)}</td>"
            f"<td>{item.get('fn', 0)}</td>"
            f"<td>{item.get('fp', 0)}</td>"
            f"<td>{item.get('diagnostic_mismatch', 0)}</td>"
            f"<td>{item.get('normal_region_fp', 0)}</td>"
            f"<td>{item.get('avg_fp_per_workbook', 0)}</td>"
            f"<td>{item.get('max_fp_per_workbook', 0)}</td>"
            "</tr>"
        )
    metrics = summary["metrics_full_contract"]
    successful = summary["metrics_successful_only"]
    completion = summary.get("completion", {})
    document = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>WorkbookCare Synthetic Validation {html.escape(manifest.run_id)}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
th, td {{ border: 1px solid #d5d9e2; padding: 8px; text-align: left; }}
th {{ background: #eef2f8; }}
.note {{ color: #5c667a; }}
.metric {{ display: inline-block; margin-right: 20px; }}
</style>
<h1>WorkbookCare Synthetic Validation</h1>
<p class="note">Synthetic diagnostic validation only. This report does not claim customer-file accuracy, Excel recalculation, HTTP/UI coverage, commercial readiness, or repair capability.</p>
<p>
  <span class="metric"><b>Run:</b> {html.escape(manifest.run_id)}</span>
  <span class="metric"><b>Pairs:</b> {manifest.pair_count}</span>
  <span class="metric"><b>Workbooks:</b> {len(manifest.workbooks)}</span>
</p>
<p>
  <span class="metric"><b>Process outputs:</b> {completion.get('process_outputs', 0)}/{completion.get('workbooks_total', 0)}</span>
  <span class="metric"><b>Fully analyzed:</b> {completion.get('completed', 0)}/{completion.get('workbooks_total', 0)}</span>
  <span class="metric"><b>Partial:</b> {completion.get('partial', 0)}</span>
  <span class="metric"><b>Failures:</b> {completion.get('failed', 0)}</span>
  <span class="metric"><b>Timeouts:</b> {completion.get('timeouts', 0)}</span>
  <span class="metric"><b>Not run:</b> {completion.get('not_run', 0)}</span>
</p>
<p>
  <span class="metric"><b>Skipped audits:</b> {completion.get('skipped', 0)}</span>
  <span class="metric"><b>Abstained audits:</b> {completion.get('abstained', 0)}</span>
  <span class="metric"><b>Failed audits:</b> {completion.get('audit_failed', 0)}</span>
  <span class="metric"><b>Truncated/omitted base scans:</b> {completion.get('truncated', 0)}</span>
  <span class="metric"><b>Raw process errors:</b> {completion.get('raw_errors', 0)}</span>
</p>
<p>
  <span class="metric"><b>TP:</b> {metrics.get('tp')}</span>
  <span class="metric"><b>FN:</b> {metrics.get('fn')}</span>
  <span class="metric"><b>FP:</b> {metrics.get('fp')}</span>
  <span class="metric"><b>Candidate FP (normal region):</b> {metrics.get('candidate_fp')}</span>
  <span class="metric"><b>Definitive FP (normal region):</b> {metrics.get('definitive_fp')}</span>
  <span class="metric"><b>Diagnostic mismatch:</b> {metrics.get('diagnostic_mismatch')}</span>
  <span class="metric"><b>Normal-region FP:</b> {metrics.get('normal_region_fp')}</span>
  <span class="metric"><b>Duplicates:</b> {metrics.get('duplicates_not_fp')}</span>
  <span class="metric"><b>Precision:</b> {metrics.get('precision')}</span>
  <span class="metric"><b>Recall:</b> {metrics.get('recall')}</span>
  <span class="metric"><b>Analysis completion rate:</b> {successful.get('completion_rate')}</span>
</p>
<p class="note">Total FP equals normal-region FP plus diagnostic mismatch. A diagnostic mismatch is still an incorrect prediction, and the unmatched expected finding remains an FN unless it also has an exact matching actual.</p>
<p class="note">Excluded ambiguous or out-of-scope findings are not passes: {metrics.get('excluded_ambiguous_or_out_of_scope_not_passes')}. Unjudged findings are not passes: {metrics.get('unjudged_findings_not_passes')}.</p>
<h2>Scope Results</h2>
<table>
<thead><tr><th>Business</th><th>Structure</th><th>Mutation</th><th>Split</th><th>TP</th><th>FN</th><th>FP</th><th>Diagnostic mismatch</th><th>Normal-region FP</th><th>Avg FP</th><th>Max FP</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<h2>Declared Scope</h2>
<p>Current scored formula-audit rules: FORMULA_PATTERN_OUTLIER and FORMULA_PATTERN_GAP. Base structural findings are scored only when predeclared as FORMULA_REF_ERROR or FORMULA_VISIBLE_ERROR_TOKEN. Exclusions and unjudged findings are reported separately and are never counted as passes.</p><p class="note">Artifacts: dataset/manifest.json, dataset/truth.json, frozen_contract.json, generation_validation.json, engine_status.json, raw_engine/*.json, reports/case_results.csv, reports/workbook_results.csv, reports/scope_results.csv.</p>
</html>
"""
    path = reports / "summary.html"
    path.write_text(document, encoding="utf-8")
    write_json(reports / "report_index.json", {"html": str(path), "summary": str(reports / "summary.json")})
    return path

