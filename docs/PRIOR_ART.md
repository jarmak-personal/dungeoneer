# Prior Art

## Purpose

This space is not barren. Before building, we surveyed existing AI Dungeon Master
work to learn from it and avoid reinventing it. The summary: the concept has many
attempts, most fail on the same axes (memory, rules, consistency), there is a
serious commercial incumbent, and the open-source community has independently
converged on much of this architecture. Dungeoneer's contribution is depth,
integration, and a deliberate move to the physical table — not novelty of concept.

## Commercial

- **Friends & Fables ("Franz")** — the leading AI DM. D&D 5e, ~100k+ users,
  $20-40/mo, browser + Discord. Cloud-hosted SaaS only: no local or self-host
  option, campaigns live on their servers. It is a virtual tabletop (on-screen
  maps, tokens, sheets). Architecturally it is a narrator LLM plus post-processing
  LLMs that decide state changes (move location, add items) — an orchestrator
  pattern, but with LLM-driven state updates rather than a deterministic rules
  engine. It does have real 5e mechanical tracking for combat and sheets, so it is
  a hybrid, not stateless.
- **AI Dungeon** (Latitude, 2019) — the original. Pure narrative text adventure,
  no rules, weak memory. The cautionary tale most criticism targets.
- **Hidden Door** and a crowd of 2026 entrants — mostly narrative, multiplayer,
  screen-native.

## Academic

- **CALYPSO** (UPenn + UMBC, AIIDE 2023) — LLMs as DM *assistants*, explicitly
  preserving the DM's creative agency. Direct support for the augment-not-replace
  framing.
- **FIREBALL** — ~25,000 real D&D sessions from the Avrae bot with true
  game-state, linking language to game commands and state. Use it for evals and
  grounding rather than reinventing eval data.

## Open-Source Convergence

Independent builders landed on the same shape, which validates the instincts and
means none of the individual pieces is novel:

- **AIDM** (deusversus) — 24+ specialized agents, ChromaDB narrative memory, an
  orchestrator, a multi-phase turn lifecycle. Closest to our orchestrator +
  sub-agent design.
- **PersistentDM** — local model, FastAPI + React, vector-based persistent world
  state. Closest to our stack.
- **fedefreak92/dungeon-master-ai** — Python state-machine rules engine with NPCs,
  skill checks, inventory.
- Others: dnd-ai (ChromaDB memory), LLMRPG (offline GM), TD-LLM-DND (Ollama).

## Documented Failure Modes

Reviews and research converge on three, which are exactly what this design
attacks:

- **Memory** — limited context windows, little or no cross-session memory;
  backstories forgotten within a few turns. The most-cited complaint.
- **Rules** — LLMs confidently wrong (a level-3 wizard "casting" 5th-level
  spells); HP, sheets, and saves often untracked.
- **Consistency** — even funded demos drift; the canonical example is a GDC 2026
  NPC insisting the tavern does not cook fowl while a cooked chicken sits beside
  it.

Pure vector retrieval does not solve memory: recall@k over a growing log is not
the same as an NPC reliably knowing the one fact that matters. This is why the NPC
design uses brain capsules, typed mementos, and post-session dreaming rather than
RAG alone.

## Where Dungeoneer Deliberately Differs

Not in concept, and not in any single pillar — those all exist somewhere. In the
combination, and on three axes the field mostly avoids:

- **Physical, in-person table.** Camera perception of a real battle grid and real
  voices in a real room. The market went to the screen and cloud virtual
  tabletops.
- **Local and private.** Runs on home hardware; no campaign data on someone
  else's servers.
- **Deterministic grounding.** A rules engine owns canonical state and narration
  cannot mutate it — a harder line than even the leading product, which lets an
  LLM decide state changes.

Plus a more rigorous memory model (capsules + mementos + dreaming) than the
typical "dump everything in a vector store" approach the failure reports describe.

These are differentiators because they are hard, which is also why others punted
on them. Differentiation and difficulty are the same edge here.

## References

- Friends & Fables: https://fables.gg/ and https://fables.gg/blog/how-franz-works
- CALYPSO: https://arxiv.org/abs/2308.07540
- AIDM: https://github.com/deusversus/aidm
- PersistentDM: https://github.com/tarnvaal/PersistentDM
- fedefreak92: https://github.com/fedefreak92/dungeon-master-ai-project
- dnd-ai: https://github.com/chungs10/dnd-ai
