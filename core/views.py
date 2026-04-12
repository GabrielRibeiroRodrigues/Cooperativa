from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from datetime import timedelta, date
from contratos.models import Contrato

from .models import (
    User, Servico, Avaliacao, ControleJornada, Mensagem, TipoServico,
    TrabalhadorServico, Demanda, InscricaoDemanda, Notificacao,
    LogAcaoAdmin, Denuncia, TermoUso, Administrador
)
from .forms import (
    RegistroForm, ServicoForm, AvaliacaoForm, MensagemForm, PerfilForm,
    TipoServicoForm, TrabalhadorServicoForm, DemandaForm, InscricaoDemandaForm,
    TermoUsoForm,
)
from decimal import Decimal
import json

# --- IMPORTAÇÃO DO DECORATOR ---
from .decorators import role_required

def _is_admin_custom(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')


def _log_admin_action(request, acao, detalhes, alvo_tipo='', alvo_id=None):
    LogAcaoAdmin.objects.create(
        administrador=request.user,
        acao=acao,
        detalhes=detalhes,
        alvo_tipo=alvo_tipo,
        alvo_id=alvo_id,
        ip_origem=request.META.get('REMOTE_ADDR')
    )


# --- VIEWS PÚBLICAS E AUTENTICAÇÃO ---

def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'contratante':
            return redirect('painel_contratante')
        else:
            return redirect('painel_trabalhador')
    return render(request, 'core/home.html')

def registro_contratante_view(request):
    if request.user.is_authenticated: return redirect('home')
    if request.method == 'POST':
        data = request.POST.copy()
        data['role'] = 'contratante'
        form = RegistroForm(data)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta de contratante criada para {username}! Você já pode fazer login.')
            return redirect('login')
    else:
        form = RegistroForm(initial={'role': 'contratante'})
    return render(request, 'core/cadastro_contratante.html', {'form': form})

def registro_trabalhador_view(request):
    if request.user.is_authenticated: return redirect('home')
    if request.method == 'POST':
        data = request.POST.copy()
        data['role'] = 'trabalhador'
        form = RegistroForm(data)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta de trabalhador criada para {username}! Você já pode fazer login.')
            return redirect('login')
    else:
        form = RegistroForm(initial={'role': 'trabalhador'})
    return render(request, 'core/cadastro_trabalhador.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated: return redirect('home')
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
    logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('home')

@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    
    context = {'form': form, 'avaliacoes': request.user.avaliacoes_recebidas.all()[:5]}
    if request.user.role == 'contratante':
        return render(request, 'core/perfil_contratante.html', context)
    return render(request, 'core/perfil_trabalhador.html', context)


# --- ROTAS EXCLUSIVAS DE CONTRATANTE ---

@login_required
@role_required('contratante')
def painel_contratante(request):
    servicos = request.user.servicos_contratados.all()[:10]
    context = {
        'servicos': servicos,
        'total_servicos': request.user.servicos_contratados.count(),
        'servicos_pendentes': request.user.servicos_contratados.filter(status='pendente').count(),
        'servicos_aceitos': request.user.servicos_contratados.filter(status='aceito').count(),
        'servicos_concluidos': request.user.servicos_contratados.filter(status='concluido').count(),
    }
    return render(request, 'core/painel_contratante.html', context)

@login_required
@role_required('contratante')
def buscar_trabalhadores(request):
    query = request.GET.get('q', '')
    valor_min = request.GET.get('valor_min', '')
    valor_max = request.GET.get('valor_max', '')
    
    trabalhadores = User.objects.filter(role='trabalhador', is_active=True)
    if query:
        trabalhadores = trabalhadores.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(username__icontains=query)
        )
    if valor_min:
        try: trabalhadores = trabalhadores.filter(valor_diario__gte=Decimal(valor_min))
        except: pass
    if valor_max:
        try: trabalhadores = trabalhadores.filter(valor_diario__lte=Decimal(valor_max))
        except: pass
    
    trabalhadores = trabalhadores.order_by('-avaliacao_media', 'valor_diario')
    paginator = Paginator(trabalhadores, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'trabalhadores': page_obj, 'query': query, 'valor_min': valor_min, 'valor_max': valor_max}
    return render(request, 'core/buscar_trabalhadores.html', context)

@login_required
@role_required('contratante')
def detalhes_trabalhador(request, user_id):
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
    
    context = {'trabalhador': trabalhador, 'avaliacoes': avaliacoes, 'form': form}
    return render(request, 'core/detalhes_trabalhador.html', context)

@login_required
@role_required('contratante')
def criar_tipo_servico(request):
    if request.method == 'POST':
        form = TipoServicoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de serviço cadastrado com sucesso.')
            return redirect('lista_tipos_servico')
    else:
        form = TipoServicoForm()
    return render(request, 'core/tipos_servico_form.html', {'form': form, 'titulo': 'Novo tipo de serviço'})

@login_required
@role_required('contratante')
def editar_tipo_servico(request, tipo_id):
    tipo = get_object_or_404(TipoServico, id=tipo_id)
    if request.method == 'POST':
        form = TipoServicoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de serviço atualizado com sucesso.')
            return redirect('lista_tipos_servico')
    else:
        form = TipoServicoForm(instance=tipo)
    return render(request, 'core/tipos_servico_form.html', {'form': form, 'titulo': 'Editar tipo de serviço', 'tipo': tipo})

@login_required
@role_required('contratante')
def excluir_tipo_servico(request, tipo_id):
    tipo = get_object_or_404(TipoServico, id=tipo_id)
    if request.method == 'POST':
        tipo.delete()
        messages.success(request, 'Tipo de serviço removido com sucesso.')
        return redirect('lista_tipos_servico')
    return render(request, 'core/tipos_servico_confirmar_exclusao.html', {'tipo': tipo})

@login_required
@role_required('contratante')
def lista_trabalhadores(request):
    query = request.GET.get('q', '').strip()
    tipo_id = request.GET.get('tipo_servico', '').strip()
    localizacao = request.GET.get('localizacao', '').strip()
    disponivel_agora = request.GET.get('disponivel_agora', '').strip()

    ofertas = TrabalhadorServico.objects.select_related('trabalhador', 'tipo_servico').filter(
        tipo_servico__ativo=True, trabalhador__is_active=True
    )

    if query:
        ofertas = ofertas.filter(
            Q(trabalhador__first_name__icontains=query) | Q(trabalhador__last_name__icontains=query) |
            Q(trabalhador__username__icontains=query) | Q(tipo_servico__nome__icontains=query) |
            Q(descricao_experiencia__icontains=query)
        )
    if tipo_id: ofertas = ofertas.filter(tipo_servico_id=tipo_id)
    if localizacao: ofertas = ofertas.filter(localizacao__icontains=localizacao)
    if disponivel_agora == '1': ofertas = ofertas.filter(disponivel_agora=True)

    ofertas = ofertas.order_by('-disponivel_agora', 'tipo_servico__e_servico_risco', 'trabalhador__first_name')
    context = {
        'ofertas': ofertas,
        'tipos_servico': TipoServico.objects.filter(ativo=True).order_by('nome'),
        'filtros': {'q': query, 'tipo_servico': tipo_id, 'localizacao': localizacao, 'disponivel_agora': disponivel_agora},
    }
    return render(request, 'core/lista_trabalhadores.html', context)

@login_required
@role_required('contratante')
def detalhe_trabalhador(request, trabalhador_id):
    trabalhador = get_object_or_404(User, id=trabalhador_id, role='trabalhador')
    ofertas = trabalhador.servicos_oferecidos.select_related('tipo_servico').filter(tipo_servico__ativo=True)
    servico_chat = Servico.objects.filter(contratante=request.user, trabalhador=trabalhador).exclude(status='cancelado').order_by('-data_criacao').first()

    context = {'trabalhador': trabalhador, 'ofertas': ofertas, 'servico_chat': servico_chat}
    return render(request, 'core/detalhe_trabalhador.html', context)

@login_required
@role_required('contratante')
def publicar_demanda(request):
    if request.method == 'POST':
        form = DemandaForm(request.POST)
        if form.is_valid():
            demanda = form.save(commit=False)
            demanda.contratante = request.user
            demanda.save()
            messages.success(request, 'Demanda publicada com sucesso.')
            return redirect('detalhe_demanda', demanda_id=demanda.id)
    else:
        form = DemandaForm()
    return render(request, 'core/publicar_demanda.html', {'form': form})

@login_required
@role_required('contratante')
def minhas_demandas(request):
    status = request.GET.get('status', '').strip()
    demandas = request.user.demandas_publicadas.select_related('tipo_servico').all()
    if status: demandas = demandas.filter(status=status)
    demandas = demandas.order_by('-data_criacao')
    context = {'demandas': demandas, 'status_atual': status}
    return render(request, 'core/minhas_demandas.html', context)

@login_required
@require_POST
@role_required('contratante')
def atualizar_inscricao(request, inscricao_id, acao):
    inscricao = get_object_or_404(InscricaoDemanda.objects.select_related('demanda', 'trabalhador'), id=inscricao_id, demanda__contratante=request.user)

    if acao == 'aceitar':
        if not inscricao.demanda.esta_aberta:
            messages.error(request, 'Demanda sem vagas disponíveis para novo aceite.')
            return redirect('detalhe_demanda', demanda_id=inscricao.demanda_id)
        inscricao.status = 'aceito'
        inscricao.save(update_fields=['status', 'data_atualizacao'])
        if inscricao.demanda.vagas_disponiveis <= 0:
            inscricao.demanda.status = 'em_andamento'
            inscricao.demanda.save(update_fields=['status', 'data_atualizacao'])
        messages.success(request, f"Inscrição de {inscricao.trabalhador.get_full_name() or inscricao.trabalhador.username} aceita.")
    elif acao == 'rejeitar':
        inscricao.status = 'rejeitado'
        inscricao.save(update_fields=['status', 'data_atualizacao'])
        messages.info(request, 'Inscrição rejeitada.')
    return redirect('detalhe_demanda', demanda_id=inscricao.demanda_id)


# --- ROTAS EXCLUSIVAS DE TRABALHADOR ---

@login_required
@role_required('trabalhador')
def painel_trabalhador(request):
    servicos = request.user.servicos_trabalhados.all()[:10]
    servico_ativo = request.user.servicos_trabalhados.filter(status='aceito').first()
    jornada_ativa = servico_ativo.jornada_ativa if servico_ativo else None
    
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
@role_required('trabalhador')
def aceitar_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id, trabalhador=request.user)
    if servico.status == 'pendente':
        servico_ativo = request.user.servicos_trabalhados.filter(status='aceito').first()
        if servico_ativo:
            messages.error(request, 'Você já possui um serviço ativo. Conclua-o antes de aceitar outro.')
        else:
            servico.status = 'aceito'
            servico.save()
            # Bloqueio de agenda [ETAPA 6]
            from disponibilidade.models import Disponibilidade
            data_ini = servico.data_servico
            data_fim = servico.data_fim or data_ini
            atual = data_ini
            while atual <= data_fim:
                for turno in ['manha', 'tarde', 'integral']:
                    Disponibilidade.objects.update_or_create(
                        trabalhador=servico.trabalhador, data=atual, turno=turno, defaults={'status': 'ocupado'}
                    )
                atual += timedelta(days=1)
            messages.success(request, 'Serviço aceito! Preencha os dados básicos para gerar o contrato.')
            return redirect('contratos:gerar_contrato', servico_id=servico.id)
    else:
        messages.error(request, 'Este serviço não pode ser aceito.')
    return redirect('detalhes_servico', servico_id=servico.id)

