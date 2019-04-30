# -*- coding: utf-8 -*-
from odoo import api, models,_
from datetime import datetime

class TrialBalance(models.AbstractModel):
    _inherit = 'account.coa.report'
    
    def get_templates(self):
        templates = super(TrialBalance, self).get_templates()
        templates['main_template'] = 'tb_report_columns_into_one.template_coa_report'
        return templates
    
    def get_columns_name(self, options):
        columns = [
            {'name': ''},
            {'name': _(''), 'class': 'number'},
        ]
        if options.get('comparison') and options['comparison'].get('periods'):
            columns += [
                {'name': _('Debit'), 'class': 'number'},
                {'name': _('Credit'), 'class': 'number'},
            ] * len(options['comparison']['periods'])
        return columns + [
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _(''), 'class': 'number'},
        ]
        
    def _post_process(self, grouped_accounts, initial_balances, options, comparison_table):
        lines = []
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        title_index = ''
        sorted_accounts = sorted(grouped_accounts, key=lambda a: a.code)
        zero_value = ''
        sum_columns = [0,0]
        for period in range(len(comparison_table)):
            sum_columns += [0, 0]
        for account in sorted_accounts:
            #skip accounts with all periods = 0 and no initial balance
            non_zero = False
            for p in range(len(comparison_table)):
                if (grouped_accounts[account][p]['debit'] or grouped_accounts[account][p]['credit']) or\
                    not company_id.currency_id.is_zero(initial_balances.get(account, 0)):
                    non_zero = True
            if not non_zero:
                continue

            initial_balance = initial_balances.get(account, 0.0)
            sum_columns[0] += initial_balance
            cols = [
                {'name': initial_balance != 0 and self.format_value(initial_balance) or zero_value, 'no_format_name': initial_balance},
            ]
            total_periods = 0
            for period in range(len(comparison_table)):
                amount = grouped_accounts[account][period]['balance']
                debit = grouped_accounts[account][period]['debit']
                credit = grouped_accounts[account][period]['credit']
                total_periods += amount
                cols += [{'name': debit > 0 and self.format_value(debit) or zero_value, 'no_format_name': debit > 0 and debit or 0},
                         {'name': credit > 0 and self.format_value(credit) or zero_value, 'no_format_name': credit > 0 and abs(credit) or 0}]
                p_indice = period * 2 if period > 1 else 3
                p_indice = 1 if period == 0 else p_indice
                sum_columns[(p_indice)] += debit if debit > 0 else 0
                sum_columns[(p_indice) + 1] += credit if credit > 0 else 0

            total_amount = initial_balance + total_periods
            sum_columns[-1] += total_amount
            cols += [
                {'name': total_amount != 0 and self.format_value(total_amount) or zero_value, 'no_format_name': abs(total_amount)},
                ]
            lines.append({
                'id': account.id,
                'name': account.code + " " + account.name,
                'columns': cols,
                'unfoldable': False,
                'caret_options': 'account.account',
            })
        lines.append({
             'id': 'grouped_accounts_total',
             'name': _('Total'),
             'class': 'o_account_reports_domain_total',
             'columns': [{'name': self.format_value(v)} for v in sum_columns],
             'level': 0,
        })
        return lines