"""Leitura do schema de formulários do Epicollect5.

As colunas do export do Epicollect são nomeadas como ``f"{idx}_{pergunta}"[:20]``,
onde ``idx`` conta todas as entradas do formulário (inclusive grupos, exceto readme)
e a pergunta perde tudo que não for letra ASCII, dígito ou espaço. Como esse nome
muda quando perguntas são inseridas ou removidas, o dashboard identifica cada
pergunta pelo ``ref`` e resolve a coluna em tempo de execução.
"""
import html
import re

from fielddash.core.model import Field

SYSTEM_FIELDS = [
    Field(ref="created_at", column="created_at", label="Data da coleta", type="datetime", system=True),
    Field(ref="created_by", column="created_by", label="Coletor", type="category", system=True),
]

# Tipos que não viram coluna no export principal
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
    """Aceita o JSON do formulário (data.form) ou o export do projeto (data.project.forms)."""
    data = schema.get("data", schema)
    if "form" in data:
        return data["form"]
    forms = data.get("project", data).get("forms", [])
    if not forms:
        raise ValueError("Schema sem formulários")
    if form_ref:
        for form in forms:
            if form["ref"] == form_ref:
                return form
        raise ValueError(f"Formulário {form_ref!r} não encontrado no projeto")
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
    """Confere se cada campo tem coluna nos dados.

    Quando a coluna esperada não existe (ex.: schema local desatualizado e
    perguntas renumeradas), tenta casar pelo texto da pergunta, ignorando o
    índice. Nunca casa por posição. Retorna (campos_ok, avisos).
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
            warnings.append(f"'{f.label}': coluna {f.column!r} não encontrada, usando {candidates[0]!r}")
            f.column = candidates[0]
            used.add(f.column)
            matched.append(f)
        elif not f.system:
            warnings.append(f"'{f.label}': sem coluna correspondente nos dados (esperada {f.column!r})")

    extra = [c for c in columns if c not in used and c not in ("ec5_uuid", "uploaded_at", "title")
             and not c.startswith("ec5_")]
    if extra:
        warnings.append(f"Colunas nos dados sem pergunta no schema: {', '.join(extra)}")
    return matched, warnings
