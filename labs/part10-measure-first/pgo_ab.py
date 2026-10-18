"""Small PGO A/B for Render, not production evidence; standard library only."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
from datetime import datetime, timezone


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--go", default="go")
    parser.add_argument("--out", type=Path, default=Path("artifacts/pgo-ab"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    out = args.out.resolve()
    # Refuse to overwrite earlier experiment evidence or source.
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, GOTOOLCHAIN="local", GOWORK="off", GOMAXPROCS="2")
    records = []

    def run(command):
        result = subprocess.run(command, cwd=root, env=env, capture_output=True)
        record = {"command": [str(x) for x in command], "exit_code": result.returncode}
        for stream in ("stdout", "stderr"):
            data = getattr(result, stream)
            record[stream + "_utf8"] = data.decode("utf-8", "replace")
            record[stream + "_base64"] = base64.b64encode(data).decode("ascii")
            record[stream + "_sha256"] = hashlib.sha256(data).hexdigest()
        records.append(record)
        if result.returncode:
            raise RuntimeError(record)
        return record

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    evidence = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "contract": "Render 1000 prebuilt readings; serial benchmark; GOMAXPROCS=2; 400ms/sample",
        "scope": "MICROBENCHMARK_ONLY_NOT_PRODUCTION_REPRESENTATIVE",
        "source_sha256": {str(p.relative_to(root)): sha(p) for p in [
            root / "go.mod", root / "fixed/render.go", root / "fixed/render_test.go",
            Path(__file__).resolve()]},
        "records": records,
    }
    try:
        evidence["go_version"] = run([args.go, "version"])["stdout_utf8"].strip()
        evidence["go_env"] = run([args.go, "env", "-json", "GOOS", "GOARCH", "GOEXPERIMENT"])["stdout_utf8"]
        suffix = ".exe" if os.name == "nt" else ""
        profile = out / "training.pprof"
        run([args.go, "test", "-pgo=off", "-run=^$", "-bench=^BenchmarkRender$",
             "-benchtime=3s", "-cpu=2", "-cpuprofile=" + str(profile),
             "-o", str(out / ("training.test" + suffix)), "./fixed"])
        evidence["training_profile_sha256"] = sha(profile)
        run([args.go, "tool", "pprof", "-top", str(profile)])
        binaries = {}
        for variant, pgo in [("off", "off"), ("on", str(profile))]:
            binary = out / (variant + ".test" + suffix)
            # -x records the actual compiler -pgoprofile argument, not an assumed use.
            run([args.go, "test", "-x", "-c", "-pgo=" + pgo, "-o", str(binary), "./fixed"])
            binaries[variant] = binary
            run([str(binary), "-test.run=^TestRender", "-test.v=true"])
        evidence["binary_sha256"] = {name: sha(path) for name, path in binaries.items()}
        benchmark = ["-test.run=^$", "-test.bench=^BenchmarkRender$",
                     "-test.benchtime=400ms", "-test.benchmem=true", "-test.cpu=2"]
        for binary in binaries.values():
            warmup = run([str(binary), *benchmark])
            warmup["classification"] = "WARMUP_EXCLUDED"
        samples = {"off": [], "on": []}
        for pair in range(6):
            # Alternate order, keep the same immutable binaries, never profile A/B timing.
            order = ["off", "on"] if pair % 2 == 0 else ["on", "off"]
            for variant in order:
                record = run([str(binaries[variant]), *benchmark])
                match = re.search(r"^BenchmarkRender-2\s+\d+\s+([\d.]+) ns/op\s+(\d+) B/op\s+(\d+) allocs/op", record["stdout_utf8"], re.M)
                if not match:
                    raise RuntimeError("unrecognized benchmark output")
                sample = {"pair": pair + 1, "variant": variant,
                          "ns_per_op": float(match[1]), "bytes_per_op": int(match[2]),
                          "allocs_per_op": int(match[3])}
                samples[variant].append(sample)
                record["sample"] = sample
        evidence["samples"] = samples
        evidence["summary"] = {variant: {
            "ns_min": min(s["ns_per_op"] for s in values),
            "ns_max": max(s["ns_per_op"] for s in values),
            "ns_median": statistics.median(s["ns_per_op"] for s in values),
            "count": len(values),
        } for variant, values in samples.items()}
        evidence["interpretation_limit"] = "Ranges and medians only; no statistical significance, no speedup assertion; no end-to-end service benchmark."
        evidence["status"] = "PASS"
    except Exception as error:
        evidence["status"] = "FAIL"
        evidence["error"] = str(error)
    evidence["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (out / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: evidence.get(key) for key in ["status", "go_version", "summary", "error"]}, ensure_ascii=False))
    return int(evidence["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
