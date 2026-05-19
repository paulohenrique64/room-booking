# Sistema de Agendamento de Salas - Documentação da API

## 🎯 Visão Geral

Backend completo em Django para gerenciar reservas de salas em universidade federal com:
- ✅ Detecção automática de conflitos de horários
- ✅ Sistema de cancelamentos com auditoria completa
- ✅ Dois papéis de usuários: Admin e Professor
- ✅ APIs RESTful com autenticação JWT
- ✅ Admin Django customizado para gestão de dados

## 🔐 Autenticação

### Obter Token JWT

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "prof_silva",
    "password": "senha123"
  }'
```

**Resposta:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cC..."
}
```

### Usar Token em Requisições

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  http://localhost:8000/api/v1/salas/
```

### Renovar Token

```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<REFRESH_TOKEN>"}'
```

## 📋 Endpoints da API

### Salas

#### Listar todas as salas
```
GET /api/v1/salas/
```

**Resposta:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "nome": "Sala 101",
      "predio": "Bloco A",
      "andar": 1,
      "capacidade": 30,
      "recursos": [
        {"id": 1, "nome": "Projetor", "ativo": true}
      ],
      "localizacao": "Bloco A - Andar 1"
    }
  ]
}
```

#### Verificar disponibilidade de uma sala
```
GET /api/v1/salas/{id}/disponibilidade/?data=2026-05-20
```

**Query Parameters:**
- `data` (obrigatório): Data no formato YYYY-MM-DD

**Resposta:**
```json
{
  "sala": {
    "id": 1,
    "nome": "Sala 101",
    "capacidade": 30,
    "localizacao": "Bloco A - Andar 1"
  },
  "data": "2026-05-20",
  "horarios_bloqueados": [
    {
      "inicio": "08:00:00",
      "fim": "10:00:00",
      "professor": "João Silva"
    }
  ],
  "disponivel": false
}
```

### Reservas

#### Criar nova reserva
```
POST /api/v1/reservas/
Content-Type: application/json

{
  "sala": 1,
  "data": "2026-05-22",
  "hora_inicio": "14:00:00",
  "hora_fim": "16:00:00",
  "motivo": "Aula de Engenharia de Software"
}
```

**Validações:**
- Horário de fim deve ser posterior ao horário de início
- Não pode fazer reserva para datas passadas
- Não pode conflitar com reservas ativas na mesma sala

**Resposta (201 Created):**
```json
{
  "id": 1,
  "sala": {...},
  "professor": {...},
  "data": "2026-05-22",
  "hora_inicio": "14:00:00",
  "hora_fim": "16:00:00",
  "motivo": "Aula de Engenharia de Software",
  "status": "ativa",
  "duracao": "2h 0min"
}
```

#### Listar minhas reservas
```
GET /api/v1/reservas/minhas_reservas/
GET /api/v1/reservas/minhas_reservas/?status=ativa
GET /api/v1/reservas/minhas_reservas/?data=2026-05-22
```

#### Listar próximas reservas (próximos 30 dias)
```
GET /api/v1/reservas/proximas_reservas/
```

#### Cancelar uma reserva
```
POST /api/v1/reservas/{id}/cancelar/
Content-Type: application/json

{
  "motivo": "Aula cancelada por feriado prolongado"
}
```

**Resposta (200 OK):**
```json
{
  "sucesso": "Reserva cancelada com sucesso"
}
```

#### Editar uma reserva (apenas professor criador)
```
PATCH /api/v1/reservas/{id}/
Content-Type: application/json

{
  "hora_inicio": "15:00:00",
  "hora_fim": "17:00:00"
}
```

#### Deletar uma reserva
```
DELETE /api/v1/reservas/{id}/
```

### Recursos

#### Listar todos os recursos
```
GET /api/v1/recursos/
```

**Resposta:**
```json
{
  "count": 6,
  "results": [
    {
      "id": 1,
      "nome": "Projetor",
      "descricao": "Projetor multimídia para apresentações",
      "ativo": true
    }
  ]
}
```

## 👤 Papéis de Usuários

### Administrador
- Username: `admin`
- Senha: `admin123`
- Acesso: Admin Django (`/admin/`)
- Permissões:
  - ✅ Gerenciar cadastro de salas
  - ✅ Editar informações de salas e recursos
  - ✅ Gerenciar usuários
  - ✅ Visualizar todas as reservas do sistema
  - ✅ Cancelar reservas de qualquer professor
  - ✅ Ver histórico completo e cancelamentos

