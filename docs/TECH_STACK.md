# Tech Stack

This document maps the intended implementation stack. It separates default
choices from spike candidates and keeps the main ownership rule visible: frameworks
may help run agents, but Dungeoneer owns canon, privacy, rules, and replay.

Choices here are calibrated to a solo build of a passion project: pragmatic, lean
on maintained community tooling rather than reinvent it, stay in the maintainer's
comfort zone (NVIDIA serving) where it does not cost flexibility, and spend effort
only on the parts Dungeoneer must own outright.

## Stack Principles

- Prefer boring, inspectable services around the hard parts: state, rules, event
  replay, privacy boundaries, and deployment.
- Put fast-changing model runtimes behind app-owned gateways.
- Use maintained community agent tooling for non-live work rather than build what
  we do not need to — but keep it behind a Dungeoneer harness boundary and off the
  latency-critical path.
- The live path is the exception Dungeoneer owns outright: custom runner, direct
  control of latency, cancellation, and tool surface.
- Make every major choice portable across deployment profiles. The home rig is a
  profile, not a hard-coded assumption.
- Treat measurement as part of the stack: latency, tool calls, model runs,
  delivery status, and eval results are first-class records.

## Core Application

| Area | Default | Notes |
|---|---|---|
| Backend language | Python | Aligns with AI tooling, FastAPI, Pydantic, LangChain/LangGraph, vLLM, and speech tooling. |
| Python runtime | Python 3.13+, standard build | asyncio single-process orchestration is the concurrency model. Free-threading (3.14t) is reserved for the offline tactics sim only, never the app or the live path. |
| API service | FastAPI | HTTP/WebSocket gateway, validation, auth/session routing, and table-client transport. |
| Contracts | Pydantic + JSON Schema | Source of truth for event payloads, tool calls, rules deltas, model gateway requests, and privacy-boundary jobs. |
| Realtime transport | WebSockets | Table console, shared display, player remotes, live transcript, and streaming status. |
| Auth & identity | Session-scoped device pairing (QR/token) | Table console, shared display, and player remotes pair to a session. Lightweight for a trusted home LAN, not public multi-tenant auth. |
| CLI | Typer or Click | First-class interface for deployment, replay, evals, debugging, and operator workflows. Exact library can wait until implementation. |
| Background jobs | Python workers | Start simple with app-owned workers and Postgres-backed queues. Add heavier queue tech only after pressure appears. Expect priority lanes later (dreaming vs. NPC prep vs. media). |

## Storage

| Area | Default | Notes |
|---|---|---|
| Canonical database | Postgres | Owns event log, typed mechanical state, JSONB narrative projections, message visibility, tool calls, traces, and jobs. |
| Schema migrations | Alembic + versioned contracts | SQL schema via Alembic; JSONB document shapes evolve in-code through versioned Pydantic contracts and replay. |
| World definition format | DWD YAML + JSON contracts | Human-authored seed packs and reviewable patches use YAML; API/event payloads use JSON backed by the same Pydantic models. |
| Spatial indexing | PostGIS | Required for location/region geometry, containment, distance, adjacency, faction territories, hazards, and map feature projections. Spatial tables are projections over DWD/events, not canon. |
| Travel routing | pgRouting | Required for sea, airship, road, river, canal, and secret-route graph solving. Dungeoneer owns route costs, constraints, seasonality, risk, and event semantics. |
| Vector retrieval | pgvector | Start in Postgres. Move to Qdrant only if scale or operations justify a separate service. |
| Narrative documents | Postgres JSONB | Flexible projections over the event log, governed by versioned Pydantic contracts. |
| Object storage | Local filesystem first | Audio, generated images/video, map captures, artifacts. S3-compatible API later if needed. |
| Backup/export | Postgres dump + object archive | Must support campaign portability and recovery before long campaigns rely on the system. |

## Agent Runtime

