# -*- coding: utf-8 -*-
import time
from openerp.report import report_sxw
from openerp import pooler
from openerp.osv import osv
from openerp.exceptions import except_orm
from openerp.tools.translate import _

class check(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(check, self).__init__(cr, uid, name, context=context)
        self.posTotals = {}
        self.localcontext.update( 
                                  {
                                   'time': time,
                                   'get_amount': self._get_amount,
                                   'get_check': self._get_check,
                                   'check_all': self._check_all,
                                  }
                                )
        self.context = context
    
    
    def _check_all(self, check):
        if check.type != 'payment':
            raise except_orm(_('User Error'),_("You must choose from supplier payments only!"))
        if not check.is_check:
            raise except_orm(_('User Error'),_("You must choose check payment only!"))
        
    
    def _get_check(self, check_id):
        check = self.pool.get('account.check').browse(self.cr ,self.uid ,check_id)
        return check
        
    def _get_amount(self, amount):
        amount_list = str(amount).split('.')
        if len(amount_list) > 1:
            l2 = amount_list[1]
            if len(l2) == 1:
                amount_list[1] = l2+'00'
            elif len(l2) == 2:
                amount_list[1] = l2+'0'
        return amount_list
    
class check_abstract(osv.AbstractModel):
    _name = 'report.sw_account_check.check'
    _inherit = 'report.abstract_report'
    _template = 'sw_account_check.check'
    _wrapped_report_class = check
    