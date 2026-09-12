"""Install locked evaluator libraries and compile with the local JDK 17."""

import argparse
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--download", action="store_true")
args = parser.parse_args()
lock = json.loads((root / "dependencies.lock.json").read_text())
(root / "lib").mkdir(exist_ok=True)
for item in lock["artifacts"]:
    path = root / "lib" / f"{item['artifact']}-{item['version']}.jar"
    if not path.exists():
        if not args.download:
            raise SystemExit("Missing locked dependency; rerun with --download")
        if not item["url"].startswith("https://repo.maven.apache.org/maven2/"):
            raise SystemExit("Unexpected dependency host")
        data = urllib.request.urlopen(item["url"], timeout=30).read()
        if hashlib.sha512(data).hexdigest() != item["sha512"]:
            raise SystemExit("Dependency checksum mismatch")
        path.write_bytes(data)
    if hashlib.sha512(path.read_bytes()).hexdigest() != item["sha512"]:
        raise SystemExit("Dependency checksum mismatch")
result = subprocess.run(
    [
        "javac",
        "--release",
        "17",
        "-cp",
        str(root / "lib/*"),
        "-d",
        str(root / "classes"),
        str(root / "DeliveryCalc.java"),
    ]
)
raise SystemExit(result.returncode)
