# DM Profile And Improvement Loop

## Position

There is no universal best DM. Tables differ: strict rules versus rule-of-cool,
heavy story pressure versus open sandbox, lethal versus forgiving, theatrical
versus terse. A fixed DM personality cannot serve all of them. Dungeoneer's edge
is not being the best DM; it is being tunable to a specific table — which no
single human DM can be.

Two separate problems:

- **DM profile**: static, table-chosen configuration of style.
- **Improvement loop**: slow, human-in-the-loop adaptation to what a table enjoys
  over time.

## The Profile Has Two Layers

### Policy knobs (system-enforced)

These cannot be prompt text, because the architecture must enforce them, not hope
the model complies.

- **Rules authority** — strict / balanced / rule-of-cool. Controls whether the
  rules engine's `narrative_override` capability is available and how freely the
  DM may use it. Strict: no override; the rules engine is final. Rule-of-cool: the
  DM may override outcomes for dramatic effect, and every override is logged with
  provenance. A controlled, inspectable relaxation of determinism, not an
  abandonment of it.
- **Lethality** — soft / standard / deadly. Whether monsters pull punches, whether
  HP/consequence fudging is permitted (and logged), how openly danger is
  telegraphed. Interacts with the tactics advisor.
- **Story pressure** — sandbox / guided / railroad. How strongly the DM steers
  toward plot versus following player agency.
- **Spotlight balance** — how actively the DM distributes scenes and attention
  across players. Fed by per-player preferences (below).
- **Pacing and patience** — tolerance for tangents and slow play before the DM
  nudges. Directly sets the out-of-character patience default.
