# Privacy Boundary

## Purpose

The RTX 6000 Ada restricted host is powerful and useful, but it is not part of the
trusted conversation domain. It should be treated as a narrow non-conversation
model host.

This boundary is defined by trust level, not by who owns the hardware. A host is
"restricted" if it is not fully under our control — owned by someone else, shared,
rented cloud capacity, or otherwise outside the home trust zone. The rule is the
same regardless of the reason: raw conversation content stays in the trusted
domain, and restricted hosts receive only sanitized non-conversation payloads.
Today the RTX 6000 Ada is the only restricted host; the design assumes there may
be others.

The home machines own private campaign content. The restricted host owns expensive
vision and media compute.

## Domains

### Home Conversation Domain

Stays on home machines:

- Microphone audio.
- Speech-to-text transcripts.
- Text-to-speech requests and generated speech.
- DM dialogue prompts and responses.
- NPC sub-agent prompts, private reasoning summaries, and memory.
- Player-private messages.
- Campaign event log and replay.
- Post-session dreaming over the event log.
- Conversation embedding generation, vector indexes, and vector search.
- Full source context for generated assets.

### Restricted-Host Non-Conversation Domain

Allowed on the RTX 6000 Ada:

- vLLM-hosted VLM/perception jobs over sanitized, cropped battle-grid images.
- Image generation from sanitized media briefs.
- Video generation from sanitized media briefs.
- Model weights, runtime caches, and generated media outputs.
- Generic non-conversation experiments that never ingest campaign private text.

The restricted host should not have direct database access, transcript access,
event-bus access, object-store listing access, or broad callback rights into home
systems.

## Allowed Payloads

### Map Perception Request

Allowed:

- Cropped battle-grid image only.
- Grid calibration hints.
- Token marker IDs or public token labels needed for perception.
- Requested output schema.
- Job ID and correlation IDs.

Forbidden:

- Full-frame room images.
- Player faces, room background, or incidental camera data.
- Audio.
- Transcript excerpts.
- Private player messages.
- NPC private thoughts or unrevealed campaign lore.

### Media Generation Request

Allowed:

- Sanitized art/video brief.
- Style tags.
- Format, aspect ratio, duration, and quality settings.
- Public-safe subject description.
- Asset references explicitly approved for the restricted-host job.
- Seed and model/workflow parameters.

Forbidden:

- Raw transcript excerpts.
- Private player messages.
- NPC private memories or intention summaries.
- Unrevealed secrets unless intentionally converted into a public-safe visual
  description.
- Full home-side source context.
- Database row dumps or event-log payloads.

## Request Skills

Use app-owned request skills to create restricted-host jobs. A request skill is a
small, testable transformation that accepts private home-side context and emits a
schema-validated, privacy-safe payload.

Required skills:

- `sanitize_map_perception_request`: crop/mask the image, strip metadata, attach
  grid hints, and emit a perception schema.
- `sanitize_portrait_request`: convert NPC/player-facing facts into a public-safe
  portrait brief.
- `sanitize_location_art_request`: convert location state into a public-safe
  scene brief.
- `sanitize_item_art_request`: convert item state into a public-safe item brief.
- `sanitize_video_request`: convert a recap or cinematic request into a
  public-safe shot list.

These skills should be deterministic where possible and model-assisted only when
needed. Model-assisted sanitization must be validated by schema and policy checks
before a job leaves the home domain.

## Validation Rules

Reject a restricted-host job if:

- It contains transcript-like quoted dialogue.
- It contains player-private message content.
- It contains raw event-log JSON.
- It references NPC private thoughts directly.
- It includes uncropped/full-frame camera input.
- It requests arbitrary file, database, URL, or LAN access.
- It lacks audience, source, and provenance metadata.

Log rejected jobs as internal audit events, not player-facing messages.

## Network Shape

The restricted host should expose narrow services only:

- vLLM endpoint for approved non-conversation VLM jobs.
- ComfyUI or equivalent endpoint for approved media workflows.
- Result upload endpoint or queue producer for structured outputs and generated
  assets.

The restricted host should not initiate arbitrary requests back into home services.
Prefer pull-free job execution: home queues sanitized job, restricted host processes
it, restricted host posts result to one narrow endpoint, home stores and validates
the result.

## Provenance

Store two provenance records:

- Home provenance: full private source context, sanitization skill version,
  validator results, and originating event IDs.
- Restricted-host provenance: sanitized prompt/brief, model, workflow, seed,
  duration, output asset IDs, and runtime metadata.

Only the restricted-host provenance crosses the privacy boundary.

## Fallback

If the restricted host is unavailable:

- Map perception falls back to manual confirmation or a smaller home-side model
  only when it does not evict the live DM.
- Image/video generation queues until the restricted host is available.
- Live play continues without generated media.
