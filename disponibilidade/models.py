from django.db import models


class Disponibilidade(models.Model):
    TURNO_CHOICES = [
        ('manha', 'Manhã'),
        ('tarde', 'Tarde'),
        ('integral', 'Integral'),
    ]
    STATUS_CHOICES = [
        ('disponivel', 'Disponível'),
        ('bloqueado', 'Bloqueado'),
        ('ocupado', 'Ocupado'),
    ]

    trabalhador = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='disponibilidades',
        limit_choices_to={'role': 'trabalhador'},
        verbose_name='Trabalhador'
    )
    data = models.DateField(
        verbose_name='Data'
    )
    turno = models.CharField(
        max_length=10,
        choices=TURNO_CHOICES,
        default='integral',
        verbose_name='Turno'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='disponivel',
        verbose_name='Status'
    )
    motivo_bloqueio = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='Motivo do Bloqueio'
    )

    def __str__(self):
        return (
            f"{self.trabalhador.get_full_name()} — "
            f"{self.data.strftime('%d/%m/%Y')} — "
            f"{self.get_turno_display()} — "
            f"{self.get_status_display()}"
        )

    class Meta:
        verbose_name = 'Disponibilidade'
        verbose_name_plural = 'Disponibilidades'
        ordering = ['data', 'turno']
        unique_together = ['trabalhador', 'data', 'turno']
