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
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("college/dashboard/", views.college_dashboard, name="college_dashboard"),


    # College features
    path("college/register-student/", views.register_student, name="register_student"),
    path("college/edit-student/<int:student_id>/", views.edit_student, name="edit_student"),
    path("team/create/", views.team_creation, name="team_creation"),
    

]
