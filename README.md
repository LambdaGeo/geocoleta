# geocoleta

Dashboards para dados de **coleta de campo** (Epicollect5), montados a partir do
**schema do formulário**. Cada pergunta é identificada pelo `ref` do Epicollect, que é
estável, e o tipo dela (`radio`, `checkbox`, `integer`, `location`, ...) decide o filtro,
o gráfico e o mapa. Mudar, inserir ou reordenar perguntas no formulário não quebra o
dashboard, e um novo trabalho de campo precisa só de um arquivo YAML.

Páginas prontas: **Visão geral** (indicadores, mapa, coletas no tempo, coletores),
**Destaques** (gráficos escolhidos na config), **Perguntas** (todas as perguntas, com
busca e cruzamento com outra pergunta) e **Dados** (tabela, CSV e Excel).

## Instalação

```bash
pip install git+https://github.com/LambdaGeo/geocoleta
# ou, para desenvolver:
git clone https://github.com/LambdaGeo/geocoleta && cd geocoleta
pip install -e ".[dev]"
```

## Experimente

```bash
geocoleta run exemplos/residuos/projeto.yaml
```

O exemplo usa dados anonimizados de uma pesquisa domiciliar sobre resíduos sólidos
(Itaqui-Bacanga, São Luís – MA) e mostra uma página própria do projeto (`Reciclagem`).

## Novo projeto de campo

1. Crie uma pasta para o projeto com um `.env` contendo as credenciais do app do
   Epicollect (criado na área de administração do projeto, em *Apps*):
   ```
   MEUPROJ_CLIENT_ID=...
   MEUPROJ_CLIENT_SECRET=...
   ```
   Projetos públicos não precisam de credenciais: omita `credenciais` na config.
2. Crie `meuprojeto.yaml`:
   ```yaml
   titulo: "Meu levantamento"
   fonte:
     tipo: epicollect
     projeto: slug-do-projeto      # ou ${VARIAVEL} do .env
     credenciais: MEUPROJ
   ```
3. Liste os campos para escolher apelidos, filtros e destaques:
   ```bash
   geocoleta campos meuprojeto.yaml
   ```
4. Complete a config (todas as chaves abaixo são opcionais) e rode `geocoleta run meuprojeto.yaml`:
   ```yaml
   subtitulo: "Equipe, instituição..."
   campos:            # apelido -> final do ref, coluna ou texto da pergunta
     bairro: "5401ce"
     destino_lixo: "48c35e"
   tipos:             # força um tipo (ex.: texto livre tratado como categoria)
     bairro: category
   ignorar: [created_by, "3401cb"]   # esconde campos (ex.: e-mail do coletor)
   filtros: [created_at, bairro]
   destaques:
     - {campo: destino_lixo, por: bairro, titulo: "Destino do lixo por bairro"}
   secoes:            # abas da página Perguntas (padrão: grupos do formulário)
     - {titulo: "Perfil", campos: [idade, genero]}
   mapa: {campo: localizacao, popup: [bairro]}
   extensoes: [paginas]              # .py ou pastas com páginas próprias
   fuso: America/Fortaleza
   cache_minutos: 5
   ```

`geocoleta run pasta/` abre todos os `.yaml` da pasta, com um seletor de projeto.
Para trabalhar sem internet, use `fonte: {tipo: json, dados: ..., schema: ...}`
(como em `exemplos/residuos/projeto.yaml`).

## Páginas próprias

Uma página específica do projeto é um arquivo `.py` listado em `extensoes`:

```python
from geocoleta.core.registry import page
from geocoleta.ui.charts import render_field


@page("Reciclagem", order=40)
def render(ctx):
    ds = ctx.dataset
    render_field(ds, ctx.df, ds.field("separa_reciclagem"), by=ds.field("bairro"))
```

`ctx.df` já vem com os filtros da barra lateral aplicados, e `ds.field("apelido")` devolve
o campo (coluna, tipo, opções) sem depender do nome da coluna no export. Novas fontes
de dados (ex.: KoboToolbox, CSV) seguem a mesma ideia com `@source("tipo")`.

## Estrutura

```
geocoleta/
  cli.py            comandos `geocoleta run` e `geocoleta campos`
  app.py            aplicação Streamlit (config, cache, filtros, navegação)
  core/schema.py    schema Epicollect -> list[Field]; regra de nomes das colunas; reconcile
  core/normalize.py respostas brutas -> tipos (categorias ordenadas, listas, lat/lon, datas)
  core/config.py    leitura do YAML (+ ${VAR} do .env em `fonte`)
  sources/          fontes de dados (@source): epicollect (API, paginação), json (arquivos)
  ui/               filtros, gráficos e mapa gerados pelo tipo do campo
  views/            páginas (@page): Visão geral, Destaques, Perguntas, Dados
exemplos/           projetos de exemplo com dados anonimizados
tests/              pytest (schema, renumeração de perguntas, todas as páginas via AppTest)
docs/PLANO.md       plano de desenvolvimento (histórico)
```

## Testes

```bash
python -m pytest -q
```
