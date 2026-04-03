import os
from io import BytesIO
from django.template.loader import get_template
from django.conf import settings
from xhtml2pdf import pisa

def gerar_pdf_contrato(contrato):
    """
    Transforma o template HTML do contrato em um arquivo PDF real.
    Salva o arquivo gerado no campo 'arquivo_pdf' do objeto contrato.
    """
    template_path = 'contratos/pdf_template.html'
    context = {
        'contrato': contrato,
        'empresa': 'Cooperativa Rural Mandik',
        'data_hoje': contrato.data_criacao.strftime('%d de %B de %Y'),
    }
    
    # Renderiza o template para HTML
    template = get_template(template_path)
    html = template.render(context)
    
    # Prepara o buffer para o PDF
    result = BytesIO()
    
    # Gera o PDF
    pisa_status = pisa.CreatePDF(html, dest=result)
    
    if pisa_status.err:
        return None
    
    # Salva o arquivo no modelo Django
    filename = f"contrato_{contrato.numero}.pdf"
    from django.core.files.base import ContentFile
    contrato.arquivo_pdf.save(filename, ContentFile(result.getvalue()), save=True)
    
    return contrato.arquivo_pdf.url
