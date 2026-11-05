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