# Latency Budget

Streaming is a hard requirement, not an optimization. The DM must feel like a
person at the table, which means it must begin responding before it has finished
thinking, and it must be interruptible. Every design choice in the live path is
subordinate to this.

This document defines the canonical metric, the per-stage budget, the
architectural constraints that streaming forces, and the degradation ladder for
when the budget is blown.

## Canonical Metric

The number that decides whether this product works is **Time To First Audio
(TTFA)**: the wall-clock time from the moment the player stops speaking
(endpoint detected) to the moment the first DM phoneme is audible.

Targets:

- TTFA p50: <= 1200 ms
- TTFA p95: <= 2000 ms
- TTFA hard ceiling: 2500 ms

Past roughly 2.5-3 s of silence after a person finishes speaking, the
conversation stops feeling live and starts feeling like a kiosk. The whole
pipeline is designed backward from this ceiling.

TTFA is not the only metric, but it is the one we optimize first. Supporting
metrics:

- **Sustained audio throughput**: once speech starts, it must not gap or stall.
- **Barge-in latency**: how fast the DM goes silent when interrupted.
- **Endpoint latency**: how long we wait to decide the player is done talking.
- **Speaker-assignment confidence**: whether game-relevant speech was attributed
  to the right player or correctly marked uncertain.

Latency is not useful if the wrong player is credited. The voice chaos gate in
[Voice chaos gate](VOICE_CHAOS.md) must pass before TTFA becomes the primary
voice milestone.

## The Live Path Is One Streaming Pipeline

The live conversational turn is a single streaming pipeline, not a sequence of
discrete request/response calls. Stages overlap. Critically, most of the work
happens *during* player speech, so the clock that matters (post-endpoint) only
pays for the serial tail.

```
player speaking ──────────────► [endpoint] ──────► first audio out
   │                                │                    ▲
   ├─ streaming STT partials        │                    │
   ├─ speculative context assembly  │                    │
   └─ (all overlapped, free)        └─ serial tail we budget below
```

What runs *during* speech and is therefore "free" on the TTFA clock:

- Streaming STT produces partial hypotheses continuously; the final transcript
  is mostly already computed when the player stops.
- Speculative context assembly begins on stable partial transcripts so
  retrieval is warm before endpoint.

## Post-Endpoint Budget

This is the serial tail measured from endpoint to first audio. The stages sum to
the TTFA targets above with headroom.

| Stage | p50 | p95 | Notes |
|---|---|---|---|
| Finalize last STT partial | 100 ms | 250 ms | Most audio already transcribed |
| Context assembly (cached) | 80 ms | 150 ms | Often near-zero if speculated |
| DM model time-to-first-token | 350 ms | 600 ms | Warm, resident model only |
| Generate first speakable clause | 200 ms | 350 ms | ~10-15 tokens at 50-80 tok/s |
| TTS first audio chunk | 250 ms | 450 ms | Streaming synth, RTF < 1 |
| Audio buffer + playback start | 50 ms | 100 ms | Small buffer for responsiveness |
| **Total TTFA** | **~1030 ms** | **~1900 ms** | Under p50/p95 targets |

The budget only holds if every model in the path is warm and resident. A cold
model load (tens of seconds for a VLM) blows the ceiling by an order of
magnitude. See "GPU Residency" below.

## Sustained Throughput

After the first audio chunk, the DM keeps talking. The risk shifts from latency
to starvation: if the next audio chunk is not ready when the current one
finishes, speech gaps and the illusion breaks.

- Spoken English runs ~150 words/min ~= 2.5 words/s ~= ~3.3 tokens/s of
  *consumed* content.
- The DM model target is 50-80 tok/s on the resident live model, ~15-20x faster
  than speech consumes it. This is a benchmark gate, not a guarantee: long
  context, image prefill, reasoning, or tool-resumption can still make the model
  the bottleneck.
- TTS is the bottleneck. It must synthesize faster than real time
  (real-time factor RTF < 1, target < 0.5) or audio underruns. TTS RTF under
  concurrent load is a promotion gate for any voice, not a nice-to-have.

Implication: we generate the next TTS chunk while the current one plays, and we
keep audio buffers small (200-300 ms) so the pipeline stays responsive to
interruption. Small buffers trade underrun safety for barge-in speed; we accept
that trade.

## Barge-In

The player must be able to cut the DM off mid-sentence, like a real table.

- Barge-in latency (player speech onset during playback to DM audio stop):
  <= 200 ms.
- On detected interruption we must: stop audio playback, flush the audio buffer,
  cancel the in-flight TTS job, and abort the in-flight LLM generation.
- The aborted partial turn is still persisted for audit with
  `delivery_status=aborted`. It must be excluded from player-facing and
  NPC-facing recall unless a later delivered event explicitly references it.

This is why the LLM and TTS calls on the live path must be cancellable streams,
not fire-and-await. Any component that cannot be aborted cheaply cannot sit on
the live path.

## Side-Channel Resource Budget

Parallel side-channel work must not borrow from the live turn's latency budget.
Private hidden checks, private DM questions, lore queries, and rules
clarifications are useful only if the table-visible conversation remains smooth.

Rules:

- The serial table lane owns the resident live DM model, streaming TTS voice, ASR
  stream, audio playback, and barge-in cancellation path.
- Side-channel work may use local deterministic tools and retrieval while the live
  lane runs, but may not evict, cold-start over, or preempt live-lane resources.
