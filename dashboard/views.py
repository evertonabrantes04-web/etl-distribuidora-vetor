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