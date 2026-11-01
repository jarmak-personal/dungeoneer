# Adventure Play

## Purpose

The world model says what is true and the rules engine says how a declared
action resolves. This document describes the play between those boundaries:
how a party finds a problem, makes informed choices, explores, travels, and lives
with the outcome. It is not a mandatory quest script. A party can refuse a job,
leave a site, change sides, or invent an approach.

[The Greywake Cull](GREYWAKE_CULL.md) is a worked opening-tier example. It is
an illustrative adventure, not a required campaign event or a replacement for
the existing Aurevost seed.

## The Adventure Loop

1. **Opportunity.** Present an actionable situation through an appropriate
   person, observation, rumor, or consequence of past play. Give the party a
   reason to care without assuming it accepts.
2. **Understanding.** Establish what the characters can reasonably learn:
   immediate stakes, known dangers, obvious costs, reward terms, and what is
   uncertain. A patron's claim is a claim, not omniscient truth. Give players
   time to ask questions, bargain, prepare, or seek another source.
3. **Commitment.** The party chooses an objective and approach. The DM states
   consequential tradeoffs before they become irreversible when the characters
   could reasonably foresee them. An accepted commission is an obligation with
   agreed terms, not permission to control the party.
4. **Action.** Travel, investigate, explore, negotiate, fight, or leave. Resolve
   a check only when its result and consequences matter. Use the active rules
   pack for mechanics; the DM describes the situation, not the outcome in
   advance.
5. **Outcome.** Apply established mechanical and immediate fictional effects.
   Deliver payment or other rewards only when their conditions are satisfied,
   or play out a dispute. A job can end in success, changed terms, partial
   completion, withdrawal, or failure without ending the campaign.
6. **Aftermath.** The party chooses its next direction. NPCs respond according
   to what they actually learned; clocks and deferred consequences follow
   their own explicit triggers. Record a promise, item transfer, or changed
   relationship when it is load-bearing, not every piece of conversation.

## Choosing And Resolving Actions

- Ask what the player is trying to accomplish and how when either is unclear.
  Tell them what their character can perceive and the obvious risks.
- If an action is feasible, unopposed, and has no meaningful cost or uncertainty,
  it succeeds without a roll. If it is impossible under the current fiction or
  pack, say what prevents it and offer relevant alternatives, not a fake roll.
- If the outcome is uncertain and consequential, specify the ability, DC or
  contest, stakes, applicable modifiers, and who sees the roll before rolling.
  An unknowable hidden DC need not be disclosed, but the nature of the risk
  should not be concealed if the character can see it.
- A failed roll does not give the same attempt a free reroll. A materially
  changed approach, new information, help, equipment, or circumstances can
  justify another attempt; otherwise the party must accept the outcome, pay an
  established cost, or try a different path.
- Use the pack's resolution and the social disclosure rules where relevant.
  Do not convert a roll into an unrelated punishment, a compulsory PC decision,
  or a new mechanical effect without a rules-owned source.

## Sites And Exploration

A site is a connected set of places, obstacles, occupants, and opportunities,
not a single perception check. Describe what is apparent on arrival; hidden
details require a credible vantage, examination, or discovery. When a player
describes an effective method that exposes a clue, deliver it without a roll
unless the method itself has a meaningful risk or uncertainty. Rolls can affect
time, danger, precision, or additional information; a sole essential lead must
not disappear solely because of one failed check. The party may still fail to
find a lead if it never investigates an accessible source.

Track time and consumables when they matter. The pack governs light, spells,
rest, carrying, and exhaustion; a cantrip or item works only as its actual
definition permits. Do not assume darkness is a resource when the party has a
reliable light source, and do not invent a light failure merely to preserve a
desired challenge. A search or harvest whose duration is specified advances
world time by that amount. Other scene durations may remain approximate.

A site should support more than one credible approach where the fiction
permits: for example, a guarded entrance, a dangerous alternate way, or
negotiation with an occupant. Players may retreat and return. What changes
while they are away follows authored triggers or an accountable NPC/faction
decision, not a reset to the original scene.

## Travel

The spatial system supplies route, ETA, risk, visibility, and assumptions; it
does not choose for the players. Before departure, offer the known alternatives,
their approximate durations, foreseeable costs and hazards, and what the
characters do not know. A hidden danger stays hidden unless independently
discovered; uncertainty is not a license to invent a precise false map.

The party chooses route, transport, and relevant preparations. A travel plan
records the choice, departure time, passengers, vehicle, supplies where
relevant, and the assumptions used for ETA. A proposed plan is not a completed
journey. Travel progresses through the existing `travel.started`,
`travel.progressed`, `travel.interrupted`, and `travel.completed` events.

Summarize a stretch when nothing meaningful requires a decision. Open a scene
when the party can make a meaningful choice or an established hazard occurs:
an inspection, storm, rescue, or vessel breakdown. A scene states its immediate
stakes; the party may change course, spend resources, negotiate, stop, or turn
back. Resolve an interruption through the relevant pack and state tools, then
recalculate the remaining journey from accepted changes. Do not roll for an
encounter merely because travel is long.

## Investigation And Social Play

Claims, clues, and facts are distinct. A witness can be wrong, lie, or lack
knowledge. A clue points to something the characters can follow; it does not
automatically prove the interpretation. Offer multiple independently
discoverable routes to a load-bearing conclusion when the fiction supports
them, and let players form their own theory.

The social system governs bounded asks, attitude, disclosure, and relationship
changes. Information, leverage, a different offer, or a new witness can change
the situation; a persuasive roll does not erase an NPC's knowledge limits,
commitments, or an explicit blocked ask. A failure may cost time, close the
current approach, or create a sourced consequence, but must not silently
manufacture a new fact or turn an NPC hostile without an accepted route.

## Rewards, Time, And Continuing Play

State compensation and conditions at the point of agreement: coin, a share of
salvage, access, a favor, or another concrete benefit. Separate the employer's
promised payment from the proceeds of items the party owns. An unpromised bonus
is not assumed; a disputed price is a social situation, not a hidden die roll
that rewrites an agreement. Ordinary SRD prices use the active pack; authored
local offers need a source and can differ by buyer and circumstance. This is
not a whole-world price simulation.

For an agreed exchange, record the parties, item or service, amount and coin
denomination, agreed terms, and source. Before completion verify the payer's
available funds and the seller's authority over any item. Append payment
(`resource_changed` for each tracked balance) and custody (`item.transferred`
for a sale) together as one validated consequence batch: the coin debited must
equal the coin credited, no tracked balance may become negative, and no part of
the exchange commits on failure. A service payment has no item transfer. Any
untracked or unknown balance blocks mechanical settlement until an authorized
starting balance or other payment arrangement is established; do not assume an
NPC has unlimited funds.

The active pack defines rests, resources, injuries, and advancement; campaign
configuration selects among policies it supports. When a needed definition or
policy is absent, report a blocked rules resolution rather than inventing one.
Players choose their own advancement options; the engine applies them. The
setting does not dictate a progression system. See
[Character play](CHARACTER_PLAY.md#progress-and-advancement).

World time advances for elapsed travel, explicit activity durations, rests, and
other established passages of time. A clock advances only on its authored
trigger and through its typed route. A `session_ends` trigger means an actual
session end, not a travel day, rest, or arbitrary scene boundary. Session
splitting is therefore a real pacing choice for clocks authored that way.
