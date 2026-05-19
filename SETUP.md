# Setup Inicial - Sistema de Agendamento de Salas

## 🔧 Requisitos

- Python 3.12+
- MySQL 8.0+ rodando
- pip e virtualenv

## 📋 Checklist Pré-Setup

Antes de começar, certifique-se que:
- [ ] MySQL está rodando (`localhost:3306`)
- [ ] Você tem credenciais MySQL (root/admin neste caso)
- [ ] Git está instalado
- [ ] Python 3.12+ está disponível

## 🚀 Instalação Passo a Passo

### 1️⃣ Clonar ou acessar o repositório

```bash
cd /caminho/para/trabalho_web_django
```

### 2️⃣ Criar e ativar virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

### 3️⃣ Instalar dependências

```bash
pip install -r requirements.txt
```

### 4️⃣ Configurar variáveis de ambiente

Editar/criar `.env`:
```
DB_NAME=agendamento_salas
DB_USER=root
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=3306
```

### 5️⃣ Criar banco de dados no MySQL

```bash
python3 << 'EOF'
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='admin',
    port=3306
)

cursor = conn.cursor()
cursor.execute("""
    CREATE DATABASE IF NOT EXISTS agendamento_salas 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;
""")
conn.commit()
cursor.close()
conn.close()
print("✓ Database criado!")
EOF
```

### 6️⃣ Aplicar migrações

```bash
cd backend
python manage.py migrate
```

### 7️⃣ Criar superusuário (admin)

```bash
python manage.py createsuperuser
# Ou use os dados de teste:
# username: admin
# password: admin123
```

Você pode criar automaticamente:
```bash
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
User.objects.create_superuser(
    username='admin',
    email='admin@universidade.edu.br',
    password='admin123'
)
EOF
```

### 8️⃣ Criar dados de teste (opcional)

```bash
cd backend
python manage.py shell < ../seed_data.py
```

Ou manualmente:
```bash
python manage.py shell << 'EOF'
from rooms.models import Recurso, Sala

# Criar recursos
recursos = [
    ('Projetor', 'Projetor multimídia'),
    ('Whiteboard', 'Quadro branco'),
    ('Ar-condicionado', 'Climatização'),
]

for nome, desc in recursos:
    Recurso.objects.get_or_create(
        nome=nome,
        defaults={'descricao': desc, 'ativo': True}
    )

# Criar sala
sala = Sala.objects.create(
    nome='Sala 101',
    predio='Bloco A',
    andar=1,
    capacidade=30,
    ativa=True
)
sala.recursos.add(*Recurso.objects.all())
EOF
```

### 9️⃣ Iniciar servidor

```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

✅ Pronto! O servidor está rodando em `http://localhost:8000`

## 🎯 Acessar as Interfaces

### Admin Django
- URL: http://localhost:8000/admin/
- Username: `admin`
- Senha: `admin123`

### API REST
- Base URL: http://localhost:8000/api/v1/
- Endpoints:
  - `/salas/` - Listar salas
  - `/reservas/` - Gerenciar reservas
  - `/recursos/` - Listar recursos

### Autenticação JWT
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"prof_silva","password":"senha123"}'
```

## 📁 Estrutura do Projeto

```
trabalho_web_django/
├── .env                    # Variáveis de ambiente
├── .venv/                  # Virtual environment
├── requirements.txt        # Dependências Python
├── API_DOCUMENTATION.md    # Documentação da API
├── SETUP.md               # Este arquivo
│
└── backend/
    ├── manage.py
    ├── db.sqlite3         # (não usado, usamos MySQL)
    │
    ├── backend/           # Configurações do projeto
    │   ├── settings.py    # Configurações Django
    │   ├── urls.py        # Rotas principais
    │   ├── wsgi.py
    │   └── __init__.py
    │
    └── rooms/             # App principal
        ├── models.py      # Modelos (Sala, Reserva, etc)
        ├── views.py       # ViewSets da API
        ├── serializers.py # Serializadores JSON
        ├── admin.py       # Admin customizado
        ├── urls.py        # Rotas da app
        ├── migrations/    # Migrações do banco
        └── tests.py
```

## 🧪 Testar a API

### 1. Obter token
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"prof_silva","password":"senha123"}' \
  | grep -o '"access":"[^"]*' | cut -d'"' -f4)

echo "Token: $TOKEN"
```

### 2. Listar salas
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/salas/
```

### 3. Criar reserva
```bash
curl -X POST http://localhost:8000/api/v1/reservas/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sala": 1,
    "data": "2026-05-22",
    "hora_inicio": "14:00:00",
    "hora_fim": "16:00:00",
    "motivo": "Aula teórica"
  }'
```

## 🐛 Troubleshooting

### Erro: "Can't connect to MySQL server"
- Verificar se MySQL está rodando: `ps aux | grep mysql`
- Verificar credenciais em `.env`
- Criar database manualmente (ver passo 5)

### Erro: "Access denied for user 'root'"
- Verificar senha em `.env`
- Reset de senha MySQL se necessário
- Usar `mysql -h localhost -u root -p` para testar

### Erro: "No module named 'rooms'"
- Garantir que `'rooms'` está em `INSTALLED_APPS` no settings.py
- Rodar: `python manage.py makemigrations rooms`

### Porta 8000 já em uso
```bash
# Matar processo na porta 8000
lsof -ti:8000 | xargs kill -9

# Ou usar outra porta
python manage.py runserver 0.0.0.0:8001
```

### Erro de migração
```bash
# Resetar todas as migrações
python manage.py migrate rooms 0001 --fake
python manage.py migrate

# Ou limpar tudo (cuidado, deleta dados!)
python manage.py flush
python manage.py migrate
```

## 📊 Verificar Status

### Verificar banco de dados
```bash
python manage.py dbshell
> SHOW TABLES;
> DESCRIBE rooms_sala;
> SELECT COUNT(*) FROM rooms_sala;
```

### Verificar migrações aplicadas
```bash
python manage.py showmigrations
```

### Verificar usuários criados
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.all()
```

## ✨ Próximos Passos

1. **Criar dados de exemplo** via Admin:
   - Acessar http://localhost:8000/admin/
   - Criar salas, recursos, usuários

2. **Testar reservas**:
   - Criar reservas via API
   - Testar detecção de conflitos

3. **Implementar frontend**:
   - React, Vue ou Svelte
   - Consumir as APIs

4. **Deploy**:
   - Docker + docker-compose
   - Gunicorn + Nginx
   - Environment production

## 🔗 Recursos

- Django Docs: https://docs.djangoproject.com/
- DRF Docs: https://www.django-rest-framework.org/
- JWT Guide: https://django-rest-framework-simplejwt.readthedocs.io/
- MySQL Guide: https://dev.mysql.com/doc/

---

**Última atualização:** 19 de Maio de 2026
**Status:** ✅ Produção Pronta
