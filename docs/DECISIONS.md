# Technical Decisions

## Initial Stack

See [Tech stack](TECH_STACK.md) for the canonical stack map, spike candidates,
and ownership boundaries. The short version:

- Backend: Python with FastAPI.
- Contracts: Pydantic models and JSON Schema.
- Storage: Postgres for everything canonical — typed rules state, the event log,
  and JSONB document projections for open-ended world state. No separate document
  store.
- Retrieval: Start with pgvector; move to Qdrant only if scale or operations
  demand it.
- Object storage: Local filesystem first, S3-compatible API later.
- Frontend: React or Tauri once the live-play UX is ready to build.
- Model gateway: HTTP services with stable app-owned interfaces.
- Agent tool gateway: typed REST service plus CLI wrapper over shared Pydantic
  contracts. MCP adapter deferred until interoperability need is proven.
- Agent workflow runtime: LangGraph for durable workflows.
- Agent harness: Deep Agents preferred for non-live NPC/dreaming/skill work,
  pending Phase 0 spike and kept behind a Dungeoneer-owned adapter.
- Restricted-host model service: vLLM for sanitized VLM/perception jobs and ComfyUI for
  sanitized media jobs.
- Realtime transport: WebSockets.

## Agent Tool Gateway Strategy

Start with a contract-first gateway, not MCP as a Phase 0 dependency.

The canonical interface is a set of versioned Pydantic contracts and service
functions. Runtime services expose those contracts through REST/WebSocket where a
process boundary is useful, and through direct Python calls where latency and
transaction boundaries matter. The CLI is a first-class adapter over the same
contracts for replay, evals, debugging, and operator workflows.

Rationale:

- The live DM path needs bounded latency, cancellation, and small tool surfaces.
  Direct calls or long-lived REST services are simpler and faster to reason about
  than spawning tools or negotiating an agent protocol inside a turn.
- CLI commands make replay and debugging easy without forcing runtime agents to
  invoke subprocesses.
- MCP is useful for sharing and interoperability, but it has tool-discovery,
  manifest, connection, and context overhead that should not be paid before it
  adds value.
- A future MCP server can wrap the same contracts once the core tool surface is
  stable. It should be an adapter, not the system of record.

Default rule:

- **Live/runtime path**: direct typed calls or REST/WebSocket to long-lived
  services.
- **Dev/replay/evals/deployment**: CLI over the same contracts.
- **Future interoperability**: MCP adapter only when a concrete integration
  benefits from it.

## Design For Agent Predictability

The primary consumers of Dungeoneer's internal surfaces — tool names, contracts,
event types, capability routes — are agents, not humans. Agent-facing design
optimizes for **predictability**: the affordance should sit where a competent,
well-trained model would reach for it, named and shaped the way such a model
predicts, so agents route correctly from priors. Human-facing surfaces (CLI,
prose, docs) optimize for **understandability**. These usually agree; when they
conflict, choose by who consumes that surface.

Consequences:

- Prefer the conventional shape over the clever one for anything an agent calls.
  Surprise-to-expectation is a defect on the machine surface.
- **Hallucination is signal.** When a fresh agent (e.g. a system simulation run)
  confidently expects an API, route, or field that does not exist, treat it as a
  design proposal — the model's prior is voting for the predictable shape.
  Hallucination proposes; design disposes. Requirements and invariants still gate,
  just as not every feature request ships.
- **Repetition is pressure.** A single surfaced expectation is interesting; the
  same one recurring across runs or models is a strong vote. Convergence is what
  separates a real predictable-shape signal from one-off sampling noise.
- **Collisions are the highest-value finding.** When a convergent expectation
  violates an invariant (an agent reaching to mutate canonical state directly), it
  predicts where future implementation agents will try to cheat. Fortify the typed
  boundary there and make the guardrail loud.

See [System simulation runs](SYSTEM_SIMULATION_RUNS.md) for how simulation surfaces
these.

