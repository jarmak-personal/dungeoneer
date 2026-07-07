from __future__ import annotations

from pathlib import Path

from dwdlint import Severity, lint_paths
from dwdlint.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_yaml(root: Path, name: str, content: str) -> Path:
    path = root / name
    path.write_text(content, encoding="utf-8")
    return path


def codes(result) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def test_aurevost_pack_is_clean() -> None:
    result = lint_paths([REPO_ROOT / "worlds" / "aurevost"])

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
