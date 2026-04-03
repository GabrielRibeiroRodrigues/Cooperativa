from django import forms
from .models import Contrato, AssinaturaContrato

class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = [
            'valor', 'data_inicio', 'data_fim', 'descricao_servico', 
            'e_servico_risco', 'clausula_risco_texto', 
            'declaracao_epi', 'declaracao_ferramentas'
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'descricao_servico': forms.Textarea(attrs={'rows': 3}),
            'clausula_risco_texto': forms.Textarea(attrs={'rows': 3}),
            'declaracao_epi': forms.Textarea(attrs={'rows': 2}),
            'declaracao_ferramentas': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class UploadAssinaturaForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ['arquivo_pdf_assinado']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['arquivo_pdf_assinado'].widget.attrs['class'] = 'form-control'