@login_required
@role_required('trabalhador')
def recusar_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id, trabalhador=request.user)
    if servico.status == 'pendente':
        servico.status = 'cancelado'
        servico.save()
        messages.info(request, 'Serviço recusado.')
    else:
        messages.error(request, 'Este serviço não pode ser recusado.')
    return redirect('painel_trabalhador')

@login_required
@role_required('trabalhador')
def controle_jornada(request, servico_id, acao):
    servico = get_object_or_404(Servico, id=servico_id, trabalhador=request.user, status='aceito')
    hoje = timezone.now().date()
    controle, created = ControleJornada.objects.get_or_create(servico=servico, data=hoje)
    agora = timezone.now()
    
    if acao == 'iniciar':
        if not servico.pode_iniciar_jornada:
            messages.error(request, 'Não é possível iniciar antes que o contrato esteja assinado e vigente.')
            return redirect('detalhes_servico', servico_id=servico.id)
        if not controle.hora_inicio:
            controle.hora_inicio = agora
            controle.save()
            messages.success(request, 'Jornada de trabalho iniciada!')
        else: messages.warning(request, 'Jornada já foi iniciada hoje.')
    
    elif acao == 'pausar':
        if controle.hora_inicio and not controle.hora_pausa:
            controle.hora_pausa = agora
            controle.save()
            messages.success(request, 'Pausa para almoço iniciada!')
        else: messages.warning(request, 'Não é possível pausar agora.')
    
    elif acao == 'retomar':
        if controle.hora_pausa and not controle.hora_retorno:
            controle.hora_retorno = agora
            controle.save()
            messages.success(request, 'Trabalho retomado!')
        else: messages.warning(request, 'Não é possível retomar agora.')
    
    elif acao == 'finalizar':
        if controle.hora_inicio and not controle.hora_fim:
            controle.hora_fim = agora
            controle.save()
            servico.status = 'concluido'
            servico.save()
            total_horas = controle.total_horas
            if total_horas >= 8: messages.info(request, f'Jornada finalizada! Total: {total_horas}h (atenção: foram trabalhadas 8h ou mais)')
            else: messages.success(request, f'Jornada finalizada! Total: {total_horas}h')
        else: messages.warning(request, 'Não é possível finalizar agora.')
    return redirect('detalhes_servico', servico_id=servico.id)

