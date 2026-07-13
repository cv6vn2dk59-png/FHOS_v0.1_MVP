# S08E10 — Cross-System Mechanistic Clustering

Implemented a domain-neutral clustering layer over hypothesis branches.

## Guarantees
- cluster != diagnosis;
- shared consequence != shared cause;
- shared risk factor != single mechanism;
- clusters preserve all member branches;
- independent branches remain visible;
- provenance and context constraints remain attached.

## API
`POST /clinical-reasoning/mechanistic-clustering`

## Alembic
`e5a9c3d7b2f4 -> f6b0d4e8c3a5`
