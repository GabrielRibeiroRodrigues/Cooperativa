from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
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
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
