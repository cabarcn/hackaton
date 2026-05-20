# licitacionesIA

Asistente de IA para apoyar la elaboración, revisión y mejora de bases de licitación municipales.

> Repositorio actual: `hackaton`.

Este proyecto fue desarrollado en el contexto de **Hackatón Municipios a la VanguardIA - MinCiencia 2025** y corresponde a la solución presentada por el equipo de **Renca**, reconocida como propuesta ganadora del desafío.

## Problema que aborda

La elaboración de licitaciones públicas exige precisión técnica, revisión normativa, consistencia documental y capacidad de detectar errores antes de publicar. En la práctica, ese trabajo puede ser lento, repetitivo y propenso a omisiones, especialmente cuando se realiza bajo presión y con múltiples versiones de documentos.

## Solución propuesta

licitacionesIA funciona como un asistente que apoya a equipos municipales en la redacción y revisión de bases de licitación. La solución ayuda a identificar observaciones, proponer mejoras y estructurar información clave para procesos más rápidos, claros y transparentes.

## Qué resuelve

- apoya la elaboración de licitaciones con asistencia inteligente
- detecta errores, inconsistencias y oportunidades de mejora
- entrega observaciones en tiempo real sobre contenido documental
- contribuye a procesos más eficientes y comprensibles para la gestión pública

## Contexto del proyecto

Según la presentación del equipo de Renca, la propuesta permitió mostrar cómo la Inteligencia Artificial puede fortalecer la gestión local mediante un asistente que mejora calidad, velocidad y trazabilidad en la preparación de licitaciones. El resultado fue el reconocimiento nacional como municipio ganador del desafío.

## Arquitectura y stack

El proyecto está construido como una aplicación web en Django con flujos orientados a formularios, análisis asistido por LLM y generación de documentos de salida.

### Backend

- Django 5
- Python
- SQLite para desarrollo
- manejo de sesiones, autenticación y vistas protegidas

### Capacidades de IA y documentos

- integración con modelo de OpenAI mediante variable de entorno
- análisis de contenido de licitaciones con salida estructurada
- generación de documentos en PDF y DOCX
- procesamiento de archivos y contenido textual para revisión

### Flujo funcional observado

- ingreso de propósito o contexto del requerimiento
- construcción y revisión de información asociada a una licitación
- análisis automático de observaciones
- exportación de resultados para uso operativo

## Diferenciales

- Aterriza IA generativa a un problema público concreto, útil y entendible.
- No se queda en una demo conversacional: integra análisis, estructura documental y salida exportable.
- Tiene un relato muy fuerte para portafolio porque combina innovación pública, automatización documental y impacto institucional.

## Estado del proyecto

Prototipo funcional de hackatón con una propuesta clara de valor. Representa una base convincente para evolucionar hacia una herramienta interna de apoyo a equipos municipales o consultoría pública.

## Cómo ejecutarlo

```bash
git clone https://github.com/cabarcn/hackaton.git
cd hackaton
python -m venv .venv
```

En Windows:

```bash
.venv\Scripts\activate
```

En Linux o macOS:

```bash
source .venv/bin/activate
```

Instala dependencias:

```bash
pip install -r requirements.txt
```

Configura al menos las variables necesarias para Django y OpenAI en tu entorno o archivo `.env`, luego ejecuta:

```bash
python manage.py migrate
python manage.py runserver
```

## Posibles evoluciones

- versionado de documentos y trazabilidad de cambios
- validaciones normativas más específicas por tipo de licitación
- panel para equipos municipales y revisores
- almacenamiento histórico de observaciones y mejoras sugeridas

## Autor

Cristopher Abarca
