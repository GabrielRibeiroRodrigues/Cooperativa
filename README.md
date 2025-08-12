# 🌾 Cooperativa Rural

Uma aplicação web desenvolvida em Django para gerenciar trabalhadores rurais de uma cooperativa. O sistema conecta contratantes com trabalhadores rurais, oferecendo funcionalidades completas de gerenciamento de serviços e controle de jornada de trabalho.

## 🚀 Funcionalidades Principais

### Para Contratantes
- ✅ Cadastro e autenticação com email/senha
- 🔍 Busca de trabalhadores por nome e faixa de preço
- ⭐ Visualização de avaliações e histórico dos trabalhadores
- 📋 Envio de solicitações de serviço
- 💬 Chat interno com trabalhadores
- ⭐ Sistema de avaliação por estrelas (1-5)
- 📊 Painel com estatísticas dos serviços contratados

### Para Trabalhadores
- ✅ Cadastro com definição de valor diário
- 📨 Recebimento e gerenciamento de propostas de trabalho
- ⏰ Controle completo de jornada de trabalho:
  - ▶️ Iniciar jornada
  - ⏸️ Pausar para almoço
  - ⏯️ Retomar trabalho
  - ⏹️ Finalizar jornada
- 🚨 Alerta automático ao atingir 8 horas trabalhadas
- 📊 Painel com estatísticas dos serviços realizados
- ⭐ Histórico de avaliações recebidas
- 💬 Chat interno com contratantes

### Funcionalidades Gerais
- 🔐 Sistema de autenticação personalizado
- 👥 Dois tipos de usuários (contratante/trabalhador)
- 💻 Interface responsiva com Bootstrap
- ⚡ Atualizações em tempo real do controle de jornada via AJAX
- 📱 Design adaptativo para dispositivos móveis
- 🗄️ Painel administrativo Django completo

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.12 + Django 5.2
- **Banco de Dados:** SQLite (desenvolvimento)
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript
- **Ícones:** Font Awesome
- **Controle de Versão:** Git

## 📦 Instalação e Configuração

### Pré-requisitos
- Python 3.8 ou superior
- Git

### Passo a Passo

1. **Clone o repositório:**
```bash
git clone https://github.com/GabrielRibeiroRodrigues/Cooperativa.git
cd Cooperativa
```

2. **Crie e ative um ambiente virtual:**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

3. **Instale as dependências:**
```bash
pip install Django Pillow
```

4. **Execute as migrações:**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Crie um superusuário (opcional):**
```bash
python manage.py createsuperuser
```

6. **Inicie o servidor de desenvolvimento:**
```bash
python manage.py runserver
```

7. **Acesse a aplicação:**
- Site principal: http://127.0.0.1:8000/
- Painel administrativo: http://127.0.0.1:8000/admin/

## 📋 Como Usar

### Primeiro Acesso

1. **Registrar-se na aplicação:**
   - Acesse a página inicial
   - Clique em "Cadastrar-se"
   - Escolha seu tipo de usuário (Contratante ou Trabalhador)
   - Preencha os dados solicitados
   - Se for trabalhador, defina seu valor diário

2. **Para Contratantes:**
   - Acesse o painel do contratante
   - Use "Buscar Trabalhadores" para encontrar profissionais
   - Visualize perfis, avaliações e envie solicitações
   - Acompanhe o andamento dos serviços
   - Use o chat para se comunicar
   - Avalie o trabalhador após conclusão

3. **Para Trabalhadores:**
   - Acesse o painel do trabalhador
   - Visualize e responda às propostas recebidas
   - Use o controle de jornada durante o trabalho:
     - Clique "Iniciar" ao começar o trabalho
     - Use "Pausar" para intervalos (almoço)
     - Clique "Retomar" para voltar ao trabalho
     - Use "Finalizar" ao terminar o dia
   - Acompanhe seu histórico e avaliações

### Controle de Jornada

O sistema oferece controle automático de jornada com as seguintes funcionalidades:

