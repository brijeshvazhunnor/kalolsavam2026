from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PublicDocument


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role Info", {'fields': ('role','college_name')}),
    )
    list_display = ('username','email','role','is_staff')


from django.contrib import admin
from .models import PublicDocument

@admin.register(PublicDocument)
class PublicDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "document_type", "created_at", "is_active")
    list_filter = ("document_type", "is_active")
    search_fields = ("title",)
