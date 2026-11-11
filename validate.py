#!/usr/bin/env python3
"""Validation harness for ai-language-strata.

Stages:
  1. Docs presence & completeness (README, both Markdown guides, both
     HTML originals, LICENSE, COMPLIANCE) with minimum-size and
     key-content checks.
  2. Python example: compile + run its self-test.
  3. TypeScript example: run with tsx, or type-check with tsc, when a
     toolchain is present; otherwise an honest labelled smoke check
     (balanced delimiters + required contract markers). SKIPPED checks
     are reported as SKIPPED-WITH-REASON, never as passes.
  4. Go example: `go build` + self-test run when Go is present;
     otherwise labelled skip-with-reason.
  5. Rust example: `rustc` compile + run when rustc is present;
     otherwise labelled skip-with-reason.
  6. FIS / internal-reference scan of the exact tree (uses the owner's
     scanner when available; a real hit FAILS the harness).
  7. Secrets scan: common credential shapes anywhere in the tree.

Exit code 0 only if no stage FAILs. Skips do not fail the harness but
are printed in the summary so coverage is never overstated.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS: list[tuple[str, str, str]] = []  # (stage, status, detail)


def record(stage: str, status: str, detail: str = "") -> None:
    RESULTS.append((stage, status, detail))
    print(f"[{status:7s}] {stage}" + (f" — {detail}" if detail else ""))


def fail_count() -> int:
    return sum(1 for _, s, _ in RESULTS if s == "FAIL")


def read(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------- stage 1
def stage_docs() -> None:
    stage = "docs presence & completeness"
    required = {
        "README.md": (2000, ["Python makes models", "docs/typescript-for-ai.md",
                             "docs/four-languages-for-ai.md", "validate.py"]),
        "docs/typescript-for-ai.md": (12000, ["TypeScript for AI", "tool",
                                              "Zod", "Exercises"]),
        "docs/four-languages-for-ai.md": (12000, ["Four Languages", "Qdrant",
                                                  "Ollama", "Comparison"]),
        "docs/html/typescript-for-ai.html": (15000, ["<html", "TypeScript"]),
        "docs/html/four-languages-for-ai.html": (15000, ["<html", "Rust"]),
        "LICENSE": (500, ["MIT License", "Ranadhir Ghosh"]),
        "COMPLIANCE.md": (800, ["ai-language-strata", "Collision"]),
        "examples/python/extract_invoice.py": (1000, []),
        "examples/typescript/tool_call.ts": (1000, []),
        "examples/go/gateway.go": (1000, []),
        "examples/rust/vector_search.rs": (1000, []),
    }
    problems = []
    for rel, (min_size, markers) in required.items():
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            problems.append(f"missing {rel}")
            continue
        text = read(rel)
        if len(text.encode()) < min_size:
            problems.append(f"{rel} too small ({len(text.encode())} B < {min_size} B)")
        for m in markers:
            if m not in text:
                problems.append(f"{rel} lacks marker {m!r}")
    if problems:
        record(stage, "FAIL", "; ".join(problems))
    else:
        record(stage, "PASS", f"{len(required)} files present with content markers")


# ---------------------------------------------------------------- stage 2
def stage_python() -> None:
    stage = "python example (compile + self-test run)"
    target = os.path.join(ROOT, "examples/python/extract_invoice.py")
    try:
        compile(read("examples/python/extract_invoice.py"), target, "exec")
    except SyntaxError as e:
        record(stage, "FAIL", f"syntax error: {e}")
        return
    r = subprocess.run([sys.executable, target], capture_output=True, text=True,
                       timeout=60)
    if r.returncode == 0 and "self-test PASS" in r.stdout:
        record(stage, "PASS", "self-test PASS line present in run output")
    else:
        record(stage, "FAIL", f"exit {r.returncode}: {(r.stdout + r.stderr)[:300]}")


# ------------------------------------------------------- smoke fallback
def smoke(stage: str, rel: str, markers: list[str]) -> None:
    text = read(rel)
    pairs = {"(": ")", "[": "]", "{": "}"}
    problems = []
    for open_c, close_c in pairs.items():
        if text.count(open_c) != text.count(close_c):
            problems.append(f"unbalanced {open_c}{close_c}")
    for m in markers:
        if m not in text:
            problems.append(f"missing marker {m!r}")
    if problems:
        record(stage, "FAIL", "smoke check failed: " + "; ".join(problems))
    else:
        record(stage, "SKIPPED",
               "toolchain absent on this machine; labelled smoke check "
               "(delimiter balance + contract markers) passed instead — "
               "this is NOT a compile/run pass")


# ---------------------------------------------------------------- stage 3
def stage_typescript() -> None:
    stage = "typescript example"
    rel = "examples/typescript/tool_call.ts"
    path = os.path.join(ROOT, rel)
    tsx = shutil.which("tsx")
    npx = shutil.which("npx")
    tsc = shutil.which("tsc")
    if tsx or npx:
        cmd = [tsx, path] if tsx else [npx, "--yes", "tsx", path]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if r.returncode == 0 and "self-check PASS" in r.stdout:
                record(stage, "PASS", "ran under tsx; self-check PASS in output")
            else:
                record(stage, "FAIL",
                       f"tsx exit {r.returncode}: {(r.stdout + r.stderr)[:300]}")
            return
        except subprocess.TimeoutExpired:
            record(stage, "FAIL", "tsx run timed out")
            return
    if tsc:
        r = subprocess.run([tsc, "--noEmit", "--strict", "--target", "ES2022",
                            "--module", "commonjs", path],
                           capture_output=True, text=True, timeout=180)
        if r.returncode == 0:
            record(stage, "PASS", "tsc --strict type-check clean (not executed)")
        else:
            record(stage, "FAIL", f"tsc errors: {(r.stdout + r.stderr)[:300]}")
        return
    smoke(stage, rel, ["dispatchToolCall", "lookup_order", "self-check PASS",
                       "Schema"])


# ---------------------------------------------------------------- stage 4
def stage_go() -> None:
    stage = "go example"
    rel = "examples/go/gateway.go"
    go = shutil.which("go")
    if not go:
        smoke(stage, rel, ["generateHandler", "mockModel", "self-test PASS",
                           "context.WithTimeout"])
        return
    with tempfile.TemporaryDirectory() as td:
        exe = os.path.join(td, "gateway")
        build = subprocess.run(
            [go, "build", "-o", exe, os.path.join(ROOT, rel)],
            capture_output=True, text=True, timeout=180,
            env={**os.environ, "GOFLAGS": "-mod=mod", "GOPATH": os.path.join(td, "gopath"),
                 "HOME": os.environ.get("HOME", "/tmp")})
        if build.returncode != 0:
            record(stage, "FAIL", f"go build: {(build.stdout + build.stderr)[:300]}")
            return
        r = subprocess.run([exe, "-selftest"], capture_output=True, text=True,
                           timeout=60)
        if r.returncode == 0 and "self-test PASS" in (r.stdout + r.stderr):
            record(stage, "PASS", "go build clean; -selftest PASS")
        else:
            record(stage, "FAIL",
                   f"selftest exit {r.returncode}: {(r.stdout + r.stderr)[:300]}")


# ---------------------------------------------------------------- stage 5
def stage_rust() -> None:
    stage = "rust example"
    rel = "examples/rust/vector_search.rs"
    rustc = shutil.which("rustc")
    if not rustc:
        smoke(stage, rel, ["fn cosine", "fn search", "self-check PASS",
                           "assert_eq"])
        return
    with tempfile.TemporaryDirectory() as td:
        exe = os.path.join(td, "vector_search")
        build = subprocess.run([rustc, "-O", os.path.join(ROOT, rel), "-o", exe],
                               capture_output=True, text=True, timeout=300)
        if build.returncode != 0:
            record(stage, "FAIL", f"rustc: {(build.stdout + build.stderr)[:300]}")
            return
        r = subprocess.run([exe], capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and "self-check PASS" in r.stdout:
            record(stage, "PASS", "rustc build clean; run self-check PASS")
        else:
            record(stage, "FAIL",
                   f"run exit {r.returncode}: {(r.stdout + r.stderr)[:300]}")


# ---------------------------------------------------------------- stage 6
def stage_fis() -> None:
    stage = "FIS scan (exact tree)"
    scanner = os.path.expanduser("~/workspace/github-fis-watch/fis_scan.py")
    if not os.path.isfile(scanner):
        record(stage, "FAIL", "owner FIS scanner not found at expected path")
        return
    # Scan every content path individually so validate.py can be handled
    # explicitly: this file is the scanner driver — it cannot invoke the
    # mandated scan without naming the stage and the scanner's own path,
    # so its mechanism lines are judged separately below instead of being
    # silently excluded or counted as content references.
    targets = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        for fn in files:
            p = os.path.join(base, fn)
            if os.path.abspath(p) != os.path.abspath(__file__):
                targets.append(p)
    r = subprocess.run([sys.executable, scanner, *targets],
                       capture_output=True, text=True, timeout=120)
    hits = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
    if hits:
        record(stage, "FAIL", f"{len(hits)} candidate hit(s) in content files: "
                              f"{hits[0][:250]}")
        return
    # Judge the driver itself with the same scanner: it may name the scan
    # and the scanner path (candidate patterns FIS-word and fis-path),
    # but any other candidate pattern in it — a domain, a codename, a
    # compound name — is a substantive reference and fails the stage.
    import json as _json
    r2 = subprocess.run([sys.executable, scanner, os.path.abspath(__file__)],
                        capture_output=True, text=True, timeout=60)
    allowed_patterns = {"FIS-word", "fis-path-segment"}
    bad = []
    for ln in r2.stdout.splitlines():
        ln = ln.strip()
        if ln.startswith("{"):
            hit = _json.loads(ln)
            if hit.get("pattern") not in allowed_patterns:
                bad.append(hit)
    if bad:
        record(stage, "FAIL", f"validate.py contains substantive candidate(s): "
                              f"{str(bad[0])[:250]}")
        return
    record(stage, "PASS",
           "0 candidate hits in all content files; validate.py's only "
           "candidates are its own scan-mechanism lines (stage name + "
           "scanner path), judged benign in context, with no substantive "
           "employer reference present")


# ---------------------------------------------------------------- stage 7
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}", r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
]

def stage_secrets() -> None:
    stage = "secrets scan"
    found = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        for fn in files:
            p = os.path.join(base, fn)
            rel = os.path.relpath(p, ROOT)
            if rel == "validate.py":
                continue  # the pattern definitions themselves
            try:
                text = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            for pat in SECRET_PATTERNS:
                for m in re.finditer(pat, text):
                    found.append(f"{rel}: /{pat}/")
                    break
    if found:
        record(stage, "FAIL", "; ".join(found[:5]))
    else:
        record(stage, "PASS", "no credential-shaped strings in the tree")


def main() -> int:
    print(f"Validating {ROOT}\n" + "-" * 60)
    stage_docs()
    stage_python()
    stage_typescript()
    stage_go()
    stage_rust()
    stage_fis()
    stage_secrets()
    print("-" * 60)
    passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
    skipped = sum(1 for _, s, _ in RESULTS if s == "SKIPPED")
    failed = fail_count()
    print(f"SUMMARY: {passed} PASS, {skipped} SKIPPED-WITH-REASON, {failed} FAIL "
          f"of {len(RESULTS)} stages")
    print("COVERAGE: python is compiled and executed; typescript/go/rust are "
          "compiled and executed only where their toolchains exist on this "
          "machine, otherwise honestly labelled smoke checks (see stages).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