### Professores
- Exemplos: `prof_silva`, `prof_santos`, `prof_oliveira`
- Senha: `senha123`
- Acesso: APIs RESTful
- Permissões:
  - ✅ Visualizar salas disponíveis
  - ✅ Criar reservas
  - ✅ Cancelar suas próprias reservas
  - ✅ Acompanhar seu histórico de agendamentos

## 📊 Modelos de Dados

### Recurso
```
id: int (PK)
nome: string[100] (unique)
descricao: text
ativo: bool
criado_em: datetime (auto)
atualizado_em: datetime (auto)
```

### Sala
```
id: int (PK)
nome: string[100]
predio: string[100]
andar: int
capacidade: int (positivo)
descricao: text
recursos: M2M → Recurso
ativa: bool
criado_em: datetime (auto)
atualizado_em: datetime (auto)
unique_together: (predio, andar, nome)
```

### Reserva
```
id: int (PK)
sala: FK → Sala
professor: FK → User
data: date
hora_inicio: time
hora_fim: time
motivo: string[255]
status: enum('ativa', 'cancelada', 'finalizada')
criado_em: datetime (auto)
atualizado_em: datetime (auto)
indexes: (sala, data, hora_inicio), (professor, data), (data, status)
```

### CancelamentoReserva
```
id: int (PK)
reserva: OneToOne → Reserva (unique)
motivo: text
cancelado_por: FK → User
data_cancelamento: datetime (auto)
```

### HistoricoReserva
```
id: int (PK)
reserva: FK → Reserva
acao: enum('criada', 'cancelada', 'editada', 'finalizada')
descricao: text
usuario: FK → User
data_hora: datetime (auto)
indexes: (reserva, data_hora)
```

## 🗄️ Banco de Dados

**Motor:** MySQL 8.0
**Character Set:** utf8mb4 (suporta emojis e caracteres especiais)
**Database:** `agendamento_salas`

### Credenciais de Desenvolvimento

```
Host: localhost
Port: 3306
User: root
Password: admin
```

### Configurar via .env

```
DB_NAME=agendamento_salas
DB_USER=root
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=3306
```

## 🚀 Executar Servidor

```bash
cd backend
source ../.venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Acesse:
- **Admin:** http://localhost:8000/admin/
- **API:** http://localhost:8000/api/v1/

## 📝 Criar Migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

## 👥 Criar Superusuário

```bash
python manage.py createsuperuser
```

## 🧪 Validações de Negócio

### Detecção de Conflitos
Antes de criar/atualizar uma reserva, valida:
- Se não há sobreposição de horários com outras reservas ativas
- Se o horário de fim é posterior ao de início
- Se a data é no futuro (não permite reservas retroativas)

### Soft Delete
Recursos e salas podem ser desativados (`ativo: false`) sem deletar do banco:
```bash
PATCH /api/v1/salas/{id}/
{"ativa": false}
```

### Auditoria Completa
Cada ação é registrada em `HistoricoReserva`:
- Criação de reserva
- Edição de reserva
- Cancelamento de reserva
- Dados do usuário que realizou a ação
- Timestamp exato

## 🔍 Consultas Úteis

### Ver estrutura do banco
```bash
python manage.py dbshell
```

### Resetar banco
```bash
python manage.py flush
```

### Executar testes
```bash
python manage.py test rooms
```

## 📦 Stack Técnico

- **Django 4.2.13** (LTS)
- **Django REST Framework 3.14.0**
- **SimpleJWT 5.3.1** (Autenticação)
- **PyMySQL 1.1.0** (Connector MySQL)
- **django-cors-headers 4.3.1** (CORS)
- **Python 3.12**

## ✨ Próximas Melhorias

- [ ] Notificações por email ao criar/cancelar reserva
- [ ] Dashboard de uso de salas
- [ ] Relatórios de ocupação por período
- [ ] Aprovação de reservas por administrador
- [ ] Sincronização com Google Calendar
- [ ] Frontend em React/Vue
- [ ] Testes automatizados com pytest
- [ ] Docker Compose para deploy

## 📞 Suporte

Para problemas ou dúvidas, consulte:
- Documentação Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- Django Admin: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/
