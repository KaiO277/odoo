from odoo import fields, models

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    checkin_map_url = fields.Char("Check-in Map", compute="_compute_checkin_map_url")

    def _compute_checkin_map_url(self):
        for rec in self:
            if hasattr(rec, 'checkin_latitude') and hasattr(rec, 'checkin_longitude') and rec.checkin_latitude and rec.checkin_longitude:
                lat = rec.checkin_latitude
                lon = rec.checkin_longitude
                rec.checkin_map_url = f"https://maps.google.com/?q={{lat}},{{lon}}"
            else:
                rec.checkin_map_url = ""
