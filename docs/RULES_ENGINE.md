# Rules Engine

The rules engine owns canonical mechanical state. Models propose and explain;
typed tools make the changes. It is deterministic, inspectable, and the boundary
that keeps narrative out of mechanics. This doc defines its tool surface, dice
sourcing, typed events, the combat model, social resolution, the
`narrative_override` capability, and the rules-pack boundary.

## Position — How, Not What

The rules engine is *how the DM implements the rules*, not *what system the table is
playing*. That is the silent assumption every real table already makes: a rulebook
underdetermines play, and the table's actual ruleset is the book plus a DM who
adjudicates it consistently. We split that into three owned, typed, swappable layers.

- **Engine — the adjudication procedure and resolution grammar.** When a check is
  called: intent → typed check spec, DC-selection procedure, the degree ladder, dice
  sourcing, applying typed effects, and replay. System-agnostic. It encodes a thin
  universal *what* — that play is checks-with-DCs resolving on a ladder into typed,
  replayable effects — but never which numbers.
- **Rules pack — the content.** Conditions, stat blocks, what a spell does, DC
  guidance, the SRD tables themselves, shipped as data behind the engine's typed
  contracts (the `rules:` namespace already referenced by `rules_binding` /
  `stat_block_ref`, e.g. `rules:npc.commoner`). This is the same engine-vs-pack
  separation worlds use. The first pack is the **D&D 5e SRD (CC-BY-4.0)**; a PF2e or
  OSR pack can swap in later without touching the engine.
- **`dm_profile` — the table's dialect of adjudication.** rules-authority, lethality,
  story-pressure, how readily `narrative_override` fires: the DM's house style made
  into typed knobs. Same pack, different profile, different table. See
  [DM profile](DM_PROFILE.md).

Two consequences of holding this line:

- **The "how" is the *disciplined* version of a DM's adjudication, not the freeform
  one.** A human DM's rulings are unbounded and unrepeatable; here rule-bending is
  fenced into one logged, high-friction gate (`narrative_override`) that never touches
  a PC and routes durable change to dreaming. That fence is what makes the engine
  replayable, which a real table's "how" never is.
- **Keep system idioms out of the engine.** Some 5e-isms are content (they belong in
  the pack); some *feel* like universal procedure but are not. Advantage/disadvantage
  is the trap — it reads like "how you roll" but is a 5e resolution mechanic (PF2e
  uses circumstance bonuses and degree steps instead). When something feels like
  engine-level "how," check that it is not a pack-level "what" in a procedure costume.
  The degree ladder is the settled case: the engine owns the abstraction, each pack
  declares how its checks map onto it.

**The game is table-runnable by construction.** The *format* of these definitions is
machine-shaped — typed contracts, events, replay — and that is fine. But the *game*
never requires a capability a table lacks: every rule resolves with a rulebook, dice,
and a GM's judgment. A runner may automate, enrich, or display play (parallel
attention, a rendered tactical scope, setup seeded from real geometry) — but a runner
is a convenience, never a prerequisite. If a mechanic can only be done by computer, it
does not belong in the game.

## Ownership

- Mechanical state (HP, conditions, resources, initiative, positions, inventory
  counts) lives in rules-owned typed structures. Narrative entities reference it
  through `rules_binding`; they never duplicate or mutate it.
- World-scale and regional travel use the spatial/travel system. The rules engine
  owns tactical/battle positions; PostGIS/pgRouting projections answer geography,
  route, ETA, and risk questions outside the battle grid.
- Every mechanical change is a typed tool call that emits a typed event with
  provenance. Replaying the events rebuilds the same state.
- The DM may explain or interpret outcomes in narration, but cannot change
  canonical state except through these tools.
- A PC's character sheet is created or imported through the engine, not authored by
  hand: onboarding hands the engine the player's choices (or a parsed import) and the
  engine initializes a rules-legal sheet, rejecting anything illegal rather than
  silently accepting it. See PC onboarding in [Lifecycle](LIFECYCLE.md).
- Players own their characters and make the *choices* (build options, level-up
  selections, reactions); the engine *applies* them as typed events. A player never
  hand-maintains mechanical state — keeping HP, resources, conditions, and
  advancement in sync is the engine's job, not the player's bookkeeping.

