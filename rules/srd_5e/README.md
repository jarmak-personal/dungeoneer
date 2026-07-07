# 5e SRD Rules Pack — Worked Examples

This is a minimal sketch of the **rules pack** layer from
[docs/RULES_ENGINE.md](../../docs/RULES_ENGINE.md) — "Position — How, Not What."
It exists to make the engine/pack seam concrete: the engine owns the *procedure*,
this pack owns the *numbers*, and a `dm_profile` owns the *dialect*.

## Layout

```text
rules/
  srd_5e/                  # the system pack (5e SRD content, CC-BY-4.0)
    pack.yaml              # manifest + ladder_mapping (the seam the engine reads)
    dc_guidance.yaml       # SRD Typical Difficulty Classes
    conditions/prone.yaml  # a typed condition (what "prone" mechanically means)
    statblocks/commoner.yaml
    statblocks/spy.yaml
    README.md              # this file
  aurevost_pregens/        # instances built FROM the pack (campaign rules state)
    pc.dorn.yaml           # resolves rules:pc.dorn  (binds pc:dorn)
    pc.vanya.yaml          # resolves rules:pc.vanya (binds pc:vanya)
```

`worlds/aurevost/` references mechanics abstractly: `wick.yaml` carries
`stat_block_ref: rules:npc.commoner`, `pcs/dorn.yaml` carries
`sheet_ref: rules:pc.dorn`. The world never names the system — the loaded pack
resolves those refs. Swap in a PF2e pack and the same world still loads.

*(Placement note: where campaign rules-state ultimately lives — here, world-seed
pregens — is still an open question. For this sketch the instances sit under
`rules/` beside the pack; they are not SRD system content.)*

## The procedure (unchanged across systems)

From `RULES_ENGINE.md`:

```text
player intent (NL)
  -> rules_referee: intent + scene context -> typed check spec
  -> rules tool (deterministic)             -> structured result
  -> map result onto the engine degree ladder (via pack.ladder_mapping)
  -> consequence plan                       -> validated state events
  -> projection update
  -> orchestrator narrates the result
```

Every step below is engine procedure; every *number* it reads comes from a pack file.

---

## Example 1 — Dorn shoves a commoner prone

**Intent:** "Dorn slams his shoulder into the commoner and knocks him flat."

1. **rules_referee → check spec.** A shove is an SRD contested check:
   ```yaml
   kind: contested_check
   actor:  { id: pc:dorn,         using: athletics }      # STR (Athletics)
   target: { id: rules:npc.commoner, using: best_of [athletics, acrobatics] }
   special: shove
   on_initiator_win: { apply_condition: rules:condition.prone }
   ```
2. **Engine reads pack data.** Dorn's sheet → Athletics **+5**. Commoner statblock →
   STR mod **+0**, no proficiency → Athletics **+0**, Acrobatics **+0** (best = +0).
3. **Roll (deterministic, seeded digital roller).** Dorn `d20=11 → 16`; commoner
   `d20=14 → 14`. Margin = **+2**.
4. **Map onto the ladder** via `pack.ladder_mapping.contested_check`:
   `margin > 0` → **success** (margin < 10, so not `strong`). The engine did not know
   "shove ties favor the defender" — that rule lives in the pack mapping.
5. **Typed effect → event.** Initiator won, so apply the prone condition:
   ```yaml
   type: condition_applied
   actor: pc:dorn
   payload: { target: <commoner instance>, condition: rules:condition.prone }
   provenance: { tool_call: tool:contested_check_0007 }
   ```
6. **Consequence is pack content, not engine logic.** Next round, Vanya's melee
   attack against the now-prone commoner gets **advantage** — the engine reads a
   `dwd.modifier.v1` `roll_shape: advantage` modifier from `conditions/prone.yaml`
   and resolves it through `pack.yaml`'s `modifier_policy`. Advantage/disadvantage
   is a 5e idiom; it lives in the pack, never in the engine.

---

## Example 2 — Vanya reads a lying merchant (hidden Insight)

**Intent:** "(privately) Can Vanya tell the merchant is lying about the shipment?"

1. **rules_referee → check spec.** An Insight check; the referee picks a difficulty
   *band* from fiction, not a number:
   ```yaml
   kind: ability_check
   actor: { id: pc:vanya, using: insight }      # WIS (Insight)
   dc_source: { band: medium }                  # -> dc 15 from dc_guidance.yaml
   adjudication_visibility: dm_only             # hidden check (see RULES_ENGINE social)
   result_audience: player:pc:vanya
   ```
2. **Engine reads pack data.** `dc_guidance.yaml` band `medium` → **DC 15**. Vanya's
   sheet → Insight **+4**.
3. **Roll (digital, because the check is hidden — RULES_ENGINE dice-source rule).**
   `d20=8 → 12`.
4. **Map onto the ladder** via `pack.ladder_mapping.ability_check`:
   `dc-5 (10) <= 12 < dc (15)` → **partial**. She gets a hedged read — "he's shading
   something, but you can't pin what." Note RAW 5e would call 12-vs-15 a flat fail;
   the **partial** band is this pack's declared overlay, and a stricter `dm_profile`
   could collapse it back to fail. Same engine, different dialect.
5. **Outcome → bounded disclosure → event.** The partial result becomes a
   perspective-limited answer to Vanya only:
   ```yaml
   type: check_resolved
   actor: pc:vanya
   payload: { skill: insight, total: 12, dc: 15, band: partial }
   visibility: dm_only
   result_audience: player:pc:vanya
   provenance: { tool_call: tool:ability_check_0042 }
   ```

---

## What this demonstrates

- **The procedure is identical** across a contest and a solo check, across combat and
  social — `rules_referee → typed tool → ladder map → typed event`. That is the "how."
- **Every number came from a pack file:** DCs from `dc_guidance.yaml`, the contest
  rule, tie-handling, degree thresholds, roll-shape policy from `pack.yaml`, the
  condition's modifiers from `conditions/prone.yaml`, and the modifiers from the
  sheets/statblock. That is the "what."
- **The ladder mapping is the seam.** 5e's binary RAW is mapped onto the engine's
  four-band ladder *by the pack*; the engine never assumes a success model. Swapping
  to a pack whose native model already has four degrees (PF2e) changes only this file.
- **`dm_profile` is the dialect knob** — it can narrow the overlay bands, tune
  lethality, and gate `narrative_override`, all without touching pack or engine.

Out of scope for this sketch (next if we go further): a typed schema/validator for
the pack files, spells/feats, the full condition set, and an eval fixture that runs
these two traces deterministically.
