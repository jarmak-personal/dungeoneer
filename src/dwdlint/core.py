from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode


class Severity(StrEnum):
    ERROR = "error"
    EXTENSION = "extension"
    WARNING = "warning"


@dataclass(frozen=True)
class Diagnostic:
    path: Path
    line: int
    severity: Severity
    code: str
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.severity.upper()} {self.code} {self.message}"

    def as_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "line": self.line,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }


@dataclass
class LintResult:
    files_checked: int
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(item.severity == Severity.ERROR for item in self.diagnostics)

    @property
    def extension_count(self) -> int:
        return sum(item.severity == Severity.EXTENSION for item in self.diagnostics)

    @property
    def warning_count(self) -> int:
        return sum(item.severity == Severity.WARNING for item in self.diagnostics)

    @property
    def ok(self) -> bool:
        return not self.error_count and not self.extension_count

    def summary(self) -> str:
        if not self.diagnostics:
            return f"DWD lint passed: {self.files_checked} files checked."
        return (
            f"DWD lint found {self.error_count} errors, "
            f"{self.extension_count} extensions, and {self.warning_count} warnings "
            f"in {self.files_checked} files."
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "files_checked": self.files_checked,
            "errors": self.error_count,
            "extensions": self.extension_count,
            "warnings": self.warning_count,
            "diagnostics": [item.as_dict() for item in self.diagnostics],
        }


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader, node: MappingNode, deep: bool = False
) -> dict[object, object]:
    loader.flatten_mapping(node)
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


@dataclass
class Document:
    path: Path
    data: Mapping[str, Any]
    object_lines: dict[int, int]
    key_lines: dict[tuple[int, str], int]

    def line(self, value: object, key: str | None = None) -> int:
        if key is not None:
            found = self.key_lines.get((id(value), key))
            if found is not None:
                return found
        return self.object_lines.get(id(value), 1)


@dataclass(frozen=True)
class Record:
    identifier: str
    value: Mapping[str, Any]
    document: Document


ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*:[a-z0-9_][a-z0-9_.-]*(?:->[a-z0-9_.-]+)?$"
)

# A single token shaped like a namespaced ID: used to spot reference candidates
# (and malformed references) without matching prose or URLs that contain colons.
NAMESPACE_SHAPE = re.compile(r"^[a-z][a-z0-9_]*:\S+$")

ENTITY_PREFIXES = {
    "world": "world",
    "calendar": "calendar",
    "region": "region",
    "location": "loc",
    "faction": "faction",
    "npc": "npc",
    "pc": "pc",
    "creature": "creature",
    "item": "item",
    "thread": "thread",
    "clock": "clock",
    "source": "source",
    "secret": "secret",
}

MANAGED_PREFIXES = set(ENTITY_PREFIXES.values()) | {
    "deity",
    "fact",
    "goal",
    "rel",
    "rules",
}

RULES_DOCUMENT_SCHEMAS = {
    "dwd.rules_pack.v1",
    "dwd.statblock.v1",
    "dwd.condition.v1",
    "dwd.dc_guidance.v1",
    "dwd.character_sheet.v1",
    "dwd.rules_template.v1",
    "dwd.rules_procedure.v1",
}
RULES_NAMED_SCHEMAS = {
    "dwd.rules_pack.v1",
    "dwd.statblock.v1",
    "dwd.condition.v1",
    "dwd.rules_template.v1",
    "dwd.rules_procedure.v1",
}

SIMULATION_FIXTURE_SCHEMA = "dwd.simulation_rules_fixture.v1"

VISIBILITY_VALUES = {"table", "dm_only", "internal", "ooc"}
VISIBILITY_PREFIXES = ("player:", "players:", "npc_private:", "faction_private:")
KNOWLEDGE_MODES = {
    "knows",
    "believes",
    "suspects",
    "heard_rumor",
    "misunderstands",
    "forgot",
}
TRUTH_STATUSES = {"canon", "claim", "belief", "rumor", "disputed", "false", "unknown"}
THREAD_STATUSES = {"active", "locked", "resolved", "failed", "dormant"}
CLOCK_STATUSES = {"active", "paused", "complete", "cancelled"}
FORBIDDEN_TABLE_KEYS = {"private_truth", "hidden_significance", "knowledge_limits"}