@login_required
@role_required('trabalhador')
def meus_servicos(request):
    if request.method == 'POST':
        form = TrabalhadorServicoForm(request.POST)
        if form.is_valid():
            servico_oferecido = form.save(commit=False)
            servico_oferecido.trabalhador = request.user
            servico_oferecido.save()
            messages.success(request, 'Serviço adicionado ao seu perfil.')
            return redirect('meus_servicos')
    else:
        form = TrabalhadorServicoForm()
    lista = request.user.servicos_oferecidos.select_related('tipo_servico').all()
    return render(request, 'core/meus_servicos.html', {'form': form, 'lista': lista})

@login_required
@role_required('trabalhador')
def editar_meu_servico(request, servico_id):
    servico_oferecido = get_object_or_404(TrabalhadorServico, id=servico_id, trabalhador=request.user)
    if request.method == 'POST':
        form = TrabalhadorServicoForm(request.POST, instance=servico_oferecido)
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço atualizado com sucesso.')
            return redirect('meus_servicos')
    else:
        form = TrabalhadorServicoForm(instance=servico_oferecido)
    return render(request, 'core/meus_servicos.html', {'form': form, 'edicao': servico_oferecido, 'lista': request.user.servicos_oferecidos.select_related('tipo_servico').all()})

@login_required
@require_POST
@role_required('trabalhador')
def excluir_meu_servico(request, servico_id):
    servico_oferecido = get_object_or_404(TrabalhadorServico, id=servico_id, trabalhador=request.user)
    servico_oferecido.delete()
    messages.success(request, 'Serviço removido do seu perfil.')
    return redirect('meus_servicos')

