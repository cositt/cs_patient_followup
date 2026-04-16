from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FollowupAddFieldWizard(models.TransientModel):
    _name = "cs.followup.add.field.wizard"
    _description = "Followup Add Field Wizard"

    template_id = fields.Many2one("cs.followup.template", string="Plantilla", required=True, readonly=True)
    section_id = fields.Many2one(
        "cs.followup.template.section",
        string="Seccion",
        required=True,
        domain="[('template_id', '=', template_id)]",
    )
    sequence = fields.Integer(string="Orden", default=1)
    name = fields.Char(string="Etiqueta", required=True)
    field_type = fields.Selection(
        [
            ("scale_1_10", "Escala 1-10"),
            ("boolean", "Si/No"),
            ("text_short", "Texto corto"),
            ("text_long", "Texto largo"),
            ("date", "Fecha"),
            ("selection", "Seleccion"),
            ("image", "Imagen"),
        ],
        string="Tipo",
        required=True,
        default="text_short",
    )
    required = fields.Boolean(string="Obligatorio", default=False)
    code = fields.Char(string="Codigo tecnico")
    help_text = fields.Text(string="Ayuda")
    option_values = fields.Text(
        string="Opciones (una por linea, varias permitidas)",
        help="Solo aplica en tipo Seleccion. Escribe una opcion por linea.",
    )
    min_value = fields.Float(string="Valor minimo")
    max_value = fields.Float(string="Valor maximo")

    @api.onchange("section_id")
    def _onchange_section_id_set_sequence(self):
        for rec in self:
            if not rec.section_id:
                continue
            field_model = self.env["cs.followup.template.field"]
            last_field = field_model.search(
                [("section_id", "=", rec.section_id.id)],
                order="sequence desc, id desc",
                limit=1,
            )
            rec.sequence = (last_field.sequence or 0) + 1 if last_field else 1

    def action_create_field(self):
        self.ensure_one()
        if self.field_type == "selection":
            options = [line.strip() for line in (self.option_values or "").splitlines() if line.strip()]
            if not options:
                raise ValidationError(
                    _(
                        "Este campo es de tipo Seleccion y necesita opciones.\n"
                        "Escribe una opcion por linea."
                    )
                )

        self.env["cs.followup.template.field"].create(
            {
                "section_id": self.section_id.id,
                "name": self.name,
                "field_type": self.field_type,
                "required": self.required,
                "code": self.code,
                "help_text": self.help_text,
                "option_values": self.option_values,
                "min_value": self.min_value,
                "max_value": self.max_value,
                "sequence": self.sequence,
            }
        )
        return {"type": "ir.actions.act_window_close"}
