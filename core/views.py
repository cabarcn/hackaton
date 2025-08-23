# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import PropositoInicialForm, SolicitudRencaForm, PautaFormSet, ComisionFormSet, NormativaFormSet, MultaFormSet
from .models import SolicitudRenca
from .services.export import export_renca_pdf
from .services.ai_renca import analizar_renca
from django.shortcuts import render
from .services.llm import respond  # o 'chat' si prefieres mensajes



def home(request):
    return redirect('proposito') if request.user.is_authenticated else redirect('login')


def login_view(request):
    next_url = request.GET.get("next") or request.POST.get("next") or "proposito"
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user:
            login(request, user)
            return redirect(next_url)
        messages.error(request, "Credenciales inválidas")
    return render(request, "core/login.html", {"next": next_url})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def proposito(request):
    if request.method == "POST":
        form = PropositoInicialForm(request.POST)
        if form.is_valid():
            request.session['proposito_inicial'] = form.cleaned_data['proposito'].strip()
            return redirect('renca_nueva')
    else:
        form = PropositoInicialForm(initial={'proposito': request.session.get('proposito_inicial', '')})
    return render(request, "core/proposito.html", {"form": form})



@login_required
def renca_nueva(request):
    if request.method == "POST":
        form = SolicitudRencaForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.usuario = request.user
            obj.proposito = request.session.pop('proposito_inicial', '')
            obj.save()
            messages.success(request, "Solicitud guardada.")
            return redirect("renca_ver", pk=obj.id)
    else:
        form = SolicitudRencaForm()
    return render(request, "core/renca_form.html", {"form": form})


@login_required
def renca_ver(request, pk):
    obj = get_object_or_404(SolicitudRenca, pk=pk, usuario=request.user)
    return render(request, "core/renca_ver.html", {"obj": obj})


@login_required
def renca_tablas(request, pk):
    obj = get_object_or_404(SolicitudRenca, pk=pk, usuario=request.user)

    if request.method == "POST":
        pauta_fs = PautaFormSet(request.POST, instance=obj, prefix="pauta")
        com_fs   = ComisionFormSet(request.POST, instance=obj, prefix="comision")
        norm_fs  = NormativaFormSet(request.POST, instance=obj, prefix="norm")
        multa_fs = MultaFormSet(request.POST, instance=obj, prefix="multa")

        if all([pauta_fs.is_valid(), com_fs.is_valid(), norm_fs.is_valid(), multa_fs.is_valid()]):
            pauta_fs.save(); com_fs.save(); norm_fs.save(); multa_fs.save()
            messages.success(request, "Tablas guardadas correctamente.")
            return redirect("renca_tablas", pk=obj.id)
    else:
        pauta_fs = PautaFormSet(instance=obj, prefix="pauta")
        com_fs   = ComisionFormSet(instance=obj, prefix="comision")
        norm_fs  = NormativaFormSet(instance=obj, prefix="norm")
        multa_fs = MultaFormSet(instance=obj, prefix="multa")

    return render(request, "core/renca_tablas.html", {
        "obj": obj,
        "pauta_fs": pauta_fs,
        "com_fs": com_fs,
        "norm_fs": norm_fs,
        "multa_fs": multa_fs,
    })


@login_required
def renca_pdf(request, pk):
    obj = get_object_or_404(SolicitudRenca, pk=pk, usuario=request.user)
    pdf_path = export_renca_pdf(obj, request=request)
    from django.http import FileResponse
    return FileResponse(open(pdf_path, "rb"), as_attachment=True, filename=f"Solicitud_Renca_{obj.id}.pdf")


@login_required
def renca_analizar(request, pk):
    obj = get_object_or_404(SolicitudRenca, pk=pk, usuario=request.user)
    data = {
        "proposito": obj.proposito,
        "unidad": {"nombre": obj.unidad_nombre, "direccion": obj.unidad_direccion, "departamento": obj.unidad_departamento},
        "responsable": {"nombre": obj.resp_nombre, "telefono": obj.resp_telefono, "correo": obj.resp_correo},
        "licitacion": {
            "tipo": obj.get_tipo_adquisicion_display(),
            "nombre": obj.nombre_licitacion,
            "modalidad_adjudicacion": obj.get_modalidad_adjudicacion_display(),
        },
        "actividades": {
            "visita": {"tipo": obj.get_visita_terreno_display(), "lugar": obj.visita_lugar},
            "reunion": {"tipo": obj.get_reunion_informativa_display(), "lugar": obj.reunion_lugar},
            "muestras": {"si": obj.entrega_muestras, "lugar": obj.muestra_lugar},
            "prueba": {"si": obj.prueba_tecnica, "lugar": obj.prueba_lugar},
        },
        "contratacion": {
            "modalidad": obj.get_modalidad_contratacion_display(),
            "otra": obj.modalidad_contratacion_otra,
            "plazo": f"{obj.plazo_valor} {obj.get_plazo_unidad_display()}",
            "fecha_inicio": obj.fecha_inicio_contrato.isoformat() if obj.fecha_inicio_contrato else "",
        },
        "monto": {"valor": float(obj.monto_contratacion), "moneda": obj.get_moneda_display(), "otra": obj.moneda_otra},
        "presupuesto": {"tipo": obj.get_tipo_presupuesto_display(), "reajustable": obj.reajustable},
        "financiamiento": {"tipo": obj.get_tipo_financiamiento_display(), "fuente": obj.fuente_financiamiento},
        "pauta": [{"factor": f.nombre, "porcentaje": f.porcentaje, "descripcion": f.descripcion} for f in obj.pauta_factores.all()],
        "comision": [{"nombre": m.nombre, "unidad": m.unidad, "rol": m.get_rol_display()} for m in obj.comision_miembros.all()],
        "normativas": [{"nombre": n.nombre, "numero": n.numero, "fecha": n.fecha.isoformat() if n.fecha else "", "institucion": n.institucion} for n in obj.normativas.all()],
        "multas": [{"nro": m.nro, "causa": m.causa, "aplicacion": m.aplicacion, "monto_utm": float(m.monto_utm)} for m in obj.multas.all()],
    }
    resultado = analizar_renca(data)
    return render(request, "core/renca_reporte.html", {"obj": obj, "resultado": resultado})

def demo_llm(request):
    salida = None
    prompt_inicial = "Escribe 'pong' y nada más."
    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip() or prompt_inicial
        salida = respond(prompt)  # llamada al servicio
    return render(request, "core/demo_llm.html", {"salida": salida, "prompt_inicial": prompt_inicial})