@login_required
@role_required('trabalhador')
def lista_demandas(request):
    q = request.GET.get('q', '').strip()
    tipo_servico = request.GET.get('tipo_servico', '').strip()
    localizacao = request.GET.get('localizacao', '').strip()
    somente_compativeis = request.GET.get('somente_compativeis', '1')

    tipo_ids_trabalhador = list(request.user.servicos_oferecidos.values_list('tipo_servico_id', flat=True))
    demandas = Demanda.objects.select_related('tipo_servico', 'contratante').filter(status='aberta')

    if somente_compativeis == '1': demandas = demandas.filter(tipo_servico_id__in=tipo_ids_trabalhador)
    if q:
        demandas = demandas.filter(
            Q(titulo__icontains=q) | Q(descricao__icontains=q) | Q(tipo_servico__nome__icontains=q) |
            Q(contratante__first_name__icontains=q) | Q(contratante__last_name__icontains=q)
        )
    if tipo_servico: demandas = demandas.filter(tipo_servico_id=tipo_servico)
    if localizacao: demandas = demandas.filter(localizacao__icontains=localizacao)

    demandas = [d for d in demandas.order_by('data_servico', '-data_criacao') if d.vagas_disponiveis > 0]
    inscricoes_ids = set(request.user.inscricoes_demandas.values_list('demanda_id', flat=True))

    context = {
        'demandas': demandas,
        'tipo_ids_trabalhador': tipo_ids_trabalhador,
        'inscricoes_ids': inscricoes_ids,
        'tipos_servico': request.user.servicos_oferecidos.select_related('tipo_servico').values_list('tipo_servico__id', 'tipo_servico__nome').distinct(),
        'filtros': {'q': q, 'tipo_servico': tipo_servico, 'localizacao': localizacao, 'somente_compativeis': somente_compativeis},
    }
    return render(request, 'core/lista_demandas.html', context)

