# S08E14 — Biomechanical Load, Adaptation & Overload

Implemented a domain-independent load/capacity/recovery layer for the biomechanical vertical slice.

## Guarantees
- high load is not treated as injury;
- pain after load is not treated as tissue damage;
- reduced capacity is not structural pathology;
- acute spikes and chronic/repetitive exposure remain distinct;
- occupational and training exposure preserve their source context;
- recovery deficit may amplify a branch but never proves causality;
- missing load or recovery data remains missing evidence.

## API
`POST /clinical-reasoning/biomechanics/load-adaptation`

## Migration
`j0f4h8c2g7e9`, down revision `i9e3g7b1f6d8`.
