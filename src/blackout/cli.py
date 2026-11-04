"""Command line entry point: ``blackout inspect | clean | profile | eda | mine``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from . import config
from .clean import clean, infer_roles, read_raw
from .profile import text_profile


def _overrides(pairs: list[str] | None) -> dict[str, str]:
    out = {}
    for p in pairs or []:
        role, _, col = p.partition("=")
        if not col:
            raise SystemExit(f"--map expects role=column, got {p!r}")
        out[role] = col
    return out


def cmd_inspect(args: argparse.Namespace) -> int:
    raw = read_raw(args.input)
    print(f"{len(raw):,} rows x {raw.shape[1]} columns")
    print("\nColumns (dtype, % missing):")
    for c in raw.columns:
        print(f"  {c!r:40} {str(raw[c].dtype):10} {raw[c].isna().mean():6.1%}")
    print("\nInferred roles:")
    for role, cols in infer_roles(list(raw.columns), _overrides(args.map)).items():
        print(f"  {role:14} <- {cols}")
    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    table, report = clean(read_raw(args.input), _overrides(args.map))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(args.output)
    report_path = args.output.with_suffix(".report.md")
    report_path.write_text(report.to_markdown())
    print(f"wrote {args.output} ({len(table):,} hourly rows) and {report_path}")
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    if not args.clean.exists():
        raise SystemExit(f"{args.clean} not found. Run `blackout clean` first.")
    print(text_profile(pd.read_parquet(args.clean)))
    return 0


def cmd_eda(args: argparse.Namespace) -> int:
    from .eda import run  # matplotlib is only needed for this command

    if not args.clean.exists():
        raise SystemExit(f"{args.clean} not found. Run `blackout clean` first.")
    print(run(args.clean))
    return 0


def cmd_mine(args: argparse.Namespace) -> int:
    from .mine import run

    if not args.clean.exists():
        raise SystemExit(f"{args.clean} not found. Run `blackout clean` first.")
    run(args.clean, skip_cluster_search=args.skip_cluster_search)
    print(f"tables and figures written to {config.RESULTS}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="blackout", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    for name, fn, help_ in [
        ("inspect", cmd_inspect, "show raw columns and the roles inferred from them"),
        ("clean", cmd_clean, "write the cleaned hourly table"),
    ]:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("--input", type=Path, default=config.MAIN_DATASET_PATH)
        sp.add_argument("--map", action="append", metavar="ROLE=COLUMN", help="pin a column role")
        if name == "clean":
            sp.add_argument("--output", type=Path, default=config.CLEAN_HOURLY_PATH)
        sp.set_defaults(fn=fn)

    sp = sub.add_parser("profile", help="reproduce the README's first profile from the clean table")
    sp.add_argument("--clean", type=Path, default=config.CLEAN_HOURLY_PATH)
    sp.set_defaults(fn=cmd_profile)

    sp = sub.add_parser("eda", help="write the data-report figures and print the tables behind them")
    sp.add_argument("--clean", type=Path, default=config.CLEAN_HOURLY_PATH)
    sp.set_defaults(fn=cmd_eda)

    sp = sub.add_parser("mine", help="run regimes, clusters, motifs, rules, episodes, anomalies")
    sp.add_argument("--clean", type=Path, default=config.CLEAN_HOURLY_PATH)
    sp.add_argument("--skip-cluster-search", action="store_true", help="reuse docs/results/cluster_comparison.csv")
    sp.set_defaults(fn=cmd_mine)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
