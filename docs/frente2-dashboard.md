# DOCUMENTAÇÃO TÉCNICA — FRENTE 2 (DASHBOARD E GOVERNANÇA)

**Projeto Integrador — Distribuidora Vetor | Interface Executiva, Curadoria no Admin e Relatórios**

* **Base de referência:** Implementação compartilhada de `dashboard/views.py`, `dashboard/templates/dashboard/painel.html`, `etl/admin.py`, `etl/views.py` e rotas associadas.

## 1. Objetivo e Responsabilidade

Enquanto a Frente 1 focou na extração, saneamento determinístico e persistência segura dos dados no backend, a **Frente 2** teve como responsabilidade transformar esse motor em uma **plataforma executiva de governança e tomada de decisão**. 

O escopo incluiu o desenvolvimento do Dashboard interativo com gráficos comparativos (*Antes vs. Depois*), a mesa de curadoria avançada no Django Admin, o sistema de upload web de novas bases CSV e a geração automatizada de planilhas gerenciais em Excel (`.xlsx`).

* **Arquivos da frente:**
  * `dashboard/views.py` e `dashboard/urls.py` (Lógica de indicadores e renderização)
  * `dashboard/templates/dashboard/painel.html` (Interface web moderna em Bootstrap 5)
  * `etl/admin.py` (Mesa de curadoria, badges visuais e imutabilidade de auditoria)
  * `etl/views.py` (Rotas POST de importação e exportação de relatórios corporativos)

---

## 2. Arquitetura e Componentes da Frente 2

### 2.1. Dashboard Executivo e Agregações (`dashboard/views.py`)
A view principal consulta os modelos tratados no SQLite utilizando o ORM do Django para calcular métricas em tempo real sem sobrecarregar a memória:
* **Métricas de Qualidade (`aggregate`):** Contagem total de clientes limpos, contagem distinta de bairros antes (`bairro_informado`) e depois (`bairro_tratado`), total de conflitos de CEP corrigidos (`DIVERGENCIA_CEP_CORRIGIDA`) e registros em quarentena (`REVISAO_MANUAL`).
* **Agrupamentos para Gráficos:** Utilização de `.annotate(total=Count("id"))` para consolidar a distribuição dos 47 clientes nas regiões administrativas canônicas e quantificar o volume de correções por campo na tabela de auditoria.
* **Serialização Segura (`json_script`):** Os dados agregados em Python são injetados de forma segura no template HTML através da tag `json_script`, permitindo a leitura nativa por scripts JavaScript do lado do cliente.

### 2.2. Interface Executiva e Interativa (`painel.html`)
Construída com **Bootstrap 5.3.8**, Google Fonts (*Inter*), **Bootstrap Icons** e **Chart.js**, a interface web adota uma identidade visual corporativa (*Dark Navy & Emerald*):
* **Cards de Indicadores (KPIs):** Indicadores visuais com animações suaves de elevação (`translateY`) no *hover*, destacando o total de clientes limpos, a redução de fragmentação de bairros, o total de transformações auditadas e o status das execuções do pipeline.
* **Gráficos Comparativos:** Barras arredondadas renderizadas via `Chart.js` exibindo a consolidação das 26 variantes iniciais nas 4 regiões canônicas (*Águas Claras, Taguatinga, Vicente Pires e Guará*) e a incidência de correções por campo.
* **Tabela de Rastreabilidade com Filtro Instantâneo:** Listagem das últimas decisões da tabela `LogAuditoria` exibindo o valor original (em vermelho tachado) e o valor tratado (em verde destacado), equipada com um campo de **pesquisa em tempo real (JavaScript)** para filtrar qualquer cliente ou regra ao vivo durante apresentações.

### 2.3. Mesa de Curadoria e Governança no Django Admin (`etl/admin.py`)
O painel administrativo padrão do Django foi transformado em uma ferramenta de governança de dados real:
* **Badges Visuais (`format_html`):** Etiquetas coloridas para o campo `status_validacao` (Verde para `VALIDADO`, Azul para `VALIDADO_SEM_CEP`, Amarelo para `DIVERGENCIA_CEP_CORRIGIDA` e Vermelho para `REVISAO_MANUAL` — destacando o caso crítico do `CLI0047`).
* **Coluna Comparativa (*Antes vs. Depois*):** Exibição na mesma coluna do bairro original riscado ao lado do bairro tratado em negrito, facilitando a auditoria visual imediata.
* **Ações em Lote (`@admin.action`):** Criação da opção de curadoria *"Aprovar curadoria (Marcar selecionados como VALIDADO)"*, permitindo que um analista aprove cadastros corrigidos em poucos cliques.
* **Blindagem da Auditoria:** A tabela `LogAuditoria` foi configurada como restrita (`has_add_permission = False` e `has_change_permission = False`), garantindo que o histórico de alterações do ETL seja **totalmente imutável**.
* **Dicionário Dinâmico (`DicionarioBairro`):** Gestão de variantes textuais diretamente pelo painel administrativo, permitindo a inclusão de novos sinônimos sem necessidade de novos deploys.

### 2.4. Exportação Corporativa em Excel (`etl/views.py`)
Através da biblioteca `openpyxl` e manipulação de buffers em memória (`BytesIO`), a rota `/etl/exportar/` gera instantaneamente um arquivo `.xlsx` estruturado com **3 abas gerenciais**:
1. `Clientes Tratados`: Base completa com os dados saneados e seus respectivos status.
2. `Resumo por Bairro`: Agregação executiva de clientes por região administrativa canônica.
3. `Log de Auditoria`: Trilha completa de rastreabilidade célula a célula para auditorias externas.

---

## 3. Decisões de Design e Trade-offs da Frente 2

* **Visualização via ORM vs. Consultas SQL Brutas:** Optou-se por utilizar o ORM nativo do Django para as agregações do dashboard. O ganho é a portabilidade entre bancos (SQLite em desenvolvimento e PostgreSQL em produção) e a segurança contra SQL Injection; o custo é a necessidade de estruturar anotações complexas com `Q` e `Count`.
* **Renderização Front-end com Chart.js via JSON Script:** Evitou-se o uso de frameworks pesados de Single-Page Application (como React ou Vue) para manter o projeto leve, rápido de instalar via `uv` e totalmente autocontido no ecossistema Django.
* **Upload Síncrono com Feedback por Mensagens:** O envio de arquivos CSV via web utiliza o sistema nativo de mensagens do Django (`messages`), fornecendo retorno imediato de sucesso, contagem de registros carregados ou erros de validação estrutural.