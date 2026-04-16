# CS Patient Followup Forms (`cs_patient_followup_forms`)

Módulo Odoo 19 para gestión integral de plantillas de seguimiento clínico personalizables y evaluaciones de pacientes.

## Descripción

Este módulo permite a los centros sanitarios crear plantillas de evaluación ajustadas a sus necesidades específicas, con soporte para múltiples tipos de campos (escala 1-10, sí/no, texto corto/largo, fechas, selecciones) y una interfaz de relleno guiada paso a paso.

## Características principales

### Gestión de Plantillas
- Creación de plantillas reutilizables con secciones organizadas
- Campos dinámicos con tipos soportados:
  - Escala 1-10
  - Sí/No (booleano)
  - Texto corto
  - Texto largo
  - Fecha
  - Selección (con opciones predefinidas)
- Validación y publicación de plantillas
- Opción de duplicar plantillas existentes

### Evaluaciones de Pacientes
- Evaluaciones asociadas a pacientes y profesionales
- Estados: Borrador, Completada, Archivada
- Relleno manual o mediante wizard guiado
- Auto-completado de campos según plantilla seleccionada
- Validación de campos requeridos al completar

### Wizard de Relleno Guiado
- Interfaz paso a paso para rellenar evaluaciones
- Pregunta por pregunta con navegación inteligente
- Botones "Anterior" y "Siguiente" deshabilitados en límites (primera/última pregunta)
- Visualización de ayuda y opciones disponibles
- Guardado automático de respuestas durante navegación

### Integración con Contactos
- Smart button en formulario de contacto para ver evaluaciones del paciente
- Vista rápida de evaluaciones asociadas

## Seguridad y Roles

### Grupos de Acceso
- **Followup Admin**: Acceso completo a plantillas y evaluaciones
- **Followup Clinician**: Crear y rellenar evaluaciones, ver plantillas
- **Followup Readonly**: Lectura de plantillas y evaluaciones

### Control de Acceso Multiempresa
- Registros limitados por empresa del usuario
- Seguridad integrada en modelo de datos

## Estructura del Módulo

```
cs_patient_followup_forms/
├── models/
│   ├── followup_template.py      # Plantillas, secciones y campos
│   ├── followup_assessment.py    # Evaluaciones y respuestas
│   └── res_partner.py            # Extensión de contactos
├── views/
│   ├── followup_template_views.xml      # Vistas de plantillas
│   ├── followup_assessment_views.xml    # Vistas de evaluaciones
│   ├── res_partner_views.xml            # Extensión de contactos
│   └── menu_views.xml                   # Menú principal
├── wizards/
│   ├── add_field_wizard.py              # Wizard para agregar campos
│   ├── add_field_wizard_views.xml
│   ├── guided_answer_wizard.py          # Wizard de relleno guiado
│   └── guided_answer_wizard_views.xml
├── security/
│   ├── security.xml             # Definición de grupos
│   └── ir.model.access.csv      # Permisos por modelo
└── __manifest__.py              # Metadatos del módulo
```

## Uso

### Crear una Plantilla
1. Ir a Seguimiento de Pacientes > Plantillas
2. Crear nueva plantilla
3. Agregar secciones según sea necesario
4. Usar botón "Nuevo campo" para agregar campos tipados
5. Configurar opciones según el tipo de campo
6. Publicar la plantilla

### Rellenar una Evaluación
1. Ir a Seguimiento de Pacientes > Evaluaciones
2. Crear nueva evaluación
3. Seleccionar paciente y plantilla
4. Opción A: Rellenar manualmente los campos
5. Opción B: Usar "Rellenado guiado" para wizard paso a paso
6. Marcar como completada o guardar como borrador

### Ver Evaluaciones de un Paciente
1. Abrir formulario de contacto del paciente
2. Hacer clic en botón inteligente "Evaluaciones"
3. Ver historial de evaluaciones realizadas

## Tipos de Campos Soportados

| Tipo | Rango/Opciones | Validación | Uso |
|------|----------------|-----------|-----|
| Escala 1-10 | 1 a 10 | Número entero | Valoraciones de síntomas, dolor, etc. |
| Sí/No | Booleano | N/A | Preguntas binarias |
| Texto corto | Libre | N/A | Respuestas breves |
| Texto largo | Libre | N/A | Observaciones detalladas |
| Fecha | ISO 8601 | Fecha válida | Registros de eventos |
| Selección | Opciones predefinidas | Una opción requerida | Diagnósticos, estados, categorías |

## Dependencias

- `base` (Odoo Core)
- `contacts` (res.partner)

## Versión

- Versión: 1.0.0
- Compatible con: Odoo 19.0+

## Autor

Centro Sanitario

## Licencia

Propietario - Centro Sanitario
