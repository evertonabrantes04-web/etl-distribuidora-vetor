from django.contrib import admin
from django.utils.html import format_html

from .models import CacheCEP, Cliente, DicionarioBairro, Execucao, LogAuditoria

# 1. Identidade visual do cabeçalho do Django Admin
admin.site.site_header = "Governança de Dados — Distribuidora Vetor"
admin.site.site_title = "Admin ETL Vetor"
admin.site.index_title = "Painel de Curadoria, Auditoria e Dicionário Canônico"


# 2. Ação em lote para aprovar clientes que estavam em Revisão Manual
@admin.action(description="Aprovar curadoria (Marcar selecionados como VALIDADO)")
def aprovar_curadoria(modeladmin, request, queryset):
    atualizados = queryset.update(status_validacao="VALIDADO")
    modeladmin.message_user(
        request,
        f"{atualizados} cliente(s) marcado(s) como VALIDADO após revisão manual.",
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        "id_cliente",
        "razao_social",
        "cnpj",
        "telefone",
        "comparativo_bairro",
        "cep",
        "badge_status",
        "vendedor_responsavel",
    ]
    list_filter = [
        "status_validacao",
        "bairro_tratado",
        "vendedor_responsavel",
        "data_cadastro",
    ]
    search_fields = [
        "id_cliente",
        "razao_social",
        "cnpj",
        "email",
        "bairro_informado",
        "bairro_tratado",
        "cep",
    ]
    # Protege o ID e o valor histórico bruto que veio no CSV
    readonly_fields = ["id_cliente", "bairro_informado", "data_cadastro"]
    actions = [aprovar_curadoria]
    list_per_page = 25

    fieldsets = (
        (
            "Identificação Comercial",
            {
                "fields": (
                    "id_cliente",
                    "razao_social",
                    "cnpj",
                    "vendedor_responsavel",
                    "data_cadastro",
                )
            },
        ),
        ("Contato Padronizado", {"fields": ("telefone", "email")}),
        (
            "Saneamento Geográfico (Antes vs. Curadoria)",
            {
                "description": (
                    "O campo 'Bairro informado' preserva o valor original do CSV. "
                    "Para sanear um cliente em REVISAO_MANUAL, preencha o 'Bairro tratado' "
                    "e altere o status para VALIDADO."
                ),
                "fields": (
                    "bairro_informado",
                    "bairro_tratado",
                    "cep",
                    "cidade",
                    "uf",
                    "status_validacao",
                ),
            },
        ),
    )

    @admin.display(description="Bairro (Original → Tratado)", ordering="bairro_tratado")
    def comparativo_bairro(self, obj):
        orig = obj.bairro_informado or "VAZIO"
        if orig == obj.bairro_tratado:
            return obj.bairro_tratado
        return format_html(
            '<span style="color: #6c757d; text-decoration: line-through;">{}</span> &rarr; <strong>{}</strong>',
            orig,
            obj.bairro_tratado,
        )

    @admin.display(description="Status de Validação", ordering="status_validacao")
    def badge_status(self, obj):
        cores = {
            "VALIDADO": ("#d1e7dd", "#0f5132"),
            "VALIDADO_SEM_CEP": ("#cff4fc", "#055160"),
            "DIVERGENCIA_CEP_CORRIGIDA": ("#fff3cd", "#664d03"),
            "REVISAO_MANUAL": ("#f8d7da", "#842029"),
        }
        bg, texto = cores.get(obj.status_validacao, ("#e2e3e5", "#41464b"))
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 6px; font-weight: 600; font-size: 0.78rem;">{}</span>',
            bg,
            texto,
            obj.status_validacao,
        )


class LogAuditoriaInline(admin.TabularInline):
    model = LogAuditoria
    extra = 0
    can_delete = False
    readonly_fields = [
        "id_cliente",
        "campo",
        "valor_original",
        "valor_tratado",
        "criterio",
        "criado_em",
    ]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = [
        "id_cliente",
        "campo",
        "transformacao_visual",
        "criterio",
        "execucao",
    ]
    list_filter = ["campo", "criterio", "execucao"]
    search_fields = ["id_cliente", "valor_original", "valor_tratado", "criterio"]
    readonly_fields = [
        "execucao",
        "id_cliente",
        "campo",
        "valor_original",
        "valor_tratado",
        "criterio",
        "criado_em",
    ]
    list_per_page = 30

    @admin.display(description="Transformação (Original → Tratado)")
    def transformacao_visual(self, obj):
        return format_html(
            '<span style="color: #dc3545;">{}</span> &rarr; <strong style="color: #198754;">{}</strong>',
            obj.valor_original or "VAZIO",
            obj.valor_tratado or "AUSENTE",
        )

    # Impede que usuários adulterem manualmente os registros de auditoria
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DicionarioBairro)
class DicionarioBairroAdmin(admin.ModelAdmin):
    list_display = ["variante_normalizada", "nome_canonico"]
    list_editable = ["nome_canonico"]
    list_filter = ["nome_canonico"]
    search_fields = ["variante_normalizada", "nome_canonico"]


@admin.register(CacheCEP)
class CacheCEPAdmin(admin.ModelAdmin):
    list_display = ["cep", "bairro", "cidade", "uf", "fonte", "atualizado_em"]
    list_filter = ["bairro", "fonte", "uf"]
    search_fields = ["cep", "bairro"]
    readonly_fields = ["atualizado_em"]


@admin.register(Execucao)
class ExecucaoAdmin(admin.ModelAdmin):
    list_display = [
        "iniciada_em",
        "arquivo",
        "lidas",
        "carregadas",
        "em_revisao",
        "descartadas",
        "sucesso",
    ]
    list_filter = ["sucesso", "iniciada_em"]
    readonly_fields = [
        "iniciada_em",
        "arquivo",
        "lidas",
        "carregadas",
        "em_revisao",
        "descartadas",
        "sucesso",
        "mensagem",
    ]
    inlines = [LogAuditoriaInline]

    def has_add_permission(self, request):
        return False