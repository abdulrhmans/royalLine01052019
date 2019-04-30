# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime,timedelta



class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'
    
    refund_id = fields.Many2one('hr.payslip', 'Refunded Slip', readonly=True)
    number_of_houres = fields.Float('Number Of Hours', help="Scheduled working hours in the period")
    actuall_days = fields.Float('Number Of Days', help="Scheduled working days in period")

    @api.multi
    def refund_sheet(self):
        for payslip in self:
            number = self.env['ir.sequence'].next_by_code('salary.slip')
            copied_payslip = payslip.copy({'credit_note': True, 'name': _('Refund: ') + payslip.name, 'refund_id':payslip.id, 'number': number})
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
        res = super(HrPayslip,self).onchange_employee()
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
        '''
            This function will get the number of days,hours that employees should works in period.
            Depends on working schedule in contract page.
        '''
        day_of_week = {'Monday':'0' ,'Tuesday':'1' ,'Wednesday':'2' ,'Thursday':'3' ,'Friday':'4' ,'Saturday':'5' ,'Sunday':'6' }
        hours_of_days = {}
        number_of_hours = number_of_days = 0.0
        res = {'hours': 0.0, 'days': 0.0}
        date_from = datetime.strptime(_from, '%Y-%m-%d')
        date_to = datetime.strptime(_to, '%Y-%m-%d')
        if employee_id:
            contract = employee_id.contract_id
            if contract.resource_calendar_id:
                break_duration = 0.0
                if hasattr(contract.resource_calendar_id, 'break_duration'):
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
    
    