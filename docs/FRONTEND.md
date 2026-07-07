# Frontend Clients

## Recommended MVP Setup

Start with a browser-first table console on a laptop.

Device layout:

- Laptop web app: primary table console, voice controls, transcript, combat
  tracker, state inspection, and media playback.
- Overhead camera: on-demand battle-grid still captures.
- Player remotes: phones or tablets for private messages, confirmations, rolls,
  handouts, and character state.
- DM-controlled shared display: iPad, TV, projector, or browser client for
  generated art, generated video, public text, map state, initiative, and public
  handouts, plus route previews and public travel cards.

This keeps the first implementation close to standard browser APIs while leaving
room for nicer table hardware later.

## DM-Controlled Shared Display

The shared display is a passive output surface controlled by the DM/orchestrator.
It is not an interactive smart table for this project.

It should support on-demand display of:

- Generated scene art, NPC portraits, item art, maps, and handouts.
- Generated video clips or post-session recap videos.
- Public text: boxed text, letters, inscriptions, riddles, rumors, and recaps.
- Public combat/rules state: initiative, turn, visible conditions, and confirmed
  map state.
- Public geography/travel state: map excerpts, route previews, ports, nearby
  towns, travel clocks, ETA/risk assumptions, and journey summaries.
- Temporary ambience: location title, faction symbol, weather, countdown, or
  active ritual status.

The DM can push, replace, hide, or clear content. Generated media should appear
when ready and never block live conversation.

Every displayed item should be persisted with:

- Asset/message ID.
- Visibility audience, usually `table`.
- Display status: queued, visible, hidden, expired.
- Source: generated, uploaded, rules state, map perception, or handout.
- Provenance for generated media: sanitized prompt, model, seed, time, and
  home-side source context reference.

This gives the table a rich public surface without making the display a source
of canonical state.

## Map Capture

Map perception should be capture-on-demand.

D&D is turn-based, so continuous scanning wastes compute and creates noisy state
updates. The DM should request a still capture when it matters:

- Before a declared action needs position confirmation.
- After movement, attacks, spell placement, or token changes.
- When a player or DM asks, "does this look right?"
- At combat start/end or round boundaries.
- When importing a VTT screenshot.

The captured image creates a perception job. The VLM proposes token positions,
terrain, obstacles, labels, and confidence scores. The rules engine applies only
confirmed changes.

Because perception runs on the restricted-host GPU, captures must be cropped to the
battle grid (or taken by a fixed map-only camera) before frames leave the home
network. An overhead camera otherwise catches the room and people, which the
privacy boundary is meant to keep off the restricted host. Crop at the source, not
after upload. The perception API should reject uncropped/full-frame images.

## Player Remotes

Player remotes are worth building early because they unlock private interaction
that a human DM normally handles with notes, texts, or side conversations.

Capabilities:

- Receive private DM messages.
- Receive private NPC whispers, visions, dreams, curses, clues, or sensory
  details.
- Send private replies to the DM.
- Confirm hidden choices or reactions.
- View personal character state.
- Build or import a character in natural terms, and review and approve it before it
  enters play — the remote is the player's authoring surface, never DWD YAML (see
  [Lifecycle](LIFECYCLE.md)).
- Roll privately when table rules allow it.
- Receive player-specific handouts or generated images.

Private messages should feel diegetic when useful, but they are still explicit
system events with audience metadata.

## Private Message Rules

Every message needs visibility and delivery metadata. Audience and delivery are
separate axes; the canonical enum lives in
[Game world schema](GAME_WORLD_SCHEMA.md). The examples below are illustrative.

Audience examples:

- `table`: everyone at the table.
- `player:{id}`: one player.
- `players:[ids]`: selected players.
- `dm_only`: DM/operator only.
- `npc_private:{id}`: NPC private memory/intention.
- `internal`: system/debug/eval only.

Delivery examples:

- `delivered`: recipient saw or heard it.
- `queued`: waiting for recipient device.
- `expired`: no longer relevant before delivery.
- `aborted`: generated but interrupted before delivery.
- `proposed`: model suggestion awaiting DM/system approval.

Only delivered messages should enter player-facing recall. A private message
enters recall only for its intended recipient(s), the DM orchestrator, and
audit/replay systems.

## Safety And Agency

Private messages are powerful, so they need guardrails.

- Do not use private messages to force secret obligations without consent.
- Mark secret objectives, whispers, and visions as private state with provenance.
- Let players reveal private messages to the table explicitly.
- Avoid leaking one player's private content into another player's context.
- Keep an audit trail for debugging and campaign replay.

## Future Hardware

Nicer table setups can come later:

- iPad as a polished player-facing display.
- TV/browser display for generated art and public state.
- Pi camera node as a fixed overhead grid appliance.
- Dedicated push-to-talk buttons or table microphones.
- QR-code player join flow for phones.
- Modern SurfaceScapes-style interactive table as a separate future project.

Do not start with a Pi appliance unless the laptop/camera path proves limiting.
