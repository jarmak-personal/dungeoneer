# Game World Schema And Definition Language

## Purpose

Dungeoneer needs a persistent universe that is easy to author, inspect, repair,
extend, and replay. The world model must serve four audiences at once:

- The DM orchestrator, which needs compact, correct context.
- NPC agents, which need private, incomplete, character-specific knowledge.
- The rules engine, which needs deterministic mechanical state.
- The human maintainer, who needs a world that can be edited without becoming a
  fragile database exercise.

The answer is not "store lore in JSON" and not "put everything in vector search."
The answer is a small typed ontology, event-sourced changes, human-editable world
definition files, and explicit modeling of perspective.

## Core Principle

Separate five things that are often blurred together:

- **Event**: something recorded as having happened.
- **Projection**: current rebuilt state derived from events.
- **Definition**: authored seed material or reviewed world edits.
- **Belief**: what an actor, faction, or audience thinks is true.
- **Proposal**: a model-generated or dream-generated change awaiting validation.

Only accepted events and accepted definitions become canon. Projections are
rebuildable. Beliefs can be false. Proposals are not canon. This distinction is
what keeps long campaigns coherent.

## World Definition Format

Use a human-editable world definition format, provisionally called **DWD**
(`Dungeoneer World Definition`).

Authoring format:

- YAML for hand-authored seeds, reviewable patches, campaign exports, and CLI
  workflows.
- JSON for API payloads and event storage.
- Pydantic models as the canonical contract behind both.

This gives us readable files without maintaining two schemas.

Example world pack layout:

```text
worlds/greyhaven/
  world.yaml
  calendars.yaml
  predicates.yaml       # reviewed pack-scoped predicate vocabulary
  spatial/
    world_map.yaml
    sea_routes.yaml
    airship_routes.yaml
  regions/
    north_coast.yaml
  locations/
    greyhaven_city.yaml
    crooked_lantern.yaml
  factions/
    ash_ledger.yaml
    harbor_watch.yaml
  npcs/
    marra_vell.yaml
  pcs/
    kael.yaml          # optional pregen player characters
    iona.yaml
  items/
    oathknife.yaml
  threads/
    missing_tax_ship.yaml
  clocks/
    ash_ledger_coup.yaml
  sources/
    homebrew_notes.yaml
```

World packs are seed material. Importing one appends `world.definition_imported`
events. Later edits are events or reviewed patches, not silent file mutation.

Authored historical occurrences inside a seed are definitions, not pre-existing
event-log entries. A pack must not invent `event:*` IDs for history that was never
appended to a campaign/world log. Seed facts describe the occurrence in authored
terms and cite a `source:*`; import assigns the accepted
`world.definition_imported` event as runtime provenance. A durable `event:*` ID may
be cited only when that event actually exists in the imported event log.

## ID Syntax

Every durable object gets a stable, namespaced ID.

Recommended namespaces:

```text
world:        setting and base canon (the imported seed definition)
campaign:     a play instance inside a world (one-shot, main, follow-up, parallel)
session:      a single play session within a campaign
player:       a human player identity (controls one or more actors)
device:       a paired client device (operator, player, or shared_display)
calendar:     calendar/time system
region:       broad geography
loc:          location, site, room, zone, plane
spatial_ref:  map/projection/coordinate-space metadata
spatial_feature: geometry-backed feature projection
route_node:   travel graph node (port, anchorage, airship tower, waypoint)
route:        travel route/edge between route nodes
travel_profile: mode/vehicle profile for travel calculations
territory:    political, factional, or control area
hazard:       spatial hazard zone or named navigational danger
scene:        live scene or prepared scene
pc:           player character
npc:          non-player character
creature:     non-unique creature/monster instance
faction:      organization, culture, institution, family, guild
item:         item, artifact, document, vehicle
thread:       quest, mystery, unresolved plot pressure
clock:        advancing pressure, deadline, faction plan
fact:         canonical assertion
belief:       perspective-bound assertion
rumor:        transmissible uncertain claim
secret:       restricted fact or knowledge bundle
asset:        image, video, audio, handout
source:       source material reference
event:        durable event ID
```

IDs are lowercase slugs with optional local suffixes:

```text
npc:marra_vell
loc:greyhaven.crooked_lantern.cellar
faction:ash_ledger
clock:ash_ledger.coup
item:oathknife
```

Rules:

- IDs are never reused.
- Renames create aliases, not new IDs.
- Display names are mutable; IDs are not.
- Imported material keeps source provenance.
- Model-generated IDs must be reviewable before becoming permanent.

## Entity Model

Use one entity registry with typed facets rather than one table per narrative
kind. Most world objects share the same needs: identity, lifecycle, visibility,
links, provenance, tags, and notes.

Base entity fields:

```yaml
id: npc:marra_vell
kind: npc
schema: dwd.entity.v1
name: Marra Vell
aliases:
  - The Lantern-Keeper
lifecycle: active
visibility: dm_only
summary: Keeper of the Crooked Lantern, secretly indebted to the Ash Ledger.
tags: [greyhaven, tavern, criminal_pressure]
source_refs:
  - source:homebrew_notes#session_zero
created_by: human
```

Common lifecycle values:

```text
active
inactive
hidden
destroyed
dead
lost
retired
merged
deprecated
```

