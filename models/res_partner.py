from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    followup_assessment_count = fields.Integer(
        string="Evaluaciones seguimiento",
        compute="_compute_followup_assessment_count",
    )

    def _compute_followup_assessment_count(self):
        grouped = self.env["cs.followup.assessment"].read_group(
            [("patient_id", "in", self.ids)],
            ["patient_id"],
            ["patient_id"],
        )
        counts = {item["patient_id"][0]: item["patient_id_count"] for item in grouped if item["patient_id"]}
        for rec in self:
            rec.followup_assessment_count = counts.get(rec.id, 0)

    def action_open_followup_assessments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Evaluaciones de seguimiento",
            "res_model": "cs.followup.assessment",
            "view_mode": "list,form",
            "domain": [("patient_id", "=", self.id)],
            "context": {
                "default_patient_id": self.id,
            },
        }
