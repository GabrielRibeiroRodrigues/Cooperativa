from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.lista_conversas, name="lista_conversas"),
    path("<int:conversa_id>/", views.chat_view, name="chat"),
    path("<int:conversa_id>/marcar-lidas/", views.marcar_lidas, name="marcar_lidas"),
    path("iniciar/<int:user_id>/", views.criar_conversa, name="criar_conversa"),
    path("<int:conversa_id>/novas/", views.buscar_novas_mensagens, name="buscar_novas"),
]
