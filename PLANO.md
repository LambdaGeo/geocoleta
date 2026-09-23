# Plano de execução — myframework

Objetivo: dashboard genérico para formulários Epicollect5 que **não quebra quando as perguntas mudam** e pode ser reaproveitado em outros trabalhos de campo trocando só um arquivo de configuração.

Princípio: o dashboard é guiado pelo **schema do formulário** (tipo da pergunta, opções, grupo), não por adivinhação de dtype do pandas. Perguntas são identificadas pelo `ref` (estável), nunca pela posição.

Cada fase é independente e termina com algo funcionando. Marque `[x]` ao concluir.

---

## Fase 0 — Limpeza (30 min)

- [ ] Consolidar: decidir que `myframework/` é a versão oficial; mover `project/`, `projeto/`, `projeto.zip` para fora do repo (ou apagar após conferir que nada ali falta).
- [ ] Garantir `token.json` e `.env` no `.gitignore`.
- [ ] Remover caminhos absolutos (`/home/sergio/dev/...`) de `datasources/dados_json.py` e `datasources/epicollect.py`; usar caminhos relativos à raiz do projeto (`Path(__file__).resolve().parents[N]`).
- [ ] `main.py`: parar de importar `api.py` (ele faz requisições HTTP na importação).

**Pronto quando:** `streamlit run myframework/main.py` abre com a fonte "Dados Estáticos" sem acessar a rede.

---

## Fase 1 — Modelo de schema (passo mais importante)

Arquivos novos: `core/schema.py`, `core/model.py`, `tests/test_schema.py`.

- [ ] `core/model.py`:
  ```python
  @dataclass
  class Field:
      ref: str
      column: str          # nome da coluna no export, ex. "4_Idade"
      label: str           # texto da pergunta (html unescape)
      type: str            # radio | checkbox | dropdown | integer | decimal | date | time | location | text | textarea | ...
      options: list[str]   # possible_answers[].answer, na ordem do form
      group: str | None    # nome do grupo pai, se houver
      alias: str | None = None  # apelido definido na config (Fase 4)

  @dataclass
  class Dataset:
      df: pd.DataFrame
      fields: list[Field]
      def field(self, key) -> Field   # busca por alias, ref ou label
  ```
- [ ] `core/schema.py` → `parse_form(schema_json) -> list[Field]`:
  - aceitar os dois formatos: `data.form.inputs` (arquivo do form) e `data.project.forms[i].inputs` (export do projeto via API);
  - percorrer recursivamente `group` **e** `branch`;
  - ignorar `readme`; `group` não vira coluna, mas passa o nome para os filhos;
  - gerar `column` no padrão do Epicollect: `f"{idx}_{slug}"`, onde idx conta as perguntas na ordem do export e `slug` = pergunta sem acentos/pontuação, espaços → `_`, cortado em 20 chars. **Validar a regra contra `dados.json`** (ex.: `4_Idade`, `12_Ocupao_principal`, `13_Ocupao_principal_`). Atenção: parece que acentos são *removidos* (não transliterados): "Gênero" → "Gnero".
- [ ] `reconcile(fields, df_columns)`: compara colunas esperadas × reais e retorna `(ok, faltando, sobrando)`. Se houver divergência, tentar casar por label como fallback e **mostrar aviso** no dashboard (nunca renomear por posição).
- [ ] `tests/test_schema.py` com `pesquisaresiduos__diagnostico__form.json` + `dados.json`: todas as colunas de pergunta do `dados.json` precisam casar com um `Field`.
- [ ] Substituir `extrair_questoes` e o `df.columns = colunas` em `datasources/dados_json.py` por `parse_form` + `reconcile`.

**Pronto quando:** `pytest` passa e `dados_json` devolve um `Dataset` com colunas corretas.

---

## Fase 2 — Normalização dos dados

Em `core/model.py` (ou `core/normalize.py`), função `normalize(df, fields) -> df`:

- [ ] `""` → `NaN` em todas as colunas.
- [ ] `location` (dict) → colunas numéricas `<col>__lat`, `<col>__lon` (+ accuracy opcional).
- [ ] `integer`/`decimal` → `pd.to_numeric(errors="coerce")`.
- [ ] `date`, `created_at`, `uploaded_at` → `pd.to_datetime`.
- [ ] `radio`/`dropdown` → `pd.Categorical(categories=field.options, ordered=True)` (mantém a ordem do form nos gráficos).
- [ ] `checkbox` → manter como lista (usar `explode` na hora de contar).
- [ ] `html.unescape` nos labels.

**Pronto quando:** `df.dtypes` bate com os tipos do schema; nenhuma função da UI precisa tratar dict/lista/string vazia.

---

## Fase 3 — Fonte Epicollect robusta

Arquivos: `sources/base.py`, `sources/epicollect.py` (substituem `datasources/epicollect.py`, `api.py`, `epicollect_auth.py`).

