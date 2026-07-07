# NPC Sub-Agents

## Position

NPCs should be real sub-agents. They need isolated memory, private knowledge,
individual goals, and scoped tools so they behave like distinct people in the
world rather than variants of the DM's voice. NPCs use identity brain capsules;
forkable expert capsules such as loremasters are covered separately in
[Brain capsules](BRAIN_CAPSULES.md).

This does not mean every live response becomes a slow multi-agent committee. The
DM orchestrator owns the table-facing stream. NPC sub-agents run in the
background, prepare stances, and are called directly only when their input is
worth the latency.

## Isolation Boundary

Each NPC agent has:

- Immutable base profile: voice, personality, background, values, flaws, and
  starting goals.
- Private mementos and memories.
- Current intention state: what the NPC wants, fears, suspects, and plans.
- Relationship state with PCs, NPCs, factions, and places.
- Tool grants that define what the NPC can know or do.
- Event subscriptions for things the NPC observes, hears about, or learns later.

NPCs do not receive global omniscient campaign context. They see the world
through their tools and event subscriptions. The DM orchestrator may know hidden
campaign state, but it should not leak that state into NPC prompts unless the NPC
has a reason to know it.

## NPC Tool Gateway

Build an NPC tool gateway over shared typed contracts.

Required surfaces:

- Long-lived REST service for runtime agent/tool calls when a process boundary is
  useful.
- Direct service functions for hot in-process paths.
- CLI wrapper for development, testing, replay, evals, and debugging.

Deferred surface:

- MCP adapter for sharing or external agent interoperability, only after the REST
  and CLI contracts are stable.

The same tool contracts should power every surface.

Example tool groups:

- `npc.observe_scene`: visible room, lighting, hazards, nearby creatures, audible
  dialogue, and sensory facts.
- `npc.get_visible_pcs`: PC identities, known public traits, apparent condition,
  and current position if visible.
- `npc.get_visible_tokens`: battle-grid tokens and positions the NPC can
  perceive.
- `npc.get_known_facts`: facts known to this NPC, filtered by provenance and
  secrecy.
- `npc.get_known_places_routes`: locations, ports, roads, sea lanes, airship
  routes, hazards, and territories this NPC knows or can currently observe;
  backed by spatial/travel projections but filtered through NPC knowledge.
- `npc.get_relationships`: relationship summaries involving this NPC.
- `npc.get_inventory`: items and resources owned or carried by this NPC.
- `npc.get_rules_state`: only the mechanical state the NPC can use.
- `npc.propose_speech`: candidate line, target, tone, and intent.
- `npc.propose_action`: candidate action with desired effect and rules hook.
- `npc.set_intention`: update private short-term plan or emotional stance.
- `npc.request_dm_attention`: tell the orchestrator the NPC wants to act, speak,
  hide information, flee, bargain, or start a scene.

NPC tools are read-mostly. Any write is a proposal or private-memory update,
never a direct mutation of canonical rules state.

Do not start a tool server per NPC materialization. NPC activation should load
the NPC capsule, assign scoped grants, and attach to already-running services.
Tool discovery and manifest construction must not sit inside a live turn.

## Orchestrator Arbitration Of Proposals

`npc.propose_speech`, `npc.propose_action`, and `npc.request_dm_attention` produce
*proposals*, not effects. The DM orchestrator arbitrates every proposal before
anything reaches the table or canon. This is the receiving side of the invariant
that NPCs are proposed-and-arbitrated, never directly mutated.

Arbitration resolves a proposal to one of:

- **Accept** — the orchestrator commits the outcome, but only through the
  appropriate typed path, never the NPC's own write: a delivered line
  (`message.delivered` / `message.delivered_to_npc`), a live typed tool
  (`relationship.update`, the rules tools), or a dream patch. Which path follows
  the live-vs-dream rule in [Game world schema](GAME_WORLD_SCHEMA.md): table-driven,
  low-stakes effects commit live; loyalty/stance/clock/faction-level changes go to
  dreaming as reviewable patches.
- **Defer** — hold the proposal as prepared stance for a later beat, or route it
  into dreaming; nothing commits now.
- **Reject** — drop the proposal and keep it as an audit record, undelivered.

**NPC-to-NPC contention.** When two NPCs propose opposed actions in the same scene
(one moves to commit a faction, another counsels against it), the orchestrator
arbitrates between the competing proposals — no player input is required to reach a
resolution. It weighs the NPCs' goals, relationships, and standing, and may invoke
the rules engine (a contested social check) when a mechanical resolution is
warranted. When PCs are present and the outcome is high-impact, it surfaces the
contention as a playable beat and lets the table act before committing any standing
change, consistent with the player-agency rule. A contentious proposal the
orchestrator can neither accept nor cleanly reject (it would change standing canon
and no clear table outcome exists) is deferred to a dream patch and the operator
review queue rather than forced live.

*(Open question: whether arbitration should emit a dedicated
`npc_proposal.arbitrated` audit event, or whether the existing accept/defer/reject
trail on agent runs and patches is sufficient.)*

## Background Runtime

NPCs should be able to run outside the immediate player turn.

Background work:

- React to newly delivered events.
- Update intention state.
- Prepare likely responses to current scene pressure.
- Notice private opportunities or threats.
- Queue requests to the DM orchestrator.
- Participate in post-session dreaming.

The live DM can then ask: "What is this NPC's prepared stance?" rather than
starting from zero on every turn.

## Live Path Contract

The live path has strict latency limits.

Allowed live behaviors:

- Use already-prepared NPC stance/state.
- Call one NPC sub-agent directly when the scene depends on that NPC's authentic
  response.
- Stream a short NPC line after the DM has already acknowledged the player.
- Fall back to a safe, low-commitment line if the NPC agent misses its deadline.

Disallowed live behaviors:

- Sequentially call many NPC agents before the DM says anything.
- Let an NPC tool call mutate canonical state directly.
- Let a slow NPC response block barge-in or audio cancellation.
- Treat undelivered or aborted text as remembered conversation.

## Persistence

Persist:

- NPC agent runs with model, prompt inputs, tool calls, timing, and output.
- Delivered NPC speech and actions as canonical events.
- Aborted or rejected NPC drafts as audit/internal events.
- Private intention summaries and memento proposals.
- Tool-grant changes and event-subscription changes.

Do not persist raw chain-of-thought as memory. Store concise private intention
summaries, decisions, and provenance instead.

## Evals

NPC quality needs tests early.

Minimum evals:

- The NPC recalls a direct promise after leaving and returning.
- The NPC does not know a secret it never observed.
- The NPC remembers a relationship change after post-session dreaming.
- The NPC cannot call a tool outside its grants.
- An aborted NPC line is not recalled as delivered dialogue.
