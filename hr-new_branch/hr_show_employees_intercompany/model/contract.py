# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    @api.model_cr
    def init(self):
        '''
            Remove record rules of employees and contracts to allow the user to see all employees in all companies and their contracts
        '''
        emp_rr = self.env.ref('hr_payroll_enhancement.hr_employee_rule', False)
        if emp_rr:
            emp_rr.unlink()
            
        cont_rr = self.env.ref('hr_payroll_enhancement.hr_contract_rule', False)
        if cont_rr:
            cont_rr.unlink()
            
        department_rr = self.env.ref('hr.hr_dept_comp_rule', False)
        if department_rr:
            department_rr.unlink()
            
        job_rr = self.env.ref('hr.hr_job_comp_rule', False)
        if job_rr:
            job_rr.unlink()