# Voice Chaos Gate

## Position

Natural table speech is a hard product gate.

D&D table audio is not a meeting transcript. People interrupt, joke, overlap,
backchannel, roll dice, move minis, look away from microphones, and talk while
the DM is speaking. If the system only works when players push-to-talk, speak one
at a time, or slow down for the machine, the voice product is not ready.

The system does not need perfect transcripts of every joke or backchannel. It
does need reliable capture of game-relevant intent, speaker identity, and
interruptions without silently assigning consequential actions to the wrong
player.

## Current Technical Read

Speaker diarization is useful but not sufficient by itself.

- Diarization answers "who spoke when" with speaker labels.
- Speaker identification maps a label to a known player.
- ASR turns speech into words.
- Overlapped speech handling tries to recover what each speaker said when more
  than one person talks at once.

Modern local options exist:

- NVIDIA Riva supports streaming ASR with speaker diarization, but its streaming
  diarization is still documented as beta.
- NVIDIA NeMo Streaming Sortformer is designed for live diarization with speaker
  cache/tracking.
- pyannote has strong local diarization pipelines and improved speaker assignment
  in `community-1`, with useful overlap detection.
- NVIDIA multitalker Parakeet-style models are specifically aimed at overlapped
  speech, but require one model instance per speaker and diarization-derived
  speaker activity.

The risk is not whether a demo can label speakers. The risk is whether a real
table can preserve player intent under overlap, noise, distance, and DM audio
playback.

## Hardware Implication

Treat multitalker ASR as an expensive overlap-recovery path, not the default path
for every frame of table audio.

NVIDIA's multitalker Parakeet model is small enough to test, but its architecture
scales by speaker: each speaker-focused instance receives the same mixed audio
and produces that speaker's transcript. Some implementations may share model
weights in one process, but inference work and streaming state still scale with
the number of active speakers.

Implications:

- Do not reserve 4090 capacity assuming 4-6 multitalker streams are always hot.
- Run normal streaming ASR + diarization for ordinary speech.
- Trigger multitalker/source-separation only for detected overlap windows that
  contain possible game intent.
- Prefer multi-channel/seat-aware microphones so the system needs the expensive
  overlap path less often.
- If 4-6 speaker overlap recovery must run continuously, the home hardware plan
  probably needs revision or DGX Spark-class overflow.

## Audio Capture Strategy

Do not bet the product on a single laptop microphone.

Preferred hardware order:

1. Multi-channel table audio with one boundary/lavalier/seat mic per player or
   per seat group.
2. Beamforming microphone array with stable seating geometry.
3. Single room microphone only as a baseline/failure case, not the target.

Seat-aware channels make the problem much easier:

- Channel identity provides a strong prior for player identity.
- Diarization still helps with bleed and overlap.
- Speaker enrollment can resolve cross-channel leakage.
- Low-confidence events can be tied to table position instead of invented
  certainty.

## Proposed Pipeline

Live path:

1. Capture synchronized multi-channel audio.
2. Apply echo cancellation or DM-audio suppression so TTS playback is not
   transcribed as a player.
3. Run VAD per channel.
4. Run streaming ASR.
5. Run streaming diarization/speaker activity tracking.
6. Merge ASR word timestamps with speaker activity.
7. Detect overlap windows.
8. For overlap windows, run a multitalker or source-separation pass when needed.
9. Convert transcripts into player-intent candidates with confidence.
10. Send only high-confidence, game-relevant intent to the DM orchestrator.

Speaker identity anchors:

- Session check-in voice sample for each player.
- Optional seat assignment.
- Optional device/player remote identity.
- Ongoing confidence scoring and correction.

## Product Rules

- No push-to-talk as the required path.
- No instruction that players must pause unnaturally or enunciate for the system.
- Backchannels may be ignored when irrelevant.
- Low-confidence crosstalk should not become canon.
- Consequential actions, private messages, consent/safety signals, and rules
  declarations require high confidence or clarification.
- The DM may ask a quick clarification after chaotic overlap, but that should be
  the exception, not the normal interaction pattern.

## Out-Of-Character And Table Pause

In-person play takes breaks: the table goes off-game for twenty minutes to catch
up on life, and that is part of the evening, not a fault. An always-listening
system must handle this gracefully or it ruins exactly the moments people show up
for.

Failure modes to avoid:

