# Virelion-Biosafety-Assessment

**Biosafety Level Assessment Tool** for cardiac stem-cell and gene-therapy laboratory work.

A single-page planning aid that suggests a minimum biosafety level (BSL) and related controls, waste, training, and documentation notes from public CDC/NIH and WHO guidance. Built for Virelion’s iPSC / ESC-derived cardiomyocyte / primary-cell and viral-vector workflows.

> **Not a substitute for formal review.** Final BSL determination is an institutional decision. This tool does not replace protocol registration or sign-off by an Institutional Biosafety Committee (IBC) or Biosafety Officer.

## Features

- Six-step form: cell type → genetic modification → viral vector → scale → intended use → additional risk factors
- Suggested containment placard (BSL-2, enhanced BSL-2+, or BSL-3 / BSL-4 path when escalators apply)
- Engineering controls & PPE, waste handling, training, and documentation lists
- Flagged items when inputs require dedicated IBC review
- Export summary (`.txt`) and Print / PDF

## Live web app

Open `index.html` in a browser, or use the hosted copy linked from the [Virelion Biotech tools page](https://github.com/Virelion-Biotech).

## Cell types covered

| Option | Notes |
|--------|--------|
| iPSC | Induced pluripotent stem cell line |
| ESC-derived CM | Embryonic stem cell–derived cardiomyocyte |
| Primary cells | Directly isolated human/animal tissue |
| NHP primary cells | Non-human primate tissue / cells (escalates review) |
| Known BBP-positive | Material known/suspected to contain bloodborne pathogens |

## Vectors covered

- None
- AAV (adeno-associated virus)
- Lentivirus (typically 2nd/3rd-gen, SIN) → enhanced BSL-2
- Lentivirus — high-titer production → enhanced; may path to BSL-3 at production scale
- Retrovirus (gammaretroviral)
- Adenovirus (E1-deleted, replication-defective)
- RCV / unknown competence → BSL-3 path + IBC flag
- Other / unsure → IBC review flag

## Higher-risk escalators

- Oncogenic / transforming insert
- In vivo animal work
- Aerosol generation outside BSC
- High sharps / injection risk
- RG3 / high-consequence agent → BSL-3 path
- RG4 / maximum containment → BSL-4 path (regulatory + BSL-4 facility required)
- Combinations that force BSL-3 include high-titer at production scale, RCV + aerosol/in vivo, BBP-positive + integrating vector, and related pairs.

## Sources (public guidance)

- CDC/NIH *Biosafety in Microbiological and Biomedical Laboratories* (BMBL), 6th ed.
- NIH *Guidelines for Research Involving Recombinant or Synthetic Nucleic Acid Molecules*
- WHO *Laboratory Biosafety Manual*, 4th ed.

## Usage

```bash
python -m http.server 8080
# visit http://localhost:8080
```

Or open `index.html` directly.

## License

MIT — see [LICENSE](LICENSE).
