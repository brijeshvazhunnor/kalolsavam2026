from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),  # signup only

    # Dashboards (role based)
    path("organizer/dashboard/", views.organizer_dashboard, name="organizer_dashboard"),
    path("college/dashboard/", views.college_dashboard, name="college_dashboard"),


    # College features
    path("college/register-student/", views.register_student, name="register_student"),
    path("college/edit-student/<int:student_id>/", views.edit_student, name="edit_student"),
    path("team/create/", views.team_creation, name="team_creation"),
    path("team/<int:team_id>/edit/", views.edit_team, name="edit_team"),
    path("team/delete/<int:team_id>/", views.delete_team, name="delete_team"),
    path("college/student-summary/", views.student_summary, name="student_summary"),
    

    #result_committee
    path("organizer/dashboard/", views.organizer_dashboard, name="organizer_dashboard"),
    path("organizer/", views.organizer_dashboard, name="organizer_dashboard"),

    # Items & Results
    path("organizer/items/", views.organizer_items, name="organizer_items"),
    path("organizer/results/add/<int:item_id>/", views.add_results, name="add_results"),
    path("organizer/results/view/<int:item_id>/", views.view_results, name="view_results"),
    path("organizer/results/edit/<int:result_id>/", views.edit_result, name="edit_result"),
    path("organizer/results/delete/<int:item_id>/", views.delete_item_results, name="delete_item_results"),
    path("organizer/results/undo/<int:item_id>/", views.undo_delete_results, name="undo_delete_results"),

    # Rankings
    path("organizer/college-ranking-live/", views.college_ranking_live, name="college_ranking_live"),

    # Student result search
    path("organizer/student-results/", views.organizer_student_results, name="organizer_student_results"),

    #PublicResultssss
    path("results/", views.public_results, name="public_results"),

    # ADMIN (CUSTOM DASHBOARD)
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/users/", views.admin_users, name="admin_users"),
    path("admin-panel/users/add/", views.admin_add_user, name="admin_add_user"),
    path("admin-panel/users/<int:user_id>/edit/", views.admin_edit_user, name="admin_edit_user"),
    path("admin-panel/settings/", views.admin_site_settings, name="admin_settings"),
    path("admin-panel/brochures/", views.admin_brochures, name="admin_brochures"),
    path("admin-panel/brochures/add/", views.admin_add_brochure, name="admin_add_brochure"),
    path("admin-panel/users/toggle/<int:user_id>/",views.admin_toggle_user,name="admin_toggle_user"),
    path("admin-panel/users/<int:user_id>/delete/",views.admin_delete_user,name="admin_delete_user"),
]