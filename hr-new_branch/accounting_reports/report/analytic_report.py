# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models,_
from datetime import datetime

class AnalyticReport(models.AbstractModel):
    _name = 'report.accounting_reports.analytic_report'
    
    deb_tot = 0.0
    credit_tot = 0.0
    bal_tot = 0.0
    def get_analytic_lines(self,form,ids):
        move_obj = self.env['account.move.line'].search([('analytic_account_id','in',ids),
                                                        ('date','>=',form['from_date']),
                                                   ('date','<=',form['to_date'])])
        debit_total = 0.0
        credit_total = 0.0
        balance_total = 0.0
        res = []
        for line in move_obj:
            index=-1
            for x in range(len(res)):
                if res[x][0] == line.analytic_account_id.id:
                    index = x
                    break
            if index != -1:
                index1 = -1
                for x1 in range(len(res[index][2])):
                    if res[index][2][x1]['id'] == line.account_id.id:
                        index1 = x1
                        break
                if index1 != -1:
                    value = {}
                    res[index][2][index1]['debit']+= line.debit
                    res[index][2][index1]['credit'] += line.credit
                    res[index][2][index1]['bal'] = res[index][2][index1]['debit'] -  res[index][2][index1]['credit']
                  
                    
                else:
                    value= {}
                    value['id'] = line.account_id.id
                    value['name'] = line.account_id.name
                    value['debit'] = line.debit
                    value['credit'] = line.credit
                    value['bal'] = line.debit - line.credit 
            
                   
                    res[index][2].append(value)
                     
                 
                debit_total += line.debit
                credit_total += line.credit
                balance_total += line.debit - line.credit
            else:
                value = {}
                tot = {'debit_tot':0.0}
                value['id'] = line.account_id.id
                value['name'] = line.account_id.name
                value['debit'] = line.debit
                value['credit'] = line.credit
                value['bal'] = line.debit - line.credit 
                res.append([line.analytic_account_id.id,line.analytic_account_id.name,[value]])
                debit_total += line.debit
                credit_total += line.credit
                balance_total += line.debit - line.credit
        self.deb_tot = debit_total
        self.credit_tot = credit_total
        self.bal_tot = balance_total
        return res
    @api.model
    def get_report_values(self, docids, data=None):
        ids = data['ids']
        docs = self.env[data['context']['active_model']].browse(self.env.context.get('active_ids', []))
        analyticlines = self.get_analytic_lines(data['form'],ids)
        if not analyticlines:
            analyticlines.append([0,'',[{'bal': 0.0, 'debit': 0.0, 'credit': 0.0, 'name': '', 'id': 0.0}]])
            
        return {
            'doc_ids': docids,
            'doc_model': 'account.analytic.account',
            'docs': docs,
            'time': time,
            'acclines': analyticlines,
            'from_date': data['form']['from_date'],
            'to_date': data['form']['to_date'],
            'Date': fields.datetime.today(),
            'debit_tot': self.deb_tot,
            'cre': self.credit_tot,
            'bal': self.bal_tot,
        }