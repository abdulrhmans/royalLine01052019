# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
import math
from odoo import models, fields, api, _
from odoo.exceptions import UserError,Warning
import time
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT



class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    eosb_id = fields.Many2one('hr.eosb.calac','EOSB',help='EOSB Record', readonly=True)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    @api.multi
    def open_eosb(self):
        action = self.env.ref('hr_eosb.action_eos_calc_action').read()[0]
        action['domain'] = [('employee_id.user_id','=',self.env.user.id)]
        return action
        
        

class Contract(models.Model):
    _inherit = 'hr.contract'
    
    has_eosb = fields.Boolean('Eligible for EOSB', help='If enabled, you can calculate EOSB for this contract', default=True)
    appeared_in_eosb = fields.Boolean('Appeared in BOSB',copy=False)
    out_state = fields.Selection([('term', 'Termination'), ('resign', 'Resignation'), ], 'End of service Status',related='term_reason_id.out_state',readonly=True,store=True)
    term_reason_id = fields.Many2one('hr.eosb.reason',string='End Employment Reason')
    work_duration = fields.Float('Work Duration', digits=(12, 11), compute="_working_duration")
    work_duration_now = fields.Float('Work Duration (Untill Now)', digits=(12, 11), compute="_working_duration")
    work_duration_char = fields.Char('Work Duration', compute="_working_duration")
    work_duration_now_char = fields.Char('Work Duration (Untill Now)', compute="_working_duration")
    contract_type= fields.Selection([('unlimited','Unlimited'),('limited','Limited')],default='unlimited',string="Contract type",required=True)
    
    @api.constrains('term_reason_id')
    def check_term_reason(self):
        for rec in self.filtered(lambda x:x.term_reason_id):
            if rec.term_reason_id.for_female and rec.employee_id.gender != 'female':
                raise UserError("""This reason is applicable for Females only""")
            
    @api.one
    def _working_duration(self):
        total_years = 0.0
        total_years_now = 0.0
        if self.date_start and self.date_end:
            start = datetime.strptime(self.date_start, '%Y-%m-%d')
            end = datetime.strptime(self.date_end, '%Y-%m-%d')+timedelta(days=1)
            duration = relativedelta(end, start)
            years = duration.years
            total_months = duration.months
            total_days = duration.days
            self.work_duration_char = '%d years, %d months and %d days'%(years,total_months,total_days)
            months_to_years = 0.0
            days_to_years = 0.0
            if calendar.isleap(end.year):
                number_of_days_for_last_year = 366.0
            else:
                number_of_days_for_last_year = 365.0
                
            if total_months > 0:
                months_to_years = total_months / 12.0
                
            if total_days > 0:
                days_to_years = total_days / number_of_days_for_last_year
            
            total_years = years + months_to_years + days_to_years
            
        if self.date_start:
            start = datetime.strptime(self.date_start, '%Y-%m-%d')
            end_now = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')+timedelta(days=1)
            duration_now = relativedelta(end_now, start)
            years_now = duration_now.years
            total_months_now = duration_now.months
            total_days_now = duration_now.days
            self.work_duration_now_char = '%d years, %d months and %d days'%(years_now,total_months_now,total_days_now)
            months_to_years_now = 0.0
            days_to_years_now = 0.0
            if calendar.isleap(end_now.year):
                number_of_days_for_last_year = 366.0
            else:
                number_of_days_for_last_year = 365.0
                
            if total_months_now > 0:
                months_to_years_now = total_months_now / 12.0
                
            if total_days_now > 0:
                days_to_years_now = total_days_now / number_of_days_for_last_year
                 
            total_years_now = years_now + months_to_years_now + days_to_years_now
            
        self.work_duration = total_years
        self.work_duration_now = total_years_now

 
