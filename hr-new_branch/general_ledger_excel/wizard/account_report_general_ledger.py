# -*- coding: utf-8 -*-

from odoo import fields, models, _,api
from odoo.exceptions import UserError
import xlwt
import tempfile
import base64
from xlwt import easyxf
from io import BytesIO



class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"
    
    def print_general_ledger_excel(self):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read()[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        report_id = self.env['report.account.report_generalledger']
        data = self.pre_print_report(data)
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))
        
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        print_journal = []
        if data['form'].get('journal_ids', False):
            print_journal = [journal.code for journal in self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]

        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        Accounts = report_id.with_context(data['form'].get('used_context',{}))._get_account_move_entry(accounts, init_balance, sortby, display_account)
        
     
        
        report = xlwt.Workbook()
        sheet = report.add_sheet("General Ledger Report")
        sheet.write_merge(0,0,0,6, '%s: General ledger'% self.env.user.company_id.name or '' )
        sheet.write_merge(1,2,0,6, 'Journals: %s'% ', '.join([ lt or '' for lt in print_journal ]) )
        
        cu = self.env.user.company_id.currency_id
        style_cur = easyxf(num_format_str='"%s" #,##0.%s'%(cu.symbol,'0'*cu.decimal_places))
       
        if data['form']['display_account'] == 'all':
            DA = 'All accounts'
        elif data['form']['display_account'] == 'movement':
            DA = 'With movements'
        else :
            DA = 'With balance not equal to zero'
        sheet.write_merge(3,3,0,2, 'Display Account: %s'% DA )
        
        if data['form']['target_move'] == 'all':
            TM = 'All Entries'
        else:
            TM = 'All Posted Entries'
        sheet.write_merge(3,3,3,5, 'Target Moves: %s'% TM )
        
        if data['form']['sortby'] == 'sort_date':
            SB = 'Date'
        else:
            SB = 'Journal and Partner'
        sheet.write_merge(4,4,0,2, 'Sorted By: %s'% SB )
        
        f_t_date =  str('From: ' + data['form']['date_from']+' ' if data['form']['date_from'] else '' )+ str('To: ' + data['form']['date_to']+' ' if data['form']['date_to'] else '' )
        sheet.write_merge(6,6,0,2, '%s'% f_t_date )
        r = 7
        
        sheet.write_merge(r,r,0,0, 'Date' )
        sheet.write_merge(r,r,1,1, 'JRNL' )
        sheet.write_merge(r,r,2,2, 'Partner' )
        sheet.write_merge(r,r,3,3, 'Ref' )
        sheet.write_merge(r,r,4,4, 'Move' )
        sheet.write_merge(r,r,5,5, 'Entry Label' )
        sheet.write_merge(r,r,6,6, 'Debit' )
        sheet.write_merge(r,r,7,7, 'Credit' )
        sheet.write_merge(r,r,8,8, 'Balance' )
        sheet.write_merge(r,r,9,9, 'Currency' )
        
        cur_obj = self.env['res.currency']
        for account in Accounts:
            r+=1
            sheet.write_merge(r,r,0,5, '\t%s'% str(account['code'])+str(account['name']) )
            sheet.write_merge(r,r,6,6,  account['debit'],style=style_cur )
            sheet.write_merge(r,r,7,7,  account['credit'],style=style_cur )
            sheet.write_merge(r,r,8,8, account['balance'],style=style_cur )
            for line in account['move_lines']:
                r+=1
                sheet.write_merge(r,r,0,0, '%s'%line['ldate'] )
                sheet.write_merge(r,r,1,1, '%s'%line['lcode'] )
                sheet.write_merge(r,r,2,2, '%s'%line['partner_name'] )
                sheet.write_merge(r,r,3,3, '%s'%line['lref'] if line['lref'] else '' )
                sheet.write_merge(r,r,4,4, '%s'%line['move_name'] )
                sheet.write_merge(r,r,5,5, '%s'%line['lname'] )
                sheet.write_merge(r,r,6,6, line['debit'],style=style_cur )
                sheet.write_merge(r,r,7,7, line['credit'],style=style_cur )
                sheet.write_merge(r,r,8,8, line['balance'],style=style_cur )
                if line['amount_currency'] and  line['amount_currency'] > 0.0:
                    cur_id = cur_obj.browse(line['currency_id'])
                    style_fc = easyxf(num_format_str='"%s" #,##0.%s'%(cur_id.symbol,'0'*cur_id.decimal_places))
                    sheet.write_merge(r,r,9,9, line['amount_currency'],style_fc )
        file_data = BytesIO()
        report.save(file_data)
        file_data.seek(0)
        data1 = file_data.read()
        attachment_id = self.env['ir.attachment'].create({
                'name': 'GeneralLedger.xls',
                'datas': base64.b64encode(data1),
                }).id
      
        return {    
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': "/web/binary/download_file?id=%s&file_name=%s"%(attachment_id,'GeneralLedger.xls'),
            }
   
            
        
        
        
        
        