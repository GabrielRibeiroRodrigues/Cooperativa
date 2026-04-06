from django.contrib import admin
from .models import Conversa, Mensagem


@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_participantes",
        "servico",
        "data_criacao",
        "ultima_atualizacao",
    ]
    list_filter = ["data_criacao", "ultima_atualizacao"]
    search_fields = ["participantes__username", "participantes__email"]
    date_hierarchy = "data_criacao"
    filter_horizontal = ["participantes"]
    readonly_fields = ["data_criacao", "ultima_atualizacao"]

    def get_participantes(self, obj):
        return ", ".join([p.username for p in obj.participantes.all()])

    get_participantes.short_description = "Participantes"


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "conversa",
        "remetente",
        "conteudo_resumido",
        "data_envio",
        "lida",
    ]
    list_filter = ["lida", "data_envio"]
    search_fields = ["remetente__username", "conteudo"]
    date_hierarchy = "data_envio"
    readonly_fields = ["data_envio"]
    list_select_related = ["conversa", "remetente"]

    def conteudo_resumido(self, obj):
        return obj.conteudo[:50] + "..." if len(obj.conteudo) > 50 else obj.conteudo

    conteudo_resumido.short_description = "Conteúdo"
