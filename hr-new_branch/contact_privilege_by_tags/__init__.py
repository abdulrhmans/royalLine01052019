# -*- encoding: utf-8 -*-
from . import models

from odoo import api, SUPERUSER_ID

def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    base_rule = env.ref('base.res_partner_rule_private_employee')
    sale_personal_rule = env.ref('sale.sale_order_personal_rule')
    sale_see_all = env.ref('sale.sale_order_see_all')
    
    if base_rule:
        base_rule.domain_force =  ['|', ('type', '!=', 'private'), ('type', '=', False)]
    
    if sale_personal_rule:
        sale_personal_rule.domain_force = "['|',('user_id','=',user.id),('user_id','=',False)]"
    
    if sale_see_all:
        sale_see_all.domain_force = [(1,'=',1)]