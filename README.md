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
Para que duas pessoas desenvolvam o sistema em paralelo usando o **GitHub Desktop** sem gerar conflitos de código (*merge conflicts*), o projeto está organizado em uma **Fase Zero** (criação do esqueleto e banco de dados) seguida de **duas frentes de trabalho independentes**, onde cada integrante edita arquivos exclusivos.

### Divisão de Responsabilidades por Arquivo

| Integrante | Foco Principal | Arquivos Exclusivos | Entregáveis que Resolve |
| :--- | :--- | :--- | :--- |
| **Desenvolvedor 1** *(Motor ETL, Enriquecimento & Testes)* | Regras de limpeza com `pandas`, normalização Unicode (`NFKD`), consulta à API de CEP com cache local, geração da auditoria e testes automatizados com *mocks*. | • `etl/pipeline.py`<br>• `etl/management/commands/importar_clientes.py`<br>• `etl/tests.py` | • Pipeline de Extração, Transformação e Carga.<br>• Tratamento de bairros, CNPJ, telefone, e-mail, data e CEP.<br>• Testes unitários e de integração simulando a API externa (`unittest.mock`). |
| **Desenvolvedor 2** *(Governança, Admin, Dashboard & Excel)* | Interface administrativa de curadoria, upload de CSV pela web, exportação de relatórios em Excel (`.xlsx`), gráficos comparativos em `Chart.js` e documentação. | • `etl/admin.py`<br>• `etl/views.py`<br>• `etl/urls.py`<br>• `dashboard/views.py`<br>• `dashboard/urls.py`<br>• `dashboard/templates/dashboard/painel.html`<br>• `config/urls.py` | • Painel de auditoria e gestão do dicionário de bairros no Django Admin.<br>• Dashboard com gráficos *Antes vs. Depois*.<br>• Upload de arquivos e download da planilha auditada. |

### Cronograma de Execução em 4 Etapas

| Etapa | O que fazer | Quem executa |
| :--- | :--- | :--- |
| **Fase 0: Esqueleto Base** | Clonar o repositório, iniciar o `uv`, criar o projeto `config` e as apps `etl` e `dashboard`, configurar `.gitignore`, `settings.py` e `etl/models.py`, rodar `makemigrations` e `migrate` e fazer o primeiro *Push*. | **Desenvolvedor 1** *(Desenvolvedor 2 faz o Clone e roda `uv sync` + `migrate` logo em seguida)*. |
| **Etapa 1: Núcleo Funcional** | **Dev 1:** Cria `etl/pipeline.py` e o comando `importar_clientes.py`, testando a carga dos 47 clientes via terminal.<br>**Dev 2:** Configura `etl/admin.py` com filtros de auditoria e cria as rotas de upload e exportação Excel em `etl/views.py`. | **Ambos em paralelo** *(arquivos separados)*. |
| **Etapa 2: Visualização e Testes** | **Dev 1:** Escreve a suíte completa de testes em `etl/tests.py` usando `unittest.mock` para simular o ViaCEP offline.<br>**Dev 2:** Cria `dashboard/views.py` e `painel.html` com os cards de indicadores e gráficos comparativos em `Chart.js`. | **Ambos em paralelo** *(arquivos separados)*. |
| **Etapa 3: Revisão e Deploy** | Integrar as duas frentes via GitHub Desktop, revisar o Relatório de Trade-offs e publicar a aplicação no **Render**. |

## 2. Diagnóstico da Base Real (`clientes_distribuidora_vetor.csv`)

A inspeção da base fornecida para o desafio revelou **47 registros** distribuídos em **11 colunas** (`id_cliente`, `razao_social`, `cnpj`, `telefone`, `email`, `bairro_informado`, `cep`, `cidade`, `uf`, `data_cadastro` e `vendedor_responsavel`). Todos os 47 registros apresentam ao menos uma inconsistência (média de $2,74$ campos inconsistentes por cliente):

