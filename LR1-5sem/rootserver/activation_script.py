#Задание ***
import sys
import requests
import re
import os
from importlib.abc import PathEntryFinder, MetaPathFinder
from importlib.util import spec_from_loader
from urllib.parse import urljoin, urlparse
import types


class PackageLoader:
    """Загрузчик для пакетов с поддержкой вложенных модулей"""

    def __init__(self, base_url, package_name):
        self.base_url = base_url.rstrip('/')
        self.package_name = package_name

    def create_module(self, spec):
        """Создает новый модуль - возвращаем None для использования стандартного"""
        return None

    def exec_module(self, module):
        """Выполняет код модуля пакета"""
        try:
            # Для пакета грузим __init__.py
            if module.__spec__.submodule_search_locations:
                init_url = f"{self.base_url}/__init__.py"
                print(f"Загрузка пакета: {init_url}")

                response = requests.get(init_url, timeout=10)
                response.raise_for_status()

                source = response.text
                code = compile(source, init_url, mode="exec")
                exec(code, module.__dict__)

            # Для обычного модуля в пакете
            else:
                module_url = f"{self.base_url}/{module.__name__.split('.')[-1]}.py"
                print(f"Загрузка модуля: {module_url}")

                response = requests.get(module_url, timeout=10)
                response.raise_for_status()

                source = response.text
                code = compile(source, module_url, mode="exec")
                exec(code, module.__dict__)

        except Exception as e:
            raise ImportError(f"Ошибка загрузки: {e}")

    def get_code(self, fullname):
        """Получает код для модуля"""
        if fullname == self.package_name:
            url = f"{self.base_url}/__init__.py"
        else:
            module_name = fullname.split('.')[-1]
            url = f"{self.base_url}/{module_name}.py"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def get_source(self, fullname):
        """Получает исходный код"""
        return self.get_code(fullname)

    def is_package(self, fullname):
        """Проверяет, является ли модуль пакетом"""
        return fullname == self.package_name


class URLFinder(PathEntryFinder):
    """Поисковик с поддержкой пакетов и вложенных модулей"""

    def __init__(self, base_url, available_modules, available_packages):
        self.base_url = base_url.rstrip('/')
        self.available_modules = available_modules
        self.available_packages = available_packages

    def find_spec(self, fullname, target=None):
        """Находит спецификацию для модуля или пакета"""
        try:
            # Разбираем полное имя на компоненты
            parts = fullname.split('.')
            first_part = parts[0]

            # 1. Проверяем корневой модуль
            if len(parts) == 1:
                if first_part in self.available_modules:
                    # Обычный модуль
                    return self._create_module_spec(first_part, False)

                elif first_part in self.available_packages:
                    # Пакет
                    return self._create_package_spec(first_part)

            # 2. Проверяем вложенные модули в пакетах
            elif len(parts) > 1:
                package_name = parts[0]
                submodule_name = parts[-1]

                if package_name in self.available_packages:
                    # Проверяем существование подмодуля
                    package_url = f"{self.base_url}/{package_name}"
                    submodule_path = f"{package_url}/{submodule_name}.py"

                    # Проверяем доступность подмодуля
                    response = requests.head(submodule_path, timeout=5)
                    if response.status_code == 200:
                        return self._create_module_spec(fullname, False, package_url)

            return None

        except Exception as e:
            print(f"Ошибка в find_spec для {fullname}: {e}")
            return None

    def _create_module_spec(self, fullname, is_package, base_url=None):
        """Создает спецификацию для модуля"""
        if base_url is None:
            base_url = self.base_url

        if is_package:
            origin = f"{base_url}/{fullname}"
            search_locations = [origin]
        else:
            module_name = fullname.split('.')[-1]
            origin = f"{base_url}/{module_name}.py"
            search_locations = None

        loader = PackageLoader(base_url, fullname if is_package else None)

        return spec_from_loader(
            fullname,
            loader,
            origin=origin,
            is_package=is_package,
            submodule_search_locations=search_locations
        )

    def _create_package_spec(self, package_name):
        """Создает спецификацию для пакета"""
        package_url = f"{self.base_url}/{package_name}"

        loader = PackageLoader(package_url, package_name)

        return spec_from_loader(
            package_name,
            loader,
            origin=f"{package_url}/__init__.py",
            is_package=True,
            submodule_search_locations=[package_url]
        )


