# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BaseScheduleNotification(models.Model):
    _name = 'base.schedule.notification'
    
    name = fields.Char('Name', required=True)
    action_id = fields.Many2one('ir.cron','Scheduled Action')
    partner_ids = fields.Many2many('res.partner', string='Recipients')
    type = fields.Selection([('Email', 'Email'), ('SMS','SMS'), ('Push Notification','Push Notification')], string="Type", default='Email', required=True)
    active = fields.Boolean('Active', default=True)
    days = fields.Integer('Period (Days)')
    note = fields.Text('Note')
    
    @api.multi
    def toggle_active(self):
        super(BaseScheduleNotification, self).toggle_active()
        for record in self:
            if record.action_id:
                record.action_id.toggle_active()
        
class IrCron(models.Model):
    _inherit = 'ir.cron'
    
    view_on_notification = fields.Boolean('View On Notifications')