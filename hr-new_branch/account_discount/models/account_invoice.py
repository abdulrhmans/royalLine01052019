# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    discount_percentage_amount = fields.Float('Discount (%) (0~100)',digits=dp.get_precision('Discount'), states={'draft': [('readonly', False)]})
    discount_amount = fields.Float(string='Total Amount Discounted',compute='_get_discount_amount', digits=dp.get_precision('Account'))
    
    @api.model
    def create(self, vals):
        discount_amount = vals.get('discount_percentage_amount',0.0)
        if vals.get('invoice_line_ids',False) or vals.get('discount_percentage_amount'):
            if vals.get('invoice_line_ids',False):
                for line in vals['invoice_line_ids']:
                    if type(line[2]) is dict:
                        if line[2].get('price_unit',0) > 0:
                            line[2]['discount'] = discount_amount
                            
        res = super(AccountInvoice,self).create(vals)
        return res
    
    @api.one
    def write(self, vals):
        discount_amount = vals.get('discount_percentage_amount', self.discount_percentage_amount)
        group1 = self.env.ref('account_discount.group_both_use_discount')
        group2 = self.env.ref('account_discount.group_percent_use_discount')
        if vals.get('invoice_line_ids',False) or vals.get('discount_percentage_amount'):
            if vals.get('invoice_line_ids',False):
                for line in vals['invoice_line_ids']:
                    if type(line[2]) is dict:
                        if line[2].get('price_unit',0) > 0:
                            line[2]['discount'] = discount_amount

            recs = self.invoice_line_ids.search([('invoice_id', '=', self.id), ('price_unit','>',0)])
            for rec in recs:
                if (group1 or group2 in self.env.user.groups_id) and rec.fix_discount > 0.0:
                    rec.write({'discount':0.0})
                else:
                    rec.write({'discount':discount_amount})
        res = super(AccountInvoice,self).write(vals)
        return res
    
    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0) - ((line.fix_discount/(line.quantity or 1)) if line.price_unit else 0.0)
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.one
    @api.depends('discount_percentage_amount', 'amount_total', 'invoice_line_ids.fix_discount')
    def _get_discount_amount(self):
        discount_lines = 0.0 
        neg_discount = 0.0
        group1 = self.env.ref('account_discount.group_both_use_discount')
        group2 = self.env.ref('account_discount.group_percent_use_discount')
        for line in self.invoice_line_ids:
            if line.fix_discount > 0.0 and (group1 or group2 in self.env.user.groups_id):
                discount_lines += line.fix_discount
                continue
            else:
                if line.price_unit > 0:
                    discount_lines += ((line.price_unit * line.quantity) * (line.discount/100))
                else:
                    neg_discount += (line.price_unit * line.quantity * -1)
                
        self.discount_amount = discount_lines + neg_discount
 
    @api.onchange('discount_percentage_amount')
    def discount_onchange(self):
        if self.discount_percentage_amount > 100 or self.discount_percentage_amount < 0.0:
            raise UserError(_("Range must between (0~100)"))
        if self.discount_percentage_amount == 0.0:
            for rec in self.invoice_line_ids:
                rec.discount = 0.0
    
    
class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity','fix_discount',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0) - ((self.fix_discount/(self.quantity or 1)) if self.price_unit else 0.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
    
    fix_discount = fields.Float('Discount')
    discount_percentage_amount = fields.Float(related='invoice_id.discount_percentage_amount', string='Discount Amount', store=False)
    