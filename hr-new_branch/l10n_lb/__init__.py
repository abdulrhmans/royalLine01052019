# -*- coding: utf-8 -*-

from . import models

from odoo import api, SUPERUSER_ID

def load_translations(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.ref('l10n_lb.l10nlb_chart_template').process_coa_translations()