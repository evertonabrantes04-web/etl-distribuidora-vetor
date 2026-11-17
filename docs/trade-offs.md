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