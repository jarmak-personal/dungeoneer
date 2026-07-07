# System Simulation Runs

## Purpose

Dungeoneer is complex enough that we need to feel the system before all code
exists. A system simulation run is a text-based RPG of the architecture itself:
create a situation, route it through the current contracts/docs/code, record what
would happen, and inspect where the design feels awkward, slow, leaky, or vague.

This is not playtesting the game fiction. It is playtesting the system design.

The useful question is:

> Given only the current code/docs/contracts, what would the system actually do?

Not:

> What do we wish the architecture would do?

What this really tests is **doc-executability**: whether a fresh, competent
reasoner can route a scenario correctly from the documents alone — which is also
what future implementation agents must do. That makes a failed run ambiguous in a
useful way. It has three possible causes, and findings must say which:

- **design gap** — the route genuinely is not defined.
- **doc ambiguity** — the design is sound but underspecified, so a fresh reader
  cannot route it.
- **simulator error** — the model misread or confabulated.

Disambiguating these is the maintainer's first job on any finding. Not every flag
is a design change.

## Core Idea

Each simulation is a structured trace:

```text
scenario input
  -> event ingestion
  -> visibility/delivery classification
  -> context assembly
  -> capsule/loremaster/NPC activation
  -> tool routing
  -> rules/world-state proposal
  -> validation/review
  -> output/delivery
  -> persisted events/projections
  -> observed design problems
```

At first, this is done from docs and planned contracts. Later, the same format
can be generated from instrumented code.

## Why Use A Fresh Sub-Agent

The main maintainer knows how the system is *supposed* to work. That is dangerous
for design simulation, because missing interfaces get mentally filled in.

The simulator should be a fresh sub-agent running from a clean disposable
workspace:

- It sees a broad repo snapshot with runner-only simulation docs removed.
- It is instructed not to invent missing machinery.
- It must mark gaps, ambiguities, and "I do not know how this routes" points.

This makes it closer to a new contributor, a future maintainer, or the actual code
path: it can only use what exists.

## Simulation Roles

### Scenario Author

Creates the situation and chooses which system areas are under test.

Example:

```yaml
id: sim:private_whisper_and_debt
focus: [message_visibility, npc_knowledge, relationship_update, capsule_activation]
setup:
  scene: loc:greyhaven.crooked_lantern
  present: [pc:iona, pc:kael, npc:marra_vell]
  hidden_context:
    - secret:ash_ledger_blackmail
input:
  player: pc:iona
  channel: player_remote_private
  text: "I quietly tell Marra I'll hide her from the Ledger if she helps us."
```

### Fresh Simulator

Routes the scenario through the current design.

Rules:

- Use only provided docs/contracts/code.
- Produce a step-by-step trace.
- Name the service, tool, event, or schema used at each step.
- If a route is not defined, stop and mark the gap.
- Do not silently fix the design.

### Critic

Checks the trace against invariants:

- Did private content leak?
- Did a model mutate canon directly?
- Did NPC knowledge stay perspective-limited?
- Did OOC content stay non-canonical?
- Did rules-owned state stay rules-owned?
- Were proposed changes reviewable?
- Was latency-sensitive work kept off the live path?
- Did capsule fork/resume behavior match the capsule type?

### Maintainer

First triages each finding by cause — design gap, doc ambiguity, or simulator
error — because not every flag is a design change. Then turns the real ones into
concrete work:

- Contract change.
- Schema field.
- Validator.
- Tool boundary.
- Roadmap item.
- Documentation fix.
- Implementation task.

## Simulation Output Format

Every run should produce a durable, searchable artifact. Treat simulation history
like eval history: append-only records with stable IDs, traceable findings, and
enough metadata to compare expectations across time and across models.

