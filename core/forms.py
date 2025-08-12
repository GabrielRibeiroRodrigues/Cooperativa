from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import User, Servico, Avaliacao, Mensagem
from decimal import Decimal


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label='Nome')
    last_name = forms.CharField(max_length=30, required=True, label='Sobrenome')
    telefone = forms.CharField(max_length=15, required=False, label='Telefone')
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        label='Tipo de usuário',
        widget=forms.RadioSelect
    )
    valor_diario = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        label='Valor diário (R$)',
        help_text='Apenas para trabalhadores',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'telefone', 'role', 'valor_diario', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS do Bootstrap
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Radio buttons para role
        self.fields['role'].widget.attrs['class'] = 'form-check-input'
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        valor_diario = cleaned_data.get('valor_diario')
        
        if role == 'trabalhador' and not valor_diario:
            raise forms.ValidationError('Trabalhadores devem informar o valor diário.')
        
        return cleaned_data


class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telefone', 'valor_diario']
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email',
            'telefone': 'Telefone',
            'valor_diario': 'Valor diário (R$)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        # Desabilitar valor diário para contratantes
        if self.instance and self.instance.role == 'contratante':
            self.fields['valor_diario'].widget.attrs['readonly'] = True


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['descricao', 'data_servico']
        labels = {
            'descricao': 'Descrição do trabalho',
            'data_servico': 'Data do serviço',
        }
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'data_servico': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['nota', 'comentario']
        labels = {
            'nota': 'Avaliação (1-5 estrelas)',
            'comentario': 'Comentário (opcional)',
        }
        widgets = {
            'nota': forms.Select(choices=[(i, f'{i} estrela{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comentario': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MensagemForm(forms.ModelForm):
    class Meta:
        model = Mensagem
        fields = ['conteudo']
        labels = {
            'conteudo': 'Mensagem',
        }
        widgets = {
            'conteudo': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Digite sua mensagem...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['conteudo'].widget.attrs['class'] = 'form-control'
