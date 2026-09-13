"""Freeze synthetic source specifications and independent oracles BEFORE product execution."""

from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import argparse, csv, hashlib, json

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
OUT = args.output
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "expected").mkdir(exist_ok=True)


def freeze(path, data):
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError("Frozen file differs: " + path.name)
    else:
        path.write_bytes(data)


def dump(path, obj):
    freeze(path, (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode())


def rnd(v):
    return int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def sheet(name, title, headers):
    return {
        "name": name,
        "title": title,
        "headers": headers,
        "cells": {},
        "formulas": {},
        "last_row": 1,
    }


def put(s, row, values):
    for col, v in enumerate(values):
        if v is not None:
            s["cells"][chr(65 + col) + str(row)] = v


def formula(s, cell, text):
    s["formulas"][cell] = text


books = []
oracle = {
    "kind": "D08_COMPLEX_SYNTHETIC_ORACLES_FROZEN_BEFORE_PRODUCT",
    "version": 1,
    "origin": "Deterministic invented transactions; no customer data. Decimal arithmetic and declared injected mutations; no product imports.",
    "diagnosis": {},
    "repair": {},
    "comparison": {},
    "negative": [],
}
# Multi-sheet calculation chains, normal manual exceptions and isolated mutations.
for broken, name in [
    (True, "01_다채널정산_혼합오류.xlsx"),
    (False, "02_다채널정산_정상예외.xlsx"),
]:
    summary = sheet("채널요약", "채널별 정산 현황", ["채널", "정산액"])
    sheets = [summary]
    expected = []
    put(summary, 2, ["다채널 정산 합성 검증"])
    put(summary, 4, ["채널", "정산액"])
    for index, title in enumerate(["온라인", "매장", "반품"]):
        s = sheet(
            title,
            title + " 정산 내역",
            [
                "거래번호",
                "구분",
                "수량",
                "단가",
                "공제액",
                "공급액",
                "세액",
                "합산액",
                "정산액",
                "단가환산",
            ],
        )
        put(s, 2, [title + " 정산 합성 자료"])
        put(s, 7, s["headers"])
        put(s, 4, [None] * 11 + ["세율", 0.1])
        put(s, 5, [None] * 11 + ["대조세율", 0.2])
        for r in range(8, 168):
            n = r - 7
            qty = (n % 7) + 1
            price = 870 + n * 23 + index * 71
            deduct = (n % 5) * 19
            put(
                s,
                r,
                [
                    f"TXN-{index + 1}-{n:04d}",
                    "수동 조정" if r in {40, 80, 120} else "일반",
                    qty,
                    price,
                    deduct,
                ],
            )
            forms = {
                "F": f"=C{r}*D{r}",
                "G": f"=ROUND(F{r}*$M$4,0)",
                "H": f"=F{r}+G{r}",
                "I": f"=H{r}-E{r}",
                "J": f"=IFERROR(I{r}/C{r},0)",
            }
            if r == 40:
                forms["F"] += "+100"
            if r == 80:
                forms["I"] = f"=H{r}-E{r}-50"
            for c, f in forms.items():
                formula(s, c + str(r), f)
        put(s, 171, ["합계"])
        formula(s, "I171", "=SUM(I8:I167)")
        s["last_row"] = 171
        if broken:
            mutations = [
                (
                    "F22",
                    "=C22*D21",
                    "FORMULA_PATTERN_OUTLIER",
                    "RELATIVE_REFERENCE_DRIFT",
                ),
                (
                    "G76",
                    "=ROUND(F76*$M$5,0)",
                    "FORMULA_PATTERN_OUTLIER",
                    "REFERENCE_CELL_DRIFT",
                ),
                (
                    "H118",
                    "=SUM(F118:F118)",
                    "FORMULA_PATTERN_OUTLIER",
                    "FUNCTION_PATTERN_DRIFT",
                ),
                ("I95", 42, "FORMULA_PATTERN_GAP", "CONSTANT_OVERRIDE_CANDIDATE"),
                ("I145", None, "FORMULA_PATTERN_GAP", "BLANK_GAP_CANDIDATE"),
            ]
            for cell, value, rule, subtype in mutations:
                if isinstance(value, str):
                    s["formulas"][cell] = value
                else:
                    del s["formulas"][cell]
                    if value is not None:
                        s["cells"][cell] = value
                expected.append(
                    {
                        "sheet": title,
                        "cell": cell,
                        "rule_code": rule,
                        "subtype": subtype,
                    }
                )
        sheets.append(s)
        put(summary, 5 + index, [title])
        formula(summary, "B" + str(5 + index), f"='{title}'!I171")
    if broken:
        put(summary, 10, ["파손 참조"])
        formula(summary, "B10", "=#REF!")
    summary["last_row"] = 10
    books.append({"file": name, "kind": "diagnosis", "sheets": sheets})
    oracle["diagnosis"][name] = {
        "structure_count": 1 if broken else 0,
        "structure_locations": [
            {"sheet": "채널요약", "cell": "B10", "rule_code": "FORMULA_REF_ERROR"}
        ]
        if broken
        else [],
        "m4": expected,
        "m4_count": len(expected),
        "manual_rows_not_candidates": [40, 80, 120],
        "data_rows": 480,
        "sheets": 4,
    }
# One supported, substantially larger exact-repair source; both profiles and partial selection.
s = sheet(
    "정산",
    "정산 수정 검증",
    [
        "거래번호",
        "추가금액",
        "수량",
        "단가",
        "할인율(소수)",
        "기본금액",
        "추가금액합",
        "합산액",
        "세액",
        "최종금액",
    ],
)
put(s, 2, ["정산 합성 자료"])
put(s, 7, s["headers"])
put(s, 4, [None] * 11 + ["세율(소수)", 0.1])
texts = {
    12: "-1,250",
    24: "7,200",
    39: "0",
    52: "120,000",
    65: "-2,400",
    78: "999,999",
    94: "500",
    111: "3,000",
}
gaps = [31, 64, 107]
source_rows = []
for r in range(8, 128):
    n = r - 7
    amount = texts.get(r, (n % 11 - 5) * 100)
    q = n % 7 + 1
    p = 900 + n * 17
    disc = Decimal(n % 4) / Decimal(20)
    put(s, r, [f"{n:06d}", amount, q, p, float(disc)])
    for col, f in {
        "F": f"=ROUND(C{r}*D{r}*(1-E{r}),0)",
        "G": f"=SUM(B{r}:B{r})",
        "H": f"=F{r}+G{r}",
        "I": f"=ROUND(H{r}*$M$4,0)",
        "J": f"=H{r}+I{r}",
    }.items():
        if col != "F" or r not in gaps:
            formula(s, col + str(r), f)
    source_rows.append(
        {
            "row": r,
            "id": f"{n:06d}",
            "amount": amount,
            "quantity": q,
            "price": p,
            "discount": str(disc),
        }
    )
put(s, 130, ["합계"])
for col in "FGHIJ":
    formula(s, col + "130", f"=SUM({col}8:{col}127)")
s["last_row"] = 130
memo = sheet("보존정보", "원본 보존 대조", ["식별자", "표기", "설명"])
put(memo, 2, ["보존 대조 합성 데이터"])
put(memo, 5, ["식별자", "표기", "설명"])
for r in range(6, 86):
    put(
        memo,
        r,
        [
            f"{r:08d}",
            "2026-09-" + str((r % 28) + 1).zfill(2),
            "지점 " + str(r % 5) + ' / 한글·쉼표, 따옴표 "보존"',
        ],
    )
memo["last_row"] = 85
repairfile = "03_정산수정_연쇄계산.xlsx"
books.append({"file": repairfile, "kind": "repair", "sheets": [s, memo]})


def values_for(selected, restored):
    out = {}
    totals = {c: 0 for c in "FGHIJ"}
    for row in source_rows:
        r = row["row"]
        b = row["amount"]
        b = int(b.replace(",", "")) if r in selected and isinstance(b, str) else b
        f = (
            rnd(
                Decimal(row["quantity"])
                * Decimal(row["price"])
                * (1 - Decimal(row["discount"]))
            )
            if r not in gaps or r in restored
            else None
        )
        g = b if isinstance(b, int) else 0
        h = (f or 0) + g
        i = rnd(Decimal(h) * Decimal("0.1"))
        j = h + i
        for c, v in zip("FGHIJ", [f, g, h, i, j]):
            out[c + str(r)] = {"type": "blank" if v is None else "number", "value": v}
            totals[c] += v or 0
        out["B" + str(r)] = {
            "type": "text" if isinstance(b, str) else "number",
            "value": b,
        }
    for c, v in totals.items():
        out[c + "130"] = {"type": "number", "value": v}
    return out


before = values_for([], [])
for label, selected, restored in [
    ("RP01_ALL", list(texts), []),
    ("RP01_SUBSET", [12, 24, 78, 111], []),
    ("RP02_ALL", [], gaps),
]:
    after = values_for(selected, restored)
    patches = ["B" + str(r) for r in selected] + ["F" + str(r) for r in restored]
    impacts = {
        c: {"before": before[c], "after": v} for c, v in after.items() if before[c] != v
    }
    oracle["repair"][label] = {
        "file": repairfile,
        "sheet": "정산",
        "profile": "RP01_NUMERIC_TEXT_FIELD_V1"
        if selected
        else "RP02_APPROVED_FORMULA_RESTORE_V1",
        "targets": patches,
        "anchor": "F8",
        "anchor_formula": "=ROUND(C8*D8*(1-E8),0)",
        "policy_role": "AMOUNT",
        "expected": after,
        "impact": impacts,
        "patch_count": len(patches),
        "sum_cell": "J130",
        "sum_before": before["J130"]["value"],
        "sum_after": after["J130"]["value"],
        "source_formulas": 602,
        "restored_formulas": {
            f"F{r}": f"=ROUND(C{r}*D{r}*(1-E{r}),0)" for r in restored
        },
        "unselected_numeric_text": {
            "B" + str(r): v for r, v in texts.items() if r not in selected
        },
    }
oracle["repair_source_rows"] = source_rows
# A realistic table/chart/cross-sheet/merge workbook must be diagnosed, not sold as repairable.
u = sheet("월별보고", "월별 정산 보고", ["월", "매출"])
put(u, 2, ["월별 정산 보고"])
put(u, 5, ["월", "매출"])
u["merge"] = "A2:D2"
u["chart"] = {"range": "A5:B17", "position": ["D5", "L19"], "title": "월별 매출"}
t = sheet("거래원장", "거래 원장", ["거래번호", "월", "금액"])
put(t, 1, t["headers"])
for r in range(2, 242):
    put(t, r, [f"SYN-{r:04d}", (r - 2) % 12 + 1, (r - 1) * 127])
t["last_row"] = 241
t["table"] = {"name": "SyntheticTransactions", "range": "A1:C241"}
for r in range(6, 18):
    put(u, r, [r - 5])
    formula(u, "B" + str(r), f"=SUMIF(거래원장!$B$2:$B$241,A{r},거래원장!$C$2:$C$241)")
u["last_row"] = 19
books.append(
    {"file": "04_실무서식_지원경계.xlsx", "kind": "unsupported", "sheets": [u, t]}
)
oracle["negative"] += [
    {
        "file": "04_실무서식_지원경계.xlsx",
        "stage": "repair_preflight",
        "required_reasons": [
            "UNSUPPORTED_PACKAGE_PART",
            "UNSUPPORTED_SHEET_STRUCTURE",
            "UNSUPPORTED_FORMULA",
        ],
        "no_plan": True,
        "no_purchase": True,
    },
    {
        "file": repairfile,
        "stage": "repair_preflight",
        "targets": ["A12"],
        "role": "AMOUNT",
        "required_reasons": ["NOT_UNAMBIGUOUS_INTEGER_TEXT"],
        "no_plan": True,
    },
    {
        "file": repairfile,
        "stage": "repair_preflight",
        "targets": ["F9"],
        "profile": "RP02_APPROVED_FORMULA_RESTORE_V1",
        "required_reasons": ["TARGET_NOT_TRUE_BLANK"],
        "no_plan": True,
    },
]
# Composite-key comparison. Declare each group before creating physical rows, then permute B.
groups = []


def group(status, key, a, b, tag=None):
    groups.append({"status": status, "key": key, "A": a, "B": b, "tag": tag})


for n in range(350):
    group(
        "MATCHED", ["지점" + str(n % 7), f"{n:06d}"], [n * 137 - 8000], [n * 137 - 8000]
    )
for n in range(40):
    group(
        "AMOUNT_DIFF",
        ["지점" + str(n % 7), f"D-{n:04d}"],
        [12000 + n * 31],
        [12000 + n * 31 + (17 if n % 2 else -25)],
    )
for n in range(20):
    group("ONLY_A", ["전용", f"A-{n:04d}"], [n * 29], [])
    group("ONLY_B", ["전용", f"B-{n:04d}"], [], [-n * 19])
for n in range(10):
    group("AMBIGUOUS", ["중복", f"DA-{n:04d}"], [100 + n, 200 + n], [300 + 2 * n])
for n in range(4):
    group("AMBIGUOUS", ["중복", f"DB-{n:04d}"], [600 + n], [300, 300 + n])
for n, v in enumerate(["bad", "1,200", "12.5", "", " 100 "]):
    group("INPUT_ERROR", ["오류", f"E-{n:04d}"], [v], [100 + n])
for side, num in [("A", 5), ("B", 3)]:
    for n in range(num):
        group(
            "INPUT_ERROR",
            None,
            [77 + n] if side == "A" else [],
            [88 + n] if side == "B" else [],
            side + "-blank-" + str(n),
        )
for key, value in [
    (["보존", "000123"], 10),
    (["보존", "123"], 11),
    (["보존", "Case"], 12),
    (["보존", "case"], 13),
    (["보존", "spaced "], 14),
    (["보존", "spaced"], 15),
]:
    group(
        "ONLY_A" if value % 2 == 0 else "ONLY_B",
        key,
        [value] if value % 2 == 0 else [],
        [value] if value % 2 else [],
    )
group("AMOUNT_DIFF", ["정밀", "BIG"], ["9007199254740993"], ["9007199254740992"])
rows = {"A": [], "B": []}
controls = {}
counts = {
    k: 0
    for k in ["MATCHED", "AMOUNT_DIFF", "ONLY_A", "ONLY_B", "AMBIGUOUS", "INPUT_ERROR"]
}
for g in groups:
    counts[g["status"]] += 1
    for side in rows:
        for amount in g[side]:
            rows[side].append(
                {
                    "key": g["key"] or ["오류", ""],
                    "amount": amount,
                    "group": g["key"] or g["tag"],
                    "status": g["status"],
                }
            )
rows["B"] = list(reversed(rows["B"]))
for side in rows:
    known = sum(
        int(r["amount"])
        for r in rows[side]
        if isinstance(r["amount"], int)
        or r["amount"] in ["9007199254740993", "9007199254740992"]
    )
    unknown = sum(
        not (
            isinstance(r["amount"], int)
            or r["amount"] in ["9007199254740993", "9007199254740992"]
        )
        for r in rows[side]
    )
    controls[side] = {
        "rows": len(rows[side]),
        "known_amount": str(known),
        "unknown_amount_rows": unknown,
    }
    c = sheet(
        "거래", side + " 관측 원장", ["지점", "거래번호", "기준월", "금액", "비고"]
    )
    put(c, 1, c["headers"])
    for r, item in enumerate(rows[side], 2):
        put(c, r, [*item["key"], "2026-09", item["amount"], "합성 원장 " + side])
        item["physical_row"] = r
    c["last_row"] = len(rows[side]) + 1
    books.append(
        {"file": f"05_복합키비교_{side}.xlsx", "kind": "comparison", "sheets": [c]}
    )
oracle["comparison"] = {
    "files": {"A": "05_복합키비교_A.xlsx", "B": "05_복합키비교_B.xlsx"},
    "sheet": "거래",
    "key_columns": ["A", "B"],
    "amount_column": "D",
    "header_row": 1,
    "range_columns": "A:E",
    "tolerance": "0",
    "counts": counts,
    "groups": len(groups),
    "controls": controls,
    "physical_rows": rows,
    "group_cases": groups,
    "big_integer_delta": "1",
    "B_is_truth": False,
}
# Capacity edge controls. Formula count is intentionally one above the supported bound.
l = sheet("수식한도", "수식 개수 한도", ["원값", "계산"])
put(l, 1, l["headers"])
for r in range(2, 1003):
    put(l, r, [r])
    formula(l, "B" + str(r), f"=A{r}+A{r}")
l["last_row"] = 1002
books.append({"file": "06_수식1001개_차단.xlsx", "kind": "limit", "sheets": [l]})
oracle["negative"].append(
    {
        "file": "06_수식1001개_차단.xlsx",
        "stage": "repair_input",
        "error_code": "LIMIT_EXCEEDED",
        "http_status": 413,
        "no_job": True,
    }
)
for count in [1000, 1001]:
    from io import StringIO

    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["거래번호", "금액"])
    writer.writerows([[f"CAP-{n:04d}", n * 7] for n in range(1, count + 1)])
    freeze(OUT / f"07_비교{count}행.csv", stream.getvalue().encode("utf-8-sig"))
oracle["capacity"] = {
    "supported_file": "07_비교1000행.csv",
    "rows": 1000,
    "same_file_pair_counts": {"MATCHED": 1000},
    "known_amount": "3503500",
    "rejected_file": "07_비교1001행.csv",
    "error_code": "COMPARISON_TABLE_LIMIT",
    "http_status": 413,
    "scope": "single sequential acceptance; not concurrency or all byte/cell limit combinations",
}
dump(OUT / "expected/expected.json", oracle)
dump(OUT / "expected/source-spec.json", {"books": books})
freeze(
    OUT / "expected/ORACLE_LOCK.sha256",
    (
        hashlib.sha256((OUT / "expected/expected.json").read_bytes()).hexdigest()
        + "  expected.json\n"
    ).encode(),
)
print(
    json.dumps(
        {
            "workbooks": len(books),
            "comparison_groups": len(groups),
            "comparison_rows": {k: len(v) for k, v in rows.items()},
            "repair_sums": {k: v["sum_after"] for k, v in oracle["repair"].items()},
            "oracle_frozen": True,
        }
    )
)
