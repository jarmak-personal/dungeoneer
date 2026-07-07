# Brain Capsules

## Purpose

Brain capsules are durable, forkable activation bundles for agents. They solve a
different problem than retrieval: instead of starting every expert from a blank
prompt and asking it to read, Dungeoneer can load a prepared capsule that already
contains the right base identity, curated memory, working assumptions, and tool
scope.

NPC reactivation is one use. Loremasters are another.

Storage is cheap. The constraint is live activation time and context quality.

## Capsule Types

### Identity Capsules

Used for durable world actors, especially NPCs.

An identity capsule preserves a continuing point of view:

- Immutable base personality and voice.
- Private mementos.
- Current intention summary.
- Relationships, goals, fears, secrets, and obligations.
- Relevant history slices.
- Tool grants scoped to what the actor can know or do.

Activating an NPC resumes that specific person.

### Expert Capsules

Used for forkable specialists such as loremasters, rules aides, faction analysts,
cartographers, historians, style critics, and dream reviewers.

An expert capsule preserves an area of competence, not a person:

- Domain scope.
- Curated canonical facts.
- Indexed source references.
- Known contradictions and unresolved questions.
- Compression notes and retrieval hints.
- Tool grants for inspection, citation, and proposal.

Activating a loremaster forks a fresh expert instance from the latest capsule
snapshot. It should be fast because the hard priming work already happened during
dreaming.

## Loremasters

Loremasters are specialized expert capsules for world knowledge.

Examples:

```text
loremaster:world.greyhaven
loremaster:region.north_coast
loremaster:city.greyhaven
loremaster:faction.ash_ledger
loremaster:thread.missing_tax_ship
loremaster:calendar.greyhaven
loremaster:rules.5e_conditions
loremaster:table.dm_profile
```

The point is not one omniscient lore agent. The point is many cheap, scoped
experts that can be forked on demand.

Use cases:

- Fast answers to the DM orchestrator: "what matters about this faction right now?"
- Context assembly for live scenes.
- Consistency checks during dreaming.
- Source-aware answers for human inspection.
- Patch proposals when contradictions appear.
- Private media/request sanitization without sending raw world context across a
  privacy boundary.

**Live-path rule.** A loremaster fork is a model call, so a synchronous fork
inside a live turn re-introduces exactly the latency problem the NPC sub-agent
design avoids — an expert chain blowing the TTFA budget. On the live path, the
orchestrator consumes only **pre-prepared** capsule material (the `prepare_likely`
payload and always-load summaries assembled before the scene), never a fresh
synchronous fork. On-demand forking is for off-live-path work: dreaming,
consistency checks, human inspection, and between-scene preparation. If a live
scene needs expert depth that was not prepared, the answer is to prepare it for
next time, not to block the turn.

**Player-facing recall rule.** Loremaster material is source-aware input, not a
player answer. Anything bound for a player or table audience passes through
`lore.recall`, which converts party knowledge, event search, and capsule snippets
into `dwd.recall_answer.v1` claims with citations and redactions. A capsule may
know the hidden truth; the recall answer may only say what that audience can know.

## Forking Versus Resuming

NPC capsules are generally **resumed**:

```text
npc:marra_vell -> same actor, same private continuity
```

Loremaster capsules are generally **forked**:

```text
loremaster:faction.ash_ledger@dream_12
  -> fork expert run for question A
  -> fork expert run for question B
  -> fork expert run for consistency check C
```

A fork may produce notes, proposed patches, or improved capsule material, but it
does not mutate the capsule directly. Accepted improvements are appended as
events or reviewed patch results, then folded into the next capsule snapshot by
dreaming.

## Capsule Contents

Common fields:

```yaml
id: capsule:loremaster.faction.ash_ledger
schema: dwd.capsule.v1
kind: expert
subject: faction:ash_ledger
version: 12
snapshot_event_range:
  from: event:s0_seed
  to: event:s12_0199
visibility: dm_only
model_profile: lore_compact
tool_grants:
  - world.inspect
  - world.search
  - world.spatial.nearby
  - world.travel.route
  - patch.propose
```

Expert capsule body:

```yaml
base_brief: >
  You are a scoped world-lore expert for the Ash Ledger. Answer from canon,
  distinguish rumor from fact, cite source event IDs, and propose patches rather
  than inventing missing truth.
always_load:
  canonical_summary: "The Ash Ledger is a debt network operating through dockside loans..."
  public_face: "A lending house for sailors and small merchants."
  private_truth: "A blackmail and smuggling leverage operation."
  active_clocks:
    - clock:ash_ledger.coup
  active_threads:
    - thread:missing_tax_ship
  unresolved_questions:
    - "Who inside the Harbor Watch is already compromised?"
  contradiction_notes:
    - "Session 8 rumor says the Ledger burned the fishmarket; no canon fact confirms it."
retrieval_hints:
  preferred_entities:
    - faction:ash_ledger
    - npc:marra_vell
    - loc:greyhaven.crooked_lantern
  source_events:
    - event:s0_ledger_seed
    - event:s12_0048
```

