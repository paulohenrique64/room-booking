# 🏫 Sistema de Agendamento de Salas - Backend Django

Sistema completo para gerenciar reservas de salas em universidade federal, com detecção automática de conflitos, auditoria completa e APIs RESTful.

## ✨ Características Principais

- ✅ **Cadastro de Salas**: Gerenciar salas com prédio, andar, capacidade e recursos
- ✅ **Reservas Inteligentes**: Sistema de reserva com detecção automática de conflitos
- ✅ **Cancelamentos**: Rastreamento completo de cancelamentos com motivos
- ✅ **Auditoria**: Histórico de todas as ações em reservas
- ✅ **APIs RESTful**: Endpoints autenticados com JWT para integração
- ✅ **Admin Django**: Interface web customizada para administração
- ✅ **Dois Papéis**: Admin (gestão) e Professores (usuários)
- ✅ **MySQL**: Banco de dados relacional com índices otimizados

## 🗂️ Estrutura de Dados

### Modelos Principais
- **Sala**: Prédio, andar, capacidade, recursos, status
- **Recurso**: Itens disponíveis em salas (projetor, whiteboard, etc)
- **Reserva**: Agendamentos de sala por professor com validação
- **CancelamentoReserva**: Auditoria de cancelamentos
- **HistoricoReserva**: Log de todas as ações em reservas

### Relacionamentos
```
User (Django nativo) ← Reserva → Sala ← Recurso
                                            ↓ M2M
                     CancelamentoReserva (opcional)
                     HistoricoReserva (múltiplos)
```

## 🚀 Quick Start

### 1. Setup Inicial
```bash
# Clonar e acessar
cd trabalho_web_django

# Criar virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados
```bash
# Criar .env
echo "DB_NAME=agendamento_salas
DB_USER=root
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=3306" > .env

# Criar database no MySQL
python3 << 'EOF'
import pymysql
conn = pymysql.connect(host='localhost', user='root', password='admin')
cursor = conn.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS agendamento_salas CHARACTER SET utf8mb4")
conn.commit()
EOF
```

### 3. Aplicar Migrações
```bash
cd backend
python manage.py migrate
```

### 4. Criar Superusuário
```bash
python manage.py createsuperuser
# ou use dados de teste:
# username: admin, password: admin123
```

### 5. Iniciar Servidor
```bash
python manage.py runserver 0.0.0.0:8000
```

✅ Pronto! Acesse:
- **Admin**: http://localhost:8000/admin/
- **API**: http://localhost:8000/api/v1/

## 📡 API Endpoints

### Autenticação
```bash
# Obter token JWT
POST /api/token/
Body: {"username": "prof_silva", "password": "senha123"}

# Renovar token
POST /api/token/refresh/
Body: {"refresh": "token_aqui"}
```

### Salas
```
GET    /api/v1/salas/                      # Listar salas
GET    /api/v1/salas/{id}/                 # Detalhes da sala
GET    /api/v1/salas/{id}/disponibilidade/ # Horários disponíveis
```

### Reservas
```
GET    /api/v1/reservas/                     # Listar reservas (admin vê tudo, prof vê suas)
GET    /api/v1/reservas/minhas_reservas/    # Minhas reservas
GET    /api/v1/reservas/proximas_reservas/  # Próximas 30 dias
POST   /api/v1/reservas/                     # Criar reserva
PATCH  /api/v1/reservas/{id}/                # Editar reserva
DELETE /api/v1/reservas/{id}/                # Deletar reserva
POST   /api/v1/reservas/{id}/cancelar/       # Cancelar com motivo
```

### Recursos
```
GET    /api/v1/recursos/                  # Listar recursos
GET    /api/v1/recursos/{id}/             # Detalhes do recurso
```

## 👥 Usuários de Teste

### Admin
- **Username**: admin
- **Senha**: admin123
- **Acesso**: Admin Django + API (is_staff=true)

### Professores
- **prof_silva** / senha123
- **prof_santos** / senha123
- **prof_oliveira** / senha123

## 📖 Documentação

Consulte os arquivos:
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Referência completa da API
- **[SETUP.md](./SETUP.md)** - Guia de instalação e troubleshooting

## 🗄️ Banco de Dados

### MySQL
- **Host**: localhost:3306
- **Database**: agendamento_salas
- **Charset**: utf8mb4 (suporta caracteres especiais)
- **User**: root
- **Password**: admin

### Tabelas
```
auth_user (Django nativo)
rooms_recurso
rooms_sala
rooms_sala_recursos (M2M)
rooms_reserva
rooms_cancelamentoreserva
rooms_historioreserva
```

## 🔒 Validações

- ✅ Horário de fim > horário de início
- ✅ Não permite reservas em datas passadas
- ✅ Detecta conflitos de horário com outras reservas
- ✅ Apenas professor criador pode editar sua reserva
- ✅ Admin pode cancelar qualquer reserva
- ✅ Histórico auditado de todas as ações

## 🛠️ Stack Técnico

| Componente | Versão | Uso |
|-----------|--------|-----|
| Django | 4.2.13 LTS | Framework web |
| Django REST Framework | 3.14.0 | APIs RESTful |
| SimpleJWT | 5.3.1 | Autenticação JWT |
| PyMySQL | 1.1.0 | Driver MySQL |
| django-cors-headers | 4.3.1 | CORS |
| Python | 3.12+ | Runtime |
| MySQL | 8.0+ | Banco de dados |

## 📊 Admin Customizado

O admin do Django foi customizado com:
- ✅ Filtros por status, data, prédio
- ✅ Busca por nome de sala, professor, motivo
- ✅ Exibição de duração em horas/minutos
- ✅ Status com cores (ativa=verde, cancelada=vermelho)
- ✅ Inlines para ver histórico e cancelamento
- ✅ Actions para cancelar múltiplas reservas
- ✅ Data hierarchy para navegação rápida

Acesse: http://localhost:8000/admin/

## 🧪 Exemplo de Uso da API

```bash
# 1. Autenticar
TOKEN=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"prof_silva","password":"senha123"}' \
  | jq -r '.access')

