#!/usr/bin/env bash
set -euo pipefail

# Claude CLI runner: same workspace snapshot, prompt shape, artifact schema,
# and persistence layout as run_fresh_simulation.sh, but drives a fresh
# `claude -p` process instead of `codex exec` (for Claude-family model runs).

usage() {
  cat <<'USAGE'
Usage:
  run_fresh_simulation_claude.sh --scenario PATH --model MODEL [options]

Options:
  --model-label LABEL       Label for filenames and runner.model_id. Defaults to MODEL.
  --effort LEVEL            Claude --effort (low, medium, high, xhigh, max). Optional.
  --run-label LABEL         Semantic run label. Defaults to fresh.
  --stamp STAMP             UTC-ish timestamp. Defaults to date -u +%Y-%m-%dT%H%M%SZ.
  --history-root PATH       Defaults to ../dungeoneer-sim-history.
  --persist                 Copy run YAML and runtime trace into history-root.
  --focus TEXT              Extra focus text appended to simulator prompt.
  -h, --help                Show this help.
USAGE
}

scenario=""
model=""
model_label=""
effort=""
run_label="fresh"
stamp=""
history_root="../dungeoneer-sim-history"
persist=0
focus=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) scenario="${2:?}"; shift 2 ;;
    --model) model="${2:?}"; shift 2 ;;
    --model-label) model_label="${2:?}"; shift 2 ;;
    --effort) effort="${2:?}"; shift 2 ;;
    --run-label) run_label="${2:?}"; shift 2 ;;
    --stamp) stamp="${2:?}"; shift 2 ;;
    --history-root) history_root="${2:?}"; shift 2 ;;
    --persist) persist=1; shift ;;
    --focus) focus="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$scenario" || -z "$model" ]]; then
  usage >&2
  exit 2
fi

if [[ ! -f "$scenario" ]]; then
  echo "scenario not found: $scenario" >&2
  exit 1
fi

if [[ -z "$model_label" ]]; then
  model_label="$model"
fi

if [[ -z "$stamp" ]]; then
  stamp="$(date -u +%Y-%m-%dT%H%M%SZ)"
fi

python_bin="python3"
if ! "$python_bin" -c "import yaml" >/dev/null 2>&1 && [[ -x .venv/bin/python3 ]]; then
  python_bin=".venv/bin/python3"
fi

scenario_slug="$(basename "$scenario" .yaml)"
workspace="/tmp/dungeoneer-sim-workspaces/${stamp}_${run_label}/${scenario_slug}__${model_label}"
out_dir="/tmp/dungeoneer-sim-artifacts/${stamp}_${run_label}"
mkdir -p "$workspace" "$out_dir"

rsync -a \
  --exclude .git \
  --exclude .venv \
  --exclude .pytest_cache \
  --exclude docs/SYSTEM_SIMULATION_RUNS.md \
  ./ "$workspace"/

run_id="simrun:${stamp}:${scenario_slug}:${model_label}:fresh:${run_label}"
prompt_version="system_simulator.${run_label}.v1"
artifact="$workspace/simulation_run.yaml"
runtime_trace="$out_dir/${model_label}.runtime.jsonl"
final_message="$out_dir/${model_label}.final.txt"

prompt_file="$(mktemp)"
trap 'rm -f "$prompt_file"' EXIT

cat > "$prompt_file" <<EOF
You are a fresh Dungeoneer system simulator, not an implementation agent.

Input boundary:
- Use only files inside the current workspace.
- Do not inspect parent directories, sibling directories, ~/.claude, git history, external simulation history, or prior run outputs.
- Treat docs/SYSTEM_SIMULATION_RUNS.md as intentionally absent runner-only documentation.
- Do not edit project docs or source files.

Task:
Run the scenario in ${scenario} against the current design.
${focus}

Expected output:
1. Create a file named simulation_run.yaml in the workspace root.
2. The file must be valid YAML with schema: dwd.system_simulation_run.v1.
3. Use this run metadata:
   id: ${run_id}
   created_at: ${stamp}
   runner.model_id: ${model_label}
   runner.kind: fresh_simulator
   runner.prompt_version: ${prompt_version}
   scenario.id: sim:${scenario_slug}
   scenario.path: ${scenario}
   workspace_root: ${workspace}
4. Include trace/routed_steps for the scenario input sequence.
5. Include findings with expectation_fingerprint, route_status, cause, disposition, severity, affected_docs, summary, evidence, recommendation, and status.
6. Include prior_findings_review when rerunning known findings.
7. Include invariant_violations and open_questions.
8. In your final response, briefly summarize the result and confirm the artifact path.

Do not invent implementation beyond the docs. The goal is design pressure-testing.
EOF

claude_args=(
  -p
  --model "$model"
  --permission-mode acceptEdits
  --tools "Read,Write,Glob,Grep"
  --strict-mcp-config
  --no-session-persistence
  --output-format stream-json
  --verbose
)
if [[ -n "$effort" ]]; then
  claude_args+=(--effort "$effort")
fi

( cd "$workspace" && claude "${claude_args[@]}" < "$prompt_file" ) > "$runtime_trace" 2>&1

if [[ ! -s "$artifact" ]]; then
  echo "missing artifact: $artifact" >&2
  echo "--- runtime trace tail ---" >&2
  tail -n 40 "$runtime_trace" >&2
  exit 1
fi

"$python_bin" - <<EOF
import json
result_text = None
with open("${runtime_trace}") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj.get("type") == "result":
            result_text = obj.get("result")
if result_text is None:
    raise SystemExit("no result message found in runtime trace")
with open("${final_message}", "w") as f:
    f.write(result_text + "\n")
EOF

"$python_bin" - <<EOF
import pathlib
import yaml

path = pathlib.Path("${artifact}")
data = yaml.safe_load(path.read_text())
if not isinstance(data, dict):
    raise SystemExit("simulation artifact is not a YAML mapping")
if data.get("schema") != "dwd.system_simulation_run.v1":
    raise SystemExit("unexpected schema: %r" % (data.get("schema"),))
print("validated", path)
EOF

if [[ "$persist" -eq 1 ]]; then
  runs_dir="${history_root}/runs/${scenario_slug}"
  traces_dir="${history_root}/runtime_traces/${scenario_slug}"
  mkdir -p "$runs_dir" "$traces_dir"
  cp "$artifact" "${runs_dir}/${stamp}_${model_label}_fresh_${run_label}.yaml"
  cp "$runtime_trace" "${traces_dir}/${stamp}_${model_label}_fresh_${run_label}.jsonl"
  echo "persisted ${runs_dir}/${stamp}_${model_label}_fresh_${run_label}.yaml"
  echo "persisted ${traces_dir}/${stamp}_${model_label}_fresh_${run_label}.jsonl"
fi

echo "final message: $final_message"
