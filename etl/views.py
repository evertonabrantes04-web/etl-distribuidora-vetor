from io import BytesIO

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .models import CacheCEP, Cliente, Execucao, LogAuditoria
from .pipeline import executar


@login_required
@require_POST
def limpar_dados(request):
    limpar_cache_cep = request.POST.get("limpar_cache_cep") == "on"

    with transaction.atomic():
        qtd_logs, _ = LogAuditoria.objects.all().delete()
        qtd_execucoes, _ = Execucao.objects.all().delete()
        qtd_clientes, _ = Cliente.objects.all().delete()

        qtd_cache = 0
        if limpar_cache_cep:
            qtd_cache, _ = CacheCEP.objects.all().delete()

    detalhe_cache = f" e {qtd_cache} CEP(s) em cache" if limpar_cache_cep else ""
    messages.warning(
        request,
        f"Base limpa com sucesso: {qtd_clientes} cliente(s), {qtd_logs} log(s) de auditoria, "
        f"{qtd_execucoes} execução(ões){detalhe_cache} removidos.",
    )
    return redirect("dashboard")

TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

@login_required
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

@login_required
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