- **Registro automático:** Todas as ações são registradas com data/hora
- **Cálculo de horas:** O sistema calcula automaticamente o total trabalhado
- **Alerta de 8 horas:** Notificação ao atingir 8 horas (permite continuar)
- **Persistência:** Os dados são salvos no banco, funcionando mesmo se fechar o navegador
- **Atualizações em tempo real:** Status atualizado automaticamente a cada 30 segundos
- **Um serviço ativo:** Trabalhadores só podem ter um serviço ativo por vez

## 🏗️ Estrutura do Projeto

```
cooperativa_rural/
├── core/                          # App principal
│   ├── migrations/               # Migrações do banco
│   ├── static/core/             # Arquivos estáticos CSS
│   ├── templates/core/          # Templates HTML
│   ├── admin.py                 # Configuração do admin
│   ├── apps.py                  # Configuração do app
│   ├── forms.py                 # Formulários Django
│   ├── models.py                # Modelos do banco
│   ├── signals.py               # Sinais Django
│   ├── urls.py                  # URLs do app
│   └── views.py                 # Views/Controladores
├── cooperativa_rural/           # Configurações do projeto
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py              # Configurações principais
│   ├── urls.py                  # URLs principais
│   └── wsgi.py
├── manage.py                    # Script de gerenciamento
├── db.sqlite3                   # Banco de dados (gerado)
└── README.md                    # Este arquivo
```

## 🎨 Modelos de Dados

### User (Usuário Personalizado)
- Herda de AbstractUser
- Campos adicionais: role, telefone, valor_diario, avaliacao_media

### Servico
- Relaciona contratante e trabalhador
- Status: pendente, aceito, concluído, cancelado
- Inclui descrição, data e valor acordado

### Avaliacao
- Sistema de avaliação 1-5 estrelas
- Comentário opcional
- Recalcula automaticamente a média do usuário

### ControleJornada
- Registra horários de início, pausa, retorno e fim
- Calcula automaticamente total de horas
- Valida regras de negócio (8h de trabalho)

### Mensagem
- Chat simples entre contratante e trabalhador
- Organizado por serviço

## 🔒 Validações e Regras de Negócio

- **Um serviço ativo:** Trabalhadores só podem aceitar um serviço por vez
- **Controle sequencial:** Jornada deve seguir ordem lógica (iniciar → pausar → retomar → finalizar)
- **Persistência de dados:** Controle funciona mesmo fechando o navegador
- **Alerta de 8 horas:** Sistema alerta mas permite continuar trabalhando
- **Validação de usuários:** Contratantes só podem contratar, trabalhadores só podem trabalhar
- **Avaliação única:** Cada serviço pode ter apenas uma avaliação por contratante

## 🎯 Recursos de Usabilidade

- **Interface intuitiva:** Design limpo e fácil navegação
- **Feedback visual:** Alertas, badges de status e cores indicativas
- **Responsividade:** Funciona bem em desktop e mobile
- **Atualização automática:** Status da jornada atualiza sozinho
- **Confirmações:** Diálogos de confirmação para ações importantes
- **Paginação:** Listas grandes são paginadas automaticamente

## 🚀 Próximos Passos / Melhorias Futuras

- [ ] Sistema de notificações por email
- [ ] Relatórios de produtividade em PDF
- [ ] Mapa de localização dos trabalhadores
- [ ] Sistema de pagamento integrado
- [ ] App mobile nativo
- [ ] API REST para integração
- [ ] Backup automático dos dados
- [ ] Sistema de análise de dados

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua funcionalidade (`git checkout -b feature/AmazingFeature`)
3. Faça commit das mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Desenvolvido por

**Gabriel Ribeiro Rodrigues**

- GitHub: [@GabrielRibeiroRodrigues](https://github.com/GabrielRibeiroRodrigues)

---

⭐ **Se este projeto foi útil para você, deixe uma estrela!**

🌾 **Conectando o campo através da tecnologia!**
