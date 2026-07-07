# Roadmap

## Phase 0: Foundation

- Initialize repository, app skeleton, formatting, tests, and Docker Compose.
- Add Postgres, object storage, and local dev configuration.
- Enable required Postgres extensions: PostGIS for spatial projections and
  pgRouting for travel-route solving.
- Add host inventory, deployment profiles, and `session up/down` cold-start
  scripts for the 4090, 5090, and optional 6000 Ada roles.
- Define event schemas for campaigns, sessions, messages, tool calls, entities,
  rules state, and generated assets.
- Define the game-world schema core: DWD import/export syntax, stable ID
  namespaces, base entity contract, facts, knowledge edges, visibility, patches,
  and validators.
- Define the spatial/travel schema core: spatial references, location spatial
  facets, route nodes/edges, travel profiles, territories, hazards, and validators.
- Define the lifecycle and bootstrap layer: world/campaign/session/scene/device
  entity kinds and namespaces; campaign, session, scene, device, control, and
  display lifecycle events; the bootstrap sequence; and the dm_profile and
  safety_config schemas. See LIFECYCLE.md.
- Define generic brain capsule contracts for identity capsules and forkable
  expert/loremaster capsules, including snapshot provenance.
- Define the system simulation run artifact/history schema and a small scenario
  suite for trace-driven architecture testing with a fresh/low-context simulator
  agent. Findings must be searchable by cause, disposition, status, affected doc,
  and expectation fingerprint. Simulations run from disposable broad repo copies
  with no prior run/finding outputs and no runner-only simulation docs; the
  top-level runner extracts results to an external history store.
- Implement append-only event store and replay.
- Add model gateway interfaces without binding to a specific model.
- Add a capability registry so the core discovers which services exist per
  deployment profile (DM, perception, STT, TTS, media) and degrades gracefully
  when one is absent, keeping orchestration free of host/topology assumptions.
- Add agent-run tracing, delivery-status semantics, and minimal latency stage
  instrumentation.
- Define the NPC tool gateway REST contract, direct service interface, and CLI
  test harness. Defer MCP until the REST/CLI contracts are stable and a concrete
  interoperability need appears.
- Define audience/visibility metadata for table-wide, player-private, DM-only,
  NPC-private, out-of-character, internal, aborted, and proposed messages.
- Define shared-display events for queued, visible, hidden, expired, and cleared
  public content.
- Define the privacy-boundary job schemas for sanitized map perception,
  sanitized image generation, and sanitized video generation.
- Define request-skill contracts that turn private campaign context into
  privacy-safe payloads for the restricted-host model service.

Exit criteria:

- A campaign can be created.
- A cold `session up` can start required services, run health checks, and print
  table/shared/player URLs.
- A session can store player and DM messages with delivered, aborted, internal,
  and proposed delivery/status metadata.
- Private messages can be addressed to one or more players without leaking into
  table-wide recall.
- Events can be replayed into current campaign state.
- A seed world pack can be imported, validated, inspected, and replayed into
  projections.
- Spatial projections for the seed region can be imported, validated, and queried
  for containment, nearby locations, route nodes, and route graph integrity.
- A capsule can be inspected and forked through a CLI stub with source snapshot
  provenance.
- At least three system simulation runs produce trace artifacts and findings for
  missing routes/contracts.
- A recorded turn includes enough timing data to compute text-path latency and
  later TTFA.
- Unsanitized restricted-host jobs are rejected by schema/validator checks.
- The core boots and runs a text turn on a single-host profile with small or stub
  models, proving the orchestrator does not depend on the home topology.

## Phase 0.4: Voice Chaos Spike

Prove the highest product-risk assumption before building voice-dependent
features: natural D&D table speech can be captured without push-to-talk or forced
slow speech. Splits into two independently runnable halves (see
[Voice chaos gate](VOICE_CHAOS.md)).

- 0.4a (input chaos, needs people not the AI): capture, diarization, speaker ID,
  overlap detection, and intent attribution under real table noise. A chaotic
  co-located proxy game (e.g. family Magic: The Gathering) is a valid stand-in;
  record multi-channel plus a room-mic baseline, with video for ground truth, and
  keep the labeled clip as a reusable benchmark.
- 0.4b (full duplex, needs the AI not many people): TTS playing into the room,
  echo cancellation keeping playback out of the transcript, and barge-in. Runs
  solo or with one other person.
- Compare single-mic and practical multi-channel audio; evaluate streaming ASR,
  diarization, speaker identification, overlap detection, and low-confidence
  clarification behavior.
- Treat speaker assignment and game-intent capture as the metric, not raw
  transcript prettiness.

Exit criteria:

- The best practical setup meets the gates in [Voice chaos gate](VOICE_CHAOS.md).
- 0.4a and 0.4b each pass on their own before the full integrated test.
- Consequential player intent is not silently assigned to the wrong player.
- If the gate fails, live voice is marked blocked and the project continues only
  on text/table-console paths until audio capture is solved.

## Phase 0.5: Voice Latency Spike

After the chaos gate passes, prove the latency assumption: live spoken play can
hit the TTFA budget on the real multi-machine topology.