@login_required
@role_required('trabalhador')
def minhas_inscricoes(request):
    status = request.GET.get('status', '').strip()
    inscricoes = request.user.inscricoes_demandas.select_related('demanda', 'demanda__tipo_servico', 'demanda__contratante')
    if status: inscricoes = inscricoes.filter(status=status)
    inscricoes = inscricoes.order_by('-data_inscricao')
    context = {'inscricoes': inscricoes, 'status_atual': status}
    return render(request, 'core/minhas_inscricoes.html', context)


# --- ROTAS COMPARTILHADAS E AJAX (Sem Decorator) ---

def _usuario_pode_avaliar_servico(servico, usuario):
    if servico.status != 'concluido':
        return False
    if not hasattr(servico, 'contrato_formal') or servico.contrato_formal.status != 'encerrado':
        return False
    return usuario in (servico.contratante, servico.trabalhador)


def _ja_avaliou_servico(servico, usuario):
    return servico.avaliacoes.filter(avaliador=usuario).exists()


@login_required
def avaliar_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id)
    if request.user != servico.contratante and request.user != servico.trabalhador and not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('home')

    if not _usuario_pode_avaliar_servico(servico, request.user):
        messages.error(request, 'A avaliação só é liberada após o encerramento do contrato.')
        return redirect('detalhes_servico', servico_id=servico.id)

    if _ja_avaliou_servico(servico, request.user):
        messages.warning(request, 'Você já avaliou este serviço.')
        return redirect('detalhes_servico', servico_id=servico.id)

    if request.method == 'POST':
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            avaliacao = form.save(commit=False)
            avaliacao.servico = servico
            avaliacao.avaliador = request.user
            avaliacao.save()
            messages.success(request, 'Avaliação enviada!')
            return redirect('detalhes_servico', servico_id=servico.id)
        messages.error(request, 'Não foi possível enviar a avaliação.')
    else:
        form = AvaliacaoForm()

    avaliado = servico.trabalhador if request.user == servico.contratante else servico.contratante
    context = {
        'servico': servico,
        'avaliado': avaliado,
        'form': form,
    }
    return render(request, 'core/avaliar.html', context)