class PackageMetaFinder(MetaPathFinder):
    """MetaPathFinder для обработки вложенных импортов в пакетах"""

    def __init__(self, base_finder):
        self.base_finder = base_finder

    def find_spec(self, fullname, path, target=None):
        """Находит спецификацию через базовый finder"""
        try:
            return self.base_finder.find_spec(fullname, target)
        except Exception as e:
            print(f"Ошибка в PackageMetaFinder: {e}")
            return None


def discover_packages_and_modules(url):
    """Обнаруживает пакеты и модули на URL"""
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        data = response.text

        modules = set()
        packages = set()

        # Ищем .py файлы (исключаем __init__.py и __main__.py)
        py_files = re.findall(r'href="([a-zA-Z_][a-zA-Z0-9_]*\.py)"', data)
        modules.update({
            name[:-3] for name in py_files
            if not name.startswith('__') and name != 'setup.py'
        })

        # Ищем директории (пакеты)
        directories = re.findall(r'href="([a-zA-Z_][a-zA-Z0-9_]*)/"', data)
        packages.update({
            d for d in directories
            if not d.startswith(('.', '_')) and d not in ['static', 'templates', 'tests']
        })

        # Проверяем, какие пакеты действительно содержат __init__.py
        valid_packages = set()
        for package in packages:
            init_url = f"{url.rstrip('/')}/{package}/__init__.py"
            response = requests.head(init_url, timeout=3)
            if response.status_code == 200:
                valid_packages.add(package)

        return modules, valid_packages

    except Exception as e:
        raise ImportError(f"Ошибка discovery: {e}")


def enhanced_url_hook(some_str):
    """Улучшенный хук с поддержкой пакетов"""
    if not some_str.startswith(("http", "https")):
        raise ImportError("Неверный URL протокол")

    try:
        print(f"Анализ хоста: {some_str}")

        # Проверяем доступность
        response = requests.get(some_str, timeout=8)
        response.raise_for_status()

        # Обнаруживаем пакеты и модули
        modules, packages = discover_packages_and_modules(some_str)

        print(f"Обнаружено: {len(modules)} модулей, {len(packages)} пакетов")
        if modules:
            print(f"Модули: {sorted(modules)}")
        if packages:
            print(f"Пакеты: {sorted(packages)}")

        # Создаем finder
        finder = URLFinder(some_str, modules, packages)

        # Регистрируем meta finder для вложенных импортов
        meta_finder = PackageMetaFinder(finder)
        sys.meta_path.insert(0, meta_finder)

        return finder

    except Exception as e:
        raise ImportError(f"Ошибка обработки хоста: {e}")


# Активируем хук
sys.path_hooks.append(enhanced_url_hook)
print("Улучшенный URL hook с поддержкой пакетов активирован")


