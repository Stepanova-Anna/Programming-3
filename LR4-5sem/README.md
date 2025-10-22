# Лабораторная работа №4

### Результат:

[**Архив с проектом**](https://github.com/Stepanova-Anna/Programming-2/blob/main/LR6-4sem/lr6.zip))

`doker-compose.yml` (`main.py` с самого начала у меня был назван `new.py`, так как все работало, решила не исправлять это)

```
version: '3.8'

services:
  web:
    build: .
    command: ["uvicorn", "new:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    expose:
      - 8000
    volumes:
      - .:/app
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    depends_on:
      - db

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - web

  db:
    image: mysql:8.0
    volumes:
      - ./db:/var/lib/mysql
    ports:
      - "3307:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=1234
      - MYSQL_USER=user
      - MYSQL_PASSWORD=1234
      - MYSQL_DATABASE=mysqldb
    restart: always
```

`nginx/default.config`:

```
server {
 listen 80;
 server_name localhost;

 location / {
 proxy_pass http://web:8000;
 proxy_set_header Host $host;
 proxy_set_header X-Real-IP $remote_addr;
 proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
 proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

В `Dockerfile` изменена строка:

```
CMD ["uvicorn", "new:app", "--host", "0.0.0.0", "--port", "8000"]
```

В `new.py`:

```
engine = create_engine('mysql+pymysql://user:1234@db/mysqldb')
```

К сожалению, после многочисленных попыток и исправлений результат подключения к базам данных был одним и тем же. 
Даже после помощи одногруппников и при схожих кодах результат не менялся.

![Лабораторная работа 4](https://github.com/Stepanova-Anna/Programming-2/blob/main/LR6-4sem/502.png)



*Попытки исправить прекратились после того, как после дополнения `requirements.txt`, запуска проекта и перехода по уже знакомой ссылке в консоле pycharm стали выводиться ошибки и это невозможно было остановить. Если потребуется, у меня есть видео, записанное друзьям, где видно что именно происходило.*
