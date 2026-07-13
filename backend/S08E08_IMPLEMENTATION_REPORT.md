# S08E08 — Branch Discrimination & Information Gain

## Scope

Implemented comparison of independent hypothesis branches and ranking of missing evidence by expected ability to separate mechanisms.

## Added

- `BranchComparison` with separate support, mechanism, temporal and safety dimensions.
- `EvidenceCandidate` and branch-specific expected effects.
- `information_gain` separated from `priority_score`.
- Burden penalties for invasiveness and cost.
- Safety and time-sensitivity factors without converting them into disease probability.
- Explicit unresolved branch pairs.
- Persistence models and Alembic revision `d4f8b2c6a1e9`.
- HTTP endpoint `POST /clinical-reasoning/branch-discrimination`.

## Invariants

- Information gain is not a clinical risk score.
- Priority is not probability of diagnosis.
- High clinical utility does not imply good discrimination.
- No candidate automatically closes a branch.
- Unknown branch references are rejected from ranking and surfaced as warnings.
- Every evidence candidate requires provenance.

## Out of scope

- Automatic ordering of tests.
- Treatment recommendations.
- Diagnosis ranking.
- Cost estimation by jurisdiction.
- Probabilistic Bayesian inference.