# # Задание **
# import sys
# import requests
# import re
# import time
# from importlib.abc import PathEntryFinder
# from importlib.util import spec_from_loader
# from urllib.parse import urlparse
# import socket
# import ssl
#
#
# class URLLoader:
#     def create_module(self, spec):
#         return None
#
#     def exec_module(self, module):
#         """Выполняет код модуля с расширенной обработкой исключений"""
#         try:
#             print(f"Загрузка модуля из: {module.__spec__.origin}")
#
#             response = requests.get(
#                 module.__spec__.origin,
#                 timeout=10,  # Увеличиваем таймаут
#                 headers={'User-Agent': 'Python-URLLoader/1.0'},
#                 allow_redirects=True  # Разрешаем перенаправления
#             )
#             response.raise_for_status()  # Проверяем HTTP статус
#
#             source = response.text
#             code = compile(source, module.__spec__.origin, mode="exec")
#             exec(code, module.__dict__)
#
#             print("Модуль успешно загружен")
#
#         except Exception as e:
#             # Преобразуем все исключения в ImportError с понятными сообщениями
#             raise self._handle_exception(e, module.__spec__.origin)
#
#     def _handle_exception(self, exception, url):
#         """Обрабатывает исключения и возвращает понятные ImportError"""
#
#         if isinstance(exception, requests.exceptions.Timeout):
#             return ImportError(f"Таймаут подключения: сервер {url} не ответил в течение 10 секунд")
#
#         elif isinstance(exception, requests.exceptions.ConnectionError):
#             # Более детальный анализ ошибок соединения
#             if "Name or service not known" in str(exception):
#                 return ImportError(f"Хост не найден: {urlparse(url).netloc} не существует")
#             elif "Connection refused" in str(exception):
#                 return ImportError(f"Соединение отклонено: сервер {url} отверг подключение")
#             else:
#                 return ImportError(f"Ошибка соединения: {exception}")
#
#         elif isinstance(exception, requests.exceptions.HTTPError):
#             status_code = exception.response.status_code
#             if status_code == 404:
#                 return ImportError(f"Файл не найден (404): {url}")
#             elif status_code == 403:
#                 return ImportError(f"Доступ запрещен (403): {url}")
#             elif status_code == 500:
#                 return ImportError(f"Ошибка сервера (500): {url}")
#             else:
#                 return ImportError(f"HTTP ошибка {status_code}: {url}")
#
#         elif isinstance(exception, requests.exceptions.SSLError):
#             return ImportError(f"SSL ошибка: проблема с сертификатом для {url}")
#
#         elif isinstance(exception, requests.exceptions.TooManyRedirects):
#             return ImportError(f"Слишком много перенаправлений: {url}")
#
#         elif isinstance(exception, socket.gaierror):
#             return ImportError(f"Ошибка DNS: хост {urlparse(url).netloc} не найден")
#
#         elif isinstance(exception, ssl.SSLError):
#             return ImportError(f"SSL ошибка: {exception}")
#
#         else:
#             return ImportError(f"Неожиданная ошибка при загрузке {url}: {exception}")
#
#
# class URLFinder(PathEntryFinder):
#     def __init__(self, url, available):
#         self.url = url.rstrip('/')
#         self.available = available
#
#     def find_spec(self, name, target=None):
#         """Поиск спецификации с обработкой исключений"""
#         try:
#             if name in self.available:
#                 origin = f"{self.url}/{name}.py"
#                 loader = URLLoader()
#                 return spec_from_loader(name, loader, origin=origin)
#             return None
#         except Exception as e:
#             print(f"Ошибка в find_spec: {e}")
#             return None
#
#
# def url_hook(some_str):
#     """Хук для обработки URL с расширенной обработкой исключений"""
#
#     # Проверяем валидность URL
#     if not some_str.startswith(("http", "https")):
#         raise ImportError("Неверный протокол. Используйте http:// или https://")
#
#     try:
#         # Парсим URL для валидации
#         parsed_url = urlparse(some_str)
#         if not parsed_url.netloc:
#             raise ImportError("Неверный URL: отсутствует домен")
#
#         print(f"Проверка хоста: {some_str}")
#
#         # Проверяем доступность хоста с таймаутом
#         try:
#             response = requests.get(
#                 some_str,
#                 timeout=8,  # Таймаут для проверки доступности
#                 headers={'User-Agent': 'Python-URLHook/1.0'},
#                 allow_redirects=True
#             )
#             response.raise_for_status()
#
#         except requests.exceptions.Timeout:
#             raise ImportError(f"Хост недоступен: {some_str} не отвечает (таймаут 8с)")
#
#         except requests.exceptions.ConnectionError as e:
#             # Детальный анализ ошибок соединения
#             error_msg = str(e).lower()
#             if "name or service not known" in error_msg:
#                 raise ImportError(f" DNS ошибка: хост {parsed_url.netloc} не существует")
#             elif "connection refused" in error_msg:
#                 raise ImportError(f"Соединение отклонено: {some_str}")
#             else:
#                 raise ImportError(f"Ошибка соединения: {some_str} - {e}")
#
#         except requests.exceptions.HTTPError as e:
#             raise ImportError(f"HTTP ошибка {e.response.status_code}: {some_str}")
#
#         # Анализируем содержимое для поиска модулей
#         data = response.text
#         filenames = re.findall(r'href="([a-zA-Z_][a-zA-Z0-9_]*\.py)"', data)
#         modnames = {name[:-3] for name in filenames}
#
#         print(f"Найдены модули: {modnames}")
#         return URLFinder(some_str, modnames)
#
#     except ImportError:
#         # Пробрасываем уже обработанные ImportError
#         raise
#     except Exception as e:
#         # Ловим любые другие исключения
#         raise ImportError(f"Неожиданная ошибка при обработке {some_str}: {e}")
#
#
# # Декоратор для повторных попыток
# def retry_import(max_attempts=2, delay=2):
#     """Декоратор для повторных попыток импорта"""
#
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             last_exception = None
#             for attempt in range(max_attempts):
#                 try:
#                     return func(*args, **kwargs)
#                 except ImportError as e:
#                     last_exception = e
#                     if attempt < max_attempts - 1:
#                         print(f"Попытка {attempt + 1}/{max_attempts} не удалась. Повтор через {delay} сек...")
#                         time.sleep(delay)
#             raise last_exception
#
#         return wrapper
#
#     return decorator
#
#
# # Активируем хук
# sys.path_hooks.append(url_hook)
# print("URL hook с обработкой исключений активирован")