class EOSB(models.Model):
    """"End Of Service Benefits Calculations"""
    _name = 'hr.eosb.calac'
    _description = "EOSB"
    _inherit = ['mail.thread']
    
    name = fields.Char('Name', compute='_compute_name')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True , domain=lambda self : self.get_employee_domian())
    contract_id = fields.Many2one('hr.contract', 'Contract',  required=True)
    date= fields.Date('Date',required=True)
    contract_start_date = fields.Date('Contract Start', related='contract_id.date_start',readonly=True)
    contract_end_date = fields.Date('Contract End', related='contract_id.date_end',readonly=True)
    work_duration_char = fields.Char('Contract Duration', related='contract_id.work_duration_char',readonly=True)
    eos_original_amount = fields.Float('EoS Benefits Original Amount',readonly=True)
    deductions_amount = fields.Float('Deductions Amount', compute='_compute_deductions_amount',store=True)
    balance = fields.Float('Net EoS Amount', compute='_compute_balance')
    state = fields.Selection([('draft', 'Draft'), ('cancel', 'Canceled'), ('approved', 'Approved')], 'Status', default='draft', track_visibility='onchange')
    deduction_lines = fields.One2many('hr.eos.deduction.line', 'eos_calc', 'Deductions')
    rule_id = fields.Many2one('hr.eosb.rule','Rule',readonly=True)
    contract_type = fields.Selection([('unlimited','Unlimited'),('limited','Limited')],string="Contract type",related='contract_id.contract_type',readonly=True)
    country_id = fields.Many2one('res.country',related='employee_id.country_id',readonly=True)
    note = fields.Html('Note',readonly=True)
    payment_method = fields.Selection([('payslip','On Payslip'),('receipt','Payment Receipt')],required=True)
    payslip_id = fields.Many2one('hr.payslip',string='Payslip')
    
    
    
    def get_employee_domian(self):
        contract_id = self.env['hr.contract'].search([('term_reason_id', '!=', False),
                                                      ('date_end', '!=', False),
                                                       ('appeared_in_eosb', '=', False)])
        return [('id', 'in', contract_id.mapped('employee_id.id'))]
        
    @api.one
    @api.depends('employee_id')
    def _compute_name(self):
        if self.employee_id and self.employee_id.name:
            self.name = self.employee_id.name + ' End Of Service Benefits Calculation'

    @api.multi
    @api.depends('employee_id')
    def _get_contract_id(self):
        for rec in self:
            if rec.employee_id:
                contract_id = contract_obj.search([('out_state', '!=', False),
                                                   ('employee_id', '=', rec.employee_id.id),
                                                  ('company_id', '=', self.env.user.company_id.id)])
                if len(contract_id) > 1:
                    raise UserError('This %s employee have more than one contract with status Running or  To renew' % rec.employee_id.name)
                elif not contract_id:
                    raise UserError('This %s employee has not have running contract' % rec.employee_id.name)

                rec.contract_id = contract_id.id
            else:
                rec.employee_id = False
    
    def get_furn_balance(self, furniture):
        amount = 0.0
        #=======================================================================
        # if self.contract_id and self.contract_id.out_state:
        #     if self.contract_id.term_reason == 'discip':
        #         if self.contract_duration <= 1.0:
        #             amount = furniture.balance * 0.8
        #         elif self.contract_duration <= 2.0:
        #             amount = furniture.balance * 0.6
        #         elif self.contract_duration <= 3.0:
        #             amount = furniture.balance * 0.4
        #         elif self.contract_duration <= 4.0:
        #             amount = furniture.balance * 0.2
        #     else:
        #         if self.contract_duration <= 1.0:
        #             amount = furniture.balance * 0.6
        #         elif self.contract_duration <= 2.0:
        #             amount = furniture.balance * 0.4
        #         elif self.contract_duration <= 3.0:
        #             amount = furniture.balance * 0.3
        #         elif self.contract_duration <= 4.0:
        #             amount = furniture.balance * 0.1
        #=======================================================================
        
        return amount
    
    @api.onchange('employee_id','contract_id',)
    def onchange_employee(self):
        if not self.employee_id or not self.contract_id:
            self.deduction_lines = False
            self.eos_original_amount = 0.0
            self.rule_id = False
            self.note = ''
            return
        fur_allowances = self.env['hr.furniture.allowance'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approved')]) if self.env.get('hr.furniture.allowance', False) else []
        loans = self.env['hr.loan'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approved')]) if self.env.get('hr.loan', False) else []
        all_air_tickets = self.env['hr.air.ticket'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approved')]) if self.env.get('hr.air.ticket', False) else []
        air_tickets = all_air_tickets.filtered(lambda x: fields.Date.from_string(x.date).year == datetime.now().year) if self.env.get('hr.air.ticket', False) else []
        leaves = self.env['hr.holidays'].search([('employee_id', '=', self.employee_id.id),
                                                  ('state', '=', 'validate'),
                                                  ('holiday_status_id.leave_type', '=', 'legal'),
                                                  '|','&',('date_to', '<=', self.contract_id.date_end),
                                                ('date_from', '>=', str(datetime.now().year)+'-01-01'),
                                                 ('year', '=', str(datetime.now().year))])
        ded_lines = []
        if self.contract_id.out_state:
            # leaves deduction
            days_remove = 0.0
            days_add = 0.0
            for leave in leaves:
                if leave.type == 'add':
                    days_add += abs(leave.number_of_days)
                else:
                    days_remove += abs(leave.number_of_days)
            supose_leaves = datetime.strptime(self.contract_id.date_end,DEFAULT_SERVER_DATE_FORMAT).month * (days_add / 12.0)
            if days_remove > supose_leaves:
                deduct_leaves = (days_remove - supose_leaves) * (self.contract_id.wage / 30.4)
                vals = {'amount':deduct_leaves,
                         'type':'leaves',
                         'eos_calc':self.id,
                         }
                ded_lines.append(vals)
            
            for furn in fur_allowances:
                balance = self.get_furn_balance(furn)
                vals = {'amount':balance,
                         'type':'furniture_allowance',
                         'eos_calc':self.id,
                         }
                ded_lines.append(vals)
            
            for loan in loans:
                vals = {'amount':loan.balance,
                         'type':'loan',
                         'eos_calc':self.id,
                         }
                ded_lines.append(vals)
                
            for air_teckit in air_tickets:
                exit_day_of_year = fields.Date.from_string(self.contract_end_date).timetuple().tm_yday
                amount = (exit_day_of_year * air_teckit.amount) / 365.0 
                vals = {'amount':amount,
                         'type':'air_teckit',
                         'eos_calc':self.id,
                         }
                ded_lines.append(vals)
            
        self.deduction_lines = False
        self.deduction_lines = [(0, 0, val) for val in ded_lines]
        self._compute_eos_original_amount()
    
    @api.multi
    @api.depends('deduction_lines')
    def _compute_deductions_amount(self):
        for rec in self:
            amount = 0
            for ded_line in rec.deduction_lines:
                amount += ded_line.amount or 0
            rec.deductions_amount = amount
    
    @api.multi
    def _compute_eos_original_amount(self):
        rule_obj = self.env['hr.eosb.rule']
        for rec in self:
            amount = 0.0
            if rec.contract_id and rec.contract_id.term_reason_id:
                rule_id = rule_obj.search([('reason_id','=',rec.contract_id.term_reason_id.id),
                                           ('country_id','=',rec.employee_id.country_id.id),
                                           ('contract_type','=',rec.contract_id.contract_type)],limit=1)
                if not rule_id:
                    rule_id = rule_obj.search([('reason_id','=',rec.contract_id.term_reason_id.id),
                                           ('country_id','=',rec.employee_id.country_id.id),
                                           ('contract_type','=','both')])
                    
                if not rule_id: 
                    rule_id = rule_obj.search([('reason_id','=',rec.contract_id.term_reason_id.id),
                                           ('country_id','=',False),
                                           ('contract_type','=',rec.contract_id.contract_type)])
                if not rule_id: 
                    rule_id = rule_obj.search([('reason_id','=',rec.contract_id.term_reason_id.id),
                                           ('country_id','=',False),
                                           ('contract_type','=','both')])
                    
                text = _("""There is no matched rule for this employee please check the  rules and click on recalculate.""")
                text1 = _("""The worker is not worth the end of service reward.""")
                if not rule_id:
                    rec.rule_id = False
                    rec.note = """<span 
                           >
                            %s
                        </span>"""%text
                else:
                    rule_id = rule_id[0]
                    rec.rule_id = rule_id.id
                    
                    work_duration  = rec.contract_id.work_duration
                    wage = rec.contract_id.wage
                    
                    if not rule_id.tiers:
                        rule_line_id = rule_id.eosb_rule_line_ids.filtered(lambda x:x.from_year < work_duration and x.to_year >= work_duration)
                        if not rule_line_id:
                            rec.note = """<span 
                                >
                                %s
                            </span>"""%text1
                        else:
                            amount = wage * rule_line_id.amount * work_duration
                            rec.note = False
                    else:
                        asign_rule= True
                        wd = work_duration
                        first = True
                        for line in rule_id.eosb_rule_line_ids:
                            if first:
                                wd -= (work_duration > line.to_year and line.to_year or work_duration)
                                first = False
                                if round(wd) <= 0  and line.from_year != 0  :
                                    wd = 1
                                    break
                                amount += line.amount * wage * (work_duration > line.to_year and line.to_year or work_duration)
                            elif work_duration > line.to_year :
                                amount += line.amount * wage * (line.to_year -  line.from_year)
                                wd -= (line.to_year -  line.from_year)
                            elif  work_duration > line.from_year and work_duration <= line.to_year:
                                amount += line.amount * wage * (work_duration -  line.from_year)
                                wd -= (work_duration -  line.from_year)
                        if round(wd) > 0:
                            rec.note = """<span 
                           >
                            %s
                            </span>"""%text1
                        else:
                            rec.note = False
            rec.eos_original_amount = amount
    
    
    @api.multi
    def unlink(self):
        if self.env['account.payment'].search([('eosb_id','in',self.ids),('state','!=','cancelled')],limit=1):
            raise UserError("You can not cancel an EOSB with pending payment. Please, cancel or delete payment first!")
        if self.mapped('payslip_id'):
            raise UserError("You can not cancel an EOSB with pending payslip. Please, refund payslip first!")
        
        return super(EOSB, self).unlink()
    @api.multi
    @api.depends('eos_original_amount', 'deductions_amount')
    def _compute_balance(self):
        for rec in self:
            rec.balance = rec.eos_original_amount - rec.deductions_amount
    
    def approve_eosb(self):
        if self.search([('contract_id','in',self.contract_id.ids),('state','=','approved')],limit = 1):
            raise UserError("This contract is mentioned in another approved EOSB.")
        self.mapped('contract_id').write({'appeared_in_eosb':True})
        self.write({'state': 'approved'})
        if self.payment_method =='receipt':
            self.create_payment()
        return True
    
    def cancel_eosb(self):
        if self.env['account.payment'].search([('eosb_id','=',self.id),('state','!=','cancelled')],limit=1):
            raise UserError("You can not cancel an EOSB with a payment. Please, cancel or delete payment first!")
        if self.payslip_id:
            raise UserError("You can not cancel an EOSB with pending payslip. Please, refund payslip first!")
        self.write({'state': 'cancel'})
        return True
    
    def draft_eosb(self):
        self.write({'state': 'draft'})
        return True
    
    
    
    def get_payment_vals(self):    
        journal_id = self.env['account.journal'].search(['|',('type','=','bank'),('type','=','cash')],limit = 1)
        return{
            'payment_type': 'outbound',
            'payment_date': self.date,
            'journal_id':journal_id.id,
            'payment_method_id':1,
            'communication': 'EOSB For '+str(self.employee_id.name),
            'partner_type': 'supplier',
            'amount': self.balance,
            'company_id': self.env.user.company_id.id,
            'eosb_id': self.id,
            'partner_id':self.employee_id.user_id.partner_id.id,
            'destination_account_id':self.env.user.company_id.eosb_account_id.id
               }
    
    def create_payment(self):
        payment_obj = self.env['account.payment']
        if not self.env.user.company_id.eosb_account_id :
            raise UserError(_("Please select an EOSB Account in setting first!"))
        if not self.employee_id.user_id:
            raise UserError(_("Please make sure the employee profile is linked to a user!"))
        payment_vals = self.get_payment_vals()
        payment = payment_obj.create(payment_vals)
        return payment
    
    def open_payment(self):
        action = self.env.ref('account.action_account_payments_payable').read()[0]
        action['domain'] = [('eosb_id','=',self.id)]
        return action
        
    
class eos_deductions(models.Model):
    _name = 'hr.eos.deduction.line'
    
    name = fields.Char('Name', compute='_compute_name') 
    eos_calc = fields.Many2one('hr.eosb.calac', 'EoS Calculation')
    type = fields.Selection('_get_type', 'Deduction Type', required=True)
    amount = fields.Float('Deduction Amount')
    
    def _get_type(self):
        type = [('leaves', 'Leaves'),('furniture_allowance', 'Furniture Allowance'),('loan', 'Loan'),('air_teckit', 'Air Ticket')]
        return type
    
    
    @api.multi
    def _compute_name(self):
        for rec in self:
            if rec.type:
                rec.name = dict(self._get_type()).get(rec.type) + ' Deduction'
            
                
        

    
class EOSBrule(models.Model):
    _name = 'hr.eosb.rule'
    
    name = fields.Char('Name',readonly=True,related='reason_id.name')
    country_id = fields.Many2one('res.country', 'Country')
    tiers = fields.Boolean('Tiers')
    eosb_rule_line_ids = fields.One2many('hr.eosb.rule.line', 'eosb_rule_id', string='Rule lines', required=True)
    reason_id = fields.Many2one('hr.eosb.reason', 'Reason', required=True)
    contract_type= fields.Selection([('unlimited','Unlimited'),('limited','Limited'),('both','Both')],default='unlimited',string="Contract type",required=True)

    
class EOSBrule(models.Model):
    _name = 'hr.eosb.rule.line'
    _order  = 'from_year'
    
    eosb_rule_id = fields.Many2one('hr.eosb.rule', 'EOSB Rule')
    from_year = fields.Float('From Year', required=True)
    to_year = fields.Float('To Year')
    amount = fields.Float('amount')
    
    
    @api.constrains('to_year','from_year')
    def constrains_year(self):
        for rec in self:
            if rec.from_year>=rec.to_year:
                raise UserError("From Year must be less than to year")
            record = self.search([ '&','|','|','&',('from_year','>=',rec.from_year),('from_year','<',rec.to_year),
                         '&',('to_year','>',rec.from_year),('to_year','<=',rec.to_year),
                        '&',('to_year','>=',rec.to_year),('from_year','<=',rec.from_year),('eosb_rule_id','=',rec.eosb_rule_id.id)
                         ],limit = 1,offset=1)
            if record:
                raise UserError("There is overlap")
    
    
class EOSBreason(models.Model):
    _name = 'hr.eosb.reason'
    
    name = fields.Char('Reason',required=True)
    out_state = fields.Selection([('term', 'Termination'), ('resign', 'Resignation'), ], 'End of service Status',required=True)
    for_female = fields.Boolean('For Female Only')
    
    
class HrPayslip(models.Model): 
    _inherit = 'hr.payslip'
    
    
    @api.multi
    def refund_sheet(self):
        return super(HrPayslip, self.with_context(input_ids = self.mapped('input_line_ids').filtered(lambda x:x.code == 'EOSB'))).refund_sheet()
    
    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        print()
        res = super(HrPayslip,self).get_inputs(contracts, date_from, date_to)
        if self.employee_id and date_from and date_to:
            eosb_ids = self.env['hr.eosb.calac'].search([('date','>=',date_from),('date','<=',date_to),('state','=','approved'),('payslip_id','=',False),('payment_method','=','payslip')])
            for rec in eosb_ids:
                vals = {'eosb_id':rec.id,'name': rec.name, 'code': 'EOSB', 'amount': rec.balance, 'contract_id': rec.contract_id.id}
                res += [vals]
        return res
    
    
    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        res =  super(HrPayslip, self).create( vals)
        if self.env.context.get('input_ids',False):
            input_ids = self.env.context.get('input_ids')
            input_ids.mapped('eosb_id').write({'payslip_id':False})
            res.input_line_ids = [(0,0, {'eosb_id':rec.eosb_id.id,
                                         'name': rec.name,
                                          'code': 'EOSB', 'amount': rec.amount,
                                           'contract_id': rec.contract_id.id}) for rec in input_ids ]
            
        return res
    
class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'
    
    eosb_id = fields.Many2one('hr.eosb.calac',string='EOSB')
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.eosb_id:
                rec.eosb_id.payslip_id = False
        return super(HrPayslipInput, self).unlink()
    
    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        res =  super(HrPayslipInput, self).create( vals)
        if res.eosb_id and not self.env.context.get('input_ids',False):
            res.eosb_id.payslip_id = res.payslip_id.id
        return res
            
