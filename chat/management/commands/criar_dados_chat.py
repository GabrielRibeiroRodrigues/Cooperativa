from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Conversa, Mensagem

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria dados de teste para o sistema de chat'

    def handle(self, *args, **options):
        self.stdout.write('=== Teste do Sistema de Chat ===')

        contratante, created = User.objects.get_or_create(
            username='joao_contratante',
            defaults={
                'role': 'contratante',
                'email': 'joao@example.com',
                'telefone': '(11) 98765-4321'
            }
        )
        if created:
            contratante.set_password('senha123')
            contratante.save()
            self.stdout.write(self.style.SUCCESS(f'OK Contratante criado: {contratante.username}'))
        else:
            self.stdout.write(f'INFO Contratante ja existe: {contratante.username}')

        trabalhador, created = User.objects.get_or_create(
            username='maria_trabalhadora',
            defaults={
                'role': 'trabalhador',
                'email': 'maria@example.com',
                'telefone': '(11) 91234-5678',
                'valor_diario': 150.00
            }
        )
        if created:
            trabalhador.set_password('senha123')
            trabalhador.save()
            self.stdout.write(self.style.SUCCESS(f'OK Trabalhador criado: {trabalhador.username}'))
        else:
            self.stdout.write(f'INFO Trabalhador ja existe: {trabalhador.username}')

        conversa = Conversa.objects.filter(
            participantes=contratante
        ).filter(
            participantes=trabalhador
        ).first()

        if not conversa:
            conversa = Conversa.objects.create()
            conversa.participantes.add(contratante, trabalhador)
            self.stdout.write(self.style.SUCCESS(f'OK Conversa criada'))
            
            Mensagem.objects.create(
                conversa=conversa,
                remetente=contratante,
                conteudo="Ola Maria! Preciso de um trabalhador para colheita de cafe."
            )
            
            Mensagem.objects.create(
                conversa=conversa,
                remetente=trabalhador,
                conteudo="Oi Joao! Sim, tenho disponibilidade. Quando seria?"
            )
            
            Mensagem.objects.create(
                conversa=conversa,
                remetente=contratante,
                conteudo="Seria na proxima semana. Voce cobra quanto por dia?"
            )
            
            self.stdout.write(self.style.SUCCESS(f'OK {conversa.mensagens.count()} mensagens criadas'))
        else:
            self.stdout.write(f'INFO Conversa ja existe (ID: {conversa.id})')

        self.stdout.write(f'Total de conversas: {Conversa.objects.count()}')
        self.stdout.write(f'Total de mensagens: {Mensagem.objects.count()}')
        self.stdout.write('Acesse /chat/ - Login: joao_contratante / senha123')
