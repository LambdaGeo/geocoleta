PAGE_REGISTRY = {}
SOURCE_REGISTRY = {}


def page(name: str, order: int = 100, available=None):
    """Registers a dashboard page. The decorated function receives a PageContext.

    `available(ctx) -> bool` hides the page when it does not apply to the project.
    """
    def decorator(func):
        func.page_order = order
        func.page_available = available or (lambda ctx: True)
        PAGE_REGISTRY[name] = func
        return func
    return decorator


def source(kind: str):
    """Registers a data source class by the value of `source.type` (or `fonte.tipo`) in config."""
    def decorator(cls):
        SOURCE_REGISTRY[kind] = cls
        return cls
    return decorator


def ordered_pages() -> dict:
    return dict(sorted(PAGE_REGISTRY.items(), key=lambda item: item[1].page_order))
