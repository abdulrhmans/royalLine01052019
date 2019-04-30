# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero

class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'
    
    
    dr_account_ids = fields.One2many('account.fiscal.position.dr.account', 'position_id', 
                                        string='Deferred Revenue Accounts Mapping', copy=True)
    
    
    @api.model
    def map_dr_account(self, account):
        for pos in self.dr_account_ids:
            if pos.account_src_id.id == account:
                return pos.account_dest_id.id
        return account
    
    
class AccountFiscalPositionDRAccount(models.Model):
    _name = 'account.fiscal.position.dr.account'
    _description = 'Deferred Revenue Accounts Fiscal Position'
    _rec_name = 'position_id'

    position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',
        required=True, ondelete='cascade')
    account_src_id = fields.Many2one('account.account', string='Account on Line',
        domain=[('deprecated', '=', False)], required=True)
    account_dest_id = fields.Many2one('account.account', string='Account to Use Instead',
        domain=[('deprecated', '=', False)], required=True)

    _sql_constraints = [
        ('dr_account_src_dest_uniq',
         'unique (position_id,account_src_id,account_dest_id)',
         'An deferred revenue account fiscal position could be defined only once time on same accounts.')
    ]


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    @api.multi
    def create_move(self, post_move=True):
        created_moves = self.env['account.move']
        prec = self.env['decimal.precision'].precision_get('Account')
        for line in self:
            if line.move_id:
                raise UserError(_('This depreciation is already linked to a journal entry! Please post or delete it.'))
            category_id = line.asset_id.category_id
            depreciation_date = self.env.context.get('depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            amount = current_currency.with_context(date=depreciation_date).compute(line.amount, company_currency)
            asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
            
            dep_account_id = category_id.account_depreciation_id.id
            if line.asset_id.partner_id:
                partner = line.asset_id.partner_id
                fpos = partner.property_account_position_id
                if not fpos:
                    fpos = self.env['account.fiscal.position'].get_fiscal_position(partner.id)
                else:
                    fpos = fpos.id
                    
                if fpos:
                    fpos_rec = self.env['account.fiscal.position'].browse(fpos)
                    dep_account_id = fpos_rec.map_dr_account(dep_account_id)
                
            move_line_1 = {
                'name': asset_name,
                'account_id': dep_account_id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': category_id.journal_id.id,
                'partner_id': line.asset_id.partner_id.id,
                'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
            }
            move_line_2 = {
                'name': asset_name,
                'account_id': category_id.account_depreciation_expense_id.id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': category_id.journal_id.id,
                'partner_id': line.asset_id.partner_id.id,
                'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'purchase' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and line.amount or 0.0,
            }
            move_vals = {
                'ref': line.asset_id.code,
                'date': depreciation_date or False,
                'journal_id': category_id.journal_id.id,
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            }
            move = self.env['account.move'].create(move_vals)
            line.write({'move_id': move.id, 'move_check': True})
            created_moves |= move

        if post_move and created_moves:
            created_moves.filtered(lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).post()
        return [x.id for x in created_moves]
    
    
    
class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'
    
    
    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if 'invoice_id' in vals and 'date' in vals: 
            date = fields.Date.from_string(vals['date'])
            vals['date'] = str(date.replace(day=1))
            
        return super(AccountAssetAsset, self).create(vals)
            
