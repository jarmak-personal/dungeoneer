# Rules Engine

The rules engine owns canonical mechanical state. Models propose and explain;
typed tools make the changes. It is deterministic, inspectable, and the boundary
that keeps narrative out of mechanics. This doc defines its tool surface, dice
sourcing, typed events, the combat model, social resolution, the
`narrative_adjustment` / `narrative_override` capabilities, and the rules-pack
boundary.

## Position — How, Not What

The rules engine is *how the DM implements the rules*, not *what system the table is
playing*. That is the silent assumption every real table already makes: a rulebook
underdetermines play, and the table's actual ruleset is the book plus a DM who
adjudicates it consistently. We split that into three owned, typed, swappable layers.

- **Engine — the adjudication procedure and resolution grammar.** When a check is
  called: intent -> typed check spec, DC-selection procedure, the degree ladder, dice
  sourcing, typed consequences, and replay. System-agnostic. It encodes a thin
  universal *what* — that play is checks-with-DCs resolving on a ladder into
  replayable consequences — but never which numbers.
- **Rules pack — the content.** Conditions, stat blocks, what a spell does, DC
  guidance, the SRD tables themselves, shipped as data behind the engine's typed
  contracts (the `rules:` namespace already referenced by `rules_binding` /
  `stat_block_ref`, e.g. `rules:npc.commoner`). This is the same engine-vs-pack
  separation worlds use. The first pack is the **D&D 5e SRD (CC-BY-4.0)**; a PF2e or
  OSR pack can swap in later without touching the engine.
- **`dm_profile` — the table's dialect of adjudication.** rules-authority, lethality,
  story-pressure, how readily narrative adjustments and overrides fire: the DM's
  house style made into typed knobs. Same pack, different profile, different table.
  See
  [DM profile](DM_PROFILE.md).

Two consequences of holding this line:

- **The "how" is the *disciplined* version of a DM's adjudication, not the freeform
  one.** A human DM's rulings are unbounded and unrepeatable; here rule-bending is
  split into two logged gates: bounded `narrative_adjustment` for roll inputs, and
  high-friction `narrative_override` for exceptional NPC/world consequences. Durable
  world change routes to dreaming. That fence is what makes the engine replayable,
  which a real table's "how" never is.
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

## State And Replay Guardrails

The live session has a current rules projection for speed, but it is not an
agent-editable global state bag. Canon is the accepted event log; the projection
is rebuilt from rules definitions plus accepted events.

Every mechanical write crosses three gates:

1. **Proposal gate.** The orchestrator or `rules_referee` may propose intent,
   check specs, adjustments, overrides, or consequence plans, but none of those
   are state writes.
2. **Append gate.** The deterministic rules tool validates the proposal against
   the current projection, the active rules pack, `dm_profile`, dice source, and
   accepted modifier/consequence grammar before emitting events.
3. **Replay gate.** Rebuild verifies that every `before` value matched the prior
   projection, every `after` value matches deterministic recomputation, and every
   modifier or consequence has accepted provenance.

So "the player convinced the AI DM they get +20 damage" is not a valid state
change. The model can propose it; the append gate rejects it unless a rules-pack
feature or explicitly capped profile capability authorizes that exact modifier or
consequence, and replay can still reproduce the math.

## Resolution Flow