# 2. Listar salas disponíveis
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/salas/

# 3. Verificar disponibilidade de uma sala
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/salas/1/disponibilidade/?data=2026-05-22"

# 4. Criar reserva
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

# 5. Listar minhas reservas
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/reservas/minhas_reservas/

# 6. Cancelar reserva
curl -X POST http://localhost:8000/api/v1/reservas/1/cancelar/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"motivo": "Aula cancelada por feriado"}'
```

## 📝 Comandos Úteis

```bash
# Criar superusuário
python manage.py createsuperuser

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Executar Django shell
python manage.py shell

# Resetar banco de dados
python manage.py flush

# Rodar testes
python manage.py test rooms

# Coletar arquivos estáticos
python manage.py collectstatic

# Acessar banco de dados
python manage.py dbshell
```

## ⚙️ Configuração

Variáveis de ambiente em `.env`:
```
DB_NAME=agendamento_salas
DB_USER=root
DB_PASSWORD=admin
DB_HOST=localhost
DB_PORT=3306
```

Settings em `backend/backend/settings.py`:
- `DEBUG = True` (desenvolvimento)
- `ALLOWED_HOSTS = ['*']` (desenvolvimento)
- `TIME_ZONE = 'America/Sao_Paulo'`
- `LANGUAGE_CODE = 'pt-br'`

## 🚀 Deployment

Para produção, consulte [SETUP.md](./SETUP.md) e:
- [ ] Usar Gunicorn em vez do servidor de desenvolvimento
- [ ] Configurar Nginx como proxy reverso
- [ ] Usar Docker + docker-compose
- [ ] Habilitar HTTPS/SSL
- [ ] Adicionar variáveis de ambiente secretas
- [ ] Configurar backups do MySQL
- [ ] Implementar logging

## 🤝 Contribuindo

Este é um projeto educacional. Para melhorias:
1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit as mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes

## ✅ Checklist de Implementação

- [x] Models (Sala, Recurso, Reserva, Cancelamento, Histórico)
- [x] Validações de conflito de horários
- [x] Serializers para API
- [x] ViewSets e Endpoints
- [x] Autenticação JWT
- [x] Admin Django customizado
- [x] Permissões (Admin vs Professor)
- [x] Migrações do banco
- [x] Dados de teste
- [x] Documentação da API
- [x] Guia de setup

## 📞 Suporte

Dúvidas ou problemas?
- Consulte [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- Consulte [SETUP.md](./SETUP.md)
- Verifique logs do Django: `python manage.py runserver`
- Teste manualmente via Admin: http://localhost:8000/admin/

---

**Desenvolvido com ❤️ usando Django e MySQL**

*Status: ✅ Produção Pronta | Última atualização: 19 de Maio de 2026*
