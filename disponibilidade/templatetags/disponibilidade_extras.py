from django import template
from datetime import date

register = template.Library()

@register.filter(name='split_commas_and_colons')
def split_commas_and_colons(value):
    """Transforma 'cod:Nome,cod2:Nome2' em [('cod', 'Nome'), ...]"""
    items = value.split(',')
    return [item.split(':') for item in items]

@register.simple_tag
def get_status(mapa_disp, ano, mes, dia, turno_cod):
    """Verifica o status de um turno a partir de ano, mês e dia"""
    try:
        data_obj = date(int(ano), int(mes), int(dia))
    except:
        return 'disponivel'

    lista_reg = mapa_disp.get(data_obj, [])
    for reg in lista_reg:
        if reg.turno == turno_cod:
            return reg.status
            
    return 'disponivel'
