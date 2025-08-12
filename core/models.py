from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = [
        ('contratante', 'Contratante'),
        ('trabalhador', 'Trabalhador'),
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
        verbose_name='Data do Serviço',
        default=timezone.now
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
        """Verifica se pode iniciar jornada de trabalho"""
        return self.status == 'aceito'
    
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
        
        # Recalcula a média do avaliado
        self.avaliado.recalcular_avaliacao_media()
    
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
                horas_trabalhadas = Decimal(tempo_total.total_seconds() / 3600)
            
            return horas_trabalhadas >= 8
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
