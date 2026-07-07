# Ship Combat (Aurevost Rules Extension)

## Purpose

Aurevost is a world of crowded seas and rare prestige airships. Vessel conflict is
core campaign drama: sea combat is the common case, while sky combat is a costly
elite variant most tables may touch only if the campaign climbs into that layer.
Ship combat is the worked example of two ideas:

- a **world rules extension** — content layered on the 5e SRD system pack, adding
  ship archetypes, stations, actions, and conditions in the existing primitive
  vocabulary (it adds content, not engine primitives); and
- the engine's **encounter-mode + nested-encounter** model (see
  [Rules engine](RULES_ENGINE.md) "Encounter Modes").

Ship combat is one encounter mode: **station** action economy, **simultaneous**
resolution, a **coarse** time scale, and a **sea/sky** position space. It hosts
personnel combat (boarding) as a nested child encounter. Nothing here is a new
engine concept — it is a parameter set plus content.

## The unit of play

A ship is an entity with a `rules_binding` to a **ship profile** (a stat block at a
different scale): hull (HP), evasion (AC by size/maneuver), speed and maneuver (turn
radius), crew capacity, station list, armament slots, setwork slots, cargo, and
tradition tags (`sorrellian`, `otharian`, …). It carries conditions like any actor.

Two things make it a *ship* and not a big creature:

- **Stations are the action economy.** Helm, each gunnery battery, Sails/Rigging,
  Damage Control, Navigation/Lookout, Command. A station acts only if **manned** by a
  capable hand.
- **Crew is a resource, not a roster.** Named hands (PCs, notable officers) take real
  checks and occupy stations; the mass crew is a **pool + quality rating** that
  auto-mans routine stations and sets a baseline. Casualties drain the pool → fewer
  stations manned → the death spiral. The whole strategic tension — **fight / steer /
  fix / repel** — is just where you assign hands this turn.

## The tactical scope — position space

Ship combat's position space is an abstract **tactical scope**, not a coordinate
grid: a shared plot every ship sits on, like a radar screen. A ship's whole position
is four discrete values and every tactical question is a lookup, not geometry. (No 3D
math — true firing solids are unplayable and a determinism hazard; the third
dimension is more useful as a *resource* than a coordinate, and discrete bands replay
exactly where float geometry would not.)

A ship's position is **{range ring, bearing, altitude band}** carried on
`position_changed`, plus the shared **wind** state for the scope.

- **Range rings** — four bands from the engagement: `engaged / close / medium / long`,
  plus `broken contact` (a ship that breaks off leaves the scope; the encounter ends
  or becomes a chase). Closing/opening is a movement result; weapons and boarding each
  declare a maximum range band.
- **Bearing & arcs** — a ship faces one of eight headings; the relative arc between two
  ships resolves to a named bucket: `fore / port / starboard / aft` (a broadside covers
  port+starboard). Arcs are labels on a relationship, never angles. Arc-gating a shot
  is three discrete checks: **target's arc ∈ the weapon's arcs AND target's range ≤ the
  weapon's range AND the altitude gap within the weapon's elevation.**
- **Altitude bands** — five: `grounded(0) / low / mid / high / ceiling`. Climb costs
  thrust (a Sails/Helm action), a dive trades altitude for closing or speed; height
  gates some arcs and feeds the weather gauge. **`grounded` is a defeat axis distinct
  from hull-0:** a ship forced to band 0 with no lift is *forced down* (crashed or
  grounded, out of the fight) — the airship counterpart of sinking at hull-0.
- **Sea ships are altitude-locked** — same model, the altitude dial just does not turn;
  they sit at the surface band, and their lethal axis is *sinking* (hull-0) rather than
  *forced down* (altitude-0). One system covers sea, sky, and mixed engagements; the
  only difference is whether a ship can move on the altitude axis.
- **Wind** — one direction across the scope plus a strength band (`calm / breeze /
  gale`); it biases movement (closing downwind is cheaper, climbing into a gale costs
  more) and sets the **weather gauge**, an advantage token the favorably-positioned
  ship (upwind, with height) claims in the Navigation sub-phase.

"Overboard" from the reciprocal coupling reads off this axis: from a sea ship you hit
the water (a swim/rescue problem); from an airship you fall through altitude bands
(fall damage scaling with the band, or a grab-the-rigging save first). Same event,
altitude-dependent consequence.

The discrete scope is canonical and **paper-runnable**: a GM sets the opening rings,
headings, altitude, and wind by judgment of the fiction, and every tactical question
is a by-hand lookup. A runner *may* automate the setup by seeding the opening
positions from the real PostGIS/pgRouting spatial state (who is upwind, who has
height, the starting range), and a client *may* render a 3D view from the discrete
values — but both are conveniences over the table-runnable scope, never a requirement.
The bands are canonical; the geometry is optional enrichment.

