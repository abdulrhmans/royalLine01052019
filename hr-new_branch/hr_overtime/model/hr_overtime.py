# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from datetime import timedelta,date
import math
from pytz import timezone,all_timezones
import time

class resource_calendar(models.Model):
    _inherit = "resource.calendar"

    overtime_off_days = fields.Float('Hour for Off Days Overtime')
    overtime_work_days = fields.Float('Hour for Work Days Overtime')


class hr_overtime(models.Model):
    _name = "hr.overtime"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Many2one('hr.employee','Employee',required=True,readonly=True,states={'draft': [('readonly', False)]},track_visibility='onchange')
    date = fields.Date('Date',required=True,readonly=True,states={'draft': [('readonly', False)]},track_visibility='onchange')
    start_datetime = fields.Datetime('Start Date',required=True,readonly=True,states={'draft': [('readonly', False)]},track_visibility='onchange')
    end_datetime = fields.Datetime('End Date',required=True,readonly=True,states={'draft': [('readonly', False)]},track_visibility='onchange')
    duration = fields.Float('Duration by hour',compute='calculate_overtime',readonly=True)
    overtime = fields.Float('Overtime by hour',compute='calculate_overtime',readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account',readonly=True, states={'draft': [('readonly', False)]},track_visibility='onchange')
    state = fields.Selection([('draft','Draft'),('cancel','Cancel'),('validate','Validate'),('done','Approved')],string='Status',default='draft',track_visibility='onchange')
    cost = fields.Float('Total Cost',compute='calculate_overtime',readonly=True)
    analytic_line_id = fields.Many2one('account.analytic.line',readonly=True,track_visibility='onchange')
    time_zone = fields.Selection('_tz_get', string='Timezone', required=True, default=lambda self: self.env.user.tz or 'UTC',track_visibility='onchange')
    
    @api.model
    def _tz_get(self):
        return [(x, x) for x in all_timezones]

    @api.one
    def get_local_utc(self, offset):
        hours = minutes = 0
        hours = offset[1:3]
        minutes = offset[3:5]
        return [int(hours),int(minutes)]
    
    
    @api.one
    @api.depends('start_datetime','end_datetime','date')
    def calculate_overtime(self):
        if (self.start_datetime and self.end_datetime) and (self.start_datetime > self.end_datetime):
            raise UserError(_('The start date must be anterior to the end date.'))
        # get number of hours
        if self.start_datetime and self.end_datetime:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            
            # Add 3-2 hours for time zone problem 
            from_dt_b = datetime.datetime.strptime(self.start_datetime, DATETIME_FORMAT)
            to_dt_b = datetime.datetime.strptime(self.end_datetime, DATETIME_FORMAT)
            
            my_local_timezone = timezone(self.time_zone)
            local_date = my_local_timezone.localize(from_dt_b)
            utcOffset = local_date.strftime('%z')
            hours , minutes = self.get_local_utc(utcOffset)[0]
            
            if utcOffset[0] == '+':
                from_dt = from_dt_b - timedelta(hours=hours,minutes=minutes)
                to_dt = to_dt_b - timedelta(hours=hours,minutes=minutes)
            elif utcOffset[0] == '-':
                from_dt = from_dt_b + timedelta(hours=hours,minutes=minutes)
                to_dt = to_dt_b + timedelta(hours=hours,minutes=minutes)
            else:
                from_dt = from_dt_b
                to_dt = to_dt_b
            
            timedelta_s = to_dt - from_dt
            self.duration = timedelta_s.days*24 + float(timedelta_s.seconds)/3600
            off_day = self._calculate_durations(from_dt,to_dt)
            ## just for overtime
            contract = self.name.contract_id
            work_overtiem = 0.0
            off_overtiem = 0.0
            cost_by_hour = 0.0
            if contract:
                cost_by_hour = contract.wage/30.4/8
                if contract.resource_calendar_id:
                    work_overtiem = contract.resource_calendar_id.overtime_work_days
                    off_overtiem = contract.resource_calendar_id.overtime_off_days
            ##
            
            over_time = 0.0
            res = off_day[0]
            for r in res:
                if r[1] == True:
                    over_time += r[0]*off_overtiem
                else:
                    over_time += r[0]*work_overtiem
                    
            self.overtime = over_time
            self.cost = over_time*cost_by_hour
        
    
    @api.one
    @api.model
    def _calculate_durations(self, from_dt ,to_dt):
        res = []
        employee = self.name
        date_1 = from_dt.date()
        date_2 = to_dt.date()
        contract_id = employee.contract_id
        if contract_id:
            if date_1 == date_2:
                is_off = self._off_day(from_dt, to_dt, contract_id, same_day=True)[0]
                timedelta = to_dt - from_dt
                duration = timedelta.days*24 + float(timedelta.seconds)/3600
                res.append((duration,is_off))
            else:
                res = self._off_day(from_dt, to_dt, contract_id, same_day=False)[0]
        
        return res
    
    
    @api.one
    @api.model
    def _off_day(self, date_time_1 ,date_time_2 ,contract ,same_day=True):
        day_of_week = {'Monday':0 ,'Tuesday':1 ,'Wednesday':2 ,'Thursday':3 ,'Friday':4 ,'Saturday':5 ,'Sunday':6 }
        if same_day:
            overtime_day = date_time_1.strftime("%A")
            if self.date:
                public_holiday = self.env['hr.public_holiday'].search([('date','<=', self.date+' 00:00:00'),
                                                                       ('date_to','>=', self.date+' 00:00:00')])
                if public_holiday:
                    return True
            
            if contract.resource_calendar_id:
                for day in contract.resource_calendar_id.attendance_ids:
                    if int(day.dayofweek) == day_of_week[overtime_day]:
                        return False
                return True
            else:
                return True
        else:
            res = []
            date_1 = date_time_1.date()
            date_2 = date_time_2.date()
            date_time_4 = datetime.datetime(date_2.year,date_2.month,date_2.day,0,0,0)
            duration_date_1 = date_time_4-date_time_1
            duration_date_2 = date_time_2-date_time_4
            
            duration_1 = duration_date_1.days*24 + float(duration_date_1.seconds)/3600
            duration_2 = duration_date_2.days*24 + float(duration_date_2.seconds)/3600
            
            du1_overtime_day = date_time_1.strftime("%A")
            
            found_day = False
            if contract.resource_calendar_id:
                for day in contract.resource_calendar_id.attendance_ids:
                    if int(day.dayofweek) == day_of_week[du1_overtime_day]:
                        found_day = True
                        res.append((duration_1,False))
                if not found_day:
                    res.append((duration_1,True))
            
            du2_overtime_day = date_time_2.strftime("%A")
            found_day = False
            if contract.resource_calendar_id:
                for day in contract.resource_calendar_id.attendance_ids:
                    if int(day.dayofweek) == day_of_week[du2_overtime_day]:
                        found_day = True
                        res.append((duration_2,False))
                if not found_day:
                    res.append((duration_2,True))
            return res
        
        
    @api.one
    @api.model
    def done_overtime(self):
        analytic_line_pool = self.env['account.analytic.line']
        timenow = time.strftime('%Y-%m-%d')
        tag = self.env.ref('hr_overtime.overtime_tag')
        general_account_id = False
        vals_1 = {'state':'done'}
        if self.name and self.analytic_account_id:
            rec_pro_id = self.env['ir.property'].search([('name','=','property_account_expense')])
            if rec_pro_id.value_reference:
                account_id =  (rec_pro_id.value_reference).split(',')[1]
                general_account_id = account_id
            if not general_account_id:
                raise UserError(_('There is no property_account_expense account defined '))
            vals = {
                    'name': _('Overtime for ')+ str(self.name.name),
                    'account_id': self.analytic_account_id.id,
                    'tag_ids' : [(6,0, [tag.id])],
                    'date': timenow,
                    'unit_amount': self.overtime,
                    'general_account_id': general_account_id,
                    'amount': self.cost*-1,
                    }
            res = analytic_line_pool.create(vals)
            vals_1['analytic_line_id'] = res.id
        self.write(vals_1)    
        return True
        
    @api.one
    @api.model
    def validate_overtime(self):
        self.sudo().write({'state':'validate', 'analytic_line_id':False})  
        
    @api.one
    @api.model
    def draft_overtime(self):
        self.write({'state':'draft', 'analytic_line_id':False})    
        
    @api.one
    @api.model
    def cancel_overtime(self):
        self.analytic_line_id.unlink()
        self.write({'state':'cancel', 'analytic_line_id':False})
        
    
     
class hr_payslip_inhe(models.Model): 
    _inherit = 'hr.payslip'
     
    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(hr_payslip_inhe,self).get_inputs(contracts, date_from, date_to)
        if self.employee_id and date_from and date_to:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            from_date = datetime.datetime.strptime(date_from, "%Y-%m-%d").date()
            to_date = datetime.datetime.strptime(date_to, "%Y-%m-%d").date()
            overtime_year = year = from_date.year
            month = from_date.month
            overtime_day = from_date.day
            overtime_month = month
            if overtime_month == 0:
                overtime_month = 12
                overtime_year = year-1
            
            overtime_from_date = datetime.datetime(overtime_year,overtime_month,overtime_day,0,0,0).strftime(DATETIME_FORMAT)
            overtime_to_date = datetime.datetime(to_date.year,to_date.month,to_date.day,23,59,59).strftime(DATETIME_FORMAT)
            overtime_ids = self.env['hr.overtime'].search([('state','=','done'),
                                                            ('name','=',self.employee_id.id),
                                                            ('start_datetime','<',overtime_to_date),
                                                            ('start_datetime','>=',overtime_from_date)])
            contract = self.employee_id.contract_id
            if overtime_ids:
                total_overtimes = 0.0
                total_overtimes_holiday = 0.0
                for rec in overtime_ids:
                    total_overtimes += rec.cost
                         
                if total_overtimes:
                    vals = {'name': 'Overtime', 'code': 'OTN', 'amount': total_overtimes, 'contract_id': contract.id}
                    res += [vals]
        return res