## Resolution Flow

```text
player intent (NL)
  -> rules_referee: intent + scene context -> typed check spec
  -> rules tool (deterministic)             -> structured result
  -> typed event (provenance)               -> projection update
  -> orchestrator narrates the result
```

`rules_referee` is the translator, not the authority: it converts natural-language
intent into a typed `check_spec` (what kind of check, by whom, against what, with
which modifiers/DC source). It does not roll or mutate state — it hands a spec to a
rules tool. The tool is the deterministic authority.

```yaml
schema: dwd.check_spec.v1
kind: ability_check | saving_throw | attack | damage | contested_check
actor: pc:iona
target: npc:marra_vell            # or a DC source
skill: persuasion                 # ability/skill as applicable
dc_source: { kind: social_attitude, ... }   # see Social Resolution
modifiers: { proficiency: true, advantage: none }
dice_source: physical | digital | declared   # defaulting rule below
adjudication_visibility: table | dm_only | player:pc:iona   # who sees the raw roll/DC/provenance
result_audience: table | dm_only | player:pc:iona           # who receives the conclusion
```

A single `visibility` is too coarse for hidden checks. The raw mechanics
(roll, DC, modifiers, tool provenance) and the player-facing *conclusion* have
different audiences: a secret Insight check keeps `adjudication_visibility:
dm_only` while its `result_audience` is `player:pc:vanya`. For an ordinary
table check both are `table`. `adjudication_visibility` is what drives the
hidden-check dice rule below; `result_audience` is the audience of the
delivered answer/disclosure. Defaults: an unspecified `result_audience`
inherits `adjudication_visibility`; an unspecified `adjudication_visibility`
defaults to `table`.

## Dice Source — Real Dice Are First-Class

Dungeoneer is real tabletop play with an AI DM. Physical dice are the
**expectation**, not a fallback. A roll's source is a first-class field:

- `physical` — read from the table by the vision system (camera/VLM), the default
  expectation.
- `digital` — generated by the seeded deterministic roller (remote play, or when
  no dice are read).
- `declared` — a player states their result ("I rolled a 17"); trusted per table
  policy.

**Hidden checks roll digital-first.** Physical dice are the default only for
checks whose `adjudication_visibility: table`. When a check is hidden from the
table (`adjudication_visibility: dm_only` or `player:<pc>` — e.g. a secret
Insight, a covert Perception, a behind-the-screen save), the default
`dice_source` flips to `digital`: the seeded roller resolves it silently. A
physical table roll would leak that a check is even happening, and often its
result. Rolling digitally is the **feature** here — it gives the AI DM a kind of
secrecy a human DM gets from a screen, and is hard to fake at a shared table.
The result reaches only `result_audience` (the asking player's remote, or
dm_only); the table sees nothing unless the fiction later surfaces it. A
player-private remote roll is allowed when table policy prefers the player to
roll their own hidden checks, but it still must not be table-visible.

```yaml
schema: dwd.dice_result.v1
source: physical
formula: "1d20+5"
faces_read: [14]                  # physical: what the vision system saw
modifiers_applied: 5
total: 19
confidence: 0.92                  # physical only
seed: null                        # digital only: logged for replay
provenance: { capture: asset:roll_0042, tool_call: tool:ability_check_007 }
```

Rules for physical reads:

- A dice read is a **discrete capture** (like map perception), not continuous
  scanning — triggered when a roll is called for.
- Low-confidence reads route to a **confirm** step (re-read, ask the table, or fall
  back to declared) before the result is committed. A roll never silently commits
  on a bad read.
- The read runs on the vision pipeline; the roll's *result* is the canonical input
  to the deterministic rules tool. Physical sourcing changes where the number comes
  from, not who owns the consequence (still the rules engine).
- Latency: a dice read adds a capture+confirm step to the check loop. Mask it with
  filler ("let's see how that lands…") per the latency budget; it is not on the
  tight TTFA path because a called-for roll is already a beat in play.

## Typed Rules Tools

Each is local, deterministic, and must execute in <= 50 ms; the cost is the model
re-prompt, budgeted at <= 700 ms round-trip (see [Latency budget](LATENCY.md)).

