# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

class Banks(models.Model):
    _inherit = 'res.bank'
    
    bic = fields.Char('Bank Identifier Code', help="Sometimes called BIC or Swift.", size=3)
    
    def _check_bic(self):
        current_bank = self
        self._cr.execute("select name from res_bank where bic ilike '%s';" % str(current_bank.bic))
        res = self._cr.fetchall()

        if len(res) > 1:
            return False
        return True
     
    _constraints = [(_check_bic, 'Code already exist.', ['bic'])]
    
    
class Company(models.Model):
    _inherit = 'res.company'
    
    max_relay_days = fields.Float('Max. Relay Days')
    deduct_friday_in_leave =  fields.Boolean(string="Deduct friday in the leaves", default=True)
    
class HrBanks(models.Model):
    _name = 'hr.bank'
    
    name = fields.Char('Bank Name')
    code = fields.Char('Bank Short Name', help="Sometimes called BIC or Swift.", size=10)
    branch_lines = fields.One2many('hr.bank.branch', 'bank_id', 'Branches')
    
    @api.one
    @api.constrains('name', 'code')
    def _check_Bank(self):
      
        name_st="'"+str(self.name)+"'"
        code_st="'"+str(self.code)+ "'"
     
        self._cr.execute('SELECT id FROM hr_bank WHERE name = '+ name_st +' AND code = '+code_st+' AND id != '+str(self.id) )
        res = self._cr.fetchall()
       
        if res and res[0]:
            raise except_orm(_('User Error'),_('Bank already exist!'))  

class HrBanksBranches(models.Model):
    _name = 'hr.bank.branch'
    _description = 'HR Branches'
    
    name = fields.Char('Name', required=True) 
    bank_id = fields.Many2one('hr.bank', 'bank')
        
        
        
        
        
        
        
        
    
    