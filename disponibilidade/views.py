from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Disponibilidade
import calendar
from datetime import date, datetime

User = get_user_model()

@login_required
def agenda_trabalhador(request):
    """Exibe o calendário de disponibilidade do trabalhador logado"""
    if request.user.role != 'trabalhador':
        return render(request, 'core/home.html', {'error': 'Acesso negado'})
    
    # Pega mês e ano da query ou usa atual
    hoje = timezone.now().date()
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))
    
    # Lógica simples para navegar entre meses
    proximo_mes = mes + 1 if mes < 12 else 1
    proximo_ano = ano if mes < 12 else ano + 1
    anterior_mes = mes - 1 if mes > 1 else 12
    anterior_ano = ano if mes > 1 else ano - 1
    
    # Gera os dias do mês para o calendário
    cal = calendar.Calendar(firstweekday=6) # Começa no Domingo
    dias_calendario = cal.monthdays2calendar(ano, mes)
    
    # Pega as disponibilidades já registradas no banco para o mês
    registros = Disponibilidade.objects.filter(
        trabalhador=request.user,
        data__year=ano,
        data__month=mes
    )
    
    # Organiza em um dicionário para busca rápida no template: {data: [registros]}
    mapa_disp = {}
    for r in registros:
        if r.data not in mapa_disp:
            mapa_disp[r.data] = []
        mapa_disp[r.data].append(r)

    context = {
        'mes': mes,
        'ano': ano,
        'nome_mes': calendar.month_name[mes].capitalize(),
        'dias_calendario': dias_calendario,
        'mapa_disp': mapa_disp,
        'hoje': hoje,
        'proximo': {'mes': proximo_mes, 'ano': proximo_ano},
        'anterior': {'mes': anterior_mes, 'ano': anterior_ano},
    }
    return render(request, 'disponibilidade/agenda_trabalhador.html', context)

@login_required
@require_POST
def api_toggle_disponibilidade(request):
    """API para alternar status via AJAX (Clique no Calendário)"""
    data_str = request.POST.get('data')
    turno = request.POST.get('turno') # manha, tarde, integral
    
    try:
        # Extrai ano, mês, dia da string "2026-04-05" de forma robusta
        try:
            parts = data_str.split('-')
            data_obj = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError, TypeError) as e:
            raise ValueError(f"Formato de data inválido: {data_str}")
        
        # Tenta buscar registro existente
        obj, created = Disponibilidade.objects.get_or_create(
            trabalhador=request.user,
            data=data_obj,
            turno=turno,
            defaults={'status': 'bloqueado'}
        )
        
        if not created:
            # Se já existia, alterna: bloqueado -> disponivel (deleta) -> bloqueado
            if obj.status == 'bloqueado':
                obj.delete()
                novo_status = 'disponivel'
            else:
                obj.status = 'bloqueado'
                obj.save()
                novo_status = 'bloqueado'
        else:
            novo_status = 'bloqueado'
            
        return JsonResponse({'status': 'success', 'novo_status': novo_status, 'data': data_str, 'turno': turno})
    except Exception as e:
        print(f"ERRO API DISPONIBILIDADE: {str(e)}")
        print(f"DATA RECEBIDA: {data_str}")
        print(f"TURNO RECEBIDO: {turno}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def consultar_agenda(request, trabalhador_id):
    """View para o contratante visualizar a agenda de um trabalhador"""
    trabalhador = get_object_or_404(User, id=trabalhador_id, role='trabalhador')
    
    # Pega mês e ano da query ou usa atual
    hoje = timezone.now().date()
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))
    
    # Gera os dias do mês
    cal = calendar.Calendar(firstweekday=6)
    dias_calendario = cal.monthdays2calendar(ano, mes)
    
    # Pega as disponibilidades desse trabalhador específico
    registros = Disponibilidade.objects.filter(
        trabalhador=trabalhador,
        data__year=ano,
        data__month=mes
    )
    
    mapa_disp = {}
    for r in registros:
        if r.data not in mapa_disp:
            mapa_disp[r.data] = []
        mapa_disp[r.data].append(r)

    context = {
        'trabalhador_alvo': trabalhador,
        'mes': mes,
        'ano': ano,
        'nome_mes': calendar.month_name[mes].capitalize(),
        'dias_calendario': dias_calendario,
        'mapa_disp': mapa_disp,
        'hoje': hoje,
        'proximo': {'mes': mes + 1 if mes < 12 else 1, 'ano': ano if mes < 12 else ano + 1},
        'anterior': {'mes': mes - 1 if mes > 1 else 12, 'ano': ano if mes > 1 else ano - 1},
    }
    return render(request, 'disponibilidade/consultar_agenda.html', context)
