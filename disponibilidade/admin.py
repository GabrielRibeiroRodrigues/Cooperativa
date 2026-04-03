from django.contrib import admin
from .models import Disponibilidade

@admin.register(Disponibilidade)
class DisponibilidadeAdmin(admin.ModelAdmin):
    list_display = ['trabalhador', 'data', 'turno', 'status']
    list_filter = ['status', 'turno', 'data']
