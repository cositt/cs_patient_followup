from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FollowupAssessment(models.Model):
    _name = "cs.followup.assessment"
    _description = "Followup Assessment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "assessment_date desc, id desc"

    name = fields.Char(string="Referencia", compute="_compute_name", store=True)
    template_id = fields.Many2one(
        "cs.followup.template",
        string="Plantilla",
        required=True,
        domain=[("state", "=", "published")],
        index=True,
        tracking=True,
    )
    template_version = fields.Integer(string="Version plantilla", related="template_id.version", store=True)
    patient_id = fields.Many2one("res.partner", string="Paciente", required=True, index=True, tracking=True)
    clinician_id = fields.Many2one(
        "res.users",
        string="Profesional",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    assessment_date = fields.Date(string="Fecha", required=True, default=fields.Date.context_today, index=True, tracking=True)
    state = fields.Selection(
        [("draft", "Borrador"), ("done", "Completada"), ("cancelled", "Cancelada")],
        string="Estado",
        default="draft",
        required=True,
        index=True,
        tracking=True,
    )
    notes = fields.Text(string="Observaciones")
    answer_ids = fields.One2many("cs.followup.assessment.answer", "assessment_id", string="Respuestas")
    company_id = fields.Many2one(
        "res.company",
        string="Compania",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    def _prepare_answer_lines_from_template(self):
        self.ensure_one()
        template_fields = self.template_id.section_ids.mapped("field_ids").sorted(
            key=lambda f: (f.section_id.sequence, f.sequence, f.id)
        )
        return [(0, 0, {"template_field_id": template_field.id}) for template_field in template_fields]

    def _ordered_answers(self):
        self.ensure_one()
        return self.answer_ids.sorted(
            key=lambda a: (
                a.template_field_id.section_id.sequence,
                a.template_field_id.sequence,
                a.id,
            )
        )

    @api.onchange("template_id")
    def _onchange_template_id_fill_answers(self):
        for rec in self:
            rec.answer_ids = [(5, 0, 0)]
            if rec.template_id:
                rec.answer_ids = rec._prepare_answer_lines_from_template()

    @api.depends("patient_id", "assessment_date", "template_id")
    def _compute_name(self):
        for rec in self:
            patient = rec.patient_id.name or _("Paciente")
            template = rec.template_id.name or _("Plantilla")
            date = rec.assessment_date or fields.Date.context_today(rec)
            rec.name = f"{patient} - {template} ({date})"

    def action_mark_done(self):
        for rec in self:
            rec._validate_answers_for_completion()
            rec.state = "done"

    def action_set_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    def action_open_guided_wizard(self):
        self.ensure_one()
        wizard = self.env["cs.followup.guided.answer.wizard"].create(
            {
                "assessment_id": self.id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Rellenado guiado",
            "res_model": "cs.followup.guided.answer.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _validate_answers_for_completion(self):
        self.ensure_one()
        for answer in self.answer_ids:
            if answer.answer_type == "selection" and not answer.value_selection:
                raise ValidationError(
                    _(
                        "Debe informar una opcion para respuestas de tipo seleccion.\n"
                        "Campo: %(field)s"
                    )
                    % {"field": answer.template_field_id.name}
                )
            if answer.answer_type == "text_short" and not answer.value_text:
                raise ValidationError(
                    _(
                        "Debe informar un texto corto para este tipo de respuesta.\n"
                        "Campo: %(field)s"
                    )
                    % {"field": answer.template_field_id.name}
                )
            if answer.answer_type == "text_long" and not answer.value_text_long:
                raise ValidationError(
                    _(
                        "Debe informar un texto largo para este tipo de respuesta.\n"
                        "Campo: %(field)s"
                    )
                    % {"field": answer.template_field_id.name}
                )
            if answer.answer_type == "date" and not answer.value_date:
                raise ValidationError(
                    _(
                        "Debe informar una fecha para este tipo de respuesta.\n"
                        "Campo: %(field)s"
                    )
                    % {"field": answer.template_field_id.name}
                )
            if answer.answer_type == "scale_1_10" and (answer.value_number < 1 or answer.value_number > 10):
                raise ValidationError(
                    _(
                        "La escala debe estar entre 1 y 10.\n"
                        "Campo: %(field)s"
                    )
                    % {"field": answer.template_field_id.name}
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("template_id") and not vals.get("answer_ids"):
                template = self.env["cs.followup.template"].browse(vals["template_id"])
                template_fields = template.section_ids.mapped("field_ids").sorted(
                    key=lambda f: (f.section_id.sequence, f.sequence, f.id)
                )
                vals["answer_ids"] = [(0, 0, {"template_field_id": template_field.id}) for template_field in template_fields]
        return super().create(vals_list)


class FollowupAssessmentAnswer(models.Model):
    _name = "cs.followup.assessment.answer"
    _description = "Followup Assessment Answer"
    _order = "assessment_id, id"

    assessment_id = fields.Many2one("cs.followup.assessment", string="Evaluacion", required=True, ondelete="cascade", index=True)
    template_id = fields.Many2one(related="assessment_id.template_id")
    template_field_id = fields.Many2one("cs.followup.template.field", string="Campo plantilla", required=True, index=True)
    answer_type = fields.Selection(
        [
            ("scale_1_10", "Escala 1-10"),
            ("boolean", "Si/No"),
            ("text_short", "Texto corto"),
            ("text_long", "Texto largo"),
            ("date", "Fecha"),
            ("selection", "Seleccion"),
        ],
        string="Tipo respuesta",
        compute="_compute_answer_type",
        store=True,
    )
    value_text = fields.Char(string="Texto corto")
    value_text_long = fields.Text(string="Texto largo")
    value_number = fields.Float(string="Valor numerico")
    value_boolean = fields.Boolean(string="Valor si/no")
    value_date = fields.Date(string="Valor fecha")
    value_selection = fields.Char(string="Valor seleccion")
    company_id = fields.Many2one(related="assessment_id.company_id", store=True, index=True)

    _sql_constraints = [
        (
            "assessment_field_unique",
            "unique(assessment_id, template_field_id)",
            "No se puede responder dos veces el mismo campo en una evaluacion.",
        ),
    ]

    @api.depends("template_field_id.field_type")
    def _compute_answer_type(self):
        for rec in self:
            rec.answer_type = rec.template_field_id.field_type

    @api.constrains("template_field_id", "assessment_id")
    def _check_field_belongs_to_template(self):
        for rec in self:
            if rec.template_field_id.template_id != rec.assessment_id.template_id:
                raise ValidationError(_("El campo seleccionado no pertenece a la plantilla de la evaluacion."))

    @api.constrains(
        "answer_type",
        "value_text",
        "value_text_long",
        "value_number",
        "value_boolean",
        "value_date",
        "value_selection",
    )
    def _check_value_by_type(self):
        for rec in self:
            # Permite guardar borradores incompletos; la validacion completa se ejecuta al marcar la evaluacion como completada.
            if rec.answer_type == "scale_1_10" and rec.value_number and (rec.value_number < 1 or rec.value_number > 10):
                raise ValidationError(_("La escala debe estar entre 1 y 10."))