Facets add typed behavior:

```yaml
facets:
  actor: {}
  npc_profile: {}
  location_presence: {}
  relationships: {}
  knowledge: {}
  rules_binding: {}
```

This keeps the core stable while allowing richer domain-specific structures.

## Canonical Entity Kinds

Start with these kinds:

- `world`: top-level setting and base canon (the imported seed definition).
- `campaign`: a play instance inside a world, with its own event log and
  projection. Many campaigns (one-shots, follow-ups, parallel) can share a world;
  a campaign may `forked_from` a prior campaign at an event. See
  [Lifecycle and bootstrap](LIFECYCLE.md).
- `session`: a single play session within a campaign.
- `player`: a human player identity; controls one or more actors via control edges
  and is the principal in `player:{id}` audiences. Created/linked to a paired
  player device at onboarding (see [Lifecycle and bootstrap](LIFECYCLE.md)).
- `device`: a paired client device with a role (operator, player, shared_display).
- `region`: broad geographical, political, or planar area.
- `location`: durable place, from city to room.
- `spatial_ref`: map/projection/coordinate-space metadata. See
  [Spatial and travel system](SPATIAL_TRAVEL.md).
- `spatial_feature`: geometry-backed feature projection for a location, region,
  route, territory, hazard, or authored map layer.
- `route_node`: travel graph node such as a port, anchorage, airship tower, city
  gate, pass, or waypoint.
- `route`: travel route/edge such as a sea lane, river segment, road, airship
  corridor, canal, or secret path.
- `travel_profile`: mode/vehicle profile used to calculate route feasibility,
  speed, supply, and risk.
- `territory`: political, factional, cultural, or control area, often spatial.
- `hazard`: reef, storm belt, pirate waters, restricted airspace, monster range,
  planar instability, or other spatial danger.
- `scene`: temporary play context.
- `pc`: player character.
- `npc`: unique non-player character.
- `creature`: monster or non-unique actor instance.
- `faction`: organization, culture, family, guild, army, court, church.
- `item`: item, artifact, document, vehicle, treasure.
- `thread`: quest, mystery, open loop, player objective, narrative pressure.
- `clock`: advancing state machine for deadlines, faction plans, danger.
- `asset`: generated or uploaded media/handout.
- `source`: source material reference.

Avoid making a new top-level kind until the object has different lifecycle,
queries, or validation needs. Prefer facets and tags first.

## Facts

Facts are atomic assertions. They are not just prose notes.

Fact fields:

```yaml
id: fact:marra_owes_ash_ledger
schema: dwd.fact.v1
subject: npc:marra_vell
predicate: owes_debt_to
object: faction:ash_ledger
value:
  amount_gp: 800
  terms: "Due before the midsummer tide."
truth_status: canon
valid_from:
  world_time: greyhaven:1421-04-03
valid_until: null
source_event: event:s1_0042
visibility: dm_only
confidence: 1.0
```

Hand-authored fact files may provide shared provenance through a collection
envelope:

```yaml
schema: dwd.fact_collection.v1
source_refs:
  - source:homebrew_notes
facts:
  - id: fact:marra_owes_ash_ledger
    schema: dwd.fact.v1
    subject: npc:marra_vell
    predicate: owes_debt_to
    object: faction:ash_ledger
    truth_status: canon
    visibility: dm_only
    confidence: 1.0
```

Each contained fact inherits `source_refs` unless it declares a more specific
source. On import, the importer also records the accepted definition-import event;
the authored source and accepted event together satisfy provenance. Validators
reject high-impact seed facts with neither inherited nor per-fact source refs.

Truth status values:

```text
canon          accepted true world fact
superseded     was canon, replaced by later event
disputed       unresolved contradiction exists
false          explicitly disproven
unknown        placeholder or unresolved
```

Rules:

- Facts should be small enough to supersede individually.
- Facts should reference entities, not duplicate canonical fields.
- High-impact facts require provenance.
- If a fact changes, append a new event and supersede the old fact.
- Facts can be visible to different audiences through knowledge edges.

Predicates come from a **controlled, versioned vocabulary**, not free-form model
output. A subject-predicate-object store is a knowledge graph, and the classic
failure is predicate sprawl — `owes_debt_to` next to `is_indebted_to` next to
`has_debt_with`, none of which join or validate. New predicates are a reviewed
addition to the vocabulary; a model proposing a fact must use an existing
predicate or propose a new one for review, and validators reject unknown
predicates.

A world pack declares reviewed pack-scoped predicates in `predicates.yaml`:

```yaml
schema: dwd.predicate_vocabulary.v1
version: 1
source_refs: [source:homebrew_notes]
predicates:
  owes_debt_to: "Subject owes a quantified or described debt to object."
  controls_location: "Subject exercises effective control over object location."
```

Import validation merges the app-owned core vocabulary with this reviewed
pack-scoped vocabulary and rejects any fact whose predicate appears in neither.
Predicate meanings are stable within a vocabulary version; semantic changes require
a new predicate or vocabulary version, not an in-place reinterpretation.

## Beliefs, Rumors, And Secrets

Realistic worlds require imperfect information. Do not give every NPC direct
access to canonical truth.

Use knowledge edges:

```yaml
holder: npc:marra_vell
target: fact:marra_owes_ash_ledger
mode: knows
confidence: 1.0
acquired_from: event:s1_0042
can_share: false
secrecy: private
stale_after: null
```

