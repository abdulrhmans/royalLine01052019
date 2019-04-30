# -*- coding: utf-8 -*-

from odoo import fields, models,api,_


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    loan_account_type = fields.Selection([('once','One Account For All Employees'),
                                          ('multiple','Account Per Employee')], string='Accounting Policy', related='company_id.loan_account_type')
    
    loan_account_id = fields.Many2one('account.account','Loan Account', related='company_id.loan_account_id')
    reference_employee_in_journal_entries = fields.Boolean(string="Reference Employee In Journal Entries",related='company_id.reference_employee_in_journal_entries',default=True, readonly=True)
    loan_user_notify = fields.Many2many('res.users',string='Users To Notify',related='company_id.loan_user_notify')
    loan_period_deduct = fields.Selection([('weekly','Weekly Deduct'),
                                          ('monthly','Monthly Deduct')], string='Deduction Loan Period', related='company_id.loan_period_deduct')
    loan_account_ids = fields.One2many('loan.accounts', 'config_id', string='Sister Companies Loan Account', related='company_id.loan_account_ids')
    
    @api.onchange('loan_account_type')
    def change_accounting_poilicy(self):
        res = {}
        if self.env['hr.loan'].search([('state','=','approved')]):
            res = {'warning': {
                'title': _('Warning'),
                'message': _('If you changed Loan Accounting Policy, This change may lead to unwanted results.')
                }}
            return res

    
class Company(models.Model):
    _inherit = 'res.company'
    
    loan_account_type = fields.Selection([('once','One Account For All Employees'),
                                          ('multiple','Account Per Employee')], string='Accounting Policy')
    
    loan_account_id = fields.Many2one('account.account','Loan Account')
    reference_employee_in_journal_entries = fields.Boolean(string="Reference Employee In Journal Entries", default=True)
    loan_user_notify = fields.Many2many('res.users',string='Users To Notify')
    loan_period_deduct = fields.Selection([('weekly','Weekly Deduct'),
                                          ('monthly','Monthly Deduct')], string='Deduction Loan Period', default='monthly')
    loan_account_ids = fields.One2many('loan.accounts', 'config_id', string='Sister Companies Loan Account')

class LoanAccounts(models.Model):
    _name = 'loan.accounts'
    
    company_id = fields.Many2one('res.company', 'Company',default=lambda self: self.env.user.company_id, required=True) 
    target_company_id = fields.Many2one('res.company', 'Target Company', required=True)
    account_id = fields.Many2one('account.account', 'Account', required=True)
    config_id = fields.Many2one('res.company', 'Config')
    
    