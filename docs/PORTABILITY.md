# Portability And Deployment Tiers

## North Star

Dungeoneer should be shareable, not "only the author can run it." The premium
home build is a target, not a prerequisite. Someone with one good GPU — or, in
time, one small portable box — should be able to run a coherent Dungeoneer, just
at a lower tier.

This is a constraint on how we build now, not a future feature. The expensive,
home-specific machinery (the multi-machine rig, the privacy boundary, the
restricted-host offload) must stay isolated behind stable interfaces so the portable
core never depends on it. If the core assumes the author's topology, the product
becomes unshareable by construction.

## What Is Heavy And What Is Portable

Most of what makes Dungeoneer special is not the heavy part.

- **GPU-anchored (varies by hardware):** the DM model, the perception VLM,
  streaming STT, streaming TTS, image and video generation.
- **Portable (runs on a laptop today):** the DM orchestrator, the event store,
  the rules engine, NPC capsules and memory, retrieval, spatial/travel queries,
  state, and history.

The game — rules, persistent memory, NPCs that remember, orchestration — is
already portable. Only inference is bolted to specific hardware. The
differentiator is the system, not the size of the model. A small or MoE DM with
the full memory and orchestration stack is most of the experience; raw model
horsepower is the most replaceable component in the design.

A "tiny mobile DM" is therefore not a different product. It is the same portable
core driving smaller, cheaper inference.

## Deployment Tiers

The same codebase should run at several tiers. A tier is a deployment profile
that selects model backends and toggles optional capabilities. It is config, not
a fork.

- **Full home rig:** 5090 + 4090 + restricted-host 6000 Ada + N150. Max quality,
  all features, privacy boundary, async dreaming and media. The current target.
- **Single big GPU:** one strong card hosts the DM and time-shares the rest.
  Reduced concurrency, most features intact, one box.
- **Mobile / portable:** a single small box or a capable laptop. Small or MoE DM,
  light STT/TTS, perception and media optional or async, possibly push-to-talk
  accepted on the casual tier. The shareable tier.
- **Bring-your-own-inference:** the gateway points at a remote or hosted endpoint
  for heavy models. Maximizes shareability, trades away pure-local; offered as a
  choice, never the default, and bounded by the privacy rules of whoever runs it.
- **LAN party / ad-hoc cluster (niche):** friends bring gaming PCs and the
  capability registry schedules services (extra NPCs, perception, media) across
  whatever shows up — buying concurrency, not a bigger model, since LAN bandwidth
  rules out splitting one model. Guest machines are restricted hosts by default,
  trustable per session. Mostly an example of how far the discovered-profile
  design stretches; assumes spare GPUs few people have lying around.

## Rules That Keep It Portable

Architectural constraints, enforced from Phase 0:

- **The core talks only to the gateway.** The orchestrator, rules engine, memory,
  and state never address a specific host, GPU, or service location. They request
  a capability (a DM completion, a perception pass) and the active profile
  resolves where it runs.
- **Topology lives in profiles, not code.** Which GPU does what, the privacy
  boundary, and the restricted-host offload are properties of the home profile, not
  assumptions baked into orchestration. The privacy boundary is a feature of one
  deployment, not of the product.
- **Capabilities are discovered, not assumed.** The core asks the active profile
  what exists: is there a perception VLM, a video service, a multi-speaker audio
  stack? It adapts to the answer.
- **Optional services degrade, they do not hard-fail.** A tier without live image
  generation shows text and queues art for later. A tier without big-VLM
  perception falls back to a smaller model or manual grid entry. A missing
  capability lowers the tier; it does not break the session.
- **Spatial/travel is not optional.** Every supported tier runs Postgres with
  PostGIS and pgRouting. This is CPU-light compared with inference and is part of
  the portable core, not a premium hardware feature.

## Tradeoffs By Tier

Lower tiers cost quality, honestly:

- Smaller DM: less nuanced narration and NPC voice; the memory and rules systems
  carry more of the experience.
- Perception: a weaker VLM or manual token entry instead of high-end grid reading.
- Media: async-only or disabled image and video.
- Audio: the chaos-grade multi-speaker stack may reduce to simpler capture or
  push-to-talk on casual tiers.

The bet is that the floor is still good, because the floor is the orchestration,
memory, and rules — not the model. If that bet holds, Dungeoneer is shareable
without becoming a different product.

## Relationship To The Home Rig

None of this slows the ambitious build. The home rig stays the flagship profile
and the place new capabilities are proven. Portability only requires that those
capabilities enter through the gateway and the capability registry, so that
turning one off, swapping it, or shrinking it yields a working lower tier instead
of a broken one. The cost of preserving this is near zero if honored from the
start, and a painful untangling if discovered later.