```text
player intent (NL)
  -> rules_referee: intent + scene context -> typed check spec
  -> rules tool (deterministic)             -> structured result
  -> consequence plan                       -> validated state events
  -> projection update
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
dc_source: { kind: social_attitude, ref: tool:social_dc_003 }  # see Social Resolution
modifiers: [modifier:persuasion_proficiency]  # roll shape is just another modifier
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
- `damage_roll(source, target, formula, type, dice_source)` -> damage consequence.
- `contested_check(actor, opponent, axis, dice_source)` -> winner + margin.

All return a structured payload (roll, modifiers, DC, outcome, degree, provenance)
and emit a typed event. If a result changes mechanical state, the rules engine
applies a consequence plan (below) and emits domain events. None of the tools
accept free-form state writes.

## Typed Events

Generic `rules.state_changed` is replaced by typed events so routing is
predictable and replay is exact (see the taxonomy in
[Game world schema](GAME_WORLD_SCHEMA.md)):

```text
check_resolved        a check/save/contest resolved (may or may not mutate state)
hp_changed            HP delta with cause
resource_changed      rules-owned resource delta with cause
condition_applied     a condition instance attached
condition_removed     a condition instance removed/expired
initiative_set        initiative order established or changed
position_changed      a token/actor position changed
combat.disposition_changed  combat availability changed
rules.adjustment_granted  a bounded narrative modifier grant (see below)
rules.override_applied  a gated narrative override (see below)
```

`check_resolved` is non-mutating by itself (an Insight check that reveals nothing
mechanical still emits one), which is why it is separate from `hp_changed` et al.

## Consequences — One Pipeline, Many State Domains

A combat action resolves into **consequences**. Damage, disarm, shove, grapple,
trip, healing, resource spend, forced movement, and a narration-only flourish are
not separate architectural shapes. They are configured instances of one
consequence grammar that mutates different rules-owned state domains.

This keeps the rules surface small:

- `damage` mutates HP/temp HP and may change combat disposition.
- `resource` mutates charges, spell slots, ammunition, action slots, reactions, or
  other rules-owned counters.
- `condition` applies or removes a typed condition instance.
- `movement` mutates tactical position.
- `item_state` mutates custody, equipment slots, held items, or item position.
- `combat_disposition` mutates whether an actor is active, defeated,
  unconscious, dying, dead, fled, surrendered, or removed from the encounter.
- `narration_only` records that the rules effect is purely descriptive and emits
  no mechanical state event.

Maneuver names such as `disarm`, `grapple`, `shove`, and `trip` live in rules-pack
content as action/effect templates. They compile to the consequence kinds above;
they do **not** become custom event types. A spell uses the same path: a spell is
pack content that produces a configured consequence plan.

```yaml
schema: dwd.rules_consequence_plan.v1
resolution_id: rulesres:s4_021
source_event: event:s4_0209          # usually check_resolved or rules.override_applied
source_tool_call: tool:attack_roll_014
actor: pc:kael
action: rules:action.attack
consequences:
  - order: 1
    kind: damage
    target: npc:sevran_oke
    damage_type: slashing
    amount: { rolled: 8, final: 6 }
    mitigation:
      - { kind: resistance, source: condition:stoneskin, amount_removed: 2 }
    hp_before: 18
    hp_after: 12
    emits: [event:s4_0210]
```

The plan is not a second source of truth. It is the validated explanation of why
events were emitted. Canon is still the accepted event log; replay rebuilds state
from the domain events. The plan's `resolution_id` ties the events together for
audit, rollback, and debugging.

The rules engine applies a consequence plan atomically:

1. Validate each consequence against current rules state and the rules pack.
2. Check preconditions (`item is held`, `target is in range`, `resource exists`,
   `condition can stack`, `target can be affected`).
3. Emit the domain events in plan order.
4. Rebuild the projection and assert that every `before` field matched the prior
   projection and every `after` field matches the result.
5. Reject the whole plan if any consequence fails validation.

The key discipline: **consequence kind is thematic, event type is state-domain**.
Damage emits `hp_changed`; disarm emits `item.transferred` (and optionally
`condition_applied`); grapple emits `condition_applied`; shove emits
`position_changed` or `condition_applied` (`prone`); spending a reaction emits
`resource_changed`. This keeps same things same without hiding important state
behind a generic `effect_applied`.

### Worked Consequences

Damage:

```yaml
schema: dwd.rules_consequence_plan.v1
resolution_id: rulesres:s4_030
source_event: event:s4_0299
source_tool_call: tool:damage_roll_008
actor: creature:ledger_thug_1
action: rules:action.scimitar
consequences:
  - order: 1
    kind: damage
    target: pc:dorn
    damage_type: slashing
    amount: { rolled: 5, final: 5 }
    hp_before: 17
    hp_after: 12
    emits: [event:s4_0300]
```

Disarm:

```yaml
schema: dwd.rules_consequence_plan.v1
resolution_id: rulesres:s4_041
source_event: event:s4_0407
source_tool_call: tool:contested_check_011
actor: pc:kael
action: rules:action.disarm
consequences:
  - order: 1
    kind: item_state
    reason: disarm
    item: item:sevran_blade
    from: { actor: npc:sevran_oke, slot: hand_main }
    to: { scene: scene:s4_dock_ambush, position: grid:g7 }
    emits: [event:s4_0408]
