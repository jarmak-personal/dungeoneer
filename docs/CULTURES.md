# Cultures and Arcane Schooling (Aurevost Rules Extension)

## Purpose

Aurevost is **all-human**. What 5e loads into *ancestry* — a level-1 power spike,
innate utility powers, and a stat package — is redistributed into things the setting
already asserts: universal arcane schooling, culture-as-upbringing, common tech, and
widespread grafting. There are no PHB species. The world already says
"heritage came loose from nation and place" and that its peoples are "thoroughly
mixed" ([world.yaml](../worlds/aurevost/world.yaml)); this makes that literal.

Like [Ship combat](SHIP_COMBAT.md), this is a **world rules extension** on the SRD
pack — content in existing primitives (proficiencies, advantage, cantrips, items),
not new engine concepts.

## Where ancestry's job goes

| 5e racial feature | Aurevost home |
|---|---|
| Innate utility magic (darkvision, minor telekinesis, light) | **universal arcane schooling** (utility cantrips) + gear (khevric lamps) |
| Combat trick (breath weapon, innate attack spells) | **gear** (grenades, khevric sidearms) or class |
| Ability score increase | **nowhere** — scores are the player's (nature, chosen) |
| Skill / tool proficiencies, languages | **culture** |
| Identity / flavor | **culture + vocation** |
| The genuinely superhuman | **functional augmentation** from veined creatures, with individual costs and strain |

## The stack

0. **Universal arcane schooling** — the level-1 baseline everyone shares.
1. **Ability scores** — the player's own.
2. **Culture / origin** — where and how you were raised.
3. **Vocation / background** — what you did.
4. **Augmentation** — common and optional, with individual costs and possible strain.

Plus a **gear layer** (the purchased other half of "enhanced everything").

## Tier 0 — Universal arcane schooling

The crust is khevra-rich and basic arcane practice is normal schooling. So **every PC,
every class, begins arcane-literate.** Mechanically:

- Each PC chooses **two non-damaging utility cantrips** from an approved short
  list: **Light, Mage Hand, Mending, Message, and Prestidigitation**. No attack
  or damage cantrips. Their spell effects come from the active rules pack, not
  improvised descriptions.
- Schooling has **no ability score or ability modifier**. If a schooling
  cantrip permits a saving throw, its fixed DC is **10**, with no proficiency
  bonus. The spell's components, casting time, and effect come from the active
  pack. Missing spell content blocks that casting rather than authorizing an
  invented effect.
- Schooling choices are separate from class cantrips. If a character knows the
  same spell through both, it is not an extra distinct spell: the player
  selects which source they are using, and that source's rules apply. Each
  source's own rules decide its choice quota; a duplicate does not add another
  distinct spell to the combined list.
- The initialized sheet records each chosen spell and its granting source
  separately. A cast records the chosen source, applicable pack and spell
  definition, inputs, dice, and resulting events so replay does not have to
  infer which casting rules applied. The concrete sheet and cast schemas remain
  to be authored; a missing required spell or class definition blocks the cast.
- A graft may augment schooling only when an authored, accepted effect says so;
  schooling itself grants no graft. Starting grafts remain subject to the same
  authored options and costs as other equipment.
- **Setwork operation** — a PC can run everyday khevric devices and man a ship station
  at the baseline. This feeds [Ship combat](SHIP_COMBAT.md): anyone is a competent hand;
  culture affinity and class are the *edge*, not the price of entry.

**Why utility-only.** Magic here is *infrastructure*, not weaponry. Keeping the
universal kit non-combat preserves caster identity: a Wizard is not "the one with
magic" (everyone has magic) but "the one who specialized and weaponized it" — a truer
picture of a caster in a magic-saturated world. Firepower lives in the gear layer, not
the school layer.

**Divine is the deliberate exception.** Divine magic stays rare, costly, and socially
fraught (world.yaml), so a divine-bonded PC is genuinely unusual. Arcane is universal;
divine is not.

## Tier 1 — Ability scores

From the player (point buy / standard array), **never from origin.** Physical
capability is 5e's "born this way" lever; we keep it off the culture axis so culture
can never read as biological essentialism in cultural clothing. The setting's own canon
— people "thoroughly mixed," heritage "loose from nation and place" — forbids
nation-as-stat-block.

## Tier 2 — Culture / origin: your seafaring tradition

Before khevra, every island-nation had its own way on the water — how it read the
stars, forecast weather, built hulls, navigated, and survived the open ocean. The First
Setting dissolved the old borders, but those ways did not die; they became **diaspora
craft, carried by people rather than tied to a place** (world.yaml already names
"diaspora memory, accent, craft, and inherited grievance"). **Your culture is the
seafaring tradition you were raised in**, wherever you happened to be born.

Grants, **non-physical only**:

- **Maritime / heritage skills** — navigation, star-reading, weather-sense, water
  survival, small-boat and hull craft (Survival, Nature, Vehicles (water), the relevant
  tools). This is the *sea and heritage* domain; the workaday-job domain belongs to
  vocation, so the two never overlap.
- Exactly **one narrow, situational advantage**, in your tradition's element — open-ocean
  star navigation, storm survival, reef and coastal waters, reading a strange crew.
  Advantage is 5e's biggest non-magical lever (~+3 to +5); one situational use per
  culture, not a pile.
- A **lattice affinity** — the modern khevric engineering school your tradition fed into
  (sorrellian / otharian / savarran / ilvane; see world.yaml `engineering_traditions`).
  The famous schools descend from particular old maritime nations, so most traditions
  lean toward one — but it is a *default*: training or vocation can override it, or leave
  it **none inherited** for the smaller traditions that never grew into an engineering
  empire. Plugs into [Ship combat](SHIP_COMBAT.md)'s tradition bundles.