```yaml
schema: dwd.system_simulation.v1
id: simrun:private_whisper_and_debt.001
scenario: sim:private_whisper_and_debt
created_at: "2026-06-21T14:00:00-04:00"
docs_snapshot:
  label: local-docs-2026-06-20
  files:
    - path: docs/SCOPE.md
      content_hash: sha256:...
    - path: docs/GAME_WORLD_SCHEMA.md
      content_hash: sha256:...
runner:
  kind: fresh_simulator
  model_id: gpt-5.5
  prompt_version: system_simulator.v1
status: completed_with_gaps
focus: [message_visibility, npc_knowledge, relationship_update, capsule_activation]
tags: [private_message, npc_knowledge, visibility]

trace:
  - id: trace:001
    step: ingest_input
    component: api_gateway
    stored_as: messages_table_row    # inbound utterances are message rows, not events
    route_status: routed
    notes: "Private player remote message from pc:iona, captured as a message row."

  - id: trace:002
    step: classify_visibility
    component: message_visibility
    expected_visibility: player_private
    route_status: routed
    notes: "Visible to pc:iona, DM orchestrator, audit. Not table-visible."

  - id: trace:003
    step: npc_knowledge_update
    component: unknown
    route_status: blocked_by_gap
    gap: "Docs say private messages do not become NPC knowledge unless revealed, but this message is addressed to Marra through the DM. Need explicit event type for private PC-to-NPC communication."

findings:
  - id: finding:private_pc_to_npc_delivery
    severity: high
    type: missing_contract
    cause: design_gap        # design_gap | doc_ambiguity | simulator_error
    disposition: adopt       # adopt | fortify | ignore
    recurrence: 3            # times this expectation surfaced across runs/models
    expectation_fingerprint: private_pc_to_npc_delivery_contract
    trace_refs: [trace:003]
    affected_docs:
      - docs/FRONTEND.md
      - docs/GAME_WORLD_SCHEMA.md
      - docs/NPC_AGENTS.md
    summary: "Private PC-to-NPC messages need a delivery/knowledge transition."
    suggested_fix: "Add message.delivered_to_npc and knowledge.learned event semantics."
    status: open             # open | accepted | rejected | superseded | resolved
    owner: unassigned

open_questions:
  - id: question:private_remote_targets
    question: "Can a player privately address an NPC through the DM remote, or only the DM?"
    status: open
```

Route status values:

```text
routed
routed_with_inference
blocked_by_gap
blocked_by_invariant
expected_missing_from_taxonomy
contradicts_docs
not_tested
```

Finding status values:

```text
open
accepted
rejected
superseded
resolved
```

Use `disposition` rather than prose when triaging a finding:

- `adopt`: implement or document the expected affordance.
- `fortify`: the expectation violates an invariant; strengthen the boundary.
- `ignore`: one-off model noise or simulator mistake.

Use `expectation_fingerprint` to group the same expectation across runs even when
wording differs. The fingerprint should be stable, short, and semantic:

```text
private_pc_to_npc_delivery_contract
message_received_event_taxonomy
relationship_write_tool_contract
observable_whisper_shell_event
```

The fingerprint is what makes recurrence searchable.

## Simulation History Model

Store simulation history as append-only records, not overwritten notes. Keep
simulation outputs outside the repo/docs tree by default, because fresh simulator
agents may read project files and prior run outputs would bias later runs.

Git history is not simulation history. The repository can use git for durability
and review, but fresh simulators must see a current-file snapshot, not commit
logs, diffs, branches, old revisions, stash entries, or `.git` metadata. A runner
may record the commit hash it snapshotted in run metadata for reproducibility, but
that identifier is runner metadata, not input context for the simulator.

Early input layout in the repo:

```text
docs/simulations/
  scenarios/
    private_whisper_and_debt.yaml
    loremaster_fork.yaml
```

Early output layout outside the repo:

```text
../dungeoneer-sim-history/
  runs/
    private_whisper_and_debt/
      2026-06-21T140000Z_gpt-5.5.yaml
      2026-06-21T141500Z_gpt-5.4.yaml
  findings/
    private_pc_to_npc_delivery_contract.yaml
    relationship_write_tool_contract.yaml
```

Later database tables:

```text
simulation_scenarios
simulation_runs
simulation_trace_steps
simulation_findings
simulation_open_questions
simulation_finding_links
```

Minimum searchable fields:

