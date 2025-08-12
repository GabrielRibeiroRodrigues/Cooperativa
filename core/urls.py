from django.urls import path
from . import views

urlpatterns = [
    # Página inicial
    path('', views.home, name='home'),
    
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('perfil/', views.perfil_view, name='perfil'),
    
    # Painéis
    path('painel/contratante/', views.painel_contratante, name='painel_contratante'),
    path('painel/trabalhador/', views.painel_trabalhador, name='painel_trabalhador'),
    
    # Trabalhadores
    path('trabalhadores/', views.buscar_trabalhadores, name='buscar_trabalhadores'),
    path('trabalhador/<int:user_id>/', views.detalhes_trabalhador, name='detalhes_trabalhador'),
    
    # Serviços
    path('servico/<int:servico_id>/', views.detalhes_servico, name='detalhes_servico'),
    path('servico/<int:servico_id>/aceitar/', views.aceitar_servico, name='aceitar_servico'),
    path('servico/<int:servico_id>/recusar/', views.recusar_servico, name='recusar_servico'),
    
    # Controle de jornada
    path('jornada/<int:servico_id>/<str:acao>/', views.controle_jornada, name='controle_jornada'),
    path('jornada/<int:servico_id>/status/', views.status_jornada_ajax, name='status_jornada_ajax'),
]