## Repository History Strategy

Use git for project durability, review, and rollback. Do not use git history as a
design source of truth.

Rationale:

- The project has enough valuable design and world material that version control
  is necessary durability infrastructure.
- The current tree is the only normative source for design review. The
  documentation corpus describes the current system only; commit logs, diffs,
  branches, and old file contents are not part of the architecture.
- Fresh system simulation runs must receive current files only. The runner may
  use git to create a clean snapshot, but the simulator workspace excludes `.git`
  metadata and does not expose logs, diffs, or prior commits.
- If a decision changes, edit the canonical docs in place and keep only the
  current rationale.

## Streaming Strategy

Streaming is a hard requirement on the live conversational path, not an
optimization. The DM must begin speaking before it finishes generating and must
be interruptible mid-sentence.

Rationale:

- The product goal is live spoken play; a multi-second pause after every player
  turn breaks the illusion regardless of output quality.
- Streaming forces the live path to be a single cancellable pipeline rather than
  a multi-agent request/response chain, which keeps time-to-first-audio bounded.
- It makes GPU residency a latency constraint, surfacing the hardware question
  early instead of in month six.

See [Latency budget](LATENCY.md) for the canonical metric and per-stage budget.

## Out-Of-Character Handling

Out-of-character (OOC) is a first-class session state, not an edge case. In-person
tables take off-game breaks often, and the system must step back rather than nag
or narrate into them.

- Default to silence when the system cannot tell whether the table is playing.
- Re-engage on an address cue ("DM, we're back"), which is boundary signaling, not
  push-to-talk.
- Tag OOC spans as a non-canonical visibility class, excluded from game recall,
  NPC memory, embeddings, and dreaming, and preferably not persisted. This is both
  a memory-quality and a privacy guarantee.

See [Voice chaos gate](VOICE_CHAOS.md) for the live behavior.

## DM Profile Strategy

There is no universal best DM, so DM style is configurable per table, split into
two layers. Persona (tone, humor, narration density, NPC voicing) is prompt-shaped
and can be a persona description. Policy (rules authority, lethality, story
pressure, spotlight, pacing, safety) is system-enforced, because the architecture
must guarantee it rather than hope the model complies.

The load-bearing case is rules authority. Rule-of-cool is not a prompt instruction
to fudge; it is gated through logged `narrative_adjustment` and
`narrative_override` capabilities the rules engine exposes only when the profile
allows them, with provenance on every use. Strict mode simply does not expose
them. This keeps even rule-of-cool inspectable.

Style adapts through a human-in-the-loop loop, never silent optimization. Fun is
subjective and easy to Goodhart, so post-session dreaming proposes profile
adjustments from explicit and implicit signals, the table confirms, and style
evals verify the DM behaves to its profile. See
[DM profile and improvement loop](DM_PROFILE.md).

## NPC Sub-Agent Strategy

NPCs should be real sub-agents, not just names injected into the DM prompt.

Rationale:

- Isolation protects each NPC's private knowledge, voice, agenda, and memory.
- Background NPC agents can react to events, update intentions, and prepare
  stances without blocking the live DM response.
- Capability-scoped tools let an NPC know only what that NPC can plausibly know:
  visible PCs, audible dialogue, known factions, current position, inventory, and
  personal memories.
- The DM remains the table-facing orchestrator. NPC sub-agents propose speech and
  actions; the DM and rules engine arbitrate what becomes canonical.

The live path may call an NPC sub-agent directly for high-value dialogue, but it
should prefer already-prepared NPC stance/state when latency is tight. See
[NPC sub-agents](NPC_AGENTS.md).

## Brain Capsule Strategy

Use brain capsules as durable, forkable activation bundles for agents. An NPC is
one capsule type, but not the only one. Loremasters and other expert agents also
use capsules so Dungeoneer can quickly instantiate a prepared specialist instead
of starting from a blank agent and asking it to read the world from scratch.

