PAGE_REGISTRY = {}
SOURCE_REGISTRY = {}


def page(name: str, order: int = 100, available=None):
    """Registra uma página. A função recebe um PageContext.

    `available(ctx) -> bool` esconde a página quando não se aplica ao projeto.
    """
    def decorator(func):
        func.page_order = order
        func.page_available = available or (lambda ctx: True)
        PAGE_REGISTRY[name] = func
        return func
    return decorator


def source(kind: str):
    """Registra a classe de uma fonte de dados pelo valor de `fonte.tipo` na config."""
    def decorator(cls):
        SOURCE_REGISTRY[kind] = cls
        return cls
    return decorator


def ordered_pages() -> dict:
    return dict(sorted(PAGE_REGISTRY.items(), key=lambda item: item[1].page_order))