def _yaml_files(paths: Sequence[Path]) -> tuple[list[Path], list[Diagnostic]]:
    files: set[Path] = set()
    diagnostics: list[Diagnostic] = []
    for raw_path in paths:
        path = raw_path.resolve()
        if not path.exists():
            diagnostics.append(
                Diagnostic(raw_path, 1, Severity.ERROR, "DWD001", "path does not exist")
            )
        elif path.is_dir():
            files.update(path.rglob("*.yaml"))
            files.update(path.rglob("*.yml"))
        elif path.suffix.lower() in {".yaml", ".yml"}:
            files.add(path)
        else:
            diagnostics.append(
                Diagnostic(path, 1, Severity.ERROR, "DWD002", "expected a YAML file or directory")
            )
    return sorted(files), diagnostics


def _map_node_lines(
    node: Node,
    value: object,
    object_lines: dict[int, int],
    key_lines: dict[tuple[int, str], int],
) -> None:
    object_lines[id(value)] = node.start_mark.line + 1
    if isinstance(node, MappingNode) and isinstance(value, Mapping):
        for key_node, value_node in node.value:
            if not isinstance(key_node, ScalarNode):
                continue
            key = key_node.value
            if key not in value:
                continue
            key_lines[(id(value), key)] = key_node.start_mark.line + 1
            _map_node_lines(value_node, value[key], object_lines, key_lines)
    elif isinstance(node, SequenceNode) and isinstance(value, list):
        for child_node, child_value in zip(node.value, value, strict=False):
            _map_node_lines(child_node, child_value, object_lines, key_lines)


def _load_document(path: Path) -> tuple[Document | None, Diagnostic | None]:
    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.load(text, Loader=UniqueKeyLoader)
        node = yaml.compose(text, Loader=yaml.SafeLoader)
    except (OSError, UnicodeError) as exc:
        return None, Diagnostic(path, 1, Severity.ERROR, "DWD003", str(exc))
    except yaml.MarkedYAMLError as exc:
        line = exc.problem_mark.line + 1 if exc.problem_mark else 1
        message = exc.problem or str(exc).splitlines()[0]
        return None, Diagnostic(path, line, Severity.ERROR, "DWD004", f"invalid YAML: {message}")

    if not isinstance(data, Mapping):
        return None, Diagnostic(
            path, 1, Severity.ERROR, "DWD005", "document root must be a mapping"
        )
    if node is None:
        return None, Diagnostic(path, 1, Severity.ERROR, "DWD005", "document is empty")

    object_lines: dict[int, int] = {}
    key_lines: dict[tuple[int, str], int] = {}
    _map_node_lines(node, data, object_lines, key_lines)
    return Document(path, data, object_lines, key_lines), None