Modes:

```text
knows
believes
suspects
heard_rumor
misunderstands
forgot
```

Secrets are knowledge bundles with access rules:

```yaml
id: secret:ash_ledger_blackmail
schema: dwd.secret.v1
summary: The Ash Ledger is blackmailing three harbor officials.
facts:
  - fact:ledger_blackmails_harbor_watch
holders:
  - npc:marra_vell
  - faction:ash_ledger
visibility: dm_only
reveal_conditions:
  - type: clue_discovered
    clue: item:blackmail_letters
```

Rules:

- Canonical truth and NPC knowledge are separate.
- A false belief can be useful state.
- Rumors are not facts until confirmed.
- Private player messages do not become NPC knowledge unless revealed through an
  accepted event.
- OOC spans never become facts, memories, beliefs, or retrieval entries.

**Default knowledge model.** Authoring an explicit knowledge edge for every NPC
and fact is not required and must not be. Knowledge edges are for the interesting
exceptions — a secret known, a rumor believed, something misunderstood or
forgotten. By default, an NPC is assumed to know public (`table`/`faction` as
applicable) facts attached to its present and home locations and to factions it
belongs to, plus its own private facts. Edges then *add* non-default knowledge or
*override* the default (e.g. an NPC who conspicuously does *not* know a public
thing). This keeps casual NPCs zero-authoring while letting important ones be
modeled precisely — consistent with the realism principle of simulating only what
creates causality.

**Player and party knowledge.** Player knowledge is modeled per-PC (same shape as
NPCs) so "what does *this* character know" is answerable; party knowledge is the
union over present PCs. To avoid edge sprawl on the common case, knowledge is
**implicit by default**: a PC knows any fact delivered to an audience that included
them while they were present (derived from scene presence + delivery — no edge
stored). **Explicit per-PC knowledge edges are only for asymmetric/private
knowledge** — a whispered secret, a solo check result, a one-player handout. So the
shared case (the party witnesses something together) costs nothing, and only the
interesting private case costs an edge. `world.query_party_knowledge(entity, pcs)`
unions present PCs' implicit + explicit knowledge and visibility-filters it; a
player-facing recall answer carries truth/rumor labels and citation IDs.

## Visibility And Audience

Every world object and field that can leak information needs audience metadata.

This is the **canonical definition** of the three orthogonal axes used across
Dungeoneer. They are independent dimensions and must not be collapsed into one
enum; a single message or object carries one value on each axis. Other docs
(`SCOPE` persistence model, `FRONTEND` private messages) reference this definition
rather than redefining it.

**Audience** — who may see it:

```text
table
player:{id}
players:[ids]
dm_only
npc_private:{id}
faction_private:{id}
internal
ooc
```

**Delivery** — whether it reached its audience (messages only): `delivered`,
`queued`, `expired`, `aborted`, `proposed`.

**Truth** — canonical status of an assertion (facts only): `canon`, `superseded`,
`disputed`, `false`, `unknown`.

Audience controls visibility. Delivery controls recall (only `delivered` enters
player-facing memory). Truth controls canon. A line can be `dm_only` + `aborted`,
or `table` + `delivered`; a fact is `dm_only` + `canon`. Keeping the axes separate
is what prevents, e.g., an undelivered draft being treated as something the table
heard, or a disputed rumor being treated as canon.

Visibility is not just UI. It controls:

- Retrieval.
- NPC activation.
- Dreaming.
- Shared-display output.
- Media/request sanitization.
- Export.
- Player-facing recap.

Default rule: if visibility is ambiguous, keep it private and ask for review.

## Time

Track both real session time and world time.

Event timing fields:

```yaml
recorded_at: "2026-06-20T22:14:03-04:00"
session_id: session:greyhaven_012
world_time:
  calendar: calendar:greyhaven
  value: "1421-04-03 late evening"
world_time_precision: scene
```

Precision values:

```text
instant
round
scene
day
season
unknown
```

Rules:

- Do not pretend to know exact world time when the fiction has not established it.
- Use relative time when appropriate.
- Faction clocks and travel can advance world time.
- Mechanical combat time is strict and owned by the rules engine.
- Narrative world time is flexible but still event-sourced.

## Locations

Locations need hierarchy, graph links, and spatial facets. The spatial/travel
system is required because geography, sea travel, and airship travel are core
campaign intelligence. PostGIS and pgRouting hold queryable projections over
accepted definitions/events; they are not a second source of canon. See
[Spatial and travel system](SPATIAL_TRAVEL.md).

Example:

```yaml
id: loc:greyhaven.crooked_lantern
kind: location
schema: dwd.location.v1
name: The Crooked Lantern
parent: loc:greyhaven.docks
summary: A salt-stained tavern built into an old customs house.
scale: building
access:
  public: true
  restrictions: []
exits:
  - to: loc:greyhaven.docks
    mode: walk
    travel_time: "2 min"
  - to: loc:greyhaven.crooked_lantern.cellar
    mode: stairs
    hidden: true
atmosphere:
  sights: ["green-glass lamps", "wet cloaks", "ledger marks carved under tables"]
  sounds: ["dock bells", "low dice chatter"]
  smells: ["brine", "lamp oil", "pepper stew"]
security:
  danger_level: 2
  controlling_faction: faction:ash_ledger
facets:
  spatial:
    spatial_ref: spatial_ref:greyhaven_region_map
    representation: polygon
    precision: approximate
    feature: spatial_feature:greyhaven.crooked_lantern
    route_nodes:
      - route_node:greyhaven.docks.crooked_lantern
```

