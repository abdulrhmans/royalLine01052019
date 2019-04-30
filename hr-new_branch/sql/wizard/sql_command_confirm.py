# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ 
from odoo.exceptions import except_orm

class SqlCommandConfirm(models.TransientModel):
    '''
    Exceute Queries
    '''
    _name = 'sql.command.confirm'
    _description = 'Confirm the SQL command to be executed'

    password = fields.Char('Password', required=True)

    @api.multi
    def continue_process(self):
        self.ensure_one()
        sql_obj = self.env['sql.commands'].search([('id', '=', self.env.context['active_id'])])
        if sql_obj and self.password == sql_obj.sql_password:    
            sql_obj.execute()
        else:
            raise except_orm(_('Error!'), _('Wrong Password.'))
        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
