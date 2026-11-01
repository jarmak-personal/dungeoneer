# Lifecycle And Bootstrap

How a campaign comes into being and a session starts. Steady-state world modeling
lives in [Game world schema](GAME_WORLD_SCHEMA.md); this doc covers the cold-boot
and lifecycle layer that surrounds it — surfaced as a coherent gap by the game-start
system simulation runs.

## Worlds And Campaigns

A **world** is a setting and its base canon: the imported seed definition. It is
durable and shared. A **campaign** is a play instance *inside* a world, with its
own event log and its own projection.

- One world holds many campaigns: a main campaign, side one-shots, follow-ups, and
  parallel campaigns can all coexist in the same world.
- A campaign's canon is `replay(world definition) + replay(that campaign's events)`.
  Parallel campaigns share the world definition but diverge through their own
  events; they never cross-contaminate.
- Events are scoped: world-definition events are world-scoped (shared base canon);
  play events are campaign-scoped (private to that campaign). The event envelope
  carries both `world_id` and `campaign_id`.
- A campaign may declare `forked_from: { campaign, at_event }` to inherit a prior
  campaign's projection at a point as additional base canon — this is how
  follow-ups and "what if" parallels start from an existing state.

IDs: `world:greyhaven`, `campaign:greyhaven_main`, `campaign:greyhaven_oneshot_thieves`.

## Bootstrap Sequence

Cold boot runs in order. Each step emits typed events; nothing is canon except via
the event log.

1. **Ensure world.** Import a DWD seed pack into a world (`world.definition_imported`,
   world-scoped) or reuse an existing world. Validators run on import.
2. **Create campaign.** Create a campaign inside the world (`campaign.created`),
   optionally `forked_from` a prior campaign. One-shots and parallel campaigns are
   just campaigns, optionally tagged (`kind: one_shot`).
3. **Session zero** (first time for the campaign). A questionnaire produces two
   separate artifacts: the `dm_profile` (`dm_profile.seeded`) and the `safety_config`
   (`safety.configured`). See [DM profile](DM_PROFILE.md).
4. **Onboard devices and control.** Pair devices to the session
   (`device.paired`, with a role), and assign actor control to players
   (`control.assigned`). See "Device Pairing" and "Actors And Control" below.
5. **Start session.** `session.started` (campaign-scoped). Distinct from
   `dungeoneer session up`, which is infrastructure startup (see
   [Deployment](DEPLOYMENT.md)).
6. **Warmup pass.** A pre-session preparation phase, off the live path. See "Cold
   Start Warmup."
7. **Open first scene.** `scene.opened`; context assembly uses warmed material;
   opening narration is delivered (`message.delivered`, audience `table`); a scene
   card is pushed to the shared display (`display.content_pushed`).

## Session Zero Questionnaire

Session zero is a structured elicitation flow that compiles table answers into
`dm_profile.seeded` and `safety.configured`. The questionnaire is not a freeform
chat whose summary becomes policy.

```yaml
schema: dwd.session_zero_questionnaire.v1
campaign: campaign:greyhaven_main
surfaces:
  operator_console: required
  player_remotes: optional_private
  shared_display: public_summary_only
sections:
  - id: table_style
    visibility: table
    collection: table_discussion
    maps_to: dm_profile.seeded
  - id: rules_authority
    visibility: table
    collection: operator_confirmed
    maps_to: dm_profile.seeded
  - id: safety_lines_veils
    visibility: private_per_player
    collection: player_remote_or_operator_entry
    maps_to: safety.configured
  - id: final_review
    visibility: operator
    collection: operator_acceptance
    maps_to: [dm_profile.seeded, safety.configured]
```

Responses are structured and provenance-bearing:

```yaml
schema: dwd.session_zero_response.v1
questionnaire: questionnaire:greyhaven_main
respondent: table | player:iona | operator
visibility: table | player:iona | operator
answers:
  rules_authority: balanced
  lethality: standard
  narration_density: medium
  safety_rating: PG-13
  lines: ["no on-screen harm to children"]
  veils: ["torture fades to black"]
provenance:
  source_messages: [msg:s0_0011]
  operator_review: tool:session_zero_review_001
