# Dungeoneer

Local-first AI Dungeon Master for D&D-style tabletop campaigns.

The project goal is a complete AI DM that can run sessions by voice or text,
manage NPCs without losing context, own deterministic rules state, perceive a
map or battle grid through vision models, and generate supporting speech,
images, and video locally.

Agents working in this repo should read [AGENTS.md](AGENTS.md) first. The project
is in its architecture-and-definition stage: design work plus small validation
tooling, not product implementation.

## DWD Validation

The repository includes a small structural linter for human-authored DWD YAML.
It catches invalid YAML, duplicate and dangling IDs, containment cycles, clock
bounds, visibility leaks, and the stable seed contracts that exist today. It
allows unknown fields. Unknown kinds, schemas, enum options, and typed actions
are reported as `EXTENSION`: lint fails so the validator cannot silently drift,
but the diagnostic means the linter may need to learn a valid format addition.

The lint unit is the whole authored surface — worlds, rules packs, and
simulation scenarios — linted together, because references cross those corpora
(worlds bind NPCs to `rules:` stat blocks; scenarios reference world entities;
scenario fixtures may declare scenario-local actors that resolve only within
their own file). Running `dwdlint` with no arguments lints `worlds`, `rules`,
and `docs/simulations` where present.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/dwdlint
.venv/bin/pytest
```

The linter supports Python 3.12+ independently of Dungeoneer's Python 3.13+
application runtime. During deliberate format work,
`.venv/bin/dwdlint --allow-extensions <path>` ignores extension-only failures
while retaining hard structural and secrecy errors.

To enable the tracked Git pre-commit hook for this checkout:

```bash
git config core.hooksPath .githooks
```

The hook runs `uv run dwdlint worlds rules docs/simulations` before each commit.

## Architecture Docs

- [System scope](docs/SCOPE.md)
- [Prior art](docs/PRIOR_ART.md)
- [Tech stack](docs/TECH_STACK.md)
- [Game world schema](docs/GAME_WORLD_SCHEMA.md)
- [Spatial and travel system](docs/SPATIAL_TRAVEL.md)
- [Lifecycle and bootstrap](docs/LIFECYCLE.md)
- [Rules engine](docs/RULES_ENGINE.md)
- [Orchestration (live-decision layer)](docs/ORCHESTRATION.md)
- [Brain capsules](docs/BRAIN_CAPSULES.md)
- [System simulation runs](docs/SYSTEM_SIMULATION_RUNS.md)
- [Roadmap](docs/ROADMAP.md)
- [Technical decisions](docs/DECISIONS.md)
- [Deployment and session startup](docs/DEPLOYMENT.md)
- [NPC sub-agents](docs/NPC_AGENTS.md)
- [Frontend clients](docs/FRONTEND.md)
- [Latency budget](docs/LATENCY.md)
- [Voice chaos gate](docs/VOICE_CHAOS.md)
- [Hardware topology](docs/HARDWARE.md)
- [Privacy boundary](docs/PRIVACY_BOUNDARY.md)
- [Portability and deployment tiers](docs/PORTABILITY.md)
- [DM profile and improvement loop](docs/DM_PROFILE.md)
- [Post-session dreaming](docs/POST_SESSION_DREAMING.md)

## Core Principles

- The DM is an orchestrator, not a single prompt.
- NPCs are isolated sub-agents with private memory and capability-scoped tools.
- Rules and world state are updated through deterministic tools.
- Spatial and travel intelligence is first-class: PostGIS and pgRouting back
  geography, route, sea, and airship reasoning as projections over canon.
- Full history is the source of truth; summaries and embeddings are caches.
- NPCs are durable entities with private memory, relationships, goals, and
  event subscriptions.
- Local model services are swappable behind stable APIs.
- Dungeoneer is shareable: a portable core runs at multiple deployment tiers, and
  the home rig is one profile, never a hard dependency.
- Restricted-host compute (any GPU outside the home trust boundary) is isolated
  behind sanitized image/media request contracts; raw conversation content never
  crosses that boundary.
- Natural table speech is a launch gate: no push-to-talk, no forced slow
  enunciation, and no silent misattribution of consequential player intent.
- Visual perception proposes map-state changes; the rules engine owns the
  canonical battle state.
- Map perception is turn-gated and capture-on-demand, not continuous surveillance.
- A DM-controlled shared display can show generated images, video, text,
  handouts, and public state on demand.
- Player remotes can receive private DM/NPC messages with explicit delivery and
  visibility metadata.
- Post-session dreaming is slow, replay-based, and used to repair memory,
  validate world state, and prepare future machinations.

## License

Dungeoneer is MIT-licensed except where a file or directory states narrower
third-party content terms. SRD-derived rules material is tracked under its own
Creative Commons attribution terms in [rules/srd_5e](rules/srd_5e/README.md).