Rules:

- `parent` models containment.
- `exits` model traversal.
- Spatial facets model queryable map placement, containment, adjacency, distance,
  and route graph anchors.
- A place can be known publicly while some exits, rooms, or hazards are secret.
- Location detail should be layered: summary first, sensory details second,
  secrets only through scoped knowledge.

## Spatial And Travel

Spatial and travel contracts live in [Spatial and travel system](SPATIAL_TRAVEL.md)
and are required parts of the world model.

Required DWD/projection concepts:

```text
spatial_reference
spatial_feature
route_node
route_edge
travel_profile
travel_plan
territory
hazard_zone
```

Required travel modes:

```text
walk
road
horse
river
sea
airship
canal
secret
magical
```

Rules:

- The event log and DWD definitions are canon; PostGIS/pgRouting tables are
  rebuildable projections.
- Distance, travel time, and risk are separate values.
- "Far away" is mode-aware: a place can be close by airship, slow by sea, and
  effectively unreachable by road.
- Sea and airship routes carry constraints, hazards, seasonality, and faction
  visibility.
- Route proposals are not canon until chosen or accepted; travel execution emits
  events.
- Battle-grid/tactical position remains rules-owned. Spatial travel may anchor a
  scene or battle map, but the rules engine owns combat positions.

## Actors

Actors include PCs, NPCs, and unique creatures. Actor state spans narrative,
social, and mechanical domains.

NPC example:

```yaml
id: npc:marra_vell
kind: npc
schema: dwd.npc.v1
name: Marra Vell
facets:
  npc_profile:
    public_role: Keeper of the Crooked Lantern
    voice: "Low, careful, dry humor when nervous."
    values: [survival, loyalty_to_staff, debt_avoidance]
    flaws: [risk_averse, lies_by_omission]
    current_intention: "Keep the party away from the cellar until the ledger men leave."
    fears:
      - faction:ash_ledger
    goals:
      - id: goal:marra_clear_debt
        priority: high
        visibility: npc_private:npc:marra_vell
  location_presence:
    current_location: loc:greyhaven.crooked_lantern
    routine:
      - when: evenings
        location: loc:greyhaven.crooked_lantern
      - when: dawn
        location: loc:greyhaven.fishmarket
  rules_binding:
    stat_block_ref: rules:npc.commoner
```

Rules:

- Actor goals are not all public.
- NPC private intention is not chain-of-thought. It is concise state.
- Current location may be exact, approximate, or unknown depending on evidence.
- Mechanics live in rules-owned structures; the narrative entity references them.

**PCs and control.** PCs are actors and reuse the actor facets above, plus a
`rules_binding` to a character sheet owned by the rules engine (ability scores,
class, equipment live in rules state, not the narrative entity). Players control
actors through control edges, not 1:1 ownership: one player commonly controls a
primary PC plus companions (a familiar, animal companion, summon, or a handed-off
NPC). Control is a many-to-many `control.assigned` relationship
(`controller: player:X, actor: pc:Y | creature:Z | npc:W, role: primary |
companion | temporary`), supporting companions, co-control, and handoff. Onboarding
and the full control model are in [Lifecycle and bootstrap](LIFECYCLE.md).

## Relationships

Relationships are directional and multi-axis. A single "attitude" score is too
flat for a believable world.

Example:

```yaml
id: rel:marra_vell->ash_ledger
schema: dwd.relationship.v1
source: npc:marra_vell
target: faction:ash_ledger
axes:
  affinity: -40
  trust: -80
  fear: 75
  debt: 90
  respect: 10
  suspicion: 60
summary: Marra hates the Ledger but fears defaulting more.
source_events:
  - event:s0_ledger_debt_seed
  - event:s1_0042
visibility: dm_only
```

Rules:

- Relationships are directional.
- Relationship changes come from events.
- Use axes sparingly and consistently.
- Relationship summaries are projections and can be regenerated.
- NPCs can have beliefs about relationships that differ from canon.

**Write tool.** Relationship changes are made through a typed
`relationship.update` orchestrator tool (not an NPC tool — NPCs only propose). It
takes `source`, `target`, `axis_changes`, `reason`, and provenance
(`source_message`, `tool_call`), validates that axes are known and within range,
and emits `relationship.changed`. The live-vs-dream threshold: an in-scene nudge
driven by something that happened at the table (a direct promise → a trust bump)
commits live through this tool; a change that would flip loyalty or long-term
stance is an inference and goes through dreaming as a reviewable patch. This
follows the general live-vs-dream rule in "Live Versus Dream Commits."

## Factions

Factions make the world move when PCs are not looking.

Example:

```yaml
id: faction:ash_ledger
kind: faction
schema: dwd.faction.v1
name: The Ash Ledger
public_face: A lending house for sailors and small merchants.
values: [profit, leverage, secrecy]
methods: [debt, blackmail, arson, legal_pressure]
resources:
  coin: high
  muscle: medium
  political_cover: medium
  public_trust: low
territory:
  - loc:greyhaven.docks
leaders:
  - npc:sevran_oke
enemies:
  - faction:harbor_watch.clean_hands
visibility: table
```