```

Grapple:

```yaml
schema: dwd.rules_consequence_plan.v1
resolution_id: rulesres:s4_052
source_event: event:s4_0511
source_tool_call: tool:contested_check_019
actor: creature:ledger_thug_2
action: rules:action.grapple
consequences:
  - order: 1
    kind: condition
    operation: apply
    condition:
      type: grappled
      target: pc:iona
      source: creature:ledger_thug_2
      origin: { resolution_id: rulesres:s4_052 }
      duration: { kind: until_escape }
      removal: [escape_check_success, source_incapacitated]
      stacking: replace
      visibility: table
    emits: [event:s4_0512]
```

0 HP:

```yaml
schema: dwd.rules_consequence_plan.v1
resolution_id: rulesres:s4_063
source_event: event:s4_0621
source_tool_call: tool:damage_roll_014
actor: pc:dorn
action: rules:action.greataxe
consequences:
  - order: 1
    kind: damage
    target: creature:ledger_thug_1
    damage_type: slashing
    amount: { rolled: 11, final: 11, overkill: 4 }
    hp_before: 7
    hp_after: 0
    emits: [event:s4_0622]
  - order: 2
    kind: combat_disposition
    target: creature:ledger_thug_1
    from: active
    to: defeated
    reason: hp_zero_creature
    emits: [event:s4_0623]
```

## Effects And Modifiers

Modifiers are reusable rules facts that alter how future checks or consequences
resolve. Consequences are what an action does now. A condition, a piece of
setwork, a ship posture, a spell, cover, terrain, or the weather gauge can
contribute a **modifier**; the `modifiers` argument on the typed tools above is
the *resolved* set of applicable modifiers from every source.

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

### Narrative Adjustments Are Modifiers

A **narrative adjustment** is the rule-of-cool version of cover, inspiration, or
favorable footing: a first-class modifier grant with a narrative reason and hard
mechanical bounds. It is not prompt permission for the DM to change a result.

```yaml
schema: dwd.narrative_adjustment.v1
adjustment_id: adjustment:s4_held_line_bonus
target: pc:vanya
profile_gate: balanced            # must be allowed by dm_profile.rules_authority
reason: "Vanya invokes the old oath while holding the bridge alone."
modifier:
  schema: dwd.modifier.v1
  source: { kind: narrative_adjustment, id: adjustment:s4_held_line_bonus }
  target: { check_kind: saving_throw, save: wisdom }
  op: { kind: add, value: 2 }
  when: { next_matching_check: true }
  lifecycle: next_matching_check
caps:
  add_max: 2
  roll_shape_steps_max: 1
  damage_bonus_allowed: false
provenance: { source_message: msg:s4_0088, tool_call: tool:adjustment_002 }
```

Every grant emits `rules.adjustment_granted`. When the matching check resolves,
`check_resolved.modifiers` cites the adjustment's modifier ID, and replay verifies
that the modifier existed, matched the check, was still live, obeyed the profile
caps, and was consumed or expired exactly once.

Allowed initial targets are check math and roll shape: ability checks, saving
throws, attack rolls, contested checks, DC nudges within declared bounds, and
pack-declared `roll_shape` values such as advantage. Direct HP, resource,
condition, item, position, combat-disposition, or damage changes are
**consequences**, not adjustments. A table can later choose to allow a bounded
narrative damage modifier, but that must be an explicit pack/profile capability
with its own cap; it is not part of the default adjustment surface. The guardrail
against "I talked the AI DM into +20 damage" is that damage math and state
mutation are validated by the rules engine, not accepted from narration.

For PCs, narrative adjustments may grant beneficial roll inputs under the active
profile. Harmful PC penalties from narrative color are not adjustments; they need
a rules-pack source such as a condition, spell, terrain rule, exhaustion state, or
other typed game effect. For NPCs and creatures, the same adjustment grammar can
grant bounded bonuses or penalties when the profile allows it, but the event still
needs provenance and replay-valid math.

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

Social checks are mechanically accountable, but they do not mind-control NPCs.
The check answers a bounded question: given this ask, this NPC, this relationship,
and this roll, what is the strongest honest disclosure or stance change the rules
permit right now?

### DC Source - Hybrid, Attitude-Anchored

Real DMs do not invent social DCs; they read the room. Dungeoneer makes that
reading replayable with `dwd.social_dc_source.v1`.

```yaml
schema: dwd.social_dc_source.v1
source_id: tool:social_dc_003
npc: npc:wick
asker: pc:vanya
approach: persuasion              # persuasion | deception | intimidation | insight
ask_scope: guarded_secret         # trivial | safe_favor | meaningful_risk | costly_risk | guarded_secret | betrayal
checked_claim: secret:the_kept_flame
relationship_axes:
  trust: 20
  affinity: 5
  respect: 10
  debt: 0
  suspicion: 35
  fear: 15