- `scenario`
- `focus`
- `tags`
- `runner.kind`
- `runner.model_id`
- `runner.prompt_version`
- `docs_snapshot.files.path`
- `trace.component`
- `trace.route_status`
- `findings.id`
- `findings.type`
- `findings.cause`
- `findings.disposition`
- `findings.status`
- `findings.expectation_fingerprint`
- `findings.affected_docs`
- `open_questions.status`

Queries we should be able to answer:

```bash
dungeoneer simulate findings --status open
dungeoneer simulate findings --disposition fortify
dungeoneer simulate findings --fingerprint private_pc_to_npc_delivery_contract
dungeoneer simulate findings --affected-doc docs/GAME_WORLD_SCHEMA.md
dungeoneer simulate recurrence --min 3
dungeoneer simulate trace simrun:private_whisper_and_debt.001
```

The CLI should default to the external history root and require an explicit
override to read run outputs from inside the repo.

## Agent Input Isolation

For eval-grade runs, give simulators a disposable broad copy of the project, not
the working repo. The point is to make the copy look like the first simulation
run from the agent's perspective while letting the agent browse naturally.

`docs/SYSTEM_SIMULATION_RUNS.md` is runner-only process documentation. The
top-level runner may use it to decide where to save outputs and how to launch
sweeps, but it must not be copied into simulator workspaces.

Path secrecy is not a boundary: if the agent has normal filesystem access,
assume it can discover sibling directories, history roots, and prior outputs. Do
not rely on hiding `../dungeoneer-sim-history`; run the agent from a workspace
where that history does not exist.

The clean-run standard:

- top-level runner creates a temporary broad repo copy
- copy is a clean file snapshot or archive, not a clone with `.git`
- copy excludes simulation output/history directories
- copy excludes runner-only simulation docs
- copy excludes git metadata and any generated git-derived context
- agent `cwd` is the temporary copy
- agent prompt says where to write or return the run artifact
- top-level runner extracts the result into the external history store
- temporary copy is deleted after extraction
- runtime read/tool traces are archived when available

The copied workspace must exclude:

- prior simulation runs
- prior finding summaries
- sweep reports
- external history roots such as `../dungeoneer-sim-history`
- `.git` and any exported git logs, diffs, patches, or commit summaries
- `docs/SYSTEM_SIMULATION_RUNS.md`

Each run should record an `input_manifest`/`docs_snapshot` with paths and hashes.
That manifest is useful evidence, but not a security audit by itself. If the
agent runtime exposes tool-call or file-read traces, archive those traces with
the run metadata.

When a finding changes the design, link it forward:

```yaml
resolution:
  status: resolved
  resolved_by:
    - docs/GAME_WORLD_SCHEMA.md
    - docs/FRONTEND.md
  resolution_summary: "Added private PC-to-NPC delivery and observable whisper shell semantics."
  accepted_trace: simrun:private_whisper_and_debt.004
```

## Findings: Hallucination As Signal

A confidently expected route that does not exist is not only a gap — it is the
simulator predicting the design from its priors. Because agent-facing surfaces are
designed for predictability (see
[Design for Agent Predictability](DECISIONS.md)), a fresh reasoner's confident
expectation is a vote for the shape the design should take. Read each such finding
three ways:

- **Adopt** — a predictable affordance the design lacks. The expected
  API/route/field is where a competent model reaches for it; build it that way
  unless requirements or invariants say otherwise. Hallucination proposes; design
  disposes.
- **Fortify** — a predictable expectation that violates an invariant (e.g.
  reaching to mutate canonical state directly). This predicts exactly where future
  implementation agents will try to cheat. Reinforce the typed boundary there and
  make the guardrail loud.
- **Ignore** — idiosyncratic one-off confabulation with no convergence behind it.

**Convergence is the discriminator — for the ambiguous findings.** A single
surfaced expectation is interesting; the same one recurring across runs and across
models is pressure. But convergence is the path specifically for findings you
*cannot tell are real by inspection* — a hallucinated affordance that might be
signal or might be noise. A finding the maintainer can independently verify as a
genuine gap (a contract that is plainly missing, an event type plainly absent) can
be triaged at a single occurrence; it does not need to recur to be believed.

So findings fork two ways:

- **Verifiable now** — a human can confirm the gap by looking. Triage immediately
  at recurrence 1; convergence is not required.
