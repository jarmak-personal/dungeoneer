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

The **tactical scope** uses a shared horizontal hex grid and discrete altitude
bands. Each ship's rules-owned position is an axial hex `(q, r)`, an altitude
band, and one of six headings. The engine computes the pairwise relationships;
the table can see a simple scope with range, bearing, and altitude instead of
performing geometry. Because all relationships derive from the same positions,
three ships cannot independently acquire contradictory pairwise distances.
These are tactical coordinates, not world-map coordinates.

- **Horizontal distance** is the number of hexes on a shortest path:
  `max(abs(dq), abs(dr), abs(dq + dr))`. A pack maps that distance to
  `engaged / close / medium / long / broken contact`; the thresholds and
  whether altitude changes a particular weapon's range are content that must
  be authored, not guessed. Breaking contact with one opponent does not remove
  a ship from an engagement with others.
- **Bearing & arcs** are derived separately in each direction using the
  algorithm below. A weapon checks its own permitted arcs, range, and altitude
  limits against the resolved positions; a target's arc from the firer need not
  be the firer's arc from the target.
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

An encounter records the initial positions, headings, altitude, wind, and
scope definition, with provenance. Spatial/travel data can inform setup when
its precision supports it; otherwise authorized encounter setup establishes the
missing tactical positions. Do not silently turn an approximate world route
into exact tactical coordinates. Accepted position events are canonical rules
state; pairwise ranges, arcs, and displays are rebuildable projections.

### Deriving bearing and arc

Use integer axial coordinates. Directions clockwise on the display are:

| Heading | Axial step |
|---|---|
| 0 | `(1, 0)` |
| 1 | `(0, 1)` |
| 2 | `(-1, 1)` |
| 3 | `(-1, 0)` |
| 4 | `(0, -1)` |
| 5 | `(1, -1)` |

For displacement `(dq, dr)` and each direction `(uq, ur)`, calculate
`2*dq*uq + dq*ur + dr*uq + 2*dr*ur`. The greatest score gives the bearing.
For a tie between neighboring directions choose the clockwise direction,
including `5 -> 0`. Subtract the observer's heading modulo 6: `0` is fore,
`1` or `2` starboard, `3` aft, and `4` or `5` port. Compute the reverse
bearing independently from the other ship's heading.

Ships in the same horizontal hex have no horizontal bearing, even at different
altitudes. Describe them as vertically aligned and use only a weapon or action
whose authored rule explicitly supports that geometry. At the same altitude,
same-cell occupancy instead requires the collision or contact rules; do not
silently pick an arc. Elevation is the signed target-band difference, with
absolute gap available for a weapon's limit. An actual altitude band is not a
claim of exact height in feet.

### Simultaneous movement and replay

All ships commit movement orders before movement resolves. Validate each
proposed path against its starting state, station capabilities, applicable
speed, turn, altitude, wind, and resource rules. The yet-to-be-authored action
catalog must define those costs and any rolls; a missing rule blocks that
resolution rather than allowing unrestricted movement. A resolved path is a
sequence of simultaneous discrete steps; a ship with no remaining steps holds
position while other ships finish. All updates for a step use the same
pre-step positions, not the result of iterating ships in an arbitrary order.

Before committing, identify at least a same-cell/same-altitude destination
conflict and two ships swapping the same three-dimensional endpoints in one
step. An actual collision is physical contact and can cause damage even when
neither captain intended it; a ram is a deliberate action that exploits
contact, not the only way contact can occur. How contact affects positions,
remaining movement, hulls, crew, and a boarding child, and how simultaneous
altitude changes and other swept-path intersections are handled, require
authored collision rules. Until they exist, block the collision-dependent
movement resolution without committing a partial phase; do not choose a winner
by ship ID or allow vessels to pass through each other. Stationary or
vertically separated ships remain subject to the same checks.
Once a valid movement phase resolves, record ordered position changes and
their source orders and dice; derive all pairs and weapon arcs from that
resolved state. Collision ordering and event payloads remain open contracts.

**Geometry fixture, not a complete ship turn.** Let A be `(0, 0)`, heading 0,
altitude 1; B be `(1, 0)`, heading 3, altitude 2; and C be `(1, -1)`, heading
4, altitude 1. All three pairwise horizontal distances are 1. B is in A's
fore arc and A is in B's fore arc; C is in A's port arc and A is in C's port
arc. B is one altitude band above A. Suppose an authorized movement rule
resolves these non-colliding simultaneous steps: A to `(0, 1)`, B to `(1, -1)`,
and C to `(2, -1)`, with headings and altitudes unchanged. The resulting
distances A-B, A-C, and B-C are 2, 2, and 1. B is now in A's port arc,
including the clockwise bearing tie. This demonstrates geometry only: it does
not grant those moves, name a range band, or authorize a weapon shot.

