# Pipeline ETL e Governança de Dados — Distribuidora Vetor (Primora)

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![uv](https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![openpyxl](https://img.shields.io/badge/openpyxl-217346?style=for-the-badge&logo=python&logoColor=white)](https://openpyxl.readthedocs.io/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com/)
[![VS Code](https://img.shields.io/badge/VS%20Code-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white)](https://code.visualstudio.com/)
[![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![PowerShell](https://img.shields.io/badge/PowerShell-5391FE?style=for-the-badge&logo=powershell&logoColor=white)](https://learn.microsoft.com/powershell/)

Um sistema completo de **ETL (Extração, Transformação e Carga)**, enriquecimento geográfico via API de CEP e governança de dados desenvolvido em **Python e Django**. O projeto recebe a base histórica de clientes B2B da **Distribuidora Vetor** (`clientes_distribuidora_vetor.csv`), corrige inconsistências cadastrais acumuladas ao longo dos anos, documenta cada decisão em uma tabela de auditoria e exibe os resultados em um **Dashboard Executivo** com gráficos comparativos (*Antes vs. Depois*).

O projeto é dividido em **duas apps independentes**:
* **`etl`**: Faz todo o trabalho de leitura do CSV bruto, limpeza textual, validação de CNPJ/telefone/e-mail/data, enriquecimento por CEP com cache local, gravação idempotente no banco, auditoria célula a célula e exportação para Excel.
* **`dashboard`**: Lê os modelos já tratados do banco e apresenta indicadores de qualidade, gráficos comparativos no navegador e o histórico de execuções e auditoria.

---

## Sumário

1. [Planejamento de Desenvolvimento em Dupla](#1-planejamento-de-desenvolvimento-em-dupla)
2. [Diagnóstico da Base Real (`clientes_distribuidora_vetor.csv`)](#2-diagnóstico-da-base-real-clientes_distribuidora_vetorcsv)
3. [Visão Geral dos Conceitos e Arquitetura](#3-visão-geral-dos-conceitos-e-arquitetura)
4. [Fase 0: Criar o Esqueleto Base do Projeto](#4-fase-0-criar-o-esqueleto-base-do-projeto)
5. [Frente 1: Motor ETL, Comando de Terminal e Testes (`etl`)](#5-frente-1-motor-etl-comando-de-terminal-e-testes-etl)
6. [Frente 2: Admin, Upload, Exportação Excel e Dashboard (`dashboard`)](#6-frente-2-admin-upload-exportação-excel-e-dashboard-dashboard)
7. [Relatório de Trade-offs e Limites Conhecidos](#7-relatório-de-trade-offs-e-limites-conhecidos)
8. [Estrutura Final de Pastas e Fluxo de Funcionamento](#8-estrutura-final-de-pastas-e-fluxo-de-funcionamento)
9. [Guia de Deploy no Render](#9-guia-de-deploy-no-render)

---

## 1. Planejamento de Desenvolvimento em Dupla

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
| **Etapa 3: Revisão e Deploy** | Integrar as duas frentes via GitHub Desktop, revisar o Relatório de Trade-offs e publicar a aplicação no **Render**. | **Dupla em conjunto**. |

### Regra de Ouro no GitHub Desktop para a Dupla

1. **Antes de começar a programar no dia:** Abra o **GitHub Desktop** e clique em **Fetch origin** (e em **Pull origin**, caso apareça atualização do colega).
2. **Durante o desenvolvimento:** Edite apenas os arquivos da sua frente listados na tabela acima.
3. **Ao concluir uma etapa:** Teste no terminal, abra o **GitHub Desktop**, escreva um resumo claro no campo *Summary* (ex.: `"Implementa pipeline ETL e comando importar_clientes"`), clique em **Commit to main** e depois em **Push origin**.

---

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
| **ETL (`pipeline.py`)** | Divide o fluxo em três funções isoladas: `extrair()`, `transformar()` e `carregar()` |
| **pandas (`DataFrame`)** | Lê o CSV bruto como texto (`dtype=str`) e estrutura os dados em memória |
| **Decomposição Unicode (`NFKD`)** | Separa acentos das letras para comparar `"Águas Claras"` e `"aguas claras"` de forma determinística |
| **`DicionarioBairro`** | Tabela no banco que traduz subdivisões informais (`"norte (aguas claras)"` $\rightarrow$ `"Águas Claras"`) |
| **`CacheCEP` + ViaCEP** | Consulta o CEP na internet apenas na primeira vez e guarda no SQLite, reduzindo chamadas de rede de $O(N)$ para $O(1)$ em CEPs repetidos |
| **`LogAuditoria`** | Grava o histórico completo de cada campo alterado: `valor_original` $\rightarrow$ `valor_tratado` $\rightarrow$ `criterio` |
| **`bulk_create(update_conflicts=True)`** | Garante **idempotência**: rodar o ETL duas vezes atualiza os clientes existentes sem duplicar linhas |
| **`transaction.atomic()`** | Garante que clientes e logs de auditoria sejam gravados juntos, ou nada é salvo se houver falha |
| **`unittest.mock`** | Simula a resposta da API de CEP nos testes automatizados para não depender de internet |
| **Chart.js + `json_script`** | Renderiza os gráficos comparativos no navegador com os dados agregados pelo ORM do Django |

### Por que duas apps?

| App | Responsabilidade | Sabe da outra? |
| :--- | :--- | :--- |
| **`etl`** | Modelos (`Cliente`, `Execucao`, `LogAuditoria`, `DicionarioBairro`, `CacheCEP`), `pipeline.py`, comando de terminal, Admin, upload e exportação Excel. | **Não.** Funciona sozinha pelo terminal. |
| **`dashboard`** | Uma página executiva que lê os modelos do `etl` e mostra indicadores, gráficos e tabelas de auditoria. | **Sim:** `from etl.models import Cliente, Execucao, LogAuditoria`. |

---

## 4. Fase 0: Criar o Esqueleto Base do Projeto

> **Atenção Dupla:** Esta Fase 0 deve ser executada por **apenas uma pessoa** (Desenvolvedor 1). Ao final dela, os arquivos são enviados ao GitHub e a segunda pessoa apenas clona o projeto pronto.

### 4.1. Clonar o repositório e iniciar o `uv`

1. Clone o repositório pelo **GitHub Desktop** (ex.: `C:\projetos\etl_vetor`) e clique em **Open in Visual Studio Code**.
2. Abra o terminal integrado do VS Code (`` Ctrl + ` ``) e verifique se o `uv` está instalado (`uv --version`). Caso não esteja:

```powershell
winget install --id=astral-sh.uv -e
```

3. Inicie o gerenciamento do projeto com `--bare` (para não sobrescrever o `README.md` existente) e instale os pacotes:

```powershell
uv init --bare
uv add django pandas openpyxl requests
```

| Pacote | Para que serve |
| :--- | :--- |
| `django` | Banco de dados (ORM), painel administrativo, comandos de terminal e páginas web |
| `pandas` | Leitura e manipulação tabular do CSV |
| `openpyxl` | Motor usado pelo `pandas` para gerar planilhas Excel (`.xlsx`) |
| `requests` | Consulta HTTP à API pública de CEP (ViaCEP) |

### 4.2. Criar o projeto Django e as apps

```powershell
uv run django-admin startproject config .
uv run python manage.py startapp etl
uv run python manage.py startapp dashboard
```

No VS Code, pressione `Ctrl + Shift + P` > **Python: Select Interpreter** > escolha `.\.venv\Scripts\python.exe`.

### 4.3. Criar o `.gitignore` e a pasta `dados`

Na raiz do projeto (ao lado do `manage.py`), crie o arquivo `.gitignore`:

```text
.venv/
__pycache__/
db.sqlite3
etl.log
```

Crie a pasta `dados` na raiz do projeto e coloque o arquivo `clientes_distribuidora_vetor.csv` dentro dela (`dados/clientes_distribuidora_vetor.csv`).

### 4.4. Configurar `config/settings.py`

Abra `config/settings.py`, registre as duas apps em `INSTALLED_APPS`, configure o idioma/fuso horário brasileiro e adicione a tag de erro do Bootstrap no final do arquivo:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'etl',        # <- motor ETL, modelos e auditoria
    'dashboard',  # <- painel visual e gráficos
]

# ... (mantenha o restante do arquivo e altere idioma e fuso horário)

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

# ... (adicione no final do arquivo)
from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {message_constants.ERROR: "danger"}
```

### 4.5. Criar os modelos em `etl/models.py`

Abra `etl/models.py` e substitua todo o conteúdo por:

```python
from django.db import models


class Cliente(models.Model):
    id_cliente = models.CharField(max_length=20, unique=True)
    razao_social = models.CharField(max_length=150)
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(max_length=150)
    bairro_informado = models.CharField(max_length=100, blank=True)
    bairro_tratado = models.CharField(max_length=100)
    cep = models.CharField(max_length=9, blank=True)
    cidade = models.CharField(max_length=60)
    uf = models.CharField(max_length=2)
    data_cadastro = models.DateField()
    vendedor_responsavel = models.CharField(max_length=100)
    status_validacao = models.CharField(max_length=40, default="VALIDADO")

    class Meta:
        ordering = ["id_cliente"]

    def __str__(self):
        return f"{self.id_cliente} - {self.razao_social} ({self.bairro_tratado})"


class Execucao(models.Model):
    iniciada_em = models.DateTimeField(auto_now_add=True)
    arquivo = models.CharField(max_length=255)
    lidas = models.PositiveIntegerField(default=0)
    carregadas = models.PositiveIntegerField(default=0)
    descartadas = models.PositiveIntegerField(default=0)
    em_revisao = models.PositiveIntegerField(default=0)
    sucesso = models.BooleanField(default=False)
    mensagem = models.TextField(blank=True)

    class Meta:
        ordering = ["-iniciada_em"]
        verbose_name = "execução"
        verbose_name_plural = "execuções"

    def __str__(self):
        return f"{self.iniciada_em:%d/%m/%Y %H:%M} - {self.arquivo}"


class LogAuditoria(models.Model):
    execucao = models.ForeignKey(Execucao, on_delete=models.CASCADE, related_name="logs")
    id_cliente = models.CharField(max_length=20)
    campo = models.CharField(max_length=50)
    valor_original = models.TextField(blank=True, null=True)
    valor_tratado = models.TextField(blank=True, null=True)
    criterio = models.CharField(max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id_cliente", "campo"]
        verbose_name = "log de auditoria"
        verbose_name_plural = "logs de auditoria"

    def __str__(self):
        return f"{self.id_cliente} [{self.campo}]: {self.valor_original} -> {self.valor_tratado}"


class DicionarioBairro(models.Model):
    variante_normalizada = models.CharField(max_length=100, unique=True)
    nome_canonico = models.CharField(max_length=100)

    class Meta:
        ordering = ["nome_canonico", "variante_normalizada"]
        verbose_name = "dicionário de bairro"
        verbose_name_plural = "dicionário de bairros"

    def __str__(self):
        return f"{self.variante_normalizada} -> {self.nome_canonico}"


class CacheCEP(models.Model):
    cep = models.CharField(max_length=9, unique=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=60, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    fonte = models.CharField(max_length=50, default="ViaCEP")
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "cache de CEP"
        verbose_name_plural = "cache de CEPs"

    def __str__(self):
        return f"{self.cep} -> {self.bairro}"
```

| Modelo / Campo | Função no Sistema |
| :--- | :--- |
| `Cliente.id_cliente` (`unique=True`) | Chave única de negócio (`CLI0001` a `CLI0047`) usada para atualizar registros sem duplicar |
| `bairro_informado` vs. `bairro_tratado` | Preserva o texto original ao lado do bairro canônico limpo para permitir comparações e gráficos *Antes vs. Depois* |
| `status_validacao` | Classifica cada registro em `VALIDADO`, `VALIDADO_SEM_CEP`, `DIVERGENCIA_CEP_CORRIGIDA` ou `REVISAO_MANUAL` |
| `Execucao` | Diário de bordo de cada rodada do pipeline (quantas linhas foram lidas, carregadas, enviadas para revisão ou descartadas) |
| `LogAuditoria` | Rastreabilidade exigida pela empresa: registra cliente, campo, valor antigo, valor novo e a regra exata aplicada |
| `DicionarioBairro` | Permite adicionar novas variantes de bairros pelo painel Admin sem alterar código |
| `CacheCEP` | Armazena localmente o retorno da API de CEP para evitar chamadas repetidas na internet |

### 4.6. Criar as migrações e sincronizar a dupla

Rode no terminal:

```powershell
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

1. No **GitHub Desktop**, faça o commit (`"Fase 0: estrutura inicial e models"`) e clique em **Push origin**.
2. **Na máquina da dupla (Desenvolvedor 2):** Clone o repositório pelo GitHub Desktop e rode no terminal:

```powershell
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

---

## 5. Frente 1: Motor ETL, Comando de Terminal e Testes (`etl`)

> **Responsável:** Desenvolvedor 1.

### 5.1. Criar o Pipeline (`etl/pipeline.py`)

Crie o arquivo `etl/pipeline.py` com o código abaixo:

```python
import re
import unicodedata
from datetime import datetime

import pandas as pd
import requests
from django.db import transaction

from .models import CacheCEP, Cliente, DicionarioBairro, Execucao, LogAuditoria

COLUNAS_OBRIGATORIAS = [
    "id_cliente", "razao_social", "cnpj", "telefone", "email",
    "bairro_informado", "cep", "cidade", "uf", "data_cadastro", "vendedor_responsavel"
]

MAPA_BAIRROS_PADRAO = {
    "aguas claras": "Águas Claras",
    "sul (aguas claras)": "Águas Claras",
    "norte (aguas claras)": "Águas Claras",
    "aguas claras norte": "Águas Claras",
    "aguas claras sul": "Águas Claras",
    "taguatinga": "Taguatinga",
    "taguatinga sul": "Taguatinga",
    "taguatinga norte": "Taguatinga",
    "vicente pires": "Vicente Pires",
    "vte pires": "Vicente Pires",
    "v. pires": "Vicente Pires",
    "v pires": "Vicente Pires",
    "guara": "Guará",
    "guara i": "Guará",
    "guara ii": "Guará",
}

MESES_PT_EN = {
    "jan": "01", "feb": "02", "fev": "02", "mar": "03", "apr": "04", "abr": "04",
    "may": "05", "mai": "05", "jun": "06", "jul": "07", "aug": "08", "ago": "08",
    "sep": "09", "set": "09", "oct": "10", "out": "10", "nov": "11", "dec": "12", "dez": "12"
}


def remover_acentos(texto):
    """Decompõe caracteres acentuados (NFKD) e remove marcas de acentuação."""
    if not isinstance(texto, str):
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar_chave_bairro(texto):
    """Converte para minúsculas, remove acentos, sufixos '- DF' ou '/DF' e espaços extras."""
    limpo = remover_acentos(str(texto or "")).lower().strip()
    limpo = re.sub(r"\s*[-/]\s*df$", "", limpo)
    limpo = re.sub(r"\s+", " ", limpo)
    return limpo


def limpar_cnpj(valor):
    """Extrai apenas dígitos e aplica a máscara XX.XXX.XXX/XXXX-XX se tiver 14 números."""
    digitos = re.sub(r"\D", "", str(valor or ""))
    if len(digitos) == 14:
        return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
    return None


def limpar_telefone(valor):
    """Remove DDI +55 e formata telefones fixos (10 dígitos) e móveis (11 dígitos)."""
    digitos = re.sub(r"\D", "", str(valor or ""))
    if digitos.startswith("55") and len(digitos) in (12, 13):
        digitos = digitos[2:]
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return str(valor or "").strip()


def limpar_email(valor):
    """Remove acentos ilegais em domínios de e-mail e padroniza em minúsculas."""
    return remover_acentos(str(valor or "")).strip().lower()


def limpar_cep(valor):
    """Anula CEPs vazios ou zerados (00000-000) e formata como XXXXX-XXX."""
    if pd.isna(valor):
        return ""
    digitos = re.sub(r"\D", "", str(valor))
    if len(digitos) != 8 or digitos == "00000000":
        return ""
    return f"{digitos[:5]}-{digitos[5:]}"


def converter_data(valor):
    """Converte datas nos formatos YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY e 'MMM DD, YYYY'."""
    texto = str(valor or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            pass
    m = re.match(r"^([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})$", texto)
    if m:
        mes_str, dia, ano = m.groups()
        mes = MESES_PT_EN.get(mes_str.lower())
        if mes:
            return datetime.strptime(f"{ano}-{mes}-{int(dia):02d}", "%Y-%m-%d").date()
    return None


def consultar_cep_com_cache(cep_formatado):
    """Busca o CEP no CacheCEP local; se não existir, consulta o ViaCEP e salva no banco."""
    if not cep_formatado:
        return ""
    cache = CacheCEP.objects.filter(cep=cep_formatado).first()
    if cache:
        return cache.bairro

    digitos = cep_formatado.replace("-", "")
    bairro_api = ""
    try:
        resp = requests.get(f"https://viacep.com.br/ws/{digitos}/json/", timeout=3)
        if resp.status_code == 200 and not resp.json().get("erro"):
            dados = resp.json()
            bairro_api = dados.get("bairro", "")
            CacheCEP.objects.update_or_create(
                cep=cep_formatado,
                defaults={
                    "bairro": bairro_api,
                    "cidade": dados.get("localidade", "Brasília"),
                    "uf": dados.get("uf", "DF"),
                    "fonte": "ViaCEP",
                },
            )
    except Exception:
        if digitos.startswith("719"):
            bairro_api = "Águas Claras"
        elif digitos.startswith("720"):
            bairro_api = "Vicente Pires"
        elif digitos.startswith("721"):
            bairro_api = "Taguatinga"

    return bairro_api


def extrair(arquivo):
    """E: lê o CSV do jeito que veio, tudo como texto (dtype=str)."""
    return pd.read_csv(arquivo, sep=";", dtype=str, encoding="utf-8")


def transformar(df):
    """T: limpa os campos, cruza bairro com CEP e gera a lista de auditoria."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    faltando = set(COLUNAS_OBRIGATORIAS) - set(df.columns)
    if faltando:
        raise ValueError(f"Colunas faltando no CSV: {', '.join(sorted(faltando))}")

    mapa_bairros = dict(MAPA_BAIRROS_PADRAO)
    for item in DicionarioBairro.objects.all():
        mapa_bairros[normalizar_chave_bairro(item.variante_normalizada)] = item.nome_canonico

    registros_limpos = []
    logs_auditoria = []

    for _, linha in df.iterrows():
        id_cli = str(linha["id_cliente"]).strip()

        # 1. CNPJ
        cnpj_orig = str(linha["cnpj"]).strip()
        cnpj_limpo = limpar_cnpj(cnpj_orig)
        if not cnpj_limpo:
            continue
        if cnpj_orig != cnpj_limpo:
            logs_auditoria.append({
                "id_cliente": id_cli, "campo": "cnpj",
                "valor_original": cnpj_orig, "valor_tratado": cnpj_limpo,
                "criterio": "Padronização de máscara de CNPJ (14 dígitos)"
            })

        # 2. Telefone
        tel_orig = str(linha["telefone"]).strip()
        tel_limpo = limpar_telefone(tel_orig)
        if tel_orig != tel_limpo:
            logs_auditoria.append({
                "id_cliente": id_cli, "campo": "telefone",
                "valor_original": tel_orig, "valor_tratado": tel_limpo,
                "criterio": "Remoção de DDI +55 e aplicação de máscara nacional"
            })

        # 3. E-mail
        email_orig = str(linha["email"]).strip()
        email_limpo = limpar_email(email_orig)
        if email_orig != email_limpo:
            logs_auditoria.append({
                "id_cliente": id_cli, "campo": "email",
                "valor_original": email_orig, "valor_tratado": email_limpo,
                "criterio": "Remoção de acentuação gráfica (Padrão RFC 5322)"
            })

        # 4. Data de Cadastro
        data_orig = str(linha["data_cadastro"]).strip()
        data_limpa = converter_data(data_orig)
        if not data_limpa:
            continue
        if data_orig != data_limpa.isoformat():
            logs_auditoria.append({
                "id_cliente": id_cli, "campo": "data_cadastro",
                "valor_original": data_orig, "valor_tratado": data_limpa.isoformat(),
                "criterio": "Conversão multiformato para padrão ISO 8601 (YYYY-MM-DD)"
            })

        # 5. CEP
        cep_orig = "" if pd.isna(linha["cep"]) else str(linha["cep"]).strip()
        cep_limpo = limpar_cep(linha["cep"])
        if cep_orig != cep_limpo:
            logs_auditoria.append({
                "id_cliente": id_cli, "campo": "cep",
                "valor_original": cep_orig or "VAZIO", "valor_tratado": cep_limpo or "AUSENTE",
                "criterio": "Descarte de CEP inválido (00000-000) ou ausente"
            })

        # 6. Bairro e Resolução de Conflito com CEP
        bairro_orig = "" if pd.isna(linha["bairro_informado"]) else str(linha["bairro_informado"]).strip()
        chave_bairro = normalizar_chave_bairro(bairro_orig)
        bairro_por_texto = mapa_bairros.get(chave_bairro, "")

        bairro_api = consultar_cep_com_cache(cep_limpo)
        bairro_por_cep = mapa_bairros.get(normalizar_chave_bairro(bairro_api), "")

        status_val = "VALIDADO"
        if bairro_por_texto and bairro_por_cep and bairro_por_texto != bairro_por_cep:
            bairro_final = bairro_por_cep
            status_val = "DIVERGENCIA_CEP_CORRIGIDA"
            criterio_bairro = (
                f"Conflito resolvido via CEP ({cep_limpo}): texto indicava "
                f"'{bairro_por_texto}', mas CEP pertence a '{bairro_por_cep}'"
            )
        elif bairro_por_texto:
            bairro_final = bairro_por_texto
            criterio_bairro = "Normalização Unicode (NFKD) + Dicionário Canônico"
            if not cep_limpo:
                status_val = "VALIDADO_SEM_CEP"
        elif bairro_por_cep:
            bairro_final = bairro_por_cep
            criterio_bairro = f"Imputado via consulta de CEP ({cep_limpo})"
        else:
            bairro_final = "Não Informado"
            status_val = "REVISAO_MANUAL"
            criterio_bairro = "Ausência de bairro e CEP: enviado para curadoria manual"

        if bairro_orig != bairro_final:
            logs_auditoria.append({
                "id_cliente": id_cli, "campo": "bairro_informado",
                "valor_original": bairro_orig or "VAZIO", "valor_tratado": bairro_final,
                "criterio": criterio_bairro
            })

        registros_limpos.append({
            "id_cliente": id_cli,
            "razao_social": str(linha["razao_social"]).strip(),
            "cnpj": cnpj_limpo,
            "telefone": tel_limpo,
            "email": email_limpo,
            "bairro_informado": bairro_orig or "VAZIO",
            "bairro_tratado": bairro_final,
            "cep": cep_limpo,
            "cidade": str(linha["cidade"]).strip(),
            "uf": str(linha["uf"]).strip().upper(),
            "data_cadastro": data_limpa,
            "vendedor_responsavel": str(linha["vendedor_responsavel"]).strip(),
            "status_validacao": status_val,
        })

    return pd.DataFrame(registros_limpos), logs_auditoria


def carregar(df_limpo, logs_auditoria, execucao):
    """L: grava clientes e logs no banco dentro de uma transação atômica."""
    clientes = [
        Cliente(
            id_cliente=row.id_cliente,
            razao_social=row.razao_social,
            cnpj=row.cnpj,
            telefone=row.telefone,
            email=row.email,
            bairro_informado=row.bairro_informado,
            bairro_tratado=row.bairro_tratado,
            cep=row.cep,
            cidade=row.cidade,
            uf=row.uf,
            data_cadastro=row.data_cadastro,
            vendedor_responsavel=row.vendedor_responsavel,
            status_validacao=row.status_validacao,
        )
        for row in df_limpo.itertuples(index=False)
    ]

    with transaction.atomic():
        Cliente.objects.bulk_create(
            clientes,
            update_conflicts=True,
            unique_fields=["id_cliente"],
            update_fields=[
                "razao_social", "cnpj", "telefone", "email", "bairro_informado",
                "bairro_tratado", "cep", "cidade", "uf", "data_cadastro",
                "vendedor_responsavel", "status_validacao"
            ],
        )
        objs_log = [LogAuditoria(execucao=execucao, **log) for log in logs_auditoria]
        LogAuditoria.objects.bulk_create(objs_log)

    return len(clientes)


def executar(arquivo, nome):
    """Roda E, T e L em sequência e grava a execução no banco."""
    execucao = Execucao.objects.create(arquivo=nome)
    try:
        bruto = extrair(arquivo)
        limpo, logs = transformar(bruto)
        execucao.lidas = len(bruto)
        execucao.carregadas = carregar(limpo, logs, execucao)
        execucao.descartadas = execucao.lidas - execucao.carregadas
        execucao.em_revisao = (
            int((limpo["status_validacao"] == "REVISAO_MANUAL").sum())
            if not limpo.empty else 0
        )
        execucao.sucesso = True
        execucao.mensagem = f"Concluída sem erros. {len(logs)} transformações auditadas."
    except Exception as erro:
        execucao.sucesso = False
        execucao.mensagem = f"{type(erro).__name__}: {erro}"
    execucao.save()
    return execucao
```

### 5.2. Criar o Comando de Gerenciamento (`importar_clientes.py`)

No terminal do VS Code, crie as pastas e os arquivos do comando:

```powershell
mkdir etl\management\commands
New-Item etl\management\__init__.py
New-Item etl\management\commands\__init__.py
New-Item etl\management\commands\importar_clientes.py
```

Em `etl/management/commands/importar_clientes.py`:

```python
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from etl.pipeline import executar


class Command(BaseCommand):
    help = "Importa um CSV de clientes da Distribuidora Vetor (extrair, transformar, carregar)."

    def add_arguments(self, parser):
        parser.add_argument(
            "arquivo",
            help="Caminho do CSV, ex.: dados/clientes_distribuidora_vetor.csv",
        )

    def handle(self, *args, **opcoes):
        caminho = Path(opcoes["arquivo"])
        if not caminho.exists():
            raise CommandError(f"Arquivo não encontrado: {caminho}")

        execucao = executar(caminho, caminho.name)

        if not execucao.sucesso:
            raise CommandError(execucao.mensagem)

        self.stdout.write(
            self.style.SUCCESS(
                f"Lidas: {execucao.lidas} | Carregadas: {execucao.carregadas} | "
                f"Em Revisão: {execucao.em_revisao} | Descartadas: {execucao.descartadas} | "
                f"{execucao.mensagem}"
            )
        )
```

Teste o pipeline no terminal:

```powershell
uv run python manage.py importar_clientes dados/clientes_distribuidora_vetor.csv
```

Saída esperada em verde:

```text
Lidas: 47 | Carregadas: 47 | Em Revisão: 1 | Descartadas: 0 | Concluída sem erros. 129 transformações auditadas.
```

### 5.3. Criar os Testes Automatizados com Mocks (`etl/tests.py`)

Abra `etl/tests.py` e substitua o conteúdo por:

```python
from datetime import date
from io import StringIO
from unittest.mock import MagicMock, patch

from django.test import TestCase

from .models import CacheCEP, Cliente, DicionarioBairro, LogAuditoria
from .pipeline import (
    converter_data,
    executar,
    limpar_cep,
    limpar_cnpj,
    limpar_email,
    limpar_telefone,
    normalizar_chave_bairro,
)


class NormalizacaoUnitariaTests(TestCase):
    def test_normalizar_chave_bairro_remove_acentos_e_uf(self):
        self.assertEqual(normalizar_chave_bairro("Águas Claras/DF"), "aguas claras")
        self.assertEqual(normalizar_chave_bairro("  Taguatinga - DF "), "taguatinga")
        self.assertEqual(normalizar_chave_bairro("Sul (Águas Claras)"), "sul (aguas claras)")

    def test_limpar_cnpj_aplica_mascara(self):
        self.assertEqual(limpar_cnpj("27868011280598"), "27.868.011/2805-98")
        self.assertEqual(limpar_cnpj("84.959.310/3413-16"), "84.959.310/3413-16")
        self.assertIsNone(limpar_cnpj("123"))

    def test_limpar_telefone_remove_ddi_e_formata(self):
        self.assertEqual(limpar_telefone("+55 61 95386-2084"), "(61) 95386-2084")
        self.assertEqual(limpar_telefone("61970855700"), "(61) 97085-5700")
        self.assertEqual(limpar_telefone("61 3970-2193"), "(61) 3970-2193")

    def test_limpar_email_remove_acentos(self):
        self.assertEqual(
            limpar_email("Contato@ComercialSão.com.br"),
            "contato@comercialsao.com.br",
        )

    def test_limpar_cep_descarta_zerado_ou_vazio(self):
        self.assertEqual(limpar_cep("00000-000"), "")
        self.assertEqual(limpar_cep(None), "")
        self.assertEqual(limpar_cep("71926750"), "71926-750")

    def test_converter_data_multiformato(self):
        self.assertEqual(converter_data("2022-06-21"), date(2022, 6, 21))
        self.assertEqual(converter_data("28/02/2022"), date(2022, 2, 28))
        self.assertEqual(converter_data("08-01-2022"), date(2022, 1, 8))
        self.assertEqual(converter_data("Dec 24, 2023"), date(2023, 12, 24))
        self.assertEqual(converter_data("jul 21, 2022"), date(2022, 7, 21))


class PipelineIntegracaoMockTests(TestCase):
    @patch("etl.pipeline.requests.get")
    def test_pipeline_resolve_conflito_cep_e_gera_auditoria_sem_internet(self, mock_get):
        resposta_falsa = MagicMock()
        resposta_falsa.status_code = 200
        resposta_falsa.json.return_value = {
            "cep": "72140-010",
            "bairro": "Taguatinga Norte",
            "localidade": "Brasília",
            "uf": "DF",
        }
        mock_get.return_value = resposta_falsa

        csv_simulado = (
            "id_cliente;razao_social;cnpj;telefone;email;bairro_informado;cep;cidade;uf;data_cadastro;vendedor_responsavel\n"
            "CLI0002;Comercial São Judas;28327648350305;+55 61 95386-2084;contato@comercialsão.com.br;Sul (Aguas Claras);72140-010;Brasília;DF;Dec 24, 2023;Camila Torres\n"
            "CLI0047;Mercadinho Sem Endereço;82.675.869/2617-96;61914391105;contato@semendereco.com.br;;;Brasília;DF;2022-06-23;Juliana Reis\n"
        )

        execucao = executar(StringIO(csv_simulado), "teste_mock.csv")

        self.assertTrue(execucao.sucesso)
        self.assertEqual(execucao.lidas, 2)
        self.assertEqual(execucao.carregadas, 2)
        self.assertEqual(execucao.em_revisao, 1)
        self.assertEqual(mock_get.call_count, 1)
        self.assertTrue(CacheCEP.objects.filter(cep="72140-010").exists())

        cli2 = Cliente.objects.get(id_cliente="CLI0002")
        self.assertEqual(cli2.bairro_tratado, "Taguatinga")
        self.assertEqual(cli2.status_validacao, "DIVERGENCIA_CEP_CORRIGIDA")
        self.assertEqual(cli2.cnpj, "28.327.648/3503-05")
        self.assertEqual(cli2.email, "contato@comercialsao.com.br")

        cli47 = Cliente.objects.get(id_cliente="CLI0047")
        self.assertEqual(cli47.bairro_tratado, "Não Informado")
        self.assertEqual(cli47.status_validacao, "REVISAO_MANUAL")

        campos_auditados = set(
            LogAuditoria.objects.filter(id_cliente="CLI0002").values_list("campo", flat=True)
        )
        self.assertSetEqual(
            campos_auditados,
            {"cnpj", "telefone", "email", "data_cadastro", "bairro_informado"},
        )

    @patch("etl.pipeline.requests.get")
    def test_dicionario_dinamico_do_banco_sobrescreve_variante(self, mock_get):
        DicionarioBairro.objects.create(
            variante_normalizada="setor habitacional sol nascente",
            nome_canonico="Sol Nascente",
        )
        csv_simulado = (
            "id_cliente;razao_social;cnpj;telefone;email;bairro_informado;cep;cidade;uf;data_cadastro;vendedor_responsavel\n"
            "CLI0099;Mercado Sol;28.327.648/3503-05;(61) 98433-1053;ok@ok.com.br;Setor Habitacional Sol Nascente;;Brasília;DF;2023-10-07;Bruno\n"
        )
        executar(StringIO(csv_simulado), "teste_dic.csv")
        cli = Cliente.objects.get(id_cliente="CLI0099")
        self.assertEqual(cli.bairro_tratado, "Sol Nascente")
        mock_get.assert_not_called()
```

Para executar os testes automatizados no terminal:

```powershell
uv run python manage.py test
```

---

## 6. Frente 2: Admin, Upload, Exportação Excel e Dashboard (`dashboard`)

> **Responsável:** Desenvolvedor 2.

### 6.1. Configurar o Painel de Governança no Admin (`etl/admin.py`)

Abra `etl/admin.py` e substitua o conteúdo por:

```python
from django.contrib import admin

from .models import CacheCEP, Cliente, DicionarioBairro, Execucao, LogAuditoria


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        "id_cliente", "razao_social", "cnpj", "telefone",
        "bairro_informado", "bairro_tratado", "cep", "status_validacao", "vendedor_responsavel"
    ]
    list_filter = ["bairro_tratado", "status_validacao", "vendedor_responsavel"]
    search_fields = ["id_cliente", "razao_social", "cnpj", "bairro_informado"]


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ["id_cliente", "campo", "valor_original", "valor_tratado", "criterio", "execucao"]
    list_filter = ["campo", "criterio", "execucao"]
    search_fields = ["id_cliente", "valor_original", "valor_tratado"]


@admin.register(DicionarioBairro)
class DicionarioBairroAdmin(admin.ModelAdmin):
    list_display = ["variante_normalizada", "nome_canonico"]
    list_filter = ["nome_canonico"]
    search_fields = ["variante_normalizada", "nome_canonico"]


@admin.register(CacheCEP)
class CacheCEPAdmin(admin.ModelAdmin):
    list_display = ["cep", "bairro", "cidade", "uf", "fonte", "atualizado_em"]
    search_fields = ["cep", "bairro"]


@admin.register(Execucao)
class ExecucaoAdmin(admin.ModelAdmin):
    list_display = ["iniciada_em", "arquivo", "lidas", "carregadas", "em_revisao", "descartadas", "sucesso"]
```

### 6.2. Criar Upload de CSV e Exportação Excel (`etl/views.py` e `etl/urls.py`)

Abra `etl/views.py` e substitua o conteúdo por:

```python
from io import BytesIO

import pandas as pd
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .models import Cliente, LogAuditoria
from .pipeline import executar

TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@require_POST
def importar(request):
    arquivo = request.FILES.get("arquivo")
    if arquivo is None:
        messages.error(request, "Escolha um arquivo CSV para importar.")
        return redirect("dashboard")

    execucao = executar(arquivo, arquivo.name)

    if execucao.sucesso:
        messages.success(
            request,
            f"{execucao.carregadas} clientes processados com sucesso "
            f"({execucao.em_revisao} em revisão manual). {execucao.mensagem}",
        )
    else:
        messages.error(request, f"Falha no ETL: {execucao.mensagem}")
    return redirect("dashboard")


def exportar(request):
    clientes = pd.DataFrame(
        Cliente.objects.values(
            "id_cliente", "razao_social", "cnpj", "telefone", "email",
            "bairro_informado", "bairro_tratado", "cep", "cidade", "uf",
            "data_cadastro", "vendedor_responsavel", "status_validacao"
        )
    )
    por_bairro = pd.DataFrame(
        Cliente.objects.values("bairro_tratado")
        .annotate(total_clientes=Count("id"))
        .order_by("-total_clientes")
    )
    auditoria = pd.DataFrame(
        LogAuditoria.objects.values(
            "id_cliente", "campo", "valor_original", "valor_tratado", "criterio"
        )
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer) as planilha:
        clientes.to_excel(planilha, sheet_name="Clientes Tratados", index=False)
        por_bairro.to_excel(planilha, sheet_name="Resumo por Bairro", index=False)
        auditoria.to_excel(planilha, sheet_name="Log de Auditoria", index=False)

    resposta = HttpResponse(buffer.getvalue(), content_type=TIPO_XLSX)
    resposta["Content-Disposition"] = 'attachment; filename="clientes_vetor_tratados.xlsx"'
    return resposta
```

Crie o arquivo `etl/urls.py`:

```python
from django.urls import path

from . import views

urlpatterns = [
    path("importar/", views.importar, name="importar"),
    path("exportar/", views.exportar, name="exportar"),
]
```

### 6.3. Criar a View e as Rotas do Dashboard (`dashboard/views.py`, `dashboard/urls.py` e `config/urls.py`)

Abra `dashboard/views.py` e substitua o conteúdo por:

```python
from django.db.models import Count, Q, Sum
from django.shortcuts import render

from etl.models import Cliente, Execucao, LogAuditoria


def painel(request):
    resumo_clientes = Cliente.objects.aggregate(
        total=Count("id"),
        bairros_antes=Count("bairro_informado", distinct=True),
        bairros_depois=Count("bairro_tratado", distinct=True),
        divergencias_cep=Count("id", filter=Q(status_validacao="DIVERGENCIA_CEP_CORRIGIDA")),
        em_revisao=Count("id", filter=Q(status_validacao="REVISAO_MANUAL")),
    )

    execucoes = Execucao.objects.aggregate(
        total=Count("id"),
        falhas=Count("id", filter=Q(sucesso=False)),
        lidas=Sum("lidas"),
        carregadas=Sum("carregadas"),
    )
    total_logs = LogAuditoria.objects.count()

    por_bairro_limpo = (
        Cliente.objects.values("bairro_tratado")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    por_campo_auditado = (
        LogAuditoria.objects.values("campo")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    ultimas_execucoes = list(Execucao.objects.all()[:10])
    ultimos_logs = list(LogAuditoria.objects.all()[:20])

    graficos = {
        "bairros": {
            "rotulos": [item["bairro_tratado"] for item in por_bairro_limpo],
            "valores": [item["total"] for item in por_bairro_limpo],
        },
        "auditoria": {
            "rotulos": [item["campo"] for item in por_campo_auditado],
            "valores": [item["total"] for item in por_campo_auditado],
        },
    }

    contexto = {
        "clientes": resumo_clientes,
        "execucoes": execucoes,
        "total_logs": total_logs,
        "ultimas": ultimas_execucoes,
        "ultimos_logs": ultimos_logs,
        "graficos": graficos,
    }
    return render(request, "dashboard/painel.html", contexto)
```

Crie o arquivo `dashboard/urls.py`:

```python
from django.urls import path

from . import views

urlpatterns = [
    path("", views.painel, name="dashboard"),
]
```

Atualize `config/urls.py` para conectar o Admin, o `etl` e o `dashboard`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("etl/", include("etl.urls")),
    path("", include("dashboard.urls")),
]
```

### 6.4. Criar o Template do Dashboard (`dashboard/templates/dashboard/painel.html`)

No terminal do VS Code, crie a estrutura de pastas do template:

```powershell
mkdir dashboard\templates\dashboard
New-Item dashboard\templates\dashboard\painel.html
```

Em `dashboard/templates/dashboard/painel.html`:

```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard ETL — Distribuidora Vetor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-body-tertiary">
<main class="container py-4">
    <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-2">
        <div>
            <h1 class="h3 mb-0">Governança e Saneamento de Dados — Distribuidora Vetor</h1>
            <p class="text-secondary small mb-0">Pipeline ETL de padronização, enriquecimento por CEP e rastreabilidade</p>
        </div>
        <div class="d-flex gap-2">
            <a href="/admin/" class="btn btn-outline-secondary">Painel Admin / Curadoria</a>
            <a href="{% url 'exportar' %}" class="btn btn-success">Exportar Excel (.xlsx)</a>
        </div>
    </div>

    {% for message in messages %}
        <div class="alert alert-{{ message.tags }}">{{ message }}</div>
    {% endfor %}

    <form method="post" action="{% url 'importar' %}" enctype="multipart/form-data"
          class="card card-body shadow-sm mb-4">
        {% csrf_token %}
        <label for="arquivo" class="form-label fw-semibold">Importar base CSV da Distribuidora Vetor</label>
        <div class="input-group">
            <input type="file" name="arquivo" id="arquivo" accept=".csv" class="form-control">
            <button class="btn btn-primary">Executar Pipeline ETL</button>
        </div>
    </form>

    <div class="row row-cols-1 row-cols-sm-2 row-cols-lg-4 g-3 mb-4">
        <div class="col">
            <div class="card shadow-sm h-100"><div class="card-body">
                <div class="text-secondary small">Clientes na Base Limpa</div>
                <div class="fs-4 fw-semibold">{{ clientes.total|default:0 }}</div>
                <div class="small text-secondary">
                    {{ clientes.em_revisao|default:0 }} em revisão manual
                </div>
            </div></div>
        </div>
        <div class="col">
            <div class="card shadow-sm h-100"><div class="card-body">
                <div class="text-secondary small">Consolidação de Bairros</div>
                <div class="fs-4 fw-semibold">{{ clientes.bairros_antes|default:0 }} &rarr; {{ clientes.bairros_depois|default:0 }}</div>
                <div class="small text-success">
                    variações reduzidas para regiões oficiais
                </div>
            </div></div>
        </div>
        <div class="col">
            <div class="card shadow-sm h-100"><div class="card-body">
                <div class="text-secondary small">Transformações Auditadas</div>
                <div class="fs-4 fw-semibold">{{ total_logs|default:0 }}</div>
                <div class="small text-secondary">
                    {{ clientes.divergencias_cep|default:0 }} conflitos de CEP corrigidos
                </div>
            </div></div>
        </div>
        <div class="col">
            <div class="card shadow-sm h-100"><div class="card-body">
                <div class="text-secondary small">Execuções do Pipeline</div>
                <div class="fs-4 fw-semibold">{{ execucoes.total|default:0 }}</div>
                <div class="small {% if execucoes.falhas %}text-danger{% else %}text-secondary{% endif %}">
                    {{ execucoes.falhas|default:0 }} com erro
                </div>
            </div></div>
        </div>
    </div>

    <div class="row g-3 mb-4">
        <div class="col-lg-6">
            <div class="card shadow-sm h-100">
                <div class="card-header fw-semibold">Clientes por Bairro Canônico (Após Tratamento)</div>
                <div class="card-body"><canvas id="grafico-bairros"></canvas></div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="card shadow-sm h-100">
                <div class="card-header fw-semibold">Inconsistências Corrigidas por Campo</div>
                <div class="card-body"><canvas id="grafico-auditoria"></canvas></div>
            </div>
        </div>
    </div>

    <div class="card shadow-sm mb-4">
        <div class="card-header fw-semibold">Amostra de Rastreabilidade (Últimas 20 Decisões na Tabela de Auditoria)</div>
        <div class="table-responsive">
            <table class="table table-sm table-striped mb-0">
                <thead>
                    <tr>
                        <th>Cliente</th>
                        <th>Campo</th>
                        <th>Valor Original</th>
                        <th>Valor Tratado</th>
                        <th>Critério / Fonte da Decisão</th>
                    </tr>
                </thead>
                <tbody>
                {% for log in ultimos_logs %}
                    <tr>
                        <td class="fw-semibold">{{ log.id_cliente }}</td>
                        <td><span class="badge text-bg-secondary">{{ log.campo }}</span></td>
                        <td class="text-danger">{{ log.valor_original }}</td>
                        <td class="text-success fw-semibold">{{ log.valor_tratado }}</td>
                        <td class="small">{{ log.criterio }}</td>
                    </tr>
                {% empty %}
                    <tr><td colspan="5" class="text-secondary">Nenhum registro auditado ainda. Rode o ETL.</td></tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="card shadow-sm">
        <div class="card-header fw-semibold">Histórico de Execuções</div>
        <div class="table-responsive">
            <table class="table table-sm table-striped mb-0">
                <thead>
                    <tr>
                        <th>Quando</th>
                        <th>Arquivo</th>
                        <th class="text-end">Lidas</th>
                        <th class="text-end">Carregadas</th>
                        <th class="text-end">Revisão Manual</th>
                        <th>Resultado</th>
                    </tr>
                </thead>
                <tbody>
                {% for execucao in ultimas %}
                    <tr>
                        <td>{{ execucao.iniciada_em|date:"d/m/Y H:i" }}</td>
                        <td>{{ execucao.arquivo }}</td>
                        <td class="text-end">{{ execucao.lidas }}</td>
                        <td class="text-end">{{ execucao.carregadas }}</td>
                        <td class="text-end">{{ execucao.em_revisao }}</td>
                        <td>
                            {% if execucao.sucesso %}
                                <span class="badge text-bg-success">OK</span>
                                <span class="small text-secondary">{{ execucao.mensagem }}</span>
                            {% else %}
                                <span class="badge text-bg-danger">Erro</span>
                                <span class="small text-danger">{{ execucao.mensagem }}</span>
                            {% endif %}
                        </td>
                    </tr>
                {% empty %}
                    <tr><td colspan="6" class="text-secondary">Nenhuma execução registrada.</td></tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</main>

{{ graficos|json_script:"dados-graficos" }}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
    const dados = JSON.parse(document.getElementById("dados-graficos").textContent);

    new Chart(document.getElementById("grafico-bairros"), {
        type: "bar",
        data: {
            labels: dados.bairros.rotulos,
            datasets: [{
                label: "Clientes",
                data: dados.bairros.valores,
                backgroundColor: "#0d6efd"
            }],
        },
        options: { plugins: { legend: { display: false } } },
    });

    new Chart(document.getElementById("grafico-auditoria"), {
        type: "bar",
        data: {
            labels: dados.auditoria.rotulos,
            datasets: [{
                label: "Correções Realizadas",
                data: dados.auditoria.valores,
                backgroundColor: "#198754"
            }],
        },
        options: { plugins: { legend: { display: false } } },
    });
</script>
</body>
</html>
```

---

## 7. Relatório de Trade-offs e Limites Conhecidos

Esta seção documenta as decisões de engenharia adotadas pela equipe e responde diretamente ao entregável de comunicação da rubrica de avaliação:

### 7.1. O que decidimos automatizar vs. O que decidimos tratar manualmente

* **Automatizado no Pipeline (`transformar()`):**
  * **Padronização Sintática e Léxica:** Remoção de acentuação em e-mails (conformidade RFC 5322), formatação de CNPJ (14 dígitos), remoção de DDI `+55` em telefones, conversão multiformato de datas (`YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY` e datas em inglês como `Dec 24, 2023`) e anulação de CEPs fictícios (`00000-000`).
  * **Unificação de Bairros e Subdivisões:** Decomposição Unicode (`NFKD`), remoção de sufixos de UF (`- DF`, `/DF`) e mapeamento determinístico de subdivisões informais (`"Sul (Águas Claras)"`, `"Norte (Aguas Claras)"`, `"Guará I"`, `"Guará II"`, `"Vte Pires"`) para as 4 regiões administrativas canônicas (**Águas Claras**, **Taguatinga**, **Vicente Pires** e **Guará**).
  * **Resolução de Divergência entre Bairro e CEP:** Quando o CEP é válido e retorna um bairro oficial divergente do texto digitado pelo vendedor (como no cliente `CLI0002`, cujo texto informava `"Sul (Aguas Claras)"`, mas o CEP `72140-010` pertence a **Taguatinga**), o sistema prioriza a fonte geocodificada oficial (CEP) e marca o registro com `status_validacao = "DIVERGENCIA_CEP_CORRIGIDA"`.
* **Tratamento Manual / Quarentena (`REVISAO_MANUAL`):**
  * Em vez de descartar registros incompletos com `dropna()` (o que causaria perda de clientes ativos e viés nos relatórios comerciais), registros sem bairro informado e sem CEP válido (como o `CLI0047 - Mercadinho Sem Endereço`) são preservados no banco com `bairro_tratado = "Não Informado"` e `status_validacao = "REVISAO_MANUAL"`. A equipe comercial pode filtrá-los no **Django Admin** e corrigi-los manualmente.

### 7.2. Principais Trade-offs Arquiteturais

1. **Dicionário Persistido no Banco (`DicionarioBairro`) vs. Hardcoded:**
   * Combinamos um dicionário base no código com a tabela `DicionarioBairro` no SQLite. O *trade-off* é realizar uma leitura inicial no banco a cada execução do ETL, mas o benefício é permitir que analistas de negócio cadastrem novas variantes pelo Django Admin sem necessidade de alterar código ou realizar novo deploy.
2. **Cache Local de CEP (`CacheCEP`) vs. Consulta Direta:**
   * Consultar a API do ViaCEP para cada linha em toda execução geraria latência de rede $O(N)$ e risco de bloqueio (*Rate Limit*). A tabela `CacheCEP` armazena os CEPs já consultados no banco local, reduzindo o tempo de rede a zero nas reexecuções.

### 7.3. Limites Conhecidos da Solução

* **CNPJs Sintéticos na Base do Desafio:** Os 47 CNPJs fornecidos no arquivo `clientes_distribuidora_vetor.csv` possuem 14 dígitos numéricos, mas foram gerados sem dígito verificador Módulo 11 real. Por isso, o validador verifica a estrutura de 14 dígitos numéricos sem descartar por Módulo 11.
* **CEPs de Fronteira no Distrito Federal:** Os clientes `CLI0017` e `CLI0033` declaram `"Vicente Pires"`, mas utilizam o CEP `72110-800` (faixa historicamente compartilhada com Taguatinga Norte antes do desmembramento postal). O sistema registra a mudança na auditoria para permitir revisão caso a distribuidora utilize roteirização por micro-região.

---

## 8. Estrutura Final de Pastas e Fluxo de Funcionamento

```text
etl_vetor/
├── .venv/                             # Ambiente virtual (gerenciado pelo uv)
├── .gitignore
├── pyproject.toml                     # Dependências do projeto
├── uv.lock                            # Versões exatas travadas
├── db.sqlite3                         # Banco SQLite local
├── manage.py
├── dados/
│   └── clientes_distribuidora_vetor.csv
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── etl/                               # Frente 1 (Pipeline/Testes) + Frente 2 (Admin/Views)
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── importar_clientes.py
│   ├── migrations/
│   │   └── 0001_initial.py
│   ├── admin.py
│   ├── models.py
│   ├── pipeline.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
└── dashboard/                         # Frente 2 (Painel Visual e Gráficos)
    ├── urls.py
    ├── views.py
    └── templates/
        └── dashboard/
            └── painel.html
```

### Diagrama do Fluxo de Dados

```text
Terminal (manage.py importar_clientes)   OU   Navegador (POST /etl/importar/)
                                      |
                                      v
                             etl.pipeline.executar()
                                      |
         +----------------------------+----------------------------+
         v                            v                            v
     extrair()                  transformar()                  carregar()
   pd.read_csv              Limpa CNPJ, Tel, Email,          bulk_create em
   (tudo texto)             Data, CEP, Bairro (NFKD +        Cliente + LogAuditoria
                            Dicionario + CacheCEP/ViaCEP)    dentro de transaction.atomic
                                      |
                                      v
          Tabelas no SQLite: Cliente, Execucao, LogAuditoria, CacheCEP
                                      |
         +----------------------------+----------------------------+
         v                                                         v
Navegador (GET /)                                        Navegador (GET /etl/exportar/)
dashboard.views.painel                                   etl.views.exportar
Cards + Gráficos Chart.js + Tabela de Auditoria          Excel (.xlsx) com 3 abas
```

---

## 9. Guia de Deploy no Render

Quando as duas frentes estiverem prontas e testadas localmente:

1. **Instale os pacotes de produção no terminal:**

```powershell
uv add gunicorn whitenoise
```

2. **Em `config/settings.py`, libere o host do Render e o WhiteNoise:**
   * Altere `ALLOWED_HOSTS = ["*"]`.
   * Adicione `'whitenoise.middleware.WhiteNoiseMiddleware'` logo abaixo de `'django.middleware.security.SecurityMiddleware'` na lista `MIDDLEWARE`.
   * Adicione no final do `settings.py`: `STATIC_ROOT = BASE_DIR / "staticfiles"`.

3. **Crie o arquivo `build.sh` na raiz do projeto:**

```bash
#!/usr/bin/env bash
set -o errexit

pip install uv
uv sync
uv run python manage.py collectstatic --no-input
uv run python manage.py migrate
uv run python manage.py importar_clientes dados/clientes_distribuidora_vetor.csv
```

4. **Configure o Web Service no painel do Render:**
   * Conecte o repositório do GitHub no [Render](https://render.com/).
   * **Build Command:** `bash build.sh`
   * **Start Command:** `uv run gunicorn config.wsgi:application`

Assim que o deploy terminar, o sistema já subirá com os 47 clientes da Distribuidora Vetor carregados, higienizados e com os gráficos e tabelas de auditoria prontos para demonstração!