- `ability_check(actor, skill, dc, modifiers, dice_source)` -> result + degree.
- `saving_throw(actor, save, dc, modifiers, dice_source)` -> result + degree.
- `attack_roll(attacker, target, weapon, modifiers, dice_source)` -> hit/miss + crit.
- `damage_roll(source, target, formula, type, dice_source)` -> amount applied.
- `contested_check(actor, opponent, axis, dice_source)` -> winner + margin.

All return a structured payload (roll, modifiers, DC, outcome, degree, provenance)
and emit a typed event. None of them accept free-form state writes.

## Typed Events

Generic `rules.state_changed` is replaced by typed events so routing is
predictable and replay is exact (see the taxonomy in
[Game world schema](GAME_WORLD_SCHEMA.md)):

```text
check_resolved        a check/save/contest resolved (may or may not mutate state)
hp_changed            HP delta with cause
condition_applied     a condition instance attached
condition_removed     a condition instance removed/expired
initiative_set        initiative order established or changed
position_changed      a token/actor position changed
rules.override_applied  a gated narrative override (see below)
```

`check_resolved` is non-mutating by itself (an Insight check that reveals nothing
mechanical still emits one), which is why it is separate from `hp_changed` et al.

## Effects And Modifiers

Everything that changes a number or a capability — a condition, a piece of setwork, a
ship posture, a spell, cover, terrain, the weather gauge — does it by contributing a
**modifier**. The modifier is the engine's universal currency of effects; the
`modifiers` argument on the typed tools above is the *resolved* set of applicable
modifiers from every source.

A modifier is atomic and typed:

```yaml
schema: dwd.modifier.v1
source: { kind: component, id: rules:set.thrust_figure_mk2 }
target: { stat: maneuver }       # a roll, DC, stat, resource, action-economy slot, or position attribute
op: { kind: add, value: 2 }      # add | subtract | multiply | set | floor | cap |
                                 # grant | revoke | resist | immune | vulnerable | roll_shape
when: { tag_present: khevric }   # optional guard (the trigger half of the rule grammar)
lifecycle: while_source_active   # instantaneous | until_end_of_turn | while_source_active | ...
```

Resolution at a check is deterministic:

1. **Collect** every modifier whose `when` guard is satisfied for this check.
2. **Group and apply the stacking policy** (do two same-typed bonuses stack? take the
   highest? is advantage binary?).
3. **Resolve the ops in a fixed order** (set/floor/cap → add/subtract → multiply →
   clamp), with deterministic tie-breaks, so replay is exact.

The how/what split runs straight through this:

- **The engine owns the mechanism and the math-op order** — collection, the op set,
  and the deterministic resolution order. That is what makes replay exact.
- **The pack owns the stacking policy and the roll-shaping idioms.** 5e's "same-named
  bonuses don't stack" and binary **advantage/disadvantage** are a *pack* policy;
  PF2e's "highest bonus per type" and circumstance bonuses are a *different* pack's
  policy. The engine never assumes one; `op.roll_shape` and the stacking rule come
  from the pack.

So "amplification" (the khevra motif) is just `op: multiply` guarded by a charge cost
and a failure trigger; "advantage" is a pack-declared `roll_shape`; "prone gives
disadvantage" is a condition contributing a roll_shape modifier. One pipeline.

Two notes worked traces surface: a modifier targets either a **stat** (resolved once,
then read by any check that uses it) or the **roll** directly, and each action
declares the formula that composes them — a Helm check is `d20 + helmsman skill + the
ship's resolved maneuver`. And `multiply` is potent on large quantities (damage,
distance, hull, speed) but weak on a small check bonus (`+4 → +6` is meh), so
amplifiers belong on the big numbers, not on a +2.

## Components

A **component** — a khevra set/figure, a weapon, an augment, a ship's installed
setwork — is a host attachment that bundles modifiers, granted actions, and tags
behind a slot and (optionally) a charge cost and a failure mode.

```yaml
schema: dwd.component.v1
id: rules:set.autopilot_helm
slot: setwork
host_kinds: [ship]
charge_cost: 1                   # per activation, drawn from a resource
modifiers:
  - { target: { economy_station: helm }, op: { kind: grant, value: act_unmanned } }
grants_actions: [engage_autopilot]
tags_added: [khevric]
failure: { trigger: overdraw, effect: apply_condition:instability }
```