@login_required
def detalhes_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id)
    # AQUI ESTÁ A PERMISSÃO DO ADMIN INCLUÍDA
    if request.user != servico.contratante and request.user != servico.trabalhador and not request.user.is_superuser:
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    
    mensagens = servico.mensagens.all()
    controles = servico.controles_jornada.all()
    
    if request.method == 'POST' and 'mensagem' in request.POST:
        form_mensagem = MensagemForm(request.POST)
        if form_mensagem.is_valid():
            mensagem = form_mensagem.save(commit=False)
            mensagem.servico = servico
            mensagem.remetente = request.user
            mensagem.save()
            messages.success(request, 'Mensagem enviada!')
            return redirect('detalhes_servico', servico_id=servico.id)
    
    form_mensagem = MensagemForm()
    pode_avaliar = _usuario_pode_avaliar_servico(servico, request.user) and not _ja_avaliou_servico(servico, request.user)
    context = {
        'servico': servico, 'mensagens': mensagens, 'controles': controles,
        'form_mensagem': form_mensagem,
        'pode_avaliar': pode_avaliar
    }
    return render(request, 'core/detalhes_servico.html', context)


@login_required
def notificacoes(request):
    notificacoes_qs = request.user.notificacoes.all().order_by('-data_criacao')
    return render(request, 'core/notificacoes.html', {'notificacoes': notificacoes_qs})


@login_required
def notificacoes_polling(request):
    limite = int(request.GET.get('limite', 10))
    itens = request.user.notificacoes.all().order_by('-data_criacao')[:limite]
    nao_lidas = request.user.notificacoes.filter(lida=False).count()
    data = [
        {
            'id': n.id,
            'titulo': n.titulo,
            'mensagem': n.mensagem,
            'tipo': n.tipo,
            'lida': n.lida,
            'data': n.data_criacao.strftime('%d/%m/%Y %H:%M'),
            'link': n.link,
        }
        for n in itens
    ]
    return JsonResponse({'notificacoes': data, 'nao_lidas': nao_lidas})


@login_required
@require_POST
def marcar_notificacoes_lidas(request):
    request.user.notificacoes.filter(lida=False).update(lida=True)
    return JsonResponse({'ok': True})


@login_required
def admin_dashboard(request):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')

    context = {
        'total_usuarios': User.objects.count(),
        'total_contratos': Contrato.objects.count(),
        'demandas_ativas': Demanda.objects.filter(status='aberta').count(),
        'denuncias_pendentes': Denuncia.objects.filter(status='pendente').count(),
        'usuarios_suspendidos': User.objects.filter(is_active=False).count(),
        'total_logs_admin': LogAcaoAdmin.objects.count(),
    }
    return render(request, 'core/admin/dashboard.html', context)


@login_required
def admin_usuarios(request):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    usuarios = User.objects.all().order_by('-date_joined')
    return render(request, 'core/admin/usuarios.html', {'usuarios': usuarios})


@login_required
@require_POST
def admin_usuario_toggle_status(request, user_id):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    usuario = get_object_or_404(User, id=user_id)
    if usuario == request.user:
        messages.error(request, 'Você não pode suspender sua própria conta.')
        return redirect('admin_usuarios')

    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=['is_active'])
    if usuario.is_active:
        acao = 'reativar_usuario'
        msg = f'Usuário {usuario.username} reativado'
    else:
        acao = 'suspender_usuario'
        msg = f'Usuário {usuario.username} suspenso'
    _log_admin_action(request, acao, msg, 'User', usuario.id)
    messages.success(request, msg + '.')
    return redirect('admin_usuarios')


@login_required
def admin_contratos(request):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    contratos = Contrato.objects.select_related('contratante', 'trabalhador', 'servico').order_by('-data_criacao')
    return render(request, 'core/admin/contratos.html', {'contratos': contratos})


@login_required
@require_POST
def admin_contrato_encerrar(request, contrato_id):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    contrato = get_object_or_404(Contrato, id=contrato_id)
    contrato.status = 'encerrado'
    contrato.save(update_fields=['status', 'data_atualizacao'])
    _log_admin_action(request, 'alterar_contrato', f'Contrato {contrato.numero} encerrado manualmente', 'Contrato', contrato.id)
    Notificacao.objects.create(
        usuario=contrato.contratante,
        titulo='Contrato encerrado',
        mensagem=f'O contrato {contrato.numero} foi encerrado pelo administrador.',
        tipo='contrato',
        link=f'/contratos/{contrato.id}/'
    )
    Notificacao.objects.create(
        usuario=contrato.trabalhador,
        titulo='Contrato encerrado',
        mensagem=f'O contrato {contrato.numero} foi encerrado pelo administrador.',
        tipo='contrato',
        link=f'/contratos/{contrato.id}/'
    )
    messages.success(request, 'Contrato encerrado com sucesso.')
    return redirect('admin_contratos')


