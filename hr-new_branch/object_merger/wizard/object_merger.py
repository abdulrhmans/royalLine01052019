# -*- coding: utf-8 -*-

from odoo import fields, osv, api,  models, _ 
from odoo.tools import ustr

class object_merger(models.TransientModel):
    '''
    Merges objects
    '''
    _name = 'object.merger'
    _description = 'Merge objects'

    name = fields.Char('Name', size=32)
    delete_if_not_active = fields.Boolean('Delete records if not active field', default=False)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(object_merger, self).fields_view_get(view_id, view_type, toolbar=toolbar,submenu=False)
        object_ids = self._context.get('active_ids',[])
        active_model = self._context.get('active_model')
        field_name = 'x_' + (active_model and active_model.replace('.','_') or '') + '_id'
        fields = res['fields']
        if object_ids:
            view_part = """<label for='"""+field_name+"""'/>
                    <div>
                        <field name='""" + field_name +"""' required="1" domain="[(\'id\', \'in\', """ + str(object_ids) + """)]"/>
                    </div>"""
            res['arch'] = res['arch'].replace(
                    """<separator string="to_replace"/>""", view_part)
            field = self.fields_get([field_name])
            fields.update(field)
            res['fields'] = fields
            res['fields'][field_name]['domain'] = [('id', 'in', object_ids)]
            res['fields'][field_name]['required'] = True
        return res

    @api.multi
    def action_merge(self):
        """
        Merges two (or more objects
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Lead to Opportunity IDs
        @param context: A standard dictionary for contextual values

        @return : {}
        """
        #res = self.read()[0]
        active_model = self._context.get('active_model')
        if not active_model:
            raise osv.osv.except_orm(_('Configuration Error!'),_('The is no active model defined!'))
        model_pool = self.env[active_model]
        object_ids = self._context.get('active_ids',[])
        field_to_read = self._context.get('field_to_read')
        field_list = field_to_read and [field_to_read] or []
        objectt = self.read(field_list)[0]
        if objectt and field_list and objectt[field_to_read]:
            object_id = objectt[field_to_read][0]
        else:
            raise osv.osv.except_orm(_('Configuration Error!'),_('Please select one value to keep'))
        self.env.cr.execute("SELECT name, model FROM ir_model_fields WHERE relation=%s AND ttype NOT IN ('many2many', 'one2many');", (active_model, ))
        for name, model_raw in self.env.cr.fetchall():
            if getattr(self.env[model_raw], '_auto', None):
                if not self.env[model_raw]._auto:
                    continue
            if getattr(self.env[model_raw], '_check_time', None):
                continue
            else:
                if getattr(self.env[model_raw], '_fields', None):
                    if self.env[model_raw]._fields.get(name, False) and \
                            (isinstance(self.env[model_raw]._fields[name], fields.Many2one) \
#                            or isinstance(self.env[model_raw]._fields[name], self.env[model_raw]._fields[name].compute) \
                            and self.env[model_raw]._fields[name].store):
                        if getattr(self.env[model_raw], '_table', None):
                            if self.env[model_raw]._abstract or self.env[model_raw]._transient or not self.env[model_raw]._auto:
                                continue 
                            model = self.env[model_raw]._table
                        else:
                            model = model_raw.replace('.', '_')
                        requete = "UPDATE "+model+" SET "+name+"="+str(object_id)+" WHERE "+ ustr(name) +" IN " + str(tuple(object_ids)) + ";"
                        self.env.cr.execute(requete)
                        
        self.env.cr.execute("SELECT name, model FROM ir_model_fields WHERE relation=%s AND ttype IN ('many2many');", (active_model, ))
        for field, model in self.env.cr.fetchall():
            field_data = self.env[model] and self.env[model]._fields.get(field, False) \
                            and (isinstance(self.env[model]._fields[field], fields.many2many) \
#                            or isinstance(self.env[model_raw]._fields[name], self.env[model_raw]._fields[name].compute) \
                            and self.env[model]._fields[field].store) \
                            and self.env[model]._fields[field] \
                            or False
            if field_data:
                model_m2m, rel1, rel2 = field_data._sql_names(self.env[model])
                requete = "UPDATE %s SET %s=%s WHERE %s " \
                    "IN %s AND %s NOT IN (SELECT DISTINCT(%s) " \
                    "FROM %s WHERE %s = %s);" % (model_m2m,rel2,
                                                 str(object_id),
                                                 ustr(rel2),
                                                 str(tuple(object_ids)),
                                                 rel1,rel1,model_m2m,
                                                 rel2,str(object_id))
                self.env.cr.execute(requete)
                
        self.env.cr.execute("SELECT name, model FROM ir_model_fields WHERE name IN ('res_model', 'model');")
        for field, model in self.env.cr.fetchall():
            model_obj = self.env[model]
            if not model_obj:
                continue
            if field == 'model' and model_obj._fields.get('res_model', False):
                continue
            res_id = model_obj._fields.get('res_id')
            if res_id:
                requete = False
                if isinstance(res_id, fields.Integer) or isinstance(res_id, fields.Many2one):
                    requete = "UPDATE %s SET res_id = %s " \
                    "WHERE res_id IN %s AND " \
                    "%s = '%s';" % (model_obj._table,
                                    str(object_id),
                                    str(tuple(object_ids)),
                                    field,
                                    active_model)
                elif isinstance(res_id, fields.char):
                    requete = "UPDATE %s SET res_id = '%s' " \
                    "WHERE res_id IN %s AND " \
                    "%s = '%s';" % (model_obj._table,
                                    str(object_id),
                                    str(tuple([str(x) for x in object_ids])),
                                    field,
                                    active_model)
                if requete:
                    self.env.cr.execute(requete)
        unactive_object_ids = model_pool.search([('id', 'in', object_ids), ('id', '<>', object_id)])
        if model_pool._fields.get('active', False):
            for unactive_id in unactive_object_ids:
                unactive_id.write({'active': False})
        else:
            read_data = self.read(['delete_if_not_active'])
            if read_data['delete_if_not_active']:
                model_pool.unlink()
                
        # Try to limit multiplication of records in mail_followers table:
        requete = "DELETE FROM mail_followers WHERE id IN" \
            "(SELECT id FROM (SELECT COUNT(id) AS total, MAX(id) as id," \
            "res_model,res_id,partner_id FROM mail_followers " \
            "GROUP BY res_model,res_id,partner_id) a WHERE a.total > 1);"
        for i in range(1,len(object_ids)):
            self.env.cr.execute(requete)
        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
