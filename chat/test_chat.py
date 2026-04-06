"""
Script de teste para o sistema de chat
Cria usuários e conversas de exemplo
"""

from django.contrib.auth import get_user_model
from chat.models import Conversa, Mensagem

User = get_user_model()

# Verificar se já existem usuários de teste
print("=== Teste do Sistema de Chat ===\n")

# Buscar ou criar usuários
contratante, created = User.objects.get_or_create(
    username="joao_contratante",
    defaults={
        "role": "contratante",
        "email": "joao@example.com",
        "telefone": "(11) 98765-4321",
    },
)
if created:
    contratante.set_password("senha123")
    contratante.save()
    print(f"✅ Contratante criado: {contratante.username}")
else:
    print(f"ℹ️  Contratante já existe: {contratante.username}")

trabalhador, created = User.objects.get_or_create(
    username="maria_trabalhadora",
    defaults={
        "role": "trabalhador",
        "email": "maria@example.com",
        "telefone": "(11) 91234-5678",
        "valor_diario": 150.00,
    },
)
if created:
    trabalhador.set_password("senha123")
    trabalhador.save()
    print(f"✅ Trabalhador criado: {trabalhador.username}")
else:
    print(f"ℹ️  Trabalhador já existe: {trabalhador.username}")

# Verificar se já existe conversa entre eles
conversa = (
    Conversa.objects.filter(participantes=contratante)
    .filter(participantes=trabalhador)
    .first()
)

if not conversa:
    # Criar conversa
    conversa = Conversa.objects.create()
    conversa.participantes.add(contratante, trabalhador)
    print(f"\n✅ Conversa criada entre {contratante.username} e {trabalhador.username}")

    # Criar mensagens de teste
    Mensagem.objects.create(
        conversa=conversa,
        remetente=contratante,
        conteudo="Olá Maria! Preciso de um trabalhador para colheita de café.",
    )

    Mensagem.objects.create(
        conversa=conversa,
        remetente=trabalhador,
        conteudo="Oi João! Sim, tenho disponibilidade. Quando seria?",
    )

    Mensagem.objects.create(
        conversa=conversa,
        remetente=contratante,
        conteudo="Seria na próxima semana. Você cobra quanto por dia?",
    )

    print(f"✅ {conversa.mensagens.count()} mensagens criadas")
else:
    print(
        f"\nℹ️  Conversa já existe (ID: {conversa.id}) com {conversa.mensagens.count()} mensagens"
    )

print("\n=== Estatísticas ===")
print(f"Total de conversas: {Conversa.objects.count()}")
print(f"Total de mensagens: {Mensagem.objects.count()}")
print(f"\n💡 Acesse /chat/ para ver a lista de conversas")
print(f"💡 Login: joao_contratante / senha123")
print(f"💡 Login: maria_trabalhadora / senha123")
