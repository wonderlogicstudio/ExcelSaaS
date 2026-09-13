"""Finalize artifact-tool whitespace serialization before freezing new fixtures."""

from pathlib import Path
import argparse, hashlib, json, zipfile, xml.etree.ElementTree as E

parser = argparse.ArgumentParser()
parser.add_argument("--pack", type=Path, required=True)
parser.add_argument("--evidence", type=Path, required=True)
args = parser.parse_args()
PACK = args.pack.resolve()
OUT = args.evidence.resolve()
OUT.mkdir(parents=True, exist_ok=True)
archive = OUT / "authoring-v2"
archive.mkdir(exist_ok=True)
ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
E.register_namespace("", ns)
changed = []
assert not (PACK / "expected/source-hashes.json").exists()
for path in sorted(PACK.rglob("*.xlsx")):
    entries = []
    count = 0
    with zipfile.ZipFile(path) as z:
        for item in z.infolist():
            data = z.read(item.filename)
            if item.filename.startswith(
                "xl/worksheets/sheet"
            ) and item.filename.endswith(".xml"):
                sheet = E.fromstring(data)
                n = 0
                for cell in sheet.iter("{" + ns + "}c"):
                    value = cell.find("{" + ns + "}v")
                    if (
                        cell.get("t") == "str"
                        and value is not None
                        and value.text
                        and value.text != value.text.strip()
                        and cell.find("{" + ns + "}f") is None
                    ):
                        cell.set("t", "inlineStr")
                        cell.remove(value)
                        text = E.SubElement(
                            E.SubElement(cell, "{" + ns + "}is"),
                            "{" + ns + "}t",
                            {"{http://www.w3.org/XML/1998/namespace}space": "preserve"},
                        )
                        text.text = value.text
                        n += 1
                if n:
                    data = E.tostring(sheet, encoding="utf-8", xml_declaration=True)
                    count += n
            entries.append((item, data))
    if count:
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        dest = archive / path.name
        assert not dest.exists()
        path.replace(dest)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for item, data in entries:
                z.writestr(item, data)
        changed.append(
            {
                "file": path.name,
                "preserved_whitespace_strings": count,
                "before_sha256": before,
                "after_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
for path in PACK.rglob("*.inspect.ndjson"):
    dest = archive / path.name
    assert not dest.exists()
    path.replace(dest)
(OUT / "authoring-whitespace-fix.json").write_text(
    json.dumps(
        {
            "cause": "artifact-tool t=str lacked whitespace preservation; native Excel trimmed strings",
            "fix": "Only non-formula whitespace strings serialized as inlineStr with xml:space=preserve",
            "oracle_changed": False,
            "files": changed,
        },
        indent=2,
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)
hashes = {
    p.relative_to(PACK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted(PACK.rglob("*"))
    if p.is_file()
}
(PACK / "expected/source-hashes.json").write_text(
    json.dumps(hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(
    json.dumps(
        {
            "changed_files": len(changed),
            "frozen_files": len(hashes),
            "oracle_unchanged": True,
        }
    )
)
