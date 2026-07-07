from __future__ import annotations

from pathlib import Path

import pytest

from dwdlint import LintResult, Severity, lint_paths
from dwdlint.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]


def write_yaml(root: Path, name: str, content: str) -> Path:
    path = root / name
    path.write_text(content, encoding="utf-8")
    return path


def codes(result: LintResult) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def test_authored_corpus_is_clean() -> None:
    result = lint_paths(
        [REPO_ROOT / "worlds", REPO_ROOT / "rules", REPO_ROOT / "docs" / "simulations"]
    )

    assert result.diagnostics == [], "\n".join(item.format() for item in result.diagnostics)


def test_invalid_yaml_and_duplicate_keys_are_hard_errors(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "broken.yaml",
        """
id: item:first
id: item:second
kind: item
schema: dwd.item.v1
name: Broken
visibility: table
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD004" in codes(result)
    assert result.error_count == 1


def test_unknown_kind_is_an_extension_not_invalid_data(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "relic.yaml",
        """
id: relic:new_shape
kind: relic
schema: dwd.relic.v1
name: A New Shape
visibility: table
""",
    )

    result = lint_paths([tmp_path])

    assert result.error_count == 0
    assert result.extension_count == 1
    assert result.diagnostics[0].severity == Severity.EXTENSION

    assert main([str(tmp_path)]) == 1
    assert main(["--allow-extensions", str(tmp_path)]) == 0


def test_arbitrary_new_fields_are_allowed(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "item.yaml",
        """
id: item:test
kind: item
schema: dwd.item.v1
name: Test Item
visibility: table
new_field:
  any_shape: [is, allowed]
""",
    )

    assert lint_paths([tmp_path]).diagnostics == []


def test_dangling_managed_reference_is_an_error(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "location.yaml",
        """
id: loc:harbor
kind: location
schema: dwd.location.v1
name: Harbor
parent: region:missing
visibility: table
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD111" in codes(result)


def test_location_containment_cycle_is_an_error(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "locations.yaml",
        """
relationships: []
places:
  - id: loc:first
    kind: location
    schema: dwd.location.v1
    name: First
    parent: loc:second
    visibility: table
  - id: loc:second
    kind: location
    schema: dwd.location.v1
    name: Second
    parent: loc:first
    visibility: table
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD112" in codes(result)


def test_internal_truth_cannot_be_given_to_an_actor(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "secret.yaml",
        """
id: secret:inside
kind: secret
schema: dwd.secret.v1
name: Inside Truth
holders: [npc:someone]
visibility: internal
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD322" in codes(result)


def test_table_visible_private_field_is_an_error(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "faction.yaml",
        """
id: faction:test
kind: faction
schema: dwd.faction.v1
name: Test Faction
private_truth: This cannot be in a table-visible projection.
visibility: table
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD404" in codes(result)


def test_clock_segment_bounds_are_enforced(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "clock.yaml",
        """
id: clock:test
kind: clock
schema: dwd.clock.v1
name: Test Clock
owner: faction:owner
status: active
segments: {current: 5, max: 4}
stakes: Something changes.
advance_triggers:
  - {trigger: something_happens, amount: 1}
outcomes:
  complete:
    - create_fact: fact:test_complete
visibility: dm_only
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD301" in codes(result)


def test_empty_directory_does_not_report_a_false_pass(tmp_path: Path) -> None:
    result = lint_paths([tmp_path])

    assert "DWD006" in codes(result)


def test_foreign_id_fields_are_not_records(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "pack.yaml",
        """
id: rules:pack.test
schema: dwd.rules_pack.v1
name: Test Pack
license:
  id: CC-BY-4.0
  attribution: Someone.
""",
    )

    result = lint_paths([tmp_path])

    assert result.diagnostics == [], "\n".join(item.format() for item in result.diagnostics)


def test_reference_structs_do_not_redefine_records(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "condition.yaml",
        """
id: rules:condition.test
schema: dwd.condition.v1
pack: rules:pack.test
name: Test Condition
modifiers:
  - id: modifier:test_disadvantage
    schema: dwd.modifier.v1
    source: { kind: condition, id: rules:condition.test }
    when: { condition_active: rules:condition.test }
""",
    )
    write_yaml(
        tmp_path,
        "pack.yaml",
        """
id: rules:pack.test
schema: dwd.rules_pack.v1
name: Test Pack
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD102" not in codes(result)
    assert result.diagnostics == [], "\n".join(item.format() for item in result.diagnostics)


def test_reference_struct_id_is_checked_for_dangling(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "condition.yaml",
        """
id: rules:condition.test
schema: dwd.condition.v1
pack: rules:pack.test
name: Test Condition
modifiers:
  - id: modifier:test_disadvantage
    schema: dwd.modifier.v1
    source: { kind: condition, id: rules:condition.missing }
""",
    )
    write_yaml(
        tmp_path,
        "pack.yaml",
        """
id: rules:pack.test
schema: dwd.rules_pack.v1
name: Test Pack
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD111" in codes(result)


def test_dangling_rules_reference_is_an_error(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "npc.yaml",
        """
id: npc:someone
kind: npc
schema: dwd.npc.v1
name: Someone
visibility: table
rules_binding:
  stat_block_ref: rules:npc.missing
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD111" in codes(result)


def test_rules_documents_require_pack_citation(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "statblock.yaml",
        """
id: rules:npc.test
schema: dwd.statblock.v1
name: Test
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD602" in codes(result)
    assert "DWD901" not in codes(result)


def test_unknown_rules_schema_is_an_extension(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "extension.yaml",
        """
id: rules:ext.test
schema: dwd.rules_extension.v1
name: Test Extension
""",
    )

    result = lint_paths([tmp_path])

    assert result.error_count == 0
    assert "DWD912" in codes(result)


def test_fixture_actors_resolve_only_within_their_scenario(tmp_path: Path) -> None:
    scenario = """
schema: dwd.system_simulation_scenario.v1
id: sim:test_fixture
title: Fixture Test
focus: [rules]
setup:
  present: ["creature:fixture_only"]
  rules_fixture:
    schema: dwd.simulation_rules_fixture.v1
    actors:
      creature:fixture_only:
        stat_block_inline: { name: Fixture Beast, ac: 10 }
input: { channel: live_table }
expected_pressure_points: [none]
"""
    write_yaml(tmp_path, "scenario.yaml", scenario)
    write_yaml(
        tmp_path,
        "other.yaml",
        """
id: item:leaker
kind: item
schema: dwd.item.v1
name: Leaker
visibility: table
found_by: creature:fixture_only
""",
    )

    result = lint_paths([tmp_path])

    dangling = [item for item in result.diagnostics if item.code == "DWD111"]
    assert len(dangling) == 1
    assert dangling[0].path.name == "other.yaml"


def test_dangling_reference_reports_its_line(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "location.yaml",
        """
id: loc:harbor
kind: location
schema: dwd.location.v1
name: Harbor
parent: region:missing
visibility: table
""",
    )

    result = lint_paths([tmp_path])

    dangling = [item for item in result.diagnostics if item.code == "DWD111"]
    assert dangling and dangling[0].line == 6


def test_malformed_managed_reference_is_an_error(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "location.yaml",
        """
id: loc:harbor
kind: location
schema: dwd.location.v1
name: Harbor
parent: loc:Uppercase.Bad
visibility: table
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD113" in codes(result)


def test_undeclared_fact_predicate_is_an_error(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "predicates.yaml",
        """
schema: dwd.predicate_vocabulary.v1
version: 1
predicates:
  located_in: Subject is located inside object.
""",
    )
    write_yaml(
        tmp_path,
        "facts.yaml",
        """
schema: dwd.fact_collection.v1
source_refs: [source:notes]
facts:
  - id: fact:test
    schema: dwd.fact.v1
    subject: loc:somewhere
    predicate: rules_over
    object: loc:elsewhere
    truth_status: canon
    visibility: table
    confidence: 1
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD205" in codes(result)


def test_relationship_axes_must_stay_in_bounds(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "relationships.yaml",
        """
relationships:
  - id: rel:a->b
    schema: dwd.relationship.v1
    source: npc:a
    target: npc:b
    axes: { trust: 150 }
    visibility: dm_only
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD224" in codes(result)


def test_knowledge_edge_cannot_expose_internal_truth(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "world.yaml",
        """
id: secret:inside
kind: secret
schema: dwd.secret.v1
name: Inside Truth
holders: []
visibility: internal
""",
    )
    write_yaml(
        tmp_path,
        "npc.yaml",
        """
id: npc:someone
kind: npc
schema: dwd.npc.v1
name: Someone
visibility: table
facets:
  knowledge:
    - { holder: "npc:someone", target: "secret:inside", mode: knows }
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD403" in codes(result)


def test_table_visible_object_cannot_reference_internal_truth(tmp_path: Path) -> None:
    write_yaml(
        tmp_path,
        "world.yaml",
        """
id: secret:inside
kind: secret
schema: dwd.secret.v1
name: Inside Truth
holders: []
visibility: internal
""",
    )
    write_yaml(
        tmp_path,
        "item.yaml",
        """
id: item:brochure
kind: item
schema: dwd.item.v1
name: Brochure
visibility: table
related: [secret:inside]
""",
    )

    result = lint_paths([tmp_path])

    assert "DWD405" in codes(result)


def test_json_output_reports_diagnostics(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import json

    write_yaml(
        tmp_path,
        "location.yaml",
        """
id: loc:harbor
kind: location
schema: dwd.location.v1
name: Harbor
parent: region:missing
visibility: table
""",
    )

    assert main(["--format", "json", str(tmp_path)]) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["files_checked"] == 1
    assert payload["errors"] == 1
    assert payload["diagnostics"][0]["code"] == "DWD111"
