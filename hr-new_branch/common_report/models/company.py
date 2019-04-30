# -*- encoding: utf-8 -*-
from odoo import fields,models, api

class Company(models.Model):
    _inherit = 'res.company'
    
    external_report_layout = fields.Selection([
        ('background', 'Background'),
        ('without_background', 'Background Without Image'),
        ('boxed', 'Boxed'),
        ('clean', 'Clean'),
        ('standard', 'Standard'),
    ], string='Document Template')
    
    
    custom_logo = fields.Binary("Report Logo")

class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'
    
    @api.multi
    def edit_external_header(self):
        if self.external_report_layout == 'without_background':
            return self._prepare_report_view_action('common_report.external_layout_' + self.external_report_layout)
        return self._prepare_report_view_action('web.external_layout_' + self.external_report_layout)
    