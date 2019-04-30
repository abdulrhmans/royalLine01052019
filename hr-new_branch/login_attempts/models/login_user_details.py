# -*- coding: utf-8 -*-

import logging
from itertools import chain
from odoo.http import request
from odoo import models, fields, api, _
from datetime import datetime
_logger = logging.getLogger(__name__)
USER_PRIVATE_FIELDS = ['password']
concat = chain.from_iterable
from odoo.exceptions import except_orm

class LoginLocation(models.Model):
    
    _name = 'login.location'
    _description = 'Location which is specifically allowed to this user'
    
    name = fields.Char(string='Name', required=True)
    ip_address = fields.Char(string='IP Address', required=True)

class LoginUpdate(models.Model):
    
    _name = 'login.detail'
    _description = 'User login attempts and details'
    _order = 'date_time desc'

    name = fields.Char(string="User Name")
    date_time = fields.Datetime(string="Login Date And Time", default=lambda self: fields.datetime.now())
    ip_address = fields.Char(string="IP Address")
    database = fields.Char(string='Database', size=64,  readonly=True)
    login_state = fields.Selection([('success','Success'),
                                    ('fail','Fail')],
                                   string='Attempt Status', readonly=True)
    location_id = fields.Many2one(comodel_name='login.location', string='Location', readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string='User', readonly=True)
    password = fields.Char(string='Password', size=64, readonly=True)

    @api.multi
    def show_password(self):
        self.ensure_one()
        raise except_orm(_("Password on this attempt is '%s':") % self.password)
    
class LoginUserDetail(models.Model):
    
    _inherit = 'res.users'
    
    location_ids = fields.Many2many('login.location', string='Allowed Locations', help="If Empty Then All Locations Allowed")
    login_locked = fields.Boolean(string='Lock Login', default=False)
    login_locked_time = fields.Datetime(string="Locked Time")

    @api.multi
    def unlock_user_login(self):
        self.ensure_one()
        if self.login_locked:
            self.write({'login_locked':False, 'login_locked_time':None})
        return True
        
    @classmethod
    def authenticate(self, db, login, password, user_agent_env):
        uid = super(LoginUserDetail, self).authenticate(db, login, password, user_agent_env)
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        user_log_obj = request.env['login.detail']
        users_obj = request.env['res.users']
        is_allowed = False
        if uid:
            vals = {
                'date_time':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'name':login,
                'user_id':uid,
                'database':db,
                }
            user = users_obj.sudo().browse(uid)
            location_ids = user.location_ids
            
            if not location_ids:
                if not user.login_locked:
                    is_allowed = True
                    location_idss = request.env['login.location'].sudo().search([])
                    location_id = False
                    for loc in location_idss:
                        if ip_address == loc.ip_address:
                            location_id = loc.id
                    vals.update({'login_state': 'success', 'location_id': location_id, 'ip_address': ip_address})
                
            for loc in location_ids:
                if ip_address == loc.ip_address:
                    if not user.login_locked:
                        is_allowed = True
                        vals.update({'login_state': 'success', 'location_id':loc.id, 'ip_address': loc.ip_address})
                    
            if not is_allowed:
                location_idss = request.env['login.location'].sudo().search([])
                location_id = False
                for loc in location_idss:
                    if ip_address == loc.ip_address:
                        location_id = loc.id
                vals.update({'login_state': 'fail', 'location_id':location_id ,'ip_address': ip_address})
                user_log_obj.sudo().create(vals)
                return False
            else:
                user_log_obj.sudo().create(vals)
                return uid
        else:
            location_ids = request.env['login.location'].sudo().search([])
            location_id = False
            for loc in location_ids:
                if ip_address == loc.ip_address:
                    location_id = loc.id
            vals = {
                'name':login,
                'password': password,
                'database':db,
                'location_id':location_id,
                'login_state':'fail',
                'date_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': ip_address
                }
            user_log_obj.sudo().create(vals)
            login_count = user_log_obj.sudo().search([('name', '=', login), ('login_state', '=', 'fail')])
            if len(login_count) > 3:
                user = users_obj.sudo().search([('login', '=', login)])
                if user:
                    user.sudo().write({'login_locked':True, 'login_locked_time':datetime.now()})
                    user.sudo().create_mail_message(body='User '+str(user.name)+': has been Locked')
                    _logger.info('User  **'+ str(user.name) +'** is Locked due to 3 incorrect attempts')
            return False

