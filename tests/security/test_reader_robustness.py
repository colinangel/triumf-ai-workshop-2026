"""Hostile-input checks for the C++ WFB1 reader (Lab S, Advanced track).

A DAQ reader is the first code to touch bytes that came from somewhere else:
a digitiser, a colleague's disk, a download. These tests feed it malformed
files and require that it never reads or writes out of bounds, never hangs,
and fails with a clear error instead of a crash.

The reader is rebuilt with AddressSanitizer and UndefinedBehaviorSanitizer, so
an out-of-bounds read is reported even when it would not crash a normal build.

Run:
    uv run pytest tests/security -v                               # legacy/cpp (fails, by design)
    uv run pytest tests/security -v --wfb1-source work/reader     # a folder with your CMakeLists.txt

Skips if there is no CMake or no compiler with sanitizer support (on Windows,
run it inside WSL 2).
"""

from __future__ import annotations

import os
import shutil
import struct
import subprocess
from pathlib import Path

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[2]
FILE_HEADER = "<4sHHIIQ"  # magic, version, n_channels, n_samples, dt_ps, n_events (24 bytes)
EVENT_HEADER = "<IHQ"  # event_id, flags, trigger_time_ps (14 bytes)
SANITIZER_ENV = {
    # Report problems instead of hiding them. Allocations over 1 GB are reported
    # too: a reader that allocates whatever the header claims fails, one that
    # checks the header against the file size first never gets that far.
    "ASAN_OPTIONS": "detect_leaks=0:allocator_may_return_null=1:max_allocation_size_mb=1024:abort_on_error=0",
    "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
}
TIMEOUT_S = 10


def _sanitizers_work(tmp: Path) -> bool:
    src = tmp / "probe.cpp"
    src.write_text("int main() { return 0; }\n")
    cxx = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
    if not cxx:
        return False
    r = subprocess.run([cxx, "-fsanitize=address,undefined", str(src), "-o", str(tmp / "probe")], capture_output=True, check=False)
    return r.returncode == 0


@pytest.fixture(scope="module")
def reader(tmp_path_factory) -> Path:
    if not shutil.which("cmake"):
        pytest.skip("no CMake on this machine")
    work = tmp_path_factory.mktemp("san")
    if not _sanitizers_work(work):
        pytest.skip("compiler without AddressSanitizer support (on Windows use WSL 2)")
    source = Path(os.environ.get("WFB1_SOURCE") or ROOT / "legacy" / "cpp").resolve()
    flags = "-fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=undefined -g -O1"
    build = work / "build"
    cfg = subprocess.run(
        ["cmake", "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Debug", f"-DCMAKE_CXX_FLAGS={flags}",
         "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined"],
        capture_output=True, text=True, check=False,
    )
    assert cfg.returncode == 0, cfg.stderr
    b = subprocess.run(["cmake", "--build", str(build)], capture_output=True, text=True, check=False)
    assert b.returncode == 0, b.stdout + b.stderr
    return next(p for p in build.rglob("wfb1_reader*") if p.is_file() and os.access(p, os.X_OK))


def _file(n_channels=1, n_samples=512, n_events=3, declared_events=None, declared_samples=None, declared_channels=None,
          version=1, magic=b"WFB1") -> bytes:
    """A small, valid WFB1 file, optionally with a header that lies about its contents."""
    rng = np.random.default_rng(1)
    head = struct.pack(
        FILE_HEADER, magic, version,
        n_channels if declared_channels is None else declared_channels,
        n_samples if declared_samples is None else declared_samples,
        4000,
        n_events if declared_events is None else declared_events,
    )
    body = b"".join(
        struct.pack(EVENT_HEADER, e, 0, 1000 * e) + rng.integers(7900, 8100, n_channels * n_samples, dtype="<u2").tobytes()
        for e in range(n_events)
    )
    return head + body


def _run(reader: Path, data: bytes, tmp_path: Path) -> subprocess.CompletedProcess:
    path = tmp_path / "input.wfb1"
    path.write_bytes(data)
    try:
        return subprocess.run([str(reader), str(path)], capture_output=True, text=True, timeout=TIMEOUT_S,
                              env={**os.environ, **SANITIZER_ENV}, check=False)
    except subprocess.TimeoutExpired:
        pytest.fail(f"reader still running after {TIMEOUT_S} s on a {len(data)}-byte file: it trusts the header and loops")


def _assert_memory_safe(out: subprocess.CompletedProcess):
    report = [line for line in out.stderr.splitlines() if "Sanitizer" in line or "runtime error:" in line]
    assert not report, "memory-safety problem:\n" + "\n".join(report[:5])
    assert out.returncode < 128 and out.returncode >= 0, f"crashed with exit code {out.returncode}"


def _assert_clean_rejection(out: subprocess.CompletedProcess):
    _assert_memory_safe(out)
    assert out.returncode != 0, "malformed input was accepted (exit code 0)"
    assert out.stderr.strip(), "say on stderr what is wrong with the file"


def test_valid_file_still_reads(reader, tmp_path):
    out = _run(reader, _file(), tmp_path)
    _assert_memory_safe(out)
    assert out.returncode == 0, out.stderr
    assert len(out.stdout.strip().splitlines()) == 1 + 3, "header plus one row per event and channel"


def test_record_too_short_for_the_windows(reader, tmp_path):
    # Baseline uses samples 0-99 and charge 120-199; a 50-sample record must be refused, not read past.
    _assert_clean_rejection(_run(reader, _file(n_samples=50), tmp_path))


def test_channel_times_sample_count_overflow(reader, tmp_path):
    # 2 x 0x80000001 wraps to 2 in 32-bit arithmetic: a tiny buffer, then reads far past it.
    _assert_clean_rejection(_run(reader, _file(n_samples=512, declared_channels=2, declared_samples=0x80000001), tmp_path))


def test_header_claims_more_events_than_the_file_holds(reader, tmp_path):
    _assert_clean_rejection(_run(reader, _file(n_events=1, declared_events=2**60), tmp_path))


def test_header_claims_a_huge_record(reader, tmp_path):
    # 65535 channels x 4e9 samples: allocating that is the bug, not the file.
    _assert_clean_rejection(_run(reader, _file(declared_channels=0xFFFF, declared_samples=0xFFFFFFF0), tmp_path))


def test_empty_file(reader, tmp_path):
    _assert_clean_rejection(_run(reader, b"", tmp_path))


@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.lists(st.tuples(st.integers(0, 24 + 14 + 40 - 1), st.integers(0, 255)), min_size=1, max_size=6),
       st.integers(0, 3 * (14 + 1024)))
def test_fuzzed_headers_never_break_memory_safety(reader, tmp_path, edits, cut):
    """Random byte edits in the headers and first samples, plus random truncation."""
    data = bytearray(_file(n_samples=512, n_events=3))
    for pos, value in edits:
        data[pos] = value
    data = bytes(data[: len(data) - cut])
    _assert_memory_safe(_run(reader, data, tmp_path))
