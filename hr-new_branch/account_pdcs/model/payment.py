# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time

class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    bank_id = fields.Many2one('pdc.config', 'Bank', track_visibility='onchange', readonly=True, states={'draft':[('readonly',False)]}, copy=True)
    is_check = fields.Boolean('Bank Cheque', track_visibility='onchange', readonly=True, states={'draft':[('readonly',False)]}, default=False, copy=True)
    due_date = fields.Date('Due Date', copy=True)
    check_ref = fields.Char('Cheque Reference', copy=True)
    send_to_bank_date = fields.Date('Send to Bank Date', track_visibility='onchange', copy=True)
    transfer_check = fields.Boolean('Transfer to Cheques Box', track_visibility='onchange', readonly=True, states={'draft':[('readonly',False)]}, default=False, copy=False)
    
    internal_number_pdc = fields.Char('PDC Received Entry #', track_visibility='onchange', copy=False)
    internal_number_collect = fields.Char('Collection Entry #', track_visibility='onchange', copy=False)
    collect_date = fields.Date('Collection Date', track_visibility='onchange', copy=False)
    hide_send_bank_button = fields.Boolean("Hide Send To Bank Button", default=False, copy=False)
    
    refused = fields.Boolean("Returned", default=False, copy=False)
    
    pdc_move_id = fields.Many2one('account.move', 'PDC Account Move', track_visibility='onchange', copy=False)
    collect_move_id = fields.Many2one('account.move', 'Collect Account Move', track_visibility='onchange', copy=False)
    
    inverse_pdc_move_id = fields.Many2one('account.move', 'Refused PDC Account Move', track_visibility='onchange', copy=False)
    inverse_collect_move_id = fields.Many2one('account.move', 'Refused Collect Account Move', track_visibility='onchange', copy=False)
    inverse_move_id = fields.Many2one('account.move', 'Refused Account Move', track_visibility='onchange', copy=False)
    
    cus_check_state = fields.Selection([('in_cheque_box','In Cheques Box'),
                                       ('under_collection','Under Collection'),
                                       ('refused','Refused'),
                                       ('collected','Collected')], string='Cheque Status', 
                                       track_visibility='onchange', readonly=True, copy=False)
    
    
    
    sup_check_state = fields.Selection([('issued','Issued'),
                                       ('refused','Refused'),
                                       ('collected','Collected')], string='Cheque Status', 
                                       track_visibility='onchange', readonly=True, copy=False)
    
    amount_to_text = fields.Char('Amount to Text')
    check_note = fields.Char('Cheque Note', copy=True)
    
    @api.onchange('due_date')
    def _onchange_due_date(self):
        self.collect_date = self.due_date
    
    
    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id', 'is_check', 'account_id', 'bank_id')
    def _compute_destination_account_id(self):
        if not self.invoice_ids and self.payment_type != 'transfer' and not self.partner_id:
            if self.is_check:
                if self.partner_type == 'customer':
                    self.destination_account_id = self.bank_id.box_account.id
                else:
                    self.destination_account_id = self.bank_id.pdc_issued_account.id
            else:
                self.destination_account_id = self.account_id.id if self.account_id else False
        else:
            return super(AccountPayment, self)._compute_destination_account_id()
        
    def _get_move_vals(self, journal=None):
        res = super(AccountPayment, self)._get_move_vals(journal=journal)
        if self.is_check:
            res['ref'] = res['ref'] + ' - Cheque # '+str(self.check_ref)
        return res
        
    
    def create_receipt_voucher_entries(self, amount):    
        move = super(AccountPayment, self).create_receipt_voucher_entries(amount)
        if self.is_check:
            move.ref = move.ref + ' - Cheque # '+str(self.check_ref)
        return move    
    
    def create_payment_order_entries(self, amount):    
        move = super(AccountPayment, self).create_payment_order_entries(amount)
        if self.is_check:
            move.ref = move.ref + ' - Cheque # '+str(self.check_ref)
        return move
    
    
    
    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        
        for rec in self:
            if rec.is_check and rec.partner_type == 'customer':
                if not rec.non_contact:
                    self._cr.execute("update account_move_line set account_id='"+str(rec.bank_id.box_account.id)+"' where id in "+str(tuple(rec.move_line_ids.mapped('id')))+" and account_id != "+str(rec.destination_account_id.id))
                rec.write({'cus_check_state': 'in_cheque_box'})
            elif rec.is_check and rec.partner_type == 'supplier':
                if not rec.non_contact:
                    self._cr.execute("update account_move_line set account_id='"+str(rec.bank_id.pdc_issued_account.id)+"' where id in "+str(tuple(rec.move_line_ids.mapped('id')))+" and account_id != "+str(rec.destination_account_id.id))
                rec.write({'sup_check_state': 'issued'})

        return res
    
    @api.multi
    def send_check(self):
        for payment in self:
            if not payment.bank_id:
                raise UserError(_('Please set the bank!'))
             
            if not payment.send_to_bank_date:
                raise UserError(_("Please set 'Send to Bank Date'!"))
             
            if payment.state == 'draft':
                payment.post()
                moves = self.env['account.move.line'].search([('payment_id','=',payment.id)]).mapped('move_id')
                move = moves[0]
                self._cr.execute("update account_move set date='"+str(payment.send_to_bank_date+"' where id="+str(move.id)))
                self._cr.execute("update account_move_line set date='"+str(payment.send_to_bank_date+"' where move_id="+str(move.id)))
                if not payment.non_contact:
                    self._cr.execute("update account_move_line set account_id='"+str(payment.bank_id.pdc_received_account.id)+"' where move_id="+str(move.id)+" and account_id != "+str(payment.destination_account_id.id))
                else:
                    self._cr.execute("update account_move_line set account_id='"+str(payment.bank_id.pdc_received_account.id)+"' where move_id="+str(move.id)+" and account_id = "+str(payment.destination_account_id.id))
            else:
                # Send to bank after (validate)
                move = self.create_send_to_bank_entry()
                if not payment.internal_number_pdc:
                    payment.write({'internal_number_pdc': move.name})
            payment.write({'cus_check_state': 'under_collection', 'hide_send_bank_button': True})
    
    
    def get_send_bank_move(self):
        seq_obj = self.env['ir.sequence']
        if self.internal_number_pdc:
            name = self.internal_number_pdc
        elif self.journal_id.sequence_id:
            if not self.journal_id.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
             
            name = self.journal_id.sequence_id.with_context(ir_sequence_date=self.send_to_bank_date).next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))
         
        if not self.check_ref:
            ref = name.replace('/','')
        else:
            ref = self.check_ref
 
        return {
            'name': name,
            'journal_id': self.journal_id.id,
            'date': self.send_to_bank_date,
            'ref': str(self.communication) + _(' - Cheque # ')+ ref,
        }
            
    def create_send_bank_move_line(self ,move_id ,account_id ,debit ,credit, je_currency_id, amount_currency):
        val = {
                'name': self.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': account_id,
                'move_id': move_id,
                'journal_id': self.journal_id.id,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'date': self.send_to_bank_date,
                'date_maturity': self.due_date,
                'currency_id': je_currency_id,
                'amount_currency': amount_currency,
            }
        return val
    
    def create_send_to_bank_entry(self):
        move_obj = self.env['account.move']
        move_line_pool = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        move = move_obj.create(self.get_send_bank_move())
         
        je_currency_id = False
        company_currency = self.company_id.currency_id
        currency_id = self.currency_id.id if self.currency_id else company_currency.id
        if company_currency.id != currency_id:
            je_currency_id = currency_id
        
        if company_currency.id != currency_id:
            amount_currency = self.amount
            paid_amount_in_company_currency = self.currency_id.with_context(self._context).compute(self.amount, company_currency)
        else:
            amount_currency = 0.0
            paid_amount_in_company_currency = self.amount
        
        dr_move_line = self.create_send_bank_move_line(move.id, self.bank_id.pdc_received_account.id, 
                                                                    paid_amount_in_company_currency, 0, je_currency_id, amount_currency)
        cr_move_line = self.create_send_bank_move_line(move.id, self.bank_id.box_account.id, 
                                                                    0, paid_amount_in_company_currency, je_currency_id, amount_currency*-1)

        line_ids = [(0,0, dr_move_line),(0,0, cr_move_line)]
        
        # We post the self.
        self.write({'pdc_move_id': move.id,})
        
        if self.payment_type == 'outbound':
            for l in line_ids:
                dr = l[2]['debit']
                crd = l[2]['credit']
                l[2]['debit'] = crd
                l[2]['credit'] = dr
                l[2]['amount_currency'] = l[2]['amount_currency']*-1 
        
        
        move.write({"line_ids": line_ids})
        
        move.post()
             
        return move
    
    
    def get_collect_move(self):
        seq_obj = self.env['ir.sequence']
        if self.internal_number_collect:
            name = self.internal_number_collect
        elif self.journal_id.sequence_id:
            if not self.journal_id.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
             
            name = self.journal_id.sequence_id.with_context(ir_sequence_date=self.collect_date).next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))
         
        if not self.check_ref:
            ref = name.replace('/','')
        else:
            ref = self.check_ref
 
        return {
            'name': name,
            'journal_id': self.journal_id.id,
            'date': self.collect_date,
            'ref': str(self.communication) + _(' - Cheque # ')+ ref,
        }
            
    def create_collect_move_line(self ,move_id ,account_id ,debit ,credit, je_currency_id, amount_currency):
        return {
                'name': self.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': account_id,
                'move_id': move_id,
                'journal_id': self.journal_id.id,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'date': self.collect_date,
                'date_maturity': self.due_date,
                'currency_id': je_currency_id,
                'amount_currency': amount_currency,
            }
        
    def collect_check(self):
        move_obj = self.env['account.move']
        currency_obj = self.env['res.currency']
        move_line_pool = self.env['account.move.line']
        if not self.collect_date:
            raise UserError(_("Please set 'Collection Date'!"))
        
        move = move_obj.create(self.get_collect_move())
         
         
        je_currency_id = False
        company_currency = self.company_id.currency_id
        currency_id = self.currency_id.id if self.currency_id else company_currency.id
        if company_currency.id != currency_id:
            je_currency_id = currency_id
             
        if company_currency.id != currency_id:
            amount_currency = self.amount
            paid_amount_in_company_currency = self.currency_id.with_context(self._context).compute(self.amount, company_currency)
        else:
            amount_currency = 0.0
            paid_amount_in_company_currency = self.amount
         
         
        if self.partner_type == 'customer':
            dr_move_line = self.create_collect_move_line(move.id, self.bank_id.bank_account.id,  
                                    paid_amount_in_company_currency, 0, je_currency_id, amount_currency)
            cr_move_line = self.create_collect_move_line(move.id, self.bank_id.pdc_received_account.id, 
                                    0, paid_amount_in_company_currency, je_currency_id, amount_currency*-1)
        elif self.partner_type == 'supplier':
            dr_move_line = self.create_collect_move_line(move.id, self.bank_id.pdc_issued_account.id, 
                                    paid_amount_in_company_currency, 0, je_currency_id, amount_currency)
            cr_move_line = self.create_collect_move_line(move.id, self.bank_id.bank_account.id, 
                                    0, paid_amount_in_company_currency, je_currency_id, amount_currency*-1)
        
        line_ids = [(0,0, dr_move_line),(0,0, cr_move_line)]
        
        # We post the voucher.
        self.write({
            'collect_move_id': move.id,
            'cus_check_state': 'collected',
            'sup_check_state': 'collected',
        })
        
        if (self.partner_type == 'customer' and self.payment_type == 'outbound') or (self.partner_type == 'supplier' and self.payment_type == 'inbound'):
            for l in line_ids:
                dr = l[2]['debit']
                crd = l[2]['credit']
                l[2]['debit'] = crd
                l[2]['credit'] = dr
                l[2]['amount_currency'] = l[2]['amount_currency']*-1 
        
        
        move.write({"line_ids": line_ids})
        move.post()
         
        if not self.internal_number_collect:
            self.write({'internal_number_collect': move.name})
                 
        return move
    
    @api.multi
    def cancel(self):
        result = super(AccountPayment, self).cancel()
        for payment in self:
            if payment.pdc_move_id:
                payment.pdc_move_id.line_ids.remove_move_reconcile()
                payment.pdc_move_id.button_cancel()
                payment.pdc_move_id.unlink()
                    
            if payment.collect_move_id:
                payment.collect_move_id.line_ids.remove_move_reconcile()
                payment.collect_move_id.button_cancel()
                payment.collect_move_id.unlink()
               
                    
        res = {
            'move_id':False,
            'collect_move_id':False,
            'pdc_move_id':False,
            'hide_send_bank_button':True,
            'cus_check_state': '',
            'sup_check_state': '',
        }
        self.write(res)
        return result
    
    @api.multi
    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        self.write({'hide_send_bank_button': False})
        return res
    
    
    @api.multi
    def refuse_check(self,):
        for payment in self:
            recs = []
            inverse_move_id = False
            inverse_pdc_move_id = False
            inverse_collect_move_id = False

            collect_data = payment.collect_date or False
            # create reverse entry for each entry exist on check
            move_ids = payment.move_line_ids.mapped('move_id')
            if payment.move_line_ids:
                inverse_move_id = payment.move_line_ids[0].move_id.reverse_moves(date= collect_data or payment.move_line_ids[0].move_id.date)[0]
                inverse_move = self.env['account.move'].browse(inverse_move_id)
                inverse_move.ref = inverse_move.ref + ' - Cheque # '+str(payment.check_ref)
            if payment.pdc_move_id:
                inverse_pdc_move_id = payment.pdc_move_id.reverse_moves(date= collect_data or payment.pdc_move_id.date)[0]
                inverse_pdc_move = self.env['account.move'].browse(inverse_pdc_move_id)
                inverse_pdc_move.ref = inverse_pdc_move.ref + ' - Cheque # '+str(payment.check_ref)
            if payment.collect_move_id:
                inverse_collect_move_id = payment.collect_move_id.reverse_moves(date=payment.collect_date)[0]
                inverse_collect_move = self.env['account.move'].browse(inverse_collect_move_id)
                inverse_collect_move.ref = inverse_collect_move.ref + ' - Cheque # '+str(payment.check_ref)
    
            res = {
                'state':'cancelled',
                'inverse_pdc_move_id':inverse_pdc_move_id,
                'inverse_collect_move_id':inverse_collect_move_id,
                'inverse_move_id':inverse_move_id,
                'refused':True,
                'hide_send_bank_button':True,
                'cus_check_state': 'refused',
                'sup_check_state': 'refused',
            }
            self.write(res)
        return True
    
    @api.multi
    def open_journal_entries(self):
        moves = self.env['account.move.line'].search([('payment_id','in',self.ids)]).mapped('move_id')
        move_ids = []
        if moves:
            move_ids = moves.mapped('id')
        
        if self.pdc_move_id:
            move_ids.append(self.pdc_move_id.id)
        if self.collect_move_id:
            move_ids.append(self.collect_move_id.id)
             
        if self.inverse_pdc_move_id:
            move_ids.append(self.inverse_pdc_move_id.id)
        if self.inverse_collect_move_id:
            move_ids.append(self.inverse_collect_move_id.id)
        if self.inverse_move_id:
            move_ids.append(self.inverse_move_id.id)
        
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids)],
        }
        
    def _prevet_cheque_partner(self):
        if self.is_check:
            if self.partner_type == 'customer' and self.payment_type == 'outbound':
                raise UserError(_("Cheuqe available for receive money only in customer payment!"))
        
            if self.partner_type == 'supplier' and self.payment_type == 'inbound':
                raise UserError(_("Cheuqe available for send money only in vendor payment!"))
    
    @api.model
    def create(self, vals):
        res = super(AccountPayment,self).create(vals)
        res._prevet_cheque_partner()
        return res
    
    @api.multi    
    def write(self, vals):
        res = super(AccountPayment,self).write(vals)
        self._prevet_cheque_partner()
        return res
    
        