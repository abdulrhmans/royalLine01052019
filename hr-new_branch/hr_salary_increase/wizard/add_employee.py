# -*- coding: utf-8 -*-
from odoo import models, api,fields

class AddEmployee(models.TransientModel):
    _name = "add.employee"
    
    
    employee_ids = fields.Many2many('hr.employee')
    
    def add_employee(self):
        ctx = self.env.context.copy()
        si_id = self.env['hr.salary.increase.employee'].browse(ctx.get('active_ids',[]))
        vals=[]
        for emp in self.employee_ids:
            vals.append((0,0,{'employee_id':emp.id,
                              'department_id':emp.department_id.id or False,
                              'job_id':emp.job_id.id or False,
                              'amount_percentage':si_id.amount_percentage}))
            
        
        si_id.write({'si_line_ids':vals})   
        
        return {'type': 'ir.actions.act_window_close'}
