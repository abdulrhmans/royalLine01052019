# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class RegisterSalesPayment(models.TransientModel):

    _name = "register.account.payment"
    _description = "Register Account Payments"

    @api.model
    def _get_partner(self):
        if self._context.get('active_id'):
            partner_id = self.env['sale.order'].browse(self._context.get('active_id')).partner_id.id
        return partner_id or False
    
    @api.model
    def _get_saleorder_name(self):
        if self._context.get('active_id'):
            sale_origin = self.env['sale.order'].browse(self._context.get('active_id')).name
        return sale_origin or ''

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, default=_get_partner)
    journal_id = fields.Many2one('account.journal', string='Payment Method', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type')
    amount = fields.Float(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    communication = fields.Char(string='Memo', default=_get_saleorder_name)
    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0:
            raise ValidationError('The payment amount must be strictly positive.')

    @api.one
    @api.depends('journal_id')
    def _compute_hide_payment_method(self):
        if not self.journal_id:
            self.hide_payment_method = True
            return
        journal_payment_methods = self.journal_id.outbound_payment_method_ids
        self.hide_payment_method = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            payment_methods = self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            return {'domain': {'payment_method_id': [('payment_type', '=', 'outbound'), ('id', 'in', payment_methods.ids)]}}
        return {}

    def get_payment_vals(self):
        """ Hook for extension """
        return {
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'sale_order_id': self.env['sale.order'].browse(self._context.get('active_id', [])).id
        }

    def register_payment(self):
        self.ensure_one()
        payment = self.env['account.payment'].create(self.get_payment_vals())
        payment.post()
        return {'type': 'ir.actions.act_window_close'}
