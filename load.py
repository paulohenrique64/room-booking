import os
import random
from datetime import time, timedelta


def configure_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

    try:
        import pymysql

        pymysql.install_as_MySQLdb()
    except ImportError:
        pass

    import django

    django.setup()


RECURSOS_DATA = [
    {'key': 'projetor', 'nome': 'Projetor 4K', 'descricao': 'Projetor de alta resolução para aulas e apresentações.', 'quantidade': 8, 'icone': 'videocam'},
    {'key': 'tv', 'nome': 'Smart TV 65"', 'descricao': 'Tela grande para reuniões híbridas e compartilhamento de conteúdo.', 'quantidade': 10, 'icone': 'tv'},
    {'key': 'quadro', 'nome': 'Quadro de vidro', 'descricao': 'Quadro para anotações, dinâmicas e planejamento visual.', 'quantidade': 12, 'icone': 'edit_note'},
    {'key': 'audio', 'nome': 'Sistema de áudio', 'descricao': 'Microfones e caixas para conferências e eventos.', 'quantidade': 6, 'icone': 'headphones'},
    {'key': 'notebook', 'nome': 'Notebook de apoio', 'descricao': 'Notebook para suporte em apresentações e treinamentos.', 'quantidade': 5, 'icone': 'computer'},
    {'key': 'cafe', 'nome': 'Café e apoio', 'descricao': 'Apoio para eventos, reuniões longas e workshops.', 'quantidade': 4, 'icone': 'local_cafe'},
]

SALAS_DATA = [
    {
        'key': 'studio_a',
        'nome': 'Studio A',
        'predio': 'Bloco Criativo',
        'andar': 1,
        'capacidade': 8,
        'descricao': 'Sala compacta para reuniões rápidas e alinhamentos de equipe.',
        'imagem': 'https://images.unsplash.com/photo-1497366754035-f200968a6e72',
        'recursos': ['tv', 'quadro'],
    },
    {
        'key': 'studio_b',
        'nome': 'Studio B',
        'predio': 'Bloco Criativo',
        'andar': 1,
        'capacidade': 40,
        'descricao': 'Espaço amplo para workshops, aulas práticas e encontros de equipe.',
        'imagem': 'https://images.unsplash.com/photo-1517502884422-41eaead166d4',
        'recursos': ['projetor', 'audio', 'cafe'],
    },
    {
        'key': 'boardroom_alpha',
        'nome': 'Boardroom Alpha',
        'predio': 'Bloco Executivo',
        'andar': 2,
        'capacidade': 16,
        'descricao': 'Sala executiva para reuniões estratégicas e apresentações formais.',
        'imagem': 'https://images.unsplash.com/photo-1518005020951-eccb494ad742',
        'recursos': ['projetor', 'tv', 'quadro', 'audio'],
    },
    {
        'key': 'huddle_1',
        'nome': 'Huddle Room 1',
        'predio': 'Bloco Executivo',
        'andar': 3,
        'capacidade': 6,
        'descricao': 'Sala pequena para chamadas, entrevistas e conversas rápidas.',
        'imagem': 'https://images.unsplash.com/photo-1531973576160-7125cd663d86',
        'recursos': ['tv', 'quadro'],
    },
    {
        'key': 'lab_inovacao',
        'nome': 'Laboratório de Inovação',
        'predio': 'Bloco Tecnologia',
        'andar': 2,
        'capacidade': 28,
        'descricao': 'Ambiente preparado para prototipação, dinâmicas e atividades colaborativas.',
        'imagem': 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d',
        'recursos': ['projetor', 'notebook', 'quadro'],
    },
]

DEMO_PASSWORD = 'demo12345'
ADMIN_PASSWORD = 'admin12345'

ADMIN_DATA = {
    'username': 'admin',
    'first_name': 'Administrador',
    'last_name': 'Sistema',
    'email': 'admin@example.com',
}

USUARIOS_DATA = [
    {'username': 'ana.professora', 'first_name': 'Ana Paula', 'last_name': 'Ribeiro', 'email': 'ana.ribeiro@example.com'},
    {'username': 'carlos.professor', 'first_name': 'Carlos Eduardo', 'last_name': 'Mendes', 'email': 'carlos.mendes@example.com'},
    {'username': 'fernanda.professora', 'first_name': 'Fernanda', 'last_name': 'Oliveira', 'email': 'fernanda.oliveira@example.com'},
    {'username': 'demo.professor', 'first_name': 'Professor', 'last_name': 'Demo', 'email': 'professor.demo@example.com'},
]