Two consequences worth stating:

- **A host's effective profile is a projection.** Base profile + installed components
  + active conditions + current posture, resolved through the modifier pipeline —
  *computed, not stored.* "What is this ship's maneuver right now?" is derived, and it
  recomputes the instant a component is destroyed (a called shot to the engine figure)
  or a condition changes. Install/remove are events (`component_installed` /
  `component_removed`), so the whole thing is event-sourced and replayable like every
  other projection.
- **Any target is fair game for a modifier**, including the action economy (autopilot
  grants an unmanned Helm action) and position attributes (a lift figure adds an
  altitude band). New capabilities are modifiers, not new engine code.

Components are the general primitive that ship setwork, PC equipment, and a faction's
signature **style package** all instance: a tradition is a curated component bundle +
a signature action + a failure personality + descriptive identity, not per-faction
rules. See [Ship combat](SHIP_COMBAT.md) for the worked case.

## Combat Model

```yaml
schema: dwd.combat_state.v1
scene: scene:s4_dock_ambush
round: 2
current_turn: creature:ledger_thug_2
initiative:
  - { actor: pc:kael, score: 18 }
  - { actor: creature:ledger_thug_1, score: 14 }
  - { actor: pc:iona, score: 12 }
  - { actor: npc:sevran_oke, score: 9 }
  - { actor: creature:ledger_thug_2, score: 7 }
```

- **Turn/round lifecycle events:** `turn.started`, `turn.ended`, `round.started`,
  `round.ended` — so skips, readied actions, and reactions are representable.
- **Position scale:** `position_changed` in combat is tactical and rules-owned.
  Overland, sea, airship, or city-route movement uses travel events from
  [Spatial and travel system](SPATIAL_TRAVEL.md), then may open a scene/battle
  with a rules-owned tactical map.
- **Condition instances** are typed, not prose:

```yaml
schema: dwd.condition_instance.v1
type: grappled
target: pc:iona
source: creature:ledger_thug_2
origin: { contested_check: tool:contested_check_011 }
duration: { kind: until_escape }
removal: [escape_check_success, source_incapacitated]
stacking: replace            # replace | stack | ignore
visibility: table
```

- **NPCs and creatures both take combat state** (HP, AC, conditions) via
  `rules_binding`. The difference is *control*, not mechanics: a `creature` (a
  non-unique instance) is driven by the orchestrator/tactics advisor as a rules
  actor with no sub-agent; a unique `npc` may have a sub-agent for dialogue/intent
  but its mechanical combat state is rules-owned the same way. A creature does not
  get a sub-agent unless promoted to a named NPC.
- **0 HP:** the rules engine sets the mechanical consequence (creature: defeated;
  PC: unconscious + death saves) and emits the typed event; the entity-lifecycle
  field (e.g. `dead`) is updated by the orchestrator from that event, not by
  narration.

## Encounter Modes

The combat model above is one **encounter mode** — the default, at personnel scale.
An encounter mode is a typed configuration of how a bounded, structured situation
resolves, along four parameters:

- **Action economy** — creature-based (action/bonus/move per creature) for personnel
  combat. Other modes bind it differently: a ship's economy is **station-based**,
  gated by crew; a mass battle is unit-based.
- **Resolution model** — sequential initiative here; a mode may instead resolve
  **simultaneously**. Simultaneous resolution is a *declaration phase* (orders are
  recorded inputs, hidden per the visibility model) followed by a **deterministic
  pipeline** of fixed sub-phases. Simultaneity is a decision/feel property only — the
  resolution is a pure function of declarations + recorded dice, so replay holds and
  events keep a stable append order.
- **Time scale** — the personnel round is the base unit; a mode may run coarser.
- **Position space** — the tactical grid here; a mode declares its own (range bands,
  facing, altitude, wind).

