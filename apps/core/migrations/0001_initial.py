# Generated manually for notification dismissal state.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reservations', '0004_rename_cancelamentoreserva_motivo_titulo'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationDismissal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(max_length=32)),
                ('dismissed_at', models.DateTimeField(auto_now_add=True)),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_dismissals', to='reservations.reserva')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_dismissals', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'reservation', 'kind')},
            },
        ),
        migrations.AddIndex(
            model_name='notificationdismissal',
            index=models.Index(fields=['user', 'kind'], name='core_notifi_user_id_76d973_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationdismissal',
            index=models.Index(fields=['reservation', 'kind'], name='core_notifi_reserva_3481b2_idx'),
        ),
    ]
