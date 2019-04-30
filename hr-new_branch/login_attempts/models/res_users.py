# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import models, fields, api
from email.utils import formataddr
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
        
    _inherit = 'res.users'
    
    login_locked = fields.Boolean(track_visibility='onchange')

    @api.model
    def update_user_login_state(self, cron_mode=True):
        recs = self.search([('login_locked', '=', True)])
        for rec in recs:
            current_time = datetime.now()
            loginlocked_time = datetime.strptime(str(rec.login_locked_time), '%Y-%m-%d %H:%M:%S')
            diff = current_time - loginlocked_time
            result = divmod(diff.days * 86400 + diff.seconds, 60)
            if result[0] > 10:
                rec.write({'login_locked':False, 'login_locked_time':None})
                rec.create_mail_message(body='User')
                _logger.info('User **'+ str(rec.name) +'** Login Restored')
        return True

    @api.multi
    def unlock_user_login(self):
        res = super(ResUsers, self).unlock_user_login()
        self.create_mail_message(body='User')
        return res

    @api.multi
    def _get_default_from(self):
        self.ensure_one()
        if self.env.user.email:
            return formataddr((self.env.user.name, self.env.user.email))
        raise UserError(_("Unable to send email, please configure the sender's email address or alias."))

    @api.multi
    def create_mail_message(self, body):
        user_admin = self.env.user
        for user in self:
            if not user.login_locked:
                body += ' '+str(user.name)+': has been Un-locked'
            vals = {
                'message_type': 'notification',
                'author_id': user_admin.partner_id.id,
                'date': datetime.now(),
                'email_from': self._get_default_from(),
                'model': 'res.partner',
                'res_id': user.partner_id.id,
                'subtype_id': 2,
                'body': body}
            self.env['mail.message'].create(vals)