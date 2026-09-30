"""File-based phenotype generation, evaluation, and audit verification."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
import sys
from uuid import uuid4

from .audit import audit_from_dict, audit_json, build_audit_record
from .evaluation import evaluate_benchmark
from .generator import derive_challenge
from .models import ChallengeScenario, EvidenceLevel, PhenotypeVector, ScenarioBasis
from .novelty import novelty_score
from .registry import ScenarioRegistry
from .rescue import score_rescue
from .serialization import load_json, pretty_json


def _report_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", type=Path, help="Save JSON instead of printing it")
    parser.add_argument("--audit", type=Path, help="Also save a verifiable audit event")
    parser.add_argument("--dataset-version", default="unversioned", help="Source dataset version or digest")
    parser.add_argument("--model-version", default=f"challenge-platform/{version('virelion-biosafety-assessment')}")
    parser.add_argument("--run-id", help="Audit event ID (default: random UUID)")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="virelion-challenge",
        description="Phenotype analytics; no empirical validation or biosafety approval is implied.")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate", help="Derive a scenario from JSON or a synthetic demo")
    generate.add_argument("--reference", type=Path, help="Versioned scenario JSON; omitted uses a synthetic demo")
    generate.add_argument("--scenario-id", default="CH-001")
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--magnitude", type=float, default=0.15)
    generate.add_argument("--held-out", action="store_true", help="Declare a split label; does not prove independence")
    _report_options(generate)
    validate = sub.add_parser("validate", help="Validate and normalize a scenario or registry JSON")
    validate.add_argument("file", type=Path)
    validate.add_argument("--registry", action="store_true")
    validate.add_argument("--output", type=Path)
    novelty = sub.add_parser("novelty", help="Compare a scenario with a registry of references")
    novelty.add_argument("candidate", type=Path)
    novelty.add_argument("--references", type=Path, required=True)
    novelty.add_argument("--threshold", type=float, default=0.75)
    _report_options(novelty)
    rescue = sub.add_parser("rescue", help="Evaluate recovery and newly induced impairment")
    for field in ("baseline", "challenged", "treated"):
        rescue.add_argument(f"--{field}", type=Path, required=True)
    _report_options(rescue)
    benchmark = sub.add_parser("benchmark", help="Evaluate a declared held-out family cohort")
    benchmark.add_argument("file", type=Path)
    benchmark.add_argument("--threshold", type=float, default=0.75)
    _report_options(benchmark)
    verify = sub.add_parser("verify-audit", help="Verify event and content hashes")
    verify.add_argument("file", type=Path)
    return parser


def _read(path: Path) -> object:
    return load_json(path.read_text(encoding="utf-8"))


def _scenario(path: Path) -> ChallengeScenario:
    return ChallengeScenario.from_dict(_read(path))


def _demo() -> ChallengeScenario:
    return ChallengeScenario(
        scenario_id="DEMO-REFERENCE", title="Illustrative synthetic cardiac phenotype",
        basis=ScenarioBasis.COMPUTATIONAL, evidence_level=EvidenceLevel.SYNTHETIC,
        phenotype=PhenotypeVector({"inflammation": 0.15, "vascular_dysfunction": 0.10,
                                  "contractile_impairment": 0.05, "mitochondrial_stress": 0.10}),
        family_id="synthetic-demo", uncertainty=1.0,
        notes="Arbitrary demonstration values, not experimental observations or a clinical reference.",
    )


def _write(path: Path | None, value: object) -> None:
    text = pretty_json(value) + "\n"
    if path is None:
        print(text, end="")
    else:
        path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Preserve the original no-subcommand generation invocation.
    if not argv or (argv[0].startswith("-") and argv[0] not in ("-h", "--help")):
        argv.insert(0, "generate")
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        output_path, audit_path = getattr(args, "output", None), getattr(args, "audit", None)
        source_paths = [value.resolve() for key, value in vars(args).items()
                        if isinstance(value, Path) and key not in {"output", "audit"}]
        targets = [path.resolve() for path in (output_path, audit_path) if path is not None]
        if len(set(targets)) != len(targets) or any(path in source_paths for path in targets):
            raise ValueError("output/audit paths must be distinct and must not overwrite input files")
        if args.command == "verify-audit":
            record = audit_from_dict(_read(args.file))
            _write(None, {"valid": True, "content_hash": record.content_hash,
                          "record_hash": record.record_hash})
            return 0
        if args.command == "validate":
            value = (ScenarioRegistry.from_dict(_read(args.file)).to_dict() if args.registry
                     else _scenario(args.file).to_dict())
            _write(output_path, value)
            return 0
        if args.command == "generate":
            reference = _scenario(args.reference) if args.reference else _demo()
            scenario = derive_challenge(reference, scenario_id=args.scenario_id,
                seed=args.seed, magnitude=args.magnitude, held_out=args.held_out)
            result = scenario.to_dict()
            inputs = {"reference": reference.to_dict(), "magnitude": args.magnitude,
                      "scenario_id": args.scenario_id, "held_out": args.held_out}
            scenario_id, seed = scenario.scenario_id, args.seed
        elif args.command == "novelty":
            candidate = _scenario(args.candidate)
            registry = ScenarioRegistry.from_dict(_read(args.references))
            result = {"schema_version": 1, "threshold": args.threshold, **asdict(novelty_score(
                candidate.phenotype, [(item.scenario_id, item.phenotype) for item in registry.list()],
                threshold=args.threshold))}
            inputs = {"candidate": candidate.to_dict(), "references": registry.to_dict(),
                      "threshold": args.threshold}
            scenario_id, seed = candidate.scenario_id, 0
        elif args.command == "rescue":
            states = [_scenario(getattr(args, field)) for field in ("baseline", "challenged", "treated")]
            result = {"schema_version": 1, **asdict(score_rescue(*(state.phenotype for state in states)))}
            inputs = {field: state.to_dict() for field, state in zip(("baseline", "challenged", "treated"), states)}
            scenario_id, seed = states[2].scenario_id, 0
        else:
            source = _read(args.file)
            result = evaluate_benchmark(source, threshold=args.threshold)
            inputs = {"benchmark": source, "threshold": args.threshold}
            scenario_id, seed = "held-out-benchmark", 0
        if audit_path:
            if args.dataset_version == "unversioned":
                raise ValueError("--audit requires an explicit --dataset-version (or source digest)")
            record = build_audit_record(run_id=args.run_id or str(uuid4()),
                scenario_id=scenario_id, dataset_version=args.dataset_version,
                model_version=args.model_version, seed=seed,
                inputs={"command": args.command, **inputs}, outputs=result)
            audit_path.write_text(audit_json(record) + "\n", encoding="utf-8")
        _write(output_path, result)
        return 0
    except (ValueError, TypeError, OSError, RecursionError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
