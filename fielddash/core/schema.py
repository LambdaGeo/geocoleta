"""Reading Epicollect5 form schemas.

Epicollect export columns are named as ``f"{idx}_{question}"[:20]``,
where ``idx`` counts all form entries (including groups, except readme)
and the question drops anything that is not an ASCII letter, digit, or space.
Because this name changes when questions are inserted or removed, the dashboard
identifies each question by its ``ref`` and resolves the column at runtime.
"""
import html
import re

from fielddash.core.model import Field

SYSTEM_FIELDS = [
    Field(ref="created_at", column="created_at", label="Collection date", type="datetime", system=True),
    Field(ref="created_by", column="created_by", label="Collector", type="category", system=True),
]

# Types that do not become a column in the main export
_NO_COLUMN = {"group", "readme", "branch"}


def _slug(question: str) -> str:
    text = html.unescape(question or "").strip()
    return re.sub(r"[^A-Za-z0-9 _]", "", text).replace(" ", "_")


def export_column(idx: int, question: str) -> str:
    return f"{idx}_{_slug(question)}"[:20]


def clean_label(question: str) -> str:
    text = html.unescape(question or "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip().rstrip(":").strip()


def find_form(schema: dict, form_ref: str | None = None) -> dict:
    """Accepts form JSON (data.form) or project export (data.project.forms)."""
    data = schema.get("data", schema)
    if "form" in data:
        return data["form"]
    forms = data.get("project", data).get("forms", [])
    if not forms:
        raise ValueError("Schema contains no forms")
    if form_ref:
        for form in forms:
            if form["ref"] == form_ref:
                return form
        raise ValueError(f"Form {form_ref!r} not found in project")
    return forms[0]


def parse_form(schema: dict, form_ref: str | None = None) -> list:
    form = find_form(schema, form_ref)
    fields = []
    counter = 0

    def walk(inputs, group=None):
        nonlocal counter
        for item in inputs:
            kind = item.get("type")
            if kind == "readme":
                continue
            counter += 1
            if kind not in _NO_COLUMN:
                fields.append(Field(
                    ref=item["ref"],
                    column=export_column(counter, item.get("question", "")),
                    label=clean_label(item.get("question", "")),
                    type=kind,
                    options=[html.unescape(a["answer"]).strip() for a in item.get("possible_answers") or []],
                    group=group,
                    question=item.get("question", ""),
                ))
            if kind == "group":
                walk(item.get("group") or [], clean_label(item.get("question", "")))

    walk(form.get("inputs", []))
    return [Field(**f.__dict__) for f in SYSTEM_FIELDS] + fields


def _strip_index(column: str) -> str:
    return re.sub(r"^\d+_", "", column)


def reconcile(fields: list, columns) -> tuple:
    """Checks whether each field has a corresponding column in the data.

    When the expected column does not exist (e.g. outdated local schema and
    renumbered questions), attempts to match by question text, ignoring the
    index. Never matches by position. Returns (matched_fields, warnings).
    """
    columns = list(columns)
    if not columns:
        return fields, []
    available = set(columns)
    used = {f.column for f in fields if f.column in available}
    matched, warnings = [], []

    for f in fields:
        if f.column in available:
            matched.append(f)
            continue
        slug = _slug(f.question)
        candidates = [
            c for c in columns
            if c not in used and _strip_index(c) and slug.startswith(_strip_index(c))
            and len(_strip_index(c)) >= min(len(slug), 8)
        ]
        if len(candidates) == 1:
            warnings.append(f"'{f.label}': column {f.column!r} not found, using {candidates[0]!r}")
            f.column = candidates[0]
            used.add(f.column)
            matched.append(f)
        elif not f.system:
            warnings.append(f"'{f.label}': no matching column in data (expected {f.column!r})")

    extra = [c for c in columns if c not in used and c not in ("ec5_uuid", "uploaded_at", "title")
             and not c.startswith("ec5_")]
    if extra:
        warnings.append(f"Columns in data without question in schema: {', '.join(extra)}")
    return matched, warnings