- **Ambiguous** — can't tell signal from noise by inspection. Hold the disposition
  as provisional and let recurrence decide. These are the findings that *must* be
  run repeatedly and, importantly, across **different model families** — different
  priors agreeing is the real pressure signal. Re-running one model collapses that
  dimension and tells you little.

Two process rules follow:

- An aggregated finding's `disposition` is the maintainer's triaged decision, not
  auto-copied from the first run that surfaced it. For ambiguous findings it stays
  provisional until convergence.
- Track recurrence per `expectation_fingerprint` across runs and models. For
  verifiable findings recurrence is informational; for ambiguous ones it is the
  deciding signal.

## First Simulation Suite

Start with scenarios that force boundary decisions.

### 1. Private Whisper To NPC

Tests:

- Player-private input.
- NPC knowledge transition.
- Message delivery.
- Relationship update.
- Memento proposal.

Expected value: flushes out private-message semantics.

### 2. Chaotic Table Turn With OOC Tangent

Tests:

- OOC detection.
- Canonical versus non-canonical transcript.
- Re-engagement cue.
- Voice ambiguity.

Expected value: prevents OOC from contaminating memory.

### 3. NPC Returns After Ten Sessions

Tests:

- Identity capsule resume.
- Mementos.
- Relevant history retrieval.
- Perspective-limited knowledge.

Expected value: catches "full history exists but wrong slice loaded" failures.

### 4. Loremaster Fork

Tests:

- Expert capsule fork.
- Source citation.
- Canon versus rumor.
- Patch proposal.

Expected value: proves loremasters are fast experts, not omniscient mutators.

### 5. Map Perception With Incidental Room Image

Tests:

- Source crop requirement.
- Restricted-host payload rejection.
- Manual fallback.
- Audit event.

Expected value: exercises privacy boundary.

### 6. Combat Action With Rule-Of-Cool Profile

Tests:

- Rules engine authority.
- Bounded `narrative_adjustment`.
- Gated `narrative_override`.
- State mutation provenance.
- DM profile enforcement.

Expected value: verifies profile knobs are enforced, not prompted.

### 7. Dreaming Advances A Faction Clock

Tests:

- Session replay.
- Clock advancement.
- Reviewable patch.
- Next-session prep.
- Loremaster capsule refresh.

Expected value: catches silent world mutation.

### 8. Restricted-Host Media Request

Tests:

- Sanitized brief generation.
- Secret stripping.
- Provenance split.
- Generated asset delivery.

Expected value: validates "eyes and art" host boundary.

### 9. Game Start (Cold Boot)

Tests:

- Campaign creation and world-pack import.
- Bootstrap ordering and lifecycle events (campaign/session/scene start).
- Session zero seeding dm_profile and enforceable safety guardrails.
- PC onboarding, device pairing, and player identity.
- Cold capsule creation from seed, before any dreaming has run.
- First-scene assembly with empty history and opening narration to the table.

Expected value: exercises bootstrapping paths nothing else touches — lifecycle
events, capsule creation pre-dreaming, and session-zero-to-profile. This is the
"a lot has to happen here" scenario; high chance of surfacing undefined ordering
and missing lifecycle contracts. Scenario file:
`docs/simulations/scenarios/game_start_cold_boot.yaml`.

## Expanded Suite (Breadth)

Scenario files in `docs/simulations/scenarios/`, each targeting a distinct surface
and forcing boundary decisions:

- `gameplay_skill_check` — baseline gameplay: a social skill check, rules
  resolution, NPC activation, relationship update.
- `combat_round` — a combat round with conditions, a bounded
  `narrative_adjustment`, and a rule-of-cool `narrative_override`; rules-engine
  authority.
- `player_secret_question_mid_action` — a private player→DM question during a live
  combat turn; hidden check, dm-only routing, no live-flow stall.
- `voice_overlap_turn` — overlapping speech and barge-in mid-TTS; attribution,
  overlap recovery, TTFA.
- `image_generation_scene_art` — NPC portrait via art_director; privacy
  sanitization, async media, provenance split, display push.
