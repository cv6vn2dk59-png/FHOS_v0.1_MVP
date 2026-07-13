# Apply S08E03

1. Back up the current backend folder and `fhos_local.db`.
2. Copy the contents of this archive into the existing `backend` directory with replacement.
3. Run:

```powershell
alembic upgrade head
python -m pytest tests/ -q
```

Expected:

- Alembic head: `d1a4e7c9b2f0`
- Tests: `287 passed`

Regression check through `POST /api/laboratory/`:

- triglycerides `2.3`, reference max `1.7`, no explicit `critical_high` -> `high`;
- the same result with explicit `critical_high: 2.0` -> `critical_high`.

The migration also normalizes historical heuristic `critical_low/high` rows to `low/high`, because those records had no verified explicit critical threshold.
