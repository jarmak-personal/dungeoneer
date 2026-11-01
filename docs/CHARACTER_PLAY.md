# Character Creation And Advancement

## Boundaries

A player owns the character's identity and choices. The rules engine validates
and applies mechanical choices using the campaign's active rules pack and any
accepted extensions; the event log owns the result. A setting supplies its
people, equipment, and setting-specific options, not a universal progression
system. The active game rules and campaign configuration determine whether
and how advancement is earned and applied.

This is a play procedure, not a replacement for a class catalog or advancement
table. If a necessary pack definition, setting option, or campaign policy is
missing, identify the missing input and leave the dependent operation blocked.
Do not invent a class feature, level, reward, or legal choice.

## Creating A Character

1. **Choose a front door.** The player selects a pregen, builds a character,
   or imports an existing sheet. Establish the active rules pack, extensions,
   starting level or equivalent, and character-creation policy first. If an
   import conflicts with them, present the conflicts; do not silently rewrite
   the character.
2. **Establish the person.** Ask for the character's name and the background,
   motives, relationships, and boundaries the player wants to define. Suggest
   options only as proposals. Other characters, factions, and world facts need
   their normal authority and review; the player controls their own character,
   not an NPC's private motives or the world's unapproved history.
3. **Make rules choices.** Present the available, authored options and their
   prerequisites: ability generation, class or equivalent, proficiencies,
   equipment, and any further choices the active rules require. Show source,
   costs, exclusions, and practical effects before confirmation. If options
   overlap, follow the active rules' duplicate and replacement policies; do not
   award an extra benefit because two sources name the same proficiency.
4. **Apply the setting overlay.** If the campaign loads Aurevost's 5e
   extension, collect its culture, vocation, and two distinct schooling
   cantrips using [Cultures](CULTURES.md). Its schooling does not choose an
   ability score and its save DC is 10. Culture and vocation do not grant
   physical ability bonuses. Players may choose authored starting grafts under
   the active game's equipment and purchase rules; missing graft or pricing
   rules block the affected choice. These
   setting choices do not replace unrelated choices required by the active
   class or pack. Other game systems need their own compatible extension rather
   than assuming these 5e-specific grants work unchanged.
5. **Preview and approve.** Present the narrative proposal and derived sheet,
   listing each option's source and any unresolved or illegal choice. If a
   required definition is missing, label the preview incomplete; do not present
   it as rules-legal or final. The player may revise; nothing is canon merely
   because a draft exists. Once inputs are complete, present the final sheet
   and obtain renewed approval for any changed character content. Validate the
   entire approved proposal and commit creation, sheet
   initialization, and control assignment atomically as specified in
   [Lifecycle](LIFECYCLE.md#pc-authoring-and-ingestion).

Pregens are authored examples, not proof that all underlying class definitions
exist. If a pregen omits required choices, request them from the player; a
missing definition still blocks validation. A player may cancel or save a draft
without committing the PC.

## Progress And Advancement

Before play, establish the advancement policy supported by the active game
rules and selected campaign configuration. An eligible achievement or award is
not the same thing as a completed level-up. Record its source and recipients
through the authorized rules route, without assuming that all PCs advance
together or that one kind of job grants a particular award. The policy decides
eligibility, timing, distribution, and any caps; an unspecified policy blocks
the award or advancement that depends on it.

When an actor becomes eligible:

1. Present the earned change and the active rules' legal options to the
   controlling player. Explain prerequisites, costs, and relevant tradeoffs.
   Eligibility does not automatically make a choice on the player's behalf.
2. Collect all required selections, including a recorded die result if the
   active policy requires a roll. The actor keeps their current legal state
   while a choice is pending. A player can defer the choice where the selected
   rules permit; do not assume immediate access to unselected abilities.
3. Validate against the same source versions and current state. Recheck if the
   state has changed while the proposal was pending. Apply the accepted
   selections and derived changes as one atomic rules operation; reject the
   entire operation on a failed prerequisite, missing definition, stale state,
   or invalid choice. Report the reason and allow revision.
4. Record the source, choices, required dice, and resulting before/after state
   using typed rules events sufficient for deterministic replay. A character
   level or feature does not change just because narration says it does. The
   concrete advancement event and sheet schemas remain authoring work; no
   existing event is assumed to carry an undefined payload.

An alternate campaign may use a different advancement policy or a game
without levels. The procedure follows the loaded rules instead of translating
every reward into 5e levels. Setting-specific rewards such as a core,
training, or a graft are separate from class progression and require their own
accepted definitions and costs.

## Worked Boundaries: Dorn And The Cull

Dorn's pregen is an illustrative first-level fighter sheet, not a complete
character-creation catalog. On selecting Dorn for an Aurevost 5e campaign, the
player chooses and approves two schooling cantrips not present on the pregen.
The system also checks all other required sheet inputs and the active
definitions. If the fighter, cantrips, or another required definition is
missing, it reports what is missing and does not create a partially initialized
character. The player can revise the proposal or choose a supported alternative.

After the Greywake job, the commission and any core sale settle independently
of advancement. If the campaign's supported policy authorizes progress, apply
that policy to the actual outcome and eligible recipients; refusing or sparing
the wolf does not automatically prevent progress. If Dorn becomes eligible for
advancement, his player chooses among the legal class options. Without a loaded
advancement definition, the document cannot calculate a level, hit points, or
feature and the mechanical advancement remains blocked.

## Open Authoring Work

- Complete character-sheet and advancement event contracts, including atomic
  initialization, pending choice, stale-state handling, provenance, and replay.
- The selected game's class, spell, equipment, creation, and advancement
  definitions, plus supported campaign progression configurations.
- Complete Aurevost culture and vocation catalogs, proficiency collision
  handling, and any setting-specific options not yet authored.
- Import reconciliation, multiclassing and retraining under applicable packs,
  co-controlled-character choices, and distinct treatment of companions where
  the active rules require it.
