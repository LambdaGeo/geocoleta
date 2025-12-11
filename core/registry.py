PAGE_REGISTRY = {}
DATASOURCE_REGISTRY = {}

# Decorator para páginas
def page(name: str):
    def decorator(func):
        PAGE_REGISTRY[name] = func
        return func
    return decorator

# Decorator para fontes de dados
def datasource(name: str):
    def decorator(cls):
        DATASOURCE_REGISTRY[name] = cls()
        return cls
    return decorator
