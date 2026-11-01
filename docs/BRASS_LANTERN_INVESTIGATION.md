# The Brass Lantern Investigation

## Situation

This worked example explores an existing location, NPC, and secret without
prescribing that the party uncovers them. The party is in
`loc:caelport.brass_lantern`, where `npc:wick` tends the bar. A real candle
burns, and a bricked arch is visible behind the taps. The party may notice
those visible details without a check. It does not automatically know what is
behind the arch or why Wick maintains the flame.

The private source `secret:the_kept_flame` is held by Wick and Tovin. Wick's
seed knowledge has `can_share: false`; Tovin's has `can_share: true`. That
difference is a constraint on disclosure, not a script forcing either person
to tell the PCs everything. The shrine and its contents remain private until
the PCs discover them through authorized events.

## Three Ways To Follow The Question

The party might never ask about the arch; if so, play continues elsewhere.
If it does investigate, these routes can be followed independently or in
combination. They are opportunities, not a mandatory sequence.

1. **Ask Wick.** The PCs may ask about the candle or the arch. A casual
   question does not by itself require a check: Wick can answer, avoid the
   question, or offer a mundane explanation within his knowledge and stance.
   A risky request to disclose a guarded secret uses the social DC and
   disclosure contracts if a check is warranted. A strong result cannot erase
   `can_share: false`; a clue or counter-offer is the default maximum unless
   independent reveal authority exists.
2. **Examine the room.** The candle and bricked arch are visible. A player
   describing a credible examination can learn additional *authored* details
   that the vantage exposes without treating a roll as mandatory. The
   existing location description does not specify a hidden entrance procedure
   or what a close inspection reveals, so do not invent a mechanism or reveal
   the shrine merely because a check scored high. A new specific physical
   detail needs an authorized source or a separately accepted world change.
3. **Seek another witness.** Tovin tends public lamps in the Undercroft and
   knows the secret; his role as shrine keeper is private. The party may
   encounter or seek him through information it actually possesses. If the
   party has no lead to him, do not magically tell it he is a keeper. Whether
   he shares a clue or invites the party to the shrine follows the encounter,
   his knowledge and stance, and any applicable reveal conditions.

These are not a guarantee of success. Repeatedly asking an unchanged question
is not a new check; a promise, observed help, new evidence, or a different
request can materially change the situation. The party may also pursue an
approach not listed here.

## Worked Social Boundary

Vanya asks Wick to reveal everything he guards behind the arch. If the
orchestrator determines a check is appropriate, it records a social DC source
with the current relationship, relevant intention, ask scope, and permitted
range. The roll produces a degree; the disclosure decision separately checks
what Wick knows and may share.

An illustrative strong result can support a **clue** or a **counter-offer**
within Wick's current authority. It does not itself authorize a full reveal
of `secret:the_kept_flame`. The actual words and the content of any clue must
be grounded in his authorized knowledge and the situation. Wick's seed
authorizes the bounded admission "I don't keep the candle for the draft."
He may choose to make it privately; it does not reveal the shrine or the kept
flame. A refusal or
complication on failure does not automatically change relationship state;
a sourced relationship update must pass its own delta policy.

If Wick privately tells Dorn something, only the explicitly authorized human
controller's private delivery and
knowledge can contain it. A later table-facing recall excludes it until the
knowledge is delivered to the table through an accepted event. A false rumor
is recorded as a claim or belief, not as established world truth. Tovin or
Wick may independently choose to disclose more only through the defined
authority and event paths.

## Aftermath

The party may make a promise, uncover a clue, leave, or return in a later
session. Track only load-bearing outcomes with their source and audience:
delivered messages, relevant knowledge, a bounded relationship change, or a
triggered clock. `clock:hearthward_exposed` advances only if its actual
authored trigger is met; curiosity alone is not exposure. Deferred faction
reactions follow consequence triage rather than becoming automatic world
changes.