- If the side-channel needs model work while the live DM model is busy, it either
  uses an already-resident non-live worker, returns private text from deterministic
  support, or defers.
- Side-channel answers are text-first under contention. Private TTS is disabled
  while table audio is active unless a future deployment profile proves it cannot
  affect the shared stream.
- Side-channel tasks carry deadlines and cancellation. A missed deadline records a
  queued/deferred private notice, not a silent stall or table-visible pause.

## Endpointing

Deciding when the player is done talking is a latency source that sits *before*
the TTFA clock starts, but the player perceives it as part of the delay.

- Default trailing-silence threshold: 500-700 ms, tunable per table.
- Too short cuts players off mid-thought; too long feels sluggish. This is a
  feel knob, surfaced in settings.
- Enhancement (later): semantic endpointing that ends the turn faster when the
  utterance is grammatically complete, slower when it trails off. Not required
  for MVP.

## Rules Tool Calls On The Live Path

A DM turn often needs a deterministic result mid-narration ("you swing..."
[needs an attack roll] "...and the blade bites home"). A synchronous tool
round-trip stalls token generation and threatens the budget.

Strategy:

- Rules tools are local and deterministic; tool execution itself must be
  <= 50 ms. The cost is the model re-prompt, not the tool.
- Budget for a full rules round-trip (tool exec + model resumption
  time-to-first-token): <= 700 ms.
- Mask the stall with pre-generated filler audio ("let's see how that lands...",
  dice sounds) so the player hears continuity while the tool resolves. Filler is
  a latency-hiding tool, not just flavor.
- Structure prompts so the DM streams narration up to the decision point, calls
  the tool, then resumes. Do not have the model block on the tool before it has
  said anything.

## World Consequences On The Live Path

Strict state does not mean global state scans during a turn. Live world writes use
`dwd.consequence_plan.v1` to split the beat into immediate, deferred, and blocked
effects before any write.

Rules:

- Immediate world effects validate only the addressed state and local references:
  the event being appended, the relevant projection before-state, named targets,
  and the action's validator.
- Explicit clock advances and preauthorized clock outcomes may commit live when
  those local checks pass. They do not trigger a campaign-wide reaction scan.
- Broad consequence discovery — faction reactions, rumor spread, missed clock
  triggers, mementos, capsule refresh, recap/prep updates, and contradiction
  checks — runs in dreaming or side-channel review, not in the TTFA path.
- If an immediate effect cannot validate inside the live budget, it becomes a
  deferred or blocked effect. Responsiveness wins over speculative completeness.

## GPU Residency Is A Latency Constraint

The budget assumes the live-path models never cold-load. That makes residency a
latency requirement, not just a hardware-planning detail. The resident live set:

- **5090 (home)**: resident DM dialogue model (must stay hot).
- **4090 (home)**: streaming STT and streaming TTS (both hot), plus embeddings and
  a small NPC background model. Audio and transcripts are privacy-bound to the home
  machines.
- Retrieval embeddings are precomputed where possible; live retrieval is a vector
  query plus cached context, not synchronous embedding of history.

Everything else is off the live path and must not evict the resident set:

- Map/VLM perception is a turn-taking action, not a back-channel or continuous
  scan. The DM verbally acknowledges within the live budget ("let me look at the
  grid") and delivers the perception result in 3-8 s. Perception runs on a separate
  on-LAN GPU (the restricted-host RTX 6000 Ada), so it cannot evict the resident home
  DM model by construction; its only live cost is a LAN round-trip, which must be
  kept off the audio path.
- Image generation is async: first preview in 10-30 s, surfaced when ready,
  never blocking dialogue.
- Video generation is async over minutes, fully decoupled from live play.
- Post-session dreaming is async over minutes or hours and can use heavy models,
  broad retrieval, validators, and all idle home hardware. The 6000 Ada may only
  receive sanitized media-side dream briefs.

If the resident live set does not fit on 4090 + 5090 alongside the supporting
services a session needs, that is the trigger to promote the DGX Spark from
bonus to requirement. This budget is the early-warning instrument for that call:
the first time TTFA p95 is blown by a cold load under realistic concurrency, the
hardware is the answer, not prompt tuning.

## Degradation Ladder

When the budget is at risk under load, degrade in this order. Each step trades
quality for responsiveness, and the rule is that responsiveness wins on the live
path.

1. Drop retrieval to the recency window only for low-stakes turns; skip vector
   search for this turn.
2. Switch the DM to a smaller/faster model variant for short reactive turns.
3. Switch TTS to the fastest available voice (e.g. Piper) under load.
4. Cover unavoidable long operations with filler/acknowledgement audio.
5. As a last resort, fall back to text output with a visible "DM is speaking"
   state rather than emitting gapped or badly delayed audio.

Degraded turns must not make memory-sensitive, rules-sensitive, or high-impact
world commitments. They should acknowledge, ask a clarifying question, or stall
gracefully until full context and canonical tools are available.

## Measurement

The budget is only real if it is instrumented from day one.

- Stamp every stage boundary (speech end, STT final, context ready, first token,
  first TTS chunk, first audio) into the `tool_calls` / `events` record.
- Track p50/p95/p99 per stage, per model, per GPU-residency state (warm vs
  cold).
- Alert when any stage exceeds its budget; a regression here is a release
  blocker, treated like a failing test.
- Feed these traces into the eval harness so latency regressions are caught
  alongside correctness regressions, not discovered live at the table.

The first end-to-end voice slice must report TTFA before it is considered done.
"It works" is not a passing condition; "it works within budget" is.