**There are more seafaring traditions than the four superpowers** — which is the
safeguard against four traditions becoming four origin stat blocks. A forgotten
archipelago's star-line is a culture; so is the Savarran deep-water way; a
Caelport dockrat trained on Marovari rigs must be expressible. Keep seafaring
tradition (heritage) and lattice affinity (modern engineering) as *separate,
linkable* tags.

**Why the old ways still matter.** Modern sailing runs on setwork — but setwork fails:
becalmed and dead in the water, off the charted routes, or inside a rejection zone where
khevra does not work (the Asha approaches, the First Land). Exactly there, the sailor who
can navigate by stars and survive without setwork is worth a whole crew. Culture is the
competence that pays off when khevra cannot — the setting's most charged ground.

## Tier 3 — Vocation / background: your job

The classic 5e background slot, kept **practical**: the trade you actually worked —
clerk, dockhand, smuggler, gunner, shipwright, factor. Grants job/practical
proficiencies and tools, and **no advantage** (the single situational advantage belongs
to culture, so the leash holds). **Culture (your seafaring heritage) + Vocation (your
job) replaces 5e's race + background** — two axes, neither physical, split cleanly by
domain: sea-and-heritage vs workaday-craft, so they never hand out the same thing twice.

## Tier 4 — Augmentation

Cosmetic grafts made from khevra processed out of eroded sands are widely
used for fashion and status. Functional grafts use veined creatures, including
their [cores](../worlds/aurevost/items/khevra_core.yaml); they are rarer and
more burdensome. Grafting can be socially fraught in some places. Individual
grafts have individual costs; some decorative ones have no contamination
cost. Players can choose authored
starting grafts under the active game's equipment rules. Accumulated graft
cost and temporary exposure share an uncapped total, with a free tolerance
and nonlinear penalties; removal is difficult. See
[Khevra grafts](KHEVRA_GRAFTS.md).

## The gear layer

Innate *combat* powers become **purchased tech**: grenades, khevric sidearms, and lamps
(darkvision-as-equipment — which restores light as a managed resource for dungeon and
maritime play). Firepower is bought, not born; the deliberate complement to
magic-as-schooling.

## Worked examples

Each character is **one seafaring culture + one vocation**, mixed freely.

**Culture — Savarran deep-water tradition** (the old coastal superpower's way: charted
bulk-freight routes, admiralty navigation, conservative seamanship)
- Skills: Vehicles (water), Insight. Tool: navigator's tools.
- Situational advantage: navigation and seamanship on **established, charted routes**.
- Lattice affinity: **savarran** (precise, survivable, hard to repair in the field).

**Culture — an old archipelago star-line** (a forgotten island-nation's open-ocean
star-navigation and storm-craft, now carried only by its scattered diaspora)
- Skills: Survival, Nature. Tool: navigator's tools.
- Situational advantage: navigating by stars on the **open ocean**.
- Lattice affinity: **none inherited** — this line never became an engineering empire;
  they crew others' hulls (affinity set by training or vocation instead).

**Vocations to pair with either** (job, practical, no advantage):
- *Bonded clerk* — skills History, Persuasion; tool forgery kit or calligrapher's. The
  Savarran counting-house as a *job*, not a heritage.
- *Battery gunner* — skill Perception; proficiency with ship weapons; the deck trade.

A Savarran-raised bonded clerk and a star-line sailor turned gunner are both legal, and
neither took a single physical bonus. Culture brings the sea and the one advantage;
vocation brings the trade.

## Power budget

Roughly: the 5e ancestry/background budget becomes *utility cantrips (universal)
plus a few proficiencies, one situational advantage, a ship affinity, and a
vocation*. Slightly under PHB on raw level-1 combat power **on purpose** —
chargen here is flatter and more grounded, suiting the political-maritime tone.
Ship affinity needs to be **concrete and usable at level 1** or culture will
feel like "just two skills" until ship play begins. Starting grafts require
their own affordability and power-budget review rather than being assumed to
arrive only later.

## Settled vs open

Settled in design:

- All-human; no PHB species; no physical stat from origin.
- Universal arcane schooling as the level-1 baseline; each PC chooses **two
  non-damaging utility cantrips** from Light, Mage Hand, Mending, Message, and
  Prestidigitation.
- Schooling has no ability connection and uses fixed save DC 10. Any graft
  effect that changes it is separately authored.
- Culture = a **seafaring tradition**: maritime/heritage skills + one situational
  advantage + a lattice affinity (a default; overridable; may be none inherited).
- Culture (seafaring heritage) and Vocation (job) split by **domain** — sea/heritage vs
  workaday craft — so their proficiencies never overlap. Vocation grants no advantage.
- Culture + Vocation replaces race + background.
- Cosmetic grafts are widespread; veined-derived functional grafts are rarer
  and carry a much higher burden. Both are optional at character creation
  under applicable equipment rules.
- Divine remains the rare, costly exception.

Open / to author (content and tuning, not design forks):

- How (or whether) schooling scales, and the precise khevra augmentation
  effects and costs.
- The seafaring-tradition catalog — each one's heritage skills and its single advantage,
  finer-grained than the four superpowers.
- Exact proficiency counts on each axis (the domain split is settled; the numbers tune).
- Whether lattice affinity is a flat bonus or unlocks a tradition action at level 1.
- Whether divine-bonded PCs need a distinct chargen gate.
