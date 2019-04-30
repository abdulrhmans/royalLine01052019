# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request, content_disposition
import base64


class DownloadFile(http.Controller):

    @http.route('/web/binary/download_file', type='http',auth='user')
    def download_file(self,id, file_name=False, ** kwargs):
        attachment_id = request.env['ir.attachment'].browse(int(id))
        data = b''
        if attachment_id.name == 'GeneralLedger.xls':
            data = attachment_id.datas
            attachment_id.unlink()
        try:
            return request.make_response(base64.b64decode(data), headers=[('Content-Type', 'application/vnd.ms-excel'),
                         ('Content-Disposition', content_disposition(file_name))])
        except Exception as e :
            pass
     
