from django.contrib import admin
from django.utils.html import format_html
from .models import Contrato, AssinaturaContrato

class AssinaturaInline(admin.TabularInline):
    model = AssinaturaContrato
    extra = 0
    readonly_fields = ['data_assinatura', 'ip_assinatura']
    can_delete = False

@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'contratante', 'trabalhador', 'valor', 'status_display', 'data_inicio']
    list_filter = ['status', 'e_servico_risco', 'data_criacao']
    search_fields = ['numero', 'contratante__username', 'trabalhador__username']
    readonly_fields = ['numero', 'data_criacao', 'data_atualizacao']
    inlines = [AssinaturaInline]

    def status_display(self, obj):
        colors = {
            'rascunho': '#6c757d',
            'aguardando_assinatura': '#0d6efd',
            'vigente': '#198754',
            'encerrado': '#dc3545',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Status'

@admin.register(AssinaturaContrato)
class AssinaturaContratoAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'tipo_assinante', 'usuario', 'assinado', 'data_assinatura']
    list_filter = ['tipo_assinante', 'assinado']
