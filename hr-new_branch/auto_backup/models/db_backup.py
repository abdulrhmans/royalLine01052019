# -*- coding: utf-8 -*-
from email.mime.text import MIMEText
from odoo import models, fields, api, _, service
from odoo import tools
from odoo.exceptions import ValidationError, Warning, except_orm
import os
import datetime
from werkzeug import urls
import urllib
from urllib.error import HTTPError
import random 
import requests
from urllib import parse
import json
import smtplib
from _datetime import date
from dateutil.relativedelta import relativedelta

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib
import time
import socket
import getpass
import logging
import calendar
_logger = logging.getLogger(__name__)

try:
    import paramiko
except ImportError:
    raise ImportError(
        'This module needs paramiko to automatically write backups to the FTP through SFTP. Please install paramiko on your system. (sudo pip3 install paramiko)')

TIMEOUT = 100

GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/token'

def execute(connector, method, *args):
    res = False
    try:
        res = getattr(connector, method)(*args)
    except socket.error as error:
        _logger.critical('Error while executing the method "execute". Error: ' + str(error))
        raise error
    return res

class dbBackupoptions(models.Model):
    
    _name = 'db.backup.options'

    name = fields.Char(string='Policy name', required=True)
    #first_option_keep_backup = fields.Integer(string='Backup for x Days (First Month)')
    #second_option_keep_backup = fields.Integer(string='Backup for x Days (Second Month)')
    #third_option_keep_backup = fields.Integer(string='Backups for x Days (Third Month)')
    #fourth_option_keep_backup = fields.Integer(string='Backup After first Quarter')
    #backup_plan = fields.Selection([('Daily', 'Daily'), ('Monthly', 'Monthly'), ('Quarterly', 'Quarterly')], 'Backup Plan')
    apply_on_local_files = fields.Boolean(string='Apply on Local Files')
    apply_on_google_drive = fields.Boolean(string='Apply on Files in Google Drive')
    preceding_periods_backups_retention = fields.One2many(comodel_name='db.backup.retention.preceding.period', inverse_name='backup_plan', string='Backup Retention in Preceding Periods')
    state = fields.Selection([('Draft', 'Draft'), ('Active', 'Active')], 'State', default='Draft')

    @api.one
    @api.constrains('name')
    def _check_unique_constraint(self):
        record = self.search([('name', '=', self.name)])
        if len(record) > 1:
            raise ValidationError('Policy already exists and violates unique constraint')

    @api.model
    def create(self, values):
        if 'name' in values:
            values['state'] = 'Active'
        created_rec = super(dbBackupoptions, self).create(values)
        return created_rec

    @api.one
    def write(self, values):
        self.clear_caches()
        return super(dbBackupoptions, self).write(values)