| Area | Preferred Direction | Notes |
|---|---|---|
| Live DM runner | Dungeoneer-owned custom runner | Keeps TTFA, cancellation, delivery semantics, rules boundaries, and barge-in under direct control. Live NPC calls under deadline use this runner too, never the agent framework. |
| Workflow runtime | LangGraph | Durable non-live workflows, interrupts, streaming, persistence, subgraphs, time travel, and review flows — which map directly onto dreaming and the propose-and-approve loops (DM-profile and memento review). |
| Agent harness | Deep Agents preferred for spike | Preferred for non-live agentic work: skills, subagents, permissions, filesystem/context mechanics, and background workers. Young framework; the adapter boundary is the hedge. |
| Lower-level agent layer | LangChain `create_agent` + middleware | Fallback or component layer when Deep Agents is too much or when custom middleware is enough. |

Why lean on the community stack here: LangGraph and Deep Agents are maintained,
widely used, and already provide skills, subagents, durable workflows, and
human-in-the-loop review — exactly the non-live machinery we would otherwise
hand-build. The cost is a heavy, fast-moving dependency, so it is confined to
non-live work, behind the `AgentHarness` adapter, and never on the latency path.

NeMo Agent Toolkit was considered for profiling, eval, and MCP/A2A packaging but is
deprioritized; LangGraph plus an app-owned eval harness covers it, and we do not
expect to adopt it.

The agent harness is an adapter, not the owner of campaign state. Dungeoneer owns:

- Event log and replay.
- Message visibility and delivery status.
- Rules state and canonical world state.
- Brain capsule data for NPC identity capsules and forkable expert/loremaster
  capsules, including mementos and provenance.
- Privacy-boundary validation.
- Model gateway routing and capability profiles.
- Latency deadlines and cancellation behavior.

Deep Agents may own:

- Skill loading and progressive disclosure for non-live agents.
- Subagent ergonomics for NPC background work.
- Skill-scoped files, references, scripts, and permissions.
- Dreaming worker ergonomics.
- Agent-local scratch/context, as long as canon is written back through Dungeoneer
  contracts.

## Skills And Capabilities

Use Deep Agents skills as the preferred skill format if the Phase 0 spike proves
they fit. Skills are useful for reusable agent-side procedures and references:

- NPC role/playstyle capabilities.
- Privacy sanitization procedures.
- Map-perception request preparation.
- Media prompt/request preparation.
- Rules-assistant procedures.
- Dreaming and memento-review workflows.

Rules for Dungeoneer skills:

- Skills can guide an agent, but cannot mutate canonical state directly.
- Skills must call typed Dungeoneer tools for state changes.
- Skill access is scoped by agent role, NPC identity, campaign, and deployment
  profile.
- Skill files are read-only by default. Any self-modifying or personalized skill
  behavior requires explicit review.
- Live-turn skill loading must be bounded and preferably preloaded. No broad skill
  discovery inside a latency-sensitive turn.

If Deep Agents skills do not fit cleanly, keep the same directory/manifest concept
as Dungeoneer capability packs and load them through LangChain middleware.

## Tool And Service Boundaries

| Surface | Default | Purpose |
|---|---|---|
| Hot internal calls | Direct Python/service functions | Rules tools, event append, retrieval assembly, and other latency-sensitive operations. |
| Runtime process boundary | REST/WebSocket | Long-lived services used by orchestrator, NPC workers, frontend clients, privacy-boundary jobs, and deployment health. |
| Developer/operator surface | CLI | Replay, evals, state inspection, migrations, deployment, debugging, and scripted tests. |
| Interoperability | MCP adapter later | Deferred until REST/CLI contracts are stable and a concrete sharing/integration need appears. |

The canonical contracts live once. Direct calls, REST, CLI, and any future MCP
adapter must wrap the same Pydantic models and validators.

## Model Serving

