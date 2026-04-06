from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Contrato, AssinaturaContrato
from .forms import ContratoForm, UploadAssinaturaForm
from .utils import gerar_pdf_contrato
from core.models import Servico

@login_required
def gerar_contrato(request, servico_id):
    """Gera um novo contrato a partir de um serviço aceito"""
    servico = get_object_or_404(Servico, id=servico_id, status='aceito')
    
    # Verifica se já existe um contrato para este serviço
    if hasattr(servico, 'contrato_formal'):
        messages.warning(request, 'Este serviço já possui um contrato gerado.')
        return redirect('contratos:detalhe_contrato', contrato_id=servico.contrato_formal.id)

    if request.method == 'POST':
        form = ContratoForm(request.POST)
        if form.is_valid():
            contrato = form.save(commit=False)
            contrato.servico = servico
            contrato.contratante = servico.contratante
            contrato.trabalhador = servico.trabalhador
            contrato.status = 'aguardando_assinatura'
            contrato.save()
            
            # Etapa 3: Geração do arquivo PDF físico aqui
            gerar_pdf_contrato(contrato)
            
            # Cria a assinatura automática do Contratante (Auto-assinada pelo sistema)
            AssinaturaContrato.objects.create(
                contrato=contrato,
                tipo_assinante='contratante',
                usuario=servico.contratante,
                assinado=True,
                data_assinatura=timezone.now(),
                ip_assinatura=request.META.get('REMOTE_ADDR')
            )
            
            # Cria a entrada pendente para o Trabalhador (Que deverá baixar, assinar e subir o PDF)
            AssinaturaContrato.objects.create(
                contrato=contrato,
                tipo_assinante='trabalhador',
                usuario=servico.trabalhador,
                assinado=False
            )
            
            messages.success(request, 'Contrato gerado com sucesso! Agora você deve baixar o PDF e enviar a versão assinada para que ele se torne vigente.')
            return redirect('contratos:lista_contratos')
    else:
        # Pré-preenchimento com dados do serviço
        initial_data = {
            'valor': servico.valor_acordado,
            'data_inicio': servico.data_servico,
            'data_fim': servico.data_fim,
            'descricao_servico': servico.descricao,
        }
        form = ContratoForm(initial=initial_data)
    
    return render(request, 'contratos/gerar_contrato.html', {'form': form, 'servico': servico})

@login_required
def lista_contratos(request):
    """Lista os contratos do usuário logado"""
    if request.user.role == 'contratante':
        contratos = Contrato.objects.filter(contratante=request.user)
    else:
        contratos = Contrato.objects.filter(trabalhador=request.user)
    
    return render(request, 'contratos/lista_contratos.html', {'contratos': contratos})

@login_required
def detalhe_contrato(request, contrato_id):
    """Exibe detalhes do contrato e permite upload de assinatura"""
    contrato = get_object_or_404(Contrato, id=contrato_id)
    
    # Verifica permissão
    if request.user != contrato.contratante and request.user != contrato.trabalhador:
        messages.error(request, 'Acesso negado.')
        return redirect('home')

    form_upload = None
    if request.user == contrato.trabalhador and contrato.status == 'aguardando_assinatura':
        if request.method == 'POST':
            form_upload = UploadAssinaturaForm(request.POST, request.FILES, instance=contrato)
            if form_upload.is_valid():
                contrato = form_upload.save(commit=False)
                contrato.status = 'vigente'
                contrato.save()
                
                # Marca a assinatura do trabalhador como concluída
                assinatura = contrato.assinaturas.filter(tipo_assinante='trabalhador').first()
                if assinatura:
                    assinatura.assinado = True
                    assinatura.data_assinatura = timezone.now()
                    assinatura.ip_assinatura = request.META.get('REMOTE_ADDR')
                    assinatura.save()
                
                messages.success(request, 'Assinatura enviada com sucesso!')
                return redirect('contratos:detalhe_contrato', contrato_id=contrato.id)
        else:
            form_upload = UploadAssinaturaForm(instance=contrato)

    return render(request, 'contratos/detalhe_contrato.html', {
        'contrato': contrato,
        'form_upload': form_upload
    })