There are two starting capsule families:

- **Identity capsules**: resumed for durable actors such as NPCs. They preserve a
  continuing point of view, private memory, relationships, goals, and current
  intention.
- **Expert capsules**: forked for specialists such as loremasters, rules aides,
  faction analysts, historians, cartographers, and dream reviewers. They preserve
  curated domain knowledge, contradiction notes, source references, and retrieval
  hints.

Forked expert runs can produce notes, answers, and proposed patches, but they do
not mutate the capsule directly. Accepted changes are appended as events or
reviewed patches, then folded into later capsule snapshots by dreaming.

See [Brain capsules](BRAIN_CAPSULES.md).

## NPC Memory Strategy

Store the complete conversation history of every NPC, permanently. Storage is
not the constraint; the model context window is. Disk is cheap (36 TB of local
NAS), so we never delete or lossily summarize an NPC's source history.

The model context window cannot hold a full campaign of NPC history, so "no
context loss" is achieved at *recall* time, not by stuffing everything into the
prompt. Each NPC is a restartable **brain capsule** with three tiers:

- **Immutable base**: personality, voice, core characteristics, and starting
  drives. This is who the NPC fundamentally is. It does not mutate in place; it
  is small enough to always load in full.
- **Mementos**: an append-only set of character-defining moments that accrete
  onto the base over the campaign (a debt owed, a life spared, a betrayal, an
  oath sworn, a death witnessed). Mementos always load with the base. They are
  what makes a reactivated NPC feel like it lived through events rather than
  resetting to a template.
- **Full history**: the complete append-only conversation and event log, the
  source of truth, never discarded, recalled by relevant slice at activation.

Activation assembles base + all mementos + the retrieved relevant history slice
(recent direct dialogue, shared history with present characters, rules-relevant
state) into the working context.

### Memento Rules