| Workload | Default Candidate | Notes |
|---|---|---|
| Primary DM model | vLLM / Ollama / llama.cpp behind model gateway | Runtime selected per profile. The 5090 profile keeps the live DM model resident. |
| NPC/background text | vLLM / Ollama / llama.cpp behind model gateway | Runs home-side only when it touches conversation or NPC private state. |
| Embeddings/reranking | Local embedding/reranker service | Conversation embedding generation and vector search stay in the trusted home domain. |
| Perception VLM | vLLM on restricted 6000 Ada | Sanitized cropped map images only. Returns structured perception proposals. |
| Image/video | ComfyUI | Sanitized briefs only on restricted host. Async by default. |
| Model gateway API | App-owned HTTP contracts | OpenAI-compatible where practical, but Dungeoneer contracts own capability semantics. |

The serving stack leans NVIDIA (vLLM, Riva, NeMo, ComfyUI) by deliberate choice:
it is the maintainer's comfort zone and fits the hardware. The gateways keep swaps
possible later, but treat a serving swap as a real port, not a config flip.

Every model candidate needs measured quality, latency, memory footprint, license
review, and fallback behavior before it becomes a default profile dependency.

## Speech And Audio

| Area | Candidate | Notes |
|---|---|---|
| Audio transport/capture | Browser WebRTC capture; server-side multi-channel handling | Per-player phone/mic streams reach the home audio service; local multi-channel via an audio interface where used. Raw audio constraints (`echoCancellation`/`autoGainControl` off) preserved for the pipeline. |
| STT | faster-whisper, NVIDIA Riva | Must pass voice chaos and TTFA gates before deeper voice work depends on it. |
| VAD / endpointing | Silero VAD or webrtcvad | Per-channel voice activity for endpointing and overlap-window detection. |
| Diarization / speaker tracking | NeMo Streaming Sortformer, Riva diarization, pyannote | Speaker attribution and overlap handling are product gates, not polish. |
| Overlap recovery | NeMo multitalker/source separation path | Expensive overlap-window recovery, not always-on per-player streams unless measured feasible. |
| Echo cancellation (AEC) | Spike output (WebRTC APM, speexdsp, or Riva built-in) | Keeping TTS playback out of the transcript is a top-tier risk; the approach is decided by the 0.4b full-duplex spike, not assumed. |
| TTS | NVIDIA Riva, Piper, XTTS/F5-style candidates | Streaming first audio, cancellability, and real-time factor matter more than voice quality at first. |
| Capture hardware | Phones/simple room mic first, then practical multi-channel if acceptable | If frictionless capture fails and table wiring is unacceptable, live voice is blocked rather than hidden behind push-to-talk. |

All audio, transcripts, speaker embeddings, and voice-derived context stay in the
trusted home conversation domain.

## Testing And Evaluation

| Area | Default | Notes |
|---|---|---|
| Unit/integration tests | pytest | The rules engine is deterministic and must carry regression fixtures for combat and skill-check flows. |
| Determinism | Seeded dice + event replay | Same seed plus same events reproduces the same state; evals and bug repros depend on it. |
| Eval harness | App-owned, CLI-driven | Saved scenarios scored offline: NPC recall/memento promotion, voice-chaos benchmark clips, DM style-vs-profile, retrieval quality. |
| Spatial/travel evals | App-owned route fixtures | Verify containment, nearby/neighbor queries, route solving, travel-time estimates, sea/airship constraints, and rumor/news propagation against authored fixtures. |
| System simulation runs | Structured trace/finding artifacts + fresh simulator agent | Text-based architecture playtests that route scenarios through current docs/contracts/code. Runs execute in disposable current-file snapshots with no `.git`, no prior outputs, and no runner-only simulation docs; the top-level runner extracts artifacts to external history. Findings are searchable by fingerprint, cause, disposition, status, affected docs, and recurrence. |
| Latency checks | Stage-timing assertions | TTFA and per-stage budgets are asserted like tests; a regression is a release blocker. |

Eval and latency results are first-class records, stored like tool calls and
traces, so performance regressions are caught alongside correctness ones.

## Frontend

