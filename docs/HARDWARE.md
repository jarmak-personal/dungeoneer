# Hardware Topology

## Privacy Boundary

The restricted-host GPU is powerful but sits outside the home trust boundary, so
it has a hard data boundary: no audio and no conversation content (raw speech or
transcripts) may be sent to it. The reason a host is restricted — owned by someone
else, shared, rented, or simply not fully controlled — does not change the rule;
any host outside the trust boundary is treated this way. This splits the system
into two domains.

- **Conversation domain (home machines only)**: microphone audio, STT,
  transcripts, TTS, the DM dialogue model, NPC sub-agent reasoning, embedding
  generation and vector search over conversation, query encoding, and post-session
  dreaming over the event log. Anything that ingests, emits, indexes, or searches
  raw conversation content stays home.
- **Non-conversation domain (restricted host allowed)**: battle-grid image
  perception, image generation, video generation, and generic model hosting that
  only receives sanitized non-conversation payloads.

The line is drawn conservatively. Conversation text and audio may never cross;
derived embedding vectors do not cross either for the default architecture.
Vectors are derived from private content and are not treated as opaque enough for
the restricted-host boundary. Reconsidering that would require an explicit privacy
decision later.

This boundary is not just policy; it is an architectural seam. The home boxes are
the "conversation brain"; the restricted-host GPU is "eyes and art." It constrains overflow
asymmetrically: any workload that must ingest raw conversation content (STT, TTS,
the DM model, NPC reasoning, embedding generation/search, dreaming) cannot be
relieved by the restricted host, while sanitized perception and media generation can
offload there.

See [Privacy boundary](PRIVACY_BOUNDARY.md) for the allowed payload contract.

## Current Machines

### 5090 Workstation (Home)

- GPU: RTX 5090.
- CPU: AMD Ryzen 7 X3D-class 8-core/16-thread.
- System RAM: 64 GB.
- Role: resident live DM dialogue model.

Keep the primary DM model hot here. Because battle-grid perception is offloaded to
the restricted host, the DM no longer has to host a perception VLM during live play.
The DM may still be multimodal for handouts and direct image reasoning, but a
strong text DM fed structured perception output is now a viable, lower-VRAM
option. That is an open choice, not a settled one.

### 4090 Workstation (Home)

- GPU: RTX 4090 (24 GB).
- CPU: Intel Core i9-13900K.
- System RAM: 96 GB.
- Role: the home "conversation brain" — audio plus private text.

Resident set during live play:

- Streaming STT and streaming TTS (must stay home; audio is privacy-bound).
- Embedding/reranker model for encoding conversation (needs raw text, so home
  only). The resulting vector index and similarity search stay home by default.
- A small NPC sub-agent model for background stance preparation.

These fit within 24 GB together, but they contend for compute, not VRAM. STT runs
only while a player speaks and TTS only while the DM speaks, so schedule
embeddings and NPC background reasoning into the gaps between turns rather than
during live audio. If NPC background reasoning outgrows the inter-turn gaps, that
is the first pressure point, and the privacy boundary means it cannot move to the
restricted host: relieve it by moving the NPC model onto the 5090 or by adding the
DGX Spark.

This machine also has the most system RAM, so it is a reasonable home for
Postgres, queues, and indexing during early development.

### RTX 6000 Ada Workstation (Restricted Host, Home LAN)

- GPU: RTX 6000 Ada (48 GB).
- CPU: Intel Core i9-14900K.
- Availability: a shared host on the home LAN, subject to the privacy boundary
  above. Not guaranteed always-available; treat its capacity as opportunistic
  rather than reserved.
- Role: non-conversation model host: live battle-grid perception and generated
  media.

The 48 GB matters here: it lets us run a large, high-end vision model for
perception through vLLM without competing for the 5090's live-DM VRAM. Vision
quality is decoupled from the live-path budget, so we can use a more capable VLM
than we could ever keep resident at home, and still host ComfyUI image/video
pipelines alongside it when capacity allows. Because the machine is on the home
LAN, battle-grid perception runs on the live path: the DM acknowledges within the
live budget and the structured result returns in 3-8 s. It never receives audio
or transcripts; it receives sanitized cropped images and returns structured state
(token positions, terrain, confidence).

The 6000 Ada should expose only narrow model services:

- vLLM for non-conversation VLM/perception jobs.
- ComfyUI or equivalent for sanitized image/video generation jobs.
- No database access, transcript access, event-bus access, or general LAN
  callback path.

Privacy requirement: an overhead camera can incidentally capture the room and
people, not just the grid. Captures must be cropped to the grid (or taken by a
fixed map-only camera) at the source, so only game-relevant imagery leaves the
home boxes. Tracked as a Phase 4 task.

### N150 Network Node

- Role: always-on control plane and tiny background jobs.

Good fits:

- Reverse proxy, service discovery, health checks, and dashboards.
- Queue coordinator or lightweight workers.
- Campaign backup/export jobs.
- Tiny classifiers or small CPU-only helpers after benchmarking.

Do not put live LLM, VLM, STT, or TTS requirements on this node unless measured
latency proves it can meet the budget.

### Optional DGX Spark

- Role: memory-heavy model lab and overflow node.

The 6000 Ada absorbs the vision and media load that was the main eviction threat,
so the Spark is now genuinely optional. Because of the privacy boundary, the only
workloads it could ever relieve are home-side conversation compute: NPC background
reasoning, embeddings, and dreaming over the event log. Add it only if those
outgrow the 5090 + 4090.

## Live Session Placement

- 5090 (home): resident DM dialogue model.
- 4090 (home): streaming STT, streaming TTS, embeddings/reranking, and a small NPC
  background model in inter-turn gaps.
- 6000 Ada (home LAN): on-demand battle-grid perception and any live-surfaced
  image generation from sanitized jobs.
- N150: control plane only.

All conversation audio, text, embeddings, and vector search stay on the 5090/4090.
Only sanitized cropped images and sanitized media briefs cross to the 6000 Ada.
The LAN hop is acceptable for image perception and media because those sit off the
tight TTFA path; it must never be introduced into the audio path. Validate end to
end with the Phase 0.5 voice spike.

## Offline Placement

After a session ends and TTFA no longer matters:

- Dreaming and memento repair run on the home boxes, because they replay
  conversation content. The 5090 and 4090 can both join once live play is over.
- The 6000 Ada handles the media side of dreaming from sanitized briefs: recap
  art, portraits, maps, and video. It does not replay transcripts or receive raw
  dream context.
- DGX Spark, if present, takes the heaviest long-context conversation jobs that do
  not fit at home.
- N150 coordinates jobs and runs backups.

## Hardware Promotion Gates

Promote hardware from optional to required only after measurement.

Promotion triggers:

- TTFA p95 is exceeded because a live-path model cold-loads or is evicted.
- TTS cannot maintain real-time factor under concurrent STT and NPC load.
- The 4090 cannot fit STT + TTS + embeddings + an NPC model, or cannot schedule
  NPC background reasoning into inter-turn gaps without hurting TTFA.
- Battle-grid perception or media generation on the 6000 Ada cannot keep up with
  live capture cadence.
- Post-session dreaming cannot finish before the next expected session window.
- Local model quality requires a DM model that does not fit resident on the 5090.

The privacy boundary means home-side compute (audio, transcripts, NPC text,
dreaming) is the only thing the Spark can help with; vision and media already have
a home on the 6000 Ada.