- **Promotion is mostly deterministic.** Mechanical defining moments are typed
  game events and promote to mementos automatically: a debt, a contract, an item
  gifted, an oath, a kill. Purely narrative significance ("the moment she
  decided to trust the party") is model-proposed and logged with provenance, not
  auto-trusted.
- **Promise/oath mementos require a delivered source event.** An oath or promise
  promotes only from the event that recorded it reaching its target — for a promise
  made privately to an NPC, the `message.delivered_to_npc` event (see Private
  In-Fiction Messages in [Game world schema](GAME_WORLD_SCHEMA.md)). The memento
  cites that event as its `source_event`; a promise inferred during dreaming with
  no delivered source event is not promotable.
- **Mementos are append-only but have lifecycle state.** A debt is not deleted
  when repaid; it transitions open -> settled, and the repayment is itself a new
  defining moment. The NPC remembers being owed *and* repaid, because that is
  character.
- **Canonical state lives once.** A debt's amount and terms live in entity/rules
  state; the memento references it rather than copying it, so there is no second
  source of truth to drift.
- **Mementos are a regenerable projection of events**, consistent with the rest
  of the system: if the memento set is wrong, it can be rebuilt from the event
  log. Durable and curated, but not authored independently of history.
- **The always-load set is bounded by salience.** Mementos carry weight; if the
  set outgrows its context budget, the lowest-salience ones demote to
  retrieval-only. They are never deleted, only moved out of the guaranteed-load
  tier.

This makes retrieval quality the thing to measure: with full storage and an
always-loaded memento tier, the failure mode is not lost data, it is promoting
the wrong moment or priming with the wrong history slice. Recall and promotion
correctness get an eval (see ROADMAP), not just an assertion.

Memento promotion is a trust boundary. Model-proposed promotions must be
schema-constrained, provenance-stamped, replayable, and reviewable when they
would substantially change an NPC's personality, loyalties, or long-term plans.

## State Strategy

Use event sourcing for campaign and session history.

Rationale:

- Full context can be recovered, re-indexed, and re-summarized.
- NPC memory can be rebuilt from source events.
- Rules regressions can be reproduced.
- Model mistakes can be audited against exact prompts and tool results.

## World State Storage

World state is split by kind, not stored one uniform way, and it all lives in
Postgres. There is no separate document database.

See [Game world schema](GAME_WORLD_SCHEMA.md) for the canonical ontology,
definition syntax, perspective/knowledge model, and build order.

- **Mechanical state is strictly typed.** HP, positions, initiative, resources,
  conditions, and inventory counts live in typed tables the rules engine owns and
  validates. Flexibility here is a defect: this is the state that must be
  deterministic, testable, and unmutatable by narration.
- **Narrative state is flexible documents.** Lore, faction agendas, rumors, quest
  fiction, and location color live as JSONB documents. Their shape is open-ended
  and cannot be enumerated up front.
- **Spatial/travel state is indexed projections.** Location geometry, containment,
  territories, hazards, route nodes, route edges, sea lanes, and airship corridors
  live in PostGIS/pgRouting-backed projection tables derived from definitions and
  events. They are required because geography and travel are part of play, but
  they are not canon separate from the event log.

## Knowledge And Social Disclosure Strategy

Player-facing recall and social disclosure share one contract family. Recall is
the read side: what may this player or table audience safely know, with citations
and redactions? Social disclosure is the write side: what new delivered message,
knowledge edge, fact assertion, secret reveal, or relationship proposal is
authorized by this check and NPC stance?

Rationale:

- Both surfaces are secrecy boundaries. If recall and disclosure use different
  audience, truth, and citation rules, the system can either leak a secret through
  recall or create knowledge that later cannot be safely explained.
- Canon still lands in the existing event vocabulary: `message.delivered`,
  `knowledge.learned`, `fact.asserted`, `secret.revealed`, and
  `relationship.changed`. The new contracts are query/decision payloads and
  provenance, not a parallel social event log.
- Social checks do not mind-control NPCs. They produce a replayable
  `social_dc_source`, a `check_resolved`, and a bounded
  `social_disclosure_decision`; the accepted consequences still pass through the
  normal event validators.
- Player-facing recall is claim-shaped. Each claim carries source references,
  truth/rumor status, audience, and redaction state. A beautiful paragraph with no
  citations is not a valid recall answer.

Both sit on the event-sourced log. Event payloads are JSON and append-only, so a
new kind of world fact never requires a migration — you add an event type. Current
world state is a projection rebuilt from events, so when the shape needs to change,
you change the projection and replay rather than migrating live data.

Rationale for Postgres JSONB over a separate document store such as Mongo:

- One source of truth. Narrative and mechanical state update in the same
  transaction; a second store cannot do that and would split canon.
- JSONB already provides schemaless documents with GIN indexing when a query shape
  is known.
- pgvector retrieval lives in the same database as the state it indexes.
- PostGIS and pgRouting keep geography and route solving in the same consistency,
  backup, and transaction surface as the event log.
- One backup, one consistency model, one operational surface for a home deployment.

Schemaless does not mean schema-free. The schema relocates from the database to
versioned Pydantic / JSON Schema contracts validated on read and write. The
discipline shifts with it: tolerant readers, versioned event and entity contracts,
and in-code migration of document shapes. "Define how we work within the data" is a
real workstream, not the absence of one.

## Rules Strategy

The rules engine owns canonical game state. Models may propose actions and
explain results, but they do not directly edit state.

Rationale:

- Reduces hallucinated mechanics.
- Makes combat and resources testable.
- Preserves a stable boundary between narrative and game state.

## Model Strategy

Use a model gateway rather than hard-coding model SDKs in core systems.

Rationale:

- Local model quality and runtime support change quickly.
- VLM, text, speech, embedding, image, and video workloads need different
  hardware and latency profiles.
- The app should be able to swap vLLM, Ollama, llama.cpp, ComfyUI, Riva, or
  faster-whisper without rewriting orchestration logic.

## Portability Strategy

Dungeoneer must be shareable, not "only the author can run it." The home rig is
one deployment profile, not a hard dependency.

The differentiator is the system — orchestration, memory, rules — not model size,
and those parts are CPU-light and portable today. Only inference is hardware-
anchored. So a smaller deployment is the same portable core driving smaller,
cheaper inference, not a separate product.

Enforced from Phase 0:

- The core addresses capabilities through the gateway, never specific hosts, GPUs,
  or service locations.
- Topology — which GPU does what, the privacy boundary, the restricted-host offload —
  lives in deployment profiles, not orchestration logic.
- The core discovers available capabilities per profile and degrades gracefully
  when one is absent rather than hard-failing.

This keeps the ambitious home build as the flagship profile while preserving a
single-box and eventual mobile tier at near-zero cost. See
[Portability and deployment tiers](PORTABILITY.md).

## Hardware Strategy

Use the RTX 5090 for the resident live DM model and the RTX 4090 as the home
"conversation brain": STT, TTS, embeddings, and a small NPC background model. Do
not assume pooled VRAM across GPUs.

A restricted-host RTX 6000 Ada (48 GB, home LAN) handles battle-grid perception and
image/video generation. It is bound by a hard privacy boundary: no audio and no
conversation transcripts may be sent to it, only images and generated media. This
boundary is the reason audio, NPC text reasoning, embedding generation, and
dreaming all stay on the home machines regardless of available restricted-host
capacity. The boundary is intentionally conservative: conversation embeddings and
vector search stay home too.

The 6000 Ada is a narrow non-conversation model host, not a general application
node. It receives sanitized cropped map images, sanitized art/video briefs, and
model parameters. It does not get database access, event-log access, transcripts,
raw dream context, or broad LAN callbacks. See [Privacy boundary](PRIVACY_BOUNDARY.md).

The 6000 Ada absorbs the vision and media load, so the DGX Spark is now genuinely
optional. Add it only if home-side conversation compute (NPC background reasoning,
embeddings, or dreaming over the event log) outgrows the 5090 + 4090, since those
workloads cannot be offloaded across the privacy boundary.

The N150 network node can run always-on control-plane services and tiny
non-live-path classifiers if measured useful, but it should not be assumed
capable of live LLM, STT, TTS, or VLM work. See [Hardware topology](HARDWARE.md).

## Post-Session Dreaming Strategy

Run a slow consolidation stage after sessions. It can use heavier models,
longer context, and broader retrieval because it is outside the live latency
budget.

Rationale:

- Live play should optimize responsiveness and avoid overthinking every turn.
- Campaign continuity still needs deeper reflection: memento repair, world-state
  validation, faction consequences, and next-session prep.
- Slow jobs can run validators, compare projections, and produce reviewable state
  patches instead of mutating canon silently.

See [Post-session dreaming](POST_SESSION_DREAMING.md).

## Model Candidates To Test

These are candidates, not locked dependencies:

- Primary DM: strong text or multimodal model on the 5090. A text-first DM fed
  structured perception output is viable now that battle-grid perception is
  offloaded.
- Perception VLM: Qwen3-VL or Qwen3.5-class multimodal models through vLLM on the
  6000 Ada when supported; Gemma multimodal models as alternatives.
- Text-only fallback DM/NPC models: Qwen, Gemma, Llama, or other strong
  instruction models that fit the target GPU.
- Speech-to-text: faster-whisper large-v3 or large-v3-turbo; NVIDIA Riva if
  streaming latency and production speech tooling matter more.
- Text-to-speech: NVIDIA Riva for robust local streaming; Piper for lightweight
  local voices; higher-quality character voices as licensing and latency allow.
- Image generation: ComfyUI with FLUX-class workflows.
- Video generation: ComfyUI/Wan-class workflows for async cinematic output.

Every model candidate needs latency, memory, quality, and license testing before
being promoted into the default runtime profile.
