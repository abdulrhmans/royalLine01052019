# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import  UserError


class HrTotherRequest(models.Model):
    _name = "hr.other.request"
    _description = "Request"
    _inherit = ['mail.thread']
    _rec_name = 'employee_id'
    
    name = fields.Char('Number', readonly=True,copy=False)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, track_visibility='onchange')
    notes = fields.Html('Notes',copy=False)
    date = fields.Date('Date',readonly=True,copy=False)
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('done', 'Done'), ('canceled', 'Canceled')], 'Status', default="draft",copy=False, track_visibility='onchange')
    document = fields.Binary('Document',copy=False)
    
    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].sudo().next_by_code('hr.other.request') or '/'
        vals['date'] = fields.Date.today()
        res =  super(HrTotherRequest, self).create(vals)
        add_follower = self.env['mail.wizard.invite'].create({'res_model':self._name,'res_id':res.id,
                                           'partner_ids':[(4,id) for id in self.env.user.company_id.users_to_notify_ot_r_ids.mapped('partner_id.id')]})
        add_follower.add_followers()
        return res
    
    
    @api.multi
    def write(self, vals):
        for rec in self:
            if not self.env.user.has_group('hr.group_hr_user') and rec.state != 'draft':
                raise UserError("You can only edit a drat request.")
        return  super(HrTotherRequest, self).write(vals)
    @api.multi
    def send_mail(self):
        subject = _('Requests')
        Mail = self.env['mail.mail']
        for rec in self:
            partner_id = rec.employee_id.user_id.partner_id.id
            vals = {
                'subject': subject,
                'body_html': rec.notes,
                'partner_ids': partner_id and [(4, partner_id)] or None,
                'email_to': rec.employee_id.work_email,
            }
            mail = Mail.create(vals)
            mail.send()
    
    @api.multi
    def unlink(self):
        if 'done' in self.mapped('state') or 'submitted' in self.mapped('state'):
            raise UserError(_('You can only delete a draft Request.'))
        return super(HrTotherRequest, self).unlink()
    
    @api.multi
    def make_new(self):
        self.write({'state': 'draft'})
    
    @api.multi
    def make_sup(self):
        self.write({'state': 'submitted'})
    
    @api.multi
    def make_app(self):
        self.write({'state': 'approved'})
    
    @api.multi
    def make_done(self):
        self.write({'state': 'done'})
        self.send_mail()
    
    @api.multi
    def make_cancel(self):
        self.write({'state': 'canceled'})


class Employee(models.Model):
    _inherit = "hr.employee"

    other_req_count = fields.Integer('Total Other Requisite', compute="_compute_other_req_count")

    def _compute_other_req_count(self):
        OtherReq = self.env['hr.other.request']
        for rec in self:
            rec.other_req_count = OtherReq.search_count([('employee_id', '=', rec.id)])


