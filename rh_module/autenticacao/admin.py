from django.contrib import admin
from .models import UserProfile

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    #list_display = ['user', 'cargo_rh', 'funcionario']
    list_filter = ['cargo_rh']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']