from datetime import time, timedelta

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.reservations import selectors, services
from apps.reservations.admin import ReservaAdmin
from apps.reservations.constants import HistoricoAcao, ReservaStatus
from apps.reservations.exceptions import DomainError
from apps.rooms.models import Sala

from .models import CancelamentoReserva, HistoricoReserva, Reserva


class ReservaServiceTests(TestCase):
    def setUp(self):
        self.professor = User.objects.create_user(username='professor', password='senha123')
        self.outro_professor = User.objects.create_user(username='outro', password='senha123')
        self.staff = User.objects.create_user(username='coordenador', password='senha123', is_staff=True)
        self.sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)
        self.sala_inativa = Sala.objects.create(
            nome='Lab Fechado',
            predio='Bloco A',
            andar=2,
            capacidade=30,
            ativa=False,
        )
        self.amanha = timezone.now().date() + timedelta(days=1)

    def test_criar_reserva_salva_status_padrao_e_historico(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula de redes',
        )

        self.assertEqual(reserva.status, ReservaStatus.ATIVA)
        self.assertTrue(
            HistoricoReserva.objects.filter(
                reserva=reserva,
                acao=HistoricoAcao.CRIADA,
                usuario=self.professor,
            ).exists()
        )

    def test_criar_reserva_impede_sobreposicao_na_mesma_sala_e_data(self):
        services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(10, 0),
            motivo='Aula',
        )

        with self.assertRaises(DomainError):
            services.criar_reserva(
                professor=self.outro_professor,
                sala=self.sala,
                data=self.amanha,
                hora_inicio=time(9, 0),
                hora_fim=time(11, 0),
                motivo='Reuniao',
            )

    def test_criar_reserva_permite_horario_adjacente(self):
        services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )

        reserva = services.criar_reserva(
            professor=self.outro_professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(9, 0),
            hora_fim=time(10, 0),
            motivo='Reuniao',
        )

        self.assertEqual(reserva.hora_inicio, time(9, 0))

    def test_cancelar_reserva_altera_status_cria_cancelamento_e_historico(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )

        services.cancelar_reserva(reserva=reserva, usuario=self.professor, motivo='Sem turma')
        reserva.refresh_from_db()

        self.assertEqual(reserva.status, ReservaStatus.CANCELADA)
        self.assertTrue(CancelamentoReserva.objects.filter(reserva=reserva, motivo='Sem turma').exists())
        self.assertTrue(HistoricoReserva.objects.filter(reserva=reserva, acao=HistoricoAcao.CANCELADA).exists())

    def test_usuario_nao_pode_cancelar_reserva_de_outro_professor(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )

        with self.assertRaises(PermissionDenied):
            services.cancelar_reserva(reserva=reserva, usuario=self.outro_professor, motivo='Indevido')

    def test_staff_pode_cancelar_reserva_de_qualquer_professor(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )

        services.cancelar_reserva(reserva=reserva, usuario=self.staff, motivo='Manutencao')
        reserva.refresh_from_db()

        self.assertEqual(reserva.status, ReservaStatus.CANCELADA)

    def test_criar_reserva_rejeita_sala_inativa(self):
        with self.assertRaises(DomainError):
            services.criar_reserva(
                professor=self.professor,
                sala=self.sala_inativa,
                data=self.amanha,
                hora_inicio=time(8, 0),
                hora_fim=time(9, 0),
                motivo='Aula',
            )

    def test_cancelar_reserva_finalizada_retorna_erro_de_dominio(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        reserva.status = ReservaStatus.FINALIZADA
        reserva.save(update_fields=['status'])

        with self.assertRaises(DomainError):
            services.cancelar_reserva(reserva=reserva, usuario=self.professor, motivo='Finalizada')


class ReservaSelectorTests(TestCase):
    def setUp(self):
        self.professor = User.objects.create_user(username='professor', password='senha123')
        self.outro_professor = User.objects.create_user(username='outro', password='senha123')
        self.staff = User.objects.create_user(username='coordenador', password='senha123', is_staff=True)
        self.sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)
        self.amanha = timezone.now().date() + timedelta(days=1)
        self.reserva_professor = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        self.reserva_outro = services.criar_reserva(
            professor=self.outro_professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(9, 0),
            hora_fim=time(10, 0),
            motivo='Reuniao',
        )

    def test_reservas_para_usuario_filtra_por_professor(self):
        reservas = list(selectors.reservas_para_usuario(self.professor).order_by('id'))

        self.assertEqual(reservas, [self.reserva_professor])

    def test_reservas_para_staff_retorna_todas(self):
        reservas = list(selectors.reservas_para_usuario(self.staff).order_by('id'))

        self.assertEqual(reservas, [self.reserva_professor, self.reserva_outro])

    def test_horarios_bloqueados_ignora_reservas_canceladas(self):
        services.cancelar_reserva(reserva=self.reserva_outro, usuario=self.outro_professor, motivo='Cancelado')

        bloqueados = selectors.horarios_bloqueados(self.sala, self.amanha)

        self.assertEqual(len(bloqueados), 1)
        self.assertEqual(bloqueados[0]['professor'], self.professor.username)


