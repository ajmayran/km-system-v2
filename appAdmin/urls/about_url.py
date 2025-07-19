from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from appAdmin.views import about_view
app_name = "appAdmin"

urlpatterns = (
    [

        path("main-about/", about_view.admin_main_about_page, name="main-about-page"),
        path("main-about/add/", about_view.admin_main_about_add, name="main-about-add"),
        path('objective-edit/<int:objective_id>/', about_view.admin_main_objective_edit, name='objective-edit'),
        path("main-about/edit/<int:about_id>/", about_view.admin_main_about_edit, name="main-about-edit"),
        path("main-about/delete/<int:about_id>/", about_view.admin_main_about_delete, name="main-about-delete"),

        # Image CRUD URLs
        path('image/add/<int:program_id>/', about_view.admin_image_add, name='image-add'),
        path('image/edit/<int:image_id>/', about_view.admin_image_edit, name='image-edit'),
        path('image/delete/<int:image_id>/', about_view.admin_image_delete, name='image-delete'),
        
        # Objective CRUD URLs
        path('objective/add/<int:program_id>/', about_view.admin_main_objective_add, name='objective-add'),
        # path('objective/edit/<int:objective_id>/', about_view.admin_main_objective_edit, name='objective-edit'),
        path('objective/delete/<int:objective_id>/', about_view.admin_main_objective_delete, name='objective-delete'),
        
        # Title Bullet CRUD URLs
        path('title-bullet/add/<int:objective_id>/', about_view.admin_title_bullet_add, name='title-bullet-add'),
        # path('title-bullet/edit/<int:bullet_id>/', about_view.admin_title_bullet_edit, name='title-bullet-edit'),
        path('title-bullet/delete/<int:bullet_id>/', about_view.admin_title_bullet_delete, name='title-bullet-delete'),
        
        # Target Bullet CRUD URLs
        path('target-bullet/add/<int:objective_id>/', about_view.admin_target_bullet_add, name='target-bullet-add'),
        # path('target-bullet/edit/<int:bullet_id>/', about_view.admin_target_bullet_edit, name='target-bullet-edit'),
        path('target-bullet/delete/<int:bullet_id>/', about_view.admin_target_bullet_delete, name='target-bullet-delete'),

        # Rationale URLs
        path('about-rationale/<int:pk>/', about_view.about_rationale, name='about-rationale'),
        path('about-rationale/<int:pk>/add/', about_view.about_rationale_add, name='about-rationale-add'),
        path('about-rationale/edit/<int:rationale_id>/', about_view.about_rationale_edit, name='about-rationale-edit'),
        path('about-rationale/delete/<int:rationale_id>/', about_view.about_rationale_delete, name='about-rationale-delete'),

        # Objective
        path('about-objective/<int:pk>/', about_view.about_objective, name='about-objective'),
        path('about-objective/<int:pk>/add/', about_view.about_objective_add, name='about-objective-add'),
        path('about/objective/edit/<int:pk>/', about_view.about_objective_edit, name='about-objective-edit'),
        path('about-objective/delete/<int:objective_id>/', about_view.about_objective_delete, name='about-objective-delete'),

        # Objective Detail (No separate page needed)
        # path('about-objective/<int:pk>/detail/add/', about_view.about_objectivedetail_add, name='about-objectivedetail-add'),
        # path('about-objective/detail/edit/<int:detail_id>/', about_view.about_objectivedetail_edit, name='about-objectivedetail-edit'),
        # path('about-objective/detail/delete/<int:detail_id>/', about_view.about_objectivedetail_delete, name='about-objectivedetail-delete'),

        # Activity URLs
        path('about-activity/<int:pk>/', about_view.about_activity, name='about-activity'),
        path('about-activity/<int:pk>/add/', about_view.about_activity_add, name='about-activity-add'),
        path('about-activity/edit/<int:activity_id>/', about_view.about_activity_edit, name='about-activity-edit'),
        path('about-activity/delete/<int:activity_id>/', about_view.about_activity_delete, name='about-activity-delete'),

        # Timeline URLs
        path('about-timeline/<int:pk>/', about_view.about_timeline, name='about-timeline'),
        path('about-timeline/<int:pk>/add/', about_view.about_timeline_add, name='about-timeline-add'),
        path('about-timeline/edit/<int:timeline_id>/', about_view.about_timeline_edit, name='about-timeline-edit'),
        path('about-timeline/delete/<int:timeline_id>/', about_view.about_timeline_delete, name='about-timeline-delete'),
          # Bullets URLs
        # Bullets URLs
        path('about-timeline/<int:timeline_id>/bullets/add/', about_view.about_timeline_bullets_add, name='about-timeline-bullets-add'),
        path('about-timeline/<int:timeline_id>/bullets/edit/', about_view.about_timeline_bullets_edit, name='about-timeline-bullets-edit'),
        path('about-timeline/bullet/<int:bullet_id>/delete/', about_view.about_timeline_bullets_delete, name='about-timeline-bullets-delete'),

        # Images URLs
        path('about-timeline/<int:timeline_id>/images/add/', about_view.about_timeline_images_add, name='about-timeline-images-add'),
        path('about-timeline/<int:timeline_id>/images/edit/', about_view.about_timeline_images_edit, name='about-timeline-images-edit'),
        path('about-timeline/image/<int:image_id>/delete/', about_view.about_timeline_images_delete, name='about-timeline-images-delete'),
        # path('about-timeline/bullets/add/<int:timeline_id>/', about_view.about_timeline_bullets_add, name='about-timeline-bullets-add'),
        # path('about-timeline/bullets/edit/<int:timeline_id>/', about_view.about_timeline_bullets_edit, name='about-timeline-bullets-edit'),
        # path('about-timeline/bullets/get/<int:timeline_id>/', about_view.about_timeline_bullets_get, name='about-timeline-bullets-get'),
        
        # # Images URLs 
        # path('about-timeline/images/add/<int:timeline_id>/', about_view.about_timeline_images_add, name='about-timeline-images-add'),
        # path('about-timeline/images/edit/<int:timeline_id>/', about_view.about_timeline_images_edit, name='about-timeline-images-edit'),
        # path('about-timeline/images/get/<int:timeline_id>/', about_view.about_timeline_images_get, name='about-timeline-images-get'),

        # Team URLs
        path('about-team/<int:pk>/', about_view.about_team, name='about-team'),
        path('about-team/<int:pk>/add/', about_view.about_team_add, name='about-team-add'),
        path('about-team/edit/<int:member_id>/', about_view.about_team_edit, name='about-team-edit'),
        path('about-team/delete/<int:member_id>/', about_view.about_team_delete, name='about-team-delete'),

        # Team Social URLs
        path('about-team/social/add/<int:member_id>/', about_view.about_team_social_add, name='about-team-social-add'),
        path('about-team/social/delete/<int:social_id>/', about_view.about_team_social_delete, name='about-team-social-delete'),

        # Sub Project URLs
        path('about-sub-project/<int:pk>/', about_view.about_sub_project, name='about-sub-project'),
        path('about-sub-project/<int:about_id>/add/', about_view.about_sub_project_add, name='about-sub-project-add'),
        path('about-sub-project/edit/<int:sub_id>/', about_view.about_sub_project_edit, name='about-sub-project-edit'),
        path('about-sub-project/delete/<int:sub_id>/', about_view.about_sub_project_delete, name='about-sub-project-delete'),

        # Sub Project Rationale URLs
        path('about-sub-rationale/<int:pk>/', about_view.about_sub_rationale, name='about-sub-rationale'),
        path('about-sub-rationale/<int:pk>/add/', about_view.about_rationale_sub_add, name='about-rationale-sub-add'),
        path('about-sub-rationale/edit/<int:rationale_id>/', about_view.about_rationale_sub_edit, name='about-rationale-sub-edit'),
        path('about-sub-rationale/delete/<int:rationale_id>/', about_view.about_rationale_sub_delete, name='about-rationale-sub-delete'),

        # Sub Objective
        path('about-sub-objective/<int:pk>/', about_view.about_sub_objective, name='about-sub-objective'),
        path('about-sub-objective/<int:pk>/add/', about_view.about_objective_sub_add, name='about-objective-sub-add'),
        path('about-sub-objective/edit/<int:objective_id>/', about_view.about_objective_sub_edit, name='about-objective-sub-edit'),
        path('about-sub-objective/delete/<int:objective_id>/', about_view.about_objective_sub_delete, name='about-objective-sub-delete'),

        # Timeline URLs
        path('about-sub-timeline/<int:pk>/', about_view.about_sub_timeline, name='about-sub-timeline'),
        path('about-sub-timeline/<int:pk>/add/', about_view.about_timeline_sub_add, name='about-sub-timeline-add'),
        path('about-sub-timeline/edit/<int:timeline_id>/', about_view.about_timeline_sub_edit, name='about-sub-timeline-edit'),
        path('about-sub-timeline/delete/<int:timeline_id>/', about_view.about_timeline_sub_delete, name='about-sub-timeline-delete'),

        path('about-sub-timeline/<int:timeline_id>/bullets/add/', about_view.timeline_bullet_add, name='timeline-bullet-add'),
        path('about-sub-timeline/<int:timeline_id>/bullets/edit/', about_view.timeline_bullet_edit, name='timeline-bullet-edit'),
        path('about-sub-timeline/bullet/<int:bullet_id>/delete/', about_view.timeline_bullet_delete, name='timeline-bullet-delete'),
        
        path('about-sub-timeline/<int:timeline_id>/images/add/', about_view.timeline_image_add, name='timeline-image-add'),
        path('about-sub-timeline/<int:timeline_id>/images/edit/', about_view.timeline_image_edit, name='timeline-image-edit'),
        path('about-sub-timeline/image/<int:image_id>/delete/', about_view.timeline_image_delete, name='timeline-image-delete'),

        # Sub Team URLs
        path('about-sub-team/<int:pk>/', about_view.about_sub_team, name='about-sub-team'),
        path('about-sub-team/<int:pk>/add/', about_view.about_team_sub_add, name='about-team-sub-add'),
        path('about-sub-team/edit/<int:member_id>/', about_view.about_team_sub_edit, name='about-team-sub-edit'),
        path('about-sub-team/delete/<int:member_id>/', about_view.about_team_sub_delete, name='about-team-sub-delete'),

        # Team Sub Social URLs
        path('about-sub-team/social/add/<int:member_id>/', about_view.about_team_social_sub_add, name='about-team-social-sub-add'),
        path('about-sub-team/social/delete/<int:social_id>/', about_view.about_team_social_sub_delete, name='about-team-social-sub-delete'),

        path("about/page/edit/<int:about_id>/", about_view.admin_about_page_edit, name="about-page-edit"),

        path("about/", about_view.admin_about_page, name="about-page"),
        path("about/add/", about_view.admin_about_add, name="about-add"),
        path('about/edit/<int:about_id>/', about_view.admin_about_edit, name='about-edit'),
        path("about/delete/<int:about_id>/", about_view.admin_about_delete, name="about-delete"),
        path("footer/", about_view.admin_about_footer, name="about-footer"),
        path(
            "footer/edit/", about_view.admin_about_footer_edit, name="about-footer-edit"
        ),
        path("upload-video/", about_view.admin_upload_video, name="admin-video-upload"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)