from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orden_trabajo", "0007_ordentrabajo_presupuesto_telecom"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="ordentrabajo",
            name="idx_ot_fecha_prog",
        ),
        migrations.RemoveField(
            model_name="ordentrabajo",
            name="fecha_programada",
        ),
    ]