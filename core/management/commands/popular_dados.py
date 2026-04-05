import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Demanda, InscricaoDemanda, TipoServico, TrabalhadorServico


class Command(BaseCommand):
    help = "Popula a aplicação com dados fictícios para testes e demonstrações."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Apaga dados de marketplace/demandas e usuários não superusuários antes de recriar.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)
        User = get_user_model()

        if options["reset"]:
            self.stdout.write(self.style.WARNING("Limpando dados existentes..."))
            InscricaoDemanda.objects.all().delete()
            Demanda.objects.all().delete()
            TrabalhadorServico.objects.all().delete()
            TipoServico.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        tipos_base = [
            ("Plantio", False),
            ("Capina", False),
            ("Colheita", False),
            ("Aplicação de Agrotóxico", True),
            ("Operação de Motosserra", True),
            ("Operação de Máquinas", True),
            ("Irrigação", False),
            ("Manutenção de Cerca", False),
        ]

        tipos_servico = []
        for nome, risco in tipos_base:
            tipo, _ = TipoServico.objects.get_or_create(
                nome=nome,
                defaults={
                    "descricao": f"Serviço de {nome.lower()} na propriedade rural.",
                    "e_servico_risco": risco,
                    "ativo": True,
                },
            )
            tipos_servico.append(tipo)

        nomes_trabalhadores = [
            ("João", "Silva"),
            ("Maria", "Souza"),
            ("Pedro", "Oliveira"),
            ("Ana", "Pereira"),
            ("Lucas", "Santos"),
            ("Carla", "Ferreira"),
            ("Bruno", "Costa"),
            ("Patrícia", "Almeida"),
        ]

        nomes_contratantes = [
            ("Carlos", "Mendes"),
            ("Fernanda", "Rocha"),
            ("Ricardo", "Lima"),
            ("Juliana", "Barbosa"),
        ]

        trabalhadores = []
        for idx, (first_name, last_name) in enumerate(nomes_trabalhadores, start=1):
            username = f"trabalhador{idx}"
            cpf = f"900000000{idx:02d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{username}@exemplo.com",
                    "role": "trabalhador",
                    "telefone": f"1699999{idx:04d}",
                    "valor_diario": Decimal(random.randint(120, 280)),
                    "cpf": cpf,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("123456")
                user.save()
            trabalhadores.append(user)

        contratantes = []
        for idx, (first_name, last_name) in enumerate(nomes_contratantes, start=1):
            username = f"contratante{idx}"
            cpf = f"800000000{idx:02d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{username}@exemplo.com",
                    "role": "contratante",
                    "telefone": f"1633333{idx:04d}",
                    "valor_diario": Decimal("0.00"),
                    "cpf": cpf,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("123456")
                user.save()
            contratantes.append(user)

        cidades = ["Franca - SP", "Ribeirão Preto - SP", "Batatais - SP", "Restinga - SP"]

        # Cada trabalhador oferece de 2 a 4 tipos de serviço.
        for trabalhador in trabalhadores:
            qtd_servicos = random.randint(2, 4)
            for tipo in random.sample(tipos_servico, qtd_servicos):
                TrabalhadorServico.objects.get_or_create(
                    trabalhador=trabalhador,
                    tipo_servico=tipo,
                    defaults={
                        "valor_diario": Decimal(random.randint(110, 320)),
                        "disponivel_agora": random.choice([True, False]),
                        "localizacao": random.choice(cidades),
                        "descricao_experiencia": f"Experiência comprovada em {tipo.nome.lower()}.",
                    },
                )

        demandas = []
        for i in range(1, 13):
            contratante = random.choice(contratantes)
            tipo = random.choice(tipos_servico)
            demanda, _ = Demanda.objects.get_or_create(
                contratante=contratante,
                tipo_servico=tipo,
                titulo=f"Vaga {i} - {tipo.nome}",
                defaults={
                    "descricao": f"Precisamos de profissional para {tipo.nome.lower()} por diária.",
                    "data_servico": timezone.now().date() + timedelta(days=random.randint(1, 30)),
                    "valor_oferecido": Decimal(random.randint(120, 350)),
                    "vagas": random.randint(1, 3),
                    "localizacao": random.choice(cidades),
                    "status": "aberta",
                },
            )
            demandas.append(demanda)

        total_inscricoes = 0
        for demanda in demandas:
            # Match por tipo de serviço do trabalhador.
            candidatos = trabalhadores
            compativeis = [
                t for t in candidatos if t.servicos_oferecidos.filter(tipo_servico=demanda.tipo_servico).exists()
            ]

            if not compativeis:
                continue

            qtd = min(len(compativeis), random.randint(1, 4))
            selecionados = random.sample(compativeis, qtd)

            for trabalhador in selecionados:
                inscricao, created = InscricaoDemanda.objects.get_or_create(
                    demanda=demanda,
                    trabalhador=trabalhador,
                    defaults={
                        "mensagem": f"Tenho interesse na vaga de {demanda.tipo_servico.nome} e disponibilidade para a data.",
                        "status": random.choice(["pendente", "pendente", "aceito", "rejeitado"]),
                    },
                )
                if created:
                    total_inscricoes += 1

            # Se já preencheu vagas com aceitos, marca em andamento.
            if demanda.vagas_disponiveis <= 0 and demanda.status == "aberta":
                demanda.status = "em_andamento"
                demanda.save(update_fields=["status", "data_atualizacao"])

        self.stdout.write(self.style.SUCCESS("Dados fictícios gerados com sucesso."))
        self.stdout.write(f"Tipos de serviço: {TipoServico.objects.count()}")
        self.stdout.write(f"Trabalhadores: {User.objects.filter(role='trabalhador').count()}")
        self.stdout.write(f"Contratantes: {User.objects.filter(role='contratante').count()}")
        self.stdout.write(f"Serviços oferecidos: {TrabalhadorServico.objects.count()}")
        self.stdout.write(f"Demandas: {Demanda.objects.count()}")
        self.stdout.write(f"Novas inscrições criadas nesta execução: {total_inscricoes}")
        self.stdout.write("Login padrão dos usuários criados: senha 123456")
