# Dungeoneer System Scope

## Motivation

Dungeoneer is a craft project, built for the love of the game, not a product. If
it is ever released it will be MIT-licensed and given away. There is no business
model, and design decisions optimize for the experience at a real table and for
interesting engineering, not for reach, onboarding, or monetization.

The motivation comes from years of DMing and two convictions:

- The DM is the bottleneck. Far more groups want to play than have someone able
  and willing to run a game. Removing that barrier lets tables exist that
  otherwise would not, and lets the person who would have been stuck behind the
  screen finally play.
- Bad DMing, not bad rules, drives most bad play. The system does not need to beat
  a great human DM; it needs to raise the floor: never forget a thread, never
  fudge the rules into incoherence, never contradict its own canon. Reliably not
  being a bad DM already beats a large share of real tables.

This means Dungeoneer should augment, not only replace. The same orchestration,
memory, and rules machinery can sit beside a human DM who loves the craft, doing
the bookkeeping while the human keeps the parts they enjoy. See
[Portability and deployment tiers](PORTABILITY.md) for how a human-DM profile fits
the same core.

The deliberate niche is the physical, in-person table. The rest of the field (see
[Prior art](PRIOR_ART.md)) went to the screen — cloud-hosted, virtual tabletops,
play-from-anywhere. Dungeoneer goes the other way, back to friends physically
around a table, because that is where the social magic of the game lives.

## Product Goal

Dungeoneer is a local-first AI Dungeon Master for live D&D-style tabletop play.
It should support spoken conversation, text chat, persistent campaign memory,
NPC reactivation, deterministic rules adjudication, map and battle-grid
perception, and generated multimedia.

The first production-quality target is not "a chatbot that knows D&D." It is a
stateful game engine with AI agents attached to it.

## Build Philosophy

The scarce resource is systems thinking, not implementation. With capable agentic
tooling, writing code and implementing known concepts is fast; reasoning through
the systems, boundaries, and failure modes is the hard part. This repo is deep on
design and validation scaffolding before application build begins. Product code
waits until the premise and the system feel solid.

This is stated explicitly because it cuts against a strong default. "Ship the
minimal MVP, do not over-engineer" is the dominant pattern in the training data,
so agents (and habit) pull toward feature-minimalism. That advice came from a
world where implementation was the expensive, risky step. It is not our world.
Complexity is cheap to *build* now; the discipline is to make sure it is
*validated*.

So:

- **Phases are ordered by risk, not by feature count.** The early spikes (voice
  chaos, latency) come first because they are gated by physical reality, not
  because they are "minimal." A later phase may be more complex than an earlier
  one.
- **Build as rich as the design warrants** — the full world schema, capsules, and
  knowledge model can land early because implementing them is no longer the
  bottleneck. Unvalidated complexity is the enemy, not complexity itself.
- **Two gates cannot be shortcut by agents or simulation.** Physical-world
  unknowns (does room capture work, does TTFA hold) need empirical spikes.
  Subjective quality (does the NPC feel like it remembers, is the DM fun) needs
  real play. Everything between them is validated by system simulation runs (see
  [System simulation runs](SYSTEM_SIMULATION_RUNS.md)) before and during build.
- **Validation pipeline, not minimal build, is how we de-risk:** simulation finds
  design gaps, evals freeze accepted behavior, replay verifies the implementation
  keeps matching.

### Deferral Is A Deliberate Decision, Never An Escape Hatch

This is a second, sharper trap, distinct from minimalism. Legitimate deferral
applies only to **whole systems or approaches**, decided explicitly and recorded
(see "Deferred And Out Of Scope"). It is an architectural choice made up front,
visible in the plan.

It is **never** an implementation-time reaction to a hiccup. Building a system that
is defined to be built now, and hitting friction, does not authorize quietly
descoping it, stubbing it, or shipping a partial version. There is no real time
pressure here — this is a passion project with no deadline, no PR to land, no
incident clock. The imagined urgency to "just get something working fast" is false
and, in practice, *always* costs more than it saves: the system looks done, but
parts that were defined to exist were silently dropped, and nobody knows until the
gap surfaces downstream as a baffling failure.

The rule on friction while building a defined system:

- Build it as defined. Friction is not a scope decision.
- If it genuinely cannot or should not be built as written, **stop and surface it**
  as an explicit decision — do not unilaterally reduce scope mid-build.
- Never present a partial implementation as complete. "Done" means built as
  defined, not "the easy 80% landed and the hard part was quietly deferred."

A deferral that is not written down in the plan is not a deferral. It is a silent
defect.

## Required Capabilities

