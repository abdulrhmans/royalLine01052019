# -*- coding: utf-8 -*-

from odoo import models, fields, api
import time

class AccountWizard(models.TransientModel):
     _name = 'analytic.wizard.report'
     
     from_date = fields.Date('From',required=True)
     to_date = fields.Date('To',required=True)
     account_id = fields.Many2one('account.account',string='Financial Account')
     analytic_id = fields.Many2many('account.analytic.account')
     init_balance = fields.Boolean('Include Initial Balance')
     
     def print_report(self, data):
        if not self.account_id:
            analytic = []
            if self.analytic_id:
                analytic = self.analytic_id.ids
            else:
                analytic = self.env['account.analytic.account'].search([]).ids
            user = self.env.user.name
            data['form'] = {}
            data['ids'] = analytic
            data['form'].update(self.read(['from_date', 'to_date', str(user)])[0])
            return self.env.ref('accounting_reports.account_analytic_report').report_action(self, data=data)
        else:
            analytic = []
            if self.analytic_id:
                analytic = self.analytic_id.ids
            else:
                analytic = self.env['account.analytic.account'].search([]).ids
            user = self.env.user.name
            data['form'] = {}
            data['ids'] = analytic
            data['account'] = self.account_id.id
            data['accname'] = self.account_id.name
            data['intitial_balance'] = self.init_balance
            data['form'].update(self.read(['from_date', 'to_date', str(user)])[0])
            return self.env.ref('accounting_reports.account_analytic_report_per_fin').report_action(self, data=data)
