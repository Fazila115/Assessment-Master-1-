# Generated by Django 3.0.5 on 2020-12-09 15:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0002_remove_student_status'),
        ('assessment', '0003_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='exam',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assessment.Course'),
        ),
        migrations.AlterField(
            model_name='result',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.Student'),
        ),
    ]
