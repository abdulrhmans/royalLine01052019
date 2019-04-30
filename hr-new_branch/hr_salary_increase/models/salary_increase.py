from odoo import models, fields, api, _
from odoo.exceptions import UserError 
from email.policy import default

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    
    sih_ids = fields.One2many('hr.salary.increase.history','contract_id','Salar Increase History')

class SiHistory(models.Model):
    _name="hr.salary.increase.history"

    employee_id = fields.Many2one('hr.employee','Employee')
    si_id = fields.Many2one('hr.salary.increase.employee')
    si_line_id = fields.Many2one('hr.salary.increase.line')
    contract_id = fields.Many2one('hr.contract','Contract')
    wage = fields.Float('New Wage',related="si_line_id.wage_after_increase",store=True,readonly=True)
    old_wage = fields.Float('Wage',related="si_line_id.wage",store=True,readonly=True)
    amount_percentage = fields.Float('Amount/Percentage')
    job_id = fields.Many2one('hr.job','Job')
    department_id = fields.Many2one('hr.department','Department')
    increase_method = fields.Selection([('percentage','Percentage'),('amount','Amount')],store=True, readonly=True,related="si_id.increase_method")
    date = fields.Date('Date', related="si_id.date",store=True,readonly=True)
    
class SiLine(models.Model):
    _name="hr.salary.increase.line"

    employee_id = fields.Many2one('hr.employee','Employee', required=True)
    amount_percentage = fields.Float('Amount/Percentage', required=True ,default=lambda self: self.si_id.amount_percentage)
    job_id = fields.Many2one('hr.job','Job',copy=False, default=lambda self: self.employee_id.job_id.id)
    department_id = fields.Many2one('hr.department','Department',copy=False, default=lambda self: self.employee_id.department_id.id)
    si_id = fields.Many2one('hr.salary.increase.employee',copy=False)
    wage = fields.Float('wage',compute='_get_wage',store=True,copy=False)
    wage_after_increase = fields.Float('Wage After Increase',compute="_get_wage_after_increase",store=True,copy=False)
    contract_id = fields.Many2one('hr.contract','Contract',compute="_get_contract_id",store=True,copy=False)
    
    _sql_constraints = [('employee_id_uniq', 'unique(employee_id, si_id)', 'You can not have the same employee twice.'),]
    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id or False
            self.department_id = self.employee_id.department_id.id or False
        else:
            self.job_id = False
            self.department_id = False
        self.amount_percentage = self.si_id.amount_percentage
    
    @api.depends('employee_id')
    def _get_contract_id(self):
        contract_obj = self.env['hr.contract']
        for rec in self:
            if rec.employee_id:
                contract_id = contract_obj.search([('employee_id','=',rec.employee_id.id),
                                                  ('state','in',['open','pending']),
                                                  ('company_id','=',self.env.user.company_id.id)])
                if len(contract_id) > 1:
                    raise UserError('The employee %s  have more than one contract with status Running or  To renew'%rec.employee_id.name)
                elif not contract_id:
                    raise UserError('The employee %s does not have a running contract.'%rec.employee_id.name)
                rec.contract_id = contract_id.id
            
    @api.depends('employee_id','contract_id')
    def _get_wage(self):
        for rec in self:
            rec.wage = rec.contract_id.wage if rec.contract_id else False
    
    @api.multi
    @api.depends('wage','si_id.increase_method','amount_percentage')
    def _get_wage_after_increase(self):
        for rec in self:
            if not rec.si_id.increase_method:
                rec.wage_after_increase = 0.0
            rec.wage_after_increase = rec.wage + (rec.amount_percentage if rec.si_id.increase_method == 'amount' else rec.wage * rec.amount_percentage /100 )
    
    @api.model
    def create(self, vals):
        res = super(SiLine, self).create(vals)
        if (res.amount_percentage > 100  or res.amount_percentage < 1) and res.si_id.increase_method == 'percentage':
            raise UserError(_('Percentage must be between 1 and  100 .'))
        elif res.amount_percentage < 0:
                raise UserError(_('Amount/Percentage must be greater than 0.'))
        return res
    
    @api.multi
    def write(self, vals):
        res = super(SiLine, self).write(vals)
        for rec in self:
            if (rec.amount_percentage > 100  or rec.amount_percentage < 1) and rec.si_id.increase_method == 'percentage':
                raise UserError(_('Percentage must be between 1 and  100 .'))
            elif rec.amount_percentage < 0:
                raise UserError(_('Amount/Percentage must be greater than 0.'))
            
        return res
    
