from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'setor', 'is_gerente', 'primeiro_acesso']
    list_filter   = ['setor', 'is_gerente']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']