from datetime import timedelta

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import NotificationDismissal
from apps.core.notifications import build_notification_summary
from apps.reservations.constants import ReservaStatus
from apps.reservations.models import Reserva
from apps.rooms.models import Sala


class NotificationSummaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='professor', password='senha123')
        self.sala = Sala.objects.create(nome='Lab 101', predio='Bloco A', andar=1, capacidade=40)

    def test_usuario_anonimo_nao_recebe_notificacoes(self):
        summary = build_notification_summary(AnonymousUser())

        self.assertEqual(summary, {'items': [], 'new_count': 0})

    def test_reserva_proxima_gera_notificacao_de_inicio(self):
        start_at = timezone.localtime() + timedelta(minutes=15)
        Reserva.objects.create(
            professor=self.user,
            sala=self.sala,
            data=start_at.date(),
            hora_inicio=start_at.time().replace(second=0, microsecond=0),
            hora_fim=(start_at + timedelta(hours=1)).time().replace(second=0, microsecond=0),
            titulo='Executive Q3 Review',
            status=ReservaStatus.ATIVA,
        )

        summary = build_notification_summary(self.user)

        self.assertEqual(summary['new_count'], 1)
        self.assertEqual(summary['items'][0]['kind'], 'soon')
        self.assertIn('Executive Q3 Review', summary['items'][0]['message'])

    def test_notificacao_dispensada_nao_aparece_no_resumo(self):
        start_at = timezone.localtime() + timedelta(hours=2)
        reserva = Reserva.objects.create(
            professor=self.user,
            sala=self.sala,
            data=start_at.date(),
            hora_inicio=start_at.time().replace(second=0, microsecond=0),
            hora_fim=(start_at + timedelta(hours=1)).time().replace(second=0, microsecond=0),
            titulo='Planejamento',
            status=ReservaStatus.ATIVA,
        )
        NotificationDismissal.objects.create(user=self.user, reservation=reserva, kind='scheduled')

        summary = build_notification_summary(self.user)

        self.assertEqual(summary['items'], [])
        self.assertEqual(summary['new_count'], 0)

    def test_endpoint_dismiss_cria_registro_e_retorna_componente(self):
        start_at = timezone.localtime() + timedelta(hours=2)
        reserva = Reserva.objects.create(
            professor=self.user,
            sala=self.sala,
            data=start_at.date(),
            hora_inicio=start_at.time().replace(second=0, microsecond=0),
            hora_fim=(start_at + timedelta(hours=1)).time().replace(second=0, microsecond=0),
            titulo='Planejamento',
            status=ReservaStatus.ATIVA,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('notification_dismiss'),
            {'reservation_id': reserva.id, 'kind': 'scheduled'},
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(NotificationDismissal.objects.filter(user=self.user, reservation=reserva, kind='scheduled').exists())
        self.assertContains(response, 'Nenhuma notificação agora.')
