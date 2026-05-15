from django.contrib import admin
from .models import Cargo


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ['id_cargo', 'nome', 'id_departamento', 'nivel']
    list_filter = ['id_departamento', 'nivel']
    search_fields = ['nome']
    ordering = ['id_departamento', 'nivel']