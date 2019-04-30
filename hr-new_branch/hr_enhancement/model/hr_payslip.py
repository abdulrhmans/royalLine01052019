# -*- coding: utf-8 -*-
from odoo import models, fields,_
from odoo import api, tools
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from datetime import time as datetime_time


class hr_payslip_employees(models.TransientModel):
    _inherit ='hr.payslip.employees'
    
    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            slip_data.update({
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': False,
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
            })
            payslip = self.env['hr.payslip'].create(slip_data)
            payslip.onchange_employee()
            payslips += payslip
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}

class hr_payslip(models.Model):
    _inherit = 'hr.payslip'
    
    refund_id = fields.Many2one('hr.payslip','Refunded Slip',readonly=True)
    input_line_ids = fields.One2many('hr.payslip.input', 'payslip_id', string='Payslip Inputs', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    number_of_houres = fields.Float('Number Of Hours')
    actuall_days = fields.Float('Actual Working Days In Period', help="actual days between periods to work")

    @api.multi
    def refund_sheet(self):
        for payslip in self:
            copied_payslip = payslip.copy({'credit_note': True, 'name': _('Refund: ') + payslip.name, 'refund_id':payslip.id})
            copied_payslip.action_payslip_done()
        formview_ref = self.env.ref('hr_payroll.view_hr_payslip_form', False)
        treeview_ref = self.env.ref('hr_payroll.view_hr_payslip_tree', False)
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'), (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }
    
    @api.onchange('employee_id', 'date_from','date_to')
    def onchange_employee(self):
        res = super(hr_payslip,self).onchange_employee()
        if not res:
            res = {}
        if self.employee_id and self.contract_id and self.date_from and self.date_to:
            data = self.actuall_days_hours_to_work(self.employee_id, self.date_from, self.date_to)
            self.actuall_days = data['days']
            self.number_of_houres = data['hours']
            res['actuall_days'] = data['days']
            res['number_of_houres'] = data['hours']
        return res
    
    def actuall_days_hours_to_work(self, employee_id ,_from, _to):
        day_of_week = {'Monday':'0' ,'Tuesday':'1' ,'Wednesday':'2' ,'Thursday':'3' ,'Friday':'4' ,'Saturday':'5' ,'Sunday':'6' }
        hours_of_days = {}
        number_of_hours = number_of_days = 0.0
        res = {'hours': 0.0, 'days': 0.0}
        date_from = datetime.strptime(_from, '%Y-%m-%d')
        date_to = datetime.strptime(_to, '%Y-%m-%d')
        if employee_id:
            contract = employee_id.contract_id
            if contract.resource_calendar_id:
                break_duration = contract.resource_calendar_id.break_duration
                for day in contract.resource_calendar_id.attendance_ids:
                    if hours_of_days.get(str(day.dayofweek), False): 
                        hours_of_days[str(day.dayofweek)] +=  day.hour_to - day.hour_from - break_duration
                    else:
                        hours_of_days[str(day.dayofweek)] =  day.hour_to - day.hour_from - break_duration
                while date_from <= date_to: 
                    date_day = day_of_week[date_from.strftime('%A')]
                    if date_day in hours_of_days.keys():
                        number_of_days += 1
                        number_of_hours += hours_of_days[date_day]
                    date_from = date_from+timedelta(days=1)
        res['hours'] = number_of_hours
        res['days'] = number_of_days
        return res
    
    
    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), datetime_time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), datetime_time.max)

            # compute leave days
            leaves = {}
            day_leave_intervals = contract.employee_id.iter_leaves(day_from, day_to, calendar=contract.resource_calendar_id)
            break_duration = 0.0
            if hasattr(contract.resource_calendar_id, 'break_duration'):
                break_duration = contract.resource_calendar_id.break_duration
            for day_intervals in day_leave_intervals:
                for interval in day_intervals:
                    holiday = interval[2]['leaves'].holiday_id
                    current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                        'name': holiday.holiday_status_id.name,
                        'sequence': 5,
                        'code': holiday.holiday_status_id.name,
                        'number_of_days': 0.0,
                        'number_of_hours': 0.0,
                        'contract_id': contract.id,
                        'leave_type_id': holiday.holiday_status_id.id,
                    })
                    leave_time = ((interval[1] - interval[0]).seconds / 3600) - break_duration
                    current_leave_struct['number_of_hours'] += leave_time
                    work_hours = contract.employee_id.get_day_work_hours_count(interval[0].date(), calendar=contract.resource_calendar_id)
                    current_leave_struct['number_of_days'] += leave_time / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from, day_to, calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res
    
    def official_leave(self, employee, datetime_day):
        res = False
        contract = employee.contract_id
        if contract and contract.working_hours:
            day = datetime_day.strftime("%Y-%m-%d")
            holiday_ids = self.env['resource.calendar.leaves'].search([('calendar_id','=',contract.resource_calendar_id.id),
                                                                                     ('resource_id','=',employee.id),
                                                                                     ('date_from','<=',day),
                                                                                     ('date_to','>=',day)])
            if not holiday_ids:
                holiday_ids = self.env['resource.calendar.leaves'].search([('calendar_id','=',contract.resource_calendar_id.id),
                                                                                         ('resource_id','=',False),
                                                                                         ('date_from','<=',day),
                                                                                         ('date_to','>=',day)])
            if holiday_ids:
                res = 'new day'
        return res

    @api.multi
    def compute_sheet(self):
        unlink_lines_ids = []
        for payslip in self:
            for l in payslip.line_ids:
                if l.total == 0:
                    l.unlink()
            
            for line in payslip.details_by_salary_rule_category:
                if line.code == 'NET' and line.employee_id:
                    line.write({'name': 'Net for '+ (line.employee_id.name)})
                    
        return super(hr_payslip, self).compute_sheet()

    
class hr_payslip_worked_days(models.Model):
    _inherit = 'hr.payslip.worked_days'
    
    leave_type_id = fields.Many2one('hr.holidays.status','Leave Type')
    
class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"
    
    def get_day_work_hours_count(self, day_date, calendar=None):
        calendar = calendar or self.resource_calendar_id
        attendances = calendar._get_day_attendances(day_date, False, False)
        if not attendances:
            return 0
        return sum(float(i.hour_to) - float(i.hour_from) - calendar.break_duration for i in attendances)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
