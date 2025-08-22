from pathlib import Path
from django.core.mail import EmailMessage
from django.conf import settings
from .export import export_docx, export_pdf

def enviar_reporte(obj, to_email, subject, body, adj_docx=True, adj_pdf=True, request=None):
    """
    Envía (o guarda en /outbox) un correo con los adjuntos DOCX/PDF del reporte.
    En DEV (filebased backend) se genera un archivo .log en settings.EMAIL_FILE_PATH.
    """
    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@local"),
        to=[to_email],
    )

    # adjuntos
    if adj_docx:
        path_docx = export_docx(obj)
        msg.attach(path_docx.name, Path(path_docx).read_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    if adj_pdf:
        path_pdf = export_pdf(obj, request=request)
        msg.attach(path_pdf.name, Path(path_pdf).read_bytes(), "application/pdf")

    msg.send(fail_silently=False)
    return True
