# -*- coding: utf-8 -*-
from openerp import models, fields, api

class Project(models.Model):
    _inherit = 'project.project'
    
    @api.model
    def get_stages(self):
        return self.env['project.task.type'].search([]).ids
   
    stage_ids = fields.Many2many('project.task.type', 'project_task_type_rel', 'project_id', 'type_id', 'Stages',default=get_stages,)
    

class Project_task(models.Model):
    _inherit = 'project.task'
    
    approved_by_id= fields.Many2one('res.users', 'Approved By',track_visibility='onchange')
    technical_info= fields.Text('Technical Info')
    technical_pad= fields.Text('Technical Info',pad_content_field='technical_info')

    
class ResUsers(models.Model):
    _inherit = 'res.users'
    
    sw_employee = fields.Boolean('SW Employee')