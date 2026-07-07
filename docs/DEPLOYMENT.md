# Deployment And Session Startup

## Operating Assumption

Assume all Dungeoneer services are cold before a session.

That means no API server, model server, TTS/STT process, ComfyUI workflow, or
background worker is expected to already be running. The deployment flow must be
able to start from powered-on machines with only host-level prerequisites in
place.

Acceptable one-time prerequisites:

- OS, GPU drivers, container runtime, and SSH access are installed.
- Persistent directories for data, model weights, caches, and logs exist.
- Model weights can be cached on disk between sessions.
- Hostnames or static LAN addresses are stable.

Do not assume long-lived Dungeoneer application daemons. If the container runtime
itself is stopped, `session up` may start it as a host-level prerequisite check.

## Cold-State Levels

There are three different "cold" states. Handle them explicitly.

### Service-Cold

The machine is powered on and reachable over SSH, but no Dungeoneer containers are
running.

This is the normal target. `session up` should fully recover from this state.

### Runtime-Cold

The machine is reachable, but Docker/Podman is stopped.

`session up` may start the container runtime, then continue. If the operator does
not want the runtime daemon running between sessions, this is acceptable as long
as startup time is measured.

### Power-Cold

The machine is asleep or powered off.

`session up` can try Wake-on-LAN if configured, but it should not depend on a
custom always-on Dungeoneer agent. If wake fails, the CLI should tell the operator
which machine needs manual power-on and then resume when the host becomes
reachable.

## Target Operator Experience

Pre-session:

```bash
dungeoneer session up --campaign <campaign-id>
```

That command should:

1. Read the host inventory.
2. Check SSH/LAN reachability for each required machine.
3. Check GPU availability, disk space, ports, model files, and privacy-boundary
   config.
4. Start the required Docker Compose profiles on each machine.
5. Wait for health checks.
6. Warm the live models.
7. Run a short smoke test through the API, DM model, STT/TTS path, and optional
   restricted-host model service.
8. Print the table-console URL and shared-display/player-join URLs.

Post-session:

```bash
dungeoneer session down
```

That command should:

1. Stop live-path services.
2. Leave databases, object storage, model caches, and logs persisted on disk.
3. Optionally start or continue post-session dreaming jobs.
4. Produce a shutdown report with backup status and any failed jobs.

## Machine Roles

### 4090 Home State Host

Primary role:

- Canonical data and home private text/audio services.

Starts for a live session:

- Postgres with pgvector, PostGIS, and pgRouting.
- Object storage path or local S3-compatible service.
- API gateway and WebSocket server.
- Event/job workers.
- STT service.
- TTS service.
- Embedding/reranker service.
- Small NPC background model if capacity allows.

Persistent between sessions:

- Postgres volume.
- Object storage.
- Audio/transcript artifacts.
- Embedding/vector indexes.
- Logs and timing traces.
- Model caches.

### 5090 Home DM Host

Primary role:

- Resident live DM dialogue model.

Starts for a live session:

- vLLM/Ollama/llama.cpp profile for the selected DM model.
- Health endpoint.
- Optional direct image-reasoning model if chosen later.

Persistent between sessions:

- Model weights.
- Runtime cache if useful.
- Logs.

### RTX 6000 Ada Restricted Host

Primary role:

- Non-conversation model host for eyes and art.

Starts for a live session when available:

- vLLM endpoint for sanitized VLM/perception jobs.
- ComfyUI or equivalent media generation service.
- Narrow result endpoint or queue producer.

Never receives:

- Audio.
- Transcripts.
- Private messages.
- NPC private memory/thoughts.
- Raw event logs.
- Conversation embeddings/vector search.
- Full home-side source context.

Persistent between sessions:

- Non-conversation model weights.
- ComfyUI workflows and model caches.
- Generated media temp/cache if policy allows.

If unavailable:

- Map perception falls back to manual confirmation or a smaller home-side model
  only if it does not evict the live DM.
- Image/video jobs queue until the restricted host returns.
- Live play continues.

### Laptop Table Console

Primary role:

- Browser client, microphone/camera capture, shared-display controller, and local
  operator surface.

Starts for a live session:

- Browser pointed at the API gateway.
- Optional local helper for camera selection/crop if browser APIs are not enough.

### N150 Node

Optional role:

- Always-on convenience host for dashboards, wake checks, reverse proxy, or job
  coordination.

Do not make it required for live LLM, VLM, STT, or TTS.

## One-Time Bootstrap

Each machine gets a small host bootstrap, separate from per-session startup.

Bootstrap responsibilities:

- Create a `dungeoneer` service user.
- Install NVIDIA driver/runtime where needed.
- Install Docker or another container runtime.
- Configure SSH key access from the operator machine.
- Create persistent directories:
  - `/srv/dungeoneer/config`
  - `/srv/dungeoneer/data`
  - `/srv/dungeoneer/models`
  - `/srv/dungeoneer/cache`
  - `/srv/dungeoneer/logs`
- Pull base container images.
- Download or verify model weights.
- Configure local firewall rules.
- Write host-specific `.env` files.

Bootstrap should be idempotent. Running it twice should repair drift, not destroy
state.

## Inventory

Use an explicit inventory file rather than hard-coded hostnames.

Example:

```yaml
hosts:
  state_4090:
    address: dungeoneer-4090.local
    roles: [state, api, audio, embeddings, npc_background]
    gpu: rtx4090
    private_domain: true
  dm_5090:
    address: dungeoneer-5090.local
    roles: [dm_model]
    gpu: rtx5090
    private_domain: true
  work_6000ada:
    address: work-6000ada.local
    roles: [sanitized_vlm, sanitized_media]
    gpu: rtx6000ada
    private_domain: false
    optional: true
```

The startup CLI should derive compose profiles, health checks, and allowed
payload boundaries from this file.

## Compose Profiles

Use Docker Compose profiles per role. Do not require one giant compose file to run
unchanged on every machine.

Suggested profiles:

- `state`: Postgres with pgvector/PostGIS/pgRouting, object store, migrations.
- `api`: API gateway, WebSocket server.
- `workers`: event workers, job workers.
- `audio`: STT, TTS, VAD helpers.
- `retrieval`: embeddings, reranker, vector index jobs.
- `npc`: NPC background model/runtime.
- `dm`: resident DM model host.
- `perception`: restricted-host vLLM perception endpoint.
- `media`: restricted-host ComfyUI/media endpoint.
- `monitoring`: dashboards and logs.

The operator CLI can run remote commands like:

```bash
ssh dungeoneer-4090.local 'cd /srv/dungeoneer/app && docker compose --profile state --profile api --profile audio up -d'
ssh dungeoneer-5090.local 'cd /srv/dungeoneer/app && docker compose --profile dm up -d'
ssh work-6000ada.local 'cd /srv/dungeoneer/app && docker compose --profile perception --profile media up -d'
```

This is not the final user interface; it is the primitive the CLI automates.

The deployment controller should run from the laptop/table console or the 4090
state host. It should use SSH plus compose commands first. Avoid Kubernetes or a
custom cluster manager until the simple path is actually insufficient.

## Session Startup Phases

### 1. Preflight

Check:

- Power state or Wake-on-LAN status where configured.
- Host reachability.
- SSH auth.
- Time sync.
- GPU present and not heavily occupied.
- Container runtime available or startable.
- Required ports free.
- Persistent volumes mounted.
- Database volume present.
- Model weights present or downloadable.
- Privacy-boundary service has no database credentials.
- Restricted-host service exposes only approved endpoints.

Failure should be clear and actionable.

### 2. Start State Plane

Start on the 4090 host:

- Postgres.
- Object storage.
- API gateway.
- Event/job workers.
- Migrations.

Health criteria:

- Database accepts connections.
- Migrations are current.
- API health endpoint is green.
- Campaign can be loaded.

### 3. Start Live Conversation Plane

Start:

- DM model on the 5090.
- STT/TTS on the 4090.
- Embedding/reranker service on the 4090.
- NPC background runtime if enabled.

Health criteria:

- DM model responds to a tiny prompt.
- STT accepts an audio test or synthetic sample.
- TTS produces a short audio chunk.
- Embeddings service returns a vector for a harmless test phrase.

### 4. Start Optional Restricted-Host Plane

Start on the 6000 Ada if available:

- vLLM perception model.
- ComfyUI/media workflows.
- Privacy-boundary result path.

Health criteria:

- Sanitized test image returns structured perception output.
- Sanitized test media brief queues successfully.
- Unsanitized test payload is rejected.
- No private-domain credentials are present.

### 5. Warm Models

Warm in the order needed for live play:

1. STT.
2. TTS.
3. DM model.
4. Retrieval/reranker.
5. NPC background model.
6. Perception VLM.
7. Media workflows.

The goal is not just "loaded." The goal is measured first-token/first-audio
latency under budget.

### 6. Open The Table

Print:

- Table console URL.
- Shared display URL.
- Player join URL / QR code.
- Health dashboard URL.
- Active hardware profile.
- Privacy-boundary status.
- Fallback mode if the restricted host is unavailable.

## Health Model

Every service needs:

- `ready`: can receive work.
- `warm`: model loaded and first request complete.
- `degraded`: usable but slower or missing optional capability.
- `failed`: should not receive traffic.

The table console should show this in human terms:

- Voice ready.
- DM model ready.
- NPC background ready.
- Map perception ready or manual fallback.
- Media queue ready or deferred.
- Dreaming queue idle/running.

## Shutdown

Default shutdown:

- Stop live-path model services.
- Stop API and workers if no dream jobs are running.
- Keep Postgres/object storage volumes intact.
- Keep model caches intact.
- Write a session shutdown report.

Optional shutdown modes:

- `--keep-dreaming`: keep home-side dreaming workers running after live services
  stop.
- `--keep-media`: keep 6000 Ada media jobs running after live play.
- `--cold`: stop every Dungeoneer container.
- `--backup`: run backup/export before stopping state services.

## Upgrade Strategy

Separate host bootstrap from app deploy.

- Host bootstrap changes drivers, runtimes, directories, firewall, and SSH.
- App deploy updates repo code, compose files, migrations, prompts, schemas, and
  service images.
- Model deploy downloads or changes model weights and runtime profiles.

Never mix schema migration, model replacement, and live session startup without a
preflight report. The CLI should warn when a migration or model download is about
to happen close to session time.

## Minimum MVP Deployment

For the earliest working version, do not solve everything.

Minimum:

- One inventory file.
- One `session up` script.
- One `session down` script.
- Docker Compose profiles for 4090 state/API/audio and 5090 DM model.
- Optional 6000 Ada profile for sanitized perception/media.
- Health checks and model warmup.
- Clear manual fallback when optional hosts are unavailable.

This is enough to make "cold before session" operational without building a full
cluster manager.