## The ship turn — simultaneous, but deterministic

"Everyone acts at once" cannot mean nondeterministic, or replay breaks. So
simultaneity lives at the decision layer and resolution is a fixed pipeline:

1. **Declaration.** Enemy ships commit their orders privately before receiving
   information about the party's orders. The party then assigns its stations.
   A Lookout can commit its station to read one enemy order or posture before
   the other party stations commit; that choice consumes the Lookout action.
   The party may use the revealed information when choosing its posture and
   remaining orders. Once committed, an order cannot be revised because of a
   later reveal. **Enemy orders are `dm_only` until authorized disclosure**;
   they are recorded inputs, not facts the party automatically knows.
2. **Resolution pipeline** — a fixed sub-phase order, deterministic tie-breaks:
   1. Navigation / positioning (weather gauge, wind, claim advantage)
   2. Movement (helm + sails; facing / range / altitude update)
   3. Heavy weaponry (arcs computed against the *resolved* positions)
   4. Boarding (opens the nested melee — see "Nesting")
   5. Tending / damage control (repair, douse, pump, reload)
3. **Emit deltas as events** in stable phase order.

**Replay invariant:** the pipeline is a pure function of the starting rules
state, versioned rules and scope, committed declarations, and recorded dice;
events have a stable append order. Simultaneity is feel; resolution is
deterministic.

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

### Orders And Effects Across The Boundary

The parent pipeline does not restart or interrupt a personnel round. A ship
order given while a boarding child is running is a declaration for the **next**
ship turn. If the order is a hard maneuver, resolve it in that turn's normal
movement phase, before heavy weapons and the boarding phase. An unavailable
station, lost capability, or other failed precondition prevents the order
from resolving; do not inject the maneuver's consequences merely because it
was requested.

If a hard maneuver resolves while a boarding child remains active, queue its
deck effect against the affected ship and the source movement event. When the
child next resumes in the boarding phase, resolve the sourced balance saves for
the actors then on that deck **before** its next personnel turn. The five-round
limit counts personnel rounds, not this boundary effect. A failed save may
apply prone or overboard only as defined by the active ship rules. If the
child has ended or an actor is no longer on the affected deck, do not apply a
stale effect to that child or actor.

Child results that affect station availability are recorded as they happen in
the personnel encounter and are included in the projection used for the next
parent declaration. A downed or captured hand cannot be assigned then; a crew
replacement is possible only if the station and crew-assignment rules permit
it. A child result does not retroactively invalidate a parent order already
resolved earlier in the current pipeline. Other casualties, captured stations,
and sabotage likewise reach parent decisions at the next parent boundary.

## Reciprocal coupling — battle impacts ship, ship impacts battle

This is the heart of it. The two scales are not independent; they inject events into
each other at the zoom boundary, both directions.

**Battle → ship (child → parent), applied at the next ship turn:**

- Casualties drain the crew pool → fewer stations manned.
- A captured station (helm, a battery) works for the enemy or is disabled.
- A defender killed/downed at a station is unavailable at the next parent
  declaration; the station is unmanned unless an eligible replacement is
  assigned under the applicable crew rules.
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
  declared station order before the other party stations commit. The reader
  chooses the enemy ship and whether to read posture or one named station's
  order. The result is delivered to the reader; speaking it aloud can make it
  table-visible through the ordinary delivery route. If that station has no
  order, the reader learns that it has no order, not a different secret order.
  The action does not reveal the whole plan or allow the enemy to revise its
  already committed orders.
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
- Tactical scope: shared hex coordinates, six headings, derived ranges/arcs,
  five altitude bands, wind + weather
  gauge; arc-gating as a discrete lookup; **forced-down (altitude-0)** as a defeat
  axis distinct from hull-0; sea ships altitude-locked.
- Pairwise ranges and directed arcs are derived from accepted positions and
  headings for every ship pair, not independently mutable facts.
- An unintentional collision is physical contact with possible damage; a ram
  intentionally exploits contact.
- An order during boarding takes effect no earlier than the next parent turn;
  a successful hard maneuver affects the child when it next resumes.

Open / to author (content and tuning, not design forks):

- The exact posture list and the per-posture math.
- The station/action catalog specifics and per-weapon arcs/ranges.
- Concrete movement action costs, speed, turning, climbing, paths, collision
  handling, simultaneous resolution/event ordering, and range-band thresholds.
- The ram/collision and called-shot formulas (rule grammar).
- The set/figure catalog per tradition and their failure mechanics.
- Whether the 5:1 ratio survives playtest, wants a nudge, or needs an
  objective-based boarding shortcut that preserves cross-scale consequences without
  running a full fight inside every ship turn.
