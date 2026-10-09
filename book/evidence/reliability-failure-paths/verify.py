"""Reproduce scoped checks; never builds or modifies a publication PDF.

Writes actual command output and exit codes next to this script. No credentials,
clusters, Internet HTTP workload, dependency updates or publication QA implied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--go", required=True, help="Existing pinned Go executable")
    args = parser.parse_args()
    go = str(Path(args.go).resolve())
    env = os.environ.copy()
    env.update(GOTOOLCHAIN="local", CGO_ENABLED="1", PYTHONIOENCODING="utf-8")
    env["PATH"] = str(Path(go).parent) + os.pathsep + env["PATH"]
    env.pop("RELIABILITY_MUTANT", None)
    env.pop("RUN_BOUNDED_LOAD", None)
    report = {"os": platform.platform(), "python": sys.version,
              "go": go, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "steps": [], "real_api": "NOT_RUN"}
    report["prerequisites"] = {name: shutil.which(name) for name in ["docker", "kubectl", "kind", "wsl"]}
    report["kubebuilder_assets"] = env.get("KUBEBUILDER_ASSETS")
    pdf = ROOT / "Golang_Master.pdf"
    pdf_before = hashlib.sha256(pdf.read_bytes()).hexdigest()
    report["pdf_before_sha256"] = pdf_before
    logs = []

    def run(name, cwd, command, overrides=None, expected_exit=0, marker=None):
        step_env = env | (overrides or {})
        started = time.monotonic()
        try:
            completed = subprocess.run(command, cwd=ROOT / cwd, env=step_env,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       timeout=600, encoding="utf-8", errors="replace")
            code, output = completed.returncode, completed.stdout
        except subprocess.TimeoutExpired as exc:
            # Go tests themselves use -timeout and child CommandContext budgets.
            code = -1
            output = "HARNESS_TIMEOUT: " + str(exc)
        except OSError as exc:
            code, output = -1, "HARNESS_EXECUTION_ERROR: " + str(exc)
        ok = code == expected_exit and (marker is None or marker in output)
        step = dict(name=name, cwd=cwd, command=command, environment=overrides or {},
                    exit_code=code, expected_exit=expected_exit,
                    expected_marker=marker, accepted=ok,
                    elapsed_seconds=round(time.monotonic()-started, 3))
        report["steps"].append(step)
        # Display-only whitespace formatting; retain exact stdout in JSON.
        step["stdout"] = output
        display = "\n".join(line.expandtabs(4).rstrip() for line in output.splitlines()) + "\n"
        logs.append(f"\n[{name}] cwd={cwd}\ncommand={json.dumps(command)}\n"
                    f"environment={json.dumps(overrides or {})}\n{display}"
                    f"exit_code={code} accepted={ok}\n")
        print(f"{name}: exit={code} accepted={ok}", flush=True)
        if not ok:
            print(output, flush=True)
        # Persist partial evidence after EVERY command, including a failed one.
        (OUT / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
        (OUT / "validation.log").write_text("".join(logs), encoding="utf-8")

    run("toolchain", ".", [go, "version"])
    run("go_environment", ".", [go, "env", "-json", "GOOS", "GOARCH", "GOVERSION", "CGO_ENABLED", "CC"])
    modules = ["labs/part11-request-path", "labs/part13-transaction-boundary",
               "projects/opsprobe", "labs/part23-controller-runtime-operator",
               "labs/part16-real-signals", "labs/part25-github-automation",
               "labs/part28-mcp-ops-tools", "labs/part10-resource-retention"]
    for module in modules:
        run(module+":test", module, [go, "test", "-mod=readonly", "-count=1", "-timeout=120s", "-v", "./..."])
        run(module+":vet", module, [go, "vet", "-mod=readonly", "./..."])
        run(module+":race", module, [go, "test", "-mod=readonly", "-race", "-count=1", "-timeout=120s", "./..."])
    for module, package in [(modules[0], "./identity"), (modules[1], "./outbox"), (modules[2], "./failurelab")]:
        run(module+":repeat", module, [go, "test", "-mod=readonly", "-count=20", "-timeout=120s", package])
    mutants = [
        (modules[1], "./outbox", "TestOutboxContract", "split_commit", "committed business requires pending event"),
        (modules[2], "./failurelab", "TestConsumerStopsContract", "uncancellable_send", "contract: cancellation must release result handoff"),
        (modules[0], "./identity", "TestAuthorizationContract", "trust_equals_role", "authenticated caller"),
    ]
    for module, package, test, mutant, marker in mutants:
        run("EXPECTED_FAILURE:"+mutant, module,
            [go, "test", "-count=1", "-timeout=30s", "-run", "^"+test+"$", "-v", package],
            {"RELIABILITY_MUTANT": mutant}, expected_exit=1, marker=marker)
    run("bounded_load", modules[2], [go, "test", "-count=1", "-timeout=30s", "-run", "^TestBoundedWorkloadObservation$", "-v", "./failurelab"], {"RUN_BOUNDED_LOAD":"1"})
    run("real_api_prerequisite", modules[3], [go, "test", "-tags", "integration", "-count=1", "-v", "./integration"])
    report["real_api"] = "NOT_RUN" if "NOT_RUN" in logs[-1] else (
        "INTEGRATION_TESTED" if report["steps"][-1]["accepted"] and
        "INTEGRATION_TESTED owned real API" in logs[-1] else "NOT_VERIFIED")
    run("linux_integration_compile_ONLY", modules[3],
        [go, "test", "-mod=readonly", "-tags", "integration", "-c", "-o", str(ROOT / ".workspace/reliability-envtest.test"), "./integration"],
        {"GOOS":"linux", "GOARCH":"amd64", "CGO_ENABLED":"0"})
    for name in ["validate_main_manuscript_no_bullets", "validate_code_width", "validate_error_atlas", "validate_manuscript_diagrams", "validate_diagram_encoding"]:
        run(name, ".", [sys.executable, str(ROOT / "scripts" / (name+".py"))])
    run("git_diff_check", ".", ["git", "diff", "--check"])
    report["pdf_sha256"] = hashlib.sha256(pdf.read_bytes()).hexdigest()
    report["pdf_unchanged"] = report["pdf_sha256"] == pdf_before
    report["scoped_checks_accepted"] = all(step["accepted"] for step in report["steps"]) and report["pdf_unchanged"]
    report["ended"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    (OUT / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return 0 if report["scoped_checks_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
