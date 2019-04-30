# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import except_orm
import datetime
import logging
_logger = logging.getLogger(__name__)

def format_select_html(rows, field_names, callback=None):
	"""
	Take a table and format it in HTML
	@param rows
		list of lists
	@param field_names
		list of strings
	@return
		single big string containing HTML data
	"""
	outbuffer = '<table class="o_list_view table table-condensed table-striped">\r\n'
	outbuffer += '<thead>\r\n'
	for name in field_names:
		outbuffer += '<th>%s</th>\r\n' % str(name)
	outbuffer += '</thead>\r\n'
	outbuffer += '<tbody>\r\n'
	for row in rows:
		if callback is None:
			outbuffer += '<tr>'
		else:
			outbuffer += '<tr onclick="javascript:alert(''%s'')">' % callback
		for cell in row:
			outbuffer += '<td>%s</td>' % str(cell)
		outbuffer += '</tr>\r\n'
	outbuffer += '</tbody>\r\n'
	outbuffer += '</table>\r\n'
	return outbuffer

def execute_and_format_select_html(cursor, query, callback=None):
	"""
	Execute a SELECT statement, then call format_select_html()
	"""
	_logger.info("Executing: " + query)
	cursor.execute(query)
	rows = cursor.fetchall()
	field_names = [x[0] for x in cursor.description]
	return format_select_html(rows, field_names, callback)


def _compute_command_output(self):
	"""
	Utility method for classes that execute and show a single command
	"""
	return execute_and_format_select_html(self._cr, self.command)

class SqlCommands(models.Model):
	
	_name = "sql.commands"
	_description = "Execute SQL commands"
	
	name = fields.Char('Name', required=True)
	start_date = fields.Datetime('Start Date', readonly=True)
	duration = fields.Float('Duration', readonly=True)
	state = fields.Selection([('draft','Draft'), ('done','Done')], 'Status', default='draft')
	command = fields.Text('SQL Command', help="Type any SQL command (SELECT/INSERT/UPDATE/...) here. The command will be executed on current database.")
	command_output = fields.Html('Command output', readonly=True)
	sql_password = fields.Char('Password', required=True)

	def unlink(self):
		for sql in self:
			if sql.state == 'done':
				raise except_orm(_('Error!'), _('You cannot delete executed sql.'))
		super(SqlCommands, self).unlink()

	def _get_duration(self, start, stop):
		if start and stop:
			diff = datetime.datetime.strptime(str(start), '%Y-%m-%d %H:%M:%S') - stop
			if diff:
				duration = abs(float(diff.days) * 24 + (float(diff.seconds) / 3600))
				return round(duration, 2)
			return 0.0

	@api.multi
	def start_process(self):
		return {
				'name': _('Confirm'),
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'sql.command.confirm',
				'view_id': False,
				'context':{},
				'type': 'ir.actions.act_window',
				'nodestroy': True,
				'target': 'new',
			}
		
	@api.multi
	def execute(self):
		self.ensure_one()
		self.start_date = datetime.datetime.now()
		"""
		Button pressed
		"""
		_logger.info("Executing: " + self.command)
		cursor = self._cr
		cursor.execute(self.command)
		rowcount = cursor.rowcount
		try:
			# is this a SELECT?
			rows = cursor.fetchall()
		except:
			# No, probably it is not
			self.command_output = "%d rows affected." % rowcount
			self.state = 'done'
			return
		field_names = [x[0] for x in cursor.description]
		self.command_output = format_select_html(rows, field_names)
		stop_date = datetime.datetime.now()
		duration = self._get_duration(self.start_date, stop_date)
		self.duration = duration
		self.state = 'done'
		