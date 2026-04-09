from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_merge_20260406_2254'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='total_avaliacoes',
            field=models.PositiveIntegerField(default=0, verbose_name='Total de Avaliações'),
        ),
        migrations.AlterField(
            model_name='avaliacao',
            name='servico',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name='avaliacoes',
                to='core.servico',
                verbose_name='Serviço',
            ),
        ),
    ]