# Задание *
# import sys
# import requests
# import re
# from importlib.abc import PathEntryFinder
# from importlib.util import spec_from_loader
# import time
#
#
# class URLLoader:
#     def create_module(self, spec):
#         return None
#
#     def exec_module(self, module):
#         try:
#             print(f"Загрузка модуля из: {module.__spec__.origin}")
#             start_time = time.time()
#
#             response = requests.get(
#                 module.__spec__.origin,
#                 timeout=10,
#                 headers={'User-Agent': 'Python-URLLoader/1.0'}
#             )
#             response.raise_for_status()
#
#             source = response.text
#             code = compile(source, module.__spec__.origin, mode="exec")
#             exec(code, module.__dict__)
#
#             end_time = time.time()
#             print(f"Модуль загружен за {end_time - start_time:.2f} секунд")
#
#         except requests.exceptions.Timeout:
#             raise ImportError("Таймаут: хост не ответил вовремя")
#         except requests.exceptions.ConnectionError:
#             raise ImportError("Ошибка соединения: хост недоступен")
#         except requests.exceptions.HTTPError as e:
#             raise ImportError(f"HTTP ошибка: {e.response.status_code}")
#         except Exception as e:
#             raise ImportError(f"Ошибка: {e}")
#
#
# class URLFinder(PathEntryFinder):
#     def __init__(self, url, available):
#         self.url = url.rstrip('/')
#         self.available = available
#
#     def find_spec(self, name, target=None):
#         if name in self.available:
#             origin = f"{self.url}/{name}.py"
#             loader = URLLoader()
#             return spec_from_loader(name, loader, origin=origin)
#         return None
#
#
# def url_hook(some_str):
#     if not some_str.startswith(("http", "https")):
#         raise ImportError("Неверный URL протокол")
#
#     try:
#         print(f"Проверка хоста: {some_str}")
#         response = requests.get(some_str, timeout=5)
#         response.raise_for_status()
#
#         data = response.text
#         filenames = re.findall(r'href="([a-zA-Z_][a-zA-Z0-9_]*\.py)"', data)
#         modnames = {name[:-3] for name in filenames}
#
#         print(f"Найдены модули: {modnames}")
#         return URLFinder(some_str, modnames)
#
#     except requests.exceptions.Timeout:
#         raise ImportError(f"Таймаут: хост {some_str} недоступен")
#     except Exception as e:
#         raise ImportError(f"Ошибка доступа к {some_str}: {e}")
#
#
# # Активируем хук
# sys.path_hooks.append(url_hook)
# print("URL hook добавлен в sys.path_hooks")