# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2.5 web application for a rural worker cooperative marketplace in Brazil. It connects contractors (contratantes) with rural workers (trabalhadores) for service management, contracts, work-hour tracking, and messaging. Language: Portuguese (pt-br).

## Commands

```bash
# Install dependencies
pip install Django Pillow xhtml2pdf

# Database setup / after model changes
python manage.py makemigrations
python manage.py migrate

# Run development server
python manage.py runserver  # http://127.0.0.1:8000/

# Create admin user
python manage.py createsuperuser

# Django shell
python manage.py shell
```

No test suite exists yet.

## Architecture

**Django MVT** with 4 apps:

| App | Responsibility |
|-----|---------------|
| `core` | Users, services (Servico), demands (Demanda), work hours (ControleJornada), ratings |
| `contratos` | Formal contract lifecycle, PDF generation (xhtml2pdf), digital signatures |
| `disponibilidade` | Worker availability calendar |
| `chat` | Real-time messaging between users |

**Custom User model** (`core.User` extends `AbstractUser`) with three roles: `contratante`, `trabalhador`, `admin`. Role-based access is enforced via `@role_required` decorator in `core/decorators.py`.

## Key Data Flow

1. Contractor searches workers → creates `Servico` (status: `pendente`)
2. Worker accepts → `Servico` status → `aceito`
3. Worker uses `ControleJornada` to clock in/out (AJAX state machine: `iniciar → pausar → retomar → finalizar`)
4. Contractor generates a `Contrato` (PDF) → worker uploads signed PDF
5. Either party evaluates via `Avaliacao` (1–5 stars) → `post_save` signal auto-recalculates `User.avaliacao_media`

Contractors can also post public `Demanda` jobs; workers apply via `InscricaoDemanda`.

## Important Business Rules

- CPF validation uses modulo-11 check digits (`core/forms.py` `RegistroForm`)
- One `ControleJornada` per worker per service per day (unique_together constraint)
- One `Avaliacao` per service per evaluator (unique_together constraint)
- Contract numbering is auto-generated: `CONT-YYYY-NNNNN`
- Work-hour AJAX endpoint polls every 30 seconds (`status_jornada_ajax`)
- `Demanda.esta_aberta` and `vagas_disponiveis` are computed properties

## Frontend

Templates use Bootstrap 5 (CDN) + Font Awesome (CDN) + minimal custom CSS in `core/static/core/style.css`. The current branch (`refatorar-frontend`) is actively modernizing the UI. Base template is `core/templates/core/base.html`.

## Settings Notes

- `AUTH_USER_MODEL = "core.User"` — always use `get_user_model()` in models/forms
- `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Sao_Paulo"`
- `DEBUG = True` and SQLite are for development only
- PDF files are stored under `pdfs/` (generated) and `pdfs_assinados/` (signed uploads)