**Encounters nest.** A coarse-scale encounter may host a finer one at a **fixed
time-scale ratio** — one parent turn spans N child rounds. The child runs time-boxed
and carries over if unresolved; parent and child exchange effects through events at
the zoom boundary (a parent maneuver imposes checks in the child; child casualties
change the parent's state). One primitive serves ship combat hosting a boarding
melee, a chase hosting a clamber, a siege hosting an assault. The worked extension is
[Ship combat](SHIP_COMBAT.md).

## Social Resolution

### DC — hybrid, attitude-anchored

Real DMs do not invent social DCs; they read the room. So:

1. **Baseline from NPC attitude** (hostile / indifferent / friendly), anchored to
   SRD social-interaction guidance. Attitude is derived from the NPC's relationship
   axes toward the asker (fear, trust, affinity) and current intention.
2. **Adjust for stakes and the size of the ask.** Low-stakes asks of an NPC with no
   reason to defend lean easy; asks that cut against a core goal/fear/secret lean
   hard.
3. The model may **nudge within bounds**, not set the DC freely. The bounds come
   from attitude + stakes; the nudge is the DM's judgment inside them.

### Degree of success — a ladder

Outcomes resolve on a four-band ladder by margin vs. DC, not binary pass/fail:

```text
fail      missed the DC
partial   missed narrowly, or hit with a cost/complication
success   met the DC
strong    beat it by a wide margin (or a natural-20-class result)
```

Good DMs apply a ladder implicitly; making it explicit is more fun and consistent.

### Outcome -> disclosure

A check result does not directly unlock secrets. The rules engine emits the
`check_resolved` result + degree; the NPC/orchestrator translates that into
**bounded** disclosure:

- A successful Insight reveals the truth of *the checked claim* (is Sevran bluffing
  about reinforcements?), not every secret the NPC holds.
- Disclosure that creates canon emits `knowledge.learned` (the asker learns it),
  `fact.asserted` (if it becomes table canon), or `secret.revealed` (a secret
  bundle opening, with visibility), each with correct audience.
- Degree shapes how much: `partial` reveals a hedge or a clue; `strong` reveals
  more or with certainty. The NPC may still **refuse or counter-offer** within its
  goals — `npc.propose_speech` carries a stance (accept / refuse / counter) so a
  high roll against a defensive NPC yields a negotiation, not automatic compliance.

### Relationship change

A relationship moves via the `relationship.update` tool (see
[Game world schema](GAME_WORLD_SCHEMA.md)). Threshold:

- A table-driven nudge (a direct promise -> a trust bump) **commits live**.
- A change that would flip loyalty or long-term stance is an inference and goes to
  **dreaming** as a reviewable patch.

A direct in-fiction promise can also promote a social **memento** (mechanical:
auto; purely interpretive: model-proposed, reviewed).

## narrative_override — Principle First

Rule-of-cool is a sanctioned, logged capability — but it is fenced hard, because
the easy version of it is railroading.

- **It never touches a PC. Ever.** Players own their characters. Only a rules-legal
  game effect (through the engine — a spell, a condition, an ability) can constrain
  a PC, and that is not an override. A `narrative_override` targeting a player
  character is rejected, unconditionally.
- **NPC and world overrides are allowed but deliberately high-friction.** It is not
  a default tool. It exists for the rare cinematic beat (a flourish that disarms an
  NPC the roll did not support), gated by the `dm_profile` rules-authority setting,
  and it should feel costly to reach for.
- **Durable world change is dreaming's job**, not live override. If a change wants
  to reshape the world (a faction turns, a fact becomes canon), it goes through the
  slow, reviewed dreaming path — not a live fudge.

```yaml
schema: dwd.narrative_override.v1
actor: pc:kael                    # the in-fiction agent of the beat
affected_entities: [npc:sevran_oke]   # NPC/world only; a PC here is rejected
override_type: disarm
justification: "cinematic flourish on the killing blow"
profile_gate: rule_of_cool        # must match dm_profile.rules_authority
provenance: { source_message: msg:s4_0091, tool_call: tool:override_003 }
```

Every use emits `rules.override_applied` and is always audit-logged. Whether the
table *sees* a tell that an override happened is a disclosure policy (see
[DM profile](DM_PROFILE.md)) — but inspectability in the log is non-negotiable.

## Build Order

- Phase 2: rules_referee + typed tools + typed events; combat state, conditions,
  turn/round events; the dice-source contract (digital first, physical read
  integrated with the vision pipeline); social DC + ladder + disclosure;
  `narrative_override` with its PC-immunity rule and profile gate.
- Regression fixtures for the common combat and skill-check flows, scored against
  the saved simulation traces.
