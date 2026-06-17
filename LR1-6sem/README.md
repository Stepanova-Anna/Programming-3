# Отчет по лабораторной работе CI/CD с использованием SourceCraft на примере Hugo

### Цель работы
Изучить процесс создания статического сайта-блога с использованием генератора статических сайтов **Hugo** и настройки автоматической сборки и деплоя через CI/CD платформу **SourceCraft**.

### Задачи
1. Развернуть статический блог на Hugo
2. Настроить структуру проекта
3. Настроить CI/CD для автоматической сборки
4. Обеспечить доступность сайта по ссылке

### CI/CD

**CI/CD (Continuous Integration / Continuous Deployment)** — это практика автоматизации сборки, тестирования и развертывания приложений. В данном проекте используется **SourceCraft** — платформа для автоматической сборки и публикации статических сайтов.

---

### Структура проекта

```
lab1-hugo/
├── .sourcecraft/          # Конфигурация CI/CD
├── archetypes/            # Шаблоны для новых записей
├── assets/                # Ресурсы (SCSS, JS)
├── config/                # Конфигурация Hugo
├── content/               # Содержимое сайта (посты, страницы)
├── data/                  # Данные для шаблонов
├── i18n/                  # Файлы интернационализации
├── layouts/               # Шаблоны
├── public/                # Сгенерированный сайт (игнорируется в git)
├── resources/             # Кэш ресурсов Hugo
├── static/                # Статические файлы (изображения, CSS, JS)
├── themes/                # Темы (используется blowfish)
├── .gitignore             # Игнорируемые файлы
├── .gitmodules            # Подмодули Git
├── .hugo_build.lock       # Блокировка сборки Hugo
├── hugo.toml              # Основной конфигурационный файл Hugo
└── README.md              # Документация проекта
```

### Настройка CI/CD

#### Конфигурация сборки (`.sourcecraft/ci.yaml`)

```yaml
on:
  push:
    workflows: build-hugo-site
    filter:
      branches: main

workflows:
  build-hugo-site:
    env:
      HUGO_VERSION: 0.128.0
    tasks:
      - name: Check-markdown-links
        cubes:
          - name: Run-markdown-link-check
            action: tcort/github-action-markdown-link-check@v1
            with:
              base-branch: main
              use-verbose-mode: yes

      - name: Build-and-deploy
        needs: [Check-markdown-links]
        cubes:
          - name: Download-Hugo
            script:
              - curl -LJO https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb

          - name: Check_File
            script:
              - ls -la

          - name: Install_Hugo
            script:
              - sudo dpkg -i hugo_extended_${HUGO_VERSION}_linux-amd64.deb
              - rm hugo_extended_${HUGO_VERSION}_linux-amd64.deb

          - name: Check_Hugo
            script:
              - hugo version

          - name: Build_Site
            script:
              - hugo --config hugo.toml --destination ./public
              - ls -la public/
          
          - name: Publish_Reliase_Site
            script:
              - git checkout -b release
              - ls -la
              - git add .
              - "git commit -m \"feat: Deploy Hugo site\""
              - "git push origin release -f"
```

#### Конфигурация сайта (`.sourcecraft/sites.yaml`)

```yaml
site:
  root: ./public
  ref: release
```
---

## Результаты

### Достигнутые результаты

| Пункт | Статус | Описание |
|-------|--------|----------|
| 1️⃣ | ✅ | Создан статический блог на Hugo |
| 2️⃣ | ✅ | Настроена структура проекта |
| 3️⃣ | ✅ | Настроен CI/CD для автоматической сборки |
| 4️⃣ | ✅ | Сайт доступен по ссылке |

### 🌐 Ссылка на сайт

**Адрес сайта:** [https://stepprog.sourcecraft.site/lab1-hugo](https://stepprog.sourcecraft.site/lab1-hugo)

[Ссылка на репозиторий](https://sourcecraft.dev/stepprog/lab1-hugo?rev=main)

---

## Вывод

**Настроен CI/CD** — автоматизирован процесс сборки при изменениях в ветке `main`

**Сайт опубликован** — статический блог доступен по адресу `https://stepprog.sourcecraft.site/lab1-hugo`

