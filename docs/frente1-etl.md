# DOCUMENTAÇÃO TÉCNICA — FRENTE 1
**Projeto Integrador — Distribuidora Vetor | Motor ETL, Enriquecimento e Testes**

* **Base de referência:** Proposta do desafio, planejamento técnico e implementação de `etl/pipeline.py`, comandos de terminal e testes automatizados.

---

## 1. Objetivo e Responsabilidade
A **Distribuidora Vetor** é uma empresa fictícia B2B cuja base cadastral apresenta grafias diferentes para os mesmos bairros, além de inconsistências em CEP, CNPJ, telefone, e-mail e datas. O objetivo da **Frente 1** foi construir um processo reproduzível de extração, tratamento e carga, preservando a rastreabilidade das alterações e sinalizando com segurança os casos que exigem curadoria humana.

* **Arquivos da frente:** 
  * `etl/pipeline.py` (Regras de limpeza e execução)
  * `etl/management/commands/importar_clientes.py` (Interface de linha de comando)
  * `etl/tests.py` (Suíte de testes automatizados)

---

## 2. Fluxo ETL e Justificativas Técnicas

### 2.1. Extração (Extract)
A função `extrair()` utiliza o `pandas.read_csv` com separador `;`, codificação UTF-8 e `dtype=str`. Ler inicialmente todos os campos como texto é uma decisão fundamental para **preservar os zeros à esquerda** de CEPs, telefones e identificadores, evitando conversões automáticas indesejadas. Na transformação, os nomes das colunas são padronizados e é conferida a presença das 11 colunas obrigatórias; se faltar alguma, a execução é abortada com erro.

### 2.2. Transformação (Transform)

| Campo | Regra Aplicada | Motivo da Decisão |
| :--- | :--- | :--- |
| **CNPJ** | Remover caracteres não numéricos e aplicar a máscara `XX.XXX.XXX/XXXX-XX` quando houver 14 dígitos. | Unificar a apresentação sem rejeitar os CNPJs fictícios apenas por dígito verificador. Entradas com comprimento diferente de 14 são descartadas. |
| **Telefone** | Retirar pontuação, remover DDI `55` quando aplicável e aplicar máscara para 10 ou 11 dígitos. | Permitir agrupamento e leitura consistente de telefones fixos e móveis; formatos não reconhecidos são preservados como texto. |
| **E-mail** | Remover acentos, espaços externos e converter para minúsculas. | Reduzir diferenças de grafia (conformidade RFC 5322). Não valida a existência ou entregabilidade do endereço. |
| **Data de Cadastro** | Interpretar ISO (`YYYY-MM-DD`), barras (`DD/MM/YYYY`), hífens (`DD-MM-YYYY`) e mês abreviado em português/inglês (`Dec 24, 2023`); converter para data. | Uniformizar datas para consultas. Datas não reconhecidas impedem a carga daquele registro. |
| **CEP** | Conservar somente oito dígitos válidos em formato, aplicar `XXXXX-XXX`; CEP vazio, zerado (`00000-000`) ou malformado torna-se vazio. | Evitar utilizar um CEP estruturalmente inválido como referência geográfica. |
| **Bairro** | Normalizar chave com Unicode `NFKD`, minúsculas, espaços e remoção de sufixos DF; consultar dicionário canônico. | Agrupar variações como `"Aguas claras"` e `"Águas Claras"` sob o mesmo nome, reduzindo fragmentação nos relatórios. |

### 2.3. Padronização e Decisão sobre Bairros
Foi adotado um dicionário inicial de variantes para os nomes canônicos **Águas Claras**, **Taguatinga**, **Vicente Pires** e **Guará**. A tabela `DicionarioBairro` no banco de dados complementa e sobrescreve as correspondências iniciais sem exigir alteração de código.

Quando o CEP está disponível, `consultar_cep_com_cache()` busca primeiro na tabela local `CacheCEP` e, na ausência de resposta armazenada, consulta a API ViaCEP com timeout de três segundos. A utilização de cache reduz chamadas repetidas e dependência da rede.

**Ordem de decisão implementada:**
1. Se bairro textual e bairro do CEP forem reconhecidos e **divergirem**, priorizar o bairro do CEP e marcar `DIVERGENCIA_CEP_CORRIGIDA`.
2. Se o bairro textual for reconhecido, preservá-lo, usando `VALIDADO_SEM_CEP` quando o CEP estiver ausente.
3. Se apenas o bairro do CEP for reconhecido, utilizá-lo.
4. Se nenhuma fonte for suficiente, manter `"Não Informado"` e marcar `REVISAO_MANUAL`.

### 2.4. Carga (Load)
A função `carregar()` utiliza modelos Django e transações atômicas (`transaction.atomic()`). O `bulk_create` com `update_conflicts=True` e chave única `id_cliente` atualiza registros já existentes, evitando duplicação na reimportação. Os registros de auditoria são inseridos em lote e vinculados à execução.

---

## 3. Auditoria e Rastreabilidade
Para cada campo alterado, o pipeline registra `id_cliente`, nome do campo, valor original, valor tratado e critério da transformação na tabela `LogAuditoria`. Isso permite reconstruir a justificativa de uma correção, especialmente quando o bairro informado e o bairro retornado pelo CEP divergem. Alterações são registradas apenas quando o valor de entrada difere do resultado tratado.

---

## 4. Resultados Observados
* **Comando utilizado:** `uv run python manage.py importar_clientes dados/clientes_distribuidora_vetor.csv`
* **Registros lidos:** 47
* **Clientes carregados:** 47
* **Descartados:** 0
* **Em revisão manual:** 1 (`CLI0047`)
* **Logs de auditoria:** 113
* **Testes automatizados:** 8 aprovados

**Distribuição de status:** 30 `VALIDADO`, 15 `VALIDADO_SEM_CEP`, 1 `DIVERGENCIA_CEP_CORRIGIDA` e 1 `REVISAO_MANUAL`.

---

## 5. Testes Automatizados
A suíte `etl/tests.py` foi executada com sucesso via `uv run python manage.py test`. Ela valida funções de normalização de CNPJ, telefone, e-mail, CEP, datas e cenários de resolução de divergência. As respostas externas do ViaCEP são simuladas com `unittest.mock` (`patch`/`MagicMock`), garantindo independência de internet.

---

## 6. Trade-offs e Limites Conhecidos
* **Automação vs. Revisão Humana:** Casos sem evidências suficientes são mantidos em quarentena (`REVISAO_MANUAL`), evitando inventar dados.
* **CEP como Referência Prioritária:** Reduz divergências regionais, mas o retorno postal pode refletir limites ou informações desatualizadas.
* **Cache Local de CEP:** Melhora o desempenho drasticamente, mas pode reter respostas antigas caso não haja política de expiração.
* **Validação Estrutural de CNPJ:** O validador verifica 14 dígitos estruturais, mas não valida os dígitos verificadores (adequado à amostra sintética fornecida).