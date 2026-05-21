from datetime import time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.reservations import selectors, services

from .models import Recurso, Sala


class SalaModelTests(TestCase):
    def test_sala_str_exibe_nome_predio_e_capacidade(self):
        sala = Sala.objects.create(
            nome='Lab 101',
            predio='Bloco A',
            andar=1,
            capacidade=40,
        )

        self.assertEqual(str(sala), 'Lab 101 - Bloco A (40 pessoas)')

    def test_salas_ativas_retorna_apenas_salas_ativas(self):
        ativa = Sala.objects.create(nome='Sala Ativa', predio='A', andar=1, capacidade=20)
        Sala.objects.create(nome='Sala Inativa', predio='A', andar=2, capacidade=20, ativa=False)

        self.assertEqual(list(selectors.salas_ativas()), [ativa])


class SalaViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='professor', password='senha123')
        self.sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)

    def test_lista_salas_exige_login(self):
        response = self.client.get(reverse('rooms:lista'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/contas/login/', response['Location'])

    def test_lista_salas_autenticado(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('rooms:lista'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sala.nome)


class SalaApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='professor', password='senha123')
        self.sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)
        self.recurso = Recurso.objects.create(nome='Projetor')
        self.sala.recursos.add(self.recurso)
        self.data = timezone.now().date() + timedelta(days=1)

    def test_api_salas_exige_autenticacao(self):
        response = self.client.get('/api/v1/salas/')

        self.assertEqual(response.status_code, 401)

    def test_api_lista_salas_autenticado(self):
        self.client.force_authenticate(self.user)

        response = self.client.get('/api/v1/salas/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['nome'], 'Lab 101')

    def test_api_disponibilidade_retorna_horarios_bloqueados(self):
        services.criar_reserva(
            professor=self.user,
            sala=self.sala,
            data=self.data,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/v1/salas/{self.sala.id}/disponibilidade/', {'data': self.data.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['disponivel'])
        self.assertEqual(response.data['horarios_bloqueados'][0]['inicio'], '08:00:00')

    def test_api_disponibilidade_valida_data_obrigatoria(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/v1/salas/{self.sala.id}/disponibilidade/')

        self.assertEqual(response.status_code, 400)
