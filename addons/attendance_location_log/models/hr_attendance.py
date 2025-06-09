from odoo import models, fields, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    checkin_latitude = fields.Float(string="Check-in Latitude")
    checkin_longitude = fields.Float(string="Check-in Longitude")

    checkin_map_url = fields.Char(
        string="Check-in Map URL",
        compute="_compute_checkin_map_url",
        store=True
    )

    customer = fields.Text(
        string="Tên Khách hàng"
    )

    distance_travelled = fields.Float(string="Quãng đường đã di chuyển (km)")
    sales_report_note = fields.Text(string="Nội dung báo cáo khách hàng")

    @api.depends('checkin_latitude', 'checkin_longitude')
    def _compute_checkin_map_url(self):
        for rec in self:
            if rec.checkin_latitude and rec.checkin_longitude:
                rec.checkin_map_url = f"https://www.google.com/maps?q={rec.checkin_latitude},{rec.checkin_longitude}"
            else:
                rec.checkin_map_url = ""
