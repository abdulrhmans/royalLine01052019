# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
import time
import base64
import os, io
from PIL import Image
from xlwt import *
from odoo.tools.misc import *
from odoo.tools.misc import formatLang
from datetime import datetime

class wizard_salary_details_report(models.Model):
    _name = "salary.details.report"
    _description = "Salary Details Report"
    
    from_date = fields.Date('From date', required=True)
    to_date = fields.Date('To date', required=True)
    employee_ids = fields.Many2many('hr.employee', 'salary_detail_employee_rel', 'employee_id', 'report_id',required=True)
    sort_on =  fields.Selection([('name','Name'),('salary','Salary')]
                                    ,'Sort On', required=True,default='name')
    sort_type = fields.Selection([('desc','Descending'),
                                       ('asc','Ascending'),]
                                      ,'Sort Type', required=True,default='asc')
    state = fields.Selection([('draft','Draft'),
                              ('done','Done'),
                              ('all','Draft and Done'),]
                              ,'Payslip State', required=True)
    
    def print_report(self, data):
        data['form'] = {}
        data['form'].update(self.read(['from_date', 'to_date', 'employee_ids', 'sort_on', 'sort_type', 'state'])[0])
        return self.env.ref('hr_report_salary.salary_detail_report').with_context(landscape=True).report_action(self, data=data)
    
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
    
    def print_excel(self):
        self.get_report()
        filename = ('/tmp//Salary-Report.xls') 
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_xls_document/?filename=%s' % (filename),
            'target': 'new',
        }
     
    def get_report(self):
        month = self._get_month_name(self.from_date)
        book = xlwt.Workbook(style_compression=2)
        today = fields.date.today()
        style = 'font: name Arial ; font:height 300; align: wrap on, vert center, horiz center'
        
        sheet1 = book.add_sheet("From")
        sheet1.write_merge(1, 2 ,4 ,6, 'Salary Details %s'%month, Style.easyxf(style))
        sheet1.write(4, 0 , 'From:')
        sheet1.write(4, 1 , self.from_date)
        sheet1.write(4, 6 , 'To:')
        sheet1.write(4, 7 , self.to_date)
        sheet1.write(6, 0 , 'Print Date:')
        sheet1.write(6, 1 , str(today))
        sheet1.write_merge(8, 8 , 3, 7 , 'Allowances')
        sheet1.write_merge(8, 8 , 9, 13, 'Deductions')
        
        sheet1.write(10, 0 , 'ID')
        sheet1.write(10, 1 , 'Name')
        sheet1.write(10, 2 , 'Basic Salary ')
        sheet1.write(10, 3 , 'Communication')
        sheet1.write(10, 4 , 'Transportation')
        sheet1.write(10, 5 , 'Overtime')
        sheet1.write(10, 6 , 'Commission')
        sheet1.write(10, 7 , 'Others')
        sheet1.write(10, 8 , 'Gross')
        sheet1.write(10, 9 , 'Attendance Deductions')
        sheet1.write(10, 10 , 'Social Security')
        sheet1.write(10, 11 , 'Health Insurance')
        sheet1.write(10, 12 , 'Loan')
        sheet1.write(10, 13 , 'Others')
        sheet1.write(10, 14 , 'Net Salary')
        payslip = self.get_payslip_lines()
        totals = self.get_totals()
        x = 11
        if payslip:
            for line in payslip:
                sheet1.write(x, 0 ,line['id'])
                sheet1.write(x, 1 ,line['name'])
                sheet1.write(x, 2 ,line['basic'])
                sheet1.write(x, 3 ,line['comm_alw'])
                sheet1.write(x, 4 ,line['trans_alw'])
                sheet1.write(x, 5 ,line['otr_alw'])
                sheet1.write(x, 6 ,line['commission_alw'])
                sheet1.write(x, 7 ,line['other_alw'])
                sheet1.write(x, 8 ,line['gross'])
                sheet1.write(x, 9 ,line['add_ded'])
                sheet1.write(x, 10 ,line['ss_ded'])
                sheet1.write(x, 11 ,line['hi_ded'])
                sheet1.write(x, 12 ,line['loan_ded'])
                sheet1.write(x, 13 ,line['other_ded'])
                sheet1.write(x, 14 ,line['net'])
                x+=1
                
        sheet1.write(x+1, 1 ,'Total')
        sheet1.write(x+1, 2 ,totals['basic_total'])
        sheet1.write(x+1, 3 ,totals['ca_total'])
        sheet1.write(x+1, 4 ,totals['trans_total'])
        sheet1.write(x+1, 5 ,totals['OTA_total'])
        sheet1.write(x+1, 6 ,totals['commission_total'])
        sheet1.write(x+1, 7 ,totals['oa_total'])
        sheet1.write(x+1, 8 ,totals['gross_total'])
        sheet1.write(x+1, 9 ,totals['add_total'])
        sheet1.write(x+1, 10 ,totals['ssd_total'])
        sheet1.write(x+1, 11 ,totals['hi_total'])
        sheet1.write(x+1, 12 ,totals['loan_total'])
        sheet1.write(x+1, 13 ,totals['od_total'])
        sheet1.write(x+1, 14 ,totals['net_total'])
        
        sheet1.write_merge(x+3, x+3 , 0, 1 , 'Human Resource Signature ')
        sheet1.write_merge(x+4, x+4 , 0, 1 , '..................')
        sheet1.write_merge(x+3, x+3 , 4, 5 , 'Financial Manager Signature ')
        sheet1.write_merge(x+4, x+4 , 4, 5 , '..................')
        sheet1.write_merge(x+3, x+3 , 8, 9 , 'General Manager Signature ')
        sheet1.write_merge(x+4, x+4 , 8, 9 , '..................')
        
        sheet1.col(0).width = 35 * 70
        sheet1.col(1).width = 35 * 120
        sheet1.col(2).width = 35 * 85
        sheet1.col(3).width = 35 * 100
        sheet1.col(4).width = 35 * 105
        sheet1.col(9).width = 35 * 150
        sheet1.col(10).width = 35 * 110
        sheet1.col(11).width = 35 * 115
        
        report = book.save('/tmp//Salary-Report.xls')
        return True
    
        
    def get_payslip_lines(self):
        sort_on = self.sort_on
        sort_type = self.sort_type
         
        state_domain = self.state
        if self.state == 'all':
            state_domain = ['done','draft']
        
        all_employee_ids = self.employee_ids.ids
        payslip_obj = self.env['hr.payslip']
        payslip_line_obj = self.env['hr.payslip.line']
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        employee_ids = employee_obj.search([])
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
                 
        if sort_on != 'salary':
            employee_ids = employee_ids.ids
        for employee in employee_ids:
            payslips = payslip_obj.search([('date_to','<=',self.to_date),
                                                                 ('date_from','>=',self.from_date),
                                                                 ('employee_id','=',employee),
                                                                 ('state','=',state_domain)])
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