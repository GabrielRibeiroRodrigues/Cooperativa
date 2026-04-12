from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, Servico, Avaliacao, ControleJornada, Mensagem, Notificacao,
    Administrador, LogAcaoAdmin, Denuncia, TermoUso, TipoServico
)

# Register your models here.

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'telefone', 'valor_diario', 'avaliacao_display', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff', 'avaliacao_media']
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
    
    def avaliacao_display(self, obj):
        if obj.avaliacao_media > 0:
            stars = '★' * int(obj.avaliacao_media) + '☆' * (5 - int(obj.avaliacao_media))
            return format_html(
                '<span style="color: gold;">{}</span> ({})',
                stars,
                obj.avaliacao_media
            )
        return 'Sem avaliações'
    avaliacao_display.short_description = 'Avaliação'


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['id', 'contratante', 'trabalhador', 'descricao_resumida', 'data_servico', 'valor_acordado', 'status_display', 'data_criacao']
    list_filter = ['status', 'data_servico', 'data_criacao']
    search_fields = ['contratante__username', 'trabalhador__username', 'descricao']
    date_hierarchy = 'data_servico'
    readonly_fields = ['data_criacao', 'data_atualizacao']
    
    def descricao_resumida(self, obj):
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao
    descricao_resumida.short_description = 'Descrição'
    
    def status_display(self, obj):
        colors = {
            'pendente': 'orange',
            'aceito': 'blue',
            'concluido': 'green',
            'cancelado': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['servico', 'avaliador', 'avaliado', 'nota_display', 'data_avaliacao']
    list_filter = ['nota', 'data_avaliacao']
    search_fields = ['avaliador__username', 'avaliado__username', 'comentario']
    readonly_fields = ['avaliado', 'data_avaliacao']
    
    def nota_display(self, obj):
        stars = '★' * obj.nota + '☆' * (5 - obj.nota)
        return format_html('<span style="color: gold; font-size: 16px;">{}</span>', stars)
    nota_display.short_description = 'Nota'


@admin.register(ControleJornada)
class ControleJornadaAdmin(admin.ModelAdmin):
    list_display = ['servico', 'data', 'hora_inicio', 'hora_pausa', 'hora_retorno', 'hora_fim', 'total_horas_display', 'status_display']
    list_filter = ['data']
    search_fields = ['servico__contratante__username', 'servico__trabalhador__username']
    date_hierarchy = 'data'
    readonly_fields = ['total_horas']
    
    def total_horas_display(self, obj):
        if obj.total_horas >= 8:
            return format_html('<span style="color: red; font-weight: bold;">{}h</span>', obj.total_horas)
        return f'{obj.total_horas}h'
    total_horas_display.short_description = 'Total de Horas'
    
    def status_display(self, obj):
        colors = {
            'nao_iniciada': 'gray',
            'em_andamento': 'blue',
            'pausada': 'orange',
            'finalizada': 'green',
        }
        status_text = {
            'nao_iniciada': 'Não iniciada',
            'em_andamento': 'Em andamento',
            'pausada': 'Pausada',
            'finalizada': 'Finalizada',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status_jornada, 'black'),
            status_text.get(obj.status_jornada, 'Desconhecido')
        )
    status_display.short_description = 'Status da Jornada'


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ['servico', 'remetente', 'conteudo_resumido', 'data_envio', 'lida']
    list_filter = ['data_envio', 'lida']
    search_fields = ['remetente__username', 'conteudo']
    date_hierarchy = 'data_envio'
    readonly_fields = ['data_envio']
    
    def conteudo_resumido(self, obj):
        return obj.conteudo[:50] + '...' if len(obj.conteudo) > 50 else obj.conteudo
    conteudo_resumido.short_description = 'Mensagem'


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'titulo', 'tipo', 'lida', 'data_criacao']
    list_filter = ['tipo', 'lida', 'data_criacao']
    search_fields = ['usuario__username', 'titulo', 'mensagem']


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'ativo', 'data_designacao']
    list_filter = ['ativo']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name']


@admin.register(LogAcaoAdmin)
class LogAcaoAdminAdmin(admin.ModelAdmin):
    list_display = ['administrador', 'acao', 'alvo_tipo', 'alvo_id', 'data_acao']
    list_filter = ['acao', 'data_acao']
    search_fields = ['administrador__username', 'detalhes', 'alvo_tipo']
    readonly_fields = ['administrador', 'acao', 'detalhes', 'alvo_tipo', 'alvo_id', 'ip_origem', 'data_acao']


@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    list_display = ['id', 'denunciante', 'denunciado', 'motivo', 'status', 'data_criacao']
    list_filter = ['status', 'data_criacao']
    search_fields = ['denunciante__username', 'denunciado__username', 'motivo', 'descricao']
    readonly_fields = ['data_criacao', 'data_resolucao']


@admin.register(TermoUso)
class TermoUsoAdmin(admin.ModelAdmin):
    list_display = ['versao', 'ativo', 'criado_por', 'data_publicacao']
    list_filter = ['ativo', 'data_publicacao']
    search_fields = ['versao', 'conteudo']
