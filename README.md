# QA AGENTIC RAG

## Make commands

### Run project

```bash
make start
```

### Stop project

```bash
make stop
```

## Architecture

### Целевая архитектура

![Целевая архитектура](./scheme.png)

## Infrastructure

```plaintext
📦infra
┣📂mounts/ ← Docker volumes
┃  ┣📂alertmanager/ ← Настройки для alertmanager
┃  ┃  ┗📜alertmanager.yml ← Настройки для alertmanager
┃  ┣📂db/ ← Хранилище PostgreSQL
┃  ┣📂db_init_scripts/
┃  ┃  ┗📜multiple_db.sh ← Скрипт создания нескольких БД при старте контейнера
┃  ┣📂grafana/ ← Хранилище и настройки Grafana
┃  ┃  ┣📂dashboards ← Дашборды Grafana
┃  ┃  ┗📂provisioning ← Настройки источников и т. п.
┃  ┣📂prefect_server/ ← Хранилище Prefect Server
┃  ┣📂prefect_worker/ ← Хранилище Prefect Worker
┃  ┣📂resume_generator/ ← Хранилище для resume_generator
┃  ┃  ┣📂resumes_pdf/
┃  ┃  ┗📂resumes_json/
┃  ┣📂s3_storage/ ← Хранилище MinIO
┃  ┣📂vector-dst/ ← Настройки vector для отправки логов в кафку
┃  ┃  ┗📜vector.yaml
┃  ┣📂vector-src/ ← Настройки vector для сбора логов из docker stdout
┃  ┃  ┗📜vector.yaml
┃  ┣📂victoriametrics/ ← Хранилище и настройки для Victoria Metrics
┃  ┃  ┗📜prometheus-victoria.yml ← Настройки для Victoria Metrics
┃  ┗📂vmalert/ ← Правила для алертинга
┃     ┗📂rules/
┃        ┗📜vlogs-example-alerts.yml/ ← Правило для алертинга
┣📂prefect_server/
┃  ┗📜Dockerfile ← Dockerfile для Prefect Server
┗📂prefect_worker/
   ┣📂flows/
   ┃  ┗📜deploy_flow.py ← Пример flow с интеграцией S3
   ┣📜Dockerfile ← Dockerfile для Prefect Worker
   ┣📜entrypoint.sh ← Entrypoint для Docker-контейнера
   ┗📜requirements.txt ← Зависимости для выполнения flows
```

## TODO List

- [ ] Добавить Mypy
- [ ] Добавить парсинг "сырых" резюме из S3 в PostgreSQL через оркестратор
- [ ] Добавить тесты