- [ ] `DataSource.load() -> Dataset` (dados **e** schema).
- [ ] Registry: `@datasource` registra a **classe**; instanciar só ao usar.
- [ ] Auth: reaproveitar `epicollect_auth.py`, mas sem `initialize_tokens()` global; token em cache (`st.cache_resource` ou arquivo em pasta ignorada).
- [ ] Schema via API: `GET https://five.epicollect.net/api/export/project/{slug}` → `parse_form` (manter fallback para arquivo local).
- [ ] Entradas com **paginação**: `.../api/export/entries/{slug}?form_ref=...&per_page=1000&page=N`, seguir `links.next` / `meta.last_page` até o fim (evita o erro `ec5_335`).
- [ ] `@st.cache_data(ttl=300)` no carregamento + botão "Atualizar dados" que limpa o cache.
- [ ] Mensagens de erro claras (credencial ausente, 401, limite, rede).

**Pronto quando:** o formulário de resíduos carrega pela API, com cache, e editar/reordenar uma pergunta no Epicollect não quebra o carregamento (no máximo gera aviso da Fase 1).

---

## Fase 4 — Configuração por projeto (YAML)

Arquivos: `core/config.py`, `projetos/residuos.yaml`.

- [ ] Formato:
  ```yaml
  titulo: "Diagnóstico de Resíduos – Itaqui-Bacanga"
  fonte:
    tipo: epicollect            # ou json_file
    projeto: pesquisaresiduos
    form_ref: ${FORM_RESIDUOS_REF}
    credenciais: RESIDUOS       # RESIDUOS_CLIENT_ID / RESIDUOS_CLIENT_SECRET
  apelidos:                     # alias -> ref (ou label)
    idade: "...83aec3"
    bairro: "...5401ce"
  ignorar: [consentimento, cep]
  filtros: [bairro, idade]
  destaques:
    - {campo: destino_lixo, grafico: barras, por: bairro}
  mapa: {campo: localizacao, tipo: heatmap}
  ```
- [ ] `load_config(path)`: YAML + expansão de `${VAR}` do `.env`; validar que aliases existem no schema.
- [ ] Script utilitário `python -m myframework.tools.listar_campos <config>`: imprime `ref | coluna | tipo | label` para facilitar escrever os apelidos.
- [ ] `app.py`: `streamlit run app.py -- --config projetos/residuos.yaml` (ou variável `DASH_CONFIG`).

**Pronto quando:** trocar de projeto = trocar o YAML + `.env`, sem editar Python.

---

## Fase 5 — UI gerada pelo tipo da pergunta

Arquivos: `ui/filters.py`, `ui/charts.py`, `ui/maps.py` (substituem `core/filters.py`, `core/charts_auto.py`, `core/maps.py`, `core/df_profile.py`).

| Tipo | Filtro | Gráfico |
|---|---|---|
| radio / dropdown | multiselect (ordem do form) | barras (contagem / %) |
| checkbox | multiselect + `explode` | barras de frequência |
| integer / decimal | slider | histograma |
| date / created_at | intervalo de datas | série temporal (coletas por dia) |
| location | — | mapa (heatmap / pontos) |
| text / textarea | busca textual | tabela |

- [ ] `render_filters(dataset, campos)` e `apply_filters` baseados em `Field.type` (não em `isinstance` do valor).
- [ ] `render_chart(dataset, field, por=None)`: um gráfico por campo; `por` = cruzamento com outro campo categórico.
- [ ] Mapa: usar colunas `__lat/__lon` da Fase 2; centralizar na média; ignorar NaN.

Páginas (`pages/`):
- [ ] **Visão geral**: KPIs (total de entrevistas, última coleta, coletores) + coletas por dia + mapa.
- [ ] **Por seção**: um expander por `group` do form, com gráfico de cada pergunta automaticamente.
- [ ] **Destaques**: gráficos definidos em `destaques` no YAML.
- [ ] **Dados**: tabela filtrada + download CSV/Excel.

**Pronto quando:** um formulário Epicollect diferente (ex.: o de comércio) gera um dashboard útil só com um YAML novo.

---

## Fase 6 — Migração e entrega

- [ ] Portar gráficos específicos de `pags/` (graficos, comparacao, relatorio) como páginas `@page` curadas usando `dataset.field("alias")` em vez de nomes de coluna fixos.
- [ ] README do framework: como criar um projeto novo (YAML + `.env` + `listar_campos`).
- [ ] Trocar o `dashboard.py` da raiz para usar o framework; remover `api.py`/`epicollect_auth.py` duplicados.

---

## Riscos / pontos a verificar

- Regra exata de geração dos nomes de coluna do export (Fase 1): confirmar com `dados.json`; se ficar frágil, usar *mapping* personalizado no Epicollect.
- Perguntas dentro de `branch` saem em outro endpoint (`branch_ref`) — tratar depois, se o form usar.
- Formulários hierárquicos (`hierarchy`, múltiplos forms): começar só com o primeiro form.
- Dados sensíveis (e-mail do coletor em `created_by`): decidir se aparecem no dashboard público.