current_intention:
  stance: protect_secret
  modifier: -10
  source_ref: "npc:wick#current_intention"
attitude_formula:
  version: social_attitude.default.v1
  score: -11
  computed_attitude: indifferent  # hostile | indifferent | friendly
stake_class: high
base_dc: 30
allowed_range: [28, 32]
selected_dc: 31
nudge:
  amount: 1
  reason: "The ask touches a secret Wick is actively guarding."
provenance:
  relationship_refs: [rel:wick->pc:vanya]
  source_message: msg:s12_0172
  tool_call: tool:social_dc_003
```

Default attitude formula:

```text
score = clamp(
  trust*0.35 + affinity*0.25 + respect*0.15 + debt*0.10
  - suspicion*0.25 - fear*0.10 + current_intention.modifier,
  -100,
  100
)

friendly    score >= 25
hostile     score <= -25
indifferent otherwise
```

The weighted sum is rounded to the nearest integer before banding.
Missing relationship axes count as 0. `current_intention.modifier` is selected
from `-20`, `-10`, `0`, `+10`, or `+20`, with a cited NPC intention, goal, fear,
oath, or scene fact. It is not a free model-authored DC adjustment; the separate
`nudge` field is the bounded judgment space.

Fear is intentionally a small default negative. It often changes the *stakes* or
approach more than warmth: an intimidated NPC may comply, but that does not mean
they are friendly.

Default DC bands:

```yaml
schema: dwd.social_dc_band.v1
bands:
  friendly:
    trivial: 5
    safe_favor: 10
    meaningful_risk: 15
    costly_risk: 20
    guarded_secret: 25
    betrayal: blocked
  indifferent:
    trivial: 10
    safe_favor: 15
    meaningful_risk: 20
    costly_risk: 25
    guarded_secret: 30
    betrayal: blocked
  hostile:
    trivial: 15
    safe_favor: 20
    meaningful_risk: 25
    costly_risk: 30
    guarded_secret: blocked
    betrayal: blocked
model_nudge_default: [-2, 2]
```

`blocked` means the check cannot directly win that ask. The orchestrator may still
offer a counter, hint, price, alternate route, or future opportunity. A profile may
allow a wider nudge, but the selected DC must always fall inside the recorded
`allowed_range`.

### Degree Of Success - A Ladder

Outcomes resolve on a four-band ladder by margin vs. DC, not binary pass/fail:

```text
fail      margin <= -5
partial   margin -4..-1, or success with a cost/complication
success   margin 0..9
strong    margin >= 10, or a pack-declared critical social result
```

Good DMs apply a ladder implicitly; making it explicit is more fun and consistent.

### Outcome To Disclosure

A check result does not directly unlock secrets. The rules engine emits the
`check_resolved` result + degree; the orchestrator then records a
`dwd.social_disclosure_decision.v1` tool result that translates the check into
bounded message and knowledge events.

```yaml
schema: dwd.social_disclosure_decision.v1
decision_id: tool:social_disclosure_002
source_check: event:s12_0173
dc_source: tool:social_dc_003
npc: npc:wick
asker: pc:vanya
audience: table
degree: success
ask_scope: guarded_secret
checked_claim: secret:the_kept_flame
npc_knowledge_consulted:
  - target: secret:the_kept_flame
    mode: knows
    can_share: false
    secrecy: private
relationship_refs: [rel:wick->pc:vanya]
stance: counter_offer             # refuse | deflect | hint | answer | counter_offer | lie
disclosure_limit: clue            # none | hedge | clue | checked_claim | checked_claim_plus_context
proposed_events:
  - type: message.delivered
    audience: table
    summary: "Wick admits there is a shrine matter, but asks for proof of intent first."
  - type: knowledge.learned
    holder: pc:vanya
    target: fact:wick_guards_shrine_secret
    mode: suspects
    audience: table
provenance:
  source_message: msg:s12_0172
  tool_call: tool:social_disclosure_002
