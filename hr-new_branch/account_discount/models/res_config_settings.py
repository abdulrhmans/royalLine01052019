# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    
    _inherit = 'res.config.settings'

    discount_type = fields.Selection([('fixed', 'Use Fixed Discount'),
                                      ('percentage', 'Use Percentage Discount'),
                                      ('both', 'Use Both Discount')], string="Discount Type")
    group_fix_use_discount = fields.Boolean(string="Fixed", 
                                            implied_group='account_discount.group_fix_use_discount', 
                                            group='base.group_user,base.group_public')
    group_percent_use_discount = fields.Boolean(string="Percentage", 
                                                implied_group='account_discount.group_percent_use_discount', 
                                                group='base.group_user,base.group_public')
    group_both_use_discount = fields.Boolean(string="All", 
                                             implied_group='account_discount.group_both_use_discount', 
                                             group='base.group_user,base.group_public')
    
    @api.onchange('discount_type')
    def _onchange_discount_type_qty(self):
        if self.discount_type == 'fixed':
            self.update({'group_fix_use_discount': True})
            self.update({'group_percent_use_discount': False})
            self.update({'group_both_use_discount': False})
            
        elif self.discount_type == 'percentage':
            self.update({'group_fix_use_discount': False})
            self.update({'group_percent_use_discount': True})
            self.update({'group_both_use_discount': False})
            
        else:
            self.update({'group_fix_use_discount': False})
            self.update({'group_percent_use_discount': False})
            self.update({'group_both_use_discount': True})

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('account_discount.discount_type', self.discount_type)
        
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(discount_type=self.env['ir.config_parameter'].sudo().get_param('account_discount.discount_type', default='fixed'))
        return res
    
    @api.model    
    def create(self, values):
        if 'discount_type' in values:
            if values['discount_type'] == 'fixed':
                values['group_fix_use_discount'] = True
            elif values['discount_type'] == 'percentage':
                values['group_percent_use_discount'] = True
            else:
                values['group_both_use_discount'] = True
        return super(ResConfigSettings, self).create(values)
    