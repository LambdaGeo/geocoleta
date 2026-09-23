# myframework — dashboard para formulários Epicollect5

Dashboard Streamlit que se monta a partir do **schema do formulário**: cada pergunta é
identificada pelo `ref` do Epicollect (estável), e o tipo dela (`radio`, `checkbox`,
`integer`, `location`, ...) decide o filtro e o gráfico. Mudar, inserir ou reordenar
perguntas no Epicollect não quebra o dashboard.

## Rodar

```bash
pip install -r requirements.txt
streamlit run myframework/app.py                                  # escolhe o projeto na barra lateral
streamlit run myframework/app.py -- --config projetos/residuos.yaml
```

Credenciais ficam no `.env` (na raiz do repositório ou em `myframework/`).

## Novo projeto de campo

1. No `.env`, adicione as credenciais do app do Epicollect (Project → Apps):
   ```
   MEUPROJ_CLIENT_ID=...
   MEUPROJ_CLIENT_SECRET=...
   ```
   Projetos públicos não precisam de credenciais (omita `credenciais` na config).
2. Crie `projetos/meuprojeto.yaml`:
   ```yaml
   titulo: "Meu levantamento"
   fonte:
     tipo: epicollect
     projeto: slug-do-projeto
     credenciais: MEUPROJ
   ```
3. Liste os campos para escolher apelidos, filtros e destaques:
   ```bash
   python myframework/tools/listar_campos.py myframework/projetos/meuprojeto.yaml
   ```
4. Complete a config (todas as chaves são opcionais):
   ```yaml
   campos:            # apelido -> final do ref, coluna ou texto da pergunta
     bairro: "5401ce"
   tipos:             # força um tipo (ex.: texto livre tratado como categoria)
     bairro: category
   ignorar: [created_by, "3401cb"]   # esconde campos (ex.: e-mail do coletor)
   filtros: [created_at, bairro]
   destaques:
     - {campo: destino_lixo, por: bairro, titulo: "Destino do lixo por bairro"}
   secoes:            # padrão: grupos do formulário
     - {titulo: "Perfil", campos: [idade, genero]}
   mapa: {campo: localizacao, popup: [bairro]}
   fuso: America/Fortaleza
   cache_minutos: 5
   ```

Para trabalhar sem internet, use `fonte: {tipo: json, dados: ..., schema: ...}`
(veja `projetos/residuos_offline.yaml`).

## Estrutura

```
app.py            ponto de entrada (config, cache, filtros, navegação)
core/schema.py    schema Epicollect -> list[Field]; regra de nomes das colunas; reconcile
core/normalize.py respostas brutas -> tipos (categorias ordenadas, listas, lat/lon, datas)
core/config.py    leitura do YAML (+ ${VAR} do .env em `fonte`)
sources/          fontes de dados (@source): epicollect (API, paginação), json (arquivos)
ui/               filtros, gráficos e mapa gerados pelo tipo do campo
views/            páginas (@page): Visão geral, Destaques, Perguntas, Dados
tools/            utilitários de linha de comando
tests/            pytest (schema, dados offline e todas as páginas via AppTest)
```

Uma página específica de um projeto é só um módulo em `views/`:

```python
from core.registry import page
from ui.charts import render_field

@page("Reciclagem", order=40, available=lambda ctx: ctx.dataset.find("separa_reciclagem"))
def render(ctx):
    render_field(ctx.dataset, ctx.df, ctx.dataset.field("separa_reciclagem"),
                 by=ctx.dataset.field("bairro"))
```

## Testes

```bash
cd myframework && python -m pytest -q tests
```