- Stand up a throwaway end-to-end voice path: mic capture -> streaming STT -> a
  small resident LLM -> streaming TTS -> speaker.
- No game logic and no persistence beyond timing traces. The deliverable is the
  number, not the feature.
- Measure across the actual network hops between client, audio box, and DM box,
  not on a single machine.
- Compare warm-resident vs cold-load to confirm the residency assumption.

Exit criteria:

- Measured TTFA p50/p95 and barge-in latency on real hardware, compared against
  the budget in LATENCY.md.
- A go/no-go on the current machine and network split for live voice.
- If the budget is blown, the topology or hardware is revised now, not in
  Phase 3.

This is throwaway code and is allowed to be ugly. It exists only to de-risk the
voice loop before the text DM slice, rules engine, and NPC work are stacked on top
of an unvalidated latency assumption.

## Phase 1: Text DM Vertical Slice

- Implement DM orchestrator loop, including DM-initiated narration for scene
  openings (not only reactive-to-player turns).
- Implement the bootstrap flow: campaign-in-world creation, session zero seeding
  dm_profile and safety_config, device pairing, PC onboarding and control
  assignment (including companions), and the cold-start warmup pass that builds the
  first capsules and prepares the opening scene off the live path.
- Add basic retrieval over campaign history and structured entities.
- Add basic spatial inspection over the starting region: `where_is`, `nearby`,
  `contains`, `neighbors`, and `distance`.
- Add DWD-backed NPC, location, relationship, and basic thread facets for text
  context assembly.
- Add deterministic dice roller, core ability checks, and minimal typed state
  tools for facts, inventory, relationships, and resources.
- Add first NPC entity model, isolated NPC sub-agent runtime, and NPC activation
  flow.
- Add the first loremaster expert capsule for the campaign or starting location.
- Seed the first region's ports, nearby towns, faction waters, airship moorings,
  and the early boat's travel profile.
- Add simple web chat UI.
- Add a basic DM-controlled shared display for public text and uploaded/static
  handouts.
- Add first pass of player remotes for private DM messages and simple
  confirmations.
- Add recall and memento-promotion eval fixtures for the first NPC.
- Add `dm_profile` as first-class config (persona layer plus policy knobs), seeded
  by a session-zero questionnaire and read by the orchestrator.

Exit criteria:

- The DM can run a short scene with one or more NPCs.
- All messages, rolls, and state changes are persisted.
- An NPC can leave and re-enter later with remembered context.
- The NPC can only access information exposed through its scoped tools.
- The DM can answer basic geography questions about the starting region and nearby
  ports without relying on model guesswork.
- The DM can push public text or a handout to the shared display on demand.

## Phase 2: Rules Engine

See [Rules engine](RULES_ENGINE.md) for the full contract.

- Add character sheets, monster stat blocks, resources, inventory, and conditions.
- Wire PC sheet creation/import into onboarding: the engine initializes a
  rules-legal sheet from the player's choices or a parsed import (rejecting illegal
  input), and level-up/state changes are engine-applied, never player bookkeeping.
  See "PC Authoring And Ingestion" in [Lifecycle](LIFECYCLE.md).
- Add the `rules_referee` tool contract and typed rules tools (`ability_check`,
  `saving_throw`, `attack_roll`, `damage_roll`, `contested_check`) with structured
  result payloads; replace generic `rules.state_changed` with typed events.
- Add `dwd.combat_state.v1`, turn/round lifecycle events, and typed condition
  instances.
- Add the dice-source contract: digital roller first; physical-dice reading via the
  vision system (discrete capture + confidence/confirm) as the default expectation.
- Add the gated, logged `narrative_override` capability — enforced not prompted,
  with its absolute PC-immunity rule (overrides never target a player character).
- Add social resolution: attitude-anchored DCs, the degree-of-success ladder, and
  the outcome->disclosure bridge (`secret.revealed`, bounded knowledge transitions).
- Establish the world-state storage pattern: event-sourced JSONB projections under
  versioned contracts, with typed mechanical state owned by the rules engine.
- Add minimal faction, thread, clock, item, fact, and knowledge-edge contracts
  (typed where mechanical, JSONB where narrative) so later dreaming has real
  world state to advance.
- Add pgRouting-backed route tools for sea, airship, road, river, canal, and
  secret routes, including ETA, risk, season/weather modifiers, and travel events.
- Add the player/party knowledge model (implicit from presence+delivery; explicit
  edges only for private knowledge).
- Add the orchestrator live-decision layer (see
  [Orchestration](ORCHESTRATION.md)): hybrid input-intent classification, the
  parallel side-channel, loremaster live fallback, and player-facing capsule
  redaction.
- Add the override tell and the player "something's off" channel.
- Add regression tests for common combat and skill-check flows, scored against the
  saved simulation traces.

Exit criteria:

- The DM can run a small combat using canonical rules state and physical-dice reads.
- Model narration cannot directly mutate HP, positions, conditions, or resources.
- A `narrative_override` can never target a PC; NPC/world overrides are logged and
  profile-gated.
