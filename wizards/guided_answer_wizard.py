from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FollowupGuidedAnswerWizard(models.TransientModel):
    _name = "cs.followup.guided.answer.wizard"
    _description = "Followup Guided Answer Wizard"

    assessment_id = fields.Many2one("cs.followup.assessment", string="Evaluacion", required=True, readonly=True)
    current_answer_id = fields.Many2one(
        "cs.followup.assessment.answer",
        string="Campo actual",
        required=True,
        domain="[('assessment_id', '=', assessment_id)]",
    )
    question_label = fields.Char(string="Pregunta", compute="_compute_question_data")
    question_help = fields.Text(string="Ayuda", compute="_compute_question_data")
    answer_type = fields.Selection(
        [
            ("scale_1_10", "Escala 1-10"),
            ("boolean", "Si/No"),
            ("text_short", "Texto corto"),
            ("text_long", "Texto largo"),
            ("date", "Fecha"),
            ("selection", "Seleccion"),
        ],
        string="Tipo",
        compute="_compute_question_data",
    )
    position_label = fields.Char(string="Progreso", compute="_compute_position_label")
    options_hint = fields.Text(string="Opciones disponibles", compute="_compute_question_data")
    option_ids = fields.One2many(
        "cs.followup.guided.answer.wizard.option",
        "wizard_id",
        string="Opciones",
    )
    selected_option_id = fields.Many2one(
        "cs.followup.guided.answer.wizard.option",
        string="Valor seleccion",
        domain="[('wizard_id', '=', id)]",
    )

    value_text = fields.Char(string="Texto corto")
    value_text_long = fields.Text(string="Texto largo")
    value_number = fields.Float(string="Valor numerico")
    value_boolean = fields.Boolean(string="Valor si/no")
    value_date = fields.Date(string="Valor fecha")
    value_selection = fields.Char(string="Valor seleccion (legacy)")

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        assessment_id = vals.get("assessment_id")
        if not assessment_id:
            return vals

        assessment = self.env["cs.followup.assessment"].browse(assessment_id)
        ordered_answers = assessment._ordered_answers()
        if not ordered_answers:
            raise ValidationError(_("Esta evaluacion no tiene campos para rellenar."))

        first_answer = ordered_answers[0]
        vals["current_answer_id"] = first_answer.id
        vals.update(self._prepare_ui_values_from_answer(first_answer))
        return vals

    @api.model
    def _prepare_ui_values_from_answer(self, answer):
        vals = {
            "value_text": answer.value_text,
            "value_text_long": answer.value_text_long,
            "value_number": answer.value_number,
            "value_boolean": answer.value_boolean,
            "value_date": answer.value_date,
            "value_selection": answer.value_selection,
            "selected_option_id": False,
            "option_ids": [(5, 0, 0)],
        }
        if answer.answer_type == "selection":
            options = [line.strip() for line in (answer.template_field_id.option_values or "").splitlines() if line.strip()]
            vals["option_ids"] = [(5, 0, 0)] + [(0, 0, {"value": opt, "label": opt}) for opt in options]
        return vals

    @api.depends("current_answer_id")
    def _compute_question_data(self):
        for rec in self:
            answer = rec.current_answer_id
            rec.question_label = answer.template_field_id.name if answer else False
            rec.question_help = answer.template_field_id.help_text if answer else False
            rec.answer_type = answer.answer_type if answer else False
            rec.options_hint = answer.template_field_id.option_values if answer and answer.answer_type == "selection" else False

    @api.depends("current_answer_id", "assessment_id")
    def _compute_position_label(self):
        for rec in self:
            if not rec.assessment_id or not rec.current_answer_id:
                rec.position_label = False
                continue
            ordered = rec.assessment_id._ordered_answers()
            index = ordered.ids.index(rec.current_answer_id.id) + 1 if rec.current_answer_id.id in ordered.ids else 1
            rec.position_label = _("%(idx)s de %(total)s") % {"idx": index, "total": len(ordered)}

    @api.onchange("current_answer_id")
    def _onchange_current_answer_id_load_values(self):
        for rec in self:
            answer = rec.current_answer_id
            if not answer:
                continue
            if answer.answer_type == "selection":
                options = [line.strip() for line in (answer.template_field_id.option_values or "").splitlines() if line.strip()]
                rec.option_ids = [(5, 0, 0)] + [(0, 0, {"value": opt, "label": opt}) for opt in options]
                rec.selected_option_id = rec.option_ids.filtered(lambda opt: opt.value == answer.value_selection)[:1]
            else:
                rec.option_ids = [(5, 0, 0)]
                rec.selected_option_id = False
            rec.value_text = answer.value_text
            rec.value_text_long = answer.value_text_long
            rec.value_number = answer.value_number
            rec.value_boolean = answer.value_boolean
            rec.value_date = answer.value_date
            rec.value_selection = answer.value_selection

    def _write_current_answer_value(self):
        self.ensure_one()
        answer = self.current_answer_id
        vals = {
            "value_text": False,
            "value_text_long": False,
            "value_number": 0.0,
            "value_boolean": False,
            "value_date": False,
            "value_selection": False,
        }

        if answer.answer_type == "text_short":
            vals["value_text"] = self.value_text
        elif answer.answer_type == "text_long":
            vals["value_text_long"] = self.value_text_long
        elif answer.answer_type == "scale_1_10":
            vals["value_number"] = self.value_number
        elif answer.answer_type == "boolean":
            vals["value_boolean"] = self.value_boolean
        elif answer.answer_type == "date":
            vals["value_date"] = self.value_date
        elif answer.answer_type == "selection":
            vals["value_selection"] = self.selected_option_id.value or False

        answer.write(vals)

    def _move(self, direction):
        self.ensure_one()
        self._write_current_answer_value()
        ordered = self.assessment_id._ordered_answers()
        ids = ordered.ids
        if self.current_answer_id.id not in ids:
            return {"type": "ir.actions.act_window_close"}
        index = ids.index(self.current_answer_id.id)
        new_index = index + direction
        if new_index < 0 or new_index >= len(ids):
            return {"type": "ir.actions.act_window_close"}
        self.current_answer_id = ordered[new_index].id
        self._onchange_current_answer_id_load_values()
        return {
            "type": "ir.actions.act_window",
            "name": "Rellenado guiado",
            "res_model": "cs.followup.guided.answer.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_previous(self):
        return self._move(-1)

    def action_next(self):
        return self._move(1)

    def action_save_and_close(self):
        self.ensure_one()
        self._write_current_answer_value()
        return {"type": "ir.actions.act_window_close"}


class FollowupGuidedAnswerWizardOption(models.TransientModel):
    _name = "cs.followup.guided.answer.wizard.option"
    _description = "Followup Guided Answer Wizard Option"

    wizard_id = fields.Many2one("cs.followup.guided.answer.wizard", required=True, ondelete="cascade")
    label = fields.Char(string="Etiqueta", required=True)
    value = fields.Char(string="Valor", required=True)
