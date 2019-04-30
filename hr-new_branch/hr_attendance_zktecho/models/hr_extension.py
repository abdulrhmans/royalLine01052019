# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models,_
from odoo.exceptions import ValidationError,UserError


class HrAttendance(models.Model):
    
    _name = 'hr.attendance'
    _inherit = ['hr.attendance','mail.thread']
    
    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    name = fields.Datetime('Datetime')
    day = fields.Date("Day")
    is_missing = fields.Boolean('Missing', default=False)
    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True, ondelete='cascade', index=True, track_visibility='onchange')
    check_in = fields.Datetime(string="Check In", default=fields.Datetime.now, required=True, track_visibility='onchange')
    check_out = fields.Datetime(string="Check Out", track_visibility='onchange')


class hrDraftAttendance(models.Model):

    _name = 'hr.draft.attendance'
    _inherit = ['mail.thread']
    _order = 'name desc'
    
    name = fields.Datetime('Datetime', required=False,track_visibility='onchange')
    date = fields.Date('Date', required=False,track_visibility='onchange')
    day_name = fields.Char('Day',track_visibility='onchange')
    attendance_status = fields.Selection([('sign_in', 'Sign In'), ('sign_out', 'Sign Out'), ('sign_none', 'None')], 'Attendance State', required=True,track_visibility='onchange')
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',track_visibility='onchange')
    lock_attendance = fields.Boolean('Lock Attendance',track_visibility='onchange')
    biometric_attendance_id = fields.Integer(string='Biometric Attendance ID',track_visibility='onchange')
    is_missing = fields.Boolean('Missing', default=False,track_visibility='onchange')
    moved = fields.Boolean(default=False)
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.moved == True:
                raise UserError(_("You can`t delete Moved Attendance"))
        return super(hrDraftAttendance, self).unlink()
    
class Employee(models.Model):
    
    _inherit = 'hr.employee'
    
    is_shift = fields.Boolean("Shifted Employee")
    attendance_devices = fields.One2many(comodel_name='employee.attendance.devices', inverse_name='name', string='Attendance')
    

class EmployeeAttendanceDevices(models.Model):
    
    _name = 'employee.attendance.devices'
    
    name = fields.Many2one(comodel_name='hr.employee', string='Employee', readonly=True)
    attendance_id = fields.Char("Attendance ID", required=True)
    device_id = fields.Many2one(comodel_name='biomteric.device.info', string='Biometric Device', required=True, ondelete='restrict')
    
    @api.multi
    @api.constrains('attendance_id', 'device_id')
    def _check_unique_constraint(self):
        self.ensure_one()
        record = self.search([('attendance_id', '=', self.attendance_id), ('device_id', '=', self.device_id.id)])
        if len(record) > 1:
            raise ValidationError('Employee with Id ('+ str(self.attendance_id)+') exists on Device ('+ str(self.device_id.name)+') !')
        record = self.search([('name', '=', self.name.id), ('device_id', '=', self.device_id.id)])
        if len(record) > 1:
            raise ValidationError('Configuration for Device ('+ str(self.device_id.name)+') of Employee  ('+ str(self.name.name)+') already exists!')
