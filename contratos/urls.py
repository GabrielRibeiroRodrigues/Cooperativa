from django.urls import path
from . import views

app_name = 'contratos'

urlpatterns = [
    path('', views.lista_contratos, name='lista_contratos'),
    path('gerar/<int:servico_id>/', views.gerar_contrato, name='gerar_contrato'),
    path('<int:contrato_id>/', views.detalhe_contrato, name='detalhe_contrato'),
]
