# Orchestration — The Live-Decision Layer

How the DM orchestrator decides what an inbound utterance *is*, and how it handles
traffic that arrives while a turn is in flight. Surfaced by system simulation as
the layer as under-specified as the rules engine was.

## Input Intent Classification

Every inbound utterance must be classified before routing. Classification is
**hybrid**: client-signaled where the player can cheaply say so, model-inferred
otherwise.

Message-type taxonomy:

```text
in_fiction_action     a declared action needing adjudication ("I attack")
in_fiction_speech     in-character dialogue to the table
npc_whisper           private in-fiction speech directed at an NPC
meta_question         a player asking the DM a question (rules, perception, "can I tell…")
ooc                   off-game table talk (non-canonical; see OOC handling)
lore_query            "what do we know about X" — a recall request
spatial_query         "where is X", "how far", "what is nearby", "how do we get there"
```

- **Client-signaled** first: an explicit channel/button (player remote "ask DM
  privately", an OOC toggle, a "whisper to NPC" target) sets the type cheaply and
  unambiguously.
- **Model-inferred** otherwise: the orchestrator classifies from content when no
  signal is given (most voice input).
- **Low confidence routes to a quick clarification**, never a silent guess on
  consequential traffic — consistent with the voice-chaos rule that consequential
  intent is never misassigned.

## The Parallel Side-Channel

A real DM can only think about one thing at a time. Dungeoneer does not have to.
Traffic splits into two lanes:

- **Serial lane (the turn):** anything that mutates shared canon or commits a
  table-visible result — actions, rolls that land on the table, narration everyone
  hears. These serialize into the live turn and respect the TTFA budget.
- **Parallel side-channel:** non-mechanical, non-shared traffic — lore questions,
  "what does my character notice," rules clarifications, private DM questions. These
  run *alongside* the active turn without stalling it.

The boundary is **shared-state mutation**, not topic. Edge case: a private question
that triggers a *hidden* check (the secret-question scenario) **computes in
parallel** — it rolls, resolves, and delivers privately — because its result
touches no shared canon and no table-visible commit. Only commits that hit the
table serialize.

This is a genuine capability, not just a concurrency fix: parallelized DM attention
smooths interactions in a way no human DM can, letting a player get a private
answer without the table waiting.

### Side-Channel QoS

The side-channel is subordinate to the table-visible live lane. It must not protect
private convenience by degrading the shared turn.

```yaml
schema: dwd.side_channel_task.v1
task_id: task:s4_private_insight
source_message: msg:s4_0132
kind: private_hidden_check | lore_query | rules_clarification | private_dm_question
audience: player:vanya
priority: background_interactive
deadline_ms: 1200
resource_policy:
  may_use_rules_tools: true
  may_use_retrieval: true
  may_use_live_dm_model: only_when_idle
  may_use_tts: false
  evict_live_models: false
  preempt_serial_lane: false
degradation:
  on_contention: text_only_or_defer
  on_deadline_miss: queue_private_notice
  cancellable: true
```

Rules:

- The serial table lane always has priority over side-channel tasks.
- A side-channel task may use local deterministic tools and retrieval if they do
  not stall the live lane.
- It may not evict the resident live DM model, TTS voice, ASR stream, or other
  resources needed for the current table-visible turn.
- Under contention, the side-channel degrades to private text, a short queued
  notice, or deferral. It does not synthesize private audio or force the table to
  wait.
- Side-channel work is cancellable. If the triggering context expires before
  completion, the task records `expired` or `aborted` delivery and does not enter
  player-facing recall.

### Private Hidden Check Pattern

A private hidden check is a side-channel task with a concrete event chain. It is
private because the result audience is private, not because it is unlogged.

```yaml
schema: dwd.private_hidden_check.v1
source_message: msg:s4_0132
check:
  schema: dwd.check_spec.v1
  kind: ability_check
  skill: insight
  actor: pc:vanya
  target: npc:ren_castavel
  adjudication_visibility: dm_only
  result_audience: player:vanya
  dice_source: digital
result_chain:
  - check_resolved
  - social_disclosure_decision
  - message.delivered
  - knowledge.learned
```

The usual chain is:

1. The player sends a private DM question.
2. The rules engine emits `check_resolved` with private adjudication visibility.
3. The orchestrator records a bounded disclosure decision.
4. The answer is delivered to that player (`message.delivered`, audience
   `player:<pc>`).
5. If the fiction gives the PC knowledge, emit a private `knowledge.learned` edge
   for that PC.

The table does not learn the answer until the player discloses it through a
table-delivered event. Usually that is just the player speaking aloud in character
or at the table. An optional remote "share" affordance is only another way to emit
the same kind of table-delivered disclosure event; it is not required for normal
play.

## Consequence Triage

In live play, one player action can imply more consequences than the turn can
responsibly resolve. The orchestrator always separates consequence handling into
three buckets before committing state:

```yaml
schema: dwd.consequence_plan.v1
source_message: msg:s12_0048
source_event: event:s12_0049
immediate_effects:
  - kind: clock_advance
    target: clock:hearthward_exposed
    route: live_tool
deferred_effects:
  - kind: faction_reaction
    target: faction:choir
    route: dream.patch_proposed
blocked_effects:
  - kind: create_fact
    target: fact:hearthward_shrine_exposed
    route: no_canon_write
```

Rules:

- If an utterance or narration beat has no load-bearing consequence, the
  orchestrator records delivery/transcript provenance and stops. It does not
  manufacture a fact, clue, thread, clock tick, or consequence plan just because
  the content is interesting.
- **Immediate** means the next few seconds of play depend on the result and a
  bounded typed tool can validate it locally. Rules results, explicit knowledge
  delivery, item transfers, location/position changes, targeted relationship
  nudges, explicit clock advances, and preauthorized clock outcomes fit here.
- **Deferred** means the consequence is real pressure but does not need to block
  the live turn: broad fallout, off-screen reactions, rumor spread, memento
  promotion, capsule refresh, recap/prep updates, and clock outcomes that are not
  preauthorized for live completion.
- **Blocked** means the system lacks a deterministic definition, payload,
  authority, or validator. Blocked effects produce no canon mutation. The DM may
  acknowledge uncertainty or narrow the narration, but cannot invent the missing
  mechanics or world write.
- The live lane serializes only immediate table-visible effects. Deferred effects
  are queued for dreaming/review with provenance. Blocked effects are logged for
  operator/rules follow-up.
- A table event is valid provenance, not unlimited live write authority. The
  orchestrator commits only explicitly addressed, validator-owned effects now.

## Loremaster Live Fallback

A live loremaster fork is forbidden (latency), and warmup prepares likely experts —
but a player can always ask something unprepared. The fallback, *this turn*:

1. Answer from **direct retrieval** (lore_librarian + party knowledge + event
   search) at reduced depth, within the context-assembly budget — never a
   synchronous fork.
2. If even that is thin, give a **caveated recall** ("what you remember is…") rather
   than stalling or fabricating.
3. Emit `lore.prepare_requested` for the next warmup / prepare_likely pass, so the
   gap closes for next time.

Players never feel the machinery; they get a bounded honest answer now and a better
one later.

### Lore Recall Contract

`lore_query` routes to one orchestrator-facing tool: `lore.recall`. The tool
bundles party-knowledge projection, event search, prepared capsule material, and
player-facing redaction. Agents should not assemble player recall by hand from raw
retrieval snippets.

```yaml
schema: dwd.lore_recall_request.v1
request_id: tool:lore_recall_012
source_message: msg:s12_0180
requester: pc:dorn
scene: scene:s12_brass_lantern
channel: voice
audience: table
topic:
  kind: entity
  refs: [faction:choir]
  text: "what do we know about the Choir?"
```

Default routing:

1. Classify the message as `lore_query`.
2. Derive audience. Voice in a table scene defaults to `table`; private remote,
   explicit aside, or operator override narrows it to the relevant player audience.
3. Call `world.query_party_knowledge` using present PCs and delivered-only sources.
4. Add event-search and prepared capsule snippets only after applying the same
   player-facing projection.
5. Return `dwd.recall_answer.v1` claims with per-claim citations, truth/rumor
   labels, and redaction metadata.
6. Deliver the rendered answer as `message.delivered`.

If the system has no player-safe support for a claim, it says so. It may return a
caveated recall claim, but it must mark that claim as uncertain and cite no hidden
source text.

### Lore Prepare Request

When `lore.recall` returns `caveated`, `empty`, or `deferred` because prepared
material is thin or missing, the orchestrator records a durable preparation
request.

```yaml
schema: dwd.lore_prepare_requested.v1
type: lore.prepare_requested
payload:
  topic:
    kind: entity | thread | location | faction | freeform
    refs: [faction:choir]
    text: "what do we know about the Choir?"
  scene: scene:s12_brass_lantern
  triggering_message: msg:s12_0180
  audience: table
  reason: missing_prepared_capsule | thin_player_safe_support | unresolved_contradiction
  urgency: next_warmup | before_next_scene | operator_review
  target_capsules:
    - loremaster:faction.choir
  privacy_classification: player_safe | dm_only | mixed
status: requested
```

Warmup and dreaming consume the projection of open `lore.prepare_requested`
records, coalesce duplicates by topic/scene/capsule, refresh the relevant
`prepare_likely` material, and mark the request prepared, superseded, or rejected.

## Spatial And Travel Queries

Spatial/travel reasoning is a required tool surface, not model intuition. When the
DM needs to answer where something is, how far away it is, what borders it, what
ports or airship towers are nearby, or how long a route takes, the orchestrator
calls the spatial/travel tools defined in
[Spatial and travel system](SPATIAL_TRAVEL.md).

Live behavior:

1. Use fast spatial projections for containment, nearby, neighbors, distance, and
   prepared route summaries.
2. Use pgRouting-backed route solving when the answer affects a player choice
   ("can we get there before dawn?").
3. If weather, faction risk, or vehicle capability is uncertain, answer with
   assumptions and mark the uncertainty rather than inventing precision.
4. If travel will advance world time or move actors/vehicles, serialize it through
   accepted travel events; a route preview alone is only a proposal.

Spatial tools can run in the parallel side-channel when they do not mutate shared
canon. Travel execution that changes world time, party position, faction clocks,
or encounter risk serializes through the main lane.

## Player-Facing Capsule Redaction

A loremaster/expert capsule is DM-facing — its always-load material can include
`private_truth` and dm_only notes. Answering a *player* query directly from that
material would leak secrets (an invariant collision surfaced by simulation).

So any capsule-derived content bound for a table/player audience passes a
**player-facing projection** that strips dm_only material before delivery — the
same shape as the restricted-host sanitizer, but for the DM->player direction. No
capsule content reaches players unredacted.
