# S08E07 — Hypothesis Expansion Graph

Implemented the first domain-neutral multi-branch layer of the FHOS Cube.

## Added

- `HypothesisBranch` with supporting, contradicting, neutral and missing evidence slots;
- typed branch relationships without generic `related_to`;
- mechanistic clusters that do not replace member branches;
- `DominanceGuard` against single-branch collapse, unsupported closure and duplicate branches;
- safety flags and discriminator placeholders;
- TEST-001 cardiometabolic clustering while retaining the renal branch;
- persistence models and Alembic revision `c3e7a9b4d2f1`.

## Boundaries

- no diagnosis generation;
- no treatment recommendation;
- no global medical risk score;
- full information-gain prioritization remains for S08E08.
