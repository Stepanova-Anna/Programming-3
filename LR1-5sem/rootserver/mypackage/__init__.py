from .utils import greet
from .helpers import calculate

__version__ = "1.0.0"
__all__ = ['greet', 'calculate']

print(f"Пакет mypackage {__version__} инициализирован!")

def package_info():
    return {
        'name': 'mypackage',
        'version': __version__,
        'modules': ['utils', 'helpers']
    }