class SalaryIncrease(models.Model):
    _name = "hr.salary.increase.employee"
    _description = "Salary Increase"
    _inherit = ['mail.thread']
    
    name = fields.Char('Name', required=True,track_visibility='onchange')
    amount_percentage = fields.Float('Amount/Percentage', required=True,track_visibility='onchange')
    date = fields.Date('Date', required=True,default=fields.Date.today(),copy=False,track_visibility='onchange')
    note = fields.Text('Note',copy=False,track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'), ('refuse', 'Refused') ,('confirmed', 'Confirmed'),('approved', 'Approved')], string='State',default='draft',copy=False,track_visibility='onchange')
    si_line_ids = fields.One2many('hr.salary.increase.line','si_id','Employees',copy=True,track_visibility='onchange')
    increase_method = fields.Selection([('percentage','Percentage'),('amount','Amount')], required=True,default='percentage',track_visibility='onchange')
    company_id = fields.Many2one('res.company',string="Company",default= lambda self: self.env.user.company_id.id)
   
    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        res = super(SalaryIncrease, self).create(vals)
        add_follower = self.env['mail.wizard.invite'].create({'res_model':self._name,'res_id':res.id,
                                           'partner_ids':[(4,id) for id in self.env.user.company_id.users_to_notify_ids.mapped('partner_id.id')]})
        add_follower.add_followers()
        return res
        
        
        
    def clear_employee(self):
        self.si_line_ids.unlink()
    

    @api.multi
    def unlink(self):
        for rec in self:
            print( rec.state)
            if rec.state in ['approved','confirmed'] :
                raise UserError(_("You Can not delete confirmed or approved salary increase."))
        return super(SalaryIncrease,self).unlink()
    
        
    def get_employee_contract(self ,cr ,uid ,employee ,date ,context=None):
        payslip_obj = self.pool.get('hr.payslip')
        contract_id = payslip_obj.get_contract(cr, uid, employee, date, date)
        if contract_id:
            return self.pool.get('hr.contract').browse(cr ,uid ,contract_id)[0]
        else:
            raise except_orm(_('Error!'),
                     _('Employee dose not have valid contract '+unicode(employee.name)+'!'))
     
    
    @api.multi
    def refuse_si(self):
        self.write({'state': 'refuse'})
   
    @api.multi
    def confirm_si(self):
        for si in self:
            if not si.si_line_ids:
                raise UserError(_('Please add employees first.'))
        self.write({'state': 'confirmed'})
    
    def approve_si(self):
        
        history = self.env['hr.salary.increase.history']
        line_obj = self.env['hr.salary.increase.line']
        for si in self:
            if not si.si_line_ids:
                raise UserError(_('Please add employees first.'))
            for line in si.si_line_ids:
                line.contract_id.wage = line.wage_after_increase
                # create history
                vals = {'si_id': si.id,
                        'si_line_id':line.id,
                        'contract_id':line.contract_id.id,
                        'employee_id':line.employee_id.id,
                        'amount_percentage':line.amount_percentage,
                        'department_id':line.department_id.id or False,
                        'job_id':line.job_id.id or False,
                        
                        }
                self.env['hr.salary.increase.history'].create(vals)                    
                        
        self.write({'state': 'approved'})
    
    
        
    
    
        
        