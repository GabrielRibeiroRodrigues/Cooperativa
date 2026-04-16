"""
Comando de management para popular o banco com dados fictícios.

Uso:
    python manage.py popular_dados            # insere sem apagar
    python manage.py popular_dados --reset    # apaga tudo primeiro
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from chat.models import Conversa, Mensagem
from contratos.models import Contrato
from core.models import (
    Avaliacao,
    ControleJornada,
    Demanda,
    InscricaoDemanda,
    Servico,
    TipoServico,
    TrabalhadorServico,
)
from disponibilidade.models import Disponibilidade

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cpf_valido():
    """Gera um CPF válido (dígitos verificadores pelo módulo 11)."""
    def digito(parcial):
        n = len(parcial) + 1
        soma = sum(d * (n - i) for i, d in enumerate(parcial))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    base = [random.randint(0, 9) for _ in range(9)]
    d1 = digito(base)
    d2 = digito(base + [d1])
    nums = base + [d1, d2]
    return f"{nums[0]}{nums[1]}{nums[2]}.{nums[3]}{nums[4]}{nums[5]}.{nums[6]}{nums[7]}{nums[8]}-{nums[9]}{nums[10]}"


def _data_aleatoria(dias_atras=90, dias_frente=30):
    hoje = date.today()
    delta = random.randint(-dias_atras, dias_frente)
    return hoje + timedelta(days=delta)


def _dt_aleatoria(dias_atras=60):
    agora = timezone.now()
    segundos = random.randint(0, dias_atras * 86400)
    return agora - timedelta(seconds=segundos)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Popula o banco de dados com dados fictícios para desenvolvimento."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Apaga todos os dados não-superusuário antes de recriar.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)

        if options["reset"]:
            self._limpar()

        tipos = self._criar_tipos_servico()
        contratantes = self._criar_contratantes()
        trabalhadores = self._criar_trabalhadores(tipos)
        self._criar_trabalhador_servicos(trabalhadores, tipos)
        servicos = self._criar_servicos(contratantes, trabalhadores)
        self._criar_contratos(servicos)
        self._criar_jornadas(servicos)
        self._criar_avaliacoes(servicos)
        self._criar_demandas(contratantes, tipos)
        self._criar_inscricoes(trabalhadores)
        self._criar_disponibilidades(trabalhadores)
        self._criar_chat(servicos)

        self._resumo()

    # ------------------------------------------------------------------
    # Limpeza
    # ------------------------------------------------------------------

    def _limpar(self):
        self.stdout.write(self.style.WARNING("Removendo dados existentes..."))
        Mensagem.objects.all().delete()
        Conversa.objects.all().delete()
        Disponibilidade.objects.all().delete()
        InscricaoDemanda.objects.all().delete()
        Demanda.objects.all().delete()
        Avaliacao.objects.all().delete()
        ControleJornada.objects.all().delete()
        Contrato.objects.all().delete()
        Servico.objects.all().delete()
        TrabalhadorServico.objects.all().delete()
        TipoServico.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.WARNING("Dados removidos.\n"))

    # ------------------------------------------------------------------
    # Tipos de Serviço
    # ------------------------------------------------------------------

    def _criar_tipos_servico(self):
        dados = [
            ("Plantio",                  "Semeadura manual ou mecanizada de culturas.",        False),
            ("Capina",                   "Remoção de ervas daninhas entre as culturas.",        False),
            ("Colheita",                 "Colheita manual de frutas, grãos ou hortaliças.",     False),
            ("Irrigação",                "Instalação e operação de sistemas de irrigação.",     False),
            ("Poda",                     "Poda de árvores frutíferas e arbustos.",              False),
            ("Manutenção de Cerca",      "Reparo e instalação de cercas e porteiras.",          False),
            ("Aplicação de Agrotóxico",  "Pulverização de defensivos agrícolas.",               True),
            ("Operação de Motosserra",   "Corte e manejo de madeira com motosserra.",           True),
            ("Operação de Máquinas",     "Condução de tratores e colheitadeiras.",              True),
        ]
        tipos = []
        for nome, descricao, risco in dados:
            tipo, _ = TipoServico.objects.get_or_create(
                nome=nome,
                defaults={"descricao": descricao, "e_servico_risco": risco, "ativo": True},
            )
            tipos.append(tipo)
        self.stdout.write(f"  Tipos de serviço: {len(tipos)}")
        return tipos

    # ------------------------------------------------------------------
    # Usuários
    # ------------------------------------------------------------------

    def _criar_contratantes(self):
        perfis = [
            ("Carlos",   "Mendes",    "carlos.mendes"),
            ("Fernanda", "Rocha",     "fernanda.rocha"),
            ("Ricardo",  "Lima",      "ricardo.lima"),
            ("Juliana",  "Barbosa",   "juliana.barbosa"),
        ]
        contratantes = []
        for i, (first, last, username) in enumerate(perfis, start=1):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@exemplo.com",
                    "role": "contratante",
                    "telefone": f"(16) 9{8000 + i}-{1000 + i:04d}",
                    "valor_diario": Decimal("0.00"),
                    "cpf": _cpf_valido(),
                    "is_active": True,
                },
            )
            if created:
                user.set_password("123456")
                user.save()
            contratantes.append(user)
        self.stdout.write(f"  Contratantes: {len(contratantes)}")
        return contratantes

    def _criar_trabalhadores(self, tipos):
        perfis = [
            ("João",      "Silva",      "joao.silva",      Decimal("180.00")),
            ("Maria",     "Souza",      "maria.souza",     Decimal("160.00")),
            ("Pedro",     "Oliveira",   "pedro.oliveira",  Decimal("200.00")),
            ("Ana",       "Pereira",    "ana.pereira",     Decimal("145.00")),
            ("Lucas",     "Santos",     "lucas.santos",    Decimal("220.00")),
            ("Carla",     "Ferreira",   "carla.ferreira",  Decimal("170.00")),
            ("Bruno",     "Costa",      "bruno.costa",     Decimal("190.00")),
            ("Patrícia",  "Almeida",    "patricia.almeida",Decimal("155.00")),
        ]
        trabalhadores = []
        for i, (first, last, username, valor) in enumerate(perfis, start=1):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@exemplo.com",
                    "role": "trabalhador",
                    "telefone": f"(16) 9{9000 + i}-{2000 + i:04d}",
                    "valor_diario": valor,
                    "cpf": _cpf_valido(),
                    "is_active": True,
                },
            )
            if created:
                user.set_password("123456")
                user.save()
            trabalhadores.append(user)
        self.stdout.write(f"  Trabalhadores: {len(trabalhadores)}")
        return trabalhadores

    # ------------------------------------------------------------------
    # TrabalhadorServico
    # ------------------------------------------------------------------

    def _criar_trabalhador_servicos(self, trabalhadores, tipos):
        cidades = [
            "Franca - SP", "Ribeirão Preto - SP", "Batatais - SP",
            "Restinga - SP", "Patrocínio Paulista - SP",
        ]
        experiencias = [
            "Mais de 5 anos de experiência na atividade.",
            "Trabalhei em diversas propriedades da região.",
            "Aprendi com meu pai e tenho prática sólida.",
            "Certificado técnico e vivência no campo.",
            "Excelente referência nos últimos 3 empregadores.",
        ]
        criados = 0
        for trab in trabalhadores:
            qtd = random.randint(2, 4)
            for tipo in random.sample(tipos, qtd):
                _, created = TrabalhadorServico.objects.get_or_create(
                    trabalhador=trab,
                    tipo_servico=tipo,
                    defaults={
                        "valor_diario": trab.valor_diario + Decimal(random.randint(-20, 30)),
                        "disponivel_agora": random.choice([True, True, False]),
                        "localizacao": random.choice(cidades),
                        "descricao_experiencia": random.choice(experiencias),
                    },
                )
                if created:
                    criados += 1
        self.stdout.write(f"  Serviços oferecidos: {criados}")

    # ------------------------------------------------------------------
    # Servico
    # ------------------------------------------------------------------

    def _criar_servicos(self, contratantes, trabalhadores):
        descricoes = [
            "Colheita de laranja nas fileiras 3 a 12 do talhão sul.",
            "Capina entre as linhas de plantio de cana, aproximadamente 2 alqueires.",
            "Plantio de mudas de café em área recém-preparada.",
            "Aplicação de herbicida pós-emergente na lavoura de soja.",
            "Poda de formação em 200 pés de manga tommy.",
            "Instalação de cerca de arame farpado, 500 metros, divisa leste.",
            "Irrigação por aspersão no talhão de hortaliças.",
            "Operação de trator para preparo de solo — 4 horas.",
            "Colheita manual de tomate cereja para entrega no mercado.",
            "Corte e remoção de eucaliptos caídos após tempestade.",
            "Capina e limpeza geral do pomar de goiaba.",
            "Plantio de milho verde, 1 alqueire, adubo incluso.",
        ]
        status_pool = [
            "pendente", "pendente",
            "aceito", "aceito", "aceito",
            "concluido", "concluido", "concluido",
            "cancelado",
        ]
        servicos = []
        pares_usados = set()
        for i, descricao in enumerate(descricoes):
            contratante = random.choice(contratantes)
            trabalhador = random.choice(trabalhadores)
            # evita duplicata contratante+trabalhador (não é restrição do model, mas mantém variedade)
            tentativas = 0
            while (contratante.id, trabalhador.id) in pares_usados and tentativas < 10:
                trabalhador = random.choice(trabalhadores)
                tentativas += 1
            pares_usados.add((contratante.id, trabalhador.id))

            status = status_pool[i % len(status_pool)]
            hoje = date.today()
            if status == "concluido":
                data_inicio = hoje - timedelta(days=random.randint(10, 60))
            elif status == "cancelado":
                data_inicio = hoje - timedelta(days=random.randint(5, 30))
            else:
                data_inicio = hoje + timedelta(days=random.randint(1, 20))

            servico, created = Servico.objects.get_or_create(
                contratante=contratante,
                trabalhador=trabalhador,
                descricao=descricao,
                defaults={
                    "data_servico": data_inicio,
                    "data_fim": data_inicio + timedelta(days=random.randint(0, 3)) if random.random() > 0.5 else None,
                    "valor_acordado": trabalhador.valor_diario + Decimal(random.randint(-10, 20)),
                    "status": status,
                },
            )
            servicos.append(servico)
        self.stdout.write(f"  Serviços: {len(servicos)}")
        return servicos

    # ------------------------------------------------------------------
    # Contrato
    # ------------------------------------------------------------------

    def _criar_contratos(self, servicos):
        status_map = {
            "aceito":    ["aguardando_assinatura", "vigente"],
            "concluido": ["vigente", "encerrado"],
        }
        criados = 0
        for servico in servicos:
            if servico.status not in status_map:
                continue
            if hasattr(servico, "contrato_formal"):
                continue
            status_contrato = random.choice(status_map[servico.status])
            Contrato.objects.create(
                servico=servico,
                contratante=servico.contratante,
                trabalhador=servico.trabalhador,
                status=status_contrato,
                valor=servico.valor_acordado,
                data_inicio=servico.data_servico,
                data_fim=servico.data_fim,
                descricao_servico=servico.descricao,
                e_servico_risco=False,
            )
            criados += 1
        self.stdout.write(f"  Contratos: {criados}")

    # ------------------------------------------------------------------
    # ControleJornada
    # ------------------------------------------------------------------

    def _criar_jornadas(self, servicos):
        criados = 0
        for servico in servicos:
            if servico.status not in ("aceito", "concluido"):
                continue
            if not hasattr(servico, "contrato_formal"):
                continue
            if servico.contrato_formal.status not in ("vigente", "encerrado"):
                continue

            num_dias = random.randint(1, 3)
            base = timezone.now() - timedelta(days=random.randint(3, 30))
            for d in range(num_dias):
                dia = (base + timedelta(days=d)).date()
                hora_inicio = timezone.make_aware(
                    timezone.datetime(dia.year, dia.month, dia.day,
                                      random.randint(6, 8), random.randint(0, 59))
                )
                hora_pausa = hora_inicio + timedelta(hours=random.uniform(3, 4))
                hora_retorno = hora_pausa + timedelta(minutes=random.randint(30, 60))
                hora_fim = hora_retorno + timedelta(hours=random.uniform(2, 4))

                _, created = ControleJornada.objects.get_or_create(
                    servico=servico,
                    data=dia,
                    defaults={
                        "hora_inicio": hora_inicio,
                        "hora_pausa": hora_pausa,
                        "hora_retorno": hora_retorno,
                        "hora_fim": hora_fim,
                        "observacoes": "Jornada registrada normalmente.",
                    },
                )
                if created:
                    criados += 1
        self.stdout.write(f"  Jornadas: {criados}")

    # ------------------------------------------------------------------
    # Avaliacao
    # ------------------------------------------------------------------

    def _criar_avaliacoes(self, servicos):
        comentarios = [
            "Ótimo profissional, muito dedicado e pontual.",
            "Trabalho bem feito, recomendo sem dúvida.",
            "Atendeu às expectativas. Voltaria a contratar.",
            "Serviço realizado com qualidade e cuidado.",
            "Pontualidade exemplar e excelente desempenho.",
            "Bom trabalho, mas poderia ter comunicado melhor os atrasos.",
            "Muito profissional, entregou tudo conforme combinado.",
        ]
        criados = 0
        for servico in servicos:
            if servico.status != "concluido":
                continue
            try:
                Avaliacao.objects.get_or_create(
                    servico=servico,
                    avaliador=servico.contratante,
                    defaults={
                        "nota": random.randint(3, 5),
                        "comentario": random.choice(comentarios),
                    },
                )
                criados += 1
            except Exception:
                pass
        self.stdout.write(f"  Avaliações: {criados}")

    # ------------------------------------------------------------------
    # Demanda
    # ------------------------------------------------------------------

    def _criar_demandas(self, contratantes, tipos):
        cidades = [
            "Franca - SP", "Ribeirão Preto - SP", "Batatais - SP",
            "Restinga - SP", "Patrocínio Paulista - SP",
        ]
        status_pool = ["aberta", "aberta", "aberta", "em_andamento", "encerrada", "cancelada"]
        titulos_base = [
            "Colheita de laranja pera — safra {ano}",
            "Plantio de café arábica — talhão {n}",
            "Capina mecânica — lavoura de cana",
            "Aplicação de defensivos — soja {ano}",
            "Poda e condução de videiras",
            "Manutenção de cercas — perímetro da fazenda",
            "Irrigação — horta orgânica",
            "Colheita de tomate cereja",
            "Operação de trator — preparo de solo",
            "Corte seletivo de madeira",
        ]
        criados = 0
        ano = date.today().year
        for i, titulo_tpl in enumerate(titulos_base, start=1):
            titulo = titulo_tpl.format(ano=ano, n=i)
            contratante = random.choice(contratantes)
            tipo = random.choice(tipos)
            status = status_pool[i % len(status_pool)]
            _, created = Demanda.objects.get_or_create(
                contratante=contratante,
                titulo=titulo,
                defaults={
                    "tipo_servico": tipo,
                    "descricao": f"Precisamos de profissional para {tipo.nome.lower()}. Experiência necessária.",
                    "data_servico": _data_aleatoria(dias_atras=30, dias_frente=45),
                    "valor_oferecido": Decimal(random.randint(130, 320)),
                    "vagas": random.randint(1, 3),
                    "localizacao": random.choice(cidades),
                    "status": status,
                },
            )
            if created:
                criados += 1
        self.stdout.write(f"  Demandas: {criados}")

    # ------------------------------------------------------------------
    # InscricaoDemanda
    # ------------------------------------------------------------------

    def _criar_inscricoes(self, trabalhadores):
        mensagens_pool = [
            "Tenho disponibilidade para a data e experiência na área.",
            "Já realizei esse tipo de serviço diversas vezes e estou disponível.",
            "Posso atender na data combinada. Entre em contato para alinharmos detalhes.",
            "Tenho ferramentas próprias e experiência comprovada.",
            "Disponível e interessado. Tenho ótimas referências.",
        ]
        criados = 0
        for demanda in Demanda.objects.filter(status__in=("aberta", "em_andamento")):
            candidatos = random.sample(trabalhadores, min(len(trabalhadores), random.randint(1, 4)))
            for trab in candidatos:
                _, created = InscricaoDemanda.objects.get_or_create(
                    demanda=demanda,
                    trabalhador=trab,
                    defaults={
                        "mensagem": random.choice(mensagens_pool),
                        "status": random.choice(["pendente", "pendente", "aceito", "rejeitado"]),
                    },
                )
                if created:
                    criados += 1
            # fecha vagas preenchidas
            if demanda.vagas_disponiveis <= 0 and demanda.status == "aberta":
                demanda.status = "em_andamento"
                demanda.save(update_fields=["status", "data_atualizacao"])
        self.stdout.write(f"  Inscrições: {criados}")

    # ------------------------------------------------------------------
    # Disponibilidade
    # ------------------------------------------------------------------

    def _criar_disponibilidades(self, trabalhadores):
        turnos = ["manha", "tarde", "integral"]
        status_pool = ["disponivel", "disponivel", "disponivel", "bloqueado", "ocupado"]
        criados = 0
        hoje = date.today()
        for trab in trabalhadores:
            for delta in range(0, 45):
                dia = hoje + timedelta(days=delta)
                # ~70 % dos dias tem disponibilidade cadastrada
                if random.random() > 0.70:
                    continue
                turno = random.choice(turnos)
                status = random.choice(status_pool)
                _, created = Disponibilidade.objects.get_or_create(
                    trabalhador=trab,
                    data=dia,
                    turno=turno,
                    defaults={
                        "status": status,
                        "motivo_bloqueio": "Compromisso pessoal" if status == "bloqueado" else "",
                    },
                )
                if created:
                    criados += 1
        self.stdout.write(f"  Disponibilidades: {criados}")

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def _criar_chat(self, servicos):
        trocas = [
            [
                ("contratante", "Olá! Tudo bem? Vim confirmar o serviço para a próxima semana."),
                ("trabalhador",  "Oi! Tudo sim, obrigado. Confirmado da minha parte."),
                ("contratante", "Ótimo! Pode chegar às 7h. Vou deixar a porteira aberta."),
                ("trabalhador",  "Perfeito. Estarei lá pontualmente."),
            ],
            [
                ("contratante", "Preciso que traga luvas e protetor solar, temos tudo mais aqui."),
                ("trabalhador",  "Entendido, já tenho esses itens. Algum detalhe extra sobre a área?"),
                ("contratante", "São 3 hectares de café. O talhão fica no lado direito da entrada."),
                ("trabalhador",  "Anotado. Até lá!"),
            ],
            [
                ("trabalhador",  "Bom dia! Cheguei e já estou iniciando o serviço."),
                ("contratante", "Bom dia! Qualquer dúvida pode me chamar."),
            ],
            [
                ("contratante", "Como está o andamento? Conseguiu terminar a seção 1?"),
                ("trabalhador",  "Já terminei a seção 1 e estou na metade da 2."),
                ("contratante", "Excelente ritmo! Obrigado pelo retorno."),
            ],
        ]
        conv_criadas = 0
        msg_criadas = 0
        servicos_com_contrato = [s for s in servicos if hasattr(s, "contrato_formal")]
        amostra = random.sample(servicos_com_contrato, min(len(servicos_com_contrato), 6))

        for servico in amostra:
            conv, created = Conversa.objects.get_or_create(servico=servico)
            if created:
                conv.participantes.add(servico.contratante, servico.trabalhador)
                conv_criadas += 1

            troca = random.choice(trocas)
            base_dt = timezone.now() - timedelta(days=random.randint(1, 10))
            for minutos, (papel, texto) in enumerate(troca, start=1):
                remetente = servico.contratante if papel == "contratante" else servico.trabalhador
                msg = Mensagem.objects.create(
                    conversa=conv,
                    remetente=remetente,
                    conteudo=texto,
                    data_envio=base_dt + timedelta(minutes=minutos * 3),
                    lida=True,
                )
                msg_criadas += 1

        self.stdout.write(f"  Conversas: {conv_criadas} | Mensagens: {msg_criadas}")

    # ------------------------------------------------------------------
    # Resumo final
    # ------------------------------------------------------------------

    def _resumo(self):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 48))
        self.stdout.write(self.style.SUCCESS("  Dados fictícios gerados com sucesso!"))
        self.stdout.write(self.style.SUCCESS("=" * 48))
        linhas = [
            ("Tipos de serviço",    TipoServico.objects.count()),
            ("Contratantes",        User.objects.filter(role="contratante").count()),
            ("Trabalhadores",       User.objects.filter(role="trabalhador").count()),
            ("Serviços oferecidos", TrabalhadorServico.objects.count()),
            ("Serviços solicitados",Servico.objects.count()),
            ("Contratos",           Contrato.objects.count()),
            ("Jornadas",            ControleJornada.objects.count()),
            ("Avaliações",          Avaliacao.objects.count()),
            ("Demandas",            Demanda.objects.count()),
            ("Inscrições",          InscricaoDemanda.objects.count()),
            ("Disponibilidades",    Disponibilidade.objects.count()),
            ("Conversas",           Conversa.objects.count()),
            ("Mensagens",           Mensagem.objects.count()),
        ]
        for label, count in linhas:
            self.stdout.write(f"  {label:<25} {count}")
        self.stdout.write("")
        self.stdout.write("  Senha de todos os usuários: 123456")
        self.stdout.write("  Contratantes: carlos.mendes, fernanda.rocha, ricardo.lima, juliana.barbosa")
        self.stdout.write("  Trabalhadores: joao.silva, maria.souza, pedro.oliveira, ana.pereira,")
        self.stdout.write("                 lucas.santos, carla.ferreira, bruno.costa, patricia.almeida")
