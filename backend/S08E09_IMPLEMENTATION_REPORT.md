# S08E09 — Temporal Causality & Clinical Timeline

## Scope completed

- uncertain dates represented as intervals rather than invented exact timestamps;
- conservative temporal relations between clinical events;
- causal-order checks for cause-after-effect and lag violations;
- missing temporal evidence generation;
- branch-level temporal coherence assessment;
- persistence tables for timeline events, relations, conflicts and missing temporal evidence;
- HTTP endpoint `POST /clinical-reasoning/temporal-causality`;
- Alembic revision `e5a9c3d7b2f4` after `d4f8b2c6a1e9`.

## Safety invariants

- temporal precedence does not establish causality;
- unknown timing remains unknown;
- overlapping/imprecise intervals produce missing evidence, not false conflict;
- treatment, procedure, injury and other event kinds are represented without diagnostic promotion;
- branch temporal coherence is independent from disease probability.
