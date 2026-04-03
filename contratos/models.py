from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class Contrato(models.Model):
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('aguardando_assinatura', 'Aguardando Assinatura'),
        ('vigente', 'Vigente'),
        ('encerrado', 'Encerrado'),
    ]

    numero = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Número do Contrato'
    )
    servico = models.OneToOneField(
        'core.Servico',
        on_delete=models.CASCADE,
        related_name='contrato_formal',
        verbose_name='Serviço'
    )
    contratante = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='contratos_como_contratante',
        limit_choices_to={'role': 'contratante'},
        verbose_name='Contratante'
    )
    trabalhador = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='contratos_como_trabalhador',
        limit_choices_to={'role': 'trabalhador'},
        verbose_name='Trabalhador'
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='rascunho',
        verbose_name='Status'
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor do Contrato (R$)',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    data_inicio = models.DateField(
        verbose_name='Data de Início'
    )
    data_fim = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Término'
    )
    descricao_servico = models.TextField(
        verbose_name='Descrição do Serviço'
    )

    e_servico_risco = models.BooleanField(
        default=False,
        verbose_name='Serviço de Risco?',
        help_text='Marque se o serviço envolve atividades de risco.'
    )

    clausula_risco_texto = models.TextField(
        blank=True,
        default='',
        verbose_name='Cláusula de Risco'
    )
    declaracao_epi = models.TextField(
        blank=True,
        default='',
        verbose_name='Declaração de EPI'
    )
    declaracao_ferramentas = models.TextField(
        blank=True,
        default='',
        verbose_name='Declaração de Ferramentas'
    )

    arquivo_pdf = models.FileField(
        upload_to='contratos/pdfs/',
        null=True,
        blank=True,
        verbose_name='PDF do Contrato (Gerado)'
    )
    arquivo_pdf_assinado = models.FileField(
        upload_to='contratos/pdfs_assinados/',
        null=True,
        blank=True,
        verbose_name='PDF Assinado (Upload do Trabalhador)'
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
        return f"{self.numero} — {self.contratante.get_full_name()} / {self.trabalhador.get_full_name()} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._gerar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def _gerar_numero():
        ano = timezone.now().year
        prefixo = f"CONT-{ano}-"
        ultimo = Contrato.objects.filter(numero__startswith=prefixo).order_by('-numero').first()
        if ultimo:
            ultimo_seq = int(ultimo.numero.split('-')[-1])
            novo_seq = ultimo_seq + 1
        else:
            novo_seq = 1
        return f"{prefixo}{novo_seq:05d}"

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-data_criacao']


class AssinaturaContrato(models.Model):
    TIPO_CHOICES = [
        ('contratante', 'Contratante'),
        ('trabalhador', 'Trabalhador'),
    ]

    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name='assinaturas',
        verbose_name='Contrato'
    )
    tipo_assinante = models.CharField(
        max_length=12,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Assinante'
    )
    usuario = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='assinaturas_contrato',
        verbose_name='Usuário'
    )
    assinado = models.BooleanField(
        default=False,
        verbose_name='Assinado?'
    )
    data_assinatura = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data da Assinatura'
    )
    ip_assinatura = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP da Assinatura'
    )

    class Meta:
        verbose_name = 'Assinatura de Contrato'
        verbose_name_plural = 'Assinaturas de Contrato'
        unique_together = ['contrato', 'tipo_assinante']
