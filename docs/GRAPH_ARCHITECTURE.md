# Knowledge graph architecture

## Who gets cited

- **LBO (state law)** is the only citable source (e.g. “§ 6 BbgBO”, “Art. 31 BayBO”). The product must never cite MBO as legal authority.
- **MBO** is used only as an internal structure: shared topic map and source of relationship types. We copy MBO-style edges onto state graphs via section mapping; the user always sees the LBO.

## Central nodes

- **MBO:** `MBO_ROOT` — root for the Musterbauordnung (model code).
- **Per state:** `{State}_ROOT` (e.g. `BbgBO_ROOT`, `BayBO_ROOT`) — root for that state’s LBO. All section anchors for that law link to this node via `supplements`.

## Adding a state

See **[ADDING_A_NEW_STATE.md](ADDING_A_NEW_STATE.md)** for the step-by-step (inventory → refine granularity → mapping → register → build).
