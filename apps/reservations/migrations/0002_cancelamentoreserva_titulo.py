from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="cancelamentoreserva",
            name="titulo",
            field=models.CharField(max_length=255, default=""),
            preserve_default=False,
        ),
    ]