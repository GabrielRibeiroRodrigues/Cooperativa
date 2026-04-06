from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Max
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Conversa, Mensagem
from core.models import User


@login_required
def lista_conversas(request):
    """Exibe inbox com todas as conversas do usuário"""
    conversas = (
        Conversa.objects.filter(participantes=request.user)
        .prefetch_related("participantes", "mensagens")
        .annotate(ultima_msg_data=Max("mensagens__data_envio"))
        .order_by("-ultima_msg_data")
    )

    # Adicionar informações extras para cada conversa
    conversas_data = []
    for conversa in conversas:
        outra_parte = conversa.get_outra_parte(request.user)
        ultima_msg = conversa.ultima_mensagem()
        nao_lidas = conversa.mensagens_nao_lidas(request.user)

        conversas_data.append(
            {
                "conversa": conversa,
                "outra_parte": outra_parte,
                "ultima_mensagem": ultima_msg,
                "nao_lidas": nao_lidas,
            }
        )

    context = {
        "conversas_data": conversas_data,
        "total_nao_lidas": sum(c["nao_lidas"] for c in conversas_data),
    }

    return render(request, "chat/lista_conversas.html", context)


@login_required
def chat_view(request, conversa_id):
    """Exibe a tela de conversa e permite enviar mensagens"""
    conversa = get_object_or_404(
        Conversa.objects.prefetch_related("participantes", "mensagens__remetente"),
        id=conversa_id,
    )

    # Verificar se o usuário faz parte da conversa
    if request.user not in conversa.participantes.all():
        messages.error(request, "Você não tem permissão para acessar esta conversa.")
        return redirect("chat:lista_conversas")

    # Marcar mensagens como lidas
    conversa.mensagens.filter(lida=False).exclude(remetente=request.user).update(
        lida=True
    )

    # Processar envio de mensagem
    if request.method == "POST":
        conteudo = request.POST.get("conteudo", "").strip()
        if conteudo:
            Mensagem.objects.create(
                conversa=conversa, remetente=request.user, conteudo=conteudo
            )
            messages.success(request, "Mensagem enviada!")
            return redirect("chat:chat", conversa_id=conversa.id)

    # Buscar todas as mensagens da conversa
    mensagens_list = conversa.mensagens.select_related("remetente").all()
    outra_parte = conversa.get_outra_parte(request.user)

    context = {
        "conversa": conversa,
        "mensagens": mensagens_list,
        "outra_parte": outra_parte,
    }

    return render(request, "chat/chat.html", context)


@login_required
@require_POST
def marcar_lidas(request, conversa_id):
    """Marca mensagens como lidas via AJAX"""
    conversa = get_object_or_404(Conversa, id=conversa_id)

    if request.user not in conversa.participantes.all():
        return JsonResponse({"success": False, "error": "Permissão negada"}, status=403)

    count = (
        conversa.mensagens.filter(lida=False)
        .exclude(remetente=request.user)
        .update(lida=True)
    )

    return JsonResponse({"success": True, "marcadas": count})


@login_required
def criar_conversa(request, user_id):
    """Cria uma nova conversa com outro usuário ou redireciona se já existe"""
    outro_usuario = get_object_or_404(User, id=user_id)

    if outro_usuario == request.user:
        messages.error(request, "Você não pode iniciar uma conversa consigo mesmo.")
        return redirect(
            "core:painel_contratante"
            if request.user.role == "contratante"
            else "core:painel_trabalhador"
        )

    # Verificar se já existe uma conversa entre os dois usuários
    conversa_existente = (
        Conversa.objects.filter(participantes=request.user)
        .filter(participantes=outro_usuario)
        .first()
    )

    if conversa_existente:
        return redirect("chat:chat", conversa_id=conversa_existente.id)

    # Criar nova conversa
    conversa = Conversa.objects.create()
    conversa.participantes.add(request.user, outro_usuario)

    messages.success(request, f"Conversa iniciada com {outro_usuario.username}!")
    return redirect("chat:chat", conversa_id=conversa.id)


@login_required
def buscar_novas_mensagens(request, conversa_id):
    """Endpoint AJAX para polling - retorna novas mensagens desde uma data"""
    conversa = get_object_or_404(Conversa, id=conversa_id)

    if request.user not in conversa.participantes.all():
        return JsonResponse({"error": "Permissão negada"}, status=403)

    # Pegar timestamp da última mensagem conhecida pelo cliente
    ultima_id = request.GET.get("ultima_id", 0)

    # Buscar mensagens novas
    novas_mensagens = (
        conversa.mensagens.filter(id__gt=ultima_id)
        .select_related("remetente")
        .values("id", "remetente__username", "conteudo", "data_envio", "remetente__id")
    )

    # Converter QuerySet para lista
    mensagens_list = list(novas_mensagens)

    # Formatar data_envio para string
    for msg in mensagens_list:
        msg["data_envio"] = msg["data_envio"].strftime("%d/%m/%Y %H:%M")
        msg["e_minha"] = msg["remetente__id"] == request.user.id

    return JsonResponse({"mensagens": mensagens_list, "count": len(mensagens_list)})