Factions should be advanced by clocks and events, not by vague "the world reacts"
prompts.

**Operational stance.** A faction's mutable posture — what it is currently
committed to, pursuing, or set against — is canon only as facts and relationships,
the typed spine that drives history, query, validation, and review routing. A
declared course (the Asha commit to a strike) is a fact using a reviewed stance
predicate (`adopts_operational_stance`); a directional posture toward another
entity (now hostile to a rival) is a `faction`→target relationship with axes. A
change that flips a faction's standing or long-term course is high-impact and goes
through dreaming as a reviewable patch, per "Live Versus Dream Commits"; a routine,
table-driven nudge can commit live. Authors and agents may *also* keep descriptive
fields on the entity (the prose `stance` block on a private faction, `dm_notes`,
ad-hoc context someone thought worth recording) — these are regenerable context,
bound by the visibility rule below, and never the sole home of a load-bearing
claim. New descriptive fields can accrue over time without schema churn; whatever
carries causal or canonical weight still belongs in facts and relationships.

A table-visible faction definition must not embed `private_truth`, hidden stances,
or secret capabilities as unscoped prose. Put those claims in atomic facts and
secret bundles with `dm_only`, `faction_private:{id}`, `npc_private:{id}`, or
`internal` audience as appropriate. `private_truth` is permitted only when the
containing entity itself is private to an audience that may receive every field.

## Clocks

Clocks are structured pressure. They are the preferred realism mechanism for
off-screen plans, deadlines, escalating danger, rituals, investigations, and
faction maneuvers.

Example:

```yaml
id: clock:ash_ledger.coup
kind: clock
schema: dwd.clock.v1
name: Ash Ledger Takes The Harbor Watch
owner: faction:ash_ledger
status: active
segments:
  current: 2
  max: 6
stakes: The harbor watch becomes a Ledger-controlled police arm.
advance_triggers:
  - trigger: session_ends_without_interference
    amount: 1
  - trigger: party_publicly_embarrasses_harbor_watch
    amount: 1
  - trigger: party_exposes_blackmail_letters
    amount: -2
outcomes:
  complete:
    - create_fact: fact:harbor_watch_compromised
    - unlock_thread: thread:clean_hands_rebellion
visibility: dm_only
```

Rules:

- Clocks must have owners, stakes, and outcomes.
- Clocks advance through typed events.
- Clock changes are reviewable when high impact.
- Dreaming can propose clock movement, but validators and review decide.

## Threads

Use `thread`, not only `quest`. Threads include mysteries, debts, relationships,
threats, open loops, player promises, and plot pressures.

Example:

```yaml
id: thread:missing_tax_ship
kind: thread
schema: dwd.thread.v1
name: The Missing Tax Ship
status: active
summary: A crown tax ship vanished before docking at Greyhaven.
stakes:
  public: "The city may face royal reprisal."
  hidden: "The Ash Ledger redirected the ship to buy the harbor watch."
participants:
  - faction:ash_ledger
  - faction:harbor_watch
  - npc:marra_vell
leads:
  - clue:item:blackmail_letters
  - loc:greyhaven.crooked_lantern.cellar
resolution_conditions:
  - expose_the_ship_manifest
  - recover_the_tax_chest
  - broker_coverup
visibility: dm_only
```

Rules:

- Threads track pressure and stakes, not just tasks.
- Threads can resolve in multiple ways.
- Hidden stakes must not leak into player summaries until discovered.
- Leads and clues have their own reveal state.

## Items

Important items need custody, rules binding, and history.

Example:

```yaml
id: item:oathknife
kind: item
schema: dwd.item.v1
name: Oathknife
category: weapon
summary: A narrow ceremonial dagger used to seal dockside contracts.
current_holder: npc:marra_vell
current_location: loc:greyhaven.crooked_lantern.office
rules_binding:
  item_ref: rules:item.dagger
significance:
  - thread:missing_tax_ship
custody_history:
  - holder: faction:ash_ledger
    from_event: event:s0_seed
  - holder: npc:marra_vell
    from_event: event:s1_0042
visibility: dm_only
```

Rules:

- Ordinary inventory can stay in rules tables.
- Narrative-significant items become entities.
- Custody changes are events.
- Generated item art is an asset linked to the item, not the item itself.

## Scenes

Scenes are temporary play contexts. They gather the currently relevant subset of
the world.

Scene fields:

```yaml
id: scene:s12_crooked_lantern_cellar
kind: scene
schema: dwd.scene.v1
location: loc:greyhaven.crooked_lantern.cellar
participants:
  pcs: [pc:kael, pc:iona]
  npcs: [npc:marra_vell]
  creatures: []        # non-unique creature/monster instances in combat scenes
active_threads:
  - thread:missing_tax_ship
active_clocks:
  - clock:ash_ledger.coup
visibility: table
```

Scene context is assembled from current location, participants, visible facts,
known private facts, relevant threads, active clocks, and recent events. The scene
is not the source of truth.

## Events

Events are the source of truth for change.

Event envelope:

