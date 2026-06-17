# Отчет по лабораторной работе
## «Основы работы с n8n»
### Автоматизация дайджеста новостей по интересам

---

## Цель работы

Создание pipeline для парсинга статей на habr.com, обработки их с помощью LLM (GigaChat), а также отправки результата на почту.

---

В связи с ограничениями безопасности n8n Cloud (запрет на использование requests и BeautifulSoup в Python), все вычислительные узлы были реализованы на JavaScript с использованием встроенных средств платформы.

---

## Схема Workflow


---

## Настройка каждого узла

### Manual Trigger

**Назначение:** Запуск workflow вручную для тестирования.

**Настройки:** Без дополнительных параметров.

---

### 4.2 HTTP Request (Парсинг Habr)

<img width="542" height="672" alt="image" src="https://github.com/user-attachments/assets/4ddaeefa-9593-4e89-ae5c-8a794980ee3b" />

---

### 4.3 Code (JavaScript) — Парсинг статей

**Назначение:** Извлечение данных о статьях из HTML.

**Код:**

```javascript
const htmlContent = $input.first().json.data;

const parser = new DOMParser();
const doc = parser.parseFromString(htmlContent, 'text/html');

const articles = [];

// Ищем статьи на странице
const items = doc.querySelectorAll('article');

items.forEach(article => {
    try {
        const titleLink = article.querySelector('a.tm-title__link');
        const title = titleLink ? titleLink.textContent.trim() : 'Без названия';
        const link = titleLink ? 'https://habr.com' + titleLink.getAttribute('href') : '';
        
        const authorElem = article.querySelector('a.tm-user-info__username');
        const author = authorElem ? authorElem.textContent.trim() : 'Автор не указан';
        
        const dateElem = article.querySelector('time');
        const date = dateElem ? dateElem.getAttribute('datetime') : '';
        
        articles.push({ title, link, author, date });
    } catch (e) {
        // Пропускаем ошибки
    }
});

// Ограничиваем до 10 статей
const result = articles.slice(0, 10);

return {
    articles: result,
    count: result.length
};
```

---

### 4.4 HTTP Request (Получение токена GigaChat)

**Назначение:** Получение OAuth-токена для доступа к GigaChat API.

<img width="545" height="668" alt="image" src="https://github.com/user-attachments/assets/15e1c8bc-5f07-497c-96fa-c3ca56b8fbf8" />


---

### 4.5 Merge (Append)

**Назначение:** Объединение данных из двух потоков: статей и токена.

| Параметр | Значение |
|----------|----------|
| Mode | `Append` |

**Схема соединения:**
- Вход 1: от парсинга статей
- Вход 2: от HTTP Request (токен)

---

### 4.6 Code (JavaScript) — Формирование промпта

**Назначение:** Подготовка запроса к GigaChat с использованием различных типов промптов.

**Код:**

```javascript
const inputData = $input.first().json;
const articles = inputData.articles || [];
const token = inputData.access_token || '';

const articlesText = articles.map((a, i) => 
    `${i+1}. **${a.title}**\n   Автор: ${a.author}\n   Ссылка: ${a.link}`
).join('\n\n');

const prompt = `
Ты — профессиональный редактор дайджестов новостей об искусственном интеллекте.

**РОЛЕВОЙ ПРОМПТ:** Ты — опытный журналист с 10-летним стажем, специализирующийся на AI-тематике.

**ЗАДАНИЕ (zero-shot):** Сделай структурированный дайджест из следующих статей.

**ПРИМЕР (one-shot):**
Вот пример хорошего дайджеста:
# Дайджест AI-новостей
## Топ-3 новости
1. [Название] — краткое описание

**ДОПОЛНИТЕЛЬНЫЕ ПРИМЕРЫ (few-shot):**
Пример 1: ...
Пример 2: ...

**ЦЕПОЧКА РАССУЖДЕНИЙ (Chain of Thought):**
ШАГ 1: Прочитай все статьи
ШАГ 2: Определи главные темы
ШАГ 3: Отбери 3 самые важные статьи
ШАГ 4: Напиши краткое резюме для каждой
ШАГ 5: Сгруппируй остальные по темам
ШАГ 6: Сформируй итоговый дайджест

**НЕГАТИВНЫЙ ПРОМПТ:** НЕ используй смайлики, НЕ пиши "к сожалению", НЕ делай рекламы.

**СТАТЬИ:**
${articlesText}

**Сделай дайджест!**
`;

const payload = {
    model: "GigaChat-Pro",
    messages: [
        { role: "system", content: "Ты профессиональный редактор AI-новостей" },
        { role: "user", content: prompt }
    ],
    temperature: 0.7,
    max_tokens: 1500
};

return {
    access_token: token,
    payload: payload,
    articles: articles
};
```

---

### HTTP Request (Запрос к GigaChat)

<img width="548" height="674" alt="image" src="https://github.com/user-attachments/assets/91526020-942c-4271-9cc1-c6a19cc98db7" />

---

### Code (JavaScript) — Форматирование дайджеста

**Назначение:** Извлечение текста дайджеста и преобразование Markdown → HTML.

**Код:**

```javascript
const response = $input.first().json;
const digest = response.choices?.[0]?.message?.content || 'Дайджест не получен';

// Преобразование Markdown в HTML
const htmlContent = digest
    .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
    .replace(/\*(.*?)\*/g, '<i>$1</i>')
    .replace(/### (.*?)\n/g, '<h3>$1</h3>')
    .replace(/## (.*?)\n/g, '<h2>$1</h2>')
    .replace(/# (.*?)\n/g, '<h1>$1</h1>')
    .replace(/\n/g, '<br>')
    .replace(/• /g, '• ')
    .replace(/- /g, '• ');

return {
    digest: digest,
    html: htmlContent
};
```

---

### Gmail (Send)

<img width="534" height="684" alt="image" src="https://github.com/user-attachments/assets/890fce09-7d8f-4a1f-972a-081bdb409f6d" />

---

## Типы промптов

В работе были реализованы следующие типы промптов:

| Тип промпта | Пример |
|-------------|--------|
| **Ролевой** | `"Ты — опытный журналист с 10-летним стажем, специализирующийся на AI-тематике."` |
| **Zero-shot** | `"Сделай структурированный дайджест из следующих статей."` |
| **One-shot** | `"Вот пример хорошего дайджеста: ... Теперь сделай так же."` |
| **Few-shot** | `"Вот 3 примера дайджестов: ... Сделай по аналогии."` |
| **Chain of Thought** | `"ШАГ 1: Прочитай все статьи. ШАГ 2: Определи главные темы. ..."` |
| **Негативный** | `"НЕ используй смайлики, НЕ пиши 'к сожалению'."` |

---

## Результат работы



---

## Вывод

В ходе выполнения лабораторной работы был создан автоматизированный пайплайн для парсинга статей с Habr, обработки их с помощью GigaChat и отправки дайджеста на почту.

**Основные результаты:**
1. Настроен парсинг статей с хабра «Искусственный интеллект»
2. Реализована авторизация в GigaChat API и получение токена
3. Сформированы промпты всех требуемых типов
4. Получен дайджест от GigaChat
5. Настроена отправка письма через Gmail

Все поставленные задачи выполнены, workflow готов к использованию.

---