```

Rules:

- A success reveals the checked claim, not the NPC's whole secret inventory.
- A `strong` result may add certainty, a relevant context clue, or a second bounded
  connected claim. It still cannot reveal unrelated secrets.
- If `can_share: false`, the default maximum is `clue` or `counter_offer` unless
  another authority exists: a reveal condition, direct table action, operator
  review, or explicit scenario/scripted trigger.
- `partial` usually yields a hedge, tell, clue, cost, or counter-offer. `fail`
  can produce refusal, deflection, false confidence, suspicion, or a relationship
  proposal, but any state change still uses the ordinary typed path.
- NPC speech is a proposal until the orchestrator accepts it. The accepted line is
  delivered by `message.delivered`; knowledge/fact/secret changes are separate
  events with the disclosure decision as provenance.
- Lies and rumors are knowledge states, not canon facts. They may emit
  `knowledge.learned` with `mode: believes` or `heard_rumor` and `truth: false` or
  `unknown`, but they do not emit `fact.asserted` as canon.

### Relationship change

A relationship moves via the `relationship.update` tool (see
[Game world schema](GAME_WORLD_SCHEMA.md)). Threshold:

- A table-driven nudge (a direct promise -> a trust bump) **commits live**.
- A change that would flip loyalty or long-term stance is an inference and goes to
  **dreaming** as a reviewable patch.

A direct in-fiction promise can also promote a social **memento** (mechanical:
auto; purely interpretive: model-proposed, reviewed).

## Narrative Adjustment And Override

Rule-of-cool is sanctioned, but split by authority:

- **`narrative_adjustment` changes roll inputs.** It grants bounded modifiers such
  as a +2 attack bonus, a small saving-throw bonus, a bounded DC nudge, or a
  pack-declared roll-shape change like advantage. It may benefit a PC when the
  active `dm_profile` allows it, because the grant is typed, capped, logged, and
  replay-validated.
- **`narrative_override` authorizes exceptional consequences.** It is the rare
  high-friction tool for an NPC/world cinematic beat that ordinary rules did not
  produce, such as a disarm flourish against an NPC. It is not a default tool.
- **Override authority is binary for now.** `dm_profile.rules_authority` either
  exposes `narrative_override` or it does not. Do not add rate limits, point
  budgets, or per-session caps until play shows the binary gate is too loose; the
  current enforceable checks are profile gate, target legality, consequence-plan
  validation, provenance, audit log, and tell.
- **PC state and agency remain protected.** A PC may be the actor of an override
  beat, and a PC may receive a beneficial `narrative_adjustment`, but
  `narrative_override` cannot target a PC with a consequence, move them, damage
  them, change their resources, impose or remove a condition, alter their items,
  set their combat disposition, or decide their choices. Harmful PC effects need a
  rules-pack source and normal rules-engine validation.
- **Durable world change is dreaming's job**, not live override. If a change wants
  to reshape the world (a faction turns, a fact becomes canon), it goes through the
  slow, reviewed dreaming path, not a live fudge.

```yaml
schema: dwd.narrative_override.v1
actor: pc:kael                    # the in-fiction agent of the beat
affected_entities: [npc:sevran_oke]   # override consequence targets are NPC/world only
override_type: disarm
justification: "cinematic flourish on the killing blow"
profile_gate: rule_of_cool        # must match dm_profile.rules_authority
consequence:
  kind: item_state
  reason: disarm
  item: item:sevran_blade
  from: { actor: npc:sevran_oke, slot: hand_main }
  to: { scene: scene:s4_dock_ambush, position: grid:g7 }
tell:
  operator_visible: true
  table_cue: diegetic              # diegetic | ui | none
provenance: { source_message: msg:s4_0091, tool_call: tool:override_003 }
```

Every use emits `rules.override_applied` and is always audit-logged. If it has
mechanical impact, the impact is still expressed through the same consequence
plan and domain events as any other action; the override is the audited authority
to produce that plan, not a special state-writing path. Whether the table *sees*
a tell that an override happened is a disclosure policy (see
[DM profile](DM_PROFILE.md)) — but inspectability in the log is non-negotiable.

## Build Order

- Phase 2: rules_referee + typed tools + consequence plans + typed events;
  combat state, conditions, resources, combat disposition, turn/round events; the
  dice-source contract (digital first, physical read integrated with the vision
  pipeline); social DC + ladder + disclosure; `narrative_adjustment` and
  `narrative_override` with profile gates and replay validation.
- Regression fixtures for the common combat and skill-check flows, scored against
  the saved simulation traces.
