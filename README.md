# Гайд по использованию

## 1. Клонирование репозитория

```bash
git clone https://github.com/repen7ant/LoyaltyHub.git
cd LoyaltyHub
```

## 2. Создание .env

```bash
mv .env.example .env
cd fastapi
mv .env.example .env
```

## 3. Запуск

```bash
docker-compose up -d --build
```

## 4. Разработка

После запуска API будет доступно по адресу:

```bash
http://localhost:8000
```

Swagger:

```bash
http://localhost:8000/docs#
```

Логи бэкенда:

```bash
docker compose logs fastapi -f
```

Логи всех контейнеров:

```bash
docker compose logs -f
```

## 5. Остановка проекта

```bash
docker compose down
```

С удалением данных:

```bash
docker compose down -v
```
