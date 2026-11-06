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