"""Strict repair-profile relationship and content-type inventory, independent of ZIP safety."""

from __future__ import annotations

import posixpath
import re

from defusedxml import ElementTree as ET

from .delivery_inputs import reject

BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
MIME = "application/vnd.openxmlformats-officedocument."


def validate_package(archive):
    expected = {
        "xl/workbook.xml": MIME + "spreadsheetml.sheet.main+xml",
        "xl/styles.xml": MIME + "spreadsheetml.styles+xml",
        "xl/sharedStrings.xml": MIME + "spreadsheetml.sharedStrings+xml",
        "docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
        "docProps/app.xml": MIME + "extended-properties+xml",
    }
    names = set(archive.namelist())
    tree = ET.fromstring(archive.read("[Content_Types].xml"))
    ns = "{http://schemas.openxmlformats.org/package/2006/content-types}"
    if tree.tag != ns + "Types":
        reject("UNSUPPORTED_PACKAGE_INVENTORY", "내부 파일 형식 선언이 잘못되었습니다.")
    defaults = {}
    overrides = {}
    for node in tree:
        if node.tag == ns + "Default":
            key = node.get("Extension")
            mapping = defaults
        elif node.tag == ns + "Override":
            key = node.get("PartName")
            mapping = overrides
        else:
            reject("UNSUPPORTED_PACKAGE_INVENTORY", "지원하지 않는 형식 선언입니다.")
        if key in mapping:
            reject("UNSUPPORTED_PACKAGE_INVENTORY", "중복된 형식 선언입니다.")
        mapping[key] = node.get("ContentType")
    for name in names - {"[Content_Types].xml"}:
        required = expected.get(name)
        if re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml", name):
            required = MIME + "spreadsheetml.worksheet+xml"
        if re.fullmatch(r"xl/theme/theme[0-9]+\.xml", name):
            required = MIME + "theme+xml"
        if name.endswith(".rels"):
            required = "application/vnd.openxmlformats-package.relationships+xml"
        declared = overrides.get("/" + name, defaults.get(name.rsplit(".", 1)[-1]))
        if required is not None and declared != required:
            reject("UNSUPPORTED_PACKAGE_INVENTORY", "내부 파일과 선언된 형식이 다릅니다.")
    if any(not k or not k.startswith("/") or k[1:] not in names for k in overrides):
        reject("UNSUPPORTED_PACKAGE_INVENTORY", "형식 선언이 실제 파일을 가리키지 않습니다.")
    targets = set()
    for path in ["_rels/.rels", "xl/_rels/workbook.xml.rels"]:
        if path not in names:
            reject("UNSUPPORTED_PACKAGE_INVENTORY", "필수 내부 연결 정보가 없습니다.")
        root = ET.fromstring(archive.read(path))
        ns = "{http://schemas.openxmlformats.org/package/2006/relationships}"
        if root.tag != ns + "Relationships":
            reject("UNSUPPORTED_PACKAGE_INVENTORY", "잘못된 내부 연결 정보입니다.")
        ids = set()
        for node in root:
            name = node.get("Id")
            target = node.get("Target", "")
            kind = node.get("Type", "")
            if (
                node.tag != ns + "Relationship"
                or not name
                or name in ids
                or node.get("TargetMode") not in {None, "Internal"}
            ):
                reject("UNSUPPORTED_PACKAGE_INVENTORY", "중복 또는 외부 연결을 수정하지 않습니다.")
            ids.add(name)
            resolved = posixpath.normpath(
                target.lstrip("/")
                if target.startswith("/")
                else ("" if path == "_rels/.rels" else "xl/") + target
            )
            allowed = (
                {
                    BASE + "officeDocument": r"xl/workbook\.xml",
                    BASE + "extended-properties": r"docProps/app\.xml",
                    (
                        "http://schemas.openxmlformats.org/package/2006/relationships/"
                        "metadata/core-properties"
                    ): r"docProps/core\.xml",
                }
                if path == "_rels/.rels"
                else {
                    BASE + "worksheet": r"xl/worksheets/sheet[0-9]+\.xml",
                    BASE + "styles": r"xl/styles\.xml",
                    BASE + "sharedStrings": r"xl/sharedStrings\.xml",
                    BASE + "theme": r"xl/theme/theme[0-9]+\.xml",
                }
            )
            if (
                kind not in allowed
                or not re.fullmatch(allowed[kind], resolved)
                or resolved not in names
            ):
                reject("UNSUPPORTED_PACKAGE_INVENTORY", "지원하지 않는 내부 연결 또는 형식입니다.")
            targets.add(resolved)
    # Unknown forbidden parts remain an explicit preflight exclusion in the existing inspector.
    known = {
        name
        for name in names
        if name in expected
        or re.fullmatch(r"xl/(worksheets/sheet[0-9]+|theme/theme[0-9]+)\.xml", name)
    }
    if known - targets:
        reject("UNSUPPORTED_PACKAGE_INVENTORY", "연결되지 않은 내부 파일은 수정하지 않습니다.")
