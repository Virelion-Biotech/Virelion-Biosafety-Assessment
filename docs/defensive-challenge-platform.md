# Defensive cardiac challenge platform

A small, dependency-free toolkit for **observable phenotype analytics**: bounded
synthetic variation, reference-distance scoring, recovery scoring, and declared
held-out-family evaluation. It is a computational baseline, not a validated
cardiac model, clinical predictor, or biosafety approval system.

The existing `virelion-bsa` containment planning aid remains separate. This package
does not supply biological-agent construction, modification, or deployment
procedures. Evidence labels are source claims, not independent verification.

## Install and run

Requires Python 3.10 or newer. From the repository root:

```bash
python -m pip install -e '.[dev]'
virelion-challenge --help
python -m challenge_platform --help
```

All commands emit strict JSON; errors go to stderr with exit code 2. No network
access is required at runtime. Examples below are deliberately synthetic and have
no experimental or clinical evidentiary value.

```bash
# Default demonstration; original flag-only invocation is also supported.
virelion-challenge generate --seed 42 --output challenge.json
virelion-challenge --seed 42 --magnitude 0.15

# Validate a scenario and normalize its representation.
virelion-challenge validate examples/challenge/baseline.json
virelion-challenge validate examples/challenge/registry.json --registry

# Record source ancestry, generation parameters, and dataset identity.
virelion-challenge generate \
  --reference examples/challenge/baseline.json \
  --scenario-id CH-002 --seed 7 --magnitude 0.1 \
  --dataset-version synthetic-fixture-v1 \
  --output challenge.json --audit generation-audit.json
virelion-challenge verify-audit generation-audit.json

# Compare a candidate with reference phenotypes.
virelion-challenge novelty examples/challenge/challenged.json \
  --references examples/challenge/registry.json --threshold 0.75

# Report recovery and new impairment separately.
virelion-challenge rescue \
  --baseline examples/challenge/baseline.json \
  --challenged examples/challenge/challenged.json \
  --treated examples/challenge/treated.json

# Evaluate a fixed threshold on declared independent families.
virelion-challenge benchmark examples/challenge/benchmark.json \
  --threshold 0.75 --dataset-version synthetic-fixture-v1 \
  --output benchmark-results.json --audit benchmark-audit.json
```

`generate`, `novelty`, `rescue`, and `benchmark` accept `--output`, `--audit`,
`--dataset-version`, `--model-version`, and `--run-id`. Audit creation requires an
explicit dataset version or digest. Use an actual version/digest for real data;
the program does not check that an identifier resolves to the claimed dataset.
The default model version identifies the installed package; use a commit-pinned
identifier when running a modified development checkout. A random event ID is
created unless supplied. The report is deterministic; event time and ID are not.
Output and audit paths must differ from each other and from input paths.

## Scenario format and provenance

Scenario JSON has `schema_version: 1`. See `examples/challenge/baseline.json` for
a complete round-trippable file. Required fields are `scenario_id`, `title`,
`basis`, `evidence_level`, and a nonempty `phenotype` object. Optional fields are
`evidence_refs`, `temporal_profile`, `uncertainty`, `held_out`, `notes`, `family_id`,
and `provenance`. Unknown fields, duplicate JSON keys, unsupported schema
versions, nonfinite numbers, and ambiguous normalized feature names are rejected.

| Evidence label | Meaning |
| --- | --- |
| `observed` | Source declares direct measurements; source references required |
| `proxy` | Source declares proxy measurements; source references required |
| `derived` | Computational transformation of an observed/proxy/derived state |
| `synthetic` | Constructed benchmark/example values |
| `exploratory` | Hypothesis-generating, not validated |

Basis values are `experimental`, `literature`, `proxy`, `computational`, or `mixed`.
A computational basis cannot claim observed/proxy evidence. Nonempty references
are required for observed/proxy labels, but their authenticity, experimental
quality, authorization, and applicability still require external review.

Derivation preserves synthetic and exploratory labels instead of upgrading them.
It records the entire parent scenario snapshot, seed, magnitude, and operation
version in `provenance`, inherits evidence references and family identity, and
uses a new scenario ID. It does **not** infer empirical grounding from a label.
`held_out` defaults to false and is only a declared split label.

Phenotype values are finite normalized numbers in [0, 1]. Feature names, units,
normalization, and biological meaning must be aligned before comparison. The
software can enforce identical feature names, but cannot verify that equally
named features from different datasets mean the same thing. Missing measurements
are rejected rather than silently converted to zero. Vectors and nested scenario
provenance are immutable snapshots.

## Algorithms and interpretation

### Generation

A seeded pseudorandom uniform offset in `[-magnitude, magnitude]` is added to each
feature and clipped to [0, 1]. Features are processed in sorted order, so input
mapping order does not change the result. Magnitude must be in [0, 1]. Pin the
implementation/package version as well as the seed for replay.

This perturbation does not model biological feasibility, causality, feature
correlation, or agent properties. Derived uncertainty is the inherited value
plus half the perturbation magnitude, clipped to 1: an **uncalibrated heuristic**,
not a probability, error bar, or confidence interval. Any temporal profile is
inherited unchanged, not simulated or recomputed.

### Novelty

