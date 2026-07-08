#!/usr/bin/env python3
"""
Convert RTCM3 logs in this directory to RINEX by using RTKLIB convbin.

Place RTKLIB's convbin.exe in one of these locations:
  - the same directory as this script
  - ./bin/convbin.exe
  - anywhere listed in PATH

Example:
  py -3 convert_rtcm3_to_rinex.py
  py -3 convert_rtcm3_to_rinex.py --input session_20260511_144858.rtcm3
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_RINEX_VERSION = "3.04"
RTCM_SUFFIXES = {".rtcm3", ".rtcm"}
DEFAULT_ANTENNA_DELTA = (0.0, 0.0, 0.0)


def crc24q(data: bytes) -> int:
    """Return RTCM3 CRC-24Q for data excluding the trailing 3 CRC bytes."""
    crc = 0
    poly = 0x1864CFB
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= poly
            crc &= 0xFFFFFF
    return crc


def scan_rtcm3(path: Path) -> tuple[collections.Counter[int], int, int]:
    """Scan RTCM3 frames and return message counts, CRC errors, and sync skips."""
    data = path.read_bytes()
    counts: collections.Counter[int] = collections.Counter()
    crc_errors = 0
    skipped = 0
    i = 0

    while i + 6 <= len(data):
        if data[i] != 0xD3:
            i += 1
            skipped += 1
            continue

        length = ((data[i + 1] & 0x03) << 8) | data[i + 2]
        frame_end = i + 3 + length + 3
        if frame_end > len(data):
            break

        frame = data[i:frame_end]
        expected_crc = int.from_bytes(frame[-3:], "big")
        actual_crc = crc24q(frame[:-3])
        if actual_crc == expected_crc and length >= 2:
            payload = frame[3:-3]
            message_type = (payload[0] << 4) | (payload[1] >> 4)
            counts[message_type] += 1
            i = frame_end
        else:
            crc_errors += 1
            i += 1

    return counts, crc_errors, skipped


def find_convbin(script_dir: Path, requested: str | None) -> Path:
    candidates: list[Path] = []
    if requested:
        candidates.append(Path(requested))

    candidates.extend(
        [
            script_dir / "convbin.exe",
            script_dir / "convbin",
            script_dir / "bin" / "convbin.exe",
            script_dir / "bin" / "convbin",
        ]
    )

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    found = shutil.which("convbin") or shutil.which("convbin.exe")
    if found:
        return Path(found).resolve()

    raise FileNotFoundError(
        "RTKLIB convbin was not found. Put convbin.exe next to this script, "
        "put it in .\\bin, or add it to PATH."
    )


def list_inputs(base_dir: Path, explicit_input: str | None) -> list[Path]:
    if explicit_input:
        path = Path(explicit_input)
        if not path.is_absolute():
            path = base_dir / path
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        return [path.resolve()]

    files = [
        path.resolve()
        for path in base_dir.iterdir()
        if path.is_file() and path.suffix.lower() in RTCM_SUFFIXES
    ]
    return sorted(files)


def split_convbin_time(value: str) -> list[str]:
    parts = value.strip().split()
    if len(parts) != 2:
        raise ValueError(
            "Time must be written as 'yyyy/mm/dd hh:mm:ss', "
            f"for example '2026/05/11 14:48:58': {value}"
        )
    return parts


def format_convbin_triplet(values: list[float] | tuple[float, float, float]) -> str:
    return "/".join(f"{value:.4f}" for value in values)


def build_command(args: argparse.Namespace, convbin: Path, input_file: Path, output_dir: Path) -> list[str]:
    cmd = [
        str(convbin),
        "-r",
        "rtcm3",
        "-v",
        args.rinex_version,
        "-od",
        "-os",
        "-d",
        str(output_dir),
    ]

    if args.marker:
        cmd.extend(["-hm", args.marker])
    if args.marker_number:
        cmd.extend(["-hn", args.marker_number])
    if args.marker_type:
        cmd.extend(["-ht", args.marker_type])
    if args.receiver:
        cmd.extend(["-hr", args.receiver])
    if args.antenna:
        cmd.extend(["-ha", args.antenna])
    cmd.extend(["-hd", format_convbin_triplet(args.antenna_delta)])
    if args.position:
        cmd.extend(["-hp", *[str(v) for v in args.position]])
    if args.interval is not None:
        cmd.extend(["-ti", str(args.interval)])
    if args.frequency is not None:
        cmd.extend(["-f", str(args.frequency)])
    if args.rinex_options:
        cmd.extend(["-ro", args.rinex_options])
    if args.start:
        cmd.extend(["-ts", *split_convbin_time(args.start)])
    if args.end:
        cmd.extend(["-te", *split_convbin_time(args.end)])

    cmd.append(str(input_file))
    return cmd


def write_log(log_path: Path, cmd: list[str], result: subprocess.CompletedProcess[str]) -> None:
    text = [
        f"timestamp: {dt.datetime.now().isoformat(timespec='seconds')}",
        "command:",
        "  " + subprocess.list2cmdline(cmd),
        "",
        f"returncode: {result.returncode}",
        "",
        "stdout:",
        result.stdout.rstrip(),
        "",
        "stderr:",
        result.stderr.rstrip(),
        "",
    ]
    log_path.write_text("\n".join(text), encoding="utf-8")


def print_scan_summary(input_file: Path) -> None:
    print(f"\n[scan] {input_file.name}")
    counts, crc_errors, skipped = scan_rtcm3(input_file)
    if counts:
        common = ", ".join(f"{msg}:{count}" for msg, count in counts.most_common(12))
        print(f"  RTCM message counts: {common}")
    else:
        print("  No valid RTCM3 messages were found.")
    if crc_errors:
        print(f"  Warning: {crc_errors} CRC error(s) found while scanning.")
    if skipped:
        print(f"  Note: skipped {skipped} byte(s) before sync.")


def convert_one(args: argparse.Namespace, convbin: Path, input_file: Path, output_dir: Path) -> int:
    if not args.no_scan:
        print_scan_summary(input_file)

    cmd = build_command(args, convbin, input_file, output_dir)
    print(f"[convert] {input_file.name} -> {output_dir}")
    if args.dry_run:
        print("  " + subprocess.list2cmdline(cmd))
        return 0

    result = subprocess.run(cmd, capture_output=True, text=True)
    log_path = output_dir / f"{input_file.stem}_convbin.log"
    write_log(log_path, cmd, result)

    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)

    if result.returncode != 0:
        print(f"[error] convbin failed. See log: {log_path}", file=sys.stderr)
        return result.returncode

    produced = sorted(p for p in output_dir.iterdir() if p.is_file() and p.name.startswith(input_file.stem))
    if produced:
        print("[ok] produced:")
        for path in produced:
            print(f"  {path.name}")
    else:
        print("[ok] convbin finished. Check output directory for generated RINEX files.")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert RTCM3 files in this folder to RINEX using RTKLIB convbin."
    )
    parser.add_argument("--input", help="Specific RTCM3 file. Default: all *.rtcm3/*.rtcm in script folder.")
    parser.add_argument("--output-dir", default="rinex", help="Output directory. Default: ./rinex")
    parser.add_argument("--convbin", help="Path to RTKLIB convbin.exe")
    parser.add_argument("--rinex-version", default=DEFAULT_RINEX_VERSION, help="RINEX version. Default: 3.04")
    parser.add_argument("--marker", help="RINEX marker name (-hm)")
    parser.add_argument("--marker-number", help="RINEX marker number (-hn)")
    parser.add_argument("--marker-type", help="RINEX marker type (-ht), for example GEODETIC")
    parser.add_argument("--receiver", help="Receiver information for RINEX header (-hr)")
    parser.add_argument("--antenna", help="Antenna information for RINEX header (-ha)")
    parser.add_argument(
        "--antenna-delta",
        nargs=3,
        type=float,
        default=DEFAULT_ANTENNA_DELTA,
        metavar=("H", "E", "N"),
        help="Antenna delta H/E/N in meters for RINEX header (-hd). Default: 0 0 0",
    )
    parser.add_argument(
        "--position",
        nargs=3,
        type=float,
        metavar=("X", "Y", "Z"),
        help="Approximate receiver position in ECEF meters (-hp X Y Z)",
    )
    parser.add_argument("--start", help="Start UTC time: 'yyyy/mm/dd hh:mm:ss'")
    parser.add_argument("--end", help="End UTC time: 'yyyy/mm/dd hh:mm:ss'")
    parser.add_argument("--interval", type=float, help="Output interval in seconds (-ti)")
    parser.add_argument("--frequency", type=int, help="Frequency option passed to convbin (-f)")
    parser.add_argument("--rinex-options", help="Raw RINEX option string passed to convbin (-ro)")
    parser.add_argument("--scan-only", action="store_true", help="Scan RTCM3 messages without running convbin.")
    parser.add_argument("--no-scan", action="store_true", help="Skip quick RTCM3 message/CRC scan.")
    parser.add_argument("--dry-run", action="store_true", help="Print convbin command without running it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = script_dir / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        inputs = list_inputs(script_dir, args.input)
        if not inputs:
            print(f"No RTCM3 files found in {script_dir}", file=sys.stderr)
            return 2

        if args.scan_only:
            for input_file in inputs:
                print_scan_summary(input_file)
            return 0

        convbin = find_convbin(script_dir, args.convbin)
        print(f"Using convbin: {convbin}")
        print(f"RINEX output: {output_dir}")

        exit_code = 0
        for input_file in inputs:
            exit_code = max(exit_code, convert_one(args, convbin, input_file, output_dir))
        return exit_code
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
