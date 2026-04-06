from django.urls import path
from . import views

app_name = 'disponibilidade'

urlpatterns = [
    path('agenda/', views.agenda_trabalhador, name='agenda_trabalhador'),
    path('api/toggle/', views.api_toggle_disponibilidade, name='api_toggle'),
    path('consultar/<int:trabalhador_id>/', views.consultar_agenda, name='consultar_agenda'),
]