## The ship turn — simultaneous, but deterministic

"Everyone acts at once" cannot mean nondeterministic, or replay breaks. So
simultaneity lives at the decision layer and resolution is a fixed pipeline:

1. **Declaration.** Every manned station commits an order. The crew (PCs) coordinate
   openly; **enemy orders are `dm_only` until reveal** — fog of war. Declarations are
   recorded inputs. Players do not know enemy orders unless they spend to learn them
   (see "Information").
2. **Resolution pipeline** — a fixed sub-phase order, deterministic tie-breaks:
   1. Navigation / positioning (weather gauge, wind, claim advantage)
   2. Movement (helm + sails; facing / range / altitude update)
   3. Heavy weaponry (arcs computed against the *resolved* positions)
   4. Boarding (opens the nested melee — see "Nesting")
   5. Tending / damage control (repair, douse, pump, reload)
3. **Emit deltas as events** in stable phase order.

**Replay invariant:** declarations are inputs, the pipeline is a pure function of
(declarations + recorded dice), events have a stable append order. Simultaneity is
feel; the resolution is deterministic.

### Why the pipeline order is fixed (and command stays bounded)

Fully captain-chosen sub-phase order is incompatible with simultaneous resolution —
if one ship fires-then-moves while another moves-then-fires, there is no coherent
"resolve everyone's movement together," and `movement → weapons` (maneuver sets your
arcs) stops being codifiable. Simultaneous resolution *forces* a fixed pipeline.

Command agency is real, but it is bounded so one player does not own the whole
ship. Station holders declare their own station orders: the gunner chooses the
shot, the lookout chooses whether to read intent, damage control chooses what to
save, and the helm executes the maneuver. On a fully manned ship, the captain
settles the shared movement/posture decision when the table needs a final call
and takes one command action, expressed two ways that do **not** reorder the
pipeline:

- **Posture** — a per-turn stance that *biases* the fixed pipeline:

  | Posture | Effect | Tradition that shines |
  |---|---|---|
  | Gunnery priority | lock heading (−maneuver), stabilize guns (+to hit / better arcs) | Otharan (stable platform) |
  | Maneuver priority | +maneuver / extra move; firing at penalty (jinking spoils aim) | Marovari (thrust) |
  | All hands | shift crew to repel boarders or damage control; guns/maneuver suffer | Ilvane (rapid repair) |
  | Steady | balanced | — |

  Posture is also a faction-feel and component hook (a fire-control set removes the
  maneuver-priority firing penalty; an Ilvane signals set shares a posture across a
  fleet) and it feeds the cross-scale coupling below (maneuver-priority = more hard
  turns = more deck chaos).

- **Command action** — focus fire, grant a station an extra action, rally crew
  (restore/steady the pool), or clarify the movement priority when the table is
  split. In-turn agency without touching the pipeline or taking station ownership.

So command shapes the turn through posture, movement intent, and support, not by
rewriting the physics or choosing every station's action. Codifiable, commanded,
and still shared by the table.

## Time scale and nesting

- **1 ship turn = 5 personnel rounds (fixed).** A boarding melee fits inside one ship
  turn's gap. The ratio is fixed, not per-encounter — fixed keeps the two clocks
  coherent. (5:1 is deliberately tight: it maximizes carry-over and cross-scale
  interplay, which is the point. The only cost is fiction — a "ship turn" is not a
  literal single 30-second maneuver but an abstract *pulse* of simultaneous activity;
  we accept the abstraction for the drama.)
- **Boarding zooms in.** When boarding resolves in the pipeline, the engine opens a
  **nested personnel-combat encounter** (normal creature initiative) on the deck,
  runs it **time-boxed to 5 rounds**, then zooms out to the next ship turn with the
  outcome baked in.
- **Time-boxed with carry-over.** A boarding not settled in 5 rounds **continues**
  into the next ship turn's gap — and meanwhile the ships have maneuvered again
  ("we couldn't take the deck before their consort closed"). The fixed ratio keeps
  both clocks in lockstep.

## Reciprocal coupling — battle impacts ship, ship impacts battle

This is the heart of it. The two scales are not independent; they inject events into
each other at the zoom boundary, both directions.

**Battle → ship (child → parent), applied at the next ship turn:**

- Casualties drain the crew pool → fewer stations manned.
- A captured station (helm, a battery) works for the enemy or is disabled.
- A defender killed/downed at a station → that station goes unmanned mid-turn.
- Sabotage (boarders set a fire, foul the rigging) → conditions on the ship.

**Ship → battle (parent → child), injected into the nested melee:**

