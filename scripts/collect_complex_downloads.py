from pathlib import Path
import argparse, hashlib, json, shutil, time

R = Path(__file__).resolve().parents[1]
O = R / "artifacts/verification/d08-complex/browser-downloads"
D = Path.home() / "Downloads"
O.mkdir(parents=True, exist_ok=True)
p = argparse.ArgumentParser()
p.add_argument("phase", choices=["begin", "collect"])
p.add_argument("case")
a = p.parse_args()
state = O / (a.case + "-before.json")


def files():
    return {
        f.name: {"size": f.stat().st_size, "mtime": f.stat().st_mtime_ns}
        for f in D.iterdir()
        if f.is_file()
        and (
            f.name.startswith(
                (
                    "workbookcare_repaired_",
                    "changes_",
                    "verification_",
                    "comparison_report_",
                    "comparison_verification_",
                )
            )
        )
    }


if a.phase == "begin":
    assert not state.exists()
    state.write_text(
        json.dumps({"time": time.time(), "files": files()}), encoding="utf-8"
    )
    print("Download baseline recorded")
else:
    before = json.loads(state.read_text())
    current = files()
    new = [n for n, v in current.items() if before["files"].get(n) != v]
    expected = 2 if a.case.startswith("comparison") else 3
    assert len(new) == expected, {"new_download_count": len(new), "required": expected}
    target = O / a.case
    target.mkdir(exist_ok=True)
    rows = []
    for name in new:
        src = D / name
        dest = target / name
        assert not dest.exists()
        shutil.copyfile(src, dest)
        rows.append(
            {
                "file": dest.relative_to(O).as_posix(),
                "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                "bytes": dest.stat().st_size,
            }
        )
    (O / (a.case + ".json")).write_text(
        json.dumps({"case": a.case, "actual_browser_downloads": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"case": a.case, "actual_downloads": len(rows)}))