class dbBackupPrecedingPeriodRetention(models.Model):
    
    _name = 'db.backup.retention.preceding.period'
    
    @api.one
    @api.depends('period', 'previous_period_number', 'number_of_backups_to_retain')
    def compute_period_name(self):
        name = 'Unsaved Record'
        if self.period:
            name = 'After '
            name += self.period.capitalize()
            if self.previous_period_number:
                name += ' Number ' + str(self.previous_period_number) + ' (i.e. ' + self.period.capitalize() + ' - ' + str(self.previous_period_number) + ')'
            name += ' Retain ' + str(self.number_of_backups_to_retain) + ' Backup' + ('s' if self.number_of_backups_to_retain > 1 else '')  + ' per ' + self.period.capitalize()
        self.name = name
    
    name = fields.Char(string='Preceding Period', compute=compute_period_name, readonly=True)
    period = fields.Selection([('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('quarter', 'Quarter'), ('year', 'Year')], 'Time Period', required=True,
                              help="The type of time slot period the rule is applicable for")
    previous_period_number = fields.Integer(string='Preceding Period Number', required=True,
                                            help="The number of time periods allowed to pass before the rule starts taking affect.")
    number_of_backups_to_retain = fields.Integer(string='Number of Backups to Retain', required=True, help='Number of backups to retain in after this rule start taking affect.')
    backups_retention_order = fields.Selection([('ascending', 'Ascending Order'), ('descending', 'Descending Order')], 'Backups Retention Order', default='descending', required=True,  
                                               help="Descending Order retain the latest backups e.g. if one backup is to be retained its going to be from the end of the period, Ascending Order results in the retention of the older backups i.e. if one backups is to be retained its going to be from the start of the period")
    backups_distribution_list = [('even_distribution', 'Evenly Distributed'), ('alternative', 'Alternate Backups'), ('consecutive', 'Consecutive - Back to Back')] #, ('manual_sequence', 'Manually Defined Sequence')
    backups_distribution = fields.Selection(backups_distribution_list, 'Distribution of Retained backups', required=True, default='even_distribution',
                                            help="If more than one backups are to be retained they are distributed evenly within the time period under consideration")
    manual_backups_sequence = fields.One2many(comodel_name='db.backup.retention.manual.sequence', inverse_name='preceding_period_retention', string='Manually Defined Backups Sequence')
    backup_plan = fields.Many2one('db.backup.options', string='Backup Retention Policy', help="Bakups Retention policy stipulates how much backups are to be retained in specified time periods")
    apply_on_local_files = fields.Boolean(string='Apply on local storage Backups', invisible=True)
    apply_on_google_drive = fields.Boolean(string='Apply on Google drive Backups', invisible=True)
    #state = fields.Selection([('Draft', 'Draft'), ('Active', 'Active')], 'State', default='Draft')

    @api.one
    @api.constrains('backup_plan', 'period', 'previous_period_number', 'number_of_backups_to_retain', 'backups_distribution')
    def _check_unique_constraint(self):
        #if self.previous_period_number <= 0:
        #    raise ValidationError('The number for the previous period must be greater than 0')
        max_previous_period = None
        #if self.period == 'day':
        #    max_previous_period = 7
        #if self.period == 'week':
        #    max_previous_period = 4
        #if self.period == 'month':
        #    max_previous_period = 12
        #if self.period == 'quarter':
        #    max_previous_period = 4
        if max_previous_period:
            if self.previous_period_number > max_previous_period:
                raise ValidationError('The value for previous period in case of ' + str(self.period.capitalize()) + ' interval cannot exceed ' + str(max_previous_period))
        record = self.search([('backup_plan', '=', self.backup_plan.id), ('period', '=', self.period), ('previous_period_number', '=', self.previous_period_number), ('apply_on_local_files', '=', self.apply_on_local_files)])
        if len(record) > 1:
            raise ValidationError('Record already exists for local storage ' + str(self.period.capitalize()) + ' - ' + str(self.previous_period_number) + ' and violates unique constraint')
        record = self.search([('backup_plan', '=', self.backup_plan.id), ('period', '=', self.period), ('previous_period_number', '=', self.previous_period_number), ('apply_on_google_drive', '=', self.apply_on_google_drive)])
        if len(record) > 1:
            raise ValidationError('Record already exists for Google Drive ' + str(self.period.capitalize()) + ' - ' + str(self.previous_period_number) + ' and violates unique constraint')
        record = self.search([('backup_plan', '=', self.backup_plan.id), ('period', '=', self.period), ('previous_period_number', '<', self.previous_period_number), ('number_of_backups_to_retain', '<', self.number_of_backups_to_retain)])
        if len(record) > 1:
            raise ValidationError('Other backup retention rules occuring before ' + str(self.period.capitalize()) + ' - ' + str(self.previous_period_number) + ' will have reduced the number of backups below the specified number ' + str(self.number_of_backups_to_retain))
        if self.backups_distribution =='alternative':
            #TODO: Alternative constraint
            if self.period == 'day':
                raise ValidationError('Alternate backups retention should not be configured with the time period of a day, kindly choose other options for backups distribution in the rule of ' + str(self.name))
            record = self.search([('backup_plan', '=', self.backup_plan.id), ('period', '=', self.period), ('previous_period_number', '<', self.previous_period_number)], order='previous_period_number desc', limit=1)
            if record:
                if type(record) is list:
                    record = record[0]
                if record.number_of_backups_to_retain < self.number_of_backups_to_retain*2:
                    raise ValidationError('Other backup retention rules occuring before ' + str(self.period.capitalize()) + ' - ' + str(self.previous_period_number) + ' will have reduced the number of backups below the required number ' + str(self.number_of_backups_to_retain*2) + ' for alternate backup retention, the maximum number of backups that can be retained alternatively is ' + str(record.number_of_backups_to_retain//2) + ' instead of the currently specified ' + str(self.number_of_backups_to_retain))
    @api.model
    def get_slot_interval(self, preceding_period_backup_retention_rule, interval_start, interval_end):
        time_slot_window = interval_end - interval_start
        slot_interval = time_slot_window / datetime.timedelta(minutes=1)
        slot_interval = slot_interval / (preceding_period_backup_retention_rule.number_of_backups_to_retain if preceding_period_backup_retention_rule.number_of_backups_to_retain else 1) 
        slot_interval = datetime.timedelta(minutes=slot_interval)
        return slot_interval
    
    @api.model
    def regular_interval_delta(self, start, end, delta):
        curr = start
        while curr < end:
            curr += delta
            yield curr
    
    @api.model
    def retention_policy_remove_local_backups(self):
        backups_requiring_pruning = self.env['db.backup.configuration'].search([('autoremove', '=', True)])
        if backups_requiring_pruning:
            for configured_backup in backups_requiring_pruning:
                if configured_backup.backup_remove_option:
                    if configured_backup.backup_remove_option.preceding_periods_backups_retention:
                        for preceding_period_backup_retention_rule in configured_backup.backup_remove_option.preceding_periods_backups_retention:
                            backups_to_remove = preceding_period_backup_retention_rule.get_list_of_backups_to_remove(complete_path=True, force_storage='local')[0]
                            for backup in backups_to_remove:
                                if os.path.exists(backup['file_path']):
                                    os.remove(backup['file_path'])
                                self.env['db.backups'].browse(backup['id']).write({'backup_action': 'Delete', 'stored_on_local_storage': False})
    
    @api.model
    def monthdelta(self, date, delta):
        m, y = (date.month+delta) % 12, date.year + ((date.month)+delta-1) // 12
        if not m: m = 12
        d = min(date.day, [31,
            29 if y%4==0 and not y%400==0 else 28,31,30,31,30,31,31,30,31,30,31][m-1])
        return date.replace(day=d,month=m, year=y)

    @api.one
    def get_backups_to_retain(self, force_storage=None):
        self.ensure_one()
        preceding_period_backup_retention_rule = self
        date_threshold_start = None
        date_threshold_end = None
        
        group_by_clause = ''
        order_by_clause = ''
        
        if preceding_period_backup_retention_rule.period == 'day':
            #date_threshold_start = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d') + " 23:59:59", '%Y-%m-%d %H:%M:%S.%f') - datetime.timedelta(days=preceding_period_backup_retention_rule.previous_period_number)
            date_threshold_start = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d') + " 23:59:59", '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=preceding_period_backup_retention_rule.previous_period_number)
            date_threshold_end = datetime.datetime.strptime('%s-1-1 00:00:00' %(str(date_threshold_start.year)), '%Y-%m-%d %H:%M:%S')#date_threshold_start - datetime.timedelta(days=7)
            group_by_clause = 'GROUP BY day'
            order_by_clause = ' ORDER BY day DESC'
        if preceding_period_backup_retention_rule.period == 'week':
            start_of_next_week = datetime.datetime.strptime((datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d') + " 23:59:59", '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=datetime.datetime.today().isoweekday() % 7)
            week_end_date = start_of_next_week - datetime.timedelta(days=1)
            date_threshold_start = week_end_date - datetime.timedelta(days=7*preceding_period_backup_retention_rule.previous_period_number)
            date_threshold_end = datetime.datetime.strptime('%s-1-1 00:00:00' %(str(date_threshold_start.year)), '%Y-%m-%d %H:%M:%S')#date_threshold_start - datetime.timedelta(days=7)
            group_by_clause = 'GROUP BY week'
            order_by_clause = ' ORDER BY week DESC'
        if preceding_period_backup_retention_rule.period == 'month':
            month_relevant_date = self.monthdelta(datetime.datetime.now(), -preceding_period_backup_retention_rule.previous_period_number) #datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-') + "1 23:59:59", '%Y-%m-%d %H:%M:%S')
            date_threshold_start = datetime.datetime.strptime(str(month_relevant_date.year)+'-' + str(month_relevant_date.month) + '-' + str(calendar.monthrange(month_relevant_date.year,month_relevant_date.month)[1]) + ' 23:59:59', '%Y-%m-%d %H:%M:%S') #month_relevant_date - datetime.timedelta(days=preceding_period_backup_retention_rule.previous_period_number*365/12)
            date_threshold_end = datetime.datetime.strptime('%s-1-1 00:00:00' %(str(date_threshold_start.year)), '%Y-%m-%d %H:%M:%S')#date_threshold_start - datetime.timedelta(days=7)
            group_by_clause = 'GROUP BY month'
            order_by_clause = ' ORDER BY month DESC'
        if preceding_period_backup_retention_rule.period == 'quarter':
            quarter_relevant_date = self.monthdelta(datetime.datetime.now(), -(preceding_period_backup_retention_rule.previous_period_number*3))
            quarter = (quarter_relevant_date.month - 1) / 3 + 1
            quarter_start_date = datetime.datetime(datetime.datetime.now().year, 3 * quarter - 2, 1)
            date_threshold_start = quarter_start_date #- datetime.timedelta(days=preceding_period_backup_retention_rule.previous_period_number*365/3)
            date_threshold_end = datetime.datetime.strptime('%s-1-1 00:00:00' %(str(date_threshold_start.year)), '%Y-%m-%d %H:%M:%S')#date_threshold_start - datetime.timedelta(days=7)
            group_by_clause = 'GROUP BY quarter'
            order_by_clause = ' ORDER BY quarter DESC'
        if preceding_period_backup_retention_rule.period == 'year':
            year_start_date = datetime.datetime(datetime.datetime.now().year, 12, 31)
            year_relevant_date = self.monthdelta(datetime.datetime.now(), -(preceding_period_backup_retention_rule.previous_period_number*12)) #datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-') + "1 23:59:59", '%Y-%m-%d %H:%M:%S')
            date_threshold_start = datetime.datetime.strptime(str(year_relevant_date.year) + '-12-31 23:59:59' , '%Y-%m-%d %H:%M:%S')#year_start_date - datetime.timedelta(days=preceding_period_backup_retention_rule.previous_period_number*365)
            date_threshold_end = datetime.datetime.strptime('%s-1-1 00:00:00' %(str(date_threshold_start.year - 1)), '%Y-%m-%d %H:%M:%S')#date_threshold_start - datetime.timedelta(days=7)
            group_by_clause = 'GROUP BY year'
            order_by_clause = ' ORDER BY year DESC'
        if date_threshold_start:
            print(preceding_period_backup_retention_rule.name, ' - start applying from ', date_threshold_start)
        backups_order = 'DESC' if preceding_period_backup_retention_rule.backups_retention_order == 'descending' else 'ASC'
        #backups_found = self.env['db.backups'].search([('backup_creation_time', '<', date_threshold_start.strftime('%Y-%m-%d %H:%M:%S'))])
        record_filter_clause = """WHERE backup_creation_time <= '""" + date_threshold_start.strftime('%Y-%m-%d %H:%M:%S.%f') + """'
                        AND backup_creation_time >= '""" + date_threshold_end.strftime('%Y-%m-%d %H:%M:%S.%f') + "'"
        backup_storage_filter = ''
        file_storage_filter = ''
        storage = None
        if not force_storage:
            if preceding_period_backup_retention_rule.apply_on_local_files:
                storage='local'
            if preceding_period_backup_retention_rule.apply_on_google_drive:
                storage='google_drive'
        else:
            storage = force_storage
        if storage == 'local':
            backup_storage_filter += ' AND stored_on_local_storage=true'
            #file_storage_filter += ' AND stored_on_local_storage=true'
        if storage == 'google_drive':
            backup_storage_filter += ' AND stored_on_google_drive=true'
            #file_storage_filter += ' AND stored_on_google_drive=true'
        if storage == 'sftp_storage':
            backup_storage_filter += ' AND stored_on_sftp_server=true'
            #file_storage_filter += ' AND stored_on_sftp_server=true'
        grouped_records_query = """SELECT concat(concat('[', array_to_string(array_agg(id), ', ')), ']'), count(id), min(backup_creation_time), max(backup_creation_time) 
                                        FROM (select * from db_backups order by backup_creation_time desc) as backups %s %s %s %s""" %(record_filter_clause, backup_storage_filter, group_by_clause, order_by_clause)
        self.env.cr.execute(grouped_records_query)
        grouped_records_found = self.env.cr.fetchall()
        backups_to_retain = []
        backups_to_remove = []
        backup_interval_start = None
        backup_interval_end = None
        if grouped_records_found:
            previous_period_number = preceding_period_backup_retention_rule.previous_period_number
            for grouped_records_row in grouped_records_found:
                grouped_backup_rec_ids = eval(grouped_records_row[0])
                if len(grouped_backup_rec_ids) > preceding_period_backup_retention_rule.number_of_backups_to_retain:
                    slot_interval = None
                    #sql_interval_bound = """SELECT min(backup_creation_time), max(backup_creation_time) 
                    #                                from db_backups WHERE id IN %s""" %(str(tuple(grouped_backup_rec_ids)).replace(',)', ')'))
                    #self.env.cr.execute(sql_interval_bound)
                    #interval_bounds_retrieved = self.env.cr.fetchone()
                    #if interval_bounds_retrieved:
                    if grouped_records_row[2] and grouped_records_row[3]:
                        backup_interval_start = datetime.datetime.strptime(grouped_records_row[2], '%Y-%m-%d %H:%M:%S.%f')
                        backup_interval_end = datetime.datetime.strptime(grouped_records_row[3], '%Y-%m-%d %H:%M:%S.%f')
                        if preceding_period_backup_retention_rule.period == 'day':
                            #date_threshold_start = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d') + " 23:59:59", '%Y-%m-%d %H:%M:%S.%f') - datetime.timedelta(days=preceding_period_backup_retention_rule.previous_period_number)
                            backup_interval_start = datetime.datetime.strptime(backup_interval_start.strftime('%Y-%m-%d') + " 00:00:00", '%Y-%m-%d %H:%M:%S')
                            backup_interval_end = datetime.datetime.strptime(backup_interval_start.strftime('%Y-%m-%d') + " 23:59:59", '%Y-%m-%d %H:%M:%S')#date_threshold_start - datetime.timedelta(days=7)
                        if preceding_period_backup_retention_rule.period == 'week':
                            backup_interval_start = datetime.datetime.strptime(backup_interval_start.strftime('%Y-%m-%d') + " 00:00:00", '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=backup_interval_start.isoweekday() % 7)
                            backup_interval_end = backup_interval_start + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)
                        if preceding_period_backup_retention_rule.period == 'month':
                            backup_interval_start = datetime.datetime.strptime(backup_interval_start.strftime('%Y-%m-') + "1 00:00:00", '%Y-%m-%d %H:%M:%S')
                            backup_interval_end = datetime.datetime.strptime(backup_interval_start.strftime('%Y-%m-') + str(calendar.monthrange(backup_interval_start.year, backup_interval_start.month)[1]) +" 23:59:59", '%Y-%m-%d %H:%M:%S')
                        if preceding_period_backup_retention_rule.period == 'quarter':
                            quarter = (backup_interval_start.month - 1) // 3 + 1
                            backup_interval_start = datetime.datetime(backup_interval_start.year, 3 * quarter - 2, 1, 0, 0, 0)
                            backup_interval_end = backup_interval_start + relativedelta(months=3,seconds=-1)
                        if preceding_period_backup_retention_rule.period == 'year':
                            backup_interval_start = datetime.datetime(backup_interval_start.year, 1, 1, 0, 0, 0)
                            backup_interval_end = datetime.datetime(backup_interval_start.year, 12, calendar.monthrange(backup_interval_start.year, 12)[1], 23, 59, 59)
                        query_bound_start = backup_interval_start
                        if not preceding_period_backup_retention_rule.number_of_backups_to_retain:
                            sql_select_backups_to_remove_in_time_slot = """SELECT concat(concat('[', array_to_string(array_agg(id), ', ')), ']'), count(id) 
                                                FROM db_backups WHERE backup_creation_time >='""" + backup_interval_start.strftime('%Y-%m-%d %H:%M:%S.%f') + """'
                                        AND backup_creation_time<='""" + backup_interval_end.strftime('%Y-%m-%d %H:%M:%S.%f') + "' AND retained_fiscal_year_backup=false" 
                            self.env.cr.execute(sql_select_backups_to_remove_in_time_slot)
                            backups_found_to_be_removed_in_time_slot = self.env.cr.fetchone()
                            if backups_found_to_be_removed_in_time_slot:
                                backup_to_be_removed_from_time_slot = eval(backups_found_to_be_removed_in_time_slot[0])
                                if backup_to_be_removed_from_time_slot:
                                    backups_to_remove.extend(backup_to_be_removed_from_time_slot)
                        else:
                            if preceding_period_backup_retention_rule.backups_distribution == 'even_distribution':
                                slot_interval = self.get_slot_interval(preceding_period_backup_retention_rule, backup_interval_start, backup_interval_end)
                                for backup_time_slot_param in self.regular_interval_delta(backup_interval_start, backup_interval_end, slot_interval):
                                    sql_select_backup_to_retain_in_time_slot = "SELECT id FROM db_backups WHERE backup_creation_time >='" + query_bound_start.strftime('%Y-%m-%d %H:%M:%S.%f') + """'
                                    AND backup_creation_time<='""" + backup_time_slot_param.strftime('%Y-%m-%d %H:%M:%S.%f') + "' " + backup_storage_filter + " ORDER BY backup_creation_time " + backups_order + " LIMIT 1"
                                    self.env.cr.execute(sql_select_backup_to_retain_in_time_slot)
                                    backup_to_be_retained_found_in_time_slot = self.env.cr.fetchone()
                                    if backup_to_be_retained_found_in_time_slot:
                                        backups_to_retain.append(backup_to_be_retained_found_in_time_slot[0])
                                        sql_select_backups_to_remove_in_time_slot = """SELECT concat(concat('[', array_to_string(array_agg(id), ', ')), ']'), count(id) 
                                                FROM db_backups WHERE backup_creation_time >='""" + query_bound_start.strftime('%Y-%m-%d %H:%M:%S.%f') + """'
                                        AND backup_creation_time<='""" + backup_time_slot_param.strftime('%Y-%m-%d %H:%M:%S.%f') + """' 
                                        AND retained_fiscal_year_backup=false AND id != """ + str(backup_to_be_retained_found_in_time_slot[0]) + backup_storage_filter
                                        self.env.cr.execute(sql_select_backups_to_remove_in_time_slot)
                                        backups_found_to_be_removed_in_time_slot = self.env.cr.fetchone()
                                        if backups_found_to_be_removed_in_time_slot:
                                            backup_to_be_removed_from_time_slot = eval(backups_found_to_be_removed_in_time_slot[0])
                                            if backup_to_be_removed_from_time_slot:
                                                backups_to_remove.extend(backup_to_be_removed_from_time_slot)
                                    query_bound_start = backup_time_slot_param
                            elif preceding_period_backup_retention_rule.backups_distribution == 'alternative':
                                sql_select_backup_to_retain_in_time_slot = """SELECT id FROM db_backups WHERE retained_fiscal_year_backup=false 
                                AND backup_creation_time >='""" + backup_interval_start.strftime('%Y-%m-%d %H:%M:%S.%f') + """'
                                AND backup_creation_time<='""" + backup_interval_end.strftime('%Y-%m-%d %H:%M:%S.%f') + "' " + backup_storage_filter + " ORDER BY backup_creation_time " + backups_order
                                self.env.cr.execute(sql_select_backup_to_retain_in_time_slot)
                                backup_to_be_retained_found_in_time_slot = self.env.cr.fetchall()
                                if backup_to_be_retained_found_in_time_slot:
                                    if len(backup_to_be_retained_found_in_time_slot) == preceding_period_backup_retention_rule.number_of_backups_to_retain * 2:
                                        alternate = False
                                        for backup_row in backup_to_be_retained_found_in_time_slot:
                                            if not alternate:
                                                backups_to_retain.append(backup_row[0])
                                                alternate = True
                                            else:
                                                backups_to_remove.append(backup_row[0])
                                                alternate = False
                            elif preceding_period_backup_retention_rule.backups_distribution == 'consecutive':
                                sql_select_backup_to_retain_in_time_slot = """SELECT id FROM db_backups WHERE retained_fiscal_year_backup=false 
                                AND backup_creation_time >='""" + backup_interval_start.strftime('%Y-%m-%d %H:%M:%S.%f') + """'
                                AND backup_creation_time<='""" + backup_interval_end.strftime('%Y-%m-%d %H:%M:%S.%f') + """' 
                                """ + backup_storage_filter + " ORDER BY backup_creation_time " + backups_order
                                self.env.cr.execute(sql_select_backup_to_retain_in_time_slot)
                                backup_to_be_retained_found_in_time_slot = self.env.cr.fetchall()
                                if backup_to_be_retained_found_in_time_slot:
                                    if len(backup_to_be_retained_found_in_time_slot) >= preceding_period_backup_retention_rule.number_of_backups_to_retain:
                                        i = 0
                                        for backup_row in backup_to_be_retained_found_in_time_slot:
                                            i += 1
                                            if i <= preceding_period_backup_retention_rule.number_of_backups_to_retain:
                                                backups_to_retain.append(backup_row[0])
                                            else:
                                                backups_to_remove.append(backup_row[0])
                            else:
                                raise ValidationError('The specified backups distribution algorithm has no implementation ' + str(preceding_period_backup_retention_rule.backups_distribution))
                previous_period_number += 1
                #see if a record catering to the preceding period exists if yes then don't cascade the effect
                rule_for_following_preceding_period_found = self.search([('backup_plan', '=', preceding_period_backup_retention_rule.backup_plan.id), ('period', '=', preceding_period_backup_retention_rule.period), ('previous_period_number', '=', previous_period_number)])
                if rule_for_following_preceding_period_found:
                    break         
                                
        return {'backups_to_retain': backups_to_retain, 'backups_to_remove': backups_to_remove, 'record_filter_clause': record_filter_clause, 'backup_storage_filter': backup_storage_filter, 'backup_interval_start': backup_interval_start, 'backup_interval_end': backup_interval_end}
    
    @api.one
    def get_list_of_backups_to_remove(self, complete_path=None, force_storage=None):
        self.ensure_one()
        files_to_be_removed_paths = []
        files_to_be_removed_names = []
        backups_retention_params = self.get_backups_to_retain(force_storage=force_storage)[0]
        if backups_retention_params:
            backups_to_remove = backups_retention_params['backups_to_remove']
            
#             backups_to_retain = backups_retention_params['ids']
#             file_storage_filter = backups_retention_params['file_storage_filter']
#             backup_interval_start = backups_retention_params['backup_interval_start']
#             backup_interval_end = backups_retention_params['backup_interval_end']
#             record_filter_clause = backups_retention_params['record_filter_clause']
#             sql_interval_bounds = """SELECT min(backup_creation_time), max(backup_creation_time) 
#                                             FROM db_backups %s %s""" %(record_filter_clause, file_storage_filter)
#             self.env.cr.execute(sql_interval_bounds)
#             interval_bounds_retrieved = self.env.cr.fetchone()
            
#             if interval_bounds_retrieved:
#                 if interval_bounds_retrieved[0] and interval_bounds_retrieved[1]:
#                     backup_interval_start = datetime.datetime.strptime(interval_bounds_retrieved[0], '%Y-%m-%d %H:%M:%S.%f')
#                     backup_interval_end = datetime.datetime.strptime(interval_bounds_retrieved[1], '%Y-%m-%d %H:%M:%S.%f')
            if len(backups_retention_params['backups_to_retain']) >= self.number_of_backups_to_retain:
                if backups_to_remove:
                    sql_select_backups_to_remove = """SELECT id, path_db_backup, backup_file_name, stored_on_local_storage, stored_on_google_drive FROM db_backups 
                    WHERE id IN """ + str(tuple(backups_to_remove)).replace(',)', ')')
                    self.env.cr.execute(sql_select_backups_to_remove)
                    backups_to_be_removed = self.env.cr.fetchall()
                    for backup_rec in backups_to_be_removed:
                        files_to_be_removed_paths.append({'file_path': backup_rec[1], 'id': backup_rec[0]})
                        files_to_be_removed_names.append({'file_name': backup_rec[2], 'id': backup_rec[0]})
        if complete_path:
            return files_to_be_removed_paths
        return files_to_be_removed_names
            
    @api.model
    def create(self, values):
        created_rec = super(dbBackupPrecedingPeriodRetention, self).create(values)
        return created_rec

    @api.one
    def write(self, values):
        self.clear_caches()
        return super(dbBackupPrecedingPeriodRetention, self).write(values)
    
class dbBackupRetentionManualSequence(models.Model):
    
    _name = 'db.backup.retention.manual.sequence'
    
    _rec_name = 'sequence_number'
    
    sequence_number = fields.Integer(string='Sequence Number')
    preceding_period_retention = fields.Many2one('db.backup.retention.preceding.period', string='Backup Retention Preceding Period', required=True, invisible=True)

    @api.one
    @api.constrains('sequence_number', 'backup_retention_preceding_period')
    def _check_unique_constraint(self):
        record = self.search([('sequence_number', '=', self.sequence_number), ('backup_retention_preceding_period', self.backup_retention_preceding_period)])
        if len(record) > 1:
            raise ValidationError('Duplicate backup sequence number ' + str(self.sequence_number) + ' defined for the period ' + str(self.backup_retention_preceding_period))

class dbBackupGoogleDriveLink(models.Model):
    
    _name = 'db.backup.google.drive.link'
    #_name = 'backup.file.google.drive.rel'
    #_table = 'backup_file_google_drive_rel'
    _rec_name = 'google_file_id'
    
    @api.one
    def _get_id(self):
        sql_select_max_id = "SELECT max(id) FROM backup_file_google_drive_rel"
        self.env.cr.execute(sql_select_max_id)
        result = self.env.cr.fetchone()
        id = 1
        if result:
            max_id = result[0]
            id = max_id + 1
        self.id = id
        
    #id = fields.Integer(string='ID', compute='_get_id', store=True)
    backup_rec_id = fields.Many2one(comodel_name='db.backups', string='Backup')
    google_drive_rec_id = fields.Many2one(comodel_name='db.backup.google.account', string='Google Account')
    google_file_id = fields.Char(string='Google File ID')
    
    @api.multi
    def action_download_file_in_new_tab(self):
        for rec in self:
            dbbackup_google_drive_uri = 'https://drive.google.com/uc?export=download&id=' + self.google_file_id
            record_url = str(dbbackup_google_drive_uri)
            client_action = {
                    'type': 'ir.actions.act_url',
                    'name': "db.backup.google.account",
                    'target': 'new',
                    'url': record_url,
                    }
            return client_action

class dbBackups(models.Model):
    
    _name = 'db.backups'
    
    @api.one
    @api.depends('backup_creation_time')
    def _get_date_parameters(self):
        backup_creation_date = None
        
        if self.backup_creation_time:
            backup_creation_date = datetime.datetime.strptime(self.backup_creation_time, '%Y-%m-%d %H:%M:%S') 
        else:
            backup_creation_date = datetime.datetime.strptime(self.self.create_time, '%Y-%m-%d %H:%M:%S')
        if not backup_creation_date:
            backup_creation_date = datetime.datetime.now()
        if backup_creation_date:
            #backup_creation_date = datetime.datetime.strptime(self.backup_creation_time, '%Y-%m-%d %H:%M:%S.%f')
            self.hour = backup_creation_date.strftime('%Y-%m-%d %H')
            self.day = backup_creation_date.strftime('%Y%m%d')
            self.week = backup_creation_date.strftime('%Y%W')
            self.month = backup_creation_date.strftime('%Y%m')
            self.quarter = str(backup_creation_date.year) + str(int((backup_creation_date.month - 1) / 3 + 1))
            self.year = backup_creation_date.year
        else:
            print('cant compute field values ')
            
    
    host = fields.Char('Host', help='The host from where the backup was taken')
    port = fields.Char('Port', help='The port using which the backup was taken')
    name = fields.Char('Database', help='The database from which backup was taken')
    path_db_backup = fields.Char(string='Backup Link', help='location of the backup file on local storage on the host machine')
    backup_file_name = fields.Char(string='Backup File Name', help='backup file name')
    first_backup = fields.Datetime(string='First Backup', invisible=True)
    latest_backup = fields.Datetime(string='Latest Backup', invisible=True)
    backup_creation_time = fields.Datetime(string='Backup Creation Time', default=fields.Datetime.now(), help='The time at which backup was taken/created')
    store_values_flag = True
    hour = fields.Char(string='Hour', compute='_get_date_parameters', store=True)
    day = fields.Integer(string='Day', compute='_get_date_parameters', store=True)
    week = fields.Integer(string='Week', compute='_get_date_parameters', store=True)
    month = fields.Integer(string='Month', compute='_get_date_parameters', store=True)
    quarter = fields.Integer(string='Quarter', compute='_get_date_parameters', store=True)
    year = fields.Integer(string='Year', compute='_get_date_parameters', store=True)
    backup_action = fields.Selection([('Create', 'Backup Created'), ('Delete', 'Backup Deleted')], 'Backup Action')
    backup_config =  fields.Many2one('db.backup.configuration', string='Backups Schedule', help='The backup configuration record as a result of which the backup was created')
    stored_on_local_storage = fields.Boolean(string='Available on local Storage', default=True, help='Backup is stored on the host machine')
    created_on_local_storage = fields.Boolean(string='Created on local Storage', default=True, help='Backup is stored on the host machine')
    stored_on_google_drive = fields.Boolean(string='Available on Google Drive', compute='_get_google_drive_status', store=True, help='Whether backup is available on google drive or not')
    created_on_google_drive = fields.Boolean(string='Created on Google Drive', compute='_get_google_drive_status', store=True, help='Whether backup was or is available on google drive or not')
    file_uploaded_to_google_drive_accounts = fields.Many2many(comodel_name='db.backup.google.account', relation='backup_file_google_drive_rel', column1='backup_rec_id', column2='google_drive_rec_id', string='File Uploaded to Google Drives')
    file_removed_from_google_drive_accounts = fields.Many2many(comodel_name='db.backup.google.account', relation='backup_file_removed_google_drive_rel', column1='backup_rec_id', column2='google_drive_rec_id', string='File Removed From Google Drives')
    stored_on_sftp_server = fields.Boolean(string='Stored on SFTP Server', compute='_get_sftp_status', store=True, help='Whether backup is available on remote SFTP storage or not')
    created_on_sftp_server = fields.Boolean(string='Created on SFTP Server', compute='_get_sftp_status', store=True, help='Whether backup was or is available on remote SFTP storage or not')
    uploaded_to_sftp_server = fields.Many2many(comodel_name='db.backup.remote.server.logins', relation='backup_file_sftp_server_rel', column1='backup_rec_id', column2='sftp_server_rec_id', string='File Uploaded to SFTP Servers')
    removed_from_sftp_server = fields.Many2many(comodel_name='db.backup.remote.server.logins', relation='backup_file_removed_sftp_server_rel', column1='backup_rec_id', column2='sftp_server_rec_id', string='File Removed From SFTP Servers')
    google_drive_uploads = fields.One2many(comodel_name='db.backup.google.drive.link', inverse_name='backup_rec_id', string='Google Drive Uploads')
    retained_fiscal_year_backup = fields.Boolean(string='End of fiscal Year Backup', help='Whether backup is to be retained from fiscal year end')
    
    @api.one
    @api.depends('uploaded_to_sftp_server', 'removed_from_sftp_server')
    def _get_sftp_status(self):
        if self.uploaded_to_sftp_server:
            self.stored_on_sftp_server = True
            self.created_on_sftp_server = True
        else:
            self.stored_on_sftp_server = False
            if self.removed_from_sftp_server:
                self.created_on_sftp_server = True
    
    @api.one
    @api.depends('file_uploaded_to_google_drive_accounts', 'file_removed_from_google_drive_accounts')
    def _get_google_drive_status(self):
        if self.file_uploaded_to_google_drive_accounts:
            self.stored_on_google_drive = True
            self.created_on_google_drive = True
        else:
            self.stored_on_google_drive = False
            if self.file_removed_from_google_drive_accounts:
                self.created_on_google_drive = True

    @api.model
    def create(self, values):
        created_rec = super(dbBackups, self).create(values)
        return created_rec

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def create(self, vals):
        result = super(ResConfigSettings, self).create(vals)
        if vals.get('fiscalyear_last_day') or vals.get('fiscalyear_last_month'):
            #update the cron to be run at the specified time
            if not vals.get('fiscalyear_last_day'):
                vals['fiscalyear_last_day'] = self.env.user.company_id.fiscalyear_last_day
            if not vals.get('fiscalyear_last_month'):
                vals['fiscalyear_last_month'] = self.env.user.company_id.fiscalyear_last_month
            fiscal_year_backup_cron_obj = self.env['ir.model.data'].get_object('auto_backup','fiscal_year_backup_scheduler')
            fiscal_year_backup_cron_obj.nextcall = str(datetime.datetime.now().year) + '-' + str(vals.get('fiscalyear_last_month')) + '-' + str(vals.get('fiscalyear_last_day')) + ' 23:59:00'
        return result
    
class dbBackupConfgiuration(models.Model):
    
    _name = 'db.backup.configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    @api.multi
    def _get_db_name(self):
        dbName = self._cr.dbname
        return dbName

    @api.multi
    def _get_backup_path(self):
        if getpass.getuser():
            backup_path = '/opt/'+ str(getpass.getuser()) +'/backups'
        else:
            backup_path = '/home/backups'
        return backup_path
    
    @api.multi
    def _get_default_cron_job_id(self):
        return self.env.ref('auto_backup.backup_scheduler').id
    
    host = fields.Char('Host', default='localhost', readonly=True, track_visibility='always', help='The host where the database is hosted from which backups will be taken')
    port = fields.Char('Port', default=lambda *self: tools.config['http_port'], readonly=True, track_visibility='always', help='Odoo XMLRPC port used to connect to the host')
    name = fields.Char('Database', default=_get_db_name, readonly=True, track_visibility='always', help='The database which needs to be backed up')
    folder = fields.Char('Backup Directory', required=True, default=_get_backup_path, track_visibility='always', help='The location where backup files will be stored on local storage')
    backup_type = fields.Selection([('zip', 'Zip'), ('dump', 'Dump')], 'Backup Type', required=True, default='zip', track_visibility='always', help='The type of backup whether SQL dump only or a zip file including the file store')
    autoremove = fields.Boolean('Auto. Remove Backups', track_visibility='always', help='Remove old backups retaining the ones covered under the defined backups retention policy')
    backup_remove_option = fields.Many2one('db.backup.options', string='Backup Retention Policy', track_visibility='always')
    
    # Columns for external server (SFTP)
    sftp_write = fields.Boolean('Backup on Remote', track_visibility='always', help='Enable/Disable uploading of backups to remote SFTP storage')
    remote_servers = fields.One2many('db.backup.remote.server.logins', 'name', string='Backup Notification', track_visibility='always', help='Configurations for Remote SFTP servers')
    email_upon_backpfail = fields.Boolean('E-mail on backup fail', default=False, track_visibility='always', help='Send message to specified email accounts when the system fails to take a backup')
    email_accounts = fields.Many2one('db.backup.email.accounts', string='Email Account', track_visibility='always', help='Email address used to send emails informing about backup failures')
    emails_to_notify = fields.Many2many('res.partner', 'backup_res_partner_rel', 'partner_id', 'backup_id', string='Partners', track_visibility='always', help='Partners who will be notified about failures in creating backups')
    linked_google_drives = fields.One2many('db.backup.google.account', 'name', string='Google Drive', track_visibility='always', help='Google Drive accounts where backups will be uploaded')
    gdrive_write = fields.Boolean('Backup on G-Drive', track_visibility='always', help='Upload backups to Google Drive')
    first_backup = fields.Datetime(string='First Backup')
    latest_backup = fields.Datetime(string='Latest Backup', track_visibility='always')
    comments = fields.Text('Comments')
    interval_number = fields.Integer(default=1, help="Take Backups every x.", track_visibility='always', related='backup_cron_job.interval_number')
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='days', track_visibility='always', related='backup_cron_job.interval_type')
    nextcall = fields.Datetime(string='Next Backup On', required=True, default=fields.Datetime.now, track_visibility='always', 
                               related='backup_cron_job.nextcall', help='The scheduled time for the next upcoming backup')
    backup_cron_job = fields.Many2one('ir.cron', string='Backup Cron Job', default=_get_default_cron_job_id, readonly=True)
    backups_created = fields.One2many(comodel_name='db.backups', inverse_name='backup_config', string='Backups Created', readonly=True, help='Backups of the DB created by the system')
    
    @api.one
    @api.constrains('name')
    def _check_unique_constraint(self):
        record = self.search([('name', '=', self.name)])
        if len(record) > 1:
            raise ValidationError('Backups already configured for ' + str(self.name) + ' database.\n\nKindly modify the existing record instead of creating a new one.')
    
    @api.model
    def create(self, values):
        if 'linked_google_drives' in values:
            discard_child_vals = []
            for drive_rec_tuple in values['linked_google_drives']:
                if len(drive_rec_tuple) > 2:
                    if drive_rec_tuple[0] != 1:
                        continue
                    if type(drive_rec_tuple[2]) is dict:
                        new_rec_val = (0, _, drive_rec_tuple[2])
                        discard_child_vals.append(drive_rec_tuple)
                        values['linked_google_drives'].append(new_rec_val)
            if discard_child_vals:
                for vals_discard in discard_child_vals:
                    for gdrive_rec in self.env['db.backup.google.account'].search([('id', '=', vals_discard[1])]):
                        #_logger.info('Triggering Unlink for linked google drive account ' + str(gdrive_rec))
                        for drive_rec_tuple in values['linked_google_drives']:
                            if drive_rec_tuple[0] == 4 and drive_rec_tuple[1] == gdrive_rec.id:
                                values['linked_google_drives'].remove(drive_rec_tuple)
                        gdrive_rec.unlink()
                        
                    values['linked_google_drives'].remove(vals_discard)
        created_rec = super(dbBackupConfgiuration, self).create(values)
        return created_rec

    @api.one
    def write(self, values):
        self.clear_caches()
        remove_unnecessary_account = []
        for linked_drive_rec in self.linked_google_drives:
            if not linked_drive_rec.dbbackup_google_drive_authorization_code:
                remove_unnecessary_account.append((2, linked_drive_rec.id))
        if 'linked_google_drives' in values:
            for drive_rec_tuple in values['linked_google_drives']:
                gdrive_records_to_be_linked = gdrive_records_to_be_updated = gdrive_records_to_be_removed = []
                if len(drive_rec_tuple) > 2:
                    if drive_rec_tuple[0] > 0:
                        if drive_rec_tuple[0] == 1:
                            gdrive_records_to_be_updated.append(drive_rec_tuple[1])
                            if type(drive_rec_tuple[2]) is dict:
                                if 'dbbackup_google_drive_authorization_code' in drive_rec_tuple[2]:
                                    if drive_rec_tuple[2]['dbbackup_google_drive_authorization_code']:
                                        if (2, drive_rec_tuple[1]) in remove_unnecessary_account:
                                             remove_unnecessary_account.remove((2, drive_rec_tuple[1]))
                        elif drive_rec_tuple[0] == 2:
                            gdrive_records_to_be_removed.append(drive_rec_tuple[1])
                        elif drive_rec_tuple[0] == 4:
                            gdrive_records_to_be_linked.append(drive_rec_tuple[1])
                        continue
                    if type(drive_rec_tuple[2]) is dict:
                        #_logger.info('Processing Drive Info ' + str(drive_rec_tuple[2]))
                        if 'dbbackup_google_drive_authorization_code' in drive_rec_tuple[2]:
                            existing_record_found = self.linked_google_drives.search([('dbbackup_google_drive_authorization_code', '=', drive_rec_tuple[2]['dbbackup_google_drive_authorization_code'])])
                            if existing_record_found:
                                values['linked_google_drive'].remove(drive_rec_tuple)
                            for linked_drive_rec in self.linked_google_drives:
                                if linked_drive_rec.dbbackup_google_drive_authorization_code == drive_rec_tuple[2]['dbbackup_google_drive_authorization_code']:
                                    values['linked_google_drive'].remove(drive_rec_tuple)
            if remove_unnecessary_account:
                if values['linked_google_drives']:
                    values['linked_google_drives'].extend(remove_unnecessary_account)
                else:
                    values['linked_google_drives'] = remove_unnecessary_account
        #_logger.info('Updating the db backups config record with values ' + str(values))
        return super(dbBackupConfgiuration, self).write(values)

    @api.multi
    def get_db_list(self, host, port, context={}):
        url = 'http://' + host + ':' + port
        conn = xmlrpclib.ServerProxy(url + '/xmlrpc/db')
        db_list = execute(conn, 'list')
        return db_list

    @api.one
    @api.constrains('name')
    def _check_db_exist(self):
        db_list = self.get_db_list(self.host, self.port)
        if self.name in db_list:
            return True
        raise ValidationError('Error ! No such database exists!')
    
    @api.multi
    def run_manual_backup(self):
        self.schedule_backup()
    
    @api.model
    def fiscal_year_schedule_backup(self):
        if datetime.datetime.now().month == self.env.user.company_id.fiscalyear_last_month and datetime.datetime.now().day==self.env.user.company_id.fiscalyear_last_day:
            self.schedule_backup(fiscal_year_end_backup=True)
    
    @api.model
    def schedule_backup(self, fiscal_year_end_backup=False):
        conf_ids = self.search([])
        for rec in conf_ids:
            db_list = self.get_db_list(rec.host, rec.port)
            if rec.name in db_list:
                try:
                    if not os.path.isdir(rec.folder):
                        os.makedirs(rec.folder)
                except:
                    raise ValidationError(_('Could Not Create a Local Folder for Backup'))
                
                # Create name for backup file.
                curr_datetime = datetime.datetime.now()                
                _logger.info("Started Database Backup at: ",)
                bkp_file = '%s_%s.%s' % (curr_datetime.strftime('%Y_%m_%d_%H_%M_%S'), rec.name, rec.backup_type)
                file_path = os.path.join(rec.folder, bkp_file)
                backup_format=rec.backup_type
                new_db_backup_rec = None
                try:
                    stream = open(file_path,'wb')
                    service.db.dump_db(rec.name, stream, backup_format=backup_format)
                    stream.flush()
                    if stream:
                        db_backup = None
#                         if not db_backup:
#                             first_backup = datetime.datetime.now()
#                         else:
#                             first_backup = db_backup[0].first_backup
                        values = {'host': rec.host,
                                  'port': rec.port,
                                  'name': rec.name,
                                  'path_db_backup': file_path,
                                  'backup_file_name': bkp_file,
                                  'backup_creation_time': datetime.datetime.now(),
                                  'backup_action':'Create',
                                  'backup_config': rec.id,
                                  'stored_on_local_storage': True,
                                  'created_on_local_storage': True,
                                  'retained_fiscal_year_backup': fiscal_year_end_backup 
                                  }
                        new_db_backup_rec = self.env['db.backups'].create(values)
                        vals_write ={#'first_backup':first_backup,
                                     'latest_backup': datetime.datetime.now(),
                                     } 
                        rec.write(vals_write)
                    stream.close()
                    if stream:
                        print ('success')
                except:
                    #------------- Sending Email to the concerned Partners ------------------
                    if rec.email_upon_backpfail:
                        text = 'The local backup for ' +str(rec.name)+ ' database has failed'
                        if rec.email_accounts and rec.emails_to_notify:
                            _logger.info('sending fail mail')
                            self.env['db.backup.email.accounts'].send_fail_email(text, rec.email_accounts.id)
                        else:
                            raise ValidationError(_('Email Account Not Configured for sending mails'))
                            _logger.debug("Couldn't backup database %s. Bad database administrator password for server running at http://%s:%s" % (rec.name, rec.host, rec.port))
                    continue
                if new_db_backup_rec:
                    if rec.gdrive_write is True:
                        for rec_server in rec.linked_google_drives:
                            rec_server.shecdule_google_grive_backup(bkp_file, new_db_backup_rec)
                            new_db_backup_rec.write({'stored_on_google_drive': True})
                    
                    if rec.sftp_write is True:
                        for rec_server in rec.remote_servers:
                            rec_server.copy_file_to_remote_sftp(bkp_file, new_db_backup_rec)
            else:
                _logger.debug("database %s doesn't exist on http://%s:%s" % (rec.name, rec.host, rec.port))

class dbBackupremoteserverLogins(models.Model):
    
    _name = 'db.backup.remote.server.logins'

    name = fields.Many2one('db.backup.configuration', string='Backup Configurations')
    remote_name = fields.Char(string='Remote Name', help='Name/Title of the remote SFTP server')
    sftp_path = fields.Char(string='Remote Path', readonly=True, help='The path where backups will be stored on the remote server')
    sftp_host = fields.Char(string='IP Address', help='IP Address of the SFTP server')
    sftp_port = fields.Integer(string='SFTP Port', default=22, help='Connection port')
    sftp_user = fields.Char(string='Remote User', help='Username used as login to the server')
    sftp_password = fields.Char(string='Remote User Password', size=64, help='password for server login')
    auto_remove = fields.Boolean(string='Auto Remove Backups', help='Remove backups not covered by the backups retention policy')
    backup_remove_option_sftp = fields.Many2one('db.backup.options', string='Backup Retention Policy', help='Policy containing rules that the number of backups that are to be retained in the specified time periods')
    uploaded_backup_files = fields.Many2many(comodel_name='db.backups', relation='backup_file_sftp_server_rel', column1='sftp_server_rec_id', column2='backup_rec_id', string='File Uploaded to SFTP Servers', readonly=True, help='The backup files that have been uploaded to the server')

    @api.model
    def create(self, values):
        if 'sftp_user' in values:
            sftpuser = values['sftp_user']
            values['sftp_path'] = '/home/'+ str(sftpuser) +'/backups'
        else:
            values['sftp_path'] = '/home/backups'
        if 'sftp_host' in values:
            if values['sftp_host']:
                if not 'Copy' in values['sftp_host']:
                    if values['sftp_host']:
                        values['sftp_host'] = "".join(values['sftp_host'].split())
                    sftp_host = values['sftp_host']
                    if not self.validate_ip_address(sftp_host):
                        raise ValidationError('Invalid IP Address')
                    ip_address_found = self.search([('sftp_host', '=like', sftp_host + str('%'))])
                    if ip_address_found:
                        raise ValidationError('A record with the same IP address already exists, IP address must be unique')
        created_rec = super(dbBackupremoteserverLogins, self).create(values)
        return created_rec

    @api.multi
    def validate_ip_address(self, ip_address_string):
        a = ip_address_string.split('.')
        if len(a) != 4:
            return False
        for x in a:
            if not x.isdigit():
                return False
            i = int(x)
            if i < 0 or i > 255:
                return False
        return True

    @api.one
    @api.constrains('remote_name', 'sftp_host')
    def _check_unique_constraint(self):
        record = self.search(['|', ('remote_name', '=', self.remote_name), ('sftp_host', '=', self.sftp_host)])
        if len(record) > 1:
            raise ValidationError('Remote Server already exists and violates unique constraint')

    @api.multi
    def test_sftp_connection(self, context=None):
        self.ensure_one()
        # Check if there is a success or fail and write messages
        messageTitle = ""
        messageContent = ""
        error = ""
        has_failed = False
        for rec in self:
            ipHost = rec.sftp_host
            usernameLogin = rec.sftp_user
            passwordLogin = rec.sftp_password
            # Connect with external server over SFTP, in order to check if the conneciton works successfully
            try:
                s = paramiko.SSHClient()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                s.connect(ipHost, 22, usernameLogin, passwordLogin, timeout=10)
                s.open_sftp()
                messageTitle = _("Connection Test Succeeded!\nEverything seems properly set up for FTP back-ups!")
            except Exception as e:
                _logger.critical('There was a problem connecting to the remote ftp: ' + str(e))
                error += str(e)
                has_failed = True
                messageTitle = _("Connection Test Failed!")
                if len(rec.sftp_host) < 8:
                    messageContent += "\nYour IP address seems to be too short.\n"
                messageContent += _("Here is what we got instead:\n")
            finally:
                if s:
                    s.close()

        if has_failed:
            raise Warning(messageTitle + '\n\n' + messageContent + "%s" % str(error))
        else:
            raise Warning(messageTitle + '\n\n' + messageContent)

    @api.one        
    def copy_file_to_remote_sftp(self, backup_file_name, backup_rec):
        #----------------------- Remote Server Backup Write ------------------------------------------
        rec_serv = self
        try:
            # Store all values in variables
            dirr = rec_serv.name.folder
            pathToWriteTo = rec_serv.sftp_path
            ipHost = rec_serv.sftp_host
            usernameLogin = rec_serv.sftp_user
            passwordLogin = rec_serv.sftp_password
            _logger.debug('sftp remote path: %s' % pathToWriteTo)
            try:
                s = paramiko.SSHClient()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                s.connect(ipHost, 22, usernameLogin, passwordLogin, timeout=20)
                sftp = s.open_sftp()
            except Exception as error:
                _logger.critical('Error connecting to remote server'. str(error))
            
            try:
                sftp.chdir(pathToWriteTo)
            except IOError:
                # Create directory and subdirs if they do not exist.
                currentDir = ''
                for dirElement in pathToWriteTo.split('/'):
                    currentDir += dirElement + '/'
                    try:
                        sftp.chdir(currentDir)
                    except:
                        _logger.info('(Part of the) path didn\'t exist. Creating it now at ' + currentDir)
                        # Make directory and then navigate into it
                        sftp.mkdir(currentDir, 777)
                        sftp.chdir(currentDir)
                        pass
                    
            sftp.chdir(pathToWriteTo)
            # Loop over all files in the directory.
            
            fullpath = os.path.join(dirr, backup_file_name)
            if os.path.isfile(fullpath):
                try:
                    sftp.stat(os.path.join(pathToWriteTo, backup_file_name))
                    _logger.debug('File %s already exists on the remote FTP Server ------ skipped' % fullpath)
                    backup_rec.write({'uploaded_to_sftp_server': [(4, rec_serv.id)]})
                    # This means the file does not exist (remote) yet!
                except IOError:
                    try:
                        # sftp.put(fullpath, pathToWriteTo)
                        sftp.put(fullpath, os.path.join(pathToWriteTo, backup_file_name))
                        _logger.info('Copying File % s------ success' % fullpath)
                        backup_rec.write({'uploaded_to_sftp_server': [(4, rec_serv.id)]})
                    except Exception as err:
                        _logger.critical('We couldn\'t write the file to the remote server. Error: ' + str(err))
            
            # Navigate in to the correct folder.
            sftp.chdir(pathToWriteTo)
            sftp.close()
            
        except Exception as e:
            #------------- Sending Email to the concerned Partners ------------------
            if rec_serv.name.email_upon_backpfail:
                text = 'The backup on ' +str(rec_serv.remote_name)+ 'for '+str(rec_serv.name.name)+' database has failed'
                if rec_serv.name.email_accounts and rec_serv.name.emails_to_notify:        
                    _logger.info('sending fail mail')
                    self.env['db.backup.email.accounts'].send_fail_email(text, rec_serv.name.email_accounts.id)                        
                else:
                    raise ValidationError(_('Email For sending message is not yet configured please configure email first'))
            _logger.debug('Exception! We couldn\'t back up to the FTP server..', str(e))

    @api.one        
    def remove_file_from_sftp_storage(self, backup_rec_id):
        #----------------------- Remote Server Backup Write ------------------------------------------
        rec_serv = self
        backup_rec = self.env['db.backups'].browse(backup_rec_id)
        try:
            # Store all values in variables
            dirr = rec_serv.name.folder
            pathToWriteTo = rec_serv.sftp_path
            ipHost = rec_serv.sftp_host
            usernameLogin = rec_serv.sftp_user
            passwordLogin = rec_serv.sftp_password
            _logger.debug('sftp remote path: %s' % pathToWriteTo)
            try:
                s = paramiko.SSHClient()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                s.connect(ipHost, 22, usernameLogin, passwordLogin, timeout=20)
                sftp = s.open_sftp()
            except Exception as error:
                _logger.critical('Error connecting to remote server'. str(error))
            
            sftp.chdir(pathToWriteTo)
            backup_file_name = backup_rec.backup_file_name
            fullpath = os.path.join(dirr, backup_file_name)
            #if os.path.isfile(fullpath):
            try:
                sftp.stat(os.path.join(pathToWriteTo, backup_file_name))
                _logger.debug('File %s exists on the remote FTP Server ------ Removing it' % fullpath)
                sftp.remove(os.path.join(pathToWriteTo, backup_file_name))
                _logger.info('Removing File % s------ success' % fullpath)
                # This means the file does not exist (remote) yet!
            except IOError as err:
                _logger.critical('We couldn\'t remove the file from remote server. Error: ' + str(err))
            backup_rec.write({'uploaded_to_sftp_server': [(3, rec_serv.id)], 'removed_from_sftp_server': [(4, rec_serv.id)]})
            # Navigate in to the correct folder.
            sftp.chdir(pathToWriteTo)
            sftp.close()
            
        except Exception as e:
            _logger.critical('Exception! We couldn\'t remove file from SFTP server..', str(e))

    @api.multi        
    def schedule_remote_backup(self):
        #----------------------- Remote Server Backup Write ------------------------------------------
        rec_serv = self
        try:
            # Store all values in variables
            dirr = rec_serv.name.folder
            pathToWriteTo = rec_serv.sftp_path
            ipHost = rec_serv.sftp_host
            usernameLogin = rec_serv.sftp_user
            passwordLogin = rec_serv.sftp_password
            _logger.debug('sftp remote path: %s' % pathToWriteTo)
            try:
                s = paramiko.SSHClient()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                s.connect(ipHost, 22, usernameLogin, passwordLogin, timeout=20)
                sftp = s.open_sftp()
            except Exception as error:
                _logger.critical('Error connecting to remote server'. str(error))
            
            try:
                sftp.chdir(pathToWriteTo)
            except IOError:
                # Create directory and subdirs if they do not exist.
                currentDir = ''
                for dirElement in pathToWriteTo.split('/'):
                    currentDir += dirElement + '/'
                    try:
                        sftp.chdir(currentDir)
                    except:
                        _logger.info('(Part of the) path didn\'t exist. Creating it now at ' + currentDir)
                        # Make directory and then navigate into it
                        sftp.mkdir(currentDir, 777)
                        sftp.chdir(currentDir)
                        pass
                    
            sftp.chdir(pathToWriteTo)
            # Loop over all files in the directory.
            
            for f in os.listdir(dirr):
                if rec_serv.name.name in f:
                    fullpath = os.path.join(dirr, f)
                    if os.path.isfile(fullpath):
                        try:
                            sftp.stat(os.path.join(pathToWriteTo, f))
                            _logger.debug('File %s already exists on the remote FTP Server ------ skipped' % fullpath)
                            # This means the file does not exist (remote) yet!
                        except IOError:
                            try:
                                # sftp.put(fullpath, pathToWriteTo)
                                sftp.put(fullpath, os.path.join(pathToWriteTo, f))
                                _logger.info('Copying File % s------ success' % fullpath)
                            except Exception as err:
                                _logger.critical('We couldn\'t write the file to the remote server. Error: ' + str(err))
            
            # Navigate in to the correct folder.
            sftp.chdir(pathToWriteTo)
            sftp.close()
            
        except Exception as e:
            #------------- Sending Email to the concerned Partners ------------------
            if rec_serv.name.email_upon_backpfail:
                text = 'The backup on ' +str(rec_serv.remote_name)+ 'for '+str(rec_serv.name.name)+' database has failed'
                if rec_serv.name.email_accounts and rec_serv.name.emails_to_notify:        
                    _logger.info('sending fail mail')
                    self.env['db.backup.email.accounts'].send_fail_email(text, rec_serv.name.email_accounts.id)                        
                else:
                    raise ValidationError(_('Email For sending message is not yet configured please configure email first'))
            _logger.debug('Exception! We couldn\'t back up to the FTP server..', str(e))
    
    @api.model
    def apply_sftp_retention_policy_remove_backups(self):
        sftp_storage_requiring_backup_removal = self.search([('auto_remove', '=', True)])
        if sftp_storage_requiring_backup_removal:
            for sftp_storage in sftp_storage_requiring_backup_removal:
                if sftp_storage.backup_remove_option_sftp:
                    if sftp_storage.backup_remove_option_sftp.preceding_periods_backups_retention:
                        for preceding_period_backup_retention_rule in sftp_storage.backup_remove_option_sftp.preceding_periods_backups_retention:
                            backups_to_remove = preceding_period_backup_retention_rule.get_list_of_backups_to_remove(force_storage='sftp_storage')[0]
                            if backups_to_remove:
                                for backup in backups_to_remove:
                                    if backup['id'] in sftp_storage.uploaded_backup_files.ids():
                                        sftp_storage.remove_file_from_sftp_storage(backup['id'])
    
class dbBackupGoogleAccounts(models.Model):

    _name = 'db.backup.google.account'
        
    def get_google_scope(self):
        return 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file'

    def _get_gd_backup_path(self, context=None):
        dbName = self.env.cr.dbname
        return 'backup/'+dbName

    name = fields.Many2one('db.backup.configuration', string='Backup Config', help='Name / Title of the Google Drive account')    
    dbbackup_google_drive_directory = fields.Char(string='Google Drive Path', default=_get_gd_backup_path, help='The folder on Google Drive where backups will be uploaded')
    auto_remove = fields.Boolean(string='Auto Remove Backups', help='Remove old backups that are not covered by the backups retention policy')
    backup_remove_option_gdrive = fields.Many2one('db.backup.options', string='Backup Retention Policy', help='Policy specifying how many backups are to be retained under the specified time periods')   
    dbbackup_google_drive_authorization_code = fields.Char(string='Authorization Code', help='Google Drive authorization code')
    dbbackup_google_drive_uri = fields.Char(compute='_compute_drive_uri', string='URL', help="The URL to generate the authorization code from Google")
    daysto_remove_gdrive_backup = fields.Integer('Remove Backups For X Days', invisible=True)
    uploaded_backup_files = fields.Many2many(comodel_name='db.backups', relation='backup_file_google_drive_rel', column1='google_drive_rec_id', column2='backup_rec_id', string='Files Uploaded to Account', readonly=True,
                                             help='Backup files uploaded to the Google Drive account')
    
    def generate_refresh_token(self, service, authorization_code):
        Parameters = self.env['ir.config_parameter'].sudo()
        client_id = Parameters.get_param('backup_google_drive_client_id')
        client_secret = Parameters.get_param('backup_google_drive_client_secret')
        redirect_uri = Parameters.get_param('backup_google_redirect_uri')
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8","USER-AGENT":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 Safari/537.36"}
        data = {
            'code': authorization_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': "authorization_code"
        }
        content_length=len(parse.urlencode(data))
        data['content-length'] = str(content_length)
        try:
            req = requests.post(GOOGLE_TOKEN_ENDPOINT, data=data, headers=headers, timeout=TIMEOUT)
            req.raise_for_status()
            content = req.json()
        except Exception:
            raise ValidationError(_('Token Generation Failed'))
        return content.get('refresh_token')

    def _get_google_token_uri(self, service, scope):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        encoded_params = urls.url_encode({
            'scope': scope,
            'redirect_uri': get_param('backup_google_redirect_uri'),
            'client_id': get_param('backup_google_drive_client_id'),
            'response_type': 'code',
        })
        return '%s?%s' % (GOOGLE_AUTH_ENDPOINT, encoded_params)

    @api.multi
    def action_open_new_tab(self):
        dbbackup_google_drive_uri = self._get_google_token_uri('drive', scope=self.get_google_scope())
        record_url = str(dbbackup_google_drive_uri)
        client_action = {
                'type': 'ir.actions.act_url',
                'name': "db.backup.google.account",
                'target': 'new',
                'url': record_url,
                }
        return client_action

    @api.one
    @api.depends('dbbackup_google_drive_authorization_code', 'name')
    def _compute_drive_uri(self):
        dbbackup_google_drive_uri = self._get_google_token_uri('drive', scope=self.get_google_scope())
        if dbbackup_google_drive_uri:
            self.dbbackup_google_drive_uri = dbbackup_google_drive_uri

    @api.model
    def create(self, values):
        _logger.info('Creating backup google drive account rec with values ' + str(values))
        created_rec = super(dbBackupGoogleAccounts, self).create(values)
        rec = self.browse(created_rec.id)
        if values['dbbackup_google_drive_authorization_code'] and rec.dbbackup_google_drive_authorization_code:
            self.set_google_authorization_code(created_rec.id)
        return created_rec
        
    def set_google_authorization_code(self, idd):
        get_param = self.env['ir.config_parameter'].sudo().get_param        
        for rec in self.browse(idd):
            auth_code = rec.dbbackup_google_drive_authorization_code
            if auth_code and auth_code != get_param('dbbackup_google_drive_authorization_code'):
                refresh_token = self.generate_refresh_token('drive', rec.dbbackup_google_drive_authorization_code)
                params = self.env['ir.config_parameter'].sudo()
                params.set_param('backup_google_drive_authorization_code', auth_code)
                params.set_param('backup_google_drive_refresh_token', refresh_token)
        
    @api.one
    def write(self, values):
        _logger.info('Updating backup google drive account rec with values ' + str(values))
        updated_rec = super(dbBackupGoogleAccounts, self).write(values)
        if 'dbbackup_google_drive_authorization_code' in values:
            if self.dbbackup_google_drive_authorization_code:
                self.set_google_authorization_code(self.id)
        return updated_rec#

    @api.one
    def shecdule_google_grive_backup(self, bkp_file, backup_rec):
        rec = self
        try:
            access_token = self.get_access_token()
            chunk = 536870912
            #get google drive folder id
            parent_folder = 'root'
            try:
                parent_folder = self.get_or_create_parent(create=True)
            except Exception as e:
                _logger.error('error in finding or creating backup folder:')
                raise e
            
            file_name=bkp_file
            file_path = rec.name.folder+'/'+str(bkp_file)
            file_len = os.path.getsize(file_path)
            dbdata = {"title": file_name,
                    "parents": [{"kind":"drive#file","id": parent_folder}]}
            dbdata = json.dumps(dbdata)
            if type(access_token) is list:
                access_token = access_token[0]
            
            headers = {"Content-Type": "application/json; charset=UTF-8", 'X-Upload-Content-Type':'application/zip', 'X-Upload-Content-Length': str(file_len), 'Authorization': 'Bearer ' + access_token}
            _logger.info('opening upload session')
            upload_resp = requests.post('https://www.googleapis.com/upload/drive/v2/files?uploadType=resumable', data=dbdata, headers=headers, timeout=TIMEOUT)
            upload_url = upload_resp.headers.get('Location')
            #Step 2: upload the file
            bkp_stream = open(file_path,'rb')
            max_retrys = 10
            retrys = 0
            finished = 0
            data = bkp_stream.read(chunk)
            _logger.info('uploading the backup')
            while data:
                _logger.info('Uploading Backup to Google Drive')
                to = finished+chunk-1
                if to > file_len: to=file_len-1
                chunk_str = str(finished)+'-'+str(to)+'/'+str(file_len)
                headers = {'Content-Type': 'application/zip',
                           'Content-Length':str(len(data)),
                           'Content-Range': 'bytes '+chunk_str,
                           }
                upload_resp = requests.post(upload_url, data=data, headers=headers, timeout=TIMEOUT)
                _logger.info( '----- uploading chunk '+chunk_str)
                try:
                    retrys = 0
                    _logger.info('finished uploading chunk '+ chunk_str)
                    
                except HTTPError as e:
                    _logger.info('Upload Failed1 '+ str(e))
                    if e.code == 308:
                        retrys = 0
                        _logger.info('finished uploading chunk '+ chunk_str)
                        data = bkp_stream.read(chunk)
                        finished += chunk
                        continue
                    if (e.code == 404):
                        bkp_stream.seek(0)
                        data = bkp_stream.read(chunk)
                        finished = 0
                        file_len = len(bkp_file)
                        _logger.warning('upload failed, restarting from beginning')
                        _logger.info('opening upload session')
                        req = requests.get(upload_url, headers=headers)
                        upload_url = req.headers.get('Location')
                    else:
                        raise e
                    #rec.write({'files_uploaded': [(4, backup_rec.id)]})
                    
                except Exception as e:
                    _logger.info('Upload Failed '+ str(e))
                    if(retrys == max_retrys):
                        _logger.error(chunk_str+' upload failed '+str(retrys)+' times, aborting! : '+ str(e))
                        raise e
                    
                    sleeptime = random.random() + (2**retrys)
                    retrys+=1
                    _logger.warning('upload failed '+str(retrys)+' times, retrying again after '+str(sleeptime)+' seconds')
                    time.sleep(sleeptime)
                    continue
                        
                data = bkp_stream.read(chunk)
                finished += chunk
            backup_rec.write({'file_uploaded_to_google_drive_accounts': [(4, rec.id)]})
            _logger.info('finished uploading backup to google drive ')
            _logger.info('getting id of the recently uploaded file')
            if type(parent_folder) is list:
                parent_folder = parent_folder[0]
            search_q = {'fields':'items(id,title)','q':"mimeType!='application/vnd.google-apps.folder' and '"+parent_folder+"' in parents and 'me' in owners and title = '" + backup_rec.backup_file_name + "'"}
            url = 'https://www.googleapis.com/drive/v2/files?%s'% urls.url_encode(search_q)
            #access_token = self.get_access_token()
            #if type(access_token) is list:
            #    access_token = access_token[0]
            headers = {'Authorization': 'Bearer ' + access_token,
                       'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                       }
            file_response = requests.get(url, headers=headers)
            find_files_body = json.loads(file_response.text)
            if find_files_body:
                file_id = find_files_body['items'][0]['id']
                file_account_link_rec = self.env['db.backup.google.drive.link'].create({'backup_rec_id': backup_rec.id, 'google_drive_rec_id': rec.id, 'google_file_id': file_id})
                
                
        except Exception as e:
            #--------------------Check if the user wants to send email upon failed google drive backup --------------
            _logger.info('Upload Failed1 '+ str(e))
            if rec.name.email_upon_backpfail:
                text = 'The backup on ' +str(rec.dbbackup_google_drive_directory)+ 'for '+str(rec.name.name)+' database has failed'
                if rec.name.email_accounts and rec.name.emails_to_notify:
                    _logger.info('sending fail mail'+ str(e))
                    self.env['db.backup.email.accounts'].send_fail_email(text, rec.name.email_accounts.id)                        
                else:
                    raise ValidationError(_('Email For sending message is not yet configured please configure email first'))

    @api.one
    def get_access_token(self, scope=None, context=None):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        google_drive_refresh_token = get_param('backup_google_drive_refresh_token')
        user_is_admin = self.env['res.users'].has_group('base.group_erp_manager')
        if not google_drive_refresh_token:
            if user_is_admin:
                model, action_id = self.env['ir.model.data'].get_object_reference('auto_backup', 'action_backup')
                msg = "You haven't configured 'Authorization Code' generated from google, Please generate and configure it"
                raise ValidationError(_(str(msg) + str(action_id) + 'Go to the configuration panel'))
            else:
                raise except_orm(_('Error!'), _("Google Drive is not yet configured. Please contact your administrator."))
            
        google_drive_client_id = get_param('backup_google_drive_client_id')
        google_drive_client_secret = get_param('backup_google_drive_client_secret')
        
        data = {
            'client_id': google_drive_client_id,
            'refresh_token': google_drive_refresh_token,
            'client_secret': google_drive_client_secret,
            'scope': scope or 'https://www.googleapis.com/auth/drive',
            'grant_type': "refresh_token"
        }
        content_length=len(parse.urlencode(data))
        data['content-length'] = str(content_length)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}
        try:
            req = requests.post(GOOGLE_TOKEN_ENDPOINT, data=data, headers=headers, timeout=TIMEOUT)
            req.raise_for_status()
            content = req.json()
            
        except urllib.error.HTTPError:
            if user_is_admin:
                model, action_id = self.env['ir.model.data'].get_object_reference('base_setup', 'action_general_configuration')
                msg = _("Something went wrong during the token generation. Please request again an authorization code .")
                raise Warning(msg, action_id, _('Go to the configuration panel'))
            else:
                raise except_orm(_('Error!'), _("Google Drive is not yet configured. Please contact your administrator."))
        return content.get('access_token')

    @api.one
    def get_or_create_parent(self, create=True, context=None):
        parent_folder='root'
        access_token = self.get_access_token(context=self._context)
        rec = self
        if rec.dbbackup_google_drive_directory and len(rec.dbbackup_google_drive_directory.strip()):
            _logger.info('search for backup folder '+rec.dbbackup_google_drive_directory)
            folders = rec.dbbackup_google_drive_directory.strip('/').split('/')
            for folder in folders:
                search_q = {'fields':'items(id,title)','q':"mimeType='application/vnd.google-apps.folder' and '"+parent_folder+"' in parents and 'me' in owners and title = '"+folder+"'"}
                url = 'https://www.googleapis.com/drive/v2/files?%s'% urls.url_encode(search_q)
                if type(access_token) is list:
                    access_token = access_token[0]
                headers = {'Authorization': 'Bearer ' + access_token,
                           'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                           }
                folder_response = requests.get(url, headers=headers)
                find_folder_body = json.loads(folder_response.text)
                    #folder exists
                if find_folder_body['items']:
                    parent_folder = find_folder_body['items'][0]['id']
                    _logger.info('found folder '+folder)
                elif not create:
                    return
                elif create:
                    _logger.info('folder '+folder+' not found, creating it...')
                    #folder does not exist, create it
                    if type(access_token) is list:
                        access_token = access_token[0]
                        
                    create_folder_url = 'https://www.googleapis.com/drive/v2/files'
                    create_folder_headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json', 'Accept': 'text/plain',
                                             'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}
                    create_folder_data=json.dumps({
                                          "title": folder,
                                          "parents": [{"id":parent_folder}],
                                          "mimeType": "application/vnd.google-apps.folder"
                                        })
                    create_folder_res = requests.post(create_folder_url, data=create_folder_data, headers=create_folder_headers, timeout=TIMEOUT)
                    create_folder_body = json.loads(create_folder_res.text)
                    parent_folder = create_folder_body['id']
                    _logger.info('folder '+ folder+ ' created!')
        return parent_folder

    @api.one
    def remove_google_drive_backups(self):
        parent_folder = self.get_or_create_parent(create=True)
        date_to_remove = (datetime.date.today() - datetime.timedelta(days=self.daysto_remove_gdrive_backup)).isoformat()
        if not parent_folder:
            _logger.info('backup folder does not exist no old files to delete')
            return
        
        access_token = self.get_access_token()
        if type(access_token) is list:
            access_token = access_token[0]

        if type(parent_folder) is list:
            parent_folder = parent_folder[0]
        
        #search for old files {id:'',title:''}
        search_q = {'fields':'items(id,title)','q':"mimeType!='application/vnd.google-apps.folder' and '"+parent_folder+"' in parents and 'me' in owners and modifiedDate <= '"+date_to_remove+"'"}
        old_files=[]
        url = 'https://www.googleapis.com/drive/v2/files?%s'% urls.url_encode(search_q)
        
        headers = {'Authorization': 'Bearer ' + access_token,
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                   }
        folder_response = requests.get(url, headers=headers)
        find_old_files_body = json.loads(folder_response.text)
        for item in find_old_files_body['items']:
            old_files.append(item)
            
        #Deleteing old files from google drive ----------
        _logger.info('found the following old files '+str(old_files))
        for f in old_files:
            _logger.info('deleting old files from google drive '+str(f['id']))
            folder_url = 'https://www.googleapis.com/drive/v2/files/%s/trash' % f['id']
            if type(access_token) is list:
                access_token = access_token[0]
            folder_headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json', 'Accept': 'text/plain',
                                     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}
            requests.post(folder_url, data='', headers=folder_headers, timeout=TIMEOUT)
        _logger.info('deleted all old files successfully')

    @api.one
    def remove_backup_file_from_google_drive(self, backup_rec_id):
        parent_folder = self.get_or_create_parent(create=True)
        date_to_remove = (datetime.date.today() - datetime.timedelta(days=self.daysto_remove_gdrive_backup)).isoformat()
        if not parent_folder:
            _logger.info('backup folder does not exist no old files to delete')
            return
        
        access_token = self.get_access_token()
        if type(access_token) is list:
            access_token = access_token[0]

        if type(parent_folder) is list:
            parent_folder = parent_folder[0]
        backup_rec = self.env['db.backups'].browse(backup_rec_id)
        backup_file_name = backup_rec.backup_file_name 
        #search for old files {id:'',title:''}
        search_q = {'fields':'items(id,title)','q':"mimeType!='application/vnd.google-apps.folder' and '"+parent_folder+"' in parents and 'me' in owners and name = " + backup_file_name}
        old_files=[]
        url = 'https://www.googleapis.com/drive/v2/files?%s'% urls.url_encode(search_q)
        
        headers = {'Authorization': 'Bearer ' + access_token,
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                   }
        folder_response = requests.get(url, headers=headers)
        find_old_files_body = json.loads(folder_response.text)
        if 'items' in find_old_files_body:
            for item in find_old_files_body['items']:
                old_files.append(item)
            
            #Deleteing old files from google drive ----------
            _logger.info('found the following old files '+str(old_files))
            for f in old_files:
                _logger.info('deleting old file from google drive '+str(f['id']) + ' -> ' + backup_file_name)
                folder_url = 'https://www.googleapis.com/drive/v2/files/%s/trash' % f['id']
                if type(access_token) is list:
                    access_token = access_token[0]
                folder_headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json', 'Accept': 'text/plain',
                                         'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}
                requests.post(folder_url, data='', headers=folder_headers, timeout=TIMEOUT)
            backup_rec.write({'file_uploaded_to_google_drive_accounts':[(3, self.id)], 'file_removed_from_google_drive_accounts':[(4, self.id)]})
            file_google_drive_link_found = self.env['db.backup.google.drive.link'].search([('backup_rec_id', '=', backup_rec.id), ('google_drive_rec_id', '=', self.id)])
            if file_google_drive_link_found:
                file_google_drive_link_found.unlink()
                #self.write({'files_uploaded': [(3, backup_rec.id)]})
            _logger.info('Successfully deleted old file ' + backup_file_name)
    
    @api.model
    def apply_account_retention_policy_remove_backups(self):
        accounts_requiring_backup_removal= self.search([('auto_remove', '=', True)])
        if accounts_requiring_backup_removal:
            for google_drive_account in accounts_requiring_backup_removal:
                if google_drive_account.backup_remove_option_gdrive:
                    if google_drive_account.backup_remove_option_gdrive.preceding_periods_backups_retention:
                        for preceding_period_backup_retention_rule in google_drive_account.backup_remove_option_gdrive.preceding_periods_backups_retention:
                            backups_to_remove = preceding_period_backup_retention_rule.get_list_of_backups_to_remove(force_storage='google_drive')[0]
                            if backups_to_remove:
                                for backup in backups_to_remove:
                                    if backup['id'] in google_drive_account.uploaded_backup_files.mapped('id'):
                                        google_drive_account.remove_backup_file_from_google_drive(backup['id'])
    
class dbBackupEmailAccounts(models.Model):

    _name = 'db.backup.email.accounts'

    smtp_server = fields.Char(string='SMTP server', help='SMTP server used to route/send emails')
    smtp_port = fields.Char(string='SMTP port', help='port used for SMTP connection')
    smtp_security = fields.Selection([('SSL','SSL'),('None','None')], string='Security', default='SSL', help='SMTP connection security')
    name = fields.Char(string='Email sender', help='Sender Email Address')
    smtp_password = fields.Char(string='Email password', help='Password used to establish the connection and send the message')

    def send_fail_email(self, text, email_account):
        rec = self.browse(email_account)
        db_config = self.env['db.backup.configuration'].search([('email_accounts', '=', email_account)])
        try :
            get_param = self.env['ir.config_parameter'].sudo().get_param
            base_url = get_param('web.base.url')
            text += '\n'+str(base_url)
            msg = MIMEText(text)
            msg['Subject'] = 'Backup Failed Notification'
            msg['From'] = rec.name
            emaillist = []
            for partner in db_config.emails_to_notify:
                emaillist.append(partner.email)
            receivers = emaillist
            string_email = ', '.join(receivers)
            msg['To'] = string_email
            s = None
            if rec.smtp_security == 'SSL' :
                s = smtplib.SMTP_SSL(rec.smtp_server, int(rec.smtp_port))
            else:
                s = smtplib.SMTP(rec.smtp_server, int(rec.smtp_port))
            s.login(rec.name, rec.smtp_password)
            s.sendmail(rec.name, receivers, msg.as_string())
            s.quit()
        except Exception as ex:
            print ('Error: ' + str(ex) +'-'+ str(ex))

    @api.one
    @api.constrains('name')
    def _check_unique_constraint(self):
        record = self.search([('name', '=', self.name)])
        if len(record) > 1:
            raise ValidationError('Email already exists and violates unique constraint')