- Text and voice interaction with the DM.
- Multi-client play surfaces: table console, player display, and player remotes.
- Streaming speech-to-text and text-to-speech.
- Persistent campaign, session, scene, NPC, location, item, and rules state.
- Event-sourced conversation and game history with replayable state changes.
- Required spatial and travel intelligence for geography, containment, nearby
  places, borders, route planning, sea travel, airship travel, and travel-time/risk
  estimates. See [Spatial and travel system](SPATIAL_TRAVEL.md).
- DM orchestrator that retrieves context, loads NPCs, invokes rules tools, and
  controls pacing.
- Isolated NPC sub-agents with durable memory, relationships, secrets, goals,
  voice profile, style constraints, background activity, and scoped tools.
- Deterministic dice, checks, initiative, turn order, conditions, resources,
  inventory, spell effects, and monster actions, with physical-dice reading via the
  vision system as the default (digital roller as fallback). See
  [Rules engine](RULES_ENGINE.md).
- VLM-based map and battle-grid perception from uploaded images, webcam frames,
  or VTT screenshots.
- Image generation for portraits, locations, items, monsters, and scene beats.
- Video generation for async cinematic recaps or short cutscenes.
- Table safety and campaign guardrails configurable per group.
- Out-of-character / table-pause as a first-class state: the DM steps back during
  off-game tangents, and off-game speech is excluded from canonical memory.
- Selectable and customizable DM profiles (style presets plus per-knob custom),
  with a human-in-the-loop improvement loop that proposes adjustments via dreaming.

## Deferred And Out Of Scope

These are deferred by risk-ordering or excluded on principle — not omitted for
minimalism. Some are sequencing calls (revisit when their prerequisites or
validation exist); others are hard non-goals.

Sequencing (revisit later):

- Real-time video generation in the live DM response path.
- Interactive smart-table hardware or a modern SurfaceScapes-style tabletop.
- Fine-tuning large models before we have logs, evals, and stable prompts.

Hard non-goals:

- Replacing the rules engine with model judgment.
- Fully autonomous tactical combat without player confirmation.
- Bundling proprietary D&D books or settings beyond licensed/open material.

## Service Layout

### Client

Primary live-play surface:

- Web app or desktop shell.
- Text chat, voice input, push-to-talk, and live transcript.
- DM/NPC audio playback with interruption support.
- Campaign timeline, inventory, character state, and combat tracker.
- Turn-gated map frame upload, webcam capture, or VTT screenshot import.
- Generated image/video gallery.
- DM-controlled shared display for generated images, generated video, public
  text, handouts, NPC portraits, scene cards, and public rules/combat state.
- Player remote UI for private messages, character state, rolls, handouts, and
  confirmations.

See [Frontend clients](FRONTEND.md) for the recommended device layout.

### API Gateway

Backend entry point:

- FastAPI or equivalent HTTP/WebSocket service.
- Auth and campaign/session routing.
- Streaming event transport.
- Request validation and rate limiting.
- Tool-call boundary between agents and deterministic systems.
- Capability-scoped tool access for DM, NPC, rules, lore, and perception agents.

### DM Orchestrator

The central agent loop:

1. Ingest player speech/text/map input.
2. Store raw input as immutable events.
3. Retrieve relevant campaign, NPC, location, rules, and safety context.
4. Decide whether to narrate, ask a question, activate NPC sub-agents, call
   rules tools, or request map perception.
5. Validate game-state changes through deterministic tools.
6. Emit narration, NPC lines, rule results, and follow-up actions.
7. Persist every model response, tool call, generated asset, and state delta.

### Agent Roster

- `dm_orchestrator`: Owns scene flow, tool selection, and player-facing output.
- `rules_referee`: Converts natural-language intent into rule tool calls.
- `npc_actor`: Isolated sub-agent that speaks, acts, plans, and reacts for a
  specific NPC from durable private memory.
- `loremaster`: Forkable expert capsule for a world, region, faction, thread,
  rules domain, or source corpus. Answers from canon, cites provenance, and
  proposes patches rather than inventing truth.
- `lore_librarian`: Retrieves canon, session history, and campaign notes for
  orchestrator and loremaster context assembly.
- `map_perceptor`: Reads images/video frames and proposes map-state updates.
- `art_director`: Creates prompts and jobs for image/video generation.
- `safety_moderator`: Applies table-specific boundaries and pause mechanics.

Agents should communicate through typed events and tool results, not hidden
shared prompt text. NPCs are true sub-agents, but the live voice path should not
become a slow sequential chain of agent calls. The orchestrator owns pacing and
may use prepared NPC stance/state from background work.

See [NPC sub-agents](NPC_AGENTS.md) for the isolation and tool-boundary model.

## Persistence Model

Use full-history storage as the source of truth.

