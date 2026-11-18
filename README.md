# cardix — Karten-Projekt

Репозиторий проекта карточных каталогов и offline-first сервисов **Karten-Projekt**.

> [!NOTE]
> На ветке `main` в настоящее время размещены только `LICENSE` и этот `README.md`. Основной код, спецификации и прототипы монорепозитория находятся в неслитой ветке [`karten-projekt`](../../tree/karten-projekt/karten-projekt) в каталоге `karten-projekt/`.

## Обзор концепции

Идея ядра — **карточка как стабильный номер позиции**. Одна и та же запись каталога печатается на бумаге, отображается в HTML-интерфейсе, кодируется в QR-код и используется симулятором:

- **Единый каталог:** печать, экран, QR и симулятор опираются на один источник данных.
- **Приватность по умолчанию:** на карточке и в QR-коде хранится только код позиции, без персональных данных, имён и сведений о здоровье.
- **Непереиспользуемые идентификаторы:** удалённые позиции помечаются статусом `retired`, а их номер остаётся занятым.
- **Offline-first и минимум зависимостей:** бумажный сценарий остаётся работоспособным без сети; серверная часть и симулятор написаны на стандартной библиотеке Python и статическом HTML/JS.

## Структура проекта (ветка `karten-projekt`)

| Каталог | Назначение | Статус |
|---|---|---|
| `karten-projekt/00-kern/` | Спецификация формата каталога (`SPEC-katalog.md`) и общие правила ядра | Спецификация v0.1 |
| `karten-projekt/10-senioren-dienste/` | Карточки услуг для пожилых (6 позиций: Einkaufen, Essen, Putzen, Spazieren, Briefe, Reden), каталог `katalog-sen.json`, офлайн-страница `karten-senioren.html`, HTTP-сервер заказов `server.py`, `Dockerfile` | Прототип (ожидает проверки на пользователях) |
| `karten-projekt/20-essen-vending/` | Концепция заказа еды, вендинга, ячеек выдачи и велокурьеров | Идея и выводы модели |
| `karten-projekt/30-spiele-comics/` | Карточные игры, комиксы и многослойные бумажные модели | Идея |
| `karten-projekt/40-projekt-karten/` | Карточки задач, конвейеры, спецификации, Zettelkasten | Идея |
| `karten-projekt/50-digitaler-zwilling/` | Симулятор `sim.py` (заказы, робот у ячеек, курьеры, сбои, погодные коэффициенты) | Модель v0.2 |
| `karten-projekt/60-reise-sprachkarten/` | Офлайн-разговорник в виде карточек для поездок | Идея |

## Стек и команды запуска

- **Ядро и сервер:** Python 3 (только стандартная библиотека, без сторонних пакетов), HTML/JS без этапа сборки.
- **Сервер заказов (`10-senioren-dienste/server.py`):**
  - Эндпоинты: `GET /health`, `GET /katalog`, `POST /bestellung` (принимает псевдонимный код клиента `K-0000`..`K-9999` и список активных карт).
  - Переменные окружения: `PORT` (по умолчанию `8080`), `KATALOG`, `STORE`, `ALLOWED_ORIGIN`.

```bash
# Запуск локального HTTP-сервера заказов (из ветки karten-projekt)
python3 karten-projekt/10-senioren-dienste/server.py

# Сборка и запуск через Docker (порт 8080)
cd karten-projekt/10-senioren-dienste
docker build -t karten-server .
docker run -p 8080:8080 karten-server

# Запуск симулятора (только stdlib Python)
python3 karten-projekt/50-digitaler-zwilling/sim.py
```

## Ветки репозитория

- `main` — базовая ветка (файл лицензии и `README.md`).
- `karten-projekt` — основная неслитая ветка с монорепозиторием `karten-projekt/` (спецификация ядра, сервер заказов, HTML-прототип и симулятор v0.2; Pull Request не открыт).

## Лицензия

- В ветке `main` размещён файл `LICENSE` с текстом **GNU Affero General Public License v3.0 (AGPL-3.0)**.
- В документах и заголовках кода ветки `karten-projekt` (`karten-projekt/README.md`, `server.py`, `Dockerfile`, `50-digitaler-zwilling/README.md`) указана лицензия **Apache-2.0**.
