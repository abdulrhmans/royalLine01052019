# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta
import time
import calendar

class Employee(models.Model):
    _inherit = 'hr.employee'
    
    month_days = fields.Float('Monthly Days', default=0)
    year_days = fields.Float('Yearly Days', default=0)
    work_hour = fields.Float('Working Hours Per Day', default=8)
    dependent_lines = fields.One2many('hr.employee.dependent','employee_id','Dependent Information')
    iban = fields.Char('IBAN')
    bank_id = fields.Many2one('hr.bank', 'Bank')
    religion = fields.Selection([('islam','Islam'),('other','Other')])
    contract_id = fields.Many2one('hr.contract', 'Contract', compute='_compute_contract')
    branch_id = fields.Many2one('hr.bank.branch', 'Branch')
    
    @api.one
    def was_on_leave(self, employee_id, datetime_day, context=None):
        res = False
        day = datetime_day.strftime("%Y-%m-%d")
        holiday_ids = self.env['hr.holidays'].search([('state','=','validate'),('employee_id','=',employee_id),('type','=','remove'),
                                                                    ('date_from','<=',day),('date_to','>=',day)])
        if holiday_ids:
            res = holiday_ids[0].holiday_status_id
            return True
        return res
    
    @api.one
    def _compute_contract(self):
        self.contract_id = self.get_contract()[0]
        
    @api.one
    def get_paid_days(self, worked_days):
        paid_days = 0.0
        unpaid_days = 0.0
        for l in worked_days.dict:
            line = worked_days.dict[l]
            if line.leave_type_id:
                if line.leave_type_id.unpaid:
                    unpaid_days += line.number_of_days
                else:
                    paid_days += line.number_of_days
            else:
                paid_days += line.number_of_days
            
        return paid_days
    
    @api.one
    def get_sick_days(self, date_from, date_to):
        date1 = datetime.strptime(date_from, "%Y-%m-%d").date()
        date1 = datetime.strptime(str(date1.year)+'-'+'01-01', "%Y-%m-%d").date()
        date2 = datetime.strptime(date_to, "%Y-%m-%d").date()
        sum = 0
        while date1 <= date2:
            was = self.was_on_leave(self.id, date1)
            if was[0]:
                sum += 1
            date1 = date1 + timedelta(days=1)
        return sum 
    
    @api.one
    def get_contract(self,date_from=None, date_to=None):
        if not date_from:
            date_from = fields.Date.to_string(datetime.today())
        if not date_to:
            date_to = fields.Date.to_string(datetime.today())
            
#         clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
#         # OR if it starts between the given dates
#         clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
#         # OR if it starts before the date_from and finish after the date_end (or never finish)
#         clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
#         clause_final = [('employee_id', '=', self.id), ('state', '=', 'open'), '|', '|'] + clause_1 + clause_2 + clause_3
#         return self.env['hr.contract'].search(clause_final).ids
    
        contract_obj = self.env['hr.contract']
        clause_final =  [('employee_id', '=', self.id),('date_start','<=', date_from),'|',('date_end', '=', False),('date_end','>=', date_to)]
        contract_ids = contract_obj.search(clause_final)
        if contract_ids:
            return contract_ids
         
        clause_final =  [('employee_id', '=', self.id),('date_start','<=', date_from),('date_end','<', date_to)]
        contract_ids = contract_obj.search(clause_final)
        if contract_ids:
            return contract_ids
    
    
    @api.one
    def actuall_days_hours_to_work(self, contract_id ,_from=False, _to=False, date=False):
        day_of_week = {'Monday':'0' ,'Tuesday':'1' ,'Wednesday':'2' ,'Thursday':'3' ,'Friday':'4' ,'Saturday':'5' ,'Sunday':'6' }
        hours_of_days = {}
        number_of_hours = 0.0
        number_of_days = 0.0
        res = {'hours': 0.0, 'days': 0.0}
        
        if not _from and not _to:
            dates = self.get_date_ranges(date)[0]
            date_from = datetime.strptime(dates[0], '%Y-%m-%d')
            date_to = datetime.strptime(dates[1], '%Y-%m-%d')
        else:
            date_from = datetime.strptime(_from, '%Y-%m-%d')
            date_to = datetime.strptime(_to, '%Y-%m-%d')
            
        if employee_id and contract_id:
            contract = contract_id
            if contract.resource_calendar_id:
                for day in contract.resource_calendar_id.attendance_ids:
                    if hours_of_days.has_key(str(day.dayofweek)): 
                        hours_of_days[str(day.dayofweek)] +=  day.hour_to - day.hour_from - 1
                    else:
                        hours_of_days[str(day.dayofweek)] =  day.hour_to - day.hour_from - 1
                while date_from <= date_to: 
                    date_day = day_of_week[date_from.strftime('%A')]
                    if date_day in hours_of_days.keys():
                        number_of_days += 1
                        number_of_hours += hours_of_days[date_day]
                    date_from = date_from+timedelta(days=1)
                    
        res['hours'] = number_of_hours
        res['days'] = number_of_days
        return res
    
    @api.one
    def get_date_ranges(self, date):
        dates = []
        date = datetime.strptime(date, '%Y-%m-%d')
        range = calendar.monthrange(date.year,date.month)
        dates.append(str(date.year)+'-'+str(date.month)+'-01')
        dates.append(str(date.year)+'-'+str(date.month)+'-'+str(range[1]))
        return dates
    
class hr_dependent(models.Model):
    _name = "hr.employee.dependent"
    
    employee_id = fields.Many2one('hr.employee')
    name = fields.Char('Name')
    relative_type = fields.Selection([('father','Father'),
                                      ('mother','Mother'),
                                      ('brother','Brother'),
                                      ('sister','Sister'),
                                      ('husband','Husband'),
                                      ('wife','Wife'),
                                      ('daughter','Daughter'),
                                      ('son','Son')], 
                                      string='Type Of Relative')
    birthdate = fields.Date('Birth Date')
    ident_number = fields.Char('Ident Number')
    age = fields.Float('Age', compute="_calc_age", precision_digits=2)
    health_amount = fields.Float('Health Amount')
    
    @api.one
    def _calc_age(self):
        ''' This function will automatically calculates the age of relative.'''
        years = 0.0
        if self.birthdate:
            start = datetime.strptime(self.birthdate, DEFAULT_SERVER_DATE_FORMAT)
            end = datetime.strptime(time.strftime(DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT)
            delta = end - start
            years = (delta.days / 365.0)
        self.age = years
        
        
        
        