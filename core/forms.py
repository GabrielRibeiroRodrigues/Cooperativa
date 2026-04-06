import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import (
    User,
    Servico,
    Avaliacao,
    Mensagem,
    TipoServico,
    TrabalhadorServico,
    Demanda,
    InscricaoDemanda,
)
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

    cpf = forms.CharField(max_length=14, required=True, label='CPF')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'cpf', 'first_name', 'last_name', 'telefone', 'role', 'valor_diario')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].help_text = 'Obrigatório. Mínimo de 4 caracteres. Apenas letras, números e sublinhados (_).'
        # Adicionar classes CSS do Bootstrap
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Radio buttons para role
        self.fields['role'].widget.attrs['class'] = 'form-check-input'

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        
        if cpf:
            cpf_numeros = re.sub(r'\D', '', cpf)
            
            if len(cpf_numeros) != 11 or len(set(cpf_numeros)) == 1:
                raise forms.ValidationError("CPF inválido. Verifique os números digitados.")
            
            for i in range(9, 11):
                soma = sum((int(cpf_numeros[num]) * ((i + 1) - num) for num in range(0, i)))
                digito = ((soma * 10) % 11) % 10
                if digito != int(cpf_numeros[i]):
                    raise forms.ValidationError("CPF inválido. Dígito verificador incorreto.")
            
            if User.objects.filter(cpf=cpf_numeros).exists():
                raise forms.ValidationError("Este CPF já está cadastrado no sistema.")
            
            return cpf_numeros # Retornando sem máscara para o banco
        
        return cpf

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if len(username) < 4:
            raise forms.ValidationError("O nome de usuário deve ter pelo menos 4 caracteres.")

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError("O nome de usuário deve conter apenas letras, números e sublinhados (_), sem espaços.")

        return username
    
    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')

        if telefone:
            padrao = r'^\(\d{2}\) \d{4,5}-\d{4}$'
            
            if not re.match(padrao, telefone):
                raise forms.ValidationError("Digite um telefone válido no formato (XX) XXXXX-XXXX.")
            
            telefone = re.sub(r'\D', '', telefone)

        return telefone
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        valor_diario = cleaned_data.get('valor_diario')

        if role == 'trabalhador' and not valor_diario:
            self.add_error('valor_diario', 'Trabalhadores devem informar o valor diário.')

        if role == 'contratante' and not valor_diario:
            cleaned_data['valor_diario'] = Decimal('0.00')

        return cleaned_data


class PerfilForm(forms.ModelForm):
    class Meta:
        model = User

        fields = ['username', 'first_name', 'last_name', 'cpf', 'email', 'telefone', 'valor_diario']
        labels = {
            'username': 'Nome de usuário',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'cpf': 'CPF',
            'email': 'Email',
            'telefone': 'Telefone',
            'valor_diario': 'Valor diário (R$)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'username' in self.fields:
            self.fields['username'].help_text = 'Obrigatório. Mínimo de 4 caracteres. Apenas letras, números e sublinhados (_).'

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        if self.instance and self.instance.role == 'contratante':
            if 'valor_diario' in self.fields:
                del self.fields['valor_diario']


    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 4:
            raise forms.ValidationError("O nome de usuário deve ter pelo menos 4 caracteres.")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError("O nome de usuário deve conter apenas letras, números e sublinhados (_), sem espaços.")
        return username
    
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            cpf_numeros = re.sub(r'\D', '', cpf)
            
            # Validação matemática
            if len(cpf_numeros) != 11 or len(set(cpf_numeros)) == 1:
                raise forms.ValidationError("CPF inválido. Verifique os números digitados.")
            
            for i in range(9, 11):
                soma = sum((int(cpf_numeros[num]) * ((i + 1) - num) for num in range(0, i)))
                digito = ((soma * 10) % 11) % 10
                if digito != int(cpf_numeros[i]):
                    raise forms.ValidationError("CPF inválido. Dígito verificador incorreto.")
            
            if User.objects.filter(cpf=cpf_numeros).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este CPF já está sendo usado por outra conta.")
            
            return cpf_numeros
        return cpf

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            padrao = r'^\(\d{2}\) \d{4,5}-\d{4}$'
            if not re.match(padrao, telefone):
                raise forms.ValidationError("Digite um telefone válido no formato (XX) XXXXX-XXXX.")
            
            telefone = re.sub(r'\D', '', telefone)
        return telefone


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['descricao', 'data_servico', 'data_fim']
        labels = {
            'descricao': 'Descrição do trabalho',
            'data_servico': 'Data de Início',
            'data_fim': 'Data de Término',
        }
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'data_servico': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_servico')
        data_fim = cleaned_data.get('data_fim')

        if data_inicio and data_fim and data_fim < data_inicio:
            raise forms.ValidationError('A data de término não pode ser anterior à data de início.')
        
        return cleaned_data


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


class TipoServicoForm(forms.ModelForm):
    class Meta:
        model = TipoServico
        fields = ['nome', 'descricao', 'e_servico_risco', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Aplicação de Agrotóxico'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'e_servico_risco': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TrabalhadorServicoForm(forms.ModelForm):
    class Meta:
        model = TrabalhadorServico
        fields = ['tipo_servico', 'valor_diario', 'localizacao', 'descricao_experiencia']
        widgets = {
            'tipo_servico': forms.Select(attrs={'class': 'form-select'}),
            'valor_diario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'localizacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Ribeirão Preto, SP',
            }),
            'descricao_experiencia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva sua experiência com este serviço...',
            }),
        }


class DemandaForm(forms.ModelForm):
    class Meta:
        model = Demanda
        fields = ['tipo_servico', 'titulo', 'descricao', 'data_servico', 'valor_oferecido', 'vagas', 'localizacao']
        widgets = {
            'tipo_servico': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Colheita de café — 3 dias'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva o serviço, requisitos e outras informações relevantes...',
            }),
            'data_servico': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor_oferecido': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'vagas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'localizacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Fazenda Boa Esperança, Franca - SP',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_servico'].queryset = TipoServico.objects.filter(ativo=True)


class InscricaoDemandaForm(forms.ModelForm):
    class Meta:
        model = InscricaoDemanda
        fields = ['mensagem']
        widgets = {
            'mensagem': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Apresente-se e explique por que você é a pessoa certa para este serviço...',
            }),
        }