| Coluna | Problemas Encontrados nos 47 Registros | O que o `transformar()` faz |
| :--- | :--- | :--- |
| **`bairro_informado`** | **26 grafias diferentes** (incluindo 1 vazio no `CLI0047`), misturando maiúsculas/minúsculas, ausência de acentos, sufixos de UF (`"Taguatinga - DF"`, `"Águas Claras/DF"`), abreviações (`"V. Pires"`, `"Vte Pires"`) e subdivisões (`"Sul (Águas Claras)"`, `"Norte (Aguas Claras)"`, `"Guará I"`, `"Guará II"`). | Normaliza o texto via decomposição Unicode (`NFKD`), remove sufixos `- DF`/`/DF` e consulta o dicionário canônico para unificar nas **4 regiões oficiais**. |
| **`cep`** | **13 CEPs vazios**, **3 CEPs zerados** (`00000-000` em `CLI0005`, `CLI0039` e `CLI0040`) e **divergência geográfica real**: o cliente `CLI0002` informa `"Sul (Aguas Claras)"`, mas seu CEP (`72140-010`) pertence oficialmente a **Taguatinga**. | Descarta `00000-000`, formata `XXXXX-XXX`, consulta o `CacheCEP`/ViaCEP e corrige divergências priorizando o CEP oficial, marcando `DIVERGENCIA_CEP_CORRIGIDA`. |
| **`cnpj`** | Todos têm 14 dígitos numéricos (38 com máscara e 9 apenas números), gerados sinteticamente para o desafio. | Remove caracteres não numéricos via Regex, valida os 14 dígitos e padroniza na máscara `XX.XXX.XXX/XXXX-XX`. |
| **`telefone`** | **25 registros fora do padrão**, misturando DDI `+55` (13 dígitos), números colados sem espaço/hífen e fixos de 10 dígitos. | Remove o prefixo DDI `55` quando possui 12 ou 13 dígitos e aplica a máscara `(61) 9XXXX-XXXX` ou `(61) XXXX-XXXX`. |
| **`email`** | **10 e-mails possuem acentos ou cedilha** no domínio (ex.: `contato@comercialsão.com.br`, `contato@empóriochãov.com.br`), violando a RFC 5322. | Remove acentos via decomposição Unicode (`NFKD`) e converte tudo para minúsculas (`contato@comercialsao.com.br`). |
| **`data_cadastro`** | **4 formatos misturados**: ISO `YYYY-MM-DD` (23), barra `DD/MM/YYYY` (9), inglês `MMM DD, YYYY` como `Dec 24, 2023` e `jul 21, 2022` (8) e hífen `DD-MM-YYYY` (7). | Converte todos os formatos para o tipo `date` no padrão ISO (`YYYY-MM-DD`). |

### Consolidação dos Bairros (Antes $\rightarrow$ Depois)

Sem o pipeline, qualquer relatório comercial agrupado por bairro gerava **26 linhas fragmentadas**. Após o processamento pelo ETL:

| Bairro Canônico Final | Clientes (Após ETL) | Variantes Originais Agrupadas |
| :--- | :---: | :--- |
| **Águas Claras** | **21** | `Aguas claras`, `aguas claras`, `Águas Claras`, `AGUAS CLARAS`, `Sul (Águas Claras)`, `Sul (Aguas Claras)`, `Norte (Águas Claras)`, `Norte (Aguas Claras)`, `Águas Claras Norte`, `Águas Claras Sul`, `Águas Claras/DF`, `Aguas Claras - DF` |
| **Taguatinga** | **11** *(inclui `CLI0002` corrigido via CEP)* | `Taguatinga - DF`, `Taguatinga/DF`, `TAGUATINGA`, `Taguatinga`, `taguatinga sul` |
| **Vicente Pires** | **8** | `Vte Pires`, `Vicente Pires - DF`, `VICENTE PIRES`, `Vicente Pires`, `V. Pires` |
| **Guará** | **6** | `Guará II`, `Guará I`, `guara - df` |
| **Não Informado** | **1** (`CLI0047` em `REVISAO_MANUAL`) | Registro sem bairro informado e sem CEP |

---

## 3. Visão Geral dos Conceitos e Arquitetura

| Conceito | Para que serve neste projeto |
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
