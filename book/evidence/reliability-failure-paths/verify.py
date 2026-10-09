"""Scoped reliability regressions; never builds a PDF or uses an existing cluster.

JSON contains exact merged stdout/stderr bytes (base64 and SHA-256).
The log is a normalized display transcript, NOT byte-exact stdout.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASELINE = "ba25116038d35d86ef138fbb089d9094a614ded8"
ASSET_URL = "https://github.com/kubernetes-sigs/controller-tools/releases/download/envtest-v1.37.0/envtest-v1.37.0-linux-amd64.tar.gz"
ASSET_SHA512 = "1d1c453633b72c161a5d5a886cde7ac850be1a2ac796a9e1d4ffacacc64868295bdd2d57aa66cd0c158f5ce510f5dfe3fbc61ac21bd3dcfb875bd70658aa663a"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def linux_path(path):
    path = Path(path).resolve()
    if len(path.drive) != 2 or path.drive[1] != ":":
        raise ValueError("envtest paths must be local Windows drive paths")
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--go", required=True, help="Existing pinned Go executable")
    parser.add_argument("--baseline", default=BASELINE)
    parser.add_argument("--wsl-distro", help="Linux environment for an owned control plane")
    parser.add_argument("--envtest-archive", type=Path, help="Official 1.37.0 Linux amd64 archive")
    args = parser.parse_args()
    if bool(args.wsl_distro) != bool(args.envtest_archive):
        parser.error("--wsl-distro and --envtest-archive must be supplied together")
    go = str(Path(args.go).resolve())
    env = os.environ.copy()
    env.update(GOTOOLCHAIN="local", CGO_ENABLED="1", PYTHONIOENCODING="utf-8")
    env["PATH"] = str(Path(go).parent) + os.pathsep + env["PATH"]
    for key in ("RELIABILITY_MUTANT", "RUN_BOUNDED_LOAD", "GOOS", "GOARCH"):
        env.pop(key, None)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    baseline = subprocess.check_output(["git", "rev-parse", args.baseline + "^{commit}"], cwd=ROOT, text=True).strip()
    modules = ["labs/part11-request-path", "labs/part13-transaction-boundary",
               "projects/opsprobe", "labs/part23-controller-runtime-operator",
               "labs/part10-resource-retention"]
    # Fingerprint tested inputs, excluding generated evidence. A later
    # evidence-only commit cannot put its own commit SHA inside this JSON.
    tracked = subprocess.check_output(["git", "ls-files", "--", *modules,
                                      str(Path(__file__).relative_to(ROOT))], cwd=ROOT, text=True).splitlines()
    sources = {name: sha256(ROOT / name) for name in tracked}
    report = {"schema_version": 2, "tested_head": head, "baseline": baseline,
              "commit_range": baseline + ".." + head, "tested_source_sha256": sources,
              "os": platform.platform(), "python": sys.version, "go": go,
              "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "steps": [], "real_api": "NOT_RUN",
              "output_contract": "base64 is exact merged stdout/stderr; log is normalized display only",
              "prerequisites": {n: shutil.which(n) for n in ("gcc", "wsl")}}
    pdf = ROOT / "Golang_Master.pdf"
    report["pdf_before_sha256"] = sha256(pdf)
    logs = ["DISPLAY TRANSCRIPT ONLY; exact merged output bytes are in validation.json.\n"]

    def persist():
        (OUT / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        (OUT / "validation.log").write_text("".join(logs), encoding="utf-8", newline="\n")

    def run(name, cwd, command, overrides=None, expected_exit=0, marker=None, result="PASS", skip_marker=None):
        started = time.monotonic()
        capture_error = None
        try:
            completed = subprocess.run(command, cwd=ROOT / cwd, env=env | (overrides or {}),
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            code, raw = completed.returncode, completed.stdout
        except subprocess.TimeoutExpired as exc:
            code, raw, capture_error = -1, exc.output or b"", "HARNESS_TIMEOUT: " + str(exc)
        except OSError as exc:
            code, raw, capture_error = -1, b"", "HARNESS_EXECUTION_ERROR: " + str(exc)
        output = raw.decode("utf-8", errors="replace")
        skipped = skip_marker is not None and skip_marker in output and code == 0
        ok = capture_error is None and code == expected_exit and (marker is None or marker in output)
        status = "NOT_RUN" if skipped else result if ok else "FAIL"
        step = dict(name=name, cwd=cwd, command=command, environment=overrides or {},
                    exit_code=code, expected_exit=expected_exit, expected_marker=marker,
                    accepted=ok, result=status, capture_error=capture_error,
                    elapsed_seconds=round(time.monotonic() - started, 3),
                    combined_output_base64=base64.b64encode(raw).decode("ascii"),
                    combined_output_sha256=hashlib.sha256(raw).hexdigest(),
                    combined_output_text=output)
        report["steps"].append(step)
        display = "\n".join(line.expandtabs(4).rstrip() for line in output.splitlines()) + "\n"
        logs.append(f"\n[{name}] cwd={cwd}\ncommand={json.dumps(command)}\n"
                    f"environment={json.dumps(overrides or {})}\n{display}"
                    f"capture_error={capture_error} exit_code={code} result={status} accepted={ok}\n")
        print(f"{name}: exit={code} result={status} accepted={ok}", flush=True)
        if not ok:
            print(capture_error or output, flush=True)
        persist()
        return step

    run("baseline_ancestor", ".", ["git", "merge-base", "--is-ancestor", baseline, head])
    run("git_commit_range_check", ".", ["git", "diff", "--check", report["commit_range"]])
    # 1 means a nonempty staged diff, not a test failure; errors >1 are failures.
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode
    run("git_index_state", ".", ["git", "diff", "--cached", "--quiet"], expected_exit=1 if staged == 1 else 0)
    if staged == 1:
        run("git_staged_diff_check", ".", ["git", "diff", "--cached", "--check"])
    else:
        report["staged_diff"] = "NOT_RUN: index empty, checked with git diff --cached --quiet"
    run("git_worktree_diff_check", ".", ["git", "diff", "--check"])
    run("toolchain", ".", [go, "version"])
    run("go_environment", ".", [go, "env", "-json", "GOOS", "GOARCH", "GOVERSION", "CGO_ENABLED", "CC"])
    for module in modules:
        packages = ["./failurelab"] if module == "projects/opsprobe" else ["./..."]
        run(module + ":test", module, [go, "test", "-mod=readonly", "-count=1", "-timeout=120s", "-v", *packages])
        run(module + ":vet", module, [go, "vet", "-mod=readonly", *packages])
        run(module + ":race", module, [go, "test", "-mod=readonly", "-race", "-count=1", "-timeout=120s", *packages])
    for module, package in [(modules[0], "./identity"), (modules[1], "./outbox"), (modules[2], "./failurelab")]:
        overrides = {"RUN_BOUNDED_LOAD": "1"} if package == "./failurelab" else {}
        run(module + ":repeat", module, [go, "test", "-mod=readonly", "-count=20", "-timeout=120s", "-v", package], overrides)
    run("bounded_load_race_repeat", modules[2],
        [go, "test", "-mod=readonly", "-race", "-count=20", "-timeout=120s", "-run", "^TestBoundedWorkloadObservation$", "-v", "./failurelab"], {"RUN_BOUNDED_LOAD": "1"})
    mutants = [
        (modules[1], "./outbox", "TestOutboxContract", "split_commit", "committed business requires pending event"),
        (modules[2], "./failurelab", "TestConsumerStopsContract", "uncancellable_send", "contract: cancellation must release result handoff"),
        (modules[0], "./identity", "TestAuthorizationContract", "trust_equals_role", "authenticated caller"),
        (modules[2], "./failurelab", "TestBoundedWorkloadObservation", "lost_completion_count", "workload completion accounting"),
    ]
    for module, package, test, mutant, marker in mutants:
        run("EXPECTED_FAILURE:" + mutant, module,
            [go, "test", "-mod=readonly", "-count=1", "-timeout=30s", "-run", "^" + test + "$", "-v", package],
            {"RELIABILITY_MUTANT": mutant, "RUN_BOUNDED_LOAD": "1"}, expected_exit=1, marker=marker, result="EXPECTED_FAILURE")
    run("real_api_host_prerequisite", modules[3],
        [go, "test", "-mod=readonly", "-tags", "integration", "-count=1", "-v", "./integration"], skip_marker="NOT_RUN")
    binary = ROOT / ".workspace/reliability-envtest.test"
    binary.parent.mkdir(exist_ok=True)
    compiled = run("linux_integration_compile_ONLY", modules[3],
                   [go, "test", "-mod=readonly", "-tags", "integration", "-c", "-o", str(binary), "./integration"],
                   {"GOOS": "linux", "GOARCH": "amd64", "CGO_ENABLED": "0"}, result="COMPILE_ONLY")
    if args.envtest_archive:
        archive = args.envtest_archive.resolve()
        actual = hashlib.sha512(archive.read_bytes()).hexdigest()
        assets = archive.parent / "controller-tools/envtest"
        report["envtest_assets"] = {"url": ASSET_URL, "archive_sha512": actual,
                                    "expected_sha512": ASSET_SHA512, "distro": args.wsl_distro}
        if actual != ASSET_SHA512:
            report["real_api"] = "NOT_VERIFIED: archive checksum mismatch"
            persist()
            return 1
        # Re-extract verified bytes instead of trusting arbitrary adjacent files.
        extract = "cd " + shlex.quote(linux_path(archive.parent)) + " && tar -xzf " + shlex.quote(archive.name) + " --no-same-owner"
        extracted = run("envtest_verified_extract", ".", ["wsl", "-d", args.wsl_distro, "--exec", "sh", "-lc", extract])
        if compiled["accepted"] and extracted["accepted"]:
            report["envtest_assets"]["executables_sha256"] = {n: sha256(assets / n) for n in ("etcd", "kube-apiserver", "kubectl")}
            for executable in ("kube-apiserver", "etcd"):
                run("envtest_version:" + executable, ".", ["wsl", "-d", args.wsl_distro, "--exec", linux_path(assets / executable), "--version"])
            prefix = "cd " + shlex.quote(linux_path(ROOT / modules[3] / "integration")) + " && env -u TEST_ASSET_KUBE_APISERVER -u TEST_ASSET_ETCD -u TEST_ASSET_KUBECTL -u KUBECONFIG -u RELIABILITY_MUTANT KUBEBUILDER_ASSETS=" + shlex.quote(linux_path(assets)) + " USE_EXISTING_CLUSTER=false "
            flags = shlex.quote(linux_path(binary)) + " '-test.run=^TestRealAPIContract$' -test.v -test.timeout=120s"
            real = run("real_api_contract", ".", ["wsl", "-d", args.wsl_distro, "--exec", "sh", "-lc", prefix + flags], marker="INTEGRATION_TESTED owned real API")
            report["real_api"] = "INTEGRATION_TESTED" if real["accepted"] else "NOT_VERIFIED"
            run("EXPECTED_FAILURE:root_status_write", ".", ["wsl", "-d", args.wsl_distro, "--exec", "sh", "-lc", prefix + "RELIABILITY_MUTANT=root_status_write " + flags], expected_exit=1, marker="status writer contract", result="EXPECTED_FAILURE")
    report["pdf_sha256"] = sha256(pdf)
    report["pdf_unchanged"] = report["pdf_sha256"] == report["pdf_before_sha256"]
    report["tested_sources_unchanged"] = all(sha256(ROOT / name) == value for name, value in sources.items())
    report["result_counts"] = {label: sum(s["result"] == label for s in report["steps"]) for label in ("PASS", "EXPECTED_FAILURE", "NOT_RUN", "COMPILE_ONLY", "FAIL")}
    report["scoped_checks_accepted"] = all(s["accepted"] for s in report["steps"]) and report["pdf_unchanged"] and report["tested_sources_unchanged"]
    report["ended"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    persist()
    return 0 if report["scoped_checks_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
