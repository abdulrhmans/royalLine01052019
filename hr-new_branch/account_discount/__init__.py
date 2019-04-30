# -*- coding: utf-8 -*-

from . import models


def post_init_hook(cr, registry):
    from odoo.exceptions import Warning
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env['res.company'].search([]):
        res_config_id = env['res.config.settings'].create({'company_id': company.id, 'discount_type':'fixed'})
        res_config_id.execute()
