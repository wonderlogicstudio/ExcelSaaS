from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.synthetic_validation.generator import generate_dataset
from tools.synthetic_validation.runner import _verify_truth_hash
from tools.synthetic_validation.schema import (
    dataclass_to_dict,
    read_json,
    sha256_json,
    write_json,
)


def _reordered_json(value: object) -> str:
    if isinstance(value, dict):
        return "{" + ", ".join(f"{json.dumps(key)}: {_reordered_json(item)}" for key, item in reversed(list(value.items()))) + "}"
    if isinstance(value, list):
        return "[\n" + ",\n".join(_reordered_json(item) for item in value) + "\n]"
    return json.dumps(value, ensure_ascii=False)


class TruthHashTests(unittest.TestCase):
    def test_matching_manifest_and_truth_file_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = generate_dataset(run_id="truth", pair_count=1, seed=11, dataset_root=root / "dataset")

            self.assertEqual(_verify_truth_hash(manifest, root / "dataset"), manifest.truth_hash)

    def test_manifest_payload_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = generate_dataset(run_id="truth", pair_count=1, seed=12, dataset_root=root / "dataset")
            tampered_workbook = replace(manifest.workbooks[0], workbook_id="tampered")
            tampered = replace(manifest, workbooks=[tampered_workbook, *manifest.workbooks[1:]])

            with self.assertRaisesRegex(RuntimeError, "Manifest truth_hash"):
                _verify_truth_hash(tampered, root / "dataset")

    def test_declared_manifest_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = generate_dataset(run_id="truth", pair_count=1, seed=13, dataset_root=root / "dataset")
            tampered = replace(manifest, truth_hash="0" * 64)

            with self.assertRaisesRegex(RuntimeError, "Manifest truth_hash"):
                _verify_truth_hash(tampered, root / "dataset")

    def test_truth_file_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = generate_dataset(run_id="truth", pair_count=1, seed=14, dataset_root=root / "dataset")
            truth_payload = read_json(root / "dataset" / "truth.json")
            truth_payload[0]["workbook_id"] = "tampered"
            write_json(root / "dataset" / "truth.json", truth_payload)

            with self.assertRaisesRegex(RuntimeError, "truth.json hash"):
                _verify_truth_hash(manifest, root / "dataset")

    def test_missing_truth_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = generate_dataset(run_id="truth", pair_count=1, seed=15, dataset_root=root / "dataset")
            (root / "dataset" / "truth.json").unlink()

            with self.assertRaisesRegex(RuntimeError, "truth.json is required"):
                _verify_truth_hash(manifest, root / "dataset")

    def test_equivalent_truth_json_formatting_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = generate_dataset(run_id="truth", pair_count=1, seed=16, dataset_root=root / "dataset")
            truth_payload = [dataclass_to_dict(workbook) for workbook in manifest.workbooks]
            self.assertEqual(sha256_json(truth_payload), manifest.truth_hash)
            (root / "dataset" / "truth.json").write_text(_reordered_json(truth_payload), encoding="utf-8")

            self.assertEqual(_verify_truth_hash(manifest, root / "dataset"), manifest.truth_hash)


if __name__ == "__main__":
    unittest.main()