| Surface | Default | Notes |
|---|---|---|
| MVP client | Browser app | Laptop table console first: chat, transcript, voice controls, combat/state, map capture, media control. |
| Framework | React when ready | Delay frontend framework commitment until the first real live-play UX is ready. |
| Desktop shell | Tauri later if useful | Useful if browser APIs become limiting for audio/camera/device integration. |
| Shared display | Browser/iPad/TV/projector client | Passive DM-controlled output: images, video, public text, handouts, public state. |
| Player remotes | Mobile web | Private messages, confirmations, handouts, rolls, personal state. |

## Deployment

| Area | Default | Notes |
|---|---|---|
| Local dev/session runtime | Docker Compose profiles | One profile per role: state, api, workers, audio, retrieval, npc, dm, perception, media, monitoring. |
| Startup orchestration | `dungeoneer session up/down` CLI | SSH + Compose first. No Kubernetes or custom cluster manager until simple tools fail. |
| Inventory | YAML deployment profiles | Hosts, roles, GPU, trust domain, optional services, ports, models, and health checks. |
| Bootstrap | Idempotent host setup scripts | Drivers, runtime, service user, persistent dirs, SSH, firewall, model cache. |
| Secrets | Env files / local secret file | Model endpoints, SSH keys, device-pairing tokens. Kept out of the repo; simple for a home LAN, not enterprise secret management. |
| Observability | Local stage-timing/traces day one; OpenTelemetry later | Per-stage latency and trace records are required from Phase 0 by the latency budget. Richer OTel integration waits until the trace schema is stable. |

Every supported state profile must enable PostGIS and pgRouting. A deployment
without those extensions is unsupported, because spatial/travel reasoning is part
of the world model. See [Spatial and travel system](SPATIAL_TRAVEL.md).

## Privacy And Trust

| Area | Default | Notes |
|---|---|---|
| Trusted conversation domain | 4090 + 5090 home machines | Audio, transcripts, DM prompts/responses, NPC private state, embeddings, vector search, event log, dreaming. |
| Restricted non-conversation domain | 6000 Ada or any untrusted host | Sanitized cropped map images and sanitized media briefs only. |
| Boundary enforcement | Pydantic schemas + validators + narrow endpoints | Reject full-frame images, transcripts, private messages, raw event JSON, secrets, arbitrary file/DB/LAN access. |
| Provenance | Dual records | Full home provenance stays home; restricted-host provenance contains only sanitized payload and runtime metadata. |

## Phase 0 Stack Spikes

Run these before locking implementation details:

1. **Agent harness spike**
   Compare a thin custom async runner against LangChain `create_agent` and Deep
   Agents on NPC background stance, a live NPC line under deadline, a dreaming pass,
   and the privacy sanitizer. The thin-custom option is the control: adopt the
   framework only if it clearly saves work without fighting latency, cancellation,
   or the privacy boundary. Preferred outcome is Deep Agents (or LangGraph) for
   non-live work behind a Dungeoneer `AgentHarness` adapter, with the live path
   custom regardless.

2. **Voice capture chaos spike**
   Test frictionless capture first (UMIK-1/laptop/phones/cheap clip-on mics) and,
   in the 0.4b full-duplex pass, echo cancellation and barge-in with TTS playing
   into the room. If capture cannot preserve speaker intent without unacceptable
   table friction, live voice is blocked.

3. **Model gateway spike**
   Stand up one local text model behind the app-owned gateway and prove streaming,
   cancellation, tracing, and capability metadata.

4. **Restricted-host job spike**
   Send one sanitized cropped map image and one sanitized media brief through the
   privacy-boundary gateway. Prove unsanitized jobs are rejected.

5. **Deployment spike**
   Implement inventory parsing and a dry-run `session up` that reports required
   services, profiles, health checks, and fallback modes.

6. **Spatial/travel database spike**
   Enable PostGIS and pgRouting in the state profile. Import a tiny region with two
   ports, one airship tower, one faction territory, and one hazard zone; prove
   containment, nearby, route, ETA, and route-risk queries from CLI fixtures.