RESERVAS_DATA = [
    {'titulo': 'Planejamento semanal', 'sala': 'studio_a', 'dias': 0, 'inicio': time(9, 0), 'fim': time(10, 0)},
    {'titulo': 'Revisão executiva Q3', 'sala': 'boardroom_alpha', 'dias': 0, 'inicio': time(13, 0), 'fim': time(14, 30)},
    {'titulo': 'Workshop de produto', 'sala': 'studio_b', 'dias': 1, 'inicio': time(10, 0), 'fim': time(12, 0)},
    {'titulo': 'Entrevistas técnicas', 'sala': 'huddle_1', 'dias': 3, 'inicio': time(15, 0), 'fim': time(16, 30)},
    {'titulo': 'Sprint de prototipação', 'sala': 'lab_inovacao', 'dias': 4, 'inicio': time(8, 30), 'fim': time(11, 30)},
    {'titulo': 'Roadmap mensal', 'sala': 'boardroom_alpha', 'dias': 7, 'inicio': time(11, 0), 'fim': time(12, 30)},
]


def populate(clear=False, stdout=print):
    from django.contrib.auth import get_user_model
    from django.db import transaction
    from django.utils import timezone

    from apps.reservations.constants import ReservaStatus
    from apps.reservations.models import Reserva
    from apps.rooms.models import Recurso, Sala

    random.seed(2026)

    with transaction.atomic():
        if clear:
            stdout('Limpando banco de dados...')
            Reserva.objects.all().delete()
            Sala.objects.all().delete()
            Recurso.objects.all().delete()

        stdout('Populando equipamentos...')
        recursos = {}
        for item in RECURSOS_DATA:
            recurso, _created = Recurso.objects.update_or_create(
                nome=item['nome'],
                defaults={
                    'descricao': item['descricao'],
                    'quantidade': item['quantidade'],
                    'icone': item['icone'],
                },
            )
            recursos[item['key']] = recurso

        stdout('Populando salas...')
        salas = {}
        for item in SALAS_DATA:
            sala, _created = Sala.objects.update_or_create(
                nome=item['nome'],
                predio=item['predio'],
                defaults={
                    'andar': item['andar'],
                    'capacidade': item['capacidade'],
                    'descricao': f"Imagem: {item['imagem']} | {item['descricao']}",
                    'ativa': True,
                },
            )
            sala.recursos.set([recursos[key] for key in item['recursos']])
            salas[item['key']] = sala

        stdout('Populando usuários...')
        User = get_user_model()
        usuarios = []
        for item in USUARIOS_DATA:
            usuario, created = User.objects.get_or_create(
                username=item['username'],
                defaults={
                    'first_name': item['first_name'],
                    'last_name': item['last_name'],
                    'email': item['email'],
                    'is_staff': True,
                },
            )
            usuario.first_name = item['first_name']
            usuario.last_name = item['last_name']
            usuario.email = item['email']
            usuario.is_staff = True
            usuario.set_password(DEMO_PASSWORD)
            usuario.save(update_fields=['first_name', 'last_name', 'email', 'is_staff', 'password'])
            usuarios.append(usuario)

        admin, _created = User.objects.get_or_create(username=ADMIN_DATA['username'])
        admin.first_name = ADMIN_DATA['first_name']
        admin.last_name = ADMIN_DATA['last_name']
        admin.email = ADMIN_DATA['email']
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(ADMIN_PASSWORD)
        admin.save(update_fields=['first_name', 'last_name', 'email', 'is_staff', 'is_superuser', 'password'])

        stdout('Populando reservas...')
        hoje = timezone.localdate()
        for item in RESERVAS_DATA:
            Reserva.objects.update_or_create(
                sala=salas[item['sala']],
                data=hoje + timedelta(days=item['dias']),
                hora_inicio=item['inicio'],
                defaults={
                    'professor': random.choice(usuarios),
                    'hora_fim': item['fim'],
                    'titulo': item['titulo'],
                    'status': ReservaStatus.ATIVA,
                },
            )

    stdout('População concluída com sucesso!')


if __name__ == '__main__':
    configure_django()
    populate(clear=True)