- `world_recall_lore_query` — a lore query mid-scene; loremaster prepared-vs-live,
  perspective knowledge, canon vs rumor.
- `big_event_faction_clock_completes` — a faction clock completes live; live-vs-dream
  commit, cascading consequences, high-impact review.
- `session_resume_session_two` — warm boot into session two; between-session warmup,
  dreaming handoff, recap, off-screen clock advancement.

## Skill Shape

Fresh simulation is a repo-local Codex skill, not a live gameplay feature. Use
the skill when rerunning scenarios, comparing model families, or saving raw
simulation artifacts:

```text
.agents/skills/simulate/
  SKILL.md
  scripts/
    run_fresh_simulation.sh
  references/
    artifacts.md
```

The bundled runner creates a clean temporary workspace, excludes `.git`,
`docs/SYSTEM_SIMULATION_RUNS.md`, and prior run history, invokes Codex with the
requested model, validates `simulation_run.yaml`, and optionally persists the raw
run plus runtime trace into `../dungeoneer-sim-history`.

Use:

```bash
.agents/skills/simulate/scripts/run_fresh_simulation.sh \
  --scenario docs/simulations/scenarios/combat_round.yaml \
  --model gpt-5.4-mini \
  --model-label gpt-5.4-mini \
  --run-label rules_event_validation \
  --persist
```

Subagent roles remain the conceptual split:

- `fresh_simulator`: low-context runner; routes from docs/contracts only.
- `boundary_critic`: checks privacy, visibility, rules, canon, and latency.
- `scenario_mutator`: creates variants and edge cases.
- `maintainer_summarizer`: turns findings into tasks.

Fresh simulator input contract: a disposable broad repo copy with no prior
simulation outputs and no runner-only simulation docs, plus the scenario/rubric
to run. Avoid extra project context in the agent prompt.

## CLI Shape

Early CLI commands:

```bash
dungeoneer simulate list
dungeoneer simulate run scenarios/private_whisper.yaml --docs docs/
dungeoneer simulate run scenarios/loremaster_fork.yaml --mode fresh-agent
dungeoneer simulate report simrun:private_whisper_and_debt.001
dungeoneer simulate findings --status open
dungeoneer simulate recurrence --min 3
```

Before there is code, the CLI can be a thin wrapper that assembles prompt context
and writes the resulting trace artifact. After implementation starts, it should
prefer real instrumentation over imagined routing.

## What To Measure

Simulation is qualitative, but still structured.

Track:

- Number of undefined routes.
- Number of missing contracts.
- Number of privacy/visibility ambiguities.
- Number of direct-canon-mutation risks.
- Number of latency-path violations.
- Number of places the simulator had to infer behavior.
- Whether the same scenario produces stable routing across runs.
- Recurrence of each expected-but-missing affordance across runs and models —
  convergence is design pressure (adopt/fortify), a one-off is noise (ignore).
- Open findings by `cause`, `disposition`, `status`, `affected_docs`, and
  `expectation_fingerprint`.

The goal is not a perfect score. The goal is to surface architectural holes while
they are cheap.

## Relationship To Evals

Simulation runs are upstream of evals.

- Simulation finds design gaps.
- Evals freeze expected behavior once the design is accepted.
- Replay tests verify the implementation keeps matching the accepted route.

Flow:

```text
simulation run -> finding -> contract/schema/tool fix -> accepted trace -> eval fixture
```

## Build Order

Phase 0:

- Define the simulation artifact schema.
- Define the simulation history/search schema: runs, trace steps, findings,
  open questions, expectation fingerprints, and resolution links.
- Define output isolation: scenarios live in the repo; run/finding history lives
  outside the repo by default.
- Add a small hand-authored scenario suite.
- Add a prompt template for fresh simulator runs.
- Run manually through a fresh sub-agent or separate model session.
- Convert findings into roadmap/contracts.

Phase 1:

- Add CLI wrappers for simulation runs.
- Convert accepted traces into text-only DM eval fixtures.
- Use simulation before adding new tool boundaries.

Phase 2+:

- Compare simulated routing against real trace instrumentation.
- Add rules/combat/map/voice scenario packs.
- Run boundary critics automatically on trace artifacts.