@login_required
def admin_denuncias(request):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    denuncias = Denuncia.objects.select_related('denunciante', 'denunciado', 'contrato').order_by('status', '-data_criacao')
    return render(request, 'core/admin/denuncias.html', {'denuncias': denuncias})


@login_required
@require_POST
def admin_denuncia_acao(request, denuncia_id, acao):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    denuncia = get_object_or_404(Denuncia, id=denuncia_id)
    observacao = request.POST.get('observacao', '').strip()
    denuncia.observacao_admin = observacao
    denuncia.data_resolucao = timezone.now()
    alvo = denuncia.denunciado

    if acao == 'suspender':
        alvo.is_active = False
        alvo.save(update_fields=['is_active'])
        denuncia.status = 'resolvida'
        _log_admin_action(request, 'resolver_denuncia', f'Denúncia {denuncia.id} resolvida com suspensão do usuário {alvo.username}', 'Denuncia', denuncia.id)
        Notificacao.objects.create(
            usuario=alvo,
            titulo='Conta suspensa',
            mensagem='Sua conta foi suspensa após análise de denúncia.',
            tipo='denuncia',
            link='/perfil/'
        )
    elif acao == 'ignorar':
        denuncia.status = 'ignorada'
        _log_admin_action(request, 'resolver_denuncia', f'Denúncia {denuncia.id} ignorada', 'Denuncia', denuncia.id)
    else:
        messages.error(request, 'Ação inválida.')
        return redirect('admin_denuncias')

    denuncia.save(update_fields=['status', 'observacao_admin', 'data_resolucao'])
    messages.success(request, 'Ação executada com sucesso.')
    return redirect('admin_denuncias')


@login_required
def admin_termos(request):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')

    if request.method == 'POST':
        form = TermoUsoForm(request.POST)
        if form.is_valid():
            termo = form.save(commit=False)
            termo.criado_por = request.user
            if termo.ativo:
                TermoUso.objects.filter(ativo=True).update(ativo=False)
            termo.save()
            _log_admin_action(request, 'criar_termo', f'Termo {termo.versao} criado', 'TermoUso', termo.id)
            messages.success(request, 'Termo de uso salvo com sucesso.')
            return redirect('admin_termos')
    else:
        form = TermoUsoForm()

    termos = TermoUso.objects.all().order_by('-data_publicacao')
    return render(request, 'core/admin/termos.html', {'form': form, 'termos': termos})


@login_required
def admin_tipos_servico(request):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    tipos = TipoServico.objects.all().order_by('nome')
    return render(request, 'core/admin/tipos_servico.html', {'tipos': tipos})


@login_required
@require_POST
def admin_tipo_servico_toggle_risco(request, tipo_id):
    if not _is_admin_custom(request.user):
        messages.error(request, 'Acesso negado.')
        return redirect('home')
    tipo = get_object_or_404(TipoServico, id=tipo_id)
    tipo.e_servico_risco = not tipo.e_servico_risco
    tipo.save(update_fields=['e_servico_risco'])
    _log_admin_action(
        request,
        'editar_tipo_servico',
        f"Tipo de serviço '{tipo.nome}' alterado para risco={tipo.e_servico_risco}",
        'TipoServico',
        tipo.id
    )
    messages.success(request, 'Flag de risco atualizada.')
    return redirect('admin_tipos_servico')

