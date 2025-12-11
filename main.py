import streamlit as st
import importlib
import pkgutil

from core.registry import PAGE_REGISTRY, DATASOURCE_REGISTRY
import pages
import datasources

# Carrega automaticamente páginas
for module in pkgutil.iter_modules(pages.__path__):
    importlib.import_module(f"pages.{module.name}")

# Carrega automaticamente fontes de dados
for module in pkgutil.iter_modules(datasources.__path__):
    importlib.import_module(f"datasources.{module.name}")

def main():
    st.sidebar.title("Navegação")

    # Escolha da página
    page = st.sidebar.radio("Páginas", list(PAGE_REGISTRY.keys()))

    # Escolha da fonte de dados
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Fonte de Dados")
    fonte = st.sidebar.selectbox("Escolha", list(DATASOURCE_REGISTRY.keys()))

    # Carregar dados da fonte selecionada
    data = None
    try:
        data = DATASOURCE_REGISTRY[fonte].load()
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar dados: {e}")

    # Executar página com os dados
    PAGE_REGISTRY[page](data)

if __name__ == "__main__":
    main()
