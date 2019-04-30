# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models
from odoo.tools.misc import formatLang

class ReportSalaryState(models.AbstractModel):
    _name = 'report.hr_report_salary.salary_state'
    
    totals = 0.0
    social_security = 0.0
    income_tax = 0.0
    hi_company = 0.0
    ss_company = 0.0
        
    def formatDigits(self, amount, digits):
        return formatLang(self.env, amount, digits=digits)
    
    @api.model
    def get_report_values(self, docids, data=None):
        print (docids, data)
        payslipLines = self.get_payslip_lines(data['form'])
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': self.env['hr.payslip'].browse(docids),
            'time': time,
            'payslipLines': payslipLines,
            'get_totals': self.get_totals(),
            'formatLang': self.formatDigits,
            'to_date': data['form']['to_date'],
            'from_date': data['form']['from_date'],
            'Date': fields.date.today(),
            'show_bank_account': data['form']['show_bank_account'],
            'statement': data['form']['statement'],
            'salary': data['form']['salary'],
            'show_social_security': data['form']['show_social_security'],
            'show_income_tax': data['form']['show_income_tax'],
            'ss_company': data['form']['ss_company'],
            'hi_company': data['form']['hi_company'],
            'currency': self.env.user.company_id.currency_id.name,
            'company_name': self.env.user.company_id.name,
        }
        
        
    def get_payslip_lines(self,form):
        payslip_obj = self.env['hr.payslip']
        payslip_line_obj = self.env['hr.payslip.line']
        res=[]
        salary = 'NET'
        if form['salary'] == 'basic':
            salary = 'BASIC'
        
        for employee in form['employee_ids']:
            payslips = payslip_obj.search([('date_to','<=',form['to_date']),
                                                                 ('date_from','>=',form['from_date']),
                                                                 ('employee_id','=',employee),
                                                                 ('state','=','done')])
            rejected_ids = []
            for slip in payslips:
                if slip.credit_note:
                    rejected_ids.append(slip.id)
                    if slip.refund_id:
                        rejected_ids.append(slip.refund_id.id)
                         
            for line in payslips:          
                if not line.id in rejected_ids:
                    payslip_lines_ids = payslip_line_obj.search([('slip_id','=',line.id)])
                    value = {}
                    value['bank_account'] = line.employee_id.iban
                    value['bank_name'] = line.employee_id.bank_id.name if line.employee_id.bank_id else ''
                    value['branch_name'] = line.employee_id.branch_id.name if line.employee_id.branch_id else ''
                    value['emp_id'] = line.employee_id.identification_id
                    value['name'] = line.employee_id.name
                    value['from'] = line.date_from
                    value['to'] = line.date_to
                    value['net_salary'] = 0.0
                    value['income_tax'] = 0.0
                    value['social_security'] = 0.0
                    value['hi_company'] = 0.0
                    value['ss_company'] = 0.0
                    value['currency'] = line.company_id.currency_id.name
                    for pLine in payslip_lines_ids:
                        if pLine.code == salary:
                            value['net_salary'] = pLine.total
                        elif pLine.code == 'SSD':
                            value['social_security'] = pLine.total
                        elif pLine.code == 'IIT':
                            value['income_tax'] = pLine.total
                        elif pLine.code == 'SSC':
                            value['ss_company'] = pLine.total
                        elif pLine.code == 'HIR':
                            if pLine.total > 0:
                                value['hi_company'] = line.employee_id.company_health_insurance_amount
                             
                    self.totals += value['net_salary']
                    self.social_security += value['social_security']
                    self.income_tax += value['income_tax']
                    self.ss_company += value['ss_company']
                    self.hi_company += value['hi_company']
                    res.append(value)
        return res 
 
 
    def get_totals(self):
        return {'Salary':self.totals , 'Social_Security':self.social_security , 'Income_Tax':self.income_tax, 'hi_company': self.hi_company, 'ss_company':self.ss_company}
     
