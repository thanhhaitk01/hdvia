# HDVIA 1.10.9 — Data Core Integration

## Architecture

The eight warehouses remain the system of record. `DataCoreBridge` is a read-only
integration/orchestration layer; it does not create a ninth warehouse or duplicate
warehouse records.

`8 data warehouses -> Data Core Bridge -> Journey / Copilot / Agent / future modules`

A module may consume multiple warehouses, and one warehouse may serve multiple modules.

## Current integration

- Journey Intelligence: resolves detected itinerary places to destination IDs and enriches the live result with linked 8-domain context.
- AI Copilot: receives the linked Data Core context and exposes counts/availability in its response contract.
- AI Agent: receives the same context and reports which data domains are available to its inspection task.
- Existing warehouse APIs and legacy collections remain intact.
- Lineage remains attached to linked records.
- Unknown places are never guessed into a warehouse relationship.

## Data flow

1. Journey engine detects places.
2. Data Core Bridge resolves only exact normalized name/slug/alias matches.
3. Linked destination/admin/knowledge/experience/weather-risk/market/lineage records are resolved.
4. Journey result keeps all existing fields and adds `data_core` + `data_context`.
5. Copilot and Agent consume that context without owning or duplicating the data.

## Verification

Run:

```bash
python -m pytest -q
python -m compileall -q .
```

The integration is additive and backward-compatible with the existing 1.10 foundation.
