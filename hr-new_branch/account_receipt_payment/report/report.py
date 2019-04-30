# -*- coding: utf-8 -*-
from openerp import pooler
import time
from openerp.osv import osv
from openerp.report import report_sxw

class payment_receipt(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(payment_receipt, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
                                  'time': time,
                                  'getLines': self._lines_get,
                                  'getLang' : self.get_language(),
                                  'getCustomerName': self.get_customer_name,
                                  })
        self.context = context
    
    def _lines_get(self, voucher):
        voucherline_obj = pooler.get_pool(self.cr.dbname).get('account.voucher.line')
        voucherlines = voucherline_obj.search(self.cr, self.uid, [('voucher_id', '=', voucher.id)])
        voucherlines = voucherline_obj.browse(self.cr, self.uid, voucherlines)
        return voucherlines
    
    def get_language(self):
        current_user = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        if current_user['partner_id']['lang'] in ['ar_SY']:
            lang = "table_ar"
        else:
            lang = "table_en"
        return lang
    
    def get_customer_name(self, voucher, customer):
        if customer:
            if customer.parent_id:
                name = customer.parent_id.name + ', ' + customer.name
            else:
                name = customer.name
        else:
            name = voucher.partner_name
        return {'name': name}
    
   
   
class payment_receipt_report(osv.AbstractModel):
    _name = 'report.sw_account_receipt_payment.payment_receipt'
    _inherit = 'report.abstract_report'
    _template = 'sw_account_receipt_payment.payment_receipt'
    _wrapped_report_class = payment_receipt

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
