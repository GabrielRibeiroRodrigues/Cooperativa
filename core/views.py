from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from .models import User, Servico, Avaliacao, ControleJornada, Mensagem
from .forms import RegistroForm, ServicoForm, AvaliacaoForm, MensagemForm, PerfilForm
from decimal import Decimal
import json

# Create your views here.

def home(request):
    """Página inicial"""
    if request.user.is_authenticated:
        if request.user.role == 'contratante':
            return redirect('painel_contratante')
        else:
            return redirect('painel_trabalhador')
    return render(request, 'core/home.html')


def registro_view(request):
    """Registro de usuário"""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta criada para {username}! Você já pode fazer login.')
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'core/registro.html', {'form': form})


def login_view(request):
    """Login de usuário"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, 'core/login.html')


def logout_view(request):
    """Logout de usuário"""
    logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('home')


@login_required
def perfil_view(request):
    """Visualizar e editar perfil do usuário"""
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    
    context = {
        'form': form,
        'avaliacoes': request.user.avaliacoes_recebidas.all()[:5]
    }
    return render(request, 'core/perfil.html', context)


@login_required
def painel_contratante(request):
    """Painel do contratante"""
    if request.user.role != 'contratante':
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    servicos = request.user.servicos_contratados.all()[:10]
    context = {
        'servicos': servicos,
        'total_servicos': request.user.servicos_contratados.count(),
        'servicos_pendentes': request.user.servicos_contratados.filter(status='pendente').count(),
        'servicos_aceitos': request.user.servicos_contratados.filter(status='aceito').count(),
    }
    return render(request, 'core/painel_contratante.html', context)


@login_required
def painel_trabalhador(request):
    """Painel do trabalhador"""
    if request.user.role != 'trabalhador':
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    servicos = request.user.servicos_trabalhados.all()[:10]
    servico_ativo = request.user.servicos_trabalhados.filter(status='aceito').first()
    jornada_ativa = None
    
    if servico_ativo:
        jornada_ativa = servico_ativo.jornada_ativa
    
    context = {
        'servicos': servicos,
        'servico_ativo': servico_ativo,
        'jornada_ativa': jornada_ativa,
        'total_servicos': request.user.servicos_trabalhados.count(),
        'servicos_pendentes': request.user.servicos_trabalhados.filter(status='pendente').count(),
        'servicos_concluidos': request.user.servicos_trabalhados.filter(status='concluido').count(),
    }
    return render(request, 'core/painel_trabalhador.html', context)


@login_required
def buscar_trabalhadores(request):
    """Buscar trabalhadores disponíveis"""
    if request.user.role != 'contratante':
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    query = request.GET.get('q', '')
    valor_min = request.GET.get('valor_min', '')
    valor_max = request.GET.get('valor_max', '')
    
    trabalhadores = User.objects.filter(role='trabalhador', is_active=True)
    
    if query:
        trabalhadores = trabalhadores.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query)
        )
    
    if valor_min:
        try:
            trabalhadores = trabalhadores.filter(valor_diario__gte=Decimal(valor_min))
        except:
            pass
    
    if valor_max:
        try:
            trabalhadores = trabalhadores.filter(valor_diario__lte=Decimal(valor_max))
        except:
            pass
    
    trabalhadores = trabalhadores.order_by('-avaliacao_media', 'valor_diario')
    
    paginator = Paginator(trabalhadores, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'trabalhadores': page_obj,
        'query': query,
        'valor_min': valor_min,
        'valor_max': valor_max,
    }
    return render(request, 'core/buscar_trabalhadores.html', context)


@login_required
def detalhes_trabalhador(request, user_id):
    """Detalhes do trabalhador e solicitação de serviço"""
    if request.user.role != 'contratante':
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    trabalhador = get_object_or_404(User, id=user_id, role='trabalhador')
    avaliacoes = trabalhador.avaliacoes_recebidas.all()[:5]
    
    if request.method == 'POST':
        form = ServicoForm(request.POST)
        if form.is_valid():
            servico = form.save(commit=False)
            servico.contratante = request.user
            servico.trabalhador = trabalhador
            servico.valor_acordado = trabalhador.valor_diario
            servico.save()
            messages.success(request, 'Solicitação de serviço enviada!')
            return redirect('detalhes_servico', servico_id=servico.id)
    else:
        form = ServicoForm()
    
    context = {
        'trabalhador': trabalhador,
        'avaliacoes': avaliacoes,
        'form': form,
    }
    return render(request, 'core/detalhes_trabalhador.html', context)


@login_required
def detalhes_servico(request, servico_id):
    """Detalhes do serviço"""
    servico = get_object_or_404(Servico, id=servico_id)
    
    # Verificar se o usuário tem permissão para ver este serviço
    if request.user != servico.contratante and request.user != servico.trabalhador:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    mensagens = servico.mensagens.all()
    controles = servico.controles_jornada.all()
    
    # Formulário de mensagem
    if request.method == 'POST':
        if 'mensagem' in request.POST:
            form_mensagem = MensagemForm(request.POST)
            if form_mensagem.is_valid():
                mensagem = form_mensagem.save(commit=False)
                mensagem.servico = servico
                mensagem.remetente = request.user
                mensagem.save()
                messages.success(request, 'Mensagem enviada!')
                return redirect('detalhes_servico', servico_id=servico.id)
        
        elif 'avaliacao' in request.POST:
            if servico.status == 'concluido' and request.user == servico.contratante:
                form_avaliacao = AvaliacaoForm(request.POST)
                if form_avaliacao.is_valid():
                    avaliacao = form_avaliacao.save(commit=False)
                    avaliacao.servico = servico
                    avaliacao.avaliador = request.user
                    avaliacao.save()
                    messages.success(request, 'Avaliação enviada!')
                    return redirect('detalhes_servico', servico_id=servico.id)
    
    form_mensagem = MensagemForm()
    form_avaliacao = AvaliacaoForm() if servico.status == 'concluido' and request.user == servico.contratante else None
    
    context = {
        'servico': servico,
        'mensagens': mensagens,
        'controles': controles,
        'form_mensagem': form_mensagem,
        'form_avaliacao': form_avaliacao,
        'pode_avaliar': servico.status == 'concluido' and request.user == servico.contratante and not hasattr(servico, 'avaliacao')
    }
    return render(request, 'core/detalhes_servico.html', context)


@login_required
def aceitar_servico(request, servico_id):
    """Trabalhador aceita serviço"""
    if request.user.role != 'trabalhador':
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    servico = get_object_or_404(Servico, id=servico_id, trabalhador=request.user)
    
    if servico.status == 'pendente':
        # Verificar se não tem outro serviço ativo
        servico_ativo = request.user.servicos_trabalhados.filter(status='aceito').first()
        if servico_ativo:
            messages.error(request, 'Você já possui um serviço ativo. Conclua-o antes de aceitar outro.')
        else:
            servico.status = 'aceito'
            servico.save()
            messages.success(request, 'Serviço aceito! Você pode iniciar a jornada de trabalho.')
    else:
        messages.error(request, 'Este serviço não pode ser aceito.')
    
    return redirect('detalhes_servico', servico_id=servico.id)


@login_required
def recusar_servico(request, servico_id):
    """Trabalhador recusa serviço"""
    if request.user.role != 'trabalhador':
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    servico = get_object_or_404(Servico, id=servico_id, trabalhador=request.user)
    
    if servico.status == 'pendente':
        servico.status = 'cancelado'
        servico.save()
        messages.info(request, 'Serviço recusado.')
    else:
        messages.error(request, 'Este serviço não pode ser recusado.')
    
    return redirect('painel_trabalhador')


@login_required
def controle_jornada(request, servico_id, acao):
    """Controlar jornada de trabalho"""
    if request.user.role != 'trabalhador':
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    servico = get_object_or_404(Servico, id=servico_id, trabalhador=request.user, status='aceito')
    hoje = timezone.now().date()
    
    # Buscar ou criar controle de jornada para hoje
    controle, created = ControleJornada.objects.get_or_create(
        servico=servico,
        data=hoje
    )
    
    agora = timezone.now()
    
    if acao == 'iniciar':
        if not controle.hora_inicio:
            controle.hora_inicio = agora
            controle.save()
            messages.success(request, 'Jornada de trabalho iniciada!')
        else:
            messages.warning(request, 'Jornada já foi iniciada hoje.')
    
    elif acao == 'pausar':
        if controle.hora_inicio and not controle.hora_pausa:
            controle.hora_pausa = agora
            controle.save()
            messages.success(request, 'Pausa para almoço iniciada!')
        else:
            messages.warning(request, 'Não é possível pausar agora.')
    
    elif acao == 'retomar':
        if controle.hora_pausa and not controle.hora_retorno:
            controle.hora_retorno = agora
            controle.save()
            messages.success(request, 'Trabalho retomado!')
        else:
            messages.warning(request, 'Não é possível retomar agora.')
    
    elif acao == 'finalizar':
        if controle.hora_inicio and not controle.hora_fim:
            controle.hora_fim = agora
            controle.save()
            
            # Se completou o trabalho, marcar serviço como concluído
            servico.status = 'concluido'
            servico.save()
            
            total_horas = controle.total_horas
            if total_horas >= 8:
                messages.info(request, f'Jornada finalizada! Total: {total_horas}h (atenção: foram trabalhadas 8h ou mais)')
            else:
                messages.success(request, f'Jornada finalizada! Total: {total_horas}h')
        else:
            messages.warning(request, 'Não é possível finalizar agora.')
    
    return redirect('detalhes_servico', servico_id=servico.id)


@login_required
def status_jornada_ajax(request, servico_id):
    """Retorna status da jornada via AJAX"""
    if request.user.role != 'trabalhador':
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    servico = get_object_or_404(Servico, id=servico_id, trabalhador=request.user)
    hoje = timezone.now().date()
    
    try:
        controle = ControleJornada.objects.get(servico=servico, data=hoje)
        
        # Calcular horas atuais se estiver em andamento
        horas_atuais = 0
        if controle.status_jornada in ['em_andamento', 'pausada']:
            agora = timezone.now()
            if controle.status_jornada == 'pausada':
                tempo_ate_pausa = controle.hora_pausa - controle.hora_inicio
                horas_atuais = float(Decimal(tempo_ate_pausa.total_seconds() / 3600))
            else:
                tempo_total = agora - controle.hora_inicio
                if controle.hora_pausa and controle.hora_retorno:
                    tempo_pausa = controle.hora_retorno - controle.hora_pausa
                    tempo_total -= tempo_pausa
                elif controle.hora_pausa and not controle.hora_retorno:
                    # Está pausado, calcular só até a pausa
                    tempo_total = controle.hora_pausa - controle.hora_inicio
                horas_atuais = float(Decimal(tempo_total.total_seconds() / 3600))
        elif controle.status_jornada == 'finalizada':
            horas_atuais = float(controle.total_horas)
        
        return JsonResponse({
            'status': controle.status_jornada,
            'alerta_8h': controle.alerta_8_horas,
            'total_horas': horas_atuais,
            'hora_inicio': controle.hora_inicio.strftime('%H:%M') if controle.hora_inicio else None,
            'hora_pausa': controle.hora_pausa.strftime('%H:%M') if controle.hora_pausa else None,
            'hora_retorno': controle.hora_retorno.strftime('%H:%M') if controle.hora_retorno else None,
            'hora_fim': controle.hora_fim.strftime('%H:%M') if controle.hora_fim else None,
        })
    except ControleJornada.DoesNotExist:
        return JsonResponse({
            'status': 'nao_iniciada',
            'alerta_8h': False,
            'total_horas': 0,
        })
