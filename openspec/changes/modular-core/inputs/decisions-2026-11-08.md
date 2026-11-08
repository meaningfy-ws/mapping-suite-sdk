# Seed: shaping Q&A with the developer (2026-11-08)

> Secondary input, preserved; the EPICs supersede it.

- Python floor: **3.10**, CI matrix 3.10–3.13 (TED-SWS on Airflow must keep working).
- #94 lands as **2.0.0, a clean break**: MongoDB params leave `load_mapping_package`; TED-SWS
  pins `<2` until it adopts the `[mongodb]` extra.
- Tooling modernisation (Ruff, dedicated root configs, drop tox, `make check-all`, CI via make)
  is **one change with #93**.
- #14 and #15: close as resolved (generate_id removed; v3 uses `mapping_suite_hash_digest`, v1/v2
  legacy field kept); delete the dead commented code. #27: parked, no EPIC.
- Reference sibling for the development style: `rdf-fingerprinter`.