class ReservaViewTests(TestCase):
    def setUp(self):
        self.professor = User.objects.create_user(username='professor', password='senha123')
        self.sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)
        self.amanha = timezone.now().date() + timedelta(days=1)

    def test_lista_reservas_exige_login(self):
        response = self.client.get(reverse('reservations:lista'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/contas/login/', response['Location'])

    def test_criar_reserva_via_view_autenticado(self):
        self.client.force_login(self.professor)

        response = self.client.post(
            reverse('reservations:nova'),
            {
                'sala': self.sala.id,
                'data': self.amanha.isoformat(),
                'hora_inicio': '08:00',
                'hora_fim': '09:00',
                'motivo': 'Aula',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Reserva.objects.filter(professor=self.professor, sala=self.sala).exists())

    def test_criar_reserva_htmx_redireciona_sem_302_intermediario(self):
        self.client.force_login(self.professor)

        response = self.client.post(
            reverse('reservations:nova'),
            {
                'sala': self.sala.id,
                'data': self.amanha.isoformat(),
                'hora_inicio': '08:00',
                'hora_fim': '09:00',
                'motivo': 'Aula',
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response['HX-Redirect'], reverse('reservations:lista'))
        self.assertTrue(Reserva.objects.filter(professor=self.professor, sala=self.sala).exists())

    def test_cancelar_reserva_htmx_preserva_filtros_ativos(self):
        self.client.force_login(self.professor)
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha + timedelta(days=1),
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula futura',
        )

        response = self.client.post(
            reverse('reservations:cancelar', args=[reserva.pk]),
            {
                'motivo': 'Sem turma',
                'status': ReservaStatus.ATIVA,
                'data': self.amanha.isoformat(),
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nenhuma reserva encontrada.')

    def test_filtro_com_data_invalida_nao_quebra_listagem(self):
        self.client.force_login(self.professor)

        response = self.client.get(reverse('reservations:lista'), {'data': '31/12/2099'})

        self.assertEqual(response.status_code, 200)


class ReservaApiTests(APITestCase):
    def setUp(self):
        self.professor = User.objects.create_user(username='professor', password='senha123')
        self.outro_professor = User.objects.create_user(username='outro', password='senha123')
        self.staff = User.objects.create_user(username='coordenador', password='senha123', is_staff=True)
        self.sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)
        self.sala_inativa = Sala.objects.create(
            nome='Lab Fechado',
            predio='Bloco A',
            andar=2,
            capacidade=30,
            ativa=False,
        )
        self.amanha = timezone.now().date() + timedelta(days=1)

    def test_api_reservas_exige_autenticacao(self):
        response = self.client.get('/api/v1/reservas/')

        self.assertEqual(response.status_code, 401)

    def test_api_cria_reserva_para_usuario_autenticado(self):
        self.client.force_authenticate(self.professor)

        response = self.client.post(
            '/api/v1/reservas/',
            {
                'sala': self.sala.id,
                'data': self.amanha.isoformat(),
                'hora_inicio': '08:00:00',
                'hora_fim': '09:00:00',
                'motivo': 'Aula',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Reserva.objects.get().professor, self.professor)
        self.assertEqual(response.data['status'], ReservaStatus.ATIVA)
        self.assertEqual(response.data['historico'][0]['acao'], HistoricoAcao.CRIADA)

    def test_api_nao_permite_reservar_sala_inativa(self):
        self.client.force_authenticate(self.professor)

        response = self.client.post(
            '/api/v1/reservas/',
            {
                'sala': self.sala_inativa.id,
                'data': self.amanha.isoformat(),
                'hora_inicio': '08:00:00',
                'hora_fim': '09:00:00',
                'motivo': 'Aula',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_api_rejeita_reserva_com_conflito(self):
        services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(10, 0),
            motivo='Aula',
        )
        self.client.force_authenticate(self.outro_professor)

        response = self.client.post(
            '/api/v1/reservas/',
            {
                'sala': self.sala.id,
                'data': self.amanha.isoformat(),
                'hora_inicio': '09:00:00',
                'hora_fim': '11:00:00',
                'motivo': 'Reuniao',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_api_minhas_reservas_retorna_apenas_do_usuario(self):
        minha = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        services.criar_reserva(
            professor=self.outro_professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(9, 0),
            hora_fim=time(10, 0),
            motivo='Reuniao',
        )
        self.client.force_authenticate(self.professor)

        response = self.client.get('/api/v1/reservas/minhas_reservas/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [minha.id])

    def test_api_listagem_staff_retorna_reservas_de_todos(self):
        minha = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        outra = services.criar_reserva(
            professor=self.outro_professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(9, 0),
            hora_fim=time(10, 0),
            motivo='Reuniao',
        )
        self.client.force_authenticate(self.staff)

        response = self.client.get('/api/v1/reservas/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual({item['id'] for item in response.data['results']}, {minha.id, outra.id})

    def test_api_filtro_data_invalida_retorna_400(self):
        self.client.force_authenticate(self.professor)

        response = self.client.get('/api/v1/reservas/', {'data': '31/12/2099'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('data', response.data['erro'])

    def test_api_filtro_sala_invalida_retorna_400(self):
        self.client.force_authenticate(self.professor)

        response = self.client.get('/api/v1/reservas/', {'sala': 'abc'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('sala', response.data['erro'])

    def test_api_historico_mapeia_data_local_e_data_da_reserva(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 30),
            motivo='Aula',
        )
        self.client.force_authenticate(self.professor)

        response = self.client.get(f'/api/v1/reservas/{reserva.id}/')
        historico = response.data['historico'][0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(historico['data_reserva'], self.amanha.isoformat())
        self.assertEqual(historico['hora_inicio_reserva'], '08:00')
        self.assertEqual(historico['hora_fim_reserva'], '09:30')
        self.assertIn('data_hora_local', historico)
        self.assertIn('data_hora_formatada', historico)

    def test_api_cancelar_reserva(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        self.client.force_authenticate(self.professor)

        response = self.client.post(
            f'/api/v1/reservas/{reserva.id}/cancelar/',
            {'motivo': 'Sem turma'},
            format='json',
        )
        reserva.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(reserva.status, ReservaStatus.CANCELADA)
        self.assertEqual(response.data['status'], ReservaStatus.CANCELADA)
        self.assertIsNotNone(response.data['cancelamento'])
        self.assertIn(HistoricoAcao.CANCELADA, [item['acao'] for item in response.data['historico']])

    def test_api_cancelamento_mapeia_data_local(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        self.client.force_authenticate(self.professor)

        self.client.post(
            f'/api/v1/reservas/{reserva.id}/cancelar/',
            {'motivo': 'Sem turma'},
            format='json',
        )
        response = self.client.get(f'/api/v1/reservas/{reserva.id}/')

        self.assertIn('data_cancelamento_local', response.data['cancelamento'])
        self.assertIn('data_cancelamento_formatada', response.data['cancelamento'])


class ReservaAdminTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.staff = User.objects.create_user(
            username='coordenador',
            password='senha123',
            is_staff=True,
            is_superuser=True,
        )
        self.professor = User.objects.create_user(username='professor', password='senha123')
        self.sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)
        self.amanha = timezone.now().date() + timedelta(days=1)

    def _request(self):
        request = self.factory.post('/admin/reservations/reserva/')
        request.user = self.staff
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)
        return request

    def test_admin_criar_reserva_registra_historico(self):
        reserva = Reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        model_admin = ReservaAdmin(Reserva, admin.site)

        model_admin.save_model(self._request(), reserva, None, False)

        self.assertTrue(
            HistoricoReserva.objects.filter(
                reserva=reserva,
                acao=HistoricoAcao.CRIADA,
                usuario=self.staff,
                descricao='Reserva criada via admin',
            ).exists()
        )

    def test_admin_mudar_status_para_cancelada_registra_cancelamento_e_historico(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        reserva.status = ReservaStatus.CANCELADA
        model_admin = ReservaAdmin(Reserva, admin.site)

        model_admin.save_model(self._request(), reserva, None, True)
        reserva.refresh_from_db()

        self.assertEqual(reserva.status, ReservaStatus.CANCELADA)
        self.assertTrue(
            CancelamentoReserva.objects.filter(
                reserva=reserva,
                motivo='Cancelada via admin',
                cancelado_por=self.staff,
            ).exists()
        )
        self.assertEqual(
            HistoricoReserva.objects.filter(reserva=reserva, acao=HistoricoAcao.CANCELADA).count(),
            1,
        )

        model_admin.save_model(self._request(), reserva, None, True)

        self.assertEqual(CancelamentoReserva.objects.filter(reserva=reserva).count(), 1)
        self.assertEqual(
            HistoricoReserva.objects.filter(reserva=reserva, acao=HistoricoAcao.CANCELADA).count(),
            1,
        )

    def test_admin_action_cancelar_registra_cancelamento_e_historico(self):
        reserva = services.criar_reserva(
            professor=self.professor,
            sala=self.sala,
            data=self.amanha,
            hora_inicio=time(8, 0),
            hora_fim=time(9, 0),
            motivo='Aula',
        )
        model_admin = ReservaAdmin(Reserva, admin.site)

        model_admin.cancelar_reservas_selecionadas(self._request(), Reserva.objects.filter(pk=reserva.pk))
        reserva.refresh_from_db()

        self.assertEqual(reserva.status, ReservaStatus.CANCELADA)
        self.assertTrue(CancelamentoReserva.objects.filter(reserva=reserva).exists())
        self.assertTrue(
            HistoricoReserva.objects.filter(
                reserva=reserva,
                acao=HistoricoAcao.CANCELADA,
                usuario=self.staff,
            ).exists()
        )
