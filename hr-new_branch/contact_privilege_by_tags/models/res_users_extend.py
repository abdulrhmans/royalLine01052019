# -*- encoding: utf-8 -*-

from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class ResUser(models.Model):
    
    _inherit = 'res.users'

    partner_tags = fields.Many2many(string='Tags', comodel_name='res.partner.category', relation='users_partner_category_rel', column1='user_id', column2='category_id')
    allowed_contacts = fields.One2many('res.partner', compute='_compute_allowed_contacts', string="Allowed Contacts")
    show_contacts_access_controls = fields.Boolean(string='Show Contacts Access Controls', compute='_toggle_contacts_access_controls')

    @api.depends('partner_tags')
    def _compute_allowed_contacts(self):
        _logger.info('Computing contacts allowed to user')
        for user in self:
            allowed_contacts = None
            if user.has_group('contact_privilege_by_tags.group_limited_contacts'):
                if user.partner_tags:
                    for tag in user.partner_tags:
                        if tag.partner_records:
                            if not allowed_contacts:
                                allowed_contacts = tag.partner_records                            
                            else:
                                allowed_contacts += tag.partner_records
            else:
                allowed_contacts = self.env['res.partner'].search([])
            user.allowed_contacts = allowed_contacts
            
    @api.depends('groups_id')
    def _toggle_contacts_access_controls(self):
        _logger.info('Computing toggle state for contacts access controls')
        for user in self:
            allowed_contacts = None
            if user.has_group('contact_privilege_by_tags.group_limited_contacts'):
                user.show_contacts_access_controls = True
            else:
                user.show_contacts_access_controls = False
            
    @api.multi
    def write(self, vals):
        result = super(ResUser, self).write(vals)
        if vals.get('partner_tags'):
            self.env['res.partner'].update_tagged_access_rules()
        return result
    
    @api.model
    def create(self, vals):
        result = super(ResUser, self).create(vals)
        self.env['res.partner'].update_tagged_access_rules()
        return result

class Partner(models.Model):
    
    _inherit = 'res.partner'
    
    @api.multi
    def write(self, vals):
        result = super(Partner, self).write(vals)
        if vals.get('category_id'):
            self.update_tagged_access_rules()
        return result
    
    @api.model
    def create(self, vals):
        partner = super(Partner, self).create(vals)
        self.update_tagged_access_rules()
        return partner
    
    @api.model
    def update_tagged_access_rules(self):
        _logger.info('Updating the record rule')
        self.env.ref('contact_privilege_by_tags.partner_contact_rule').sudo().write({'domain_force': "['|', ('category_id', '=', False), ('id', 'in', user.allowed_contacts.ids)]"})
        self.env.ref('contact_privilege_by_tags.invoice_partner_rule').sudo().write({'domain_force': "['|', ('partner_id.category_id', '=', False), ('partner_id.id', 'in', user.allowed_contacts.ids)]"})
        self.env.ref('contact_privilege_by_tags.purchase_order_partner_rule').sudo().write({'domain_force': "['|', ('partner_id.category_id', '=', False), ('partner_id.id', 'in', user.allowed_contacts.ids)]"})
        self.env.ref('contact_privilege_by_tags.sale_order_partner_rule').sudo().write({'domain_force': "['|', ('partner_id.category_id', '=', False), ('partner_id.id', 'in', user.allowed_contacts.ids)]"})
        self.env.ref('contact_privilege_by_tags.account_move_partner_rule').sudo().write({'domain_force': "['|', ('partner_id.category_id', '=', False), ('partner_id.id', 'in', user.allowed_contacts.ids)]"})
        rule_vals =  {'domain_force': "['|', ('type', '!=', 'private'), ('type', '=', False), '|', ('category_id', '=', False), ('id', 'in', user.allowed_contacts.ids)]",
                      'group': [(4, self.env.ref('contact_privilege_by_tags.group_limited_contacts').id, False)]}
        _logger.info('Updating the private employee rule with vals ' + str(rule_vals))
        self.env.ref('base.res_partner_rule_private_employee').sudo().write(rule_vals)
        
        rule_vals = {'domain_force': "['|',('user_id','=',user.id),('user_id','=',False), '|', ('partner_id.category_id', '=', False), ('partner_id.id', 'in', user.allowed_contacts.ids)]",
                     'group': [(4, self.env.ref('contact_privilege_by_tags.group_limited_contacts').id, False)]}
        _logger.info('Updating the sale order rule with vals ' + str(rule_vals))
        self.env.ref('sale.sale_order_personal_rule').sudo().write(rule_vals)
        
        rule_vals = {'domain_force': "[(1,'=',1), '|', ('partner_id.category_id', '=', False), ('partner_id.id', 'in', user.allowed_contacts.ids)]",
                     'group': [(4, self.env.ref('contact_privilege_by_tags.group_limited_contacts').id, False)]}
        _logger.info('Updating the all sale order rule with vals ' + str(rule_vals))
        self.env.ref('sale.sale_order_see_all').sudo().write(rule_vals)

class PartnerCategory(models.Model):
    
    _inherit = 'res.partner.category'
    
    partner_records = fields.One2many('res.partner', compute='_compute_allowed_contacts', string="Allowed Contacts")

    def _compute_allowed_contacts(self):
        _logger.info('Computing partner records associated with tag')
        '''Get the partner records related to the category'''
        query_contacts_grouped_category = """SELECT concat(concat('[', array_to_string(array_agg(partner_id), ', ')), ']'), category_id, count(partner_id) 
                FROM res_partner_res_partner_category_rel WHERE category_id IN """ + str(tuple(self.ids)).replace(',)', ')') + """ GROUP BY category_id"""
        self.env.cr.execute(query_contacts_grouped_category)
        grouped_records_found = self.env.cr.fetchall()
        category_contacts_dict = {}
        if grouped_records_found:
            for grouped_records_row in grouped_records_found:
                grouped_partner_rec_ids = eval(grouped_records_row[0])
                category_contacts_dict[str(grouped_records_row[1])] = grouped_partner_rec_ids
        for category in self:
            partner_records = None
            if str(category.id) in category_contacts_dict:
                if category_contacts_dict[str(category.id)]:
                    partner_records = self.env['res.partner'].browse(category_contacts_dict[str(category.id)])
            category.partner_records = partner_records