```yaml
id: event:s12_0048
schema: dwd.event.v1
type: relationship.changed
campaign_id: campaign:greyhaven
session_id: session:greyhaven_012
actor: pc:iona
world_time:
  calendar: calendar:greyhaven
  value: "1421-04-03 late evening"
visibility: table
payload:
  relationship: rel:marra_vell->pc:iona
  axis_changes:
    trust: 15
  reason: "Iona promised to hide Marra from the Ledger."
provenance:
  source_message: msg:s12_0172
  tool_call: tool:relationship_update_003
```

Event categories:

```text
world.definition_imported
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
entity.created
entity.updated
fact.asserted
fact.superseded
knowledge.learned
knowledge.revealed
relationship.changed
location.changed
spatial.feature.updated
route.edge.updated
route.opened
route.closed
travel.started
travel.progressed
travel.completed
travel.interrupted
territory.changed
hazard.changed
weather.changed
item.transferred
clock.advanced
thread.updated
check_resolved
hp_changed
condition_applied
condition_removed
initiative_set
position_changed
turn.started
turn.ended
round.started
round.ended
rules.override_applied
secret.revealed
asset.created
message.delivered
message.delivered_to_npc
message.observed
dream.patch_proposed
patch.accepted
patch.rejected
```

Lifecycle, device, control, and display events (the first block above) are defined
in [Lifecycle and bootstrap](LIFECYCLE.md). World-definition events are
world-scoped; all others are campaign-scoped. The event envelope carries both
`world_id` and `campaign_id`.

**Messages versus events.** Raw inbound utterances (a player speaking or typing)
are rows in the `messages` / `message_visibility` tables, not events. There is no
`message.received` event. An event is recorded only when an utterance *reaches an
audience* and may change state: `message.delivered` (reached its player/table
audience), `message.delivered_to_npc` (an in-fiction utterance reached an NPC and
may update that NPC's knowledge), and `message.observed` (a content-free shell
recording that an observable act — e.g. a whisper — was witnessed, carrying no
text). Inbound capture lives in the message tables; state change lives in events.

Rules:

- Events are append-only.
- Events are typed and versioned.
- Model narration cannot directly create events that mutate canon.
- Every state-changing event records provenance.
- Replaying an event range must rebuild the same projection.

**Ordering.** Replay is ordered by append sequence (a monotonic per-campaign
event sequence), not by `world_time`. `world_time` is descriptive metadata: it is
fuzzy (precision down to season), can be unknown, and can move backward
(flashbacks, retcons). Determinism depends on a stable append order; world time
never drives projection rebuilding.

## Private In-Fiction Messages And Whispers

A player can address an NPC privately in fiction — "I quietly tell Marra I'll hide
her from the Ledger." This needs an explicit route, surfaced by system simulation.

- **Players compose, the orchestrator delivers.** A player remote may direct a
  private in-fiction utterance *at* an NPC, but it is always routed through the DM
  orchestrator, which arbitrates delivery. Players never write NPC memory directly;
  the orchestrator mediates, consistent with "NPCs are proposed-and-arbitrated,
  never directly mutated."
- **Delivery produces a knowledge transition, not canon truth.** On accepted
  delivery, emit `message.delivered_to_npc`, which sources a `knowledge.learned`
  edge: the NPC now knows *that the player said it*, held as belief/claim, not as
  canonical truth. A PC asserting hidden-context knowledge privately is a claim the
  NPC may believe, suspect, or dismiss — the system does not validate the PC's
  statement into canon, and the NPC does not gain canon knowledge, only "heard X
  claimed."
- **The observable shell is content-free.** If the act is witnessable, emit a
  separate `message.observed` event (audience: nearby/table) carrying no text —
  other PCs may notice a whisper happened without receiving its words. Content
  stays private; only the observable act is shared. Keeping these two events
  separate is what prevents a "private" whisper from either leaking its text or
  being invisible when it should be noticeable.

## Patches

Human edits, dream output, and model-proposed world changes should use the same
patch format.

Example:

```yaml
schema: dwd.patch.v1
id: patch:dream_s12_marra_trust
status: proposed
proposed_by: dream_job:dream_s12
summary: Promote Iona's promise to a Marra memento and adjust trust.
changes:
  - op: assert_fact
    fact:
      subject: npc:marra_vell
      predicate: trusts_more
      object: pc:iona
      value: {amount: 15}
  - op: add_memento
    npc: npc:marra_vell
    memento:
      title: "Iona promised protection from the Ledger"
      source_event: event:s12_0048
review:
  required: true
  reason: relationship_change
```

Rules:

- Patches are not canon until accepted.
- Accepted patches append events.
- Rejected patches stay as audit records.
- High-impact patches require review.
- Low-risk deterministic repairs can be auto-applied only after validators pass.

### Patch Conflicts

Dreaming and live inference can produce patches that target the same state from
the same replay base in incompatible ways — most often a clock advanced in two
directions by two triggers read off one session (e.g. `clock:the_hand_passes` +1
from `succession_conflict_disrupts_asha_work` and -1 from
`credible_new_candidate_or_structure_emerges`). Such patches form a **conflict
set**.

- Two patches conflict when they write the same field of the same entity from the
  same base state and are not independently composable (opposite or mutually
  exclusive deltas/outcomes).