Identity capsule body:

```yaml
base_brief: >
  You are Marra Vell as a private NPC actor. You know only what Marra knows.
  Propose speech/actions; do not mutate canon.
always_load:
  profile_ref: npc:marra_vell
  mementos:
    - memento:marra_iona_promised_protection
  current_intention: "Keep the party away from the cellar until the ledger men leave."
  known_secrets:
    - secret:ash_ledger_blackmail
```

## Dreaming Responsibilities

Post-session dreaming maintains capsules.

For identity capsules:

- Promote or demote mementos.
- Update intention summaries.
- Update relationships from delivered events.
- Check whether private knowledge leaked or is stale.
- Prepare likely next-session stances.

For expert capsules:

- Rebuild summaries from accepted events and definitions.
- Refresh active clocks, threads, and contradiction notes.
- Split oversized domains into smaller capsules.
- Merge duplicate or stale capsules.
- Produce capsule-diff patches for review when high-impact.
- Build "quick activation" payloads for likely next-session experts.

**Refresh is selective, not a full sweep.** A mature campaign may hold dozens of
loremasters (world, regions, seas, routes, cities, factions, threads, calendars,
rules domains);
refreshing all of them every session would blow the "dreaming finishes before the
next session" budget. Dreaming refreshes only capsules whose source event range
was touched this session, plus the `prepare_likely` set for the next session.
Untouched capsules keep their existing snapshot. Capsule refresh is one reason
dreaming can be slow, which is exactly why it must be scoped.

## Cold Start: Initial Capsules

Dreaming maintains and refreshes capsules — but at cold boot no dreaming has run,
so there is nothing to refresh. The **warmup pass** (see
[Lifecycle and bootstrap](LIFECYCLE.md)) creates the initial capsules directly from
the world definition, independent of dreaming:

- Build the first loremaster capsule(s) for the world and starting location from
  seed canon.
- Build identity capsules for NPCs likely present, from their seed profiles (base
  only — no mementos yet; mementos accrue through play).
- Populate the `prepare_likely` material for the opening scene.

This resolves the live-path tension directly: the live path forbids a synchronous
loremaster fork, and at cold boot there is no prepared material to use instead — so
warmup, which runs off the live path before the first scene opens, is where that
material is made. The first scene then consumes warmed material like any other
turn. Prepared stance produced by `prepare_likely` is stored on the capsule
snapshot (an always-load slot), not recomputed live.

## Tooling

Useful CLI surfaces:

```bash
dungeoneer capsule list --campaign greyhaven
dungeoneer capsule inspect capsule:loremaster.faction.ash_ledger
dungeoneer capsule fork capsule:loremaster.faction.ash_ledger --ask "What changed this session?"
dungeoneer capsule refresh --campaign greyhaven --since session:greyhaven_012
dungeoneer capsule diff capsule:loremaster.faction.ash_ledger --versions 11..12
```

Useful runtime surfaces:

- `capsule.resolve(subject, purpose)`
- `capsule.fork(capsule_id, run_context, deadline)`
- `capsule.prepare_likely(scene_id)`
- `capsule.propose_refresh(capsule_id, event_range)`

## Guardrails

- A loremaster is not a source of canon. It cites canon and proposes changes.
- Expert capsules can be broad; NPC capsules must remain perspective-limited.
- Fork output is not automatically written back into the capsule.
- Capsule snapshots must record source event ranges and schema versions.
- Private player messages and OOC spans do not enter capsules unless explicitly
  allowed by visibility rules.
- Restricted-host services never receive raw capsule contents.
- If a capsule summary contradicts the event log, the event log wins.

## Relationship To Retrieval

Retrieval still matters. Capsules are not a replacement for search.

Use capsules for:

- Always-load domain framing.
- Precomputed summaries.
- Known contradiction notes.
- Fast expert activation.
- Tool and permission scoping.

Use retrieval for:

- Exact supporting events.
- Recent changes.
- Uncommon details.
- Cross-domain connections.
- Citations and provenance.
- Spatial/travel details that should be answered from PostGIS/pgRouting-backed
  projections rather than stale capsule prose.

The activation pattern is:

```text
capsule always-load material
  + focused retrieval slices
  + current run context
  + scoped tools
  -> agent fork/resume
```

## Build Order

Phase 0:

- Add generic capsule contract and snapshot provenance.
- Add `identity` and `expert` capsule kinds.
- Add CLI inspection and fork stubs.

Phase 1:

- Use identity capsules for the first NPC activation flow.
- Add first loremaster capsule for the campaign or starting location.

Phase 2:

- Add faction/thread/rules loremasters for structured world state.

Phase 6:

- Dreaming refreshes capsule snapshots, prepares likely experts, and proposes
  reviewable capsule diffs.

Phase 7:

- Add capsule evals: recall accuracy, contradiction detection, source citation,
  leakage checks, and activation latency.
