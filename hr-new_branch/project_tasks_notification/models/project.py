# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import urllib3
from urllib.parse import urljoin
from urllib.parse import urlencode


class Project(models.Model):
    _inherit = 'project.project'
    
    @api.model
    def send_val(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        tasks_recs = self.env['project.task'].search([('stage_id.notified','=', True)], order='stage_id asc')
        db = {'db': self.env.cr.dbname}
        users={}
        partenrs={}
        table_1=""
        table_2=""
        for task in tasks_recs:
            if task.user_id :
                if task.user_id.id not in users:
                    users[task.user_id.id] = []
                users[task.user_id.id].append(task)
            else:
                if 'not_assgined' not in users:
                    users['not_assgined'] = []
                users['not_assgined'].append(task)
        
#         if 'not_assgined' in users:
#             table_2 = '<p style="font-size: 19px;"><b>Not Assigned Tasks</b></p> \n '
#             table_2 += '<table style="border-collapse: collapse;" width="100%">'+\
#                       '<tr>\
#                             <th style="padding: 6px 12px;background: #777777;color: white">Deadline</th>\
#                             <th style="padding: 6px 12px;background: #777777;color: white">Task</th>\
#                             <th style="padding: 6px 12px;background: #777777;color: white">Project</th>\
#                             <th style="padding: 6px 12px;background: #777777;color: white">Stage</th>\
#                             <th style="padding: 6px 12px;background: #777777;color: white">View</th>\
#                         </tr>'
#             odd = False
#             for t in users['not_assgined']: 
#                 if odd:
#                     background = 'background-color: #f2f2f2'
#                     odd = False
#                 else:
#                     background = ''
#                     odd = True
#                 fragment = {'view_type' : 'form','model' : 'project.task','id': t.id}
#                 link = urljoin(base_url, "web?%s#%s" % (urlencode(db), urlencode(fragment)))
#                 table_2 += '<tr> '+\
#                             ' <td style="padding: 6px 12px;'+str(background)+'">'+str(t.date_deadline or '')+'</td>'+\
#                             ' <td style="padding: 6px 12px;'+str(background)+'">'+t.name+'</td>'+\
#                             ' <td style="padding: 6px 12px;'+str(background)+'">'+str(t.project_id.name or '')+'</td>'+\
#                             ' <td style="padding: 6px 12px;'+str(background)+'">'+t.stage_id.name+'</td>'+\
#                             ' <td style="padding: 4px 10px;'+str(background)+'">'+'<a style="background-color: #777777;font-weight: bold;padding: 10px 25px;border: none;color: white;font-size:11px;border-radius: 5px;text-align: center;text-decoration: none;display: inline-block;cursor: pointer;" href="'+link+'">View</a>'+'</td>'+\
#                         ' </tr>'
#             table_2 += '</table'
            
        for user in users:
            if user != 'not_assgined':
                table_1 = '<p style="font-size: 19px;"><b>Assigned Tasks</b></p> \n '
                table_1 += '<table style="border-collapse: collapse" width="100%">'+\
                          '<tr>\
                                <th style="padding: 6px 12px;background: #A24689;color: white">Deadline</th>\
                                <th style="padding: 6px 12px;background: #A24689;color: white">Task</th>\
                                <th style="padding: 6px 12px;background: #A24689;color: white">Project</th>\
                                <th style="padding: 6px 12px;background: #A24689;color: white">Stage</th>\
                                <th style="padding: 6px 12px;background: #A24689;color: white">View</th>\
                            </tr>'
                odd = False
                for t in users[user]: 
                    if odd:
                        background = 'background-color: #f2f2f2'
                        odd = False
                    else:
                        background = ''
                        odd = True
                    fragment = {'view_type' : 'form','model' : 'project.task','id': t.id}
                    link = urljoin(base_url, "web?%s#%s" % (urlencode(db), urlencode(fragment)))
                    table_1 += '<tr> '+\
                                ' <td style="padding: 6px 12px;'+str(background)+'">'+str(t.date_deadline or '')+'</td>'+\
                                ' <td style="padding: 6px 12px;'+str(background)+'">'+t.name+'</td>'+\
                                ' <td style="padding: 6px 12px;'+str(background)+'">'+str(t.project_id.name or '')+'</td>'+\
                                ' <td style="padding: 6px 12px;'+str(background)+'">'+t.stage_id.name+'</td>'+\
                                ' <td style="padding: 4px 10px;'+str(background)+'">'+'<a style="background-color: #A24689;padding: 10px 25px;font-weight: bold;border: none;color: white;font-size:11px;border-radius: 5px;text-align: center;text-decoration: none;display: inline-block;cursor: pointer;" href="'+link+'">View</a>'+'</td>'+\
                            ' </tr>'
                table_1 += '</table>'  
                user_data = self.env['res.users'].browse(user) 
                post_values = {
                            'subject': 'New Notification ',
                            'body_html':' <div style="direction:ltr"> <p style="font-size: 22px;"><strong>Dear '+str(user_data.name) +' ,</strong></p> \
                            </br></br>'+str(table_1)+'</br></br></br></br>'+str(table_2)+'</div> '
                            ,
                            'parent_id': False,
                            'partner_ids': [user_data.partner_id.id],
                            'recipient_ids': [(6,0,[user_data.partner_id.id])],
                            'attachment_ids': [],
                    } 
                    #.with_context(default_state='sent')
                m = self.env['mail.mail'].create(post_values)
                m.send()
                    # Notification On Messaging = Inbox
#                 mail_thread_obj = self.pool.get('mail.thread')
#                 msg_id = mail_thread_obj.message_post(self.env.cr,self.env.uid,[0],subtype='mail.mt_comment',context={'default_state':'sent'},**post_values)
 
class Projecttype(models.Model):
    _inherit = 'project.task.type'
    
    notified= fields.Boolean('Notified')
 