# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models,_
from datetime import datetime

class AnalyticReport(models.AbstractModel):
    _name = 'report.accounting_reports.analytic_report_per'
    
    def get_data(self, data):
        analytic_acc = self.env['account.analytic.account'].search([('id','in',data['ids'])])
        res = []
        initial_bal = 0.0
        datas = []
        for line in analytic_acc:
            accmove = self.env['account.move.line'].search([('analytic_account_id','=',line.id),
                                                    ('account_id','=',data['account']),
                                                    ('date','>=',data['form']['from_date']),
                                                    ('date','<=',data['form']['to_date'])])
            dic={'name':line.name,'data':[],'deb_tot':0.0,'cre_tot':0.0,'bal_tot':0.0}
            if data['intitial_balance'] == True:
                acl = self.env['account.move.line'].search([('analytic_account_id','=',line.id),
                                                    ('account_id','=',data['account']),
                                                    ('date','<',data['form']['from_date'])])
                if acl:
                    initi = 0.0
                    for l in acl:
                        bal = (l.debit - l.credit) + initi
                        initi = bal
                    initial_bal = initi 
                if initial_bal > 0 and accmove:
                    value = {}
                    value['name'] = 'Initial Balance'
                    value['date'] = ''
                    value['jour'] = ''
                    value['j_entry'] = ''
                    value['debit'] = initial_bal
                    value['credit'] = 0.0
                    value['ref'] = ''
                    value['account'] = ''
                    value['bal'] = 0.0
                    dic['data'].append(value)
                elif initial_bal < 0 and accmove:
                    value = {}
                    value['name'] = 'Initial Balance'
                    value['date'] = ''
                    value['jour'] = ''
                    value['j_entry'] = ''
                    value['debit'] = 0.0
                    value['credit'] = initial_bal
                    value['ref'] = ''
                    value['account'] = ''
                    value['bal'] = 0.0
                    dic['data'].append(value)
            
            for line1 in accmove:
                value = {}
                value['name'] = line1.name
                value['date'] = line1.date
                value['jour'] = line1.journal_id.name
                value['j_entry'] = line1.move_id.name
                value['debit'] = line1.debit
                value['credit'] = line1.credit
                value['ref'] = line1.ref
                value['account'] = line1.account_id.name
                value['bal'] = (line1.debit - line1.credit) + initial_bal
                initial_bal = value['bal']
                
                dic['deb_tot'] += line1.debit
                dic['cre_tot'] +=line1.credit
                dic['bal_tot'] += value['bal']
                dic['data'].append(value)
            
            datas.append(dic)
        return datas
    
    def get_language(self):
        current_user = self.env['res.users'].browse(self._uid)
        if current_user['partner_id']['lang'] in ['ar_SY']:
            lang = "ar"
        else:
            lang = "en"
        return lang
                
        
    @api.model
    def get_report_values(self, docids, data=None):
        ids = data['ids']
        docs = self.env[data['context']['active_model']].browse(self.env.context.get('active_ids', []))
        get_data = self.get_data(data)
        x1 = 0
        for x in range(len(get_data)):
            if len(get_data[x]['data']) == 0:
                x1+=1
        if x1 == len(get_data):
            get_data = [{'deb_tot': 0.0, 'data': [{'credit': 0.0, 'jour': ' ', 'date': '', 'ref': '', 'j_entry': '', 'bal': 0.0, 'account': '', 'name': '', 'debit': 0.0}], 'cre_tot': 0.0, 'name': '', 'bal_tot': 0.0}]
        return {
            'doc_ids': docids,
            'doc_model': 'account.account',
            'docs': docs,
            'time': time,
            'from_date': data['form']['from_date'],
            'to_date': data['form']['to_date'],
            'Date': fields.datetime.today(),
            'accmove':get_data,
            'analyticaccount': data['accname'],
            'getLang' : self.get_language()
        }