@login_required
def detalhe_demanda(request, demanda_id):
    # Rota mista: contratantes e trabalhadores acessam
    demanda = get_object_or_404(Demanda.objects.select_related('tipo_servico', 'contratante'), id=demanda_id)
    inscricao_usuario = None
    pode_inscrever = False

    if request.user.role == 'trabalhador' or request.user.is_superuser:
        inscricao_usuario = InscricaoDemanda.objects.filter(demanda=demanda, trabalhador=request.user).first() if not request.user.is_superuser else None
        tem_tipo_compativel = request.user.servicos_oferecidos.filter(tipo_servico=demanda.tipo_servico).exists() if not request.user.is_superuser else True
        pode_inscrever = demanda.esta_aberta and tem_tipo_compativel and inscricao_usuario is None

        if request.method == 'POST' and request.user.role == 'trabalhador':
            if not pode_inscrever:
                messages.error(request, 'Você não pode se inscrever nesta demanda.')
                return redirect('detalhe_demanda', demanda_id=demanda.id)
            form = InscricaoDemandaForm(request.POST)
            if form.is_valid():
                inscricao = form.save(commit=False)
                inscricao.demanda = demanda
                inscricao.trabalhador = request.user
                inscricao.save()
                messages.success(request, 'Inscrição enviada com sucesso.')
                return redirect('minhas_inscricoes')
        else: form = InscricaoDemandaForm()
    else: form = None

    inscricoes = None
    if (request.user.role == 'contratante' and demanda.contratante_id == request.user.id) or request.user.is_superuser:
        inscricoes = demanda.inscricoes.select_related('trabalhador').order_by('status', '-data_inscricao')

    context = {'demanda': demanda, 'inscricao_usuario': inscricao_usuario, 'inscricoes': inscricoes, 'pode_inscrever': pode_inscrever, 'form': form}
    return render(request, 'core/detalhe_demanda.html', context)

@login_required
def lista_tipos_servico(request):
    # Rota aberta (ou admin)
    tipos = TipoServico.objects.all().order_by('nome')
    return render(request, 'core/tipos_servico_lista.html', {'tipos': tipos})

@login_required
def status_jornada_ajax(request, servico_id):
    # AQUI ADICIONADO NOT IS_SUPERUSER (Retorna JSON)
    if request.user.role != 'trabalhador' and not request.user.is_superuser:
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    servico = get_object_or_404(Servico, id=servico_id, trabalhador=request.user)
    hoje = timezone.now().date()
    try:
        controle = ControleJornada.objects.get(servico=servico, data=hoje)
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
                    tempo_total = controle.hora_pausa - controle.hora_inicio
                horas_atuais = float(Decimal(tempo_total.total_seconds() / 3600))
        elif controle.status_jornada == 'finalizada':
            horas_atuais = float(controle.total_horas)
        
        return JsonResponse({
            'status': controle.status_jornada, 'alerta_8h': controle.alerta_8_horas, 'total_horas': horas_atuais,
            'hora_inicio': controle.hora_inicio.strftime('%H:%M') if controle.hora_inicio else None,
            'hora_pausa': controle.hora_pausa.strftime('%H:%M') if controle.hora_pausa else None,
            'hora_retorno': controle.hora_retorno.strftime('%H:%M') if controle.hora_retorno else None,
            'hora_fim': controle.hora_fim.strftime('%H:%M') if controle.hora_fim else None,
            'pode_iniciar': servico.pode_iniciar_jornada, 'contrato_pendente': not servico.pode_iniciar_jornada
        })
    except ControleJornada.DoesNotExist:
        return JsonResponse({
            'status': 'nao_iniciada', 'alerta_8h': False, 'total_horas': 0,
            'pode_iniciar': servico.pode_iniciar_jornada, 'contrato_pendente': not servico.pode_iniciar_jornada
        })

@login_required
@require_POST
def toggle_disponivel_agora(request, servico_id):
    # AQUI ADICIONADO NOT IS_SUPERUSER (Retorna JSON)
    if request.user.role != 'trabalhador' and not request.user.is_superuser:
        return JsonResponse({'erro': 'Acesso negado.'}, status=403)

    servico_oferecido = get_object_or_404(TrabalhadorServico, id=servico_id, trabalhador=request.user)
    servico_oferecido.disponivel_agora = not servico_oferecido.disponivel_agora
    servico_oferecido.save(update_fields=['disponivel_agora'])

    return JsonResponse({
        'ok': True, 'disponivel_agora': servico_oferecido.disponivel_agora, 'mensagem': 'Disponibilidade atualizada.'
    })
