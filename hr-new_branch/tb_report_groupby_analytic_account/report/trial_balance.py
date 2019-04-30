# -*- coding: utf-8 -*-
from odoo import api, models,_
from datetime import datetime
import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    # TODO saas-17: remove the try/except to directly import from misc
    import xlsxwriter

class TrialBalance(models.AbstractModel):
    _inherit = 'account.coa.report'

    
    def get_templates(self):
        templates = super(TrialBalance, self).get_templates()
        templates['main_template'] = 'tb_report_groupby_analytic_account.template_coa_report'
        templates['main_template_analytic'] = 'tb_report_groupby_analytic_account.template_coa_report_analytic'
        return templates
    
    def get_xlsx(self, options, response):
        if 'analytic_accounts' in options and options['analytic_accounts'] and len(options['analytic_accounts']) and options.get('analytic_table_separate',False):
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet(self.get_report_name()[:31])
    
            def_style = workbook.add_format({'font_name': 'Arial'})
            title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
            super_col_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
            level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'pattern': 1, 'font_color': '#FFFFFF'})
            level_0_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'left': 2, 'pattern': 1, 'font_color': '#FFFFFF'})
            level_0_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'right': 2, 'pattern': 1, 'font_color': '#FFFFFF'})
            level_1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2})
            level_1_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'left': 2})
            level_1_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'right': 2})
            level_2_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2})
            level_2_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2, 'left': 2})
            level_2_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2, 'right': 2})
            level_3_style = def_style
            level_3_style_left = workbook.add_format({'font_name': 'Arial', 'left': 2})
            level_3_style_right = workbook.add_format({'font_name': 'Arial', 'right': 2})
            domain_style = workbook.add_format({'font_name': 'Arial', 'italic': True})
            domain_style_left = workbook.add_format({'font_name': 'Arial', 'italic': True, 'left': 2})
            domain_style_right = workbook.add_format({'font_name': 'Arial', 'italic': True, 'right': 2})
            upper_line_style = workbook.add_format({'font_name': 'Arial', 'top': 2})
    
            sheet.set_column(0, 0, 15) #  Set the first column width to 15
    
            super_columns = self._get_super_columns(options)
            y_offset = 0
            grand_totals = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            for analytic_account in options['analytic_accounts']:
                n_options = options.copy()
                n_options.update({'no_format':True, 'print_mode':True})
                n_options['analytic_accounts'] = [analytic_account]
                n_options['analytic_name'] = self.env['account.analytic.account'].browse(int(analytic_account)).name
                sheet.write(y_offset, 0, n_options['analytic_name'], super_col_style)
                
    
                x = super_columns.get('x_offset', 0)
                for super_col in super_columns.get('columns', []):
                    cell_content = super_col.get('string', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                    x_merge = super_columns.get('merge')
                    if x_merge and x_merge > 1:
                        sheet.merge_range(y_offset, x, y_offset, x + (x_merge - 1), cell_content, super_col_style)
                        x += x_merge
                    else:
                        sheet.write(y_offset, x, cell_content, super_col_style)
                        x += 1
        
                y_offset += 1
                x = 0
                for column in self.get_columns_name(n_options):
                    sheet.write(y_offset, x, column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '), title_style)
                    x += 1
                y_offset += 1
                
                
                lines = self.with_context(self.set_context(n_options)).get_lines(n_options)
                if n_options.get('hierarchy'):
                    lines = self.create_hierarchy(lines)
        
                if lines:
                    max_width = max([len(l['columns']) for l in lines])
        
                for y in range(0, len(lines)):
                    if lines[y].get('level') == 0:
                        for x in range(0, len(lines[y]['columns']) + 1):
                            sheet.write(y + y_offset, x, None, upper_line_style)
                        y_offset += 1
                        style_left = level_0_style_left
                        style_right = level_0_style_right
                        style = level_0_style
                    elif lines[y].get('level') == 1:
                        for x in range(0, len(lines[y]['columns']) + 1):
                            sheet.write(y + y_offset, x, None, upper_line_style)
                        y_offset += 1
                        style_left = level_1_style_left
                        style_right = level_1_style_right
                        style = level_1_style
                    elif lines[y].get('level') == 2:
                        style_left = level_2_style_left
                        style_right = level_2_style_right
                        style = level_2_style
                    elif lines[y].get('level') == 3:
                        style_left = level_3_style_left
                        style_right = level_3_style_right
                        style = level_3_style
                    else:
                        style = def_style
                        style_left = def_style
                        style_right = def_style
                        
                    sheet.write(y + y_offset, 0, lines[y]['name'], style_left)
                    for x in range(1, max_width - len(lines[y]['columns']) + 1):
                        sheet.write(y + y_offset, x, None, style)
                    for x in range(1, len(lines[y]['columns']) + 1):
                        if x < len(lines[y]['columns']):
                            sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, lines[y]['columns'][x - 1].get('name', ''), style)
                        else:
                            sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, lines[y]['columns'][x - 1].get('name', ''), style_right)
                        
                        if 'total' not in lines[y].get('class', ''):
                            grand_totals[x] += float(lines[y]['columns'][x - 1].get('no_format_name', 0))
                    
                    if 'total' in lines[y].get('class', '') or lines[y].get('level') == 0:
                        for x in range(len(lines[0]['columns']) + 1):
                            sheet.write(y + 1 + y_offset, x, None, upper_line_style)
                        y_offset += 1
                    
                if lines:
                    for x in range(max_width + 1):
                        sheet.write(len(lines) + y_offset, x, None, upper_line_style)
                    y_offset += 6
                
                y_offset += len(lines)
            
            x = 0
            for column in self.get_columns_name(n_options):
                if x == 0:
                    sheet.write(y_offset, x, 'Grand Total', style_left)
                else:
                    sheet.write(y_offset, x, self.format_value(grand_totals[x]), style_right)
                x += 1
                    
            workbook.close()
            
            output.seek(0)
            response.stream.write(output.read())
            output.close()
        else:
            super(TrialBalance, self).get_xlsx(options, response)
        
    @api.multi
    def get_html(self, options, line_id=None, additional_context=None):
        if options.get('analytic_table_separate',False):
            templates = self.get_templates()
            report_manager = self.get_report_manager(options)
            report = {'name': self.get_report_name(),
                    'summary': report_manager.summary,
                    'company_name': self.env.user.company_id.name,}
            
            if 'analytic_accounts' not in options or not options['analytic_accounts']:
                options['analytic_accounts'] = self.env['account.analytic.account'].search([]).mapped('id')
            
            if len(options['analytic_accounts']) > 1:
                html = u''.encode('utf8')
                for analytic_account in options['analytic_accounts']:
                    n_options = options.copy()
                    n_options['analytic_accounts'] = [analytic_account]
                    n_options['analytic_name'] = self.env['account.analytic.account'].browse(int(analytic_account)).name
                    lines = self.with_context(self.set_context(n_options)).get_lines(n_options, line_id=line_id)
                    if n_options.get('hierarchy'):
                        lines = self.create_hierarchy(lines)
            
                    footnotes_to_render = []
                    if self.env.context.get('print_mode', False):
                        footnotes = dict([(str(f.line), f) for f in report_manager.footnotes_ids])
                        number = 0
                        for line in lines:
                            f = footnotes.get(str(line.get('id')))
                            if f:
                                number += 1
                                line['footnote'] = str(number)
                                footnotes_to_render.append({'id': f.id, 'number': number, 'text': f.text})
            
                    rcontext = {'report': report,
                                'lines': {'columns_header': self.get_columns_name(n_options), 'lines': lines},
                                'options': n_options,
                                'context': self.env.context,
                                'model': self,
                            }
                    if additional_context and type(additional_context) == dict:
                        rcontext.update(additional_context)
                    render_template = templates.get('main_template', 'account_reports.main_template')
                    if line_id is not None:
                        render_template = templates.get('line_template', 'account_reports.line_template')
                    
                    if not html:
                        html += self.env['ir.ui.view'].render_template(
                            render_template,
                            values=dict(rcontext),
                        )
                    else:
                        render_template = templates.get('main_template_analytic')
                        html += self.env['ir.ui.view'].render_template(
                            render_template,
                            values=dict(rcontext),
                        )
            else:
                return super(TrialBalance, self).get_html(options, line_id=line_id, additional_context=additional_context)
            
            
            
            if self.env.context.get('print_mode', False):
                for k,v in self.replace_class().items():
                    html = html.replace(k, v)
                # append footnote as well
                html = html.replace(b'<div class="js_account_report_footnotes"></div>', self.get_html_footnotes(footnotes_to_render))
            return html
        else:
            return super(TrialBalance, self).get_html(options, line_id=line_id, additional_context=additional_context)


    @api.model
    def get_options(self, previous_options=None):
        # Be sure that user has group analytic if a report tries to display analytic
        if self.filter_analytic:
            self.filter_analytic = self.env.user.id in self.env.ref(
                'analytic.group_analytic_accounting').users.ids and True or None
            self.filter_analytic_table_separate = False if self.filter_analytic else None
  
        return super(TrialBalance, self).get_options(previous_options=previous_options)
    
