from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversa(models.Model):
    """Representa uma conversa entre dois usuários"""

    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="conversas", verbose_name="Participantes"
    )
    servico = models.ForeignKey(
        "core.Servico",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversas",
        verbose_name="Serviço Relacionado",
        help_text="Serviço que originou esta conversa (opcional)",
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Criação"
    )
    ultima_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Última Atualização"
    )

    class Meta:
        verbose_name = "Conversa"
        verbose_name_plural = "Conversas"
        ordering = ["-ultima_atualizacao"]

    def __str__(self):
        participantes_nomes = ", ".join([p.username for p in self.participantes.all()])
        return f"Conversa: {participantes_nomes}"

    def get_outra_parte(self, usuario):
        """Retorna o outro participante da conversa (não o usuário atual)"""
        return self.participantes.exclude(id=usuario.id).first()

    def mensagens_nao_lidas(self, usuario):
        """Retorna quantidade de mensagens não lidas para o usuário"""
        return self.mensagens.filter(lida=False).exclude(remetente=usuario).count()

    def ultima_mensagem(self):
        """Retorna a última mensagem da conversa"""
        return self.mensagens.order_by("-data_envio").first()


class Mensagem(models.Model):
    """Representa uma mensagem dentro de uma conversa"""

    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE,
        related_name="mensagens",
        verbose_name="Conversa",
    )
    remetente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensagens_chat_enviadas",
        verbose_name="Remetente",
    )
    conteudo = models.TextField(verbose_name="Conteúdo", help_text="Texto da mensagem")
    data_envio = models.DateTimeField(
        default=timezone.now, verbose_name="Data de Envio"
    )
    lida = models.BooleanField(default=False, verbose_name="Lida")

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ["data_envio"]

    def __str__(self):
        return f"{self.remetente.username}: {self.conteudo[:50]}..."

    def save(self, *args, **kwargs):
        """Ao salvar mensagem, atualiza a última atualização da conversa"""
        super().save(*args, **kwargs)
        self.conversa.ultima_atualizacao = timezone.now()
        self.conversa.save()
