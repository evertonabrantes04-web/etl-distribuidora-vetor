# Pipeline ETL e Governança de Dados — Distribuidora Vetor

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![uv](https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com/)

Sistema corporativo de **ETL (Extração, Transformação e Carga)**, enriquecimento geográfico via API de CEP e governança de dados desenvolvido em **Python e Django** para saneamento da base de clientes B2B da **Distribuidora Vetor**.

---

## 🚀 Início Rápido (Quick Start)

Siga os passos abaixo para rodar o projeto localmente:

1. **Clone o repositório** e abra a pasta raiz via terminal no VS Code.
2. **Instale as dependências** utilizando o gerenciador `uv`:
   ```powershell
   uv sync
   ```
3. **Execute as migrações** do banco de dados SQLite:
   ```powershell
   uv run python manage.py migrate
   ```
4. **Importe a base de dados** e inicie o servidor de desenvolvimento:
   ```powershell
   uv run python manage.py importar_clientes dados/clientes_distribuidora_vetor.csv
   uv run python manage.py runserver
   ```
5. Acesse no navegador:
   * **Dashboard Executivo:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   * **Painel Administrativo:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) *(Superuser padrão: `admin` / `vetor123`)*

---

## 🗺️ Mapa de Rotas (Endpoints)

| Rota | Descrição / Ação |
| :--- | :--- |
| `GET /` | Dashboard Executivo (KPIs, Gráficos Chart.js, Upload web de CSV e Trilha de Auditoria) |
| `POST /etl/importar/` | Endpoint acionado pelo formulário web para execução síncrona do pipeline |
| `GET /etl/exportar/` | Download imediato da planilha corporativa em Excel (`.xlsx`) estruturada com 3 abas |
| `GET /admin/` | Mesa de Curadoria e Gestão do Dicionário de Bairros no Django Admin |

---

## 📂 Documentação Técnica Detalhada (`docs/`)

Para manter o repositório limpo, a documentação técnica foi modularizada na pasta `docs/`:

* **[Guia Prático de Implementação Passo a Passo](docs/tutorial-desenvolvimento.md)** — Tutorial completo de criação do projeto, models, comandos e templates.
* **[Frente 1: Motor ETL, Normalização e Testes](docs/frente1-etl.md)** — Saneamento de dados, Regex, Unicode (`NFKD`), cache local de CEP e suíte de testes com *mocks*.
* **[Frente 2: Dashboard, Admin e Relatórios Excel](docs/frente2-dashboard.md)** — Arquitetura da interface moderna em Bootstrap 5, gráficos Chart.js, blindagem da auditoria e exportação multi-aba.
* **[Relatório de Trade-offs e Limites](docs/trade-offs.md)** — Decisões de engenharia (quarentena `REVISAO_MANUAL`, priorização de CEPs geocodificados e dicionário dinâmico).

---

## 🛠️ Divisão de Responsabilidades da Dupla

* **Desenvolvedor 1 (Frente 1):** Regras de limpeza com `pandas`, normalização léxica/estrutural, consulta à API de CEP com cache local (`CacheCEP`), geração de logs de auditoria e testes automatizados (`etl/tests.py`).
* **Desenvolvedor 2 (Frente 2):** Interface do Dashboard executivo, curadoria avançada no Django Admin (`etl/admin.py`), rotas de upload e exportação Excel (`.xlsx`) e estilização visual unificada.

---

## 📦 Guia de Deploy em Produção (Render)

Publicação automatizada no Render utilizando o script `build.sh`:
1. Defina a variável de ambiente `PYTHON_VERSION` = `3.14.0`.
2. **Build Command:** `bash build.sh`
3. **Start Command:** `uv run gunicorn config.wsgi:application`