- A non-mechanical player question is answered on the side-channel without stalling
  an active turn.
- A faction, quest, or clock can be advanced through a typed event and rebuilt by
  replay.
- The party can choose a sea or airship route, receive ETA/risk assumptions, and
  advance world time through travel events.

## Phase 3: Voice Loop

- Add streaming speech-to-text.
- Add VAD, optional push-to-talk fallback, barge-in, and transcript correction.
- Add out-of-character handling: detect off-game tangents, default the DM to
  silence, resume on an address cue, and exclude OOC spans from canonical recall
  and memory.
- Add TTS playback and NPC voice profiles.
- Store audio clips and transcripts with provenance.
- Report TTFA and barge-in latency from the first end-to-end voice slice.

Exit criteria:

- A live voice session works end to end with acceptable latency.
- The transcript remains the canonical conversational record.
- Aborted speech is persisted for audit but excluded from player-facing recall.

## Phase 4: Map And Battle-Grid Vision

- Add image/frame ingestion.
- Crop captures to the battle grid at the source before frames are sent to the
  restricted-host perception GPU, so incidental room/people imagery stays on the home
  network.
- Add rejection of uncropped/full-frame perception uploads.
- Add grid calibration and token-position schema.
- Add VLM perception service, sized to exploit the 6000 Ada's 48 GB for a
  high-end perception model rather than a VRAM-constrained one.
- Host the perception service through the restricted-host vLLM endpoint behind the
  privacy-boundary gateway.
- Add reconciliation flow between perceived map and rules state.
- Add human confirmation for low-confidence or high-impact updates.
- Run map perception as a queued or isolated model workload that cannot evict the
  resident live DM model.
- Trigger map perception from explicit pre-action/post-action confirmation
  points, not continuous video scanning.

Exit criteria:

- The DM can inspect a battle-grid image and propose token positions.
- Confirmed positions update canonical combat state.

## Phase 5: Image And Video Generation

- Add async generation queue.
- Integrate ComfyUI workflows for portraits, places, items, monsters, and scenes.
- Add sanitized media-brief request skills for portraits, places, items, monsters,
  and scenes.
- Add provenance: sanitized prompt, full home-side source context, model, seed,
  and license metadata. Full source context stays home.
- Add video generation as async cinematic output, not live-response blocking.
- Display generated images, generated video, and generated text on the
  DM-controlled shared display when ready.

Exit criteria:

- The DM can request and display generated assets during or after a session.
- Long-running video jobs do not block live play.
- Media jobs sent to the 6000 Ada contain sanitized briefs only, with no raw
  transcript excerpts, private messages, or unrevealed secrets.

## Phase 6: Post-Session Dreaming

- Add session replay consolidation jobs.
- Add memento promotion/demotion and repair pipeline.
- Add capsule refresh for NPC identity capsules and forkable loremaster/expert
  capsules, including reviewable capsule diffs for high-impact changes.
- Add DM-profile adjustment proposals from session signals, surfaced for table
  review (never applied silently).
- Add world clocks, faction plans, rumors, consequences, and off-screen NPC
  actions.
- Add proposed state patches with validator and review flow.
- Add next-session prep bundles and unresolved question lists.

Exit criteria:

- Ending a session creates a dream job.
- The dream job produces validated memory/world updates or reviewable patches.
- Next session can preload prepared NPC stances and world context.

## Phase 7: Campaign-Scale Reliability

- Expand eval harness with saved scenarios.
- Add style evals that score DM behavior against the active profile (authority,
  lethality, story pressure, pacing).
- Expand model-output validators.
- Expand observability for latency, token usage, retrieval quality, and tool
  errors.
- Add backup/restore and campaign export.
- Add multi-player table UX.

Exit criteria:

- Long campaigns can be resumed reliably.
- Regressions in rules, memory, and orchestration are caught by tests/evals.

## Future Exploration (Non-Critical Path)

Parked ideas, not commitments. They do not affect whether Dungeoneer works and
should not pull focus from the numbered phases.

### Tactics Advisor

A combat simulator that helps the DM make better monster decisions. Built on the
deterministic rules engine, so it cannot exist before Phase 2. The approach is
Monte Carlo rollouts — sample outcomes per candidate action and report a
distribution — not linear programming; combat is a sequential stochastic game, and
LP fits only narrow single-turn slices.

Design constraints if it is ever built:

- Advisor, not autopilot. It outputs threat assessment ("this line likely TPKs in
  three rounds") to the orchestrator; the DM picks a dramatically appropriate
  action, often deliberately sub-optimal. Tuned for drama, not lethality.
- Background, not live-blocking. Rollouts run while players take their turns and
  have a recommendation ready by the monster's initiative, like NPC prepared
  stance. Full search does not fit the live rules-tool budget.
- Designated free-threading sandbox. Parallel pure-Python rollouts over shared
  immutable rules and stat blocks are the one workload where Python 3.14t
  genuinely helps, and where it beats multiprocessing (no IPC, no state pickling).
  The main app stays on the standard interpreter; free-threading is experimented
  with only here.
