from django.urls import path
from . import views

urlpatterns = [
    # Página inicial
    path('', views.home, name='home'),
    
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('registro/contratante/', views.registro_contratante_view, name='registro_contratante'),
    path('registro/trabalhador/', views.registro_trabalhador_view, name='registro_trabalhador'),

    path('perfil/', views.perfil_view, name='perfil'),
    
    # Painéis
    path('painel/contratante/', views.painel_contratante, name='painel_contratante'),
    path('painel/trabalhador/', views.painel_trabalhador, name='painel_trabalhador'),
    
    # Trabalhadores
    path('trabalhadores/', views.buscar_trabalhadores, name='buscar_trabalhadores'),
    path('trabalhador/<int:user_id>/', views.detalhes_trabalhador, name='detalhes_trabalhador'),

    # Marketplace (core)
    path('marketplace/tipos-servico/', views.lista_tipos_servico, name='lista_tipos_servico'),
    path('marketplace/tipos-servico/novo/', views.criar_tipo_servico, name='criar_tipo_servico'),
    path('marketplace/tipos-servico/<int:tipo_id>/editar/', views.editar_tipo_servico, name='editar_tipo_servico'),
    path('marketplace/tipos-servico/<int:tipo_id>/excluir/', views.excluir_tipo_servico, name='excluir_tipo_servico'),
    path('marketplace/trabalhadores/', views.lista_trabalhadores, name='lista_trabalhadores'),
    path('marketplace/trabalhadores/<int:trabalhador_id>/', views.detalhe_trabalhador, name='detalhe_trabalhador'),
    path('marketplace/meus-servicos/', views.meus_servicos, name='meus_servicos'),
    path('marketplace/meus-servicos/<int:servico_id>/editar/', views.editar_meu_servico, name='editar_meu_servico'),
    path('marketplace/meus-servicos/<int:servico_id>/excluir/', views.excluir_meu_servico, name='excluir_meu_servico'),
    path('marketplace/meus-servicos/<int:servico_id>/toggle-disponivel/', views.toggle_disponivel_agora, name='toggle_disponivel_agora'),

    # Demandas (core)
    path('demandas/publicar/', views.publicar_demanda, name='publicar_demanda'),
    path('demandas/abertas/', views.lista_demandas, name='lista_demandas'),
    path('demandas/<int:demanda_id>/', views.detalhe_demanda, name='detalhe_demanda'),
    path('demandas/inscricao/<int:inscricao_id>/<str:acao>/', views.atualizar_inscricao, name='atualizar_inscricao'),
    path('demandas/minhas/', views.minhas_demandas, name='minhas_demandas'),
    path('demandas/minhas-inscricoes/', views.minhas_inscricoes, name='minhas_inscricoes'),
    
    # Serviços
    path('servico/<int:servico_id>/', views.detalhes_servico, name='detalhes_servico'),
    path('servico/<int:servico_id>/avaliar/', views.avaliar_servico, name='avaliar_servico'),
    path('servico/<int:servico_id>/aceitar/', views.aceitar_servico, name='aceitar_servico'),
    path('servico/<int:servico_id>/recusar/', views.recusar_servico, name='recusar_servico'),
    
    # Controle de jornada
    path('jornada/<int:servico_id>/status/', views.status_jornada_ajax, name='status_jornada_ajax'),
    path('jornada/<int:servico_id>/<str:acao>/', views.controle_jornada, name='controle_jornada'),
]