Euclidean distance over identical feature sets is compared with a finite,
strictly positive threshold. The reported score is
`min(1, nearest_distance / threshold)` and novelty means distance >= threshold.
This is not a calibrated probability. Distance depends on dimension and feature
scaling; keep them fixed across comparisons. Choose/calibrate the threshold on
separate development data. The default 0.75 is illustrative, not a validated
operating point. Empty reference collections and duplicate reference IDs are
rejected. Equal-distance ties resolve by sorted reference ID.

### Recovery

For each feature with a nonzero baseline-to-challenge gap, recovery is
`(initial_gap - treated_gap) / initial_gap`, clipped to [-1, 1]. Zero means no
improvement, one means return to baseline, and negative values mean worsening.
Overshoot past baseline is evaluated by absolute distance.

Features unaffected by challenge receive JSON `null` and are excluded from the
overall average. If none are eligible, overall is `null`. New departures on
previously unaffected features are reported in `new_impairment`. **Always inspect
that field alongside overall recovery**; a recovery score of 1 does not imply a
harmless treatment. Features are equally weighted and exact zero gaps are used;
measurement noise and meaningful effect thresholds must be addressed upstream.

### Held-out benchmark

A benchmark JSON object contains `schema_version: 1`, a `references` array of
scenarios, and a `cases` array of `{"scenario": <scenario>, "abnormal": <boolean>}`.
Each scenario requires a family ID. Reference scenarios must not be marked
held-out; cases must be. Duplicate scenario IDs, reference/case family overlap,
and shared recorded ancestry are rejected. The generator inherits family IDs,
so a perturbation of a reference cannot pass as a held-out family simply by
receiving a new scenario ID.

This checks only supplied metadata. It cannot detect omitted ancestry, falsely
labelled families, exposure during external model training, or repeated subjects
hidden under different IDs. Subject grouping, empirical validation, and threshold
calibration remain the caller's responsibility. Cases from the same held-out
family may coexist; metrics are per observation and do not adjust for dependence
or provide uncertainty intervals.

Reports contain per-case results, confusion counts, accuracy, sensitivity,
specificity, precision, and the held-out abnormal detection fraction. Undefined
denominators are JSON `null`, not zero. Only boolean labels/predictions are
accepted. `held_out_rate(predictions)` is a simple fraction for an already chosen
abnormal cohort, not an OOD discrimination metric or split validator.

## Audit guarantees and limits

Audit schema version 1 has two hashes:

- `content_hash`: SHA-256 over canonical computational content, including schema,
  scenario ID, dataset/model versions, seed, inputs, and outputs. It excludes event
  time, run ID, and hash fields, enabling comparison across reruns.
- `record_hash`: SHA-256 over the entire event (including `content_hash`, run ID,
  and timestamp), excluding only `record_hash` itself.

Canonical JSON sorts keys and uses compact separators. Inputs must be JSON-compatible:
objects with string keys, arrays, strings, booleans, null, integers, and finite
floats. Unsupported objects are rejected rather than coerced to strings. Nested
inputs and outputs are copied into immutable snapshots before hashing. Array
order remains significant; numeric types are not collapsed, so 1 and 1.0 may
have different canonical representations. Versioned normalized scenarios avoid
incidental input-format differences.

`verify-audit` recomputes both hashes and rejects altered content. These hashes
are **not digital signatures or identity/authenticity proofs**: someone who can
rewrite a record can also recompute its hashes. Preserve a trusted digest or use
an external signed storage/attestation system when authenticity is required.
The CLI stores full input snapshots in audit records; choose an appropriate
storage location for any sensitive data. Nothing is uploaded automatically.

## Library usage

```python
from challenge_platform import (
    ChallengeScenario, audit_from_dict, derive_challenge, score_rescue,
)
from challenge_platform.serialization import load_json

with open("examples/challenge/baseline.json") as source:
    baseline = ChallengeScenario.from_dict(load_json(source.read()))
child = derive_challenge(baseline, scenario_id="child", seed=7, magnitude=0.1)
assert child.family_id == baseline.family_id
```

Use `ScenarioRegistry.to_dict()/from_dict()` for deterministic persistence.
Use `ChallengeScenario.to_dict()` and `AuditRecord.to_dict()` rather than
`dataclasses.asdict()` on immutable mapping-backed objects.

## Migration from the initial draft

- `held_out_rate` takes only `held_out_predictions`; the unused known-predictions
  argument has been removed.
- Derived scenarios default to `held_out=False`; request the label explicitly.
- Empty phenotypes, mismatched feature schemas, invalid thresholds, and empty
  novelty reference sets now raise `ValueError`.
- Observed/proxy metadata requires evidence references.
- Recovery and undefined detection metrics can return `None`/JSON `null`.
- Audit records add schema and content hashes. Old timestamp-only draft records
  are not silently upgraded or accepted as version-1 verified records.
- CLI generation output is now a complete versioned scenario with ancestry.

## Validation and next scientific steps

The automated suite covers review regressions, immutable snapshots, JSON/schema
validation, split leakage, deterministic results, audit tampering, CLI error
behavior, and installed console entry points. CI tests the built wheel on Python
3.10, 3.11, and 3.12, including the existing BSL assessment tests.

Before scientific claims: define and version phenotype normalization; attach
verified empirical sources; group by donor/subject and scenario family; calibrate
thresholds using development data only; evaluate independent datasets; quantify
uncertainty and robustness to measurement noise. Passing software tests does not
complete those empirical validation steps.
