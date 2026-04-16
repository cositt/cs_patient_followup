from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FollowupTemplate(models.Model):
    _name = "cs.followup.template"
    _description = "Followup Template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Nombre", required=True, tracking=True)
    description = fields.Text(string="Descripcion")
    active = fields.Boolean(default=True, index=True)
    state = fields.Selection(
        [("draft", "Borrador"), ("published", "Publicada"), ("archived", "Archivada")],
        string="Estado",
        default="draft",
        required=True,
        index=True,
        tracking=True,
    )
    version = fields.Integer(string="Version", default=1, required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Compania",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    section_ids = fields.One2many("cs.followup.template.section", "template_id", string="Secciones")
    template_field_ids = fields.One2many(
        "cs.followup.template.field",
        "template_id",
        string="Listado de campos",
    )
    field_count = fields.Integer(string="Campos", compute="_compute_field_count")

    @api.depends("section_ids.field_ids")
    def _compute_field_count(self):
        for rec in self:
            rec.field_count = sum(len(section.field_ids) for section in rec.section_ids)

    def action_publish(self):
        for rec in self:
            if not rec.field_count:
                raise ValidationError(_("No puedes publicar una plantilla sin campos."))
            rec.state = "published"

    def action_set_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_archive(self):
        for rec in self:
            rec.state = "archived"

    def action_open_fields(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Campos de plantilla",
            "res_model": "cs.followup.template.field",
            "view_mode": "list,form",
            "domain": [("template_id", "=", self.id)],
            "context": {
                "default_template_id": self.id,
            },
        }

    def action_open_add_field_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Nuevo campo",
            "res_model": "cs.followup.add.field.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_template_id": self.id,
            },
        }


class FollowupTemplateSection(models.Model):
    _name = "cs.followup.template.section"
    _description = "Followup Template Section"
    _order = "template_id, sequence, id"

    template_id = fields.Many2one("cs.followup.template", string="Plantilla", required=True, ondelete="cascade", index=True)
    name = fields.Char(string="Titulo de seccion", required=True)
    sequence = fields.Integer(string="Orden", default=1)
    field_ids = fields.One2many("cs.followup.template.field", "section_id", string="Campos")
    company_id = fields.Many2one(related="template_id.company_id", store=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("sequence"):
                continue
            template_id = vals.get("template_id")
            if not template_id:
                vals["sequence"] = 1
                continue
            last_section = self.search(
                [("template_id", "=", template_id)],
                order="sequence desc, id desc",
                limit=1,
            )
            vals["sequence"] = (last_section.sequence or 0) + 1 if last_section else 1
        return super().create(vals_list)


class FollowupTemplateField(models.Model):
    _name = "cs.followup.template.field"
    _description = "Followup Template Field"
    _order = "section_id, sequence, id"

    field_type = fields.Selection(
        [
            ("scale_1_10", "Escala 1-10"),
            ("boolean", "Si/No"),
            ("text_short", "Texto corto"),
            ("text_long", "Texto largo"),
            ("date", "Fecha"),
            ("selection", "Seleccion"),
        ],
        string="Tipo",
        required=True,
        default="text_short",
        index=True,
    )
    section_id = fields.Many2one("cs.followup.template.section", string="Seccion", required=True, ondelete="cascade", index=True)
    template_id = fields.Many2one(related="section_id.template_id", store=True, index=True)
    name = fields.Char(string="Etiqueta", required=True)
    code = fields.Char(string="Codigo tecnico", index=True)
    help_text = fields.Text(string="Ayuda")
    required = fields.Boolean(string="Obligatorio", default=False)
    sequence = fields.Integer(string="Orden", default=1)
    option_values = fields.Text(
        string="Opciones",
        help="Una opcion por linea. Solo aplica en tipo Seleccion.",
    )
    min_value = fields.Float(string="Valor minimo")
    max_value = fields.Float(string="Valor maximo")
    company_id = fields.Many2one(related="template_id.company_id", store=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("sequence"):
                continue
            section_id = vals.get("section_id")
            if not section_id:
                vals["sequence"] = 1
                continue
            last_field = self.search(
                [("section_id", "=", section_id)],
                order="sequence desc, id desc",
                limit=1,
            )
            vals["sequence"] = (last_field.sequence or 0) + 1 if last_field else 1
        return super().create(vals_list)

    @api.constrains("field_type", "option_values")
    def _check_selection_options(self):
        for rec in self:
            if rec.field_type != "selection":
                continue
            options = [line.strip() for line in (rec.option_values or "").splitlines() if line.strip()]
            if not options:
                raise ValidationError(
                    _(
                        "El campo '%(field)s' es de tipo Seleccion y debe tener opciones.\n"
                        "Define una opcion por linea en el campo 'Opciones'."
                    )
                    % {"field": rec.name}
                )
