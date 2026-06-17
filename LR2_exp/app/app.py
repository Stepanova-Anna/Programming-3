"""
Асинхронное веб-приложение для поиска публикаций в Crossref
Использует Flask для веб-интерфейса и aiohttp для асинхронных HTTP-запросов
"""

import asyncio
import aiohttp
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import logging
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфигурация API Crossref
CROSSREF_API_URL = "https://api.crossref.org/works"
MAX_RESULTS = 20
TIMEOUT = 10

class CrossrefSearch:
    """
    Класс для асинхронного поиска в Crossref API
    Использует aiohttp для выполнения HTTP-запросов
    """

    @staticmethod
    async def search_publications(session, query_params):
        """
        Асинхронный метод для поиска публикаций

        Аргументы:
            session: aiohttp.ClientSession - сессия для HTTP-запросов
            query_params: dict - параметры поиска (author, title)

        Возвращает:
            dict: результаты поиска или информацию об ошибке
        """
        try:
            params = {
                'rows': MAX_RESULTS,
                'sort': 'relevance',
            }

            query_parts = []

            if query_params.get('author'):
                author_query = f'author:"{query_params["author"]}"'
                query_parts.append(author_query)
                logger.info(f"Добавлен поиск по автору: {query_params['author']}")

            if query_params.get('title'):
                title_query = f'title:"{query_params["title"]}"'
                query_parts.append(title_query)
                logger.info(f"Добавлен поиск по названию: {query_params['title']}")

            if query_parts:
                params['query'] = ' AND '.join(query_parts)
                logger.info(f"Итоговый запрос: {params['query']}")
            else:
                return {
                    'error': 'Не указаны параметры поиска',
                    'status': 'error'
                }

            # Логируем полный URL для отладки
            full_url = f"{CROSSREF_API_URL}?{urllib.parse.urlencode(params)}"
            logger.info(f"Отправка запроса: {full_url}")

            # Асинхронный GET-запрос с таймаутом
            async with asyncio.timeout(TIMEOUT):
                async with session.get(CROSSREF_API_URL, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API вернул статус {response.status}: {error_text}")
                        return {
                            'error': f'API вернул ошибку: {response.status}. {error_text[:100]}',
                            'status': 'error'
                        }

                    data = await response.json()

                    if not data.get('message', {}).get('items'):
                        return {
                            'error': 'По вашему запросу ничего не найдено',
                            'status': 'empty'
                        }

                    items = data['message']['items']
                    formatted_results = []

                    for item in items[:MAX_RESULTS]:
                        formatted_result = CrossrefSearch._format_publication(item)
                        if formatted_result:
                            formatted_results.append(formatted_result)

                    return {
                        'results': formatted_results,
                        'total': data['message'].get('total-results', 0),
                        'status': 'success'
                    }

        except asyncio.TimeoutError:
            logger.error("Превышено время ожидания ответа от API")
            return {
                'error': 'Превышено время ожидания ответа от сервера',
                'status': 'timeout'
            }
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка соединения: {str(e)}")
            return {
                'error': 'Ошибка соединения с API Crossref',
                'status': 'connection_error'
            }
        except Exception as e:

            logger.error(f"Неожиданная ошибка: {str(e)}")
            return {
                'error': f'Произошла ошибка: {str(e)}',
                'status': 'error'
            }

    @staticmethod
    def _format_publication(item):
        """
        Форматирование данных публикации

        Аргументы:
            item: dict - данные публикации из API

        Возвращает:
            dict: отформатированные данные публикации
        """
        try:
            title = item.get('title', ['Без названия'])[0] if item.get('title') else 'Без названия'

            authors = []
            affiliations = []

            if item.get('author'):
                for author in item['author']:
                    given = author.get('given', '')
                    family = author.get('family', '')
                    full_name = f"{given} {family}".strip() or "Неизвестный автор"
                    authors.append(full_name)

                    if author.get('affiliation') and not affiliations:
                        affiliations = [aff.get('name', 'Не указано') for aff in author['affiliation']]

            first_author_affiliation = affiliations[0] if affiliations else 'Не указано'

            container_title = item.get('container-title', ['Не указано'])[0] if item.get('container-title') else 'Не указано'

            year = 'Не указан'
            if item.get('issued'):
                date_parts = item['issued'].get('date-parts', [[]])
                if date_parts and date_parts[0]:
                    year = str(date_parts[0][0]) if date_parts[0][0] else 'Не указан'

            return {
                'title': title,
                'authors': authors,
                'first_author': authors[0] if authors else 'Неизвестный автор',
                'container_title': container_title,
                'year': year,
                'affiliation': first_author_affiliation
            }
        except Exception as e:
            logger.error(f"Ошибка форматирования публикации: {str(e)}")
            return None

# Асинхронная функция для выполнения поиска
async def perform_search(query_params):
    """
    Асинхронная функция для выполнения поиска через API Crossref

    Аргументы:
        query_params: dict - параметры поиска

    Возвращает:
        dict: результаты поиска
    """
    # Создаем асинхронную сессию aiohttp
    async with aiohttp.ClientSession() as session:
        search_instance = CrossrefSearch()
        return await search_instance.search_publications(session, query_params)

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Основной обработчик маршрута
    Поддерживает GET и POST методы
    """
    results = None
    error = None
    search_params = {}

    if request.method == 'POST':
        author = request.form.get('author', '').strip()
        title = request.form.get('title', '').strip()

        search_params = {
            'author': author,
            'title': title
        }

        if not author and not title:
            error = 'Пожалуйста, заполните хотя бы одно поле поиска'
        else:
            try:
                # Подготавливаем параметры запроса
                query_params = {}
                if author:
                    query_params['author'] = author
                if title:
                    query_params['title'] = title

                # Запускаем асинхронный поиск
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(perform_search(query_params))
                finally:
                    loop.close()

                if result['status'] == 'success':
                    results = result.get('results', [])
                else:
                    error = result.get('error', 'Произошла ошибка при поиске')

            except Exception as e:
                logger.error(f"Ошибка в основном обработчике: {str(e)}")
                error = f'Ошибка выполнения поиска: {str(e)}'

    return render_template('index.html',
                         results=results,
                         error=error,
                         search_params=search_params)

@app.route('/api/search', methods=['POST'])
async def api_search():
    """
    API-эндпоинт для асинхронного поиска
    Используется для AJAX-запросов с клиентской стороны
    """
    try:
        data = await request.get_json()
        author = data.get('author', '').strip()
        title = data.get('title', '').strip()

        if not author and not title:
            return jsonify({'error': 'Необходимо указать автора или название'}), 400

        query_params = {}
        if author:
            query_params['author'] = author
        if title:
            query_params['title'] = title

        result = await perform_search(query_params)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Ошибка в API: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)