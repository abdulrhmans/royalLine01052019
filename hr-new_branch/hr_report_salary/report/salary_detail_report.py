# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models,_
from odoo.tools.misc import formatLang
from datetime import datetime

class ReportSalaryDetail(models.AbstractModel):
    _name = 'report.hr_report_salary.salary_detail'
    
    BASIC_total = 0.0
    CA_total = 0.0
    OTA_total = 0.0
    OA_total = 0.0
    GROSS_total = 0.0
    SSD_total = 0.0
    HIR_total = 0.0
    EBR_total = 0.0
    OD_total = 0.0
    SA_total = 0.0
    NET_total = 0.0
    IT_total = 0.0
     
    loan_total = 0.0
    add_total = 0.0
    commission_total = 0.0
    trans_total = 0.0
    
    def formatDigits(self, amount, digits):
        return formatLang(self.env, amount, digits=digits)
    
    def get_payslip_lines(self,form):
        sort_on = form['sort_on']
        sort_type = form['sort_type']
         
        state_domain = [form['state']]
        if form['state'] == 'all':
            state_domain = ['done','draft']
        
        all_employee_ids = form['employee_ids']
        payslip_obj = self.env['hr.payslip']
        payslip_line_obj = self.env['hr.payslip.line']
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        employee_ids = employee_obj.search( [])
        res=[]
        # set sort on and sort type 
        if sort_on == 'salary':
            employee_ids = []
            contracts = contract_obj.search([('employee_id','in',all_employee_ids)] ,order='wage '+sort_type)
            for contract in contracts:
                if contract.employee_id.id not in employee_ids:
                    employee_ids.append(contract.employee_id.id)
        else:
            order_by = sort_on+" "+sort_type
            employee_ids = employee_obj.search( [('id','in',all_employee_ids)], order=order_by)
                 
        for employee in employee_ids:
            payslips = payslip_obj.search([('date_to','<=',form['to_date']),
                                                                 ('date_from','>=',form['from_date']),
                                                                 ('employee_id','=',employee.id),
                                                                 ('state','in',state_domain)])
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
                    value['name'] = line.employee_id.name
                    value['id'] = line.employee_id.identification_id
                    value['net'] = 0.0
                    value['basic'] = 0.0
                    value['allowances'] = 0.0
                    value['deductions'] = 0.0
                    value['ss_ded'] = 0.0
                    value['hi_ded'] = 0.0
                    value['eb_ded'] = 0.0
                    value['sa_ded'] = 0.0
                    value['it_ded'] = 0.0
                    value['other_ded'] = 0.0
                    value['gross'] = 0.0
                    value['comm_alw'] = 0.0
                    value['otr_alw'] = 0.0
                    value['other_alw'] = 0.0
                     
                    value['commission_alw'] = 0.0
                    value['loan_ded'] = 0.0
                    value['trans_alw'] = 0.0
                    value['add_ded'] = 0.0
                     
                    value['currency'] = line.company_id.currency_id.name
                    for pLine in payslip_lines_ids:
                        if pLine.category_id.code == 'NET':
                            value['net'] += pLine.total
                        elif pLine.category_id.code == 'ALW':
                            value['allowances'] += pLine.total
                            if pLine.code == 'CA':
                                value['comm_alw'] += pLine.total
                            elif pLine.code == 'OT':
                                value['otr_alw'] += pLine.total
                            elif pLine.code == 'SC':
                                value['commission_alw'] += pLine.total
                            elif pLine.code == 'TA':
                                value['trans_alw'] += pLine.total
                            else:
                                value['other_alw'] += pLine.total
                        elif pLine.category_id.code == 'DED':
                            value['deductions'] += pLine.total
                            if pLine.code == 'LOAN':
                                value['loan_ded'] += pLine.total
                            elif pLine.code == 'ADD':
                                value['add_ded'] += pLine.total
                            elif pLine.code == 'EBD':
                                value['eb_ded'] += pLine.total
                            elif pLine.code == 'HIN':
                                value['hi_ded'] += pLine.total
                            elif pLine.code == 'SSD':
                                value['ss_ded'] += pLine.total
                            elif pLine.code == 'IIT':
                                value['it_ded'] += pLine.total
                            else:
                                value['other_ded'] += pLine.total
                                 
                        elif pLine.category_id.code == 'GROSS':
                            value['gross'] += pLine.total
                        elif pLine.category_id.code == 'BASIC':
                            value['basic'] += pLine.total
                         
                          
                    self.BASIC_total += value['basic']
                    self.CA_total += value['comm_alw']
                    self.OTA_total += value['otr_alw']
                    self.OA_total += value['other_alw']
                    self.GROSS_total += value['gross']
                    self.SSD_total += value['ss_ded']
                    self.HIR_total += value['hi_ded']
                    self.EBR_total += value['eb_ded']
                    self.OD_total += value['other_ded']
                    self.SA_total += value['sa_ded']
                    self.IT_total += value['it_ded']
                     
                    self.commission_total += value['commission_alw']
                    self.loan_total += value['loan_ded']
                    self.trans_total += value['trans_alw']
                    self.add_total += value['add_ded']
                     
                    self.NET_total += value['net']
                     
                    res.append(value)
        return res 
 
 
    def get_totals(self):
        return {'basic_total':self.BASIC_total ,
                'ca_total':self.CA_total , 
                'OTA_total':self.OTA_total,
                'oa_total':self.OA_total,
                'gross_total':self.GROSS_total,
                'ssd_total':self.SSD_total,
                'hi_total':self.HIR_total,
                'eb_total':self.EBR_total,
                'sa_total':self.SA_total,
                'od_total':self.OD_total,
                'it_total':self.IT_total,
                'net_total':self.NET_total,
                 
                'commission_total':self.commission_total,
                'loan_total':self.loan_total,
                'add_total':self.add_total,
                'trans_total':self.trans_total,
                }
         
    def _get_month_name(self, day):
        months = {'January': u'كانون الثاني','February': u'شباط',
                  'March': u'اذار','April': u'نيسان',
                  'May': u'ايار','June': u'حزيران',
                  'July': u'تموز','August': u'آب',
                  'September': u'ايلول','October': u'تشرين الاول',
                  'November': u'تشرين الثاني','December': u'كانون الاول',}
        str_month=''
        month = datetime.strptime(day,'%Y-%m-%d').month
        year = datetime.strptime(day,'%Y-%m-%d').year
        if month == 1:
            str_month = 'January'
        elif month == 2:
            str_month = 'February'
        elif month == 3:
            str_month = 'March'
        elif month == 4:
            str_month = 'April'
        elif month == 5:
            str_month = 'May'
        elif month == 6:
            str_month = 'June'
        elif month == 7:
            str_month = 'July'
        elif month == 8:
            str_month = 'August'
        elif month == 9:
            str_month = 'September'
        elif month == 10:
            str_month = 'October'
        elif month == 11:
            str_month = 'November'
        elif month == 12:
            str_month = 'December'
        lang = self.get_language()
        if lang == 'ar':
            str_month = months[str_month]
        return str_month+' / '+str(year)

    def get_language(self):
        current_user = self.env['res.users'].browse(self._uid)
        if current_user['partner_id']['lang'] in ['ar_SY']:
            lang = "ar"
        else:
            lang = "en"
        return lang
    
    
    @api.model
    def get_report_values(self, docids, data=None):
        getMonthName = self._get_month_name(data['form']['from_date'])
        payslipLines = self.get_payslip_lines(data['form'])
        docs = self.env[data['context']['active_model']].browse(self.env.context.get('active_ids', []))
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'time': time,
            'payslipLines': payslipLines,
            'get_totals': self.get_totals,
            'get_month_name': getMonthName,
            'formatLang': self.formatDigits,
            'from_date': data['form']['from_date'],
            'to_date': data['form']['to_date'],
            'Date': fields.date.today(),
        }
        