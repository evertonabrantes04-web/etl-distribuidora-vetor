from django.db.models import Count, Q, Sum
from django.shortcuts import render

from etl.models import Cliente, Execucao, LogAuditoria

# --- NOVO (1/2): Mapa de nomes amigáveis para a coluna "Campo" ---
NOMES_CAMPOS = {
    "bairro_informado": "Bairro",
    "telefone": "Telefone",
    "email": "E-mail",
    "data_cadastro": "Data de Cadastro",
    "cnpj": "CNPJ",
    "cep": "CEP",
}


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

    # --- NOVO (2/2): Enriquece os logs com razão social, iniciais e código ---
    ids_clientes = {log.id_cliente for log in ultimos_logs}
    mapa_clientes = (
        dict(
            Cliente.objects.filter(id_cliente__in=ids_clientes).values_list(
                "id_cliente", "razao_social"
            )
        )
        if ids_clientes
        else {}
    )

    for log in ultimos_logs:
        digitos = "".join(ch for ch in log.id_cliente if ch.isdigit())
        log.codigo_formatado = f"#{digitos}" if digitos else log.id_cliente
        log.nome_cliente = mapa_clientes.get(
            log.id_cliente, f"Cliente {log.codigo_formatado}"
        )

        partes = log.nome_cliente.split()
        log.iniciais_cliente = (
            (partes[0][0] + partes[1][0]).upper()
            if len(partes) > 1
            else log.nome_cliente[:2].upper()
        )

        log.campo_formatado = NOMES_CAMPOS.get(
            log.campo, log.campo.replace("_", " ").title()
        )
    # --- FIM DO TRECHO NOVO ---

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