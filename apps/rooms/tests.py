from datetime import time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.reservations import selectors, services

from .forms import SalaForm
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

    def test_sala_nao_permite_nome_repetido_no_mesmo_predio(self):
        Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=20)
        sala = Sala(nome='lab 101', predio='bloco a', andar=2, capacidade=30)

        with self.assertRaises(ValidationError):
            sala.full_clean()

    def test_sala_permite_nome_repetido_em_predios_diferentes(self):
        Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=20)
        sala = Sala(nome='Lab 101', predio='Bloco B', andar=1, capacidade=30)

        sala.full_clean()


class SalaFormEstoqueTests(TestCase):
    def test_editar_sala_devolve_estoque_de_recurso_removido(self):
        recurso = Recurso.objects.create(nome='Projetor', quantidade=0)
        sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)
        sala.recursos.add(recurso)

        data = QueryDict('', mutable=True)
        data.update(
            {
                'nome': sala.nome,
                'predio': sala.predio,
                'andar': sala.andar,
                'capacidade': sala.capacidade,
                'descricao': '',
                'imagem_url': '',
                'ativa': 'on',
            }
        )
        form = SalaForm(data, instance=sala)

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        recurso.refresh_from_db()

        self.assertEqual(recurso.quantidade, 1)

    def test_excluir_sala_devolve_estoque_dos_recursos(self):
        recurso = Recurso.objects.create(nome='Projetor', quantidade=0)
        sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)
        sala.recursos.add(recurso)

        sala.delete()
        recurso.refresh_from_db()

        self.assertEqual(recurso.quantidade, 1)


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

    def test_nao_exclui_equipamento_em_uso_por_sala(self):
        recurso = Recurso.objects.create(nome='Projetor', quantidade=0)
        self.sala.recursos.add(recurso)

        response = self.client.delete(reverse('equipment_delete', args=[recurso.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Recurso.objects.filter(pk=recurso.pk).exists())
        self.assertContains(response, 'Não é possível excluir um equipamento em uso por salas.', status_code=409)


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
            titulo='Aula',
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
