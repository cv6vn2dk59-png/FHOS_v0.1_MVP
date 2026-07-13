# S08E11 — Dynamic Consilium over Hypothesis Graph

Implemented a graph-preserving consilium layer that reviews hypothesis branches, preserves minority opinions, keeps safety branches visible, aggregates missing evidence, and prevents mechanistic clusters from replacing member branches.

## Public API

`POST /clinical-reasoning/dynamic-consilium`

## Safety rules

- consensus is not a diagnosis;
- minority opinion remains visible;
- every branch must remain reviewable;
- cluster does not replace member branches;
- safety-critical branches remain unsafe to close without adequate evidence;
- warnings and limitations are not automatically violations.

## Migration

`g7c1e5f9d4b6` revises `f6b0d4e8c3a5`.
