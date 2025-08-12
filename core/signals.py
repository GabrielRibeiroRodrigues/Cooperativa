from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Avaliacao

@receiver(post_save, sender=Avaliacao)
@receiver(post_delete, sender=Avaliacao)
def recalcular_avaliacao_media(sender, instance, **kwargs):
    """Recalcula a avaliação média quando uma avaliação é criada, atualizada ou deletada"""
    instance.avaliado.recalcular_avaliacao_media()
