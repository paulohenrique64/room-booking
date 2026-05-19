# 🚀 Quick Reference - Sistema de Agendamento de Salas

## ⚡ Start Rápido

```bash
# Ativar venv
source .venv/bin/activate

# Ir para backend
cd backend

# Iniciar servidor
python manage.py runserver 0.0.0.0:8000
```

## 🔐 Credenciais de Teste

| Usuário | Senha | Tipo | Acesso |
|---------|-------|------|--------|
| admin | admin123 | Admin | Admin + API |
| prof_silva | senha123 | Professor | API |
| prof_santos | senha123 | Professor | API |
| prof_oliveira | senha123 | Professor | API |

## 🌐 URLs

| Recurso | URL |
|---------|-----|
| **Admin** | http://localhost:8000/admin/ |
| **API Base** | http://localhost:8000/api/v1/ |
| **Token** | POST http://localhost:8000/api/token/ |
| **Salas** | GET http://localhost:8000/api/v1/salas/ |
| **Reservas** | GET http://localhost:8000/api/v1/reservas/ |
| **Recursos** | GET http://localhost:8000/api/v1/recursos/ |

## 🔑 JWT Token

### Obter
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"prof_silva","password":"senha123"}'
```

### Usar em Requisições
```bash
curl -H "Authorization: Bearer TOKEN_AQUI" \
  http://localhost:8000/api/v1/salas/
```

## 📡 Endpoints Principais

### Salas
```
GET    /api/v1/salas/
GET    /api/v1/salas/{id}/
GET    /api/v1/salas/{id}/disponibilidade/?data=2026-05-22
```

### Reservas
```
GET    /api/v1/reservas/
POST   /api/v1/reservas/
PATCH  /api/v1/reservas/{id}/
DELETE /api/v1/reservas/{id}/
POST   /api/v1/reservas/{id}/cancelar/
GET    /api/v1/reservas/minhas_reservas/
GET    /api/v1/reservas/proximas_reservas/
```

### Recursos
```
GET    /api/v1/recursos/
```

## 📝 Criar Reserva (Exemplo)

```bash
TOKEN="seu_token_aqui"

curl -X POST http://localhost:8000/api/v1/reservas/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sala": 1,
    "data": "2026-05-22",
    "hora_inicio": "14:00:00",
    "hora_fim": "16:00:00",
    "motivo": "Aula de Engenharia de Software"
  }'
```

## ❌ Cancelar Reserva

```bash
curl -X POST http://localhost:8000/api/v1/reservas/1/cancelar/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Aula cancelada por feriado"
  }'
```

## 🛠️ Comandos Úteis

```bash
# Shell Django
python manage.py shell

# Migrações
python manage.py makemigrations
python manage.py migrate

# Criar user
python manage.py createsuperuser

# Reset banco
python manage.py flush

# Testes
python manage.py test rooms

# DB Shell
python manage.py dbshell
```

## 📊 Estrutura de Dados

```
User (Django Auth)
├── Reserva
│   ├── Sala
│   │   └── Recurso (M2M)
│   ├── HistoricoReserva[]
│   └── CancelamentoReserva?

Recurso ← M2M → Sala
```

## ✅ Validações Automáticas

- ✓ Horário fim > horário início
- ✓ Sem reservas em datas passadas
- ✓ Sem conflito com outras reservas
- ✓ Apenas criador pode editar (ou admin)
- ✓ Histórico auditado automaticamente

## 🔍 Query Úteis (Shell Django)

```python
from django.contrib.auth.models import User
from rooms.models import Sala, Reserva, HistoricoReserva

# Ver usuários
User.objects.all()

# Ver salas
Sala.objects.all()

# Minhas reservas
Reserva.objects.filter(professor__username='prof_silva')

# Reservas num dia
Reserva.objects.filter(data='2026-05-22')

# Histórico de uma reserva
HistoricoReserva.objects.filter(reserva_id=1)

# Criar reserva
Reserva.objects.create(
    sala_id=1,
    professor_id=2,
    data='2026-05-22',
    hora_inicio='14:00',
    hora_fim='16:00',
    motivo='Aula'
)
```

## 🚨 Troubleshooting

| Problema | Solução |
|----------|---------|
| Porta 8000 em uso | `python manage.py runserver 8001` |
| MySQL não conecta | Verificar `.env` e credenciais |
| Migrations error | `python manage.py migrate rooms --fake-initial` |
| Token inválido | `curl /api/token/refresh/` com refresh_token |
| Admin sem acesso | Verificar `is_staff=True` no usuário |

## 📚 Documentação Completa

- **[README.md](./README.md)** - Visão geral
- **[SETUP.md](./SETUP.md)** - Instalação passo a passo
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Referência de APIs
- **[SUMMARY.md](./SUMMARY.md)** - Resumo técnico completo

## 🎯 Próximas Ações

1. Acessar http://localhost:8000/admin/
2. Criar mais salas e usuários
3. Testar APIs com Postman/Insomnia
4. Implementar frontend (React/Vue)
5. Deploy em produção

---

**Status**: ✅ **PRONTO** | **Última atualização**: 19/05/2026
