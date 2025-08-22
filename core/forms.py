# core/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory, BaseInlineFormSet

from .models import (
    SolicitudRenca,
    PautaFactor, MiembroComision,
    Normativa, Multa,
)

# =========================
# 1) Propósito (simple)
# =========================
class PropositoInicialForm(forms.Form):
    proposito = forms.CharField(
        label="Propósito de la licitación",
        required=True,
        strip=True,
        widget=forms.Textarea(attrs={
            "rows": 5,
            "class": "form-control",
            "placeholder": "Describe a qué va la licitación..."
        })
    )


# =========================
# 2) Formulario oficial RENCA
# =========================
class SolicitudRencaForm(forms.ModelForm):
    class Meta:
        model = SolicitudRenca
        fields = [
            "unidad_nombre","unidad_direccion","unidad_departamento",
            "resp_nombre","resp_telefono","resp_correo",
            "tipo_adquisicion","nombre_licitacion","modalidad_adjudicacion",
            "visita_terreno","visita_lugar","reunion_informativa","reunion_lugar",
            "entrega_muestras","muestra_lugar","prueba_tecnica","prueba_lugar",
            "modalidad_contratacion","modalidad_contratacion_otra",
            "plazo_valor","plazo_unidad","fecha_inicio_contrato",
            "monto_contratacion","moneda","moneda_otra",
            "tipo_presupuesto","reajustable",
            "tipo_financiamiento","fuente_financiamiento",
        ]
        widgets = {
            # textos
            "unidad_nombre": forms.TextInput(attrs={"class":"form-control"}),
            "unidad_direccion": forms.TextInput(attrs={"class":"form-control"}),
            "unidad_departamento": forms.TextInput(attrs={"class":"form-control"}),
            "resp_nombre": forms.TextInput(attrs={"class":"form-control"}),
            "resp_telefono": forms.TextInput(attrs={"class":"form-control"}),
            "resp_correo": forms.EmailInput(attrs={"class":"form-control","placeholder":"correo@institucional.cl"}),
            "nombre_licitacion": forms.TextInput(attrs={"class":"form-control"}),

            # selects
            "tipo_adquisicion": forms.Select(attrs={"class":"form-select"}),
            "modalidad_adjudicacion": forms.Select(attrs={"class":"form-select"}),
            "visita_terreno": forms.Select(attrs={"class":"form-select"}),
            "reunion_informativa": forms.Select(attrs={"class":"form-select"}),
            "modalidad_contratacion": forms.Select(attrs={"class":"form-select"}),
            "plazo_unidad": forms.Select(attrs={"class":"form-select"}),
            "moneda": forms.Select(attrs={"class":"form-select"}),
            "tipo_presupuesto": forms.Select(attrs={"class":"form-select"}),
            "tipo_financiamiento": forms.Select(attrs={"class":"form-select"}),

            # números/fechas
            "plazo_valor": forms.NumberInput(attrs={"class":"form-control", "min":"1"}),
            "fecha_inicio_contrato": forms.DateInput(attrs={"class":"form-control", "type":"date"}),
            "monto_contratacion": forms.NumberInput(attrs={"class":"form-control", "step":"0.01", "min":"0"}),

            # “otra”/lugares
            "modalidad_contratacion_otra": forms.TextInput(attrs={"class":"form-control"}),
            "visita_lugar": forms.TextInput(attrs={"class":"form-control"}),
            "reunion_lugar": forms.TextInput(attrs={"class":"form-control"}),
            "muestra_lugar": forms.TextInput(attrs={"class":"form-control"}),
            "prueba_lugar": forms.TextInput(attrs={"class":"form-control"}),
            "moneda_otra": forms.TextInput(attrs={"class":"form-control"}),
            "fuente_financiamiento": forms.TextInput(attrs={"class":"form-control"}),

            # checkboxes
            "entrega_muestras": forms.CheckboxInput(attrs={"class":"form-check-input"}),
            "prueba_tecnica": forms.CheckboxInput(attrs={"class":"form-check-input"}),
            "reajustable": forms.CheckboxInput(attrs={"class":"form-check-input"}),
        }

    def clean(self):
        data = super().clean()
        # Validaciones condicionales sencillas del formulario RENCA
        if data.get("modalidad_contratacion") == "otra" and not (data.get("modalidad_contratacion_otra") or "").strip():
            self.add_error("modalidad_contratacion_otra", "Especifique la otra modalidad.")
        if data.get("moneda") == "OTRA" and not (data.get("moneda_otra") or "").strip():
            self.add_error("moneda_otra", "Indique la moneda.")
        if data.get("tipo_financiamiento") == "externo" and not (data.get("fuente_financiamiento") or "").strip():
            self.add_error("fuente_financiamiento", "Indique la fuente del financiamiento externo.")
        return data