def _walk_mappings(value: object) -> Iterator[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_mappings(child)


def _namespace(identifier: str) -> str:
    return identifier.split(":", 1)[0]


def _is_record_definition(value: Mapping[str, Any]) -> bool:
    """Whether a mapping defines a durable record, as opposed to referencing one.

    DWD definitions carry a schema, a name, a visibility, or a recognized entity
    kind alongside their ID (inline goal declarations are id + visibility).
    Mappings whose only ID-bearing role is pointing at another record
    (``source: {kind: condition, id: rules:condition.prone}``) and foreign ID
    fields (``license: {id: CC-BY-4.0}``) are not definitions.
    """
    if not isinstance(value.get("id"), str):
        return False
    return (
        "schema" in value
        or "name" in value
        or "visibility" in value
        or value.get("kind") in ENTITY_PREFIXES
    )


class DwdLinter:
    def __init__(self, documents: Sequence[Document], diagnostics: list[Diagnostic]) -> None:
        self.documents = documents
        self.diagnostics = diagnostics
        self.records: dict[str, Record] = {}
        self.future_facts: set[str] = set()
        self.predicates: set[str] = set()
        self.document_locals: dict[Path, set[str]] = {}

    def add(
        self,
        document: Document,
        value: Mapping[str, Any],
        severity: Severity,
        code: str,
        message: str,
        key: str | None = None,
    ) -> None:
        self.diagnostics.append(
            Diagnostic(document.path, document.line(value, key), severity, code, message)
        )

    def run(self) -> None:
        self._collect_records()
        self._collect_predicates()
        for document in self.documents:
            self._validate_document(document)
        self._validate_references()
        self._validate_location_cycles()
        self._validate_visibility_edges()

    def _collect_records(self) -> None:
        for document in self.documents:
            for value in _walk_mappings(document.data):
                if not _is_record_definition(value):
                    continue
                identifier = value["id"]
                if not ID_PATTERN.fullmatch(identifier):
                    self.add(
                        document,
                        value,
                        Severity.ERROR,
                        "DWD101",
                        f"invalid ID syntax {identifier!r}",
                        "id",
                    )
                    continue
                existing = self.records.get(identifier)
                if existing is not None:
                    self.add(
                        document,
                        value,
                        Severity.ERROR,
                        "DWD102",
                        f"duplicate ID {identifier!r}; first defined in {existing.document.path}",
                        "id",
                    )
                    continue
                self.records[identifier] = Record(identifier, value, document)

        for document in self.documents:
            for value in _walk_mappings(document.data):
                created_fact = value.get("create_fact")
                if isinstance(created_fact, str):
                    self.future_facts.add(created_fact)
                if value.get("schema") == SIMULATION_FIXTURE_SCHEMA:
                    self._collect_fixture_locals(document, value)

    def _collect_fixture_locals(self, document: Document, fixture: Mapping[str, Any]) -> None:
        """Register scenario-local actor IDs declared by a simulation rules fixture.

        Fixture actors are keyed by ID (``creature:choir_zealot_1``) and defined
        inline for that scenario only; they resolve within their own document but
        are not world canon and must not satisfy references elsewhere.
        """
        actors = fixture.get("actors")
        if not isinstance(actors, Mapping):
            return
        locals_ = self.document_locals.setdefault(document.path, set())
        locals_.update(
            key for key in actors if isinstance(key, str) and ID_PATTERN.fullmatch(key)
        )

    def _collect_predicates(self) -> None:
        for document in self.documents:
            if document.data.get("schema") != "dwd.predicate_vocabulary.v1":
                continue
            predicates = document.data.get("predicates")
            if isinstance(predicates, Mapping):
                self.predicates.update(str(name) for name in predicates)

    def _validate_document(self, document: Document) -> None:
        root = document.data
        schema = root.get("schema")
        root_id = root.get("id")
        if isinstance(root_id, str) and isinstance(root.get("kind"), str):
            self._validate_entity(document, root)
        elif isinstance(root_id, str) and _namespace(root_id) == "rules":
            self._validate_rules_document(document, root)
        elif schema == "dwd.fact_collection.v1":
            self._validate_fact_collection(document, root)
        elif schema == "dwd.predicate_vocabulary.v1":
            self._validate_predicate_vocabulary(document, root)
        elif "relationships" in root:
            self._validate_relationship_collection(document, root)
        elif schema == "dwd.system_simulation_scenario.v1":
            self._validate_simulation_scenario(document, root)
        else:
            self.add(
                document,
                root,
                Severity.EXTENSION,
                "DWD901",
                "unrecognized document shape; this may be a valid DWD extension",
                "schema" if "schema" in root else None,
            )

        for value in _walk_mappings(root):
            self._validate_visibility_value(document, value)
            if "knowledge" in value:
                self._validate_knowledge(document, value.get("knowledge"))

    def _validate_entity(self, document: Document, entity: Mapping[str, Any]) -> None:
        kind = entity.get("kind")
        identifier = entity.get("id")
        if kind not in ENTITY_PREFIXES:
            self.add(
                document,
                entity,
                Severity.EXTENSION,
                "DWD902",
                f"unrecognized entity kind {kind!r}; add linter support if intentional",
                "kind",
            )
            return

        expected_prefix = ENTITY_PREFIXES[str(kind)]
        if isinstance(identifier, str) and _namespace(identifier) != expected_prefix:
            self.add(
                document,
                entity,
                Severity.ERROR,
                "DWD103",
                f"kind {kind!r} requires an {expected_prefix}: ID",
                "id",
            )
        expected_schema = f"dwd.{kind}.v1"
        if entity.get("schema") != expected_schema:
            self.add(
                document,
                entity,
                Severity.EXTENSION,
                "DWD903",
                f"expected schema {expected_schema!r}, found {entity.get('schema')!r}",
                "schema",
            )
        for key in ("name", "visibility"):
            if key not in entity:
                self.add(
                    document,
                    entity,
                    Severity.ERROR,
                    "DWD104",
                    f"entity is missing required field {key!r}",
                )

        if kind == "clock":
            self._validate_clock(document, entity)
        elif kind == "thread":
            self._validate_thread(document, entity)
        elif kind == "secret":
            self._validate_secret(document, entity)

    def _validate_rules_document(self, document: Document, root: Mapping[str, Any]) -> None:
        schema = root.get("schema")
        if schema not in RULES_DOCUMENT_SCHEMAS:
            self.add(
                document,
                root,
                Severity.EXTENSION,
                "DWD912",
                f"unrecognized rules document schema {schema!r}",
                "schema",
            )
            return
        if schema in RULES_NAMED_SCHEMAS and not isinstance(root.get("name"), str):
            self.add(
                document,
                root,
                Severity.ERROR,
                "DWD601",
                "rules document is missing required field 'name'",
            )
        if schema != "dwd.rules_pack.v1" and not isinstance(root.get("pack"), str):
            self.add(
                document,
                root,
                Severity.ERROR,
                "DWD602",
                "rules document must cite its pack",
            )

    def _validate_fact_collection(self, document: Document, root: Mapping[str, Any]) -> None:
        facts = root.get("facts")
        if not isinstance(root.get("source_refs"), list) or not root["source_refs"]:
            self.add(
                document,
                root,
                Severity.ERROR,
                "DWD201",
                "fact collection requires non-empty source_refs",
                "source_refs",
            )
        if not isinstance(facts, list):
            self.add(document, root, Severity.ERROR, "DWD202", "facts must be a list", "facts")
            return
        for fact in facts:
            if not isinstance(fact, Mapping):
                self.add(
                    document, root, Severity.ERROR, "DWD203", "each fact must be a mapping", "facts"
                )
                continue
            required = {
                "id",
                "schema",
                "subject",
                "predicate",
                "object",
                "truth_status",
                "visibility",
                "confidence",
            }
            missing = sorted(required - fact.keys())
            if missing:
                self.add(
                    document,
                    fact,
                    Severity.ERROR,
                    "DWD204",
                    f"fact is missing required fields: {', '.join(missing)}",
                )
            if fact.get("schema") != "dwd.fact.v1":
                self.add(
                    document,
                    fact,
                    Severity.EXTENSION,
                    "DWD904",
                    f"unrecognized fact schema {fact.get('schema')!r}",
                    "schema",
                )
            predicate = fact.get("predicate")
            if isinstance(predicate, str) and predicate not in self.predicates:
                self.add(
                    document,
                    fact,
                    Severity.ERROR,
                    "DWD205",
                    f"predicate {predicate!r} is not declared in the vocabulary",
                    "predicate",
                )
            truth_status = fact.get("truth_status")
            if truth_status not in TRUTH_STATUSES:
                self.add(
                    document,
                    fact,
                    Severity.EXTENSION,
                    "DWD905",
                    f"unrecognized truth status {truth_status!r}",
                    "truth_status",
                )
            confidence = fact.get("confidence")
            if (
                not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not 0 <= confidence <= 1
            ):
                self.add(
                    document,
                    fact,
                    Severity.ERROR,
                    "DWD206",
                    "confidence must be a number from 0 through 1",
                    "confidence",
                )

    def _validate_predicate_vocabulary(
        self, document: Document, root: Mapping[str, Any]
    ) -> None:
        version = root.get("version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            self.add(
                document,
                root,
                Severity.ERROR,
                "DWD211",
                "predicate vocabulary version must be a positive integer",
                "version",
            )
        predicates = root.get("predicates")
        if not isinstance(predicates, Mapping) or not predicates:
            self.add(
                document,
                root,
                Severity.ERROR,
                "DWD212",
                "predicate vocabulary must contain predicates",
                "predicates",
            )
        elif any(
            not isinstance(description, str) or not description.strip()
            for description in predicates.values()
        ):
            self.add(
                document,
                root,
                Severity.ERROR,
                "DWD213",
                "every predicate requires a non-empty description",
                "predicates",
            )

    def _validate_relationship_collection(
        self, document: Document, root: Mapping[str, Any]
    ) -> None:
        relationships = root.get("relationships")
        if not isinstance(relationships, list):
            self.add(
                document,
                root,
                Severity.ERROR,
                "DWD221",
                "relationships must be a list",
                "relationships",
            )
            return
        for relationship in relationships:
            if not isinstance(relationship, Mapping):
                self.add(
                    document,
                    root,
                    Severity.ERROR,
                    "DWD222",
                    "each relationship must be a mapping",
                    "relationships",
                )
                continue
            required = {"id", "schema", "source", "target", "axes", "visibility"}
            missing = sorted(required - relationship.keys())
            if missing:
                self.add(
                    document,
                    relationship,
                    Severity.ERROR,
                    "DWD223",
                    f"relationship is missing required fields: {', '.join(missing)}",
                )
            if relationship.get("schema") != "dwd.relationship.v1":
                self.add(
                    document,
                    relationship,
                    Severity.EXTENSION,
                    "DWD906",
                    f"unrecognized relationship schema {relationship.get('schema')!r}",
                    "schema",
                )
            axes = relationship.get("axes")
            if not isinstance(axes, Mapping) or any(
                not isinstance(score, (int, float))
                or isinstance(score, bool)
                or not -100 <= score <= 100
                for score in axes.values()
            ):
                self.add(
                    document,
                    relationship,
                    Severity.ERROR,
                    "DWD224",
                    "relationship axes must be numeric values from -100 through 100",
                    "axes",
                )

    def _validate_clock(self, document: Document, clock: Mapping[str, Any]) -> None:
        if clock.get("status") not in CLOCK_STATUSES:
            self.add(
                document,
                clock,
                Severity.EXTENSION,
                "DWD907",
                f"unrecognized clock status {clock.get('status')!r}",
                "status",
            )
        segments = clock.get("segments")
        current = segments.get("current") if isinstance(segments, Mapping) else None
        maximum = segments.get("max") if isinstance(segments, Mapping) else None
        valid_segments = (
            isinstance(current, int)
            and not isinstance(current, bool)
            and isinstance(maximum, int)
            and not isinstance(maximum, bool)
            and maximum >= 1
            and 0 <= current <= maximum
        )
        if not valid_segments:
            self.add(
                document,
                clock,
                Severity.ERROR,
                "DWD301",
                "clock segments require integers satisfying 0 <= current <= max and max >= 1",
                "segments",
            )
        triggers = clock.get("advance_triggers")
        if not isinstance(triggers, list) or not triggers:
            self.add(
                document,
                clock,
                Severity.ERROR,
                "DWD302",
                "clock requires at least one advance trigger",
                "advance_triggers",
            )
        else:
            for trigger in triggers:
                if (
                    not isinstance(trigger, Mapping)
                    or not isinstance(trigger.get("trigger"), str)
                    or not isinstance(trigger.get("amount"), int)
                ):
                    self.add(
                        document,
                        trigger if isinstance(trigger, Mapping) else clock,
                        Severity.ERROR,
                        "DWD303",
                        "advance trigger requires a string trigger and integer amount",
                    )
        outcomes = clock.get("outcomes")
        complete = outcomes.get("complete") if isinstance(outcomes, Mapping) else None
        if not isinstance(complete, list) or not complete:
            self.add(
                document,
                clock,
                Severity.ERROR,
                "DWD304",
                "clock requires at least one typed completion outcome",
                "outcomes",
            )
            return
        for outcome in complete:
            if not isinstance(outcome, Mapping) or len(outcome) != 1:
                self.add(
                    document,
                    outcome if isinstance(outcome, Mapping) else clock,
                    Severity.ERROR,
                    "DWD305",
                    "clock outcome must be a one-key typed action",
                )
                continue
            action, target = next(iter(outcome.items()))
            if action not in {"create_fact", "unlock_thread"}:
                self.add(
                    document,
                    outcome,
                    Severity.EXTENSION,
                    "DWD908",
                    f"unrecognized clock outcome action {action!r}",
                    str(action),
                )
            elif not isinstance(target, str) or not ID_PATTERN.fullmatch(target):
                self.add(
                    document,
                    outcome,
                    Severity.ERROR,
                    "DWD306",
                    f"clock outcome {action!r} requires an ID target",
                    str(action),
                )
            elif action == "create_fact" and not target.startswith("fact:"):
                self.add(
                    document,
                    outcome,
                    Severity.ERROR,
                    "DWD307",
                    "create_fact target must use fact:",
                    str(action),
                )
            elif action == "unlock_thread" and not target.startswith("thread:"):
                self.add(
                    document,
                    outcome,
                    Severity.ERROR,
                    "DWD308",
                    "unlock_thread target must use thread:",
                    str(action),
                )

    def _validate_thread(self, document: Document, thread: Mapping[str, Any]) -> None:
        if thread.get("status") not in THREAD_STATUSES:
            self.add(
                document,
                thread,
                Severity.EXTENSION,
                "DWD909",
                f"unrecognized thread status {thread.get('status')!r}",
                "status",
            )
        for key in ("summary", "stakes", "participants", "resolution_conditions"):
            if key not in thread:
                self.add(
                    document,
                    thread,
                    Severity.ERROR,
                    "DWD311",
                    f"thread is missing required field {key!r}",
                )
        conditions = thread.get("resolution_conditions")
        if not isinstance(conditions, list) or not conditions:
            self.add(
                document,
                thread,
                Severity.ERROR,
                "DWD312",
                "resolution_conditions must be a non-empty list",
                "resolution_conditions",
            )
        elif len(conditions) == 1:
            self.add(
                document,
                thread,
                Severity.WARNING,
                "DWD313",
                "a single resolution condition may prescribe an outcome; review player agency",
                "resolution_conditions",
            )

    def _validate_secret(self, document: Document, secret: Mapping[str, Any]) -> None:
        holders = secret.get("holders")
        if not isinstance(holders, list):
            self.add(
                document,
                secret,
                Severity.ERROR,
                "DWD321",
                "secret holders must be a list",
                "holders",
            )
        if secret.get("visibility") == "internal" and holders:
            self.add(
                document,
                secret,
                Severity.ERROR,
                "DWD322",
                "internal truth cannot have in-fiction holders",
                "holders",
            )

    def _validate_knowledge(self, document: Document, knowledge: object) -> None:
        if not isinstance(knowledge, list):
            self.add(document, document.data, Severity.ERROR, "DWD331", "knowledge must be a list")
            return
        for edge in knowledge:
            if not isinstance(edge, Mapping):
                self.add(
                    document,
                    document.data,
                    Severity.ERROR,
                    "DWD332",
                    "knowledge edge must be a mapping",
                )
                continue
            missing = {"holder", "target", "mode"} - edge.keys()
            if missing:
                self.add(
                    document,
                    edge,
                    Severity.ERROR,
                    "DWD333",
                    f"knowledge edge is missing: {', '.join(sorted(missing))}",
                )
            if edge.get("mode") not in KNOWLEDGE_MODES:
                self.add(
                    document,
                    edge,
                    Severity.EXTENSION,
                    "DWD910",
                    f"unrecognized knowledge mode {edge.get('mode')!r}",
                    "mode",
                )

    def _validate_visibility_value(self, document: Document, value: Mapping[str, Any]) -> None:
        if "visibility" not in value:
            return
        visibility = value.get("visibility")
        if not isinstance(visibility, str):
            self.add(
                document,
                value,
                Severity.ERROR,
                "DWD401",
                "visibility must be a string",
                "visibility",
            )
            return
        if visibility in VISIBILITY_VALUES:
            return
        prefix = next((item for item in VISIBILITY_PREFIXES if visibility.startswith(item)), None)
        if prefix is None or len(visibility) == len(prefix):
            self.add(
                document,
                value,
                Severity.EXTENSION,
                "DWD911",
                f"unrecognized visibility {visibility!r}",
                "visibility",
            )
            return
        if prefix in {"npc_private:", "faction_private:"}:
            expected = "npc:" if prefix == "npc_private:" else "faction:"
            holder = visibility[len(prefix) :]
            if not holder.startswith(expected) or holder not in self.records:
                self.add(
                    document,
                    value,
                    Severity.ERROR,
                    "DWD402",
                    f"visibility recipient {holder!r} is not a defined {expected[:-1]}",
                    "visibility",
                )

    def _validate_simulation_scenario(
        self, document: Document, scenario: Mapping[str, Any]
    ) -> None:
        required = {"id", "title", "focus", "setup", "input", "expected_pressure_points"}
        missing = sorted(required - scenario.keys())
        if missing:
            self.add(
                document,
                scenario,
                Severity.ERROR,
                "DWD501",
                f"simulation scenario is missing: {', '.join(missing)}",
            )

    def _iter_references(self, value: object) -> Iterator[str]:
        if isinstance(value, Mapping):
            skip_id = _is_record_definition(value)
            for key, child in value.items():
                if key in {"schema", "visibility", "create_fact"}:
                    continue
                if key == "id" and skip_id:
                    continue
                yield from self._iter_references(child)
        elif isinstance(value, list):
            for child in value:
                yield from self._iter_references(child)
        elif isinstance(value, str) and NAMESPACE_SHAPE.fullmatch(value):
            yield value

    def _validate_references(self) -> None:
        known = self.records.keys() | self.future_facts
        for document in self.documents:
            resolvable = known | self.document_locals.get(document.path, set())
            for reference in self._iter_references(document.data):
                if _namespace(reference) not in MANAGED_PREFIXES:
                    continue
                if not ID_PATTERN.fullmatch(reference):
                    self.diagnostics.append(
                        Diagnostic(
                            document.path,
                            document.line(reference),
                            Severity.ERROR,
                            "DWD113",
                            f"malformed reference syntax {reference!r}",
                        )
                    )
                elif reference not in resolvable:
                    self.diagnostics.append(
                        Diagnostic(
                            document.path,
                            document.line(reference),
                            Severity.ERROR,
                            "DWD111",
                            f"dangling reference {reference!r}",
                        )
                    )

    def _validate_location_cycles(self) -> None:
        parents: dict[str, str] = {}
        for identifier, record in self.records.items():
            if not identifier.startswith("loc:"):
                continue
            parent = record.value.get("parent")
            if isinstance(parent, str) and parent.startswith("loc:"):
                parents[identifier] = parent

        checked: set[str] = set()
        for start in parents:
            if start in checked:
                continue
            path: list[str] = []
            positions: dict[str, int] = {}
            current = start
            while current in parents and current not in checked:
                if current in positions:
                    cycle = path[positions[current] :] + [current]
                    record = self.records[current]
                    self.add(
                        record.document,
                        record.value,
                        Severity.ERROR,
                        "DWD112",
                        f"circular location containment: {' -> '.join(cycle)}",
                        "parent",
                    )
                    break
                positions[current] = len(path)
                path.append(current)
                current = parents[current]
            checked.update(path)

    def _validate_visibility_edges(self) -> None:
        for document in self.documents:
            self._walk_visibility(document, document.data, None)
            for value in _walk_mappings(document.data):
                knowledge = value.get("knowledge")
                if not isinstance(knowledge, list):
                    continue
                for edge in knowledge:
                    if not isinstance(edge, Mapping):
                        continue
                    target = edge.get("target")
                    record = self.records.get(target) if isinstance(target, str) else None
                    if record is not None and record.value.get("visibility") == "internal":
                        self.add(
                            document,
                            edge,
                            Severity.ERROR,
                            "DWD403",
                            f"knowledge edge exposes internal truth {target!r} to an actor",
                            "target",
                        )

    def _walk_visibility(
        self, document: Document, value: object, inherited: str | None
    ) -> None:
        if isinstance(value, Mapping):
            visibility = value.get("visibility", inherited)
            if visibility == "table":
                forbidden = FORBIDDEN_TABLE_KEYS & value.keys()
                for key in sorted(forbidden):
                    self.add(
                        document,
                        value,
                        Severity.ERROR,
                        "DWD404",
                        f"table-visible object contains private field {key!r}",
                        key,
                    )
                for reference in self._iter_references(value):
                    record = self.records.get(reference)
                    if record is not None and record.value.get("visibility") == "internal":
                        self.add(
                            document,
                            value,
                            Severity.ERROR,
                            "DWD405",
                            f"table-visible object references internal truth {reference!r}",
                        )
            passed_down = visibility if isinstance(visibility, str) else inherited
            for child in value.values():
                self._walk_visibility(document, child, passed_down)
        elif isinstance(value, list):
            for child in value:
                self._walk_visibility(document, child, inherited)


def lint_paths(paths: Sequence[Path | str]) -> LintResult:
    normalized = [Path(path) for path in paths]
    files, diagnostics = _yaml_files(normalized)
    if not files and not diagnostics:
        target = normalized[0] if normalized else Path("worlds")
        diagnostics.append(
            Diagnostic(target, 1, Severity.ERROR, "DWD006", "no YAML files found")
        )
    documents: list[Document] = []
    for path in files:
        document, diagnostic = _load_document(path)
        if diagnostic is not None:
            diagnostics.append(diagnostic)
        elif document is not None:
            documents.append(document)

    linter = DwdLinter(documents, diagnostics)
    linter.run()
    diagnostics.sort(key=lambda item: (str(item.path), item.line, item.code))
    return LintResult(files_checked=len(files), diagnostics=diagnostics)
