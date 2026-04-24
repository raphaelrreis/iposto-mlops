# iposto-mlops

`iposto-mlops` e uma blueprint MLOps de nivel producao para monitorar e prever a volatilidade de precos de combustiveis no Brasil e nos EUA. O projeto foi estruturado para demonstrar engenharia senior com Databricks, Terraform, Docker, CI/CD e um fluxo de dados medallion pronto para ser operacionalizado.

## Eyes-on-Star

### Objetivo de negocio
- Consolidar dados brutos de postos e simulacoes de APIs em uma camada Bronze.
- Higienizar e enriquecer os dados em Silver com deduplicacao, filtros de preco e quality gates.
- Construir uma camada Gold orientada a feature store para prever o preco do dia seguinte por geohash, bandeira e tipo de combustivel.
- Registrar, promover e servir modelos com MLflow e Databricks Model Registry.

### Arquitetura-alvo
1. Ingestao
   - JSONs brutos entram em Bronze a partir de geradores mock ou APIs reais.
2. Curadoria
   - PySpark aplica schema, deduplicacao, filtros de outliers e validacoes.
3. Feature Engineering
   - Agregacoes diarias por `geohash`, `brand` e `fuel_type`, com medias moveis de 7 e 30 dias.
4. Treinamento
   - `XGBoostRegressor` em pipeline scikit-learn com MLflow autologging.
5. Deploy
   - Databricks Asset Bundle publica jobs; Terraform provisiona workspace, cluster, jobs base e Unity Catalog.
6. Serving
   - Databricks centraliza governanca, treino e registro; Kubernetes entra como camada de serving quando houver necessidade de baixa latencia, autoscaling fino, isolamento regional e estrategias de rollout mais sofisticadas.

### Por que Databricks + K8s para serving
- Databricks e a plataforma principal para engenharia de dados, treino distribuido, lineage e governanca.
- Kubernetes e a camada mais flexivel para serving online quando a inferencia precisa de SLA agressivo, canary deployment, traffic splitting e isolamento entre workloads.
- Essa separacao evita acoplamento entre workloads analiticos e transacionais, preservando custo e resiliencia operacional.

## Estrutura do repositorio

```text
.
|-- .github/workflows/           # GitHub Actions executaveis
|-- databricks_assets/           # Python tasks e recursos do Databricks Asset Bundle
|-- deployment/                  # Documentacao operacional de CI/CD
|-- scripts/                     # Entrypoints locais
|-- src/iposto_mlops/            # Package principal
|-- terraform/
|   |-- bootstrap/               # Cria o workspace Azure Databricks
|   |-- platform/                # Configura cluster, jobs e Unity Catalog
|   `-- modules/                 # Modulos reutilizaveis
`-- tests/                       # Testes de transformacoes Spark
```

## Camadas de dados

### Bronze
- Formato de entrada: JSON bruto.
- Campos principais: pais, regiao, cidade, posto, bandeira, combustivel, coordenadas e preco observado.
- Artefato de bootstrap: `scripts/generate_mock_bronze.py`.

### Silver
- Schema enforcement.
- Deduplicacao por `event_id`.
- Filtro de preco irreal por faixa de pais e combustivel.
- Colunas normalizadas e timestamps tipados.

### Gold
- Agregacao diaria por `country_code`, `fuel_type`, `brand` e `geohash`.
- Features de tendencia e volatilidade:
  - `moving_avg_7d`
  - `moving_avg_30d`
  - `volatility_7d`
  - `lag_1d_price`
  - `target_next_day_price`

## MLOps

### Experimento e registro
- MLflow autologging registra parametros, metricas e artefatos.
- O modelo pode ser registrado em `iposto_mlops_next_day_price`.
- A promocao de estagios usa `Staging` e `Production` para apoiar gates entre treino e consumo.

### Qualidade e operacao
- Logging padronizado.
- Excecoes de pipeline especificas.
- Tipagem com Python type hints.
- Testes unitarios Spark para regras de Silver e Gold.

## Deploy rapido

### 1. Ambiente local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 1.1 Stack completo de treino

```bash
pip install -e '.[dev,ml,quality]'
```

Se voce estiver em Python `3.14`, o ambiente local vai resolver `PySpark 4.x` apenas para compatibilidade de desenvolvimento. Os jobs do Databricks continuam ancorados no runtime `14.3 LTS ML`, que usa Spark `3.5`.

### 2. Gerar dados mock

```bash
python scripts/generate_mock_bronze.py --output-dir data/bronze/fuel_prices --days 45
```

### 3. Rodar testes

```bash
pytest
```

### 4. Bundle Databricks

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

### 5. Terraform

```bash
cd terraform/bootstrap
terraform init && terraform plan

cd ../platform
terraform init && terraform plan
```

## Docker e imutabilidade

O `Dockerfile` usa multi-stage build para gerar um ambiente repetivel para Databricks Container Services. A imagem congela dependencias de sistema e Python em build time, reduz drift entre dev, CI e clusters de treinamento, e facilita rollback por tag imutavel.

## Observacoes operacionais
- O pacote Python usa `iposto_mlops` porque hifens nao sao validos como nome de modulo.
- O nome do produto e do bundle permanece `iposto-mlops`.
- Os jobs do bundle usam runtime `14.3 LTS ML` como baseline de cluster.
- O conjunto minimo de dev instala apenas o necessario para testes locais; treino e validacao avancada usam os extras `ml` e `quality`.
