"""Command-line interface for the Virelion biosafety level assessment tool.

Two ways to use it:

1. Interactive wizard (default) -- walks through the six steps one at a time::

       virelion-bsa

2. Non-interactive / scriptable -- pass every field as a flag, useful in CI
   or notebooks::

       virelion-bsa --cell-type ipsc --genetic-mod none --vector lentivirus \\
           --scale small --use research --risk none --export out.txt
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from . import data, export
from .models import CellType, GeneticMod, Inputs, Risk, Scale, Use, Vector

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_COLORS = {
    "red": "\033[38;5;131m",
    "amber": "\033[38;5;172m",
    "green": "\033[38;5;71m",
    "teal": "\033[38;5;30m",
}

ENUM_BY_KEY = {
    "cell_type": CellType,
    "genetic_mod": GeneticMod,
    "vector": Vector,
    "scale": Scale,
    "use": Use,
    "risk": Risk,
}


def _supports_color(no_color: bool) -> bool:
    return not no_color and sys.stdout.isatty()


def _c(text: str, color: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{_COLORS.get(color, '')}{text}{_RESET}"


def _bold(text: str, enabled: bool) -> str:
    return f"{_BOLD}{text}{_RESET}" if enabled else text


def _dim(text: str, enabled: bool) -> str:
    return f"{_DIM}{text}{_RESET}" if enabled else text


def prompt_step(step: "data.Step", color: bool) -> object:
    """Interactively ask the user to pick one option for a wizard step."""
    print()
    print(_bold(f"[{step.number}] {step.title}", color))
    print(_dim(step.hint, color))
    for i, opt in enumerate(step.options, start=1):
        print(f"  {i}. {_bold(opt.label, color)} \u2014 {_dim(opt.desc, color)}")
    while True:
        choice = input(f"Select 1-{len(step.options)}: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(step.options):
            return step.options[int(choice) - 1].value
        print(_c("  Not a valid choice, try again.", "red", color))


def run_wizard(color: bool) -> Inputs:
    print(_bold("VIRELION BIOTECH \u2014 Biosafety Level Assessment", color))
    print(_dim(data.DISCLAIMER, color))
    values = {}
    for step in data.STEPS:
        values[step.key] = prompt_step(step, color)
    return Inputs(**values)


def print_result(inputs: Inputs, result, color: bool) -> None:
    sev = result.status_severity
    print()
    print(_c("SUGGESTED CONTAINMENT", "teal", color))
    print(_bold(result.bsl_label, color))
    print(_c(result.status_band, sev, color))
    print(result.summary_text)

    def section(title: str, items: list[str]) -> None:
        print()
        print(_bold(title, color))
        for item in items:
            if item.startswith("FLAG:"):
                print("  " + _c(f"- {item}", "red", color))
            else:
                print(f"  - {item}")

    section("Engineering controls & PPE", result.notes.controls)
    section("Waste handling", result.notes.waste)
    section("Training", result.notes.training)
    section("Documentation", result.notes.docs)
    print()
    print(_dim("SOURCES: " + " \u00b7 ".join(data.SOURCES), color))
    print(_dim("General reference only \u2014 confirm with your EHS/IBC.", color))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="virelion-bsa",
        description="Suggest a minimum biosafety level (BSL) and related controls "
        "for cardiac stem-cell / gene-therapy laboratory work.",
    )
    for step in data.STEPS:
        flag = "--" + step.key.replace("_", "-")
        choices = [o.value.value for o in step.options]
        help_text = ", ".join(f"{o.value.value}={o.label}" for o in step.options)
        parser.add_argument(flag, choices=choices, help=help_text, default=None)
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="Write the plain-text summary to PATH (use '-' for stdout only).",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        help="Write a machine-readable JSON summary to PATH.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in terminal output.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the human-readable report (useful with --json/--export in scripts).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    color = _supports_color(args.no_color)

    provided = {step.key: getattr(args, step.key) for step in data.STEPS}
    if all(v is not None for v in provided.values()):
        inputs = Inputs(**{k: ENUM_BY_KEY[k](v) for k, v in provided.items()})
    elif any(v is not None for v in provided.values()):
        missing = [k for k, v in provided.items() if v is None]
        print(
            f"{parser.prog}: error: either pass every field as a flag, or none "
            f"(for the interactive wizard). Missing: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    else:
        try:
            inputs = run_wizard(color)
        except (EOFError, KeyboardInterrupt):
            print()
            print("Cancelled.")
            return 130

    from .rules import assess

    result = assess(inputs)

    if not args.quiet:
        print_result(inputs, result, color)

    now = datetime.now()
    if args.export:
        text = export.text_summary(inputs, result, now)
        if args.export == "-":
            print()
            print(text)
        else:
            Path(args.export).write_text(text + "\n", encoding="utf-8")
            print()
            print(f"Summary written to {args.export}")

    if args.json:
        payload = export.json_summary(inputs, result, now)
        if args.json == "-":
            print(payload)
        else:
            Path(args.json).write_text(payload + "\n", encoding="utf-8")
            print(f"JSON summary written to {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
