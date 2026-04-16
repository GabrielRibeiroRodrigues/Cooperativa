from django.urls import path
from . import views

app_name = 'disponibilidade'

urlpatterns = [
    path('consultar/<int:trabalhador_id>/', views.consultar_agenda, name='consultar_agenda'),
]
