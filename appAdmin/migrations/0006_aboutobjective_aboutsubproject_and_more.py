# Generated by Django 4.2.7 on 2025-07-21 02:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appAdmin', '0005_alter_resourcemetadata_resource_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='AboutObjective',
            fields=[
                ('objective_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'tbl_about_objective',
            },
        ),
        migrations.CreateModel(
            name='AboutSubProject',
            fields=[
                ('sub_id', models.AutoField(primary_key=True, serialize=False)),
                ('image', models.ImageField(blank=True, null=True, upload_to='about_images/')),
                ('project_name', models.CharField(blank=True, max_length=255, null=True)),
                ('project_details', models.TextField(blank=True, null=True)),
                ('project_rationale_desc', models.TextField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
            ],
            options={
                'db_table': 'tbl_about_sub_project',
            },
        ),
        migrations.CreateModel(
            name='AboutSubProjectObjective',
            fields=[
                ('objective_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('about', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='objectives', to='appAdmin.aboutsubproject')),
            ],
            options={
                'db_table': 'tbl_about_objective_sub_project',
            },
        ),
        migrations.CreateModel(
            name='AboutSubProjectTeamMember',
            fields=[
                ('member_id', models.AutoField(primary_key=True, serialize=False)),
                ('profile_image', models.ImageField(blank=True, null=True, upload_to='team_profiles/')),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('mid_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('role', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('about', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.aboutsubproject')),
            ],
            options={
                'db_table': 'tbl_about_team_member_sub_project',
            },
        ),
        migrations.CreateModel(
            name='AboutSubProjectTimeline',
            fields=[
                ('timeline_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('date_start', models.DateField(blank=True, null=True)),
                ('date_end', models.DateField(blank=True, null=True)),
                ('about', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.aboutsubproject')),
            ],
            options={
                'db_table': 'tbl_about_timeline_sub_project',
            },
        ),
        migrations.CreateModel(
            name='AboutTeamMember',
            fields=[
                ('member_id', models.AutoField(primary_key=True, serialize=False)),
                ('profile_image', models.ImageField(blank=True, null=True, upload_to='team_profiles/')),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('mid_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('role', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'tbl_about_team_member',
            },
        ),
        migrations.CreateModel(
            name='AboutTimeline',
            fields=[
                ('timeline_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('date_start', models.DateField(blank=True, null=True)),
                ('date_end', models.DateField(blank=True, null=True)),
            ],
            options={
                'db_table': 'tbl_about_timeline',
            },
        ),
        migrations.CreateModel(
            name='MainProgram',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_rationale_desc', models.TextField(blank=True, null=True)),
                ('project_objectives_desc', models.TextField(blank=True, null=True)),
                ('raise_project_desc', models.TextField(blank=True, null=True)),
                ('org_struct_image', models.ImageField(blank=True, null=True, upload_to='team_profiles/')),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
            ],
            options={
                'db_table': 'tbl_main_program',
            },
        ),
        migrations.CreateModel(
            name='MainProgramObjective',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('target', models.TextField(blank=True, null=True)),
                ('main_program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='objectives', to='appAdmin.mainprogram')),
            ],
            options={
                'db_table': 'tbl_main_program_objectives',
            },
        ),
        migrations.RemoveField(
            model_name='about',
            name='content',
        ),
        migrations.AddField(
            model_name='about',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='about_images/'),
        ),
        migrations.AddField(
            model_name='about',
            name='project_details',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='about',
            name='project_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='about',
            name='project_rationale_desc',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='MainTitleBullet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('objective', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='title_bullets', to='appAdmin.mainprogramobjective')),
            ],
            options={
                'db_table': 'tbl_main_title_bullets',
            },
        ),
        migrations.CreateModel(
            name='MainTargetBullet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('objective', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_bullets', to='appAdmin.mainprogramobjective')),
            ],
            options={
                'db_table': 'tbl_main_target_bullets',
            },
        ),
        migrations.CreateModel(
            name='MainProgramImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='team_profiles/')),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('main_program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='appAdmin.mainprogram')),
            ],
            options={
                'db_table': 'tbl_main_program_img',
            },
        ),
        migrations.CreateModel(
            name='AboutTimelineImage',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('image', models.ImageField(blank=True, null=True, upload_to='team_profiles/')),
                ('timeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='appAdmin.abouttimeline')),
            ],
            options={
                'db_table': 'tbl_timeline_images',
            },
        ),
        migrations.CreateModel(
            name='AboutTimelineBullet',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('details', models.TextField()),
                ('timeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bullets', to='appAdmin.abouttimeline')),
            ],
            options={
                'db_table': 'tbl_timeline_bullets',
            },
        ),
        migrations.AddField(
            model_name='abouttimeline',
            name='about',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.about'),
        ),
        migrations.CreateModel(
            name='AboutTeamSocial',
            fields=[
                ('social_id', models.AutoField(primary_key=True, serialize=False)),
                ('platform', models.CharField(max_length=100)),
                ('link', models.URLField(max_length=255)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='socials', to='appAdmin.aboutteammember')),
            ],
            options={
                'db_table': 'tbl_about_team_social',
            },
        ),
        migrations.AddField(
            model_name='aboutteammember',
            name='about',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.about'),
        ),
        migrations.CreateModel(
            name='AboutSubProjectTimelineImage',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('image', models.ImageField(blank=True, null=True, upload_to='team_profiles/')),
                ('timeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='appAdmin.aboutsubprojecttimeline')),
            ],
            options={
                'db_table': 'tbl_timeline_images_sub_project',
            },
        ),
        migrations.CreateModel(
            name='AboutSubProjectTimelineBullet',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('details', models.TextField()),
                ('timeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bullets', to='appAdmin.aboutsubprojecttimeline')),
            ],
            options={
                'db_table': 'tbl_timeline_bullets_sub_project',
            },
        ),
        migrations.CreateModel(
            name='AboutSubProjectTeamSocial',
            fields=[
                ('social_id', models.AutoField(primary_key=True, serialize=False)),
                ('platform', models.CharField(max_length=100)),
                ('link', models.URLField(max_length=255)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='socials', to='appAdmin.aboutsubprojectteammember')),
            ],
            options={
                'db_table': 'tbl_about_team_social_sub_project',
            },
        ),
        migrations.CreateModel(
            name='AboutSubProjectRationale',
            fields=[
                ('rationale_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('detail', models.TextField()),
                ('about', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.aboutsubproject')),
            ],
            options={
                'db_table': 'tbl_about_rationale_sub_project',
            },
        ),
        migrations.CreateModel(
            name='AboutSubProjectObjectiveDetail',
            fields=[
                ('detail_id', models.AutoField(primary_key=True, serialize=False)),
                ('detail', models.TextField()),
                ('about', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.about')),
                ('objective', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='appAdmin.aboutsubprojectobjective')),
            ],
            options={
                'db_table': 'tbl_about_objective_detail_sub_project',
            },
        ),
        migrations.AddField(
            model_name='aboutsubproject',
            name='about',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.about'),
        ),
        migrations.CreateModel(
            name='AboutRationale',
            fields=[
                ('rationale_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('detail', models.TextField()),
                ('about', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.about')),
            ],
            options={
                'db_table': 'tbl_about_rationale',
            },
        ),
        migrations.CreateModel(
            name='AboutObjectiveDetail',
            fields=[
                ('detail_id', models.AutoField(primary_key=True, serialize=False)),
                ('detail', models.TextField()),
                ('about', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.about')),
                ('objective', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='appAdmin.aboutobjective')),
            ],
            options={
                'db_table': 'tbl_about_objective_detail',
            },
        ),
        migrations.AddField(
            model_name='aboutobjective',
            name='about',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.about'),
        ),
        migrations.CreateModel(
            name='AboutActivity',
            fields=[
                ('activity_id', models.AutoField(primary_key=True, serialize=False)),
                ('icon', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('detail', models.TextField()),
                ('about', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appAdmin.about')),
            ],
            options={
                'db_table': 'tbl_about_activity',
            },
        ),
    ]
