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