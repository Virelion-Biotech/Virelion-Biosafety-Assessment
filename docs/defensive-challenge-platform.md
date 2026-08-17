# Defensive Cardiac Challenge Platform

This package provides the computational foundation for scenario-grounded testing of human cardiac models and defensive analytics.

## Design goal

The platform represents plausible **host-response states** rather than operational biological-agent construction. A scenario can be grounded in experimental observations, literature, proxy measurements, or clearly labelled computational derivation.

The key distinction is provenance:

- **Observed** — directly measured in an authorized experiment.
- **Proxy** — measured from a safer experimental representation of a target response domain.
- **Derived** — computationally transformed from grounded states.
- **Synthetic** — generated for controlled benchmark variation.
- **Exploratory** — hypothesis-generating and not yet validated.

Every scenario records its evidence class and uncertainty so a benchmark cannot silently present a computational assumption as an established biological fact.

## Core workflow

```text
Grounded observations
        |
        v
 Scenario registry
        |
        v
 Phenotype representation
        |
        +--> controlled scenario variation
        |
        +--> novelty / OOD evaluation
        |
        +--> countermeasure recovery scoring
        |
        v
 Reproducible audit record
```

## What the first implementation provides

`models.py` defines validated phenotype vectors and scenario metadata.

`generator.py` creates deterministic phenotype-level challenge variants using a seed and bounded perturbation magnitude.

`novelty.py` provides nearest-reference distance and an interpretable novelty score for simple benchmark baselines.

`rescue.py` measures whether treatment moves each phenotype feature toward a defined baseline state.

`audit.py` creates canonical, hash-addressed records containing scenario, dataset, model, seed, inputs, and outputs.

## Validation philosophy

A computational challenge should be promoted only when its relationship to empirical data is explicit. The intended validation ladder is:

```text
observed response
    -> characterized proxy
    -> validated computational representation
    -> bounded synthetic variation
    -> held-out / novel challenge
```

The repository should preserve this distinction in machine-readable metadata and in benchmark reports.

## Recommended benchmark tracks

1. **Baseline discrimination** — normal variation versus known stress states.
2. **Atypical-state detection** — abnormal states that do not resemble a canonical disease class.
3. **Held-out challenge detection** — scenario families excluded from training.
4. **Mechanistic attribution** — infer affected phenotype domains.
5. **Recovery scoring** — quantify movement toward a healthy reference after intervention.
6. **Reproducibility** — verify that identical versions, inputs, and seeds produce identical computational outputs.

## Safety boundary

This package is deliberately limited to observable phenotype states, evidence provenance, model evaluation, and defensive analytics. It does not provide procedures, parameters, or optimization methods for constructing, modifying, or deploying biological agents.