- A **hard maneuver** (come-about) → everyone on deck makes a balance save or fall
  prone / **go overboard**. Order a hard port turn to break an arc and you throw your
  *own* boarders around too.
- A **ram** → both decks jolt: prone saves, falls, scattered footing.
- A **hull breach / flooding** → a stretch of the deck becomes difficult terrain or a
  hazard zone in the melee.
- A **broadside landing** → splinters/concussion as a local hazard.

The payoff is **cross-scale tradeoffs inside a single decision**: the crew choosing
maneuver-priority to survive the next broadside knows it will scatter the boarding
party on the enemy deck. Pulling Dorn off the helm to repel boarders means the ship
can't come about next turn. Battle and ship are one situation at two zoom levels.

## Stations and actions

All actions are checks/attacks (existing primitives) with ship content.

| Station | Actions | Notes |
|---|---|---|
| Helm | come-about, close/disengage, set up ram | Helm check vs ship maneuver; "becalmed"/"dead in the water" zero it |
| Sails / Rigging | full speed, trim, brace | movement modifiers; manning cost |
| Gunnery (per battery) | fire battery, called shot (mast/helm/rudder) | **arc-gated** by facing; `reload` (ordnance resource); `crew_required`; figure tags (a khevra-lance ignores hull threshold) |
| Damage Control | repair hull, douse fire, clear rigging, man pumps, reload | removes conditions / restores resources / heals; competes for crew |
| Navigation / Lookout | read wind/current, claim weather gauge, read enemy intent, spot hazard | tactical; the strategic side is [Spatial and travel](SPATIAL_TRAVEL.md) |
| Command | focus fire, grant station action, rally, set posture, settle movement intent | coordination without owning other stations |

Conditions are typed instances like any other: hull breached, taking on water,
afire, becalmed, rigging fouled, crew panicked, dead in the water.

## Information — hidden by default, bought with actions

Enemy declarations are `dm_only` until the reveal. Players have **no** insight into
enemy orders unless they earn it:

- A Lookout/Nav **read-enemy-intent** action reveals one enemy ship's posture or one
  declared station order before you commit.
- Setwork can extend this (a scrying figure reveals more; an Ilvane signals set shares
  intel across your ships); Savarran warding can **mask** your own declarations.
- Some intent leaks through the **descriptive layer** for free: a Marovari hull
  visibly rigged for speed telegraphs maneuver-priority. Reading the enemy is partly
  reading their silhouette.

Information is a contested resource, which is what makes Lookout/Nav and certain sets
worth their crew.

## Components and traditions (ship setwork)

A ship is frame + installed **sets** (setwork). A set modifies the host's profile,
adds actions (an **autopilot** set lets the Helm act unmanned — it changes the
*action economy*, not just numbers), adds passive rules including **multipliers** (a
ram amplifier doubles collision damage — the khevra amplification motif), adds tags
(installing setwork makes the ship `khevric`, which the Asha contamination extension
keys off), costs a setwork slot + charge, and carries a failure mode (overdraw,
instability).

A **tradition is a curated component bundle** — a few signature sets, a signature
action, a failure personality, and a descriptive identity — not a pile of per-faction
rules. Marovar/sorrellian plays hit-and-run and fails by overdraw; Otharan plays the
wall and fails by sluggishness; Savarran counter-punches and is hard to repair in the
field; Ilvane outlasts and coordinates. Numbers are the least of it; the felt
difference is *different things to do, a different way to win, a different way to
break*. (Components and the composable-modifier model are the general engine primitive that
ship upgrades instance — see [Rules engine](RULES_ENGINE.md) "Effects And Modifiers"
and "Components.")

## Settled vs open

Settled in design:

- Station economy + crew-as-resource; simultaneous declare → deterministic pipeline.
- Fixed pipeline order; command agency via **posture + movement intent + command**,
  not phase reorder or choosing every station action.
- **5:1** fixed ratio; boarding **time-boxed with carry-over**.
- Reciprocal ship↔battle coupling via events at the zoom boundary.
- Enemy declarations hidden; information bought with actions/sets/silhouette.
- Tactical scope: range rings, bearing/arcs, five altitude bands, wind + weather
  gauge; arc-gating as a discrete lookup; **forced-down (altitude-0)** as a defeat
  axis distinct from hull-0; sea ships altitude-locked.

Open / to author (content and tuning, not design forks):

- The exact posture list and the per-posture math.
- The station/action catalog specifics and per-weapon arcs/ranges.
- The ram/collision and called-shot formulas (rule grammar).
- The set/figure catalog per tradition and their failure mechanics.
- Whether the 5:1 ratio survives playtest, wants a nudge, or needs an
  objective-based boarding shortcut that preserves cross-scale consequences without
  running a full fight inside every ship turn.