# =========================
# 3) Pauta de Evaluación
# =========================
class PautaFactorForm(forms.ModelForm):
    class Meta:
        model = PautaFactor
        fields = ["nombre", "porcentaje", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class":"form-control"}),
            "porcentaje": forms.NumberInput(attrs={"class":"form-control","min":"1","max":"100"}),
            "descripcion": forms.Textarea(attrs={"class":"form-control","rows":2}),
        }

class BasePautaFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = 0
        activos = 0
        for form in self.forms:
            if form.cleaned_data.get("DELETE"):
                continue
            if not form.cleaned_data:
                continue
            nombre = (form.cleaned_data.get("nombre") or "").strip()
            if not nombre:
                if form.cleaned_data.get("porcentaje"):
                    raise ValidationError("Cada factor debe tener nombre.")
                continue
            activos += 1
            pct = form.cleaned_data.get("porcentaje") or 0
            total += pct
            if pct <= 0 or pct > 100:
                raise ValidationError("Cada porcentaje debe estar entre 1 y 100.")
        if activos == 0:
            raise ValidationError("Agrega al menos un factor de evaluación.")
        if total != 100:
            raise ValidationError(f"Los porcentajes deben sumar 100%. Actualmente suman {total}%.")

PautaFormSet = inlineformset_factory(
    parent_model=SolicitudRenca,
    model=PautaFactor,
    form=PautaFactorForm,
    formset=BasePautaFormSet,
    extra=2, can_delete=True, min_num=1, validate_min=True
)


# =========================
# 4) Comisión Evaluadora
# =========================
class MiembroComisionForm(forms.ModelForm):
    class Meta:
        model = MiembroComision
        fields = ["nombre", "unidad", "rol"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class":"form-control"}),
            "unidad": forms.TextInput(attrs={"class":"form-control"}),
            "rol": forms.Select(attrs={"class":"form-select"}),
        }

ComisionFormSet = inlineformset_factory(
    parent_model=SolicitudRenca,
    model=MiembroComision,
    form=MiembroComisionForm,
    extra=2, can_delete=True, min_num=1, validate_min=True
)


# =========================
# 5) Normativas
# =========================
class NormativaForm(forms.ModelForm):
    class Meta:
        model = Normativa
        fields = ["nombre", "numero", "fecha", "institucion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class":"form-control"}),
            "numero": forms.TextInput(attrs={"class":"form-control"}),
            "fecha": forms.DateInput(attrs={"class":"form-control","type":"date"}),
            "institucion": forms.TextInput(attrs={"class":"form-control"}),
        }

NormativaFormSet = inlineformset_factory(
    parent_model=SolicitudRenca,
    model=Normativa,
    form=NormativaForm,
    extra=2, can_delete=True
)


# =========================
# 6) Multas
# =========================
class MultaForm(forms.ModelForm):
    class Meta:
        model = Multa
        fields = ["nro", "causa", "aplicacion", "monto_utm"]
        widgets = {
            "nro": forms.NumberInput(attrs={"class":"form-control","min":"1"}),
            "causa": forms.Textarea(attrs={"class":"form-control","rows":2}),
            "aplicacion": forms.Textarea(attrs={"class":"form-control","rows":2}),
            "monto_utm": forms.NumberInput(attrs={"class":"form-control","step":"0.01","min":"0.01"}),
        }

class BaseMultaFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        usados = set()
        for form in self.forms:
            if form.cleaned_data.get("DELETE"):
                continue
            if not form.cleaned_data:
                continue
            nro = form.cleaned_data.get("nro")
            if nro in usados:
                raise ValidationError(f"N° de multa repetido: {nro}.")
            if nro:
                usados.add(nro)
            monto = form.cleaned_data.get("monto_utm")
            if monto is not None and monto <= 0:
                raise ValidationError("El monto en UTM debe ser mayor a 0.")

MultaFormSet = inlineformset_factory(
    parent_model=SolicitudRenca,
    model=Multa,
    form=MultaForm,
    formset=BaseMultaFormSet,
    extra=2, can_delete=True
)
