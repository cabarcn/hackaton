# core/models.py
from django.db import models
from django.contrib.auth.models import User

# =======================================
# FORMULARIO OFICIAL RENCA: SolicitudRenca
# =======================================
class SolicitudRenca(models.Model):
    # Meta
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    proposito = models.TextField(blank=True)  # <- nuevo: guardamos el propósito inicial

    # Identificación Unidad Solicitante
    unidad_nombre = models.CharField(max_length=200)
    unidad_direccion = models.CharField(max_length=200, blank=True)
    unidad_departamento = models.CharField(max_length=200, blank=True)

    # Funcionario responsable
    resp_nombre = models.CharField(max_length=200)
    resp_telefono = models.CharField(max_length=30, blank=True)
    resp_correo = models.EmailField()

    # Identificación de la licitación
    TIPO_ADQ_CHOICES = [
        ("bienes", "Adquisición de bienes de consumo o equipamientos"),
        ("serv_habituales", "Contratación de servicios habituales"),
        ("equipos_veh_maq", "Adquisición de equipos, vehículos o maquinarias"),
        ("serv_generales", "Contratación de servicios generales"),
        ("software_lic", "Adquisición de softwares, licencias o similares"),
        ("serv_prof", "Contratación de servicios profesionales"),
        ("suministro", "Suministro de bienes o servicios"),
        ("obras_civiles", "Contratación de ejecución de obras civiles"),
    ]
    tipo_adquisicion = models.CharField(max_length=30, choices=TIPO_ADQ_CHOICES)
    nombre_licitacion = models.CharField(max_length=300)

    # Características generales de la licitación
    MOD_ADJ_CHOICES = [("simple", "Adjudicación simple"), ("multiple", "Adjudicación múltiple (por línea)")]
    modalidad_adjudicacion = models.CharField(max_length=10, choices=MOD_ADJ_CHOICES)

    # Actividades
    REQ_CHOICES = [("no", "No"), ("obligatoria", "Obligatoria"), ("voluntaria", "Voluntaria")]
    visita_terreno = models.CharField(max_length=12, choices=REQ_CHOICES, default="no")
    visita_lugar = models.CharField(max_length=200, blank=True)
    reunion_informativa = models.CharField(max_length=12, choices=REQ_CHOICES, default="no")
    reunion_lugar = models.CharField(max_length=200, blank=True)
    entrega_muestras = models.BooleanField(default=False)
    muestra_lugar = models.CharField(max_length=200, blank=True)
    prueba_tecnica = models.BooleanField(default=False)
    prueba_lugar = models.CharField(max_length=200, blank=True)

    # Características de la contratación
    MOD_CONTRATO_CHOICES = [
        ("suma_alzada", "A suma alzada"),
        ("precios_unitarios", "Serie de precios unitarios"),
        ("mixta", "A suma alzada y serie de precios unitarios"),
        ("otra", "Otra modalidad"),
    ]
    modalidad_contratacion = models.CharField(max_length=20, choices=MOD_CONTRATO_CHOICES)
    modalidad_contratacion_otra = models.CharField(max_length=200, blank=True)

    PLAZO_UNIDAD_CHOICES = [("dias", "Días corridos"), ("meses", "Meses")]
    plazo_valor = models.PositiveIntegerField()
    plazo_unidad = models.CharField(max_length=10, choices=PLAZO_UNIDAD_CHOICES)
    fecha_inicio_contrato = models.DateField(null=True, blank=True)

    # Monto + Moneda
    MONEDA_CHOICES = [("CLP", "Pesos"), ("USD", "Dólares"), ("UTM", "UTM"), ("UF", "UF"), ("OTRA", "Otra")]
    monto_contratacion = models.DecimalField(max_digits=16, decimal_places=2)
    moneda = models.CharField(max_length=4, choices=MONEDA_CHOICES, default="CLP")
    moneda_otra = models.CharField(max_length=30, blank=True)

    # Presupuesto / Reajustabilidad
    TIPO_PRESUP_CHOICES = [("disponible", "Disponible"), ("referencial", "Referencial o Estimado")]
    tipo_presupuesto = models.CharField(max_length=12, choices=TIPO_PRESUP_CHOICES)
    reajustable = models.BooleanField(default=False)

    # Financiamiento
    FINANC_CHOICES = [("municipal", "Municipal"), ("externo", "Externo")]
    tipo_financiamiento = models.CharField(max_length=10, choices=FINANC_CHOICES)
    fuente_financiamiento = models.CharField(max_length=200, blank=True)

    # Trazabilidad
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Solicitud Renca #{self.id} - {self.nombre_licitacion}"

# === Pauta de Evaluación ===
class PautaFactor(models.Model):
    solicitud = models.ForeignKey(SolicitudRenca, on_delete=models.CASCADE, related_name="pauta_factores")
    nombre = models.CharField(max_length=150)
    porcentaje = models.PositiveIntegerField(help_text="Debe sumar 100% entre todos los factores.")
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje}%)"

# === Comisión Evaluadora ===
class MiembroComision(models.Model):
    ROL_CHOICES = [("titular", "Titular"), ("reemplazo", "Reemplazo")]
    solicitud = models.ForeignKey(SolicitudRenca, on_delete=models.CASCADE, related_name="comision_miembros")
    nombre = models.CharField(max_length=200)
    unidad = models.CharField(max_length=200, blank=True)
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default="titular")

    def __str__(self):
        return f"{self.nombre} - {self.get_rol_display()}"

# === Normativas ===
class Normativa(models.Model):
    solicitud = models.ForeignKey(SolicitudRenca, on_delete=models.CASCADE, related_name="normativas")
    nombre = models.CharField(max_length=200)
    numero = models.CharField(max_length=60, blank=True)  # ej. Ley 19.886, DS 250, etc.
    fecha = models.DateField(null=True, blank=True)
    institucion = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.nombre

# === Multas ===
class Multa(models.Model):
    solicitud = models.ForeignKey(SolicitudRenca, on_delete=models.CASCADE, related_name="multas")
    nro = models.PositiveIntegerField(verbose_name="N°")
    causa = models.TextField()
    aplicacion = models.TextField(help_text="Cómo se aplica / condición")
    monto_utm = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["nro"]

    def __str__(self):
        return f"Multa {self.nro} - {self.monto_utm} UTM"