- `events`: Immutable campaign/session timeline.
- `messages`: Raw text, transcripts, model responses, and speaker metadata.
- `message_visibility`: Records the audience axis (who may see it) and the
  delivery axis (delivered, queued, expired, aborted, proposed) as separate
  dimensions. Audience, delivery, and fact truth-status are orthogonal; see the
  canonical definition in [Game world schema](GAME_WORLD_SCHEMA.md).
- `tool_calls`: Inputs, outputs, model IDs, latency, and errors.
- `agent_runs`: DM, NPC, lore, perception, and dreaming agent invocations with
  model/runtime metadata.
- `brain_capsules`: Identity and expert capsule snapshots, including NPC
  activation bundles and forkable loremaster capsules.
- `entities`: NPCs, PCs, monsters, factions, locations, items, quests.
- `entity_memories`: Facts, preferences, secrets, relationships, summaries.
- `rules_state`: Characters, resources, effects, initiative, positions.
- `spatial_state`: PostGIS/pgRouting projections for location geometry,
  containment, territories, hazards, route graph, and travel plans.
- `assets`: Generated images, videos, audio, prompts, seeds, and provenance.
- `embeddings`: Retrieval index over events, messages, entities, and assets.
- `dream_jobs`: Slow post-session consolidation jobs and proposed state patches.

World state is split by kind: mechanical state (HP, positions, resources,
conditions) is strictly typed and owned by the rules engine, while narrative state
(lore, factions, rumors, quest fiction) is stored as flexible JSONB documents. Both
are projections over the event log and governed by versioned contracts. All of it
lives in Postgres; there is no separate document store. See
[Technical decisions](DECISIONS.md) and [Game world schema](GAME_WORLD_SCHEMA.md).
Spatial/travel projections also live in Postgres through required PostGIS and
pgRouting extensions; they are rebuildable projections over DWD definitions and
accepted events, not a second source of canon. See
[Spatial and travel system](SPATIAL_TRAVEL.md).

Summaries are convenience layers. If a summary is wrong, it can be regenerated
from events.

Player-facing memory must distinguish delivered content from undelivered or
aborted generations. Aborted DM or NPC speech can be retained for audit, but it
must not be recalled as something the table heard.

Private player messages are canonical only for their intended recipient(s), the
DM orchestrator, and audit/replay systems. Other players and NPCs do not receive
that content unless it is later revealed through play.

Out-of-character spans (off-game table chat during a break) are tagged as a
non-canonical visibility class. They are excluded from game recall, NPC memory,
embeddings, and dreaming, and are preferably not persisted beyond what short
retention or audit needs. See [Voice chaos gate](VOICE_CHAOS.md).

## Memory Strategy

Agent activation without context loss requires layered memory. NPCs resume
identity capsules; loremasters and other experts fork prepared expert capsules.

NPC reactivation requires:

- Full transcript and event replay for exact historical recovery.
- Structured entity facts for reliable current state.
- Relationship graph for social continuity.
- Episodic memories for important scene-level recall.
- Vector retrieval for fuzzy resurfacing.
- Recency window for immediate conversational coherence.

When an NPC is loaded, the orchestrator should assemble:

- Current scene and player intent.
- NPC public profile and private state.
- Relevant shared history with present characters.
- Active goals, fears, secrets, obligations, and constraints.
- Recent direct dialogue.
- Rules-relevant stats if combat or checks are possible.

NPC private deliberation should be stored as concise intention summaries,
mementos, and state proposals, not raw chain-of-thought transcripts.

Expert/loremaster activation requires:

- A prepared capsule for the relevant domain.
- Curated always-load summaries.
- Source references and contradiction notes.
- Focused retrieval over exact supporting events and definitions.
- Scoped tools for inspection, citation, and patch proposal.

## Rules Engine

The rules engine should be deterministic and inspectable.

Initial rules coverage:

- Ability checks, saving throws, attacks, damage, healing, advantage,
  disadvantage, proficiency, DCs, and contest resolution.
- Initiative, turns, reactions, movement, grid distance, cover, conditions, and
  concentration.
- Character resources, inventory, spells, monster stat blocks, challenge data,
  and encounter state.
- Dice roller with seed logging and optional physical dice override.

The DM may explain or interpret outcomes, but canonical state changes must go
through rules tools.

## Map And Battle-Grid Vision

The VLM is part of a perception pipeline, not the canonical state holder. D&D is
turn-based, so map perception should be capture-on-demand around meaningful
decision points rather than a continuous video scan.

Pipeline:

1. Capture or upload image/frame before an action, after an action, or when the
   DM/player requests confirmation.
