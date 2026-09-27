# FALSE-REPAIR-GUARD01 final verification

Date: 2026-09-27. Scope: local full regression and measured synthetic native Excel compatibility. No product source edit, deployment, commit, or push by this verification role. The dirty checkout was preserved.

## Fresh commands and exits

- From repository root: `.\apps\api\.venv\Scripts\python.exe -B .\scripts\verify_delivery_patch_compatibility.py --stage d08 --output-dir artifacts\synthetic_validation\false-repair-guard01-release\compatibility`: exit 0. Generated three actual patch/artifact packages; no READY publication.
- Initial native check: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_delivery_output_excel.ps1 -Directory artifacts\synthetic_validation\false-repair-guard01-release\compatibility -Stage d08`: exit 1. The script resolves relative Directory under artifacts/verification/d08, so inputs.json was not found. No Excel finding claimed from this call.
- Corrected native check: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_delivery_output_excel.ps1 -Directory C:\Users\JinwonLee\project\ExcelSaaS\artifacts\synthetic_validation\false-repair-guard01-release\compatibility -Stage d08`: exit 0. Installed Excel 16.0/build 20326 opened RP01/RP02/RP03 repaired and changes XLSX read-only with macros, links, and events disabled, performed full recalculation, matched scripted independent values and literal report formulas, closed without save, and confirmed all artifact hashes unchanged. See compatibility/excel-reopen.json.
- `.\apps\api\.venv\Scripts\python.exe -B .\scripts\register_delivery_patch_reference.py --stage d08 --evidence-dir artifacts\synthetic_validation\false-repair-guard01-release\compatibility`: exit 0. This validated current patch fingerprint, manifests and all nine artifact hashes before writing the measured production reference. `compatibility_status()` is PASS; evidence digest 41cd84b9b8230ba3bf45e964a721cb62b219ed259222f9cf5389cf6a9f0a9d1b.
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`: exit 0, one full run. Web 177 tests/31 files and build pass; Worker 16 tests pass; API 319 tests pass; Ruff passes; M4 supplied pack 36 exact candidates with no extras. Full output is full-regression.log and exit is full-regression-exit.txt. Two API warnings: Starlette/httpx deprecation and missing default style in the synthetic guard fixture.

## Guard-specific native limit

The new guard's original supported-control-source.xlsx and supported-control-repaired.xlsx were inspected and hashed before COM. Both failed installed Excel Workbooks.Open with HRESULT -2146827284. One initial read-only attempt and one diagnostic correction were made; no third COM attempt or fixture/oracle rewrite. The test fixture's incomplete style package is a likely cause, consistent with openpyxl's missing-default-style warning, but this is not established as the Excel error's root cause. Native guard-control acceptance remains NOT_ESTABLISHED. The RP01/RP02/RP03 reference PASS is real, but those three files do not exercise the new E3 padded-text case. Local patch/oracle verification for that case remains separately documented in false-repair-guard01/builder-report.md.

## Binding hashes (SHA-256)

- Current patch fingerprint: c0d2f5c7f54ef8c9659600c18bec926bcbc4b9f7abcdad06ee2f30e7eabd6cf7
- apps/api/app/delivery_patch_reference.json: 133e9e964d76eb7fd1ed4986f03eef1a45e3f649aff2b14fa77bbc57b0f644de
- compatibility/inputs.json: 88d9d290f2de04e0e8eb07453443e97029f2d3a34f7d4a00edfb8dcc1c95013f
- compatibility/excel-reopen.json: 5d5a0599c0134cd7660fa6dde465e0ad4b0f007201345b49474bca186ebf6722
- full-regression.log: 94a385e230035f243d5e7d42588377a50f027579f1e7d0d01bd1016a73d557a1
- RP01 repaired/changes/HTML: 95a4c1ac76677ad71d7fea8e37394b6fa55f3751ef2a62fae83501ee84d97ab8 / d1c64e83cc05c652e7059879be00dc75dcf543677c3865fa2a5855293cd5c0e9 / af97c7ac6114345bb81ca22e6b3e69eb18ffbb1084361de36673416c8b4bca38
- RP02 repaired/changes/HTML: 579dae795a8f439e28a08bbde00fd5093d1e290fdf4a7216807cbf0e92727a7c / 3f39c4bcc89c9c6cd4601a390150e9be149265bd36b8f33f597b30c0ee00877a / 5bca2ea135a29d1b599f969526e8211e8e3e26f2e55304f04bccace8afa6f36e
- RP03 repaired/changes/HTML: 96ffbca2612f4ab0611f5b01bce606008ed603dfed835684eb435f2f873d41cd / ac5eb0d335cd14251f8ad2723f38618bfed1e0a4f526583e4447954b12f6bb24 / 09bef49682f6316879cf86a1191bded880d621503b8c7d9b8d4c96ae355a7a0a
- Original guard source/repaired: f537e528c60c05e454f700178a34bf90c372af58cd018eac83a98bc978e9114b / 74af292176315cfd6386f8366a161b7450f38275e7ac7ed5f8f8dbde00b6694a
