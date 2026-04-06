from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from chat.models import Conversa, Mensagem
from core.models import (
    Servico,
    TipoServico,
    Demanda,
    TrabalhadorServico,
    InscricaoDemanda,
)
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = "Cria cenários completos para testar o sistema de chat"

    def handle(self, *args, **options):
        self.stdout.write("=== Criando Cenários de Teste Completos ===\n")

        # Criar usuários
        self.criar_usuarios()
        self.criar_tipos_servico()
        self.criar_servicos()
        self.criar_demandas()
        self.criar_conversas_exemplo()

        self.stdout.write(self.style.SUCCESS("\n🎉 Cenários criados com sucesso!"))
        self.mostrar_resumo()

    def criar_usuarios(self):
        # Contratantes
        contratantes_data = [
            ("joao_contratante", "João Silva", "joao@empresa.com", "(11) 98765-4321"),
            ("maria_empresa", "Maria Santos", "maria@fazenda.com", "(11) 97654-3210"),
            (
                "carlos_fazenda",
                "Carlos Oliveira",
                "carlos@agricola.com",
                "(11) 96543-2109",
            ),
        ]

        for username, nome, email, telefone in contratantes_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": "contratante",
                    "first_name": nome.split()[0],
                    "last_name": " ".join(nome.split()[1:]),
                    "email": email,
                    "telefone": telefone,
                },
            )
            if created:
                user.set_password("senha123")
                user.save()
                self.stdout.write(f"✅ Contratante: {username}")
            else:
                self.stdout.write(f"ℹ️  Contratante já existe: {username}")

        # Trabalhadores
        trabalhadores_data = [
            (
                "maria_trabalhadora",
                "Maria José",
                "maria.jose@email.com",
                "(11) 91234-5678",
                150.00,
            ),
            (
                "pedro_rural",
                "Pedro Costa",
                "pedro@rural.com",
                "(11) 92345-6789",
                180.00,
            ),
            ("ana_agricola", "Ana Souza", "ana@campo.com", "(11) 93456-7890", 160.00),
            ("jose_campo", "José Lima", "jose@trabalho.com", "(11) 94567-8901", 140.00),
        ]

        for username, nome, email, telefone, valor in trabalhadores_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": "trabalhador",
                    "first_name": nome.split()[0],
                    "last_name": " ".join(nome.split()[1:]),
                    "email": email,
                    "telefone": telefone,
                    "valor_diario": Decimal(str(valor)),
                },
            )
            if created:
                user.set_password("senha123")
                user.save()
                self.stdout.write(f"✅ Trabalhador: {username}")
            else:
                self.stdout.write(f"ℹ️  Trabalhador já existe: {username}")

    def criar_tipos_servico(self):
        tipos = [
            ("Colheita de Café", "Colheita manual de grãos de café", False),
            ("Plantio de Milho", "Plantio e preparo de solo para milho", False),
            ("Aplicação de Defensivos", "Aplicação de defensivos agrícolas", True),
            ("Poda de Árvores", "Poda de árvores frutíferas", False),
            ("Ordenha de Gado", "Ordenha manual ou mecânica", False),
        ]

        for nome, descricao, risco in tipos:
            tipo, created = TipoServico.objects.get_or_create(
                nome=nome, defaults={"descricao": descricao, "e_servico_risco": risco}
            )
            if created:
                self.stdout.write(f"✅ Tipo: {nome}")

    def criar_servicos(self):
        # Pegar usuários
        joao = User.objects.get(username="joao_contratante")
        maria_empresa = User.objects.get(username="maria_empresa")
        maria_trab = User.objects.get(username="maria_trabalhadora")
        pedro = User.objects.get(username="pedro_rural")
        ana = User.objects.get(username="ana_agricola")

        servicos_data = [
            (
                joao,
                maria_trab,
                "Colheita de café na fazenda do João. Começar às 7h.",
                date.today() + timedelta(days=1),
                150.00,
                "aceito",
            ),
            (
                maria_empresa,
                pedro,
                "Plantio de milho em 5 hectares.",
                date.today() + timedelta(days=3),
                180.00,
                "pendente",
            ),
            (
                joao,
                ana,
                "Poda das árvores do pomar.",
                date.today() + timedelta(days=2),
                160.00,
                "concluido",
            ),
        ]

        for contratante, trabalhador, desc, data_serv, valor, status in servicos_data:
            servico, created = Servico.objects.get_or_create(
                contratante=contratante,
                trabalhador=trabalhador,
                defaults={
                    "descricao": desc,
                    "data_servico": data_serv,
                    "valor_acordado": Decimal(str(valor)),
                    "status": status,
                },
            )
            if created:
                self.stdout.write(
                    f"✅ Serviço: {contratante.username} → {trabalhador.username} ({status})"
                )

    def criar_demandas(self):
        # Criar demandas
        carlos = User.objects.get(username="carlos_fazenda")
        tipo_colheita = TipoServico.objects.get(nome="Colheita de Café")
        tipo_plantio = TipoServico.objects.get(nome="Plantio de Milho")

        demandas_data = [
            (
                carlos,
                tipo_colheita,
                "Colheita Urgente - Fazenda Carlos",
                "Preciso de 3 trabalhadores para colheita de café. Trabalho de uma semana.",
                date.today() + timedelta(days=5),
                160.00,
                3,
            ),
            (
                carlos,
                tipo_plantio,
                "Plantio de Milho - Safra 2026",
                "Plantio em área de 10 hectares. Experiência necessária.",
                date.today() + timedelta(days=7),
                200.00,
                2,
            ),
        ]

        for contratante, tipo, titulo, desc, data_serv, valor, vagas in demandas_data:
            demanda, created = Demanda.objects.get_or_create(
                contratante=contratante,
                titulo=titulo,
                defaults={
                    "tipo_servico": tipo,
                    "descricao": desc,
                    "data_servico": data_serv,
                    "valor_oferecido": Decimal(str(valor)),
                    "vagas": vagas,
                    "status": "aberta",
                },
            )
            if created:
                self.stdout.write(f"✅ Demanda: {titulo} ({vagas} vagas)")

    def criar_conversas_exemplo(self):
        # Pegar usuários
        joao = User.objects.get(username="joao_contratante")
        maria_empresa = User.objects.get(username="maria_empresa")
        maria_trab = User.objects.get(username="maria_trabalhadora")
        pedro = User.objects.get(username="pedro_rural")

        # Conversa 1: João ↔ Maria Trabalhadora (sobre serviço ativo)
        conversa1, created = self.criar_conversa([joao, maria_trab])
        if created:
            self.criar_mensagens_conversa(
                conversa1,
                [
                    (
                        joao,
                        "Olá Maria! Sobre o serviço de amanhã, você pode chegar às 7h?",
                    ),
                    (
                        maria_trab,
                        "Bom dia João! Sim, posso chegar às 7h. Preciso levar alguma ferramenta?",
                    ),
                    (
                        joao,
                        "Não precisa, temos todas as ferramentas aqui. Muito obrigado!",
                    ),
                    (maria_trab, "Perfeito! Até amanhã então. 😊"),
                ],
            )

        # Conversa 2: Maria Empresa ↔ Pedro (sobre serviço pendente)
        conversa2, created = self.criar_conversa([maria_empresa, pedro])
        if created:
            self.criar_mensagens_conversa(
                conversa2,
                [
                    (
                        maria_empresa,
                        "Oi Pedro! Vi seu perfil e gostaria de conversar sobre o plantio de milho.",
                    ),
                    (
                        pedro,
                        "Oi Maria! Fico feliz pelo interesse. Tenho 5 anos de experiência com plantio.",
                    ),
                    (
                        maria_empresa,
                        "Excelente! São 5 hectares. Você consegue fazer em quantos dias?",
                    ),
                    (
                        pedro,
                        "Com uma equipe, conseguimos fazer em 3 dias. Posso levar mais 2 pessoas.",
                    ),
                    (
                        maria_empresa,
                        "Perfeito! Vou aceitar sua proposta. Quando podemos começar?",
                    ),
                ],
            )

        self.stdout.write(f"✅ {Conversa.objects.count()} conversas criadas")
        self.stdout.write(f"✅ {Mensagem.objects.count()} mensagens criadas")

    def criar_conversa(self, participantes):
        # Verificar se já existe conversa entre esses usuários
        conversa_existente = (
            Conversa.objects.filter(participantes=participantes[0])
            .filter(participantes=participantes[1])
            .first()
        )

        if conversa_existente:
            return conversa_existente, False

        # Criar nova conversa
        conversa = Conversa.objects.create()
        conversa.participantes.add(*participantes)
        return conversa, True

    def criar_mensagens_conversa(self, conversa, mensagens_data):
        for remetente, conteudo in mensagens_data:
            Mensagem.objects.create(
                conversa=conversa, remetente=remetente, conteudo=conteudo
            )

    def mostrar_resumo(self):
        self.stdout.write("\n=== RESUMO DOS DADOS CRIADOS ===")
        self.stdout.write(f"👥 Usuários: {User.objects.count()}")
        self.stdout.write(f"📋 Serviços: {Servico.objects.count()}")
        self.stdout.write(f"📢 Demandas: {Demanda.objects.count()}")
        self.stdout.write(f"💬 Conversas: {Conversa.objects.count()}")
        self.stdout.write(f"📨 Mensagens: {Mensagem.objects.count()}")

        self.stdout.write("\n=== USUÁRIOS PARA TESTE ===")

        self.stdout.write("\n🏢 CONTRATANTES:")
        contratantes = User.objects.filter(role="contratante")
        for c in contratantes:
            self.stdout.write(f"   • {c.username} / senha123 ({c.get_full_name()})")

        self.stdout.write("\n👷 TRABALHADORES:")
        trabalhadores = User.objects.filter(role="trabalhador")
        for t in trabalhadores:
            self.stdout.write(
                f"   • {t.username} / senha123 ({t.get_full_name()}) - R${t.valor_diario}/dia"
            )

        self.stdout.write("\n=== CENÁRIOS DE TESTE ===")
        self.stdout.write(
            "1️⃣  Login como joao_contratante → Ver serviço ativo → Botão mensagem"
        )
        self.stdout.write(
            "2️⃣  Login como maria_trabalhadora → Painel → Botão mensagem no serviço ativo"
        )
        self.stdout.write("3️⃣  Login como pedro_rural → Ver demandas → Botão mensagem")
        self.stdout.write("4️⃣  Login qualquer → /chat/ → Ver conversas existentes")
        self.stdout.write("5️⃣  Testar envio de mensagens em tempo real")

        self.stdout.write(f"\n💡 Acesse: http://127.0.0.1:8000/chat/")
