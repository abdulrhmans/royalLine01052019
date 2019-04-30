# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    amount = fields.Monetary(string='Payment Amount', required=False)
    
    partner_name = fields.Char('Partner Name', track_visibility='onchange', readonly=True, states={'draft':[('readonly',False)]}, copy=True)
    
    receipt_lines = fields.One2many('account.payment.receipt.line','payment_id', string="Receipt Lines", 
                                    track_visibility='onchange', readonly=True, states={'draft':[('readonly',False)]}, copy=True)
    
    payment_lines = fields.One2many('account.payment.order.line','payment_id', string="Receipt Lines", 
                                    track_visibility='onchange', readonly=True, states={'draft':[('readonly',False)]}, copy=True)
    
    non_contact = fields.Boolean('Not a Contact', readonly=True, states={'draft':[('readonly',False)]}, default=False, copy=True)
    
    account_type_ids = fields.Many2many('account.account.type',string='Account Types Payment Filter',related='journal_id.type_control_ids')
    
    account_id = fields.Many2one('account.account', string="Account", copy=True)
    
    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if self.amount <= 0:
            raise ValidationError(_('The payment amount cannot be negative or zero.'))


    @api.model
    def _set_partner_name(self):
        self._cr.execute("update account_payment set partner_name= tt.name " 
                        "from (select ap.id as id,rp.name as name from account_payment ap "
                        "left join  res_partner as rp on rp.id=ap.partner_id ) tt "
                        "where tt.id=account_payment.id")
        
    @api.onchange('journal_id')
    def _onchange_journal(self):
        res = super(AccountPayment, self)._onchange_journal()
        if self.non_contact:
            if self.partner_type == 'customer':
                self.account_id = self.journal_id.default_debit_account_id.id if self.journal_id.default_debit_account_id else False
            elif self.partner_type == 'supplier':
                self.account_id = self.journal_id.default_credit_account_id.id if self.journal_id.default_credit_account_id else False
        return res
        
    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if not self.invoice_ids:
            if self.payment_type == 'transfer':
                self.partner_type = False
            else:
                self.partner_type = self._context['default_partner_type'] if 'default_partner_type' in self._context else False
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        journal_types.update(['bank', 'cash'])
        res['domain']['journal_id'] = jrnl_filters['domain'] + [('type', 'in', list(journal_types))]
        return res
    
    @api.onchange('non_contact')
    def _onchange_nont_contact(self):
        if self.non_contact:
            self.partner_id = False
            if self.journal_id:
                if self.partner_type == 'customer':
                    self.account_id = self.journal_id.default_debit_account_id.id if self.journal_id.default_debit_account_id else False
                elif self.partner_type == 'supplier':
                    self.account_id = self.journal_id.default_credit_account_id.id if self.journal_id.default_credit_account_id else False
    
    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id', 'account_id')
    def _compute_destination_account_id(self):
        if not self.invoice_ids and self.payment_type != 'transfer' and not self.partner_id:
            if hasattr(self, 'is_check'):
                if not self.is_check:
                    self.destination_account_id = self.account_id.id if self.account_id else False
            else:
                self.destination_account_id = self.account_id.id if self.account_id else False
        else:
            return super(AccountPayment, self)._compute_destination_account_id() 
    
        
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
        
    @api.model
    def create(self, vals):
        res = super(AccountPayment,self).create(vals)
        if res.partner_id and not res.partner_name:
            res.partner_name = res.partner_id.name
        if res.non_contact:
            if res.partner_type == 'customer':
                amount = 0.0
                for l in res.receipt_lines:
                    amount += l.amount
                res.amount = amount
            if res.partner_type == 'supplier':
                amount = 0.0
                for l in res.payment_lines:
                    amount += l.amount
                res.amount = amount
        if res.payment_type == 'transfer':
            res.non_contact = False
        return res
    
    @api.multi
    def write(self, vals):
        res = super(AccountPayment,self).write(vals)
        if 'receipt_lines' in vals or 'payment_lines' in vals or 'non_contact' in vals:
            for payment in self:
                if payment.partner_type == 'customer':
                    amount = 0.0
                    for l in payment.receipt_lines:
                        amount += l.amount
                    payment.amount = amount
                if payment.partner_type == 'supplier':
                    amount = 0.0
                    for l in payment.payment_lines:
                        amount += l.amount
                    payment.amount = amount
        if 'payment_type' in vals:
            for payment in self:
                if vals['payment_type'] == 'transfer':
                    payment.non_contact = False
        return res
    
    @api.multi
    def post(self):
        for rec in self:
            if rec.non_contact:
                if rec.state != 'draft':
                    raise UserError(_("Only a draft payment can be posted."))
    
                if any(inv.state != 'open' for inv in rec.invoice_ids):
                    raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
    
    
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
                        
                        
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
    
                # Create the journal entry
                amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
                
                if rec.partner_type == 'customer':
                    if not rec.receipt_lines:
                        raise UserError(_('Please fill the table!'))
                    move = rec.create_receipt_voucher_entries(amount)
                
                if rec.partner_type == 'supplier':
                    if not rec.payment_lines:
                        raise UserError(_('Please fill the table!'))
                    move = rec.create_payment_order_entries(amount)
                
                move.post()
                rec.write({'state': 'posted', 'move_name': move.name})
            else:
                rec.receipt_lines.unlink()
                rec.payment_lines.unlink()
                super(AccountPayment, self).post()

     
    def create_receipt_voucher_entries(self, amount):
        move_pool = self.env['account.move']
        aml_obj = self.env['account.move.line']
        line_ids = []
        company_id = self.env.user.company_id.id
        move = self.env['account.move'].create(self._get_move_vals())
          
        total_amount = 0.0
        total_amount_currency = 0.0
        for line in self.receipt_lines: 
            if not self.currency_id.is_zero(line.amount):
                if not self.currency_id != self.company_id.currency_id:
                    amount_currency = 0
                
                debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(line.amount, self.currency_id, self.company_id.currency_id, False)
                total_amount += credit or debit
                total_amount_currency += amount_currency
                liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-line.amount))
                liquidity_aml_dict.update({'account_id': line.account_id.id, 'company_id': company_id, 'name': line.memo or '/'})
                line_ids.append((0, 0, liquidity_aml_dict ))
        
        debit_1, credit_1, amount_currency_1, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(total_amount, self.currency_id, self.company_id.currency_id, False)
        counterpart_aml_dict = self._get_shared_move_line_vals(debit_1, credit_1, amount_currency_1, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id, 'company_id': company_id, 'ref': self.communication,
                                     'amount_currency': total_amount_currency})
        
        if 'debit' in counterpart_aml_dict and counterpart_aml_dict['debit']:
            counterpart_aml_dict['debit'] = total_amount
        else:
            counterpart_aml_dict['credit'] = total_amount
            
        line_ids.append((0, 0, counterpart_aml_dict ))
        
        if self.payment_type == 'outbound':
            for l in line_ids:
                dr = l[2]['debit']
                crd = l[2]['credit']
                l[2]['debit'] = crd
                l[2]['credit'] = dr
                l[2]['amount_currency'] = l[2]['amount_currency']*-1 
        
        move.line_ids = line_ids
        return move
    
    def create_payment_order_entries(self, amount):
        move_pool = self.env['account.move']
        aml_obj = self.env['account.move.line']
        line_ids = []
        company_id = self.env.user.company_id.id
        move = self.env['account.move'].create(self._get_move_vals())
          
        total_amount = 0.0
        total_amount_currency = 0.0
        for line in self.payment_lines: 
            if not self.currency_id.is_zero(line.amount):
                if not self.currency_id != self.company_id.currency_id:
                    amount_currency = 0
                
                debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(line.amount*-1, self.currency_id, self.company_id.currency_id, False)
                total_amount += credit or debit
                total_amount_currency += amount_currency
                liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -1*amount_currency, move.id, False)
                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(line.amount))
                liquidity_aml_dict.update({'account_id': line.account_id.id, 'company_id': company_id, 'name': line.memo or '/', 'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else False})
                line_ids.append((0, 0, liquidity_aml_dict ))
        
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, False)
        
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id, 'company_id': company_id,'ref': self.communication,
                                     'amount_currency': total_amount_currency, 'credit': total_amount, 'debit': 0.0})
        line_ids.append((0, 0, counterpart_aml_dict ))
        
        if self.payment_type == 'inbound':
            for l in line_ids:
                dr = l[2]['debit']
                crd = l[2]['credit']
                l[2]['debit'] = crd
                l[2]['credit'] = dr
                l[2]['amount_currency'] = l[2]['amount_currency']*-1 
        
        
        move.line_ids = line_ids
        
        return move

    
class ReceiptLines(models.Model):
    _name = "account.payment.receipt.line"
    _description = 'Receipt Lines'
    
    payment_id = fields.Many2one('account.payment')
    account_id = fields.Many2one('account.account','Account')
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id, related="payment_id.currency_id")
    memo = fields.Char('Memo', default='/')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    
    
class PaymentLines(models.Model):
    _name = "account.payment.order.line"
    _description = 'Payment Lines'
    
    payment_id = fields.Many2one('account.payment')
    account_id = fields.Many2one('account.account','Account')
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id, related="payment_id.currency_id")
    memo = fields.Char('Memo', default='/')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
              