# Orchestration — The Live-Decision Layer

How the DM orchestrator decides what an inbound utterance *is*, and how it handles
traffic that arrives while a turn is in flight. Surfaced by system simulation as
the layer as under-specified as the rules engine was.

## Input Intent Classification

Every inbound utterance must be classified before routing. Classification is
**hybrid**: client-signaled where the player can cheaply say so, model-inferred
otherwise.

Message-type taxonomy:

```text
in_fiction_action     a declared action needing adjudication ("I attack")
in_fiction_speech     in-character dialogue to the table
npc_whisper           private in-fiction speech directed at an NPC
meta_question         a player asking the DM a question (rules, perception, "can I tell…")
ooc                   off-game table talk (non-canonical; see OOC handling)
lore_query            "what do we know about X" — a recall request
spatial_query         "where is X", "how far", "what is nearby", "how do we get there"
```

- **Client-signaled** first: an explicit channel/button (player remote "ask DM
  privately", an OOC toggle, a "whisper to NPC" target) sets the type cheaply and
  unambiguously.
- **Model-inferred** otherwise: the orchestrator classifies from content when no
  signal is given (most voice input).
- **Low confidence routes to a quick clarification**, never a silent guess on
  consequential traffic — consistent with the voice-chaos rule that consequential
  intent is never misassigned.

## The Parallel Side-Channel

A real DM can only think about one thing at a time. Dungeoneer does not have to.
Traffic splits into two lanes:

- **Serial lane (the turn):** anything that mutates shared canon or commits a
  table-visible result — actions, rolls that land on the table, narration everyone
  hears. These serialize into the live turn and respect the TTFA budget.
- **Parallel side-channel:** non-mechanical, non-shared traffic — lore questions,
  "what does my character notice," rules clarifications, private DM questions. These
  run *alongside* the active turn without stalling it.

The boundary is **shared-state mutation**, not topic. Edge case: a private question
that triggers a *hidden* check (the secret-question scenario) **computes in
parallel** — it rolls, resolves, and delivers privately — because its result
touches no shared canon and no table-visible commit. Only commits that hit the
table serialize.

This is a genuine capability, not just a concurrency fix: parallelized DM attention
smooths interactions in a way no human DM can, letting a player get a private
answer without the table waiting.

## Loremaster Live Fallback

A live loremaster fork is forbidden (latency), and warmup prepares likely experts —
but a player can always ask something unprepared. The fallback, *this turn*:

1. Answer from **direct retrieval** (lore_librarian + party knowledge + event
   search) at reduced depth, within the context-assembly budget — never a
   synchronous fork.
2. If even that is thin, give a **caveated recall** ("what you remember is…") rather
   than stalling or fabricating.
3. **Flag the domain** for the next warmup / prepare_likely pass, so the gap closes
   for next time.

Players never feel the machinery; they get a bounded honest answer now and a better
one later.

## Spatial And Travel Queries

Spatial/travel reasoning is a required tool surface, not model intuition. When the
DM needs to answer where something is, how far away it is, what borders it, what
ports or airship towers are nearby, or how long a route takes, the orchestrator
calls the spatial/travel tools defined in
[Spatial and travel system](SPATIAL_TRAVEL.md).

Live behavior:

1. Use fast spatial projections for containment, nearby, neighbors, distance, and
   prepared route summaries.
2. Use pgRouting-backed route solving when the answer affects a player choice
   ("can we get there before dawn?").
3. If weather, faction risk, or vehicle capability is uncertain, answer with
   assumptions and mark the uncertainty rather than inventing precision.
4. If travel will advance world time or move actors/vehicles, serialize it through
   accepted travel events; a route preview alone is only a proposal.

Spatial tools can run in the parallel side-channel when they do not mutate shared
canon. Travel execution that changes world time, party position, faction clocks,
or encounter risk serializes through the main lane.

## Player-Facing Capsule Redaction

A loremaster/expert capsule is DM-facing — its always-load material can include
`private_truth` and dm_only notes. Answering a *player* query directly from that
material would leak secrets (an invariant collision surfaced by simulation).

So any capsule-derived content bound for a table/player audience passes a
**player-facing projection** that strips dm_only material before delivery — the
same shape as the restricted-host sanitizer, but for the DM->player direction. No
capsule content reaches players unredacted.