- **Safety and content** — rating, lines, veils, banned themes. This is a
  *separate* `safety_config`, not a dm_profile knob (see "Safety Config Is
  Separate"); the profile references it.

### Persona knobs (prompt-shaped)

These are genuinely just style, and a persona description works fine.

- **Tone** — grimdark / heroic / comedic.
- **Narration density** — terse / cinematic.
- **Humor** — dry or none / playful.
- **NPC voicing** — how distinct and theatrical NPC voices are.
- **Combat description** — mechanical / cinematic.

## Preset Pack Plus Custom

A "pack of DMs" is named presets over the knobs; custom exposes the knobs
directly. Starting presets (a proposal, not fixed):

- **The Rulesmaster** — strict authority, standard-to-deadly, terse and tactical,
  low humor.
- **The Storyteller** — balanced authority, high story pressure, cinematic
  narration, strong NPC voicing.
- **The Improv Buddy** — rule-of-cool, soft lethality, playful, sandbox.
- **The Balanced DM** — the middle of every knob.

## Per-Player Spotlight

One table holds different desires: a tactics fan and an intrigue fan at the same
table cannot be served by one global knob. So the profile is table-level for
policy, plus **per-player spotlight preferences** — give the tactics fan combat
beats and the intrigue fan the political scene. Fed by per-player remote feedback.
Design the per-player dimension in early; bolting it on later is painful.

## The Improvement Loop

The loop must be human-in-the-loop and eval-driven, never silent optimization.
Fun is subjective, sparse-signal, and easy to Goodhart: optimize a proxy like
"engagement" and the DM drifts toward cheap shocks and constant combat.

- **Signals.** Explicit feedback through player remotes (a low-friction "more of
  this / less of this", an end-of-session read). Implicit signals — tangent
  frequency, session length, engagement, where barge-ins cluster, which hooks get
  ignored — are noisy and read carefully (a long tangent may mean a great night).
- **Analysis in post-session dreaming.** Dreaming already replays the session
  offline; it is the natural place to produce a *proposed* profile adjustment
  ("this table leaned into intrigue and disengaged in long combat; suggest shorter
  fights"). A proposal, not a silent change.
- **Host confirms (asynchronously).** Profile adjustments are reviewed by the host
  between sessions, not as a mid-play prompt. This is a deliberate exception to
  "players just play": tuning *how the table wants to be DMed* is a meta-choice the
  group owns, but it is a rare, low-friction, between-sessions opt-in, never a
  per-change chore. The same propose-and-approve pattern dreaming uses. The table
  always controls
  its own DM.
- **Style evals verify.** The eval harness extends to score behavior against the
  chosen profile: did the strict DM enforce the DC, did the rule-of-cool DM take
  the dramatic override, did it honor the patience setting? Style becomes testable
  instead of vibes.

## Trust And Correction

A human DM earns the table's trust over years; an AI DM has not yet, so it needs
two mechanisms a veteran human would not.

- **Override tell.** A human DM hides their fudging; a new AI DM should not, until
  trust is built. A `narrative_override` is always audit-logged, and by default
  carries a light **tell** — a subtle, dialable signal (operator-visible always; a
  soft diegetic or UI cue configurable per table) — so drift is catchable mid-play.
  As trust grows the tell can be turned down. Inspectability in the log is never
  optional; the tell is the *table-facing* dial.
- **"Something's off" channel.** Players get a first-class meta way to tell the DM
  it is going wrong — railroading, a contradiction, a tone miss, "that's not what
  happened." This is **distinct from the X-card**: the X-card is for *safety*; this
  is for *DM correctness*. On a flag the DM pauses, surfaces what it was about to
  do, and lets the table redirect. Flags are logged and feed the improvement loop —
  they are some of the highest-signal training data the system can get about whether
  this table's DM is working.

Both exist because the system has not earned blind trust yet. They are how the
table keeps a hand on the wheel while it decides whether it can let go.

## Profile Schema

`dm_profile` is first-class config, campaign-scoped, with a typed schema (no
prose-only knobs). Policy knobs are enums; persona knobs are short typed fields;
presets are a named map over the same knobs.

```yaml
schema: dwd.dm_profile.v1
id: dm_profile:greyhaven_main
campaign: campaign:greyhaven_main
preset: the_storyteller
policy:
  rules_authority: strict | balanced | rule_of_cool
  lethality: soft | standard | deadly
  story_pressure: sandbox | guided | railroad
  spotlight_balance: { mode: even | weighted, per_player: {} }
  pacing_patience: low | standard | high
persona:
  tone: "heroic but grounded"
  narration_density: terse | standard | cinematic
  humor: none | dry | playful
  npc_voicing: flat | distinct | theatrical
  combat_description: mechanical | cinematic
safety_config_ref: safety_config:greyhaven_main
```

A preset sets defaults; per-knob overrides apply on top. The profile is mutable
between sessions through the improvement loop (`dm_profile.updated`), not silently
mid-play. It is stored in its own table (`dm_profiles`) and loaded by the
orchestrator at session start.

## Safety Config Is Separate

Safety outranks style, so rating/lines/veils/banned-themes live in a separate
`safety_config`, not inside `dm_profile`. This keeps safety enforceable
independently of DM style and not silently mutable by the profile-tuning loop.

```yaml
schema: dwd.safety_config.v1
id: safety_config:greyhaven_main
campaign: campaign:greyhaven_main
rating: PG-13
lines: ["no on-screen harm to children"]      # hard nevers
veils: ["torture fades to black"]              # happens off-screen
banned_themes: []
```

Lines are hard "never" boundaries; veils are "fade to black." The
`safety_moderator` enforces the config as a gate, independent of the DM persona,
and a violation is caught before delivery rather than relying on the prompt.

## Cold Start

The first `dm_profile` and `safety_config` both come from the session-zero
questionnaire (emitting `dm_profile.seeded` and `safety.configured`). No learning
is required to start; the loop only refines the profile. See
[Lifecycle and bootstrap](LIFECYCLE.md) for where session zero sits in the boot
sequence.

## Build Order

- Phase 1: `dm_profile` as first-class config; session-zero seeds it; the persona
  layer drives DM prompting.
- Phase 2: the rules engine exposes the gated, logged `narrative_override`
  capability so rules-authority is enforced, not prompted.
- Phase 6: dreaming produces reviewable profile-adjustment proposals.
- Phase 7: style evals score DM behavior against the active profile.

Do not build the improvement loop before there is session data to learn from, and
never let it tune silently.
