from django.conf import settings
from django.db import models

from apps.reservations.models import Reserva


class NotificationDismissal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_dismissals')
    reservation = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='notification_dismissals')
    kind = models.CharField(max_length=32)
    dismissed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'reservation', 'kind']
        indexes = [
            models.Index(fields=['user', 'kind']),
            models.Index(fields=['reservation', 'kind']),
        ]

    def __str__(self):
        return f'{self.user_id}:{self.kind}:{self.reservation_id}'