- **No member of a conflict set may auto-apply.** Conflict detection overrides the
  auto-apply tier: the whole set escalates to operator review as mutually-exclusive
  candidates, each carrying its trigger, evidence events, and proposed effect.
- The operator resolves the set by accepting one member (the others become rejected
  audit records), rejecting all, or supplying a merged resolution (e.g. the two
  ticks cancel to no net change), recorded as its own patch that cites both
  originals.
- Resolution is appended as events; rejected members remain as audit records.
  Nothing in a conflict set wins silently by application order.

Independently composable patches that merely touch the same clock are not a
conflict — two distinct, same-direction triggers may each legitimately advance it.
*(Open question: whether same-direction ticks from distinct triggers read off one
replay slice should stack or be deduplicated needs a deterministic rule. Until it
is defined, treat only incompatible writes as conflicts and surface same-field
same-direction stacks for review.)*

### Review Authority

Review is not the players' job. Players should think about playing; world
bookkeeping is not their cognitive load. Three tiers decide who, if anyone, gates
a patch:

- **Auto-apply (no human).** Validators pass and the change is low-risk and
  deterministic (projection repairs, mechanical consequences, routine clock ticks
  with defined outcomes). Applied and logged. This is the default and should cover
  most dream output.
- **Operator review (host, asynchronous).** High-impact changes to world canon —
  faction turns, retcons, new major facts, capsule rewrites that shift an NPC's
  loyalties. Reviewed by the host between sessions, never as a mid-play
  interruption. The host is whoever runs Dungeoneer; in practice one person takes
  that role, and it is reasonable to assume someone willing to stand up the system
  will answer its questions. In the no-human-DM tier this queue is that person's
  async inbox, not a table prompt. Players are not involved.
- **Player involvement (rare, in-fiction).** Players are pulled in only for things
  that touch their own characters' agency or cross a safety boundary — and even
  then through the *existing* consent/safety mechanics, not a "approve this patch"
  dialog. PC-facing consequences are normally surfaced **through play**: the DM
  narrates them as fiction, not as a review request. A purely background change a
  player does not know about never requires their confirmation. One thing this tier
  does *not* cover is character authorship: creating, importing, or leveling a PC is
  the player's explicit approval over their *own* character (see PC onboarding in
  [Lifecycle](LIFECYCLE.md)), not a world-patch dialog — it is the player exercising
  agency, not bookkeeping imposed on them.

The dividing line is knowledge and agency, not impact: a huge off-screen faction
move is operator-or-auto because players do not know about it yet; a change that
would rewrite what a player's character did is the rare in-fiction/consent case.

Operator load is a necessary cost, not a designed-in virtue. We accept that the
host carries some review burden because canon integrity demands a human in the
loop somewhere — but the goal is always to minimize it: auto-apply should widen as
validator confidence grows, and the review queue should stay short. When a patch
is specific to one player (a question only Player A can answer), the **local**
message system may route it to that player rather than the host. This is a
convenience over the existing on-LAN message routing, not an internet-enabled
feature; the host remains the default and the fallback.

### Live Versus Dream Commits

Live play commits canon in real time through typed tools: `knowledge.revealed`,
`relationship.changed`, `item.transferred`, and the typed rules events
(`check_resolved`, `hp_changed`, `condition_applied`/`condition_removed`,
`initiative_set`, `position_changed`, `rules.override_applied`). These are
low-stakes, in-budget, and validator-checked at write time — not queued for
review. Dreaming is where *proposed* higher-order changes (mementos, clock
movement, new facts, capsule refreshes) are generated as patches and routed
through the review tiers above. Rule of thumb: if it happened at the table, it is
committed live; if it is an inference or off-screen consequence derived after the
fact, it is a dream patch.

## Database Shape

Use Postgres as the single durable store. Start with tables for high-value query
surfaces and JSONB for flexible facets.

Recommended early tables:

```text
events
messages
message_visibility
entities
entity_aliases
entity_facets
facts
knowledge_edges
relationships
clocks
threads
assets
sources
brain_capsules
capsule_snapshots
embeddings
agent_runs
tool_calls
patches
```

Table roles:

- `entities`: stable ID, kind, lifecycle, display name, summary, tags.
- `entity_facets`: JSONB typed facet documents, versioned by schema.
- `facts`: atomic canonical assertions and their lifecycle.
- `knowledge_edges`: who knows, believes, suspects, or misunderstands which fact.
- `relationships`: directional social projection, rebuilt from events.
- `clocks`: pressure state, owner, stakes, current segments, outcomes.
- `threads`: open loop and quest/mystery state.
- `brain_capsules`: stable capsule identity, kind, subject, visibility, and
  current version pointer.
- `capsule_snapshots`: versioned always-load payloads, source event ranges,
  retrieval hints, and provenance for NPC identity and expert/loremaster capsules.

Do not store every field in JSONB just because it is narrative. Anything that is
frequently joined, filtered, permissioned, or validated deserves a table or
indexed column.

## Authoring Syntax Guidelines

World files should be easy to maintain by hand.

Rules:

- One major entity per file.
- Use IDs for references, not names.
- Keep summaries short.
- Put rich prose under explicit fields like `atmosphere`, `description`,
  `private_truth`, or `dm_notes`.
- Never hide canonical state only in prose.
- Put secrets in `secret` or private fact/knowledge structures.
- Prefer tags for loose grouping; prefer typed fields for behavior.
- Generated material must be proposed as a patch, not silently merged.

