# -*- coding: utf-8 -*-

import time
from odoo import models , api


class SalaryGosiReport(models.AbstractModel):
    _name = 'report.l10n_sa_hr_payroll.salary_gosi'
    
    totals = {'house_alw_total':0.0, 'trans_alw_total':0.0, 'food_alw_total':0.0,
                   'sanid_ded_total':0.0, 'sanid_cont_total':0.0, 'gosi_ded_total':0.0,
                   'gosi_cont_total':0.0, 'tot_ded_total':0.0, 'monthly_pay_gosi_total':0.0,
                   'hous_alw_total':0.0, 'other_ads_ot_total':0.0, 'other_addition_total':0.0,
                   'other_ded_total':0.0, 'monthly_pay_total':0.0, 'hazard_total':0.0, 'wage_total':0.0}

    def get_payslip_lines(self, form):
        payslip_obj = self.env['hr.payslip']
        contract_obj = self.env['hr.contract']
        payslip_line_obj = self.env['hr.payslip.line']
        res = []
        for employee in form['employee_ids']:
            payslips = payslip_obj.search([('date_to', '<=', form['to_date']),
                                                                 ('date_from', '>=', form['from_date']),
                                                                 ('employee_id', '=', employee),
                                                                 ('state', '=', 'done')])
            rejected_ids = []
            for slip in payslips:
                if slip.credit_note:
                    rejected_ids.append(slip.id)
                    if slip.refund_id:
                        rejected_ids.append(slip.refund_id.id)
                        
            for line in payslips:          
                if not line.id in rejected_ids:
                        
                  
                    
                    contract_ids = payslip_obj.get_contract(line.employee_id, form['from_date'], form['to_date'])
                    contract_record = contract_obj.browse(contract_ids[0])

                    payslip_lines_ids = payslip_line_obj.search([('slip_id', '=', line.id)])
                    value = {'employee_number':line.employee_id.employee_no or '', 'gosi_number':line.employee_id.gosi_number or '',
                             'name':line.employee_id.name, 'id_number':line.employee_id.identification_id, 'national_name':line.employee_id.country_id.name or '',
                            'job_name':line.employee_id.job_id.name or '',
                             'wage':'', 'iqama':line.employee_id.iqama_no or '', 'house_alw':0.0, 'trans_alw':0.0, 'food_alw':0.0,
                             'sanid_cont':0.0, 'sanid_ded':0.0, 'gosi_cont':0.0, 'gosi_ded':0.0, 'hazard_amount':0.0,
                             'other_ded':0.0, 'monthly_pay':0.0, 'other_ads_ot':0.0, 'other_addition':0.0,
                             'monthly_pay_gosi':0.0, 'tot_ded':0.0}
                    
                    if contract_record:
                        value['wage'] = contract_record.wage
                        self.totals['wage_total'] += contract_record.wage
                        
                    for pLine in payslip_lines_ids:
                        if pLine.code == 'NET':
                            value['monthly_pay'] = pLine.total
                            self.totals['monthly_pay_total'] += pLine.total
                        elif pLine.code == 'HOA':
                            value['house_alw'] = pLine.total
                            self.totals['house_alw_total'] += pLine.total
                        elif pLine.code == 'OT':
                            value['other_ads_ot'] = pLine.total
                            self.totals['other_ads_ot_total'] += pLine.total
                        elif pLine.code == 'OA':
                            value['other_addition'] = pLine.total
                            self.totals['other_addition_total'] += pLine.total
                        elif pLine.code == 'OD':
                            value['other_ded'] = pLine.total
                            self.totals['other_ded_total'] += pLine.total
                        elif pLine.code == 'GOSI':
                            value['gosi_ded'] = pLine.total
                            self.totals['gosi_ded_total'] += pLine.total
                        elif pLine.code == 'GOSIC':
                            value['gosi_cont'] = pLine.total
                            self.totals['gosi_cont_total'] += pLine.total
                        elif pLine.code == 'OHG':
                            value['hazard_amount'] = pLine.total
                            self.totals['hazard_total'] += pLine.total
                        elif pLine.code == 'SG':
                            value['sanid_cont'] = pLine.total
                            self.totals['sanid_cont_total'] += pLine.total
                        elif pLine.code == 'SGD':
                            value['sanid_ded'] = pLine.total
                            self.totals['sanid_ded_total'] += pLine.total
                        elif pLine.code == 'TA':
                            value['trans_alw'] = pLine.total
                            self.totals['trans_alw_total'] += pLine.total
                        elif pLine.code == 'FA':
                            value['food_alw'] = pLine.total
                            self.totals['food_alw_total'] += pLine.total
                            
                    value['tot_ded'] = value['gosi_ded'] + value['other_ded'] 
                    self.totals['tot_ded_total'] += value['tot_ded'] 
                    value['monthly_pay_gosi'] = value['gosi_ded'] + value['gosi_cont'] 
                    self.totals['monthly_pay_gosi_total'] += value['monthly_pay_gosi']

                    res.append(value)
        return res 
    
    def get_totals(self):
        return self.totals
    
    @api.model
    def get_report_values(self, docids, data=None):
        return {
            'data':data,
            'time': time,
            'payslipLines': self.get_payslip_lines,
            'get_totals': self.get_totals,
        }
    