```

Rules:

- The operator console is the canonical review surface. Player remotes can collect
  private safety input; the shared display can show only non-private summary.
- Presets are shortcuts, not stored policy. A preset must expand to explicit
  `dm_profile` enum/knob values and `safety_config` fields before events are
  emitted.
- Public style/rules answers are table-visible. Private safety answers remain
  private to the operator/safety gate and are merged into the resulting
  `safety_config` without exposing who supplied which boundary.
- `dm_profile.seeded` and `safety.configured` are emitted only after final
  operator review. Later changes use `dm_profile.updated` or a new
  `safety.configured` version event; nothing silently mutates.

## Device Pairing

Devices join a session through session-scoped pairing (QR/token; see
[Tech stack](TECH_STACK.md)). This is home-LAN-scoped, not public auth.

- A device pairs with a declared **role**: `operator`, `player`, or
  `shared_display`. The role is carried in the pairing payload; the system does not
  guess it.
- Pairing emits `device.paired { device_id, role, session_id }`. The operator
  console may auto-pair as the operator device that ran `session up`.
- A `player` device is linked to a player identity. A `player:{id}` entity is the
  human player (the principal in `player:{id}` audiences and the controller in
  control edges); it is created on first pairing or selected if the player already
  exists in the campaign, and the device→player link is recorded on `device.paired`.
  One player identity may pair across sessions; devices are per-session.
- The shared display is a passive output surface and may be a read-only session URL.

## Actors And Control

Players control actors through control edges, not 1:1 ownership — a player commonly
controls a primary PC plus companions (a familiar, animal companion, summon, or an
NPC ally handed to them).

- `control.assigned { controller: player:X, actor: pc:Y | creature:Z | npc:W,
  role: primary | companion | temporary }`. The relationship is many-to-many:
  one player may control several actors, and control can be transferred or shared
  (co-control) when a table wants it.
- A PC enters play one of three ways: **select a pregen** (a `pcs/` entry authored
  in the world pack, or a prior character), **build a new one**, or **import** an
  existing character. Build and import are the player-facing path in "PC Authoring
  And Ingestion" below; all three end in `entity.created` (for new PCs) and
  `control.assigned` binding the actor to the player.
- PCs are actors and reuse the actor facets in the world schema, with a
  `rules_binding` to a character sheet owned by the rules engine. PC mechanical
  detail (ability scores, class, equipment) lives in rules state, not the narrative
  entity.

### PC Authoring And Ingestion

A player must never author their character in DWD YAML or maintain its mechanics by
hand. The world-definition format is an internal compile target; the player works in
natural terms and the system compiles, then asks the player to confirm.

- **Inputs (player's choice).** A guided builder (tap choices), free natural-language
  backstory (spoken or typed on the remote), or import of an existing sheet
  (VTT/PDF/prior PC). Any combination is allowed — the builder and import are just
  different front doors to the same compile step.
- **Compile, don't decide.** The system compiles those inputs into a *proposed* PC:
  the narrative entity plus backstory facts (provenance = the player), and a
  rules-engine character sheet. The compile transcribes and structures what the
  player gave; it never invents character meaning.
- **The player approves.** Nothing about the character becomes canon until the player
  confirms it, in plain language, on their remote. This confirmation is the review
  gate for character content — the one case where the reviewer is the player, not the
  operator, because the character is the thing the player owns. On approval:
  `entity.created` (PC + backstory facts) and the sheet is initialized in the rules
  engine (see [Rules engine](RULES_ENGINE.md)), then `control.assigned`.
- **Mechanics stay engine-applied.** After onboarding, the player makes *choices* (a
  level-up selection, a reaction) and the rules engine applies them through typed
  events. The player never edits a sheet or YAML to keep state in sync — bookkeeping
  is the system's job, the decisions are the player's.
- **Validate before commit.** Validate the approved narrative, the complete
  proposed sheet, selected schooling, and required pack definitions before
  creating the PC. If validation or initialization fails, emit no PC-creation
  or control-assignment events; explain the specific error and let the player
  revise or retry. Commit creation, initialized sheet, and control assignment
  atomically once validation succeeds.
- **Pregen schooling.** Aurevost pregens whose sheets do not specify schooling
  choices require their controlling player to choose and approve the two
  cantrips during onboarding; do not silently select them or assume they have
  already been initialized.

This is the authoring counterpart to the rules-engine guarantee that nothing
*constrains* a PC except rules-legal effects: nothing *defines* a PC except what the
player authored and approved. Pregens remain valid as authored seed content; the
build/import path is how a player brings their own character without touching the
internal format. For player-facing creation and advancement procedures and their
open content dependencies, see [Character play](CHARACTER_PLAY.md).

## Cold Start Warmup

The warmup pass resolves the cold-start tension: the live path forbids synchronous
loremaster forks (use pre-prepared material), but at cold boot no prepared material
exists yet. Warmup is where that material gets made — off the live path, before the
first scene, so the live budget is never paid synchronously.

Warmup responsibilities:

- **Build initial capsules from seed.** Create the first loremaster capsule(s) for
  the world/starting location and identity capsules for NPCs likely present, from
  the world definition — independent of dreaming (which has not run yet). See
  [Brain capsules](BRAIN_CAPSULES.md).
- **Build spatial projections from seed.** Load PostGIS/pgRouting projections for
  the opening region: location geometry, nearby places, ports, airship towers,
  territories, hazards, and route graph. See
  [Spatial and travel system](SPATIAL_TRAVEL.md).
- **Populate `prepare_likely`.** Assemble the prepared stance/context for the
  opening scene so the orchestrator consumes ready material, not a live fork.
- **Consume lore prepare requests.** Include open `lore.prepare_requested` records
  relevant to the opening or next likely scenes, refresh the target capsules, and
  mark each request prepared, superseded, or rejected.
- **Warm residency.** Ensure live-path models (DM, STT/TTS) are resident per the
  latency budget, so the first turn is not a cold load.
- **Assemble opening context.** Starting location facts, present actors, active
  threads/clocks visible to the DM — from world canon plus any `forked_from` base.

Warmup is a sibling of post-session dreaming: slow, off the live path, preparatory.
The same mechanism warms the *next* session at the end of a current one, so only the
very first session pays a true cold warmup. It may take seconds to minutes; it
blocks the first scene opening, not live play.

### Warmup Contract

The warmup pass is a named service with a defined contract, surfaced by system
simulation as the load-bearing piece of the bootstrap.

**Inputs.** `{ world_id, campaign_id, session_id, opening_scene_descriptor,
open_lore_prepare_requests }`.

**Opening scene is chosen before it is instantiated.** Warmup must prepare for a
scene that `scene.opened` has not yet created, so it targets an **opening scene
descriptor**, not a scene entity. The descriptor is resolved in order:

1. Operator override, if set.
2. Campaign metadata `opening_scene` (start location + planned participants).
3. World seed default start location.

A descriptor is `{ location, expected_pcs, expected_npcs }`. `expected_npcs` is
derived from the location's present/home NPCs (`location_presence` and
`location.npcs`), plus any operator pins. `scene.opened` later instantiates the
real scene entity from this descriptor and the warmed material.

**Ordering.** `session.started` → warmup (`session.warmed`) → `scene.opened`.
`scene.opened` blocks on `session.warmed`; live play does not. Infrastructure model
warming (the `session up` warm phase in [Deployment](DEPLOYMENT.md)) is a
*prerequisite*: narrative warmup begins only after infra health checks pass. The
two are distinct — infra warmup makes models resident; narrative warmup builds
context and capsules.

**Outputs.** A session-scoped **warm bundle** plus capsule snapshots:

```yaml
schema: dwd.warm_bundle.v1
session: session:greyhaven_001
opening_scene_descriptor: { location: loc:greyhaven.crooked_lantern, expected_pcs: [...], expected_npcs: [...] }
loremaster_capsules: [capsule:loremaster.world.greyhaven, capsule:loremaster.city.greyhaven]
npc_capsules: [capsule:npc.marra_vell]      # base-only at cold boot
opening_context: { location_facts: [...], visible_threads: [...], visible_clocks: [...] }
spatial_context: { nearby_locations: [...], ports: [...], routes: [...], territories: [...] }
prepare_likely_ref: capsule_snapshot_always_load   # prepared stance lives on the snapshot
emitted_by: session.warmed
```

Per-capsule `prepare_likely` material lives on the capsule snapshot's always-load
slot (see [Brain capsules](BRAIN_CAPSULES.md)); non-capsule opening material
(scene descriptor, location facts) lives in the warm bundle. The orchestrator reads
the warm bundle and the warmed capsules when it opens the first scene — a
synchronous read of already-prepared material, never a live build.

**Scene card.** The opening scene card is **templated by default** (location title
and atmosphere from the location entity — fast, model-free, always available) and
*optionally* enriched with generated art via `art_director`, which arrives async on
the shared display when ready and never blocks the opening narration. The card has
a schema (`dwd.scene_card.v1`) and the orchestrator emits `display.content_pushed`;
generated art additionally emits `asset.created`.

## DM-Initiated Narration

The orchestrator loop in [System scope](SCOPE.md) begins by ingesting player input,
but scene openings, recaps, and read-aloud text are DM-initiated turns with no
player input. The loop has an **initiation mode** for these: the orchestrator
composes and delivers narration without a preceding player utterance, under the
active `dm_profile` persona and `safety_config`.

## Lifecycle Events

Added to the event taxonomy (see [Game world schema](GAME_WORLD_SCHEMA.md)):

```text
campaign.created
session.started
session.ended
session.warmed
scene.opened
scene.closed
device.paired
control.assigned
control.released
dm_profile.seeded
dm_profile.updated
safety.configured
display.content_pushed
display.content_cleared
```

## Build Order

- Phase 0: world/campaign/session/scene entity kinds and ID namespaces; lifecycle,
  device, control, and display event types; the bootstrap sequence skeleton; the
  dm_profile and safety_config schemas.
- Phase 1: device pairing, PC onboarding and control assignment, session-zero
  questionnaire, the warmup pass building the first loremaster and NPC capsules, and
  DM-initiated opening narration.
