from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Servico, Avaliacao, ControleJornada, Mensagem

# Register your models here.

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'telefone', 'valor_diario', 'avaliacao_media', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'telefone']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('role', 'telefone', 'valor_diario', 'avaliacao_media')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações Adicionais', {
            'fields': ('role', 'telefone', 'valor_diario')
        }),
    )


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['contratante', 'trabalhador', 'descricao', 'data_servico', 'valor_acordado', 'status', 'data_criacao']
    list_filter = ['status', 'data_servico', 'data_criacao']
    search_fields = ['contratante__username', 'trabalhador__username', 'descricao']
    date_hierarchy = 'data_servico'
    readonly_fields = ['data_criacao', 'data_atualizacao']


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['servico', 'avaliador', 'avaliado', 'nota', 'data_avaliacao']
    list_filter = ['nota', 'data_avaliacao']
    search_fields = ['avaliador__username', 'avaliado__username', 'comentario']
    readonly_fields = ['avaliado', 'data_avaliacao']


@admin.register(ControleJornada)
class ControleJornadaAdmin(admin.ModelAdmin):
    list_display = ['servico', 'data', 'hora_inicio', 'hora_pausa', 'hora_retorno', 'hora_fim', 'total_horas']
    list_filter = ['data']
    search_fields = ['servico__contratante__username', 'servico__trabalhador__username']
    date_hierarchy = 'data'
    readonly_fields = ['total_horas']


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ['servico', 'remetente', 'conteudo', 'data_envio', 'lida']
    list_filter = ['data_envio', 'lida']
    search_fields = ['remetente__username', 'conteudo']
    date_hierarchy = 'data_envio'
    readonly_fields = ['data_envio']
