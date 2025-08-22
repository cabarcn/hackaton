from django.contrib import admin
from .models import SolicitudRenca, PautaFactor, MiembroComision, Normativa, Multa

class PautaFactorInline(admin.TabularInline): model = PautaFactor; extra = 0
class MiembroComisionInline(admin.TabularInline): model = MiembroComision; extra = 0
class NormativaInline(admin.TabularInline): model = Normativa; extra = 0
class MultaInline(admin.TabularInline): model = Multa; extra = 0

@admin.register(SolicitudRenca)
class SolicitudRencaAdmin(admin.ModelAdmin):
    list_display = ("id","usuario","nombre_licitacion","tipo_adquisicion","creado")
    search_fields = ("nombre_licitacion","usuario__username")
    list_filter = ("tipo_adquisicion","creado")
    inlines = [PautaFactorInline, MiembroComisionInline, NormativaInline, MultaInline]
