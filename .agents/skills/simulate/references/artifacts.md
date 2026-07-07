# Dungeoneer Simulation Artifacts

## Run Artifact

Each run writes `simulation_run.yaml` with:

```yaml
schema: dwd.system_simulation_run.v1
id: simrun:<stamp>:<scenario_slug>:<model_label>:fresh:<run_label>
created_at: <stamp>
runner:
  model_id: <model_label>
  kind: fresh_simulator
  prompt_version: system_simulator.<run_label>.v1
scenario:
  id: sim:<scenario_slug>
  path: docs/simulations/scenarios/<scenario_slug>.yaml
workspace_root: /tmp/dungeoneer-sim-workspaces/<stamp>_<run_label>/<scenario_slug>__<model_label>
trace: []
routed_steps: []
findings: []
prior_findings_review: []
invariant_violations: []
open_questions: []
```

Accept variant structures from simulator models if they are valid YAML and carry
the same searchable fields.

## Finding Fields

Prefer findings with:

```yaml
expectation_fingerprint: combat_event_payload_schemas
route_status: resolved_by_design
cause: design_gap
disposition: resolved
severity: info
affected_docs: [docs/RULES_ENGINE.md]
summary: >
  Short present-tense assessment.
evidence:
  - "Specific doc-backed observation."
recommendation: "Concrete next action."
status: closed
```

Common dispositions: `resolved`, `partially_resolved`, `open_gap`, `closed`,
`adopt`, `fortify`, `ignore`.

## Persistence Layout

Persist raw outputs append-only:

```text
../dungeoneer-sim-history/
  runs/<scenario_slug>/<stamp>_<model_label>_fresh_<run_label>.yaml
  runtime_traces/<scenario_slug>/<stamp>_<model_label>_fresh_<run_label>.jsonl
```

Do not update `../dungeoneer-sim-history/findings/*.yaml` during a normal rerun
unless the user explicitly asks for aggregate triage. If aggregate files are
updated, preserve present-tense status and avoid historical commentary in the
project docs.

## Clean Workspace Rules

The temporary workspace must exclude:

- `.git`
- `.venv`
- `.pytest_cache`
- `docs/SYSTEM_SIMULATION_RUNS.md`
- any prior simulation runs or external history directories

The simulator prompt must forbid parent/sibling directory inspection and prior
history reads.