- The DM nags ("so, what do you do?") into a social moment.
- The intent gate fires the DM on off-game chat ("as you discuss the movie, a
  goblin appears...").
- Off-game speech is stored as canonical game history, contaminating NPC memory,
  dreaming, and retrieval.
- Personal conversation is transcribed and kept, which players may not want.

Required behavior:

- **Out-of-character is a first-class session state**, distinct from in-play.
- **Default to silence when unsure.** If the system cannot tell whether the table
  is playing, it does nothing and waits. It never interrupts a social moment. It
  may, rarely, offer to hold the scene, but it does not prod.
- **Address-to-resume.** The table re-engages the DM with a cue ("DM, we're
  back"). This is a boundary signal, not push-to-talk: the no-push-to-talk rule
  means not gating every in-game utterance, whereas a single resume cue at the
  edge of a break is cheap and natural. Entering OOC can be explicit ("DM, pause")
  or proposed by the system after sustained off-game speech.
- **OOC spans are a visibility/retention class.** Tag them; exclude them from
  canonical game recall, NPC memory, embeddings, and post-session dreaming. Prefer
  not persisting OOC audio/transcripts at all, or quarantine them with short
  retention. This reuses the existing audience/visibility model and is a privacy
  feature as much as a memory one.

Reading the room — knowing when not to be the DM — is a human-DM strength and a
place a bad AI DM fails. Stepping back for the catch-up moments is a feature, not
a limitation.

## Phase 0.4 Audio Chaos Spike

Run this before building deep voice features. It splits into two halves with
opposite requirements, so they run independently and neither needs the full group
plus a working AI at the same time.

### 0.4a: Input Chaos (needs people, not the AI)

Tests capture, diarization, speaker identification, overlap detection, and intent
attribution under real table noise. The AI does not need to exist yet, so any
chaotic co-located game is a valid proxy — a family Magic: The Gathering night
works, since it produces real overlap, crosstalk, prop noise, and structured
game-intent speech ("attack", "block", "in response", "counterspell").

Proxy caveats: it cannot test the full-duplex problem (no TTS in the room — that
is 0.4b), it likely has fewer speakers than a 4-6 player table (more speakers is
harder, so passing at 3-4 is an early signal, not a full pass), and MTG's clipped
rules-speak is an easier register than freeform in-character D&D.

Inputs:

- Real co-located players around the intended table (D&D group, or a proxy game).
- The intended microphone setup.
- Dice, cards, paper, minis, and normal table noise.
- 20-30 minutes of representative play-like conversation.

Capture so the recording yields data, not just a memo:

- Record the candidate mic setup and a single room-mic baseline simultaneously, so
  per-channel and baseline cases come from one sitting.
- Record video for ground truth: scoring attribution requires knowing who actually
  spoke.
- Get explicit consent to record.
- Keep the labeled recording as a reusable benchmark clip. One good clip can be
  replayed offline through every candidate pipeline, so later comparisons need no
  re-gathering.

Events to capture (scripted or naturally occurring):

- Two players speak over each other with different intended actions.
- Three-way crosstalk.
- Short backchannels: "yeah", "wait", "no", "I help", "counterspell".
- Similar-volume side comments.
- Laughter and non-speech table noise.
- Physical dice and mini movement during speech.

Compare at least:

- Single laptop mic baseline.
- Best practical multi-channel table setup.
- Riva streaming ASR + diarization.
- NeMo Streaming Sortformer pipeline.
- pyannote local diarization as an offline oracle/repair path.
- Multitalker ASR/source-separation path for overlap windows if feasible.

### 0.4b: Full Duplex (needs the AI, not many people)

Tests the half 0.4a structurally cannot: the system talking back into the room.
AEC and barge-in are about the speaker-in-room feedback loop, not diarization
difficulty, so this runs solo or with one other person.

- Play TTS into the room over the table speaker while mics are live.
- Confirm DM-audio suppression / echo cancellation keeps TTS playback out of the
  transcript as a false player utterance.
- Confirm barge-in: a player interrupting mid-sentence stops DM audio quickly and
  cancels the in-flight synthesis.
- A private player message/reply that must not leak into the table-wide transcript.

The two halves converge into the full integrated test only after each passes on
its own.

## Acceptance Criteria

The spike passes only if the best practical setup meets these gates. Criteria on
attribution, overlap, and label stability are validated in 0.4a; criteria on TTS
playback and barge-in are validated in 0.4b.

- Non-overlapped action-bearing utterances are attributed to the correct player
  at least 95% of the time.
- The system detects overlapped speech windows at least 90% of the time.
- For overlapped action-bearing speech, the system either captures the correct
  player intent or asks a clarification; it must not silently assign the wrong
  action to the wrong player.
- Speaker labels remain stable across a session after enrollment/check-in.
- DM/TTS playback does not create false player utterances during normal playback
  or barge-in.
- Barge-in stops DM audio quickly enough to feel natural.
- The transcript marks uncertainty explicitly.
- Private player replies are not leaked into table-wide transcript/memory.
- Overlap recovery fits the live hardware budget or degrades to clarification
  without silently committing incorrect intent.

Failing a single laptop mic is acceptable. Failing a reasonable multi-channel
table setup means voice is not ready and the project should not proceed deeper
into voice-dependent work.

## Fallback If The Gate Fails

If the gate fails, the project can still continue as a text/table-console MVP, but
the live voice experience should be marked blocked.

Possible mitigations:

- Better microphone layout.
- Per-seat microphones.
- Better echo cancellation.
- Fine-tuned speaker embeddings from table data.
- More conservative intent-confirmation UX.
- Offline post-session transcript repair.

Do not hide this behind push-to-talk as the main product path.

## Open Questions For Speech Domain Experts

If domain experts in streaming speech can be consulted, their time is best spent
on production readiness, roadmap, and real-world footprints — things hard to
determine from documentation or self-benchmarking. Useful questions:

Diarization and attribution:

- How production-ready is streaming diarization plus speaker ID — usable for live
  attribution, or offline-only with Sortformer as the live path? Real Streaming
  Sortformer latency and accuracy with speaker-cache tracking?
- Does multitalker / target-speaker ASR scale cost per active speaker, and is it
  worth it versus per-person mics?
- How stable is cross-session speaker recognition from a short check-in sample,
  and does it expose usable confidence scores?

Full duplex:

- Is built-in AEC / barge-in available for TTS-in-the-room, or is reference-signal
  echo cancellation a build-it-yourself problem?
- TTS streaming first-chunk latency, and how fast a synthesis stream can be
  cancelled or flushed mid-utterance (the 200 ms barge-in budget). Voice cloning
  for NPC voices.

Hardware reality:

- Real VRAM and latency for a live ASR + streaming diarization + TTS stack on a
  single 4090, including gotchas not in the spec sheet.
- An honest streaming-Riva vs faster-whisper comparison for this use case.

Questions that are easy to benchmark directly (raw decode tokens/sec, basic
quality) do not need expert input.