Bad:

```yaml
notes: "Marra owes money to the Ash Ledger and hates them but is scared."
```

Good:

```yaml
facts:
  - subject: npc:marra_vell
    predicate: owes_debt_to
    object: faction:ash_ledger
relationships:
  - source: npc:marra_vell
    target: faction:ash_ledger
    axes: {fear: 75, trust: -80, affinity: -40}
```

## Context Assembly

The world schema exists to assemble good context quickly.

For a live scene, retrieve:

- Current scene card.
- Current location public facts and table-visible sensory details.
- Present actors and visible state.
- Active threads and clocks visible to the DM.
- Recently delivered messages.
- Player-private messages only for intended recipients.
- Rules state needed for immediate adjudication.
- NPC prepared stances, not raw hidden deliberation.

For an NPC activation, retrieve:

- NPC immutable base profile.
- Always-load mementos.
- Current intention summary.
- Facts the NPC knows or believes.
- Relationship projection from the NPC's perspective.
- Recent direct interactions.
- Visible scene details.
- Tool grants.

For a loremaster/expert capsule fork, retrieve:

- Capsule domain brief.
- Curated canonical summary.
- Active facts, threads, clocks, and unresolved questions in scope.
- Source references and contradiction notes.
- Focused supporting events and definitions.
- Tool grants for inspection, citation, and patch proposal.

For dreaming, retrieve:

- Frozen session event range.
- Pre-session and post-session projections.
- Delivered messages only.
- Active clocks and threads.
- Relevant NPC memories and relationship edges.
- Proposed patches and validation failures.

## Validators

Minimum validators:

- No dangling IDs.
- No reused IDs.
- No circular location containment.
- No location containment that contradicts spatial containment unless the spatial
  representation is explicitly approximate, symbolic, or unknown.
- No impossible current holder/current location contradictions.
- No actor in two exact locations at the same world time unless explicitly
  magical or approximate.
- No private fact leaked into table-visible summary.
- No NPC knowledge edge for a fact the NPC could not have learned without a
  source event or seed definition.
- No NPC knowledge gained from a private in-fiction message without a
  `message.delivered_to_npc` event; the resulting edge is a belief/claim, not canon.
- No `message.observed` event carrying message content (it is a content-free shell).
- No relationship change without a `relationship.update` tool call and provenance.
- No route edge with dangling route nodes, incompatible spatial references, missing
  travel mode, missing cost/duration model, or missing provenance.
- No travel event moving an actor or vehicle along an impossible route without an
  explicit override or magical exception.
- No rules-owned field mutated by narrative patch.
- No clock segment outside range.
- No thread resolution without accepted event.
- No memento without provenance: its `source_event` must reference an accepted,
  delivered event of a qualifying type (`message.delivered_to_npc` for a promise
  made to the NPC, `item.transferred`, `relationship.changed`, `check_resolved`,
  `secret.revealed`, and similar), or it must be a reviewed seed memento. A raw
  inbound `messages` row is not provenance.
- No member of a patch conflict set auto-applied: incompatible writes to the same
  field from the same base escalate together to operator review.
- No OOC event included in recall, embeddings, NPC memory, or dreaming.
- No restricted-host media/perception payload containing private source text.

These should run in CI/evals later and in the CLI from day one:

```bash
dungeoneer world validate --campaign greyhaven
dungeoneer world inspect npc:marra_vell
dungeoneer world graph --around faction:ash_ledger
dungeoneer world patch review patch:dream_s12_marra_trust
dungeoneer world replay --campaign greyhaven --to event:s12_0048
```

## Realism Model

Do not simulate everything. Simulate what creates causality.

Realism comes from:

- Actors with goals, fears, resources, relationships, and constraints.
- Factions with clocks, resources, territory, methods, and leaders.
- Locations with access, hazards, controlling powers, and hidden spaces.
- Items with custody and significance.
- Threads with stakes and multiple resolution paths.
- Beliefs that can be wrong, stale, private, or revealed.
- Time passing and clocks advancing when the party ignores things.

Avoid:

- Full economy simulation before it affects play.
- Omniscient NPC updates.
- Treating every rumor as truth.
- Long prose notes that contain hidden state.
- Quest flags that force one intended solution.
- Silent dream changes.

The world should be lazy but causal: define enough structure that consequences
can be replayed, explained, and continued.

## Build Order

Phase 0:

- Define ID syntax, base entity contract, event envelope, visibility, facts,
  knowledge edges, patches, and validators.
- Add YAML import/export for seed packs.
- Add CLI `world validate`, `world inspect`, and `world replay` skeletons.

Phase 1:

- Implement NPC, location, relationship, and basic thread facets.
- Use the schema for text-only DM context assembly and NPC activation.

Phase 2:

- Add rules bindings, items, combat-related location/battle state, and stricter
  mechanical/narrative mutation boundaries.
- Add faction, clock, and thread advancement through typed events.

Phase 6:

- Dreaming produces patches against these contracts.
- Add review UI/CLI for proposed mementos, clock movement, relationship updates,
  and thread changes.

Phase 7:

- Add campaign export/import, schema evolution tests, contradiction detection,
  graph visualization, and long-campaign eval fixtures.
