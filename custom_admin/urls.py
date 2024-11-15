# custom_admin/urls.py

from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='login'),
    path('logout/', views.AdminLogoutView.as_view(), name='logout'),
    path('dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),
    path('view-phone/<str:number>/', views.ViewPhoneNumberView.as_view(), name='view_phone'),
    path('edit-phone/<str:number>/', views.EditPhoneNumberView.as_view(), name='edit_phone'),
    path('delete-phone/<str:number>/', views.DeletePhoneNumberView.as_view(), name='delete_phone'),
    path('assign-admin/<str:number>/<int:community_id>/', views.AssignAdminView.as_view(), name='assign_admin'),
     path('edit-member-status/<int:member_id>/', views.EditMemberStatusView.as_view(), name='edit_member_status'),
]
