# -*- coding: utf-8 -*-

from odoo import models, fields, _, SUPERUSER_ID, api
import copy

class ir_model(models.Model):
    _inherit = 'ir.model'
    
    object_merger_model = fields.Boolean('Object Merger', default=False, help='If checked, by default the Object Merger configuration will get this module in the list')
    
class object_merger_settings(models.TransientModel):
    
    _name = 'object.merger.settings'
    _inherit = 'res.config.settings'
    
    def _get_default_object_merger_models(self):
        return self.env['ir.model'].search([('object_merger_model', '=', True)])
    
    models_ids = fields.Many2many('ir.model', 'object_merger_settings_model_rel', 'object_merger_id', 'model_id', 'Models',  default=_get_default_object_merger_models)
    
    def update_field(self, vals):
        ## Init ##
        model_ids = []
        model_obj = self.env['ir.model']
        action_obj = self.env['ir.actions.act_window']
        value_obj = self.env['ir.actions.actions']
        field_obj = self.env['ir.model.fields']
        ## Process ##
        if not vals or not vals.get('models_ids', False):
            return False
        elif vals.get('models_ids') or model_ids[0][2]:
            model_ids = vals.get('models_ids')
            if isinstance(model_ids[0], (list)):
                model_ids = model_ids[0][2]
        # Unlink Previous Actions
        unlink_ids = action_obj.search([('res_model' , '=', 'object.merger')])
        for unlink_id in unlink_ids:
            unlink_id.unlink()
            un_val_ids = value_obj.search([('binding_model_id', '=', unlink_id.id)])
            [value_obj.unlink() for value_obj in un_val_ids]
            
        # Put all models which were selected before back to not an object_merger
        model_not_merge_ids = model_obj.search([('id', 'not in', model_ids), ('object_merger_model', '=', True)])
        if model_not_merge_ids:
            for model_notmerge_id in model_not_merge_ids:
                model_notmerge_id.write({'object_merger_model' : False})
        # Put all models which are selected to be an object_merger
        if model_ids:
            object_merger_ids = model_obj.search([('model', '=', 'object.merger')])
            for model_id in model_ids:
                modelobj = self.env['ir.model'].search([('id', '=', model_id)])
                modelobj.write({'object_merger_model' : True})
          
                field_name = 'x_' + str(modelobj.model).replace('.','_') + '_id'
                act_id = action_obj.create({
                            'name': "%s " % str(modelobj.name) + _("Merger"),
                            'type': 'ir.actions.act_window',
                            'res_model': 'object.merger',
                            'src_model': str(modelobj.model),
                            'binding_model_id': modelobj.id,
                            'view_type': 'form',
                            'context': "{'field_to_read':'%s'}" % field_name,
                            'view_mode':'form',
                            'target': 'new',
                        })
                field_name = 'x_' + str(modelobj.model).replace('.','_') + '_id'
                if not field_obj.search([('name', '=', field_name), ('model', '=', 'object.merger')]):
                    field_data = {
                        'model': 'object.merger',
                        'model_id': object_merger_ids.id or False,
                        'name': field_name,
                        'relation': str(modelobj.model),
                        'field_description': "%s " % str(modelobj.name) + _('To keep'),
                        'state': 'manual',
                        'ttype': 'many2one',
                    }
                    field_obj.sudo().create(field_data)
        return True

    @api.model
    def create(self, vals):
        """ create method """
        vals2 = copy.deepcopy(vals)
        result = super(object_merger_settings, self).create(vals2)
        ## Fields Process ##
        self.update_field(vals)
        return result
    
    def install(self):
#       Initialization of the configuration
        """ install method """
        for vals in self.read():
            result = self.update_field(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
