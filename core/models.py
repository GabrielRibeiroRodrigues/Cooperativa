from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = [
        ('contratante', 'Contratante'),
        ('trabalhador', 'Trabalhador'),
        ('admin', 'Administrador'),
    ]
    
    role = models.CharField(
        max_length=12, 
        choices=ROLE_CHOICES, 
        default='trabalhador'
    )
    telefone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name='Telefone'
    )
    valor_diario = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Valor Diário (R$)',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    avaliacao_media = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Avaliação Média',
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('5.00'))
        ]
    )

    cpf = models.CharField(
        max_length=14, 
        unique=True,
        null=True,
        blank=False,
        verbose_name='CPF'
    )
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    def recalcular_avaliacao_media(self):
        """Recalcula a avaliação média baseada nas avaliações recebidas"""
        avaliacoes = self.avaliacoes_recebidas.all()
        if avaliacoes.exists():
            total = sum(av.nota for av in avaliacoes)
            self.avaliacao_media = Decimal(total / avaliacoes.count())
            self.save()
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
            
        super().save(*args, **kwargs)


class Servico(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aceito', 'Aceito'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    contratante = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='servicos_contratados',
        limit_choices_to={'role': 'contratante'},
        verbose_name='Contratante'
    )
    trabalhador = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='servicos_trabalhados',
        limit_choices_to={'role': 'trabalhador'},
        verbose_name='Trabalhador'
    )
    descricao = models.TextField(
        verbose_name='Descrição do Serviço',
        help_text='Descreva o trabalho a ser realizado'
    )
    data_servico = models.DateField(
        verbose_name='Data de Início',
        default=timezone.now
    )
    data_fim = models.DateField(
        verbose_name='Data de Término',
        null=True,
        blank=True,
        help_text='Deixe em branco se for apenas um dia'
    )
    valor_acordado = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name='Valor Acordado (R$)',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pendente',
        verbose_name='Status'
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atualização'
    )
    
    def __str__(self):
        return f"Serviço de {self.contratante.get_full_name()} para {self.trabalhador.get_full_name()} - {self.get_status_display()}"
    
    @property
    def pode_iniciar_jornada(self):
        """Verifica se pode iniciar jornada de trabalho (exige contrato assinado)"""
        if self.status != 'aceito':
            return False
        
        # O serviço só pode iniciar se houver um contrato e ele estiver 'vigente'
        if hasattr(self, 'contrato_formal'):
            return self.contrato_formal.status == 'vigente'
        
        return False
    
    @property
    def jornada_ativa(self):
        """Retorna a jornada ativa se existir"""
        return self.controles_jornada.filter(
            hora_inicio__isnull=False,
            hora_fim__isnull=True
        ).first()
    
    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        ordering = ['-data_criacao']


class Avaliacao(models.Model):
    servico = models.OneToOneField(
        Servico,
        on_delete=models.CASCADE,
        related_name='avaliacao',
        verbose_name='Serviço'
    )
    avaliador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avaliacoes_feitas',
        verbose_name='Avaliador'
    )
    avaliado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avaliacoes_recebidas',
        verbose_name='Avaliado'
    )
    nota = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Nota (1-5 estrelas)'
    )
    comentario = models.TextField(
        blank=True,
        null=True,
        verbose_name='Comentário (opcional)'
    )
    data_avaliacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da Avaliação'
    )
    
    def __str__(self):
        return f"Avaliação de {self.avaliador.get_full_name()} para {self.avaliado.get_full_name()} - {self.nota} estrelas"
    
    def save(self, *args, **kwargs):
        # Define automaticamente o avaliado baseado no serviço e avaliador
        if self.avaliador == self.servico.contratante:
            self.avaliado = self.servico.trabalhador
        else:
            self.avaliado = self.servico.contratante

        super().save(*args, **kwargs)
        # Recálculo da média é feito pelo signal post_save em signals.py
    
    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        unique_together = ['servico', 'avaliador']


class ControleJornada(models.Model):
    servico = models.ForeignKey(
        Servico,
        on_delete=models.CASCADE,
        related_name='controles_jornada',
        verbose_name='Serviço'
    )
    data = models.DateField(
        default=timezone.now,
        verbose_name='Data'
    )
    hora_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Início'
    )
    hora_pausa = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hora da Pausa'
    )
    hora_retorno = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hora do Retorno'
    )
    hora_fim = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Fim'
    )
    total_horas = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total de Horas Trabalhadas'
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observações'
    )
    
    def __str__(self):
        return f"Jornada de {self.servico.trabalhador.get_full_name()} - {self.data} - {self.total_horas}h"
    
    def calcular_total_horas(self):
        """Calcula o total de horas trabalhadas"""
        if not self.hora_inicio or not self.hora_fim:
            return Decimal('0.00')
        
        # Calcula tempo total
        tempo_total = self.hora_fim - self.hora_inicio
        
        # Se houve pausa, subtrai o tempo da pausa
        if self.hora_pausa and self.hora_retorno:
            tempo_pausa = self.hora_retorno - self.hora_pausa
            tempo_total -= tempo_pausa
        
        # Converte para horas decimais
        horas = Decimal(tempo_total.total_seconds() / 3600)
        return round(horas, 2)
    
    def save(self, *args, **kwargs):
        # Calcula automaticamente o total de horas se a jornada foi finalizada
        if self.hora_inicio and self.hora_fim:
            self.total_horas = self.calcular_total_horas()
        
        super().save(*args, **kwargs)
    
    @property
    def status_jornada(self):
        """Retorna o status atual da jornada"""
        if not self.hora_inicio:
            return 'nao_iniciada'
        elif self.hora_pausa and not self.hora_retorno:
            return 'pausada'
        elif not self.hora_fim:
            return 'em_andamento'
        else:
            return 'finalizada'
    
    @property
    def alerta_8_horas(self):
        """Verifica se atingiu 8 horas trabalhadas"""
        if self.status_jornada in ['em_andamento', 'pausada']:
            # Calcula horas já trabalhadas até agora
            agora = timezone.now()
            if self.status_jornada == 'pausada':
                tempo_ate_pausa = self.hora_pausa - self.hora_inicio
                horas_trabalhadas = Decimal(tempo_ate_pausa.total_seconds() / 3600)
            else:
                tempo_total = agora - self.hora_inicio
                if self.hora_pausa and self.hora_retorno:
                    tempo_pausa = self.hora_retorno - self.hora_pausa
                    tempo_total -= tempo_pausa
                elif self.hora_pausa and not self.hora_retorno:
                    # Está pausado, calcular só até a pausa
                    tempo_total = self.hora_pausa - self.hora_inicio
                horas_trabalhadas = Decimal(tempo_total.total_seconds() / 3600)
            
            return horas_trabalhadas >= 8
        elif self.status_jornada == 'finalizada':
            return self.total_horas >= 8
        return False
    
    class Meta:
        verbose_name = 'Controle de Jornada'
        verbose_name_plural = 'Controles de Jornada'
        ordering = ['-data', '-hora_inicio']
        unique_together = ['servico', 'data']


class Mensagem(models.Model):
    servico = models.ForeignKey(
        Servico,
        on_delete=models.CASCADE,
        related_name='mensagens',
        verbose_name='Serviço'
    )
    remetente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mensagens_enviadas',
        verbose_name='Remetente'
    )
    conteudo = models.TextField(
        verbose_name='Mensagem'
    )
    data_envio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Envio'
    )
    lida = models.BooleanField(
        default=False,
        verbose_name='Lida'
    )
    
    def __str__(self):
        return f"Mensagem de {self.remetente.get_full_name()} - {self.data_envio.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['data_envio']


class TipoServico(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Nome')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    e_servico_risco = models.BooleanField(
        default=False,
        verbose_name='Serviço de Risco',
        help_text='Marque para serviços que envolvem agrotóxico, motosserra ou máquinas pesadas',
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Tipo de Serviço'
        verbose_name_plural = 'Tipos de Serviço'
        ordering = ['nome']


class TrabalhadorServico(models.Model):
    trabalhador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='servicos_oferecidos',
        limit_choices_to={'role': 'trabalhador'},
        verbose_name='Trabalhador',
    )
    tipo_servico = models.ForeignKey(
        TipoServico,
        on_delete=models.CASCADE,
        related_name='trabalhadores',
        verbose_name='Tipo de Serviço',
    )
    valor_diario = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Valor Diário (R$)',
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    disponivel_agora = models.BooleanField(
        default=False,
        verbose_name='Disponível Agora',
    )
    localizacao = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Localização',
        help_text='Cidade/Região onde atua',
    )
    descricao_experiencia = models.TextField(
        blank=True,
        verbose_name='Descrição da Experiência',
    )
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trabalhador.get_full_name()} — {self.tipo_servico.nome}"

    class Meta:
        verbose_name = 'Trabalhador por Serviço'
        verbose_name_plural = 'Trabalhadores por Serviço'
        unique_together = ['trabalhador', 'tipo_servico']
        ordering = ['-disponivel_agora', 'trabalhador__first_name']


class Demanda(models.Model):
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('em_andamento', 'Em Andamento'),
        ('encerrada', 'Encerrada'),
        ('cancelada', 'Cancelada'),
    ]

    contratante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='demandas_publicadas',
        limit_choices_to={'role': 'contratante'},
        verbose_name='Contratante',
    )
    tipo_servico = models.ForeignKey(
        TipoServico,
        on_delete=models.CASCADE,
        related_name='demandas',
        verbose_name='Tipo de Serviço',
    )
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descricao = models.TextField(verbose_name='Descrição')
    data_servico = models.DateField(verbose_name='Data do Serviço')
    valor_oferecido = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Valor Oferecido (R$)',
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    vagas = models.PositiveIntegerField(default=1, verbose_name='Número de Vagas')
    localizacao = models.CharField(max_length=200, blank=True, verbose_name='Localização')
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='aberta',
        verbose_name='Status',
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.titulo} — {self.get_status_display()}"

    @property
    def vagas_disponiveis(self):
        aceitos = self.inscricoes.filter(status='aceito').count()
        return self.vagas - aceitos

    @property
    def esta_aberta(self):
        return self.status == 'aberta' and self.vagas_disponiveis > 0

    class Meta:
        verbose_name = 'Demanda'
        verbose_name_plural = 'Demandas'
        ordering = ['-data_criacao']


class InscricaoDemanda(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aceito', 'Aceito'),
        ('rejeitado', 'Rejeitado'),
    ]

    demanda = models.ForeignKey(
        Demanda,
        on_delete=models.CASCADE,
        related_name='inscricoes',
        verbose_name='Demanda',
    )
    trabalhador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscricoes_demandas',
        limit_choices_to={'role': 'trabalhador'},
        verbose_name='Trabalhador',
    )
    mensagem = models.TextField(
        blank=True,
        verbose_name='Mensagem de Apresentação',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status',
    )
    data_inscricao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.trabalhador.get_full_name()} → {self.demanda.titulo}"

    class Meta:
        verbose_name = 'Inscrição em Demanda'
        verbose_name_plural = 'Inscrições em Demandas'
        unique_together = ['demanda', 'trabalhador']
        ordering = ['-data_inscricao']
