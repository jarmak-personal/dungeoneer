---
name: simulate
description: Run Dungeoneer system simulation scenarios with fresh low-context agents, clean workspace snapshots, structured YAML artifacts, runtime traces, and optional persistence to ../dungeoneer-sim-history. Use when asked to run, rerun, compare, audit, or save Dungeoneer simulation runs, especially fresh simulator runs for scenario YAML files under docs/simulations/scenarios.
---

# Simulate

Use this skill to run Dungeoneer design simulations without contaminating the
simulator with prior history. The simulator reads a disposable current-file
snapshot, routes a scenario through the current docs/contracts, and returns a
structured run artifact.

## Core Rules

- Use current workspace files as the input snapshot, including uncommitted design
  edits when the user is validating current work.
- Exclude `.git`, `.venv`, `.pytest_cache`, prior simulation outputs, and
  `docs/SYSTEM_SIMULATION_RUNS.md` from simulator workspaces.
- Do not let the simulator inspect parent directories, sibling directories,
  `~/.codex`, git history, `../dungeoneer-sim-history`, or prior run outputs.
- Save raw run artifacts append-only. Do not rewrite aggregate finding files
  unless the user asks for triage or the runs clearly justify it.
- Treat `dwdlint` as static DWD authoring lint. Event/replay verification is a
  separate simulation/runtime concern.

## Quick Run

Prefer the bundled runners for repeatable runs. There are two, one per CLI:

- `run_fresh_simulation.sh` drives `codex exec` for GPT-family models.
- `run_fresh_simulation_claude.sh` drives `claude -p` for Claude-family models.

Both take the same `--scenario`/`--model-label`/`--run-label`/`--persist`/
`--focus` flags and produce artifacts with the same layout and schema.

```bash
.agents/skills/simulate/scripts/run_fresh_simulation.sh \
  --scenario docs/simulations/scenarios/combat_round.yaml \
  --model gpt-5.4-mini \
  --model-label gpt-5.4-mini \
  --run-label rules_event_validation \
  --persist
```

For a medium-effort 5.5 comparison:

```bash
.agents/skills/simulate/scripts/run_fresh_simulation.sh \
  --scenario docs/simulations/scenarios/combat_round.yaml \
  --model gpt-5.5 \
  --model-label gpt-5.5-medium \
  --reasoning medium \
  --run-label rules_event_validation \
  --persist
```

For a Claude Sonnet 5 run, use the Claude runner (it uses `--effort` instead
of `--reasoning`, and is optional):

```bash
.agents/skills/simulate/scripts/run_fresh_simulation_claude.sh \
  --scenario docs/simulations/scenarios/combat_round.yaml \
  --model claude-sonnet-5 \
  --model-label sonnet-5 \
  --run-label rules_event_validation \
  --persist
```

The Claude runner shells out to `claude -p` with `--tools "Read,Write,Glob,Grep"`
(no `Bash`/`Task`/MCP tools), `--permission-mode acceptEdits`,
`--strict-mcp-config`, and `--no-session-persistence` — the closest available
analog to codex's `-a never -s workspace-write --ephemeral` sandboxing. It cds
into the isolated workspace before invoking `claude` so default directory
access stays scoped there. Both runners fall back to `.venv/bin/python3` for
the YAML-validation step if the system `python3` lacks `pyyaml`.

Both scripts write:

- workspace artifact: `/tmp/dungeoneer-sim-workspaces/<stamp>_<label>/<scenario>__<model-label>/simulation_run.yaml`
- local runtime trace: `/tmp/dungeoneer-sim-artifacts/<stamp>_<label>/<model-label>.runtime.jsonl`
- local final message: `/tmp/dungeoneer-sim-artifacts/<stamp>_<label>/<model-label>.final.txt`
- persisted run: `../dungeoneer-sim-history/runs/<scenario>/<stamp>_<model-label>_fresh_<label>.yaml`
- persisted trace: `../dungeoneer-sim-history/runtime_traces/<scenario>/<stamp>_<model-label>_fresh_<label>.jsonl`

If the sandbox blocks Codex CLI / Claude CLI or writing to `.agents` /
`../dungeoneer-sim-history`, request escalation. Do not work around the
clean-run boundary.

## Prompt Shape

Ask the simulator to:

1. Use only files inside the temporary workspace.
2. Treat `docs/SYSTEM_SIMULATION_RUNS.md` as intentionally absent.
3. Run one scenario from `docs/simulations/scenarios/`.
4. Produce `simulation_run.yaml` with `schema: dwd.system_simulation_run.v1`.
5. Include run metadata, routed steps, findings, `prior_findings_review` when
   applicable, `invariant_violations`, and `open_questions`.
6. Avoid implementation inventions; pressure-test the design as documented.

For details on artifact fields and persistence naming, read
`references/artifacts.md`.

## Model Labels

- Use `--model gpt-5.4-mini --model-label gpt-5.4-mini` for 5.4-mini.
- Use `--model gpt-5.5 --model-label gpt-5.5-medium --reasoning medium` for
  5.5-medium.
- Use `--model claude-sonnet-5 --model-label sonnet-5` (via the Claude runner)
  for Claude Sonnet 5.
- Use the `model-label` in filenames and `runner.model_id` when it conveys the
  actual run configuration better than the API model slug.

## After A Run

- Validate the copied YAML parses.
- Summarize the model-level conclusions and disagreements.
- Mention whether aggregate findings were left unchanged or updated.
- Keep uncommitted repo docs uncommitted unless the user explicitly asks to commit.