2. Calibrate grid boundaries and orientation.
3. Detect tokens, labels, obstacles, fog, terrain, and hand-drawn annotations.
4. Ask the VLM to interpret ambiguous visual context.
5. Convert perception into proposed typed changes.
6. Reconcile with current rules state.
7. Confirm risky or low-confidence changes before applying.

Expected outputs:

- Grid dimensions and coordinates.
- Token identities and positions.
- Terrain and obstacle tags.
- Distance and line-of-sight helpers.
- Confidence scores and unresolved ambiguities.

Continuous video may be useful later for convenience, but it should still feed
discrete perception jobs. The rules engine owns the canonical state between
confirmed captures.

## Local Model Runtime

Put every model behind a local model gateway with OpenAI-compatible or simple
HTTP APIs where possible.

Recommended services:

- `vllm`: Primary LLM/VLM serving when model support is available.
- `ollama` or `llama.cpp`: Fast experimentation and smaller local models.
- `comfyui`: Image and video generation workflows.
- `faster-whisper` or NVIDIA Riva: Speech-to-text.
- NVIDIA Riva, Piper, XTTS-style, or F5-style services: Text-to-speech.
- Embedding/reranker service: Retrieval and memory ranking.

The app should not depend directly on any one model family.

## Hardware Plan

Available discrete GPUs:

- RTX 5090 (home): resident live DM dialogue model.
- RTX 4090 (home): the conversation brain — streaming STT, streaming TTS,
  embeddings, and a small NPC background model. Audio and transcripts stay here.
- RTX 6000 Ada (restricted host, home LAN): battle-grid image perception and
  image/video generation from sanitized jobs. It never receives audio,
  conversation transcripts, conversation embeddings, or raw source context.
- N150 network node: useful for always-on control-plane work, health checks,
  queue workers, dashboards, and tiny non-live-path models if benchmarks justify
  it.

A privacy boundary keeps raw audio, transcripts, conversation embeddings, vector
search, and private source context on the home machines. The restricted-host GPU may handle
sanitized cropped images, sanitized media briefs, and generated media, but
workloads that ingest, index, search, or emit conversation content cannot be
offloaded to it.

Consumer GPUs do not automatically combine VRAM. Prefer one model or service per
GPU unless tensor or pipeline parallelism is explicitly supported by the runtime.

Optional DGX Spark:

- Useful for memory-heavy local inference, larger models, fine-tuning, and long
  context experiments.
- Not required for the first build.
- Treat as a bonus model-lab node rather than a prerequisite for live play.

See [Hardware topology](HARDWARE.md) and [Privacy boundary](PRIVACY_BOUNDARY.md)
for the current machine split.

## Post-Session Dreaming

After each session, Dungeoneer should run a slow consolidation pipeline. This is
not on the live path and may take minutes or hours.

Dreaming responsibilities:

- Replay the session event log and verify that derived state matches canonical
  state.
- Promote, demote, or repair NPC mementos with provenance.
- Update faction plans, world clocks, rumors, consequences, and off-screen NPC
  actions.
- Prepare likely next-session context bundles, NPC stances, and unresolved
  question lists.
- Queue optional recap media, portraits, maps, or scene art.
- Produce reviewable proposed state patches for high-impact changes.

Dreaming does not replace the event log. It is a slow projection and planning
stage over the canonical record.

See [Post-session dreaming](POST_SESSION_DREAMING.md) for the pipeline.

## Guardrails

Rules guardrails:

- State changes require typed tool calls.
- Dice rolls and combat transitions are logged.
- Illegal actions return explanations and alternatives.
- NPC sub-agents can propose speech and actions, but they cannot directly mutate
  canonical rules state.

Table guardrails:

- Session-zero profile, boundaries, rating, tone, and banned themes.
- Pause, rewind, and X-card events.
- Out-of-character / table-pause: the DM defaults to silence during off-game
  tangents and re-engages only when addressed.
- A player "something's off" channel: a first-class meta flag for DM-correctness
  (railroading, contradiction, tone), distinct from the safety X-card. The DM pauses
  and lets the table redirect. See [DM profile](DM_PROFILE.md).
- DM must ask for player intent when ambiguity would create a major consequence.

Narrative guardrails:

- No accidental spoilers from hidden NPC or campaign state.
- NPC private knowledge is only available to that NPC and the DM orchestrator.
- Private player messages must carry explicit visibility and delivery metadata,
  and should not be used to create hidden obligations without player consent.
- The DM should preserve player agency and avoid forcing outcomes not grounded in
  rules, prior fiction, or explicit table preference.

## Licensing Notes

Use Creative Commons SRD material as the default rules source. Do not bundle
closed books, adventures, settings, monsters, or character options unless the
project has explicit legal permission or the user supplies them for private use.
