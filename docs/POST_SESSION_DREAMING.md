# Post-Session Dreaming

## Purpose

Dreaming is the slow consolidation stage that runs after a session. Live play
optimizes responsiveness; dreaming optimizes continuity, correctness, and future
setup.

It may take minutes or hours. That is expected.

## Inputs

- Complete session event log.
- Delivered player, DM, and NPC messages plus transcript spans.
- Rules tool calls and state deltas.
- Consequence plans with deferred and blocked effects from live play.
- Map perception results and confirmations.
- Asset prompts and generated media provenance.
- Current entity, faction, location, quest, and rules projections.
- Current spatial/travel projections: locations, route graph, territories,
  hazards, active travel plans, and vehicles.
- Prior mementos and relationship state.
- Prior brain capsule snapshots for NPC identity capsules and expert/loremaster
  capsules.

Aborted or internal generations are available for audit, but they are not treated
as things the table or NPCs heard.

## Pipeline

1. Freeze the session event range.
2. Replay events into fresh projections.
3. Compare replayed projections against stored current state.
4. Review delivered transcript spans for promotion candidates: transcript-only,
   claim, clue, knowledge edge, fact assertion, or state mutation.
5. Leave ordinary color as transcript evidence unless it affects future play,
   rules, privacy, recall, NPC behavior, or projections.
6. Flag drift, missing state changes, and unresolved contradictions.
7. Evaluate NPC memento promotions, demotions, and repairs.
8. Refresh brain capsule snapshots for NPCs and loremasters.
9. Update relationship summaries from delivered events.
10. Resolve deferred consequence-plan effects: clock outcomes, faction reactions,
   rumor spread, memento candidates, capsule refresh needs, and blocked-rule
   follow-up items.
11. Advance faction clocks, world clocks, rumors, and off-screen consequences not
   already resolved by live consequence plans.
12. Advance travel, route conditions, faction patrol zones, blockades, weather,
   rumor/news spread, and other spatial consequences.
13. Generate next-session prep bundles.
14. Run validators and eval fixtures.
15. Emit proposed state patches and review items.

## Outputs

- Session recap.
- Updated campaign timeline projection.
- Transcript promotion candidates that became claims, clues, knowledge edges,
  facts, or state patches.
- NPC memento proposals with provenance.
- Capsule refresh diffs for NPC identity capsules and loremaster/expert capsules.
- Relationship and faction updates.
- Resolved or proposed deferred consequence-plan effects.
- World-clock and quest-clock changes.
- Travel progress, route changes, territory/hazard changes, and spatial
  projection refreshes.
- Off-screen NPC actions and consequences.
- Next-session context bundles.
- Unresolved questions for the human table or DM operator.
- Optional media jobs for recap art, portraits, maps, or video.

Media jobs may run on the restricted-host GPU only after the home-side dream process
turns private session context into sanitized briefs. Raw transcripts, private
messages, NPC private thoughts, and unrevealed secrets do not cross the privacy
boundary.

## Canonical State Rules

Dreaming is not allowed to silently rewrite history.

- The event log remains the source of truth.
- Transcript spans are evidence, not canon truth. Promotion cites them; it does
  not rewrite them into structured state retroactively.
- Derived projections can be rebuilt.
- Low-risk deterministic fixes can be applied automatically if validators pass.
- High-impact changes become proposed patches requiring review.
- Any accepted patch is itself appended as a new event.
- Incompatible patches generated from the same replay slice form a conflict set
  and escalate together to operator review; no member auto-applies. See Patch
  Conflicts in [Game world schema](GAME_WORLD_SCHEMA.md).

Review is the host/operator's job, done asynchronously between sessions, never a
mid-play interruption — and never the players'. Players are pulled in only when a
change touches their own character's agency or a safety boundary, and then through
the existing consent/safety mechanics and in-fiction narration, not a patch
dialog. A background change players do not know about never needs their
confirmation. See the review-authority tiers in
[Game world schema](GAME_WORLD_SCHEMA.md).

High-impact examples:

- Changing an NPC's loyalty, long-term goal, secret, or core personality.
- Creating a major faction move.
- Resolving a quest branch.
- Changing PC-owned inventory, HP, resources, or relationships.
- Adding facts that players did not establish, discover, or trigger through a
  preauthorized live clock outcome.

## NPC Dreaming

Each important NPC gets a slow pass:

- What did this NPC observe or learn?
- What did this NPC misunderstand?
- What mementos should be promoted or demoted?
- Did relationships change?
- What does the NPC plan next?
- Does the NPC want to contact, avoid, betray, help, or investigate anyone?

NPC dreaming writes private intention summaries and proposed future actions. It
does not expose private thoughts to players unless later delivered through play.

## Loremaster Dreaming

Expert capsules get a slow refresh pass too:

- What facts, sources, threads, clocks, and contradictions changed in this domain?
- What route, territory, hazard, port, sea, airship, or travel facts changed in
  this domain?
- Is the capsule now too broad and should it split into smaller experts?
- Are there stale summaries or retrieval hints?
- Are there unresolved questions the DM should know before next session?
- What likely loremasters should be preloaded for the next session?

Loremaster dreaming writes refreshed capsule snapshots and reviewable capsule
diffs. A loremaster is not a source of canon; it cites canon and proposes patches.

## Next-Session Prep

Dreaming should leave the live system warm in a narrative sense:

- Prepared scene summaries.
- NPC stances for likely reappearances.
- Pending rules reminders.
- Likely player goals.
- Open loops and unresolved choices.
- Suggested encounter or social pressure points.

The goal is that the next session starts with coherent momentum without forcing a
scripted outcome.

## Failure Modes

- The dream invents facts that were never established.
- The dream promotes the wrong memento and changes an NPC incorrectly.
- The dream applies world consequences without review.
- The dream summarizes away a legally or mechanically important detail.
- The dream leaks one NPC's private knowledge into another NPC.
- The dream job runs so slowly that prep is missing when the next session starts.

These failure modes need replay tests, validators, and review gates before the
dream output can be trusted.
