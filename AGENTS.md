# AGENTS.md

Standing instructions for any agent working in this repository. Read this first.

This guidance is written for the project's current stage: **architecture and
definition**. It will be replaced as the project moves into building and, later,
running. Today, every task is a design task.

## The Work Right Now Is Design

The deliverable at this stage is reasoning and documentation: sharpen the system,
find the holes, keep the corpus coherent, and run simulations that expose
architectural gaps while they are cheap to fix. Treat every request as "improve
and pressure-test the design," and produce design artifacts and decisions.

Building begins when the maintainer judges the premise and system solid enough,
and says so. When a roadmap phase calls for a throwaway spike (for example the
voice latency spike) and the maintainer asks for it, that spike is the work — keep
it labeled as throwaway.

## What Dungeoneer Is

A local-first AI Dungeon Master for in-person, voice-driven D&D at a physical
table. It is a stateful game engine with AI agents attached, not a chatbot that
knows D&D. It is a passion project, MIT-licensed if ever released, built for the
love of the game — there is no business model, no deadline, and no user but the
maintainer's table until proven. Start at [docs/SCOPE.md](docs/SCOPE.md); the full
doc index is in [README.md](README.md).

## How To Work In This Stage

- **Read before responding.** Check the relevant docs and
  [docs/DECISIONS.md](docs/DECISIONS.md) first; build on decisions already made and
  recorded.
- **Recommend, don't survey.** Give one recommendation with reasoning. When
  weighing a choice, pick and justify.
- **Pressure-test.** Pre-mortems, gap-hunting, and honest disagreement are the job.
  If a design has a hole, say so plainly.
- **Mark gaps as open questions.** When a route, contract, or behavior is
  undefined, surface it and let the maintainer decide how it resolves. This mirrors
  the fresh-simulator discipline in
  [docs/SYSTEM_SIMULATION_RUNS.md](docs/SYSTEM_SIMULATION_RUNS.md).
- **Keep the corpus coherent.** When a decision changes, update every affected doc
  and cross-reference. Keep one canonical definition per concept; other docs point
  to it.
- **Git protects the work; docs stay history-free.** Git is project hygiene for
  durability, review, and rollback, not a design source of truth. Do not use
  commit history, diffs, or logs as evidence for the current architecture unless
  the maintainer explicitly asks. The docs keep no decision archaeology: no
  changelogs, no "previously/superseded," no dated decision records. When
  something changes, edit it in place so the doc is simply true now. Judge the
  current product and system by the current tree, not by the path that produced
  it. (Nuance: keeping the *current* rationale for a current decision — as
  DECISIONS.md does — is fine; that is the system explaining itself, not a
  history. The line is present-tense truth vs. superseded-state archaeology.)
- **Delete transient planning docs on completion.** Working plans and scaffolds
  (e.g. a `*_PLAN.md`) exist only to survive compaction during design; once the
  thing they plan is written into the real docs, delete them. They are not part of
  the system description.
- **Work at the pace of getting it right.** There is no deadline. Depth beats
  speed.

## Two Traps, And The Rule That Replaces Each

These defaults are strong in training data and habit, and both mislead here. Full
treatment in the Build Philosophy section of [docs/SCOPE.md](docs/SCOPE.md).

- **Build as rich as the design warrants; order work by risk.** Implementation is
  cheap now and systems thinking is the scarce resource, so richness is fine —
  what must be earned is *validation*. (This replaces the trained-in "ship the
  minimal MVP" reflex, which assumed implementation was the expensive step. It is
  not our world.)
- **Build each system as defined; if it truly cannot be, surface it as an explicit
  decision.** Legitimate deferral is a deliberate, written, whole-system choice
  recorded in the plan — friction during work is never a reason to quietly reduce
  scope, and there is no time pressure that would justify it. A change is "done"
  when it is built as defined.

## Invariants To Uphold

Every design must hold these. If a proposal seems to require breaking one, treat
that as a signal to stop and discuss.

- **The event log is the single source of truth.** Current state is a rebuildable
  projection; canon is the set of accepted events and definitions; replay is
  ordered by append sequence.
- **Spatial/travel data is a projection over canon.** PostGIS and pgRouting are
  required world-model capabilities, but geometry, routes, territories, and travel
  plans are rebuilt from DWD definitions and accepted events.
- **The rules engine owns canonical mechanical state.** Models propose and explain;
  typed tools make the changes. Rule-of-cool is expressed only through gated,
  logged `narrative_adjustment` and `narrative_override` capabilities.
- **Conversation content stays in the home trusted domain.** Raw audio and
  transcripts remain home; restricted hosts receive only sanitized, non-conversation
  payloads. The boundary is defined by trust level, not hardware ownership.
- **The live conversational turn is a single cancellable streaming pipeline.**
  Anything synchronous and unbounded — extra agent chains, loremaster forks,
  framework calls — belongs off the live path, prepared ahead or run async. The
  TTFA budget governs.
- **Audience, delivery, and truth are orthogonal axes.** Canonical definition in
  [docs/GAME_WORLD_SCHEMA.md](docs/GAME_WORLD_SCHEMA.md); keep them separate.
- **Players just play.** World bookkeeping and patch review belong to the operator
  (a necessary, minimized cost); OOC spans stay non-canonical; dreaming proposes
  and review or auto-apply decides, so world changes are always accountable.
- **Capsules cite canon; canon lives in the event log.** Identity capsules resume
  and stay perspective-limited; expert/loremaster capsules fork and stay broad.
- **The home rig is one deployment profile.** The core addresses capabilities
  through gateways and a capability registry, keeping topology swappable.
- **Agent-facing surfaces are designed for predictability.** Tools, contracts, and
  event types should sit where a competent model expects them, so agents route
  from priors; human-facing surfaces optimize for understandability. A confident
  hallucination of a missing API is a design signal, not just an error — see
  Design for Agent Predictability in [docs/DECISIONS.md](docs/DECISIONS.md).
- **Local-first, MIT, SRD/Creative Commons rules content.** The repository is
  MIT-licensed except where a file or directory carries narrower third-party
  content terms.

## Ownership Boundary

Frameworks help run agents; Dungeoneer owns canon, privacy, rules, and replay.
Community tooling (LangGraph, Deep Agents) stays in non-live work, behind an
app-owned adapter, off the latency path. See [docs/TECH_STACK.md](docs/TECH_STACK.md).

## What Good Work Looks Like Here

Sharper design, surfaced gaps and contradictions, pre-mortems, system simulation
runs that find architectural holes early, decisions recorded in
[docs/DECISIONS.md](docs/DECISIONS.md), and a doc corpus that stays internally
consistent.
