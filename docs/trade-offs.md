# RELATÓRIO DE TRADE-OFFS E LIMITES CONHECIDOS

**Projeto Integrador — Distribuidora Vetor | Decisões de Engenharia e Governança**

Esta seção documenta as decisões arquiteturais e de engenharia adotadas pela equipe no desenvolvimento do sistema, respondendo diretamente aos critérios de avaliação da rubrica técnica.

---

## 1. Automação vs. Tratamento Manual (Quarentena)

### 1.1. Automatizado no Pipeline (`transformar()`)
* **Padronização Sintática e Léxica:** Remoção de acentuação em e-mails (conformidade RFC 5322), formatação de CNPJ (14 dígitos), remoção de DDI `+55` em telefones, conversão multiformato de datas (`YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY` e formatos textuais em inglês como `Dec 24, 2023`) e anulação de CEPs inválidos ou zerados (`00000-000`).
* **Unificação de Bairros e Subdivisões:** Decomposição Unicode (`NFKD`), remoção de sufixos de UF (`- DF`, `/DF`) e mapeamento determinístico de subdivisões informais (`"Sul (Águas Claras)"`, `"Norte (Aguas Claras)"`, `"Guará I"`, `"Guará II"`, `"Vte Pires"`) para as **4 regiões administrativas canônicas**: *Águas Claras, Taguatinga, Vicente Pires e Guará*.
* **Resolução de Divergência entre Bairro e CEP:** Quando o CEP é válido e retorna um bairro oficial divergente do texto digitado pelo vendedor (ex.: cliente `CLI0002`, cujo texto indicava `"Sul (Aguas Claras)"`, mas o CEP `72140-010` pertence oficialmente a **Taguatinga**), o sistema prioriza a fonte geocodificada oficial e marca o registro com o status `DIVERGENCIA_CEP_CORRIGIDA`.

### 1.2. Tratamento Manual / Quarentena (`REVISAO_MANUAL`)
* **Preservação de Ativos B2B:** Em vez de descartar registros incompletos utilizando comandos destrutivos como `dropna()` (o que geraria perda de clientes ativos e distorção nos relatórios de vendas), os registros desprovidos de bairro e CEP válido (como o `CLI0047 - Mercadinho Sem Endereço`) são mantidos no banco com `bairro_tratado = "Não Informado"` e `status_validacao = "REVISAO_MANUAL"`. A equipe comercial pode filtrá-los diretamente no **Django Admin** para curadoria humana.

---

## 2. Principais Trade-offs Arquiteturais

1. **Dicionário Híbrido (`DicionarioBairro` no Banco vs. Hardcoded):**
   * *Abordagem:* Combinamos um dicionário base fixo no código (`MAPA_BAIRROS_PADRAO`) com uma tabela relacional dinâmica (`DicionarioBairro`) no SQLite.
   * *Trade-off:* O custo computacional é realizar uma consulta adicional na tabela a cada execução do ETL. O benefício gerado compensa amplamente: analistas de negócio ganham autonomia para cadastrar novas variantes e sinônimos diretamente pelo Django Admin, sem a necessidade de alterar código-fonte ou realizar novos *deploys*.

2. **Cache Local de CEP (`CacheCEP`) vs. Consulta Direta em Rede:**
   * *Abordagem:* Armazenamento em tabela local do SQLite das consultas bem-sucedidas à API pública do ViaCEP.
   * *Trade-off:* Consome espaço em disco para metadados postais, mas elimina a complexidade de latência de rede $O(N)$ e o risco de bloqueio por *Rate Limit* em reexecuções consecutivas do pipeline.

---

## 3. Limites Conhecidos da Solução

* **Validação Estrutural de CNPJ:** Os 47 registros fornecidos no dataset contêm CNPJs com 14 dígitos numéricos gerados sinteticamente para fins didáticos (sem validação real por Módulo 11). O validador do pipeline assegura a estrutura de 14 caracteres, mas não descarta por dígito verificador.
* **CEPs de Fronteira no Distrito Federal:** Casos específicos como os clientes `CLI0017` e `CLI0033`, que declaram `"Vicente Pires"` mas utilizam o CEP `72110-800` (faixa postal historicamente compartilhada com Taguatinga Norte), evidenciam os limites de granularidade das bases postais. O sistema registra a alteração na trilha de auditoria para revisão gerencial.