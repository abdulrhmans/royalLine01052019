# -*- coding: utf-8 -*-

from __future__ import division
from datetime import *
import pytz

from odoo import api, fields, models, exceptions, _


class CalendarResource(models.Model):

    _inherit = 'resource.calendar'

    max_late_minutes = fields.Float('Max Late Minutes', default=5.0)
    break_duration = fields.Float("Break Duration", default=0.0)

    
class hr_attendance(models.Model):

    _inherit = "hr.attendance"
    
    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        for attendance in self:
            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ], limit=1, order="check_in ASC")
                if no_check_out_attendances:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                        'empl_name': attendance.employee_id.name,
                        'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
                    })
        super(hr_attendance, self)._check_validity()
    
    def convert_to_float(self, time_att):
        h_m_s = time_att.split(":")
        hours = int(h_m_s[0])
        minutes_1 = float(h_m_s[1])/60.0
        minutes = ("%.2f" % minutes_1)
        return hours+float(minutes)
    
    def minutes_late(self, calendar, check_in, max_late_minutes,att):
        day_of_week = {'Monday':'0' ,'Tuesday':'1' ,'Wednesday':'2' ,'Thursday':'3' ,'Friday':'4' ,'Saturday':'5' ,'Sunday':'6' }
        date_from = check_in
        time_2 = str(date_from.time())
        day_id = date_from.strftime('%A')
        shifted_time = False
        att_line_target = False 
        if calendar:
            for day in calendar.attendance_ids:
                if str(day.dayofweek) == day_of_week[day_id]:
                    time_float = self.convert_to_float(time_2)
                    time_hour = day.hour_from
                    if shifted_time != False:
                        if shifted_time > abs(time_float - time_hour):
                            shifted_time = abs(time_float - time_hour)
                            att_line_target = day
                    else:
                        shifted_time = abs(time_float - time_hour)
                        att_line_target = day
                        
                    if check_in.hour <= att_line_target.hour_to:
                        break
            if att_line_target:
                time_hour = att_line_target.hour_from
                start_hour = int(time_hour)
                start_minute = int((time_hour - start_hour)*60)
                att_hour = int(date_from.strftime('%H'))
                att_minute = int(date_from.strftime('%M'))
                att_second = int(date_from.strftime('%S'))
                new_hour = (att_hour-start_hour)
                new_minute = (att_minute-start_minute)
                new_minute_1 = int(max_late_minutes)
                
                if check_in.hour >= att_line_target.hour_to:
                    return 0.0
                if new_hour > 0:
                    return (new_hour*60)+new_minute
                elif new_hour == 0 and new_minute > max_late_minutes:
                    return new_minute
                elif new_hour == 0 and new_minute == max_late_minutes and att_second > 0:
                    return new_minute_1
        return 0.0
    
    def get_inside_calendar_duration(self, calendar, check_in, check_out, att):
        day_of_week = {'Monday':'0' ,'Tuesday':'1' ,'Wednesday':'2' ,'Thursday':'3' ,'Friday':'4' ,'Saturday':'5' ,'Sunday':'6' }
        day_id = check_in.strftime('%A')
        att_line_target = False 
        att_line_target_1 = False
        in_duration = 0.0
        out_duration = 0.0
        period_deff = 0.0
        working_hours = 0.0
        if calendar:
            for day in calendar.attendance_ids:
                if str(day.dayofweek) == day_of_week[day_id]:
                    att_line_target = day
                    if att_line_target_1 == False:
                        att_line_target_1 = day
                    if att_line_target_1 == day:
                        att_line_target_1 = day
            period_deff = att_line_target.hour_from - att_line_target_1.hour_to if att_line_target != att_line_target_1 else calendar.break_duration
            worked_hours = att.worked_hours
            if att_line_target and att_line_target_1:
                first_from_hour = att_line_target_1.hour_from
                first_to_hour = att_line_target_1.hour_to
                second_from_hour = att_line_target.hour_from
                second_to_hour = att_line_target.hour_to
                check_in_time = self.convert_to_float(str(check_in.time()))
                check_out_time = self.convert_to_float(str(check_out.time()))
                if att_line_target != att_line_target_1:
                    working_hours = att_line_target_1.hour_to- att_line_target_1.hour_from
                else:
                    working_hours = (att_line_target.hour_to-att_line_target.hour_from)-period_deff
                    
                if att_line_target != att_line_target_1 and check_out_time > att_line_target.hour_from and check_in.day == check_out.day:
                    working_hours = (att_line_target_1.hour_to- att_line_target_1.hour_from)+(att_line_target.hour_to- att_line_target.hour_from)
                
                if check_in_time >= first_from_hour and check_out_time <= second_to_hour and check_out_time >= second_from_hour and check_in_time <= first_to_hour and check_in.day == check_out.day:
                    in_duration = (first_to_hour-check_in_time)+(check_out_time-second_from_hour)
                    out_duration = (check_out_time-check_in_time)-period_deff
                elif check_in_time >= first_from_hour and  check_out_time <= second_from_hour and check_in_time <= first_to_hour and check_out_time >=first_to_hour and check_in.day == check_out.day:
                    in_duration = first_to_hour-check_in_time
                    out_duration = check_out_time-first_to_hour
                elif check_in_time >= first_from_hour and check_out_time <= first_to_hour  and check_in.day == check_out.day:
                    in_duration = working_hours-((check_in_time-first_from_hour)+(first_to_hour-check_out_time))
                    out_duration = 0.0
                elif check_in_time > first_from_hour and check_in_time >= second_from_hour and check_in_time < second_to_hour and check_out_time > second_to_hour and check_in.day == check_out.day and first_from_hour != second_from_hour:
                    in_duration = second_to_hour-check_in_time
                    out_duration = check_out_time-second_to_hour
                elif check_in_time <= first_from_hour and check_out_time < first_to_hour and att_line_target != att_line_target_1 and check_in.day == check_out.day: 
                    in_duration = working_hours-(first_to_hour-check_out_time)
                    out_duration = first_from_hour-check_in_time
                elif check_in_time > first_from_hour and check_in_time < second_from_hour and check_in_time >= first_to_hour and check_out_time >= second_to_hour and check_in.day == check_out.day:
                    in_duration = second_to_hour-second_from_hour
                    out_duration = (second_from_hour-check_in_time)+(check_out_time-second_to_hour)
                elif check_in_time >= second_to_hour and check_in.day == check_out.day:
                    in_duration = 0.0
                    out_duration = check_out_time-check_in_time
                elif check_in_time >= first_from_hour and check_out_time >= second_to_hour and check_in_time < first_to_hour and check_in.day == check_out.day:
                    in_duration = (second_to_hour-check_in_time)-period_deff
                    out_duration = period_deff+(check_out_time-second_to_hour)
                elif check_in_time <= first_from_hour and check_out_time >= first_to_hour and check_out_time <= second_from_hour:
                    in_duration = working_hours
                    out_duration = (first_from_hour-check_in_time)+(check_out_time-first_to_hour)
                elif check_in_time <= first_to_hour and check_in_time >= first_from_hour and check_out_time <= second_to_hour and check_out_time > second_from_hour and check_in.day == check_out.day:
                    in_duration = worked_hours-period_deff
                    out_duration = period_deff
                elif check_in_time >= first_to_hour and check_in_time > first_from_hour and check_out_time <= second_to_hour and check_out_time > second_from_hour:
                    in_duration = worked_hours-(second_from_hour-check_in_time)
                    out_duration = second_from_hour-check_in_time
                elif check_in_time < first_from_hour and check_out_time > second_to_hour:
                    in_duration = (second_to_hour-first_from_hour)-period_deff
                    out_duration = ((first_from_hour-check_in_time)+(check_out_time-second_to_hour))+period_deff
                elif check_in_time < first_from_hour and check_out_time >= second_from_hour and check_out_time <= second_to_hour:
                    in_duration = (check_out_time-first_from_hour)-period_deff
                    out_duration = (first_from_hour-check_in_time)+period_deff
                elif check_in_time >= first_to_hour and check_out_time <= second_from_hour:
                    in_duration = 0.0
                    out_duration = check_out_time-check_in_time
                
        if in_duration < 0 and in_duration > -1:
            in_duration = period_deff+in_duration
        elif in_duration < 0 and in_duration <= -1:
            in_duration = in_duration*-1
            
        if out_duration < 0:
            out_duration = out_duration*-1
        
        return [in_duration, out_duration, working_hours,period_deff]
    
    
    @api.multi
    @api.depends('check_in', 'check_out')
    def _get_attendance_duration(self):
        for att in self:
            calendar = att.employee_id.resource_calendar_id
            max_hours = 0.0 
            checkin_weekday = datetime.strptime(att.check_in, '%Y-%m-%d %H:%M:%S').weekday()
            attendance_days = self.env['resource.calendar.attendance'].search([('dayofweek', '=', checkin_weekday), ('calendar_id', '=', att.employee_id.resource_calendar_id.id)])
            for day in attendance_days:
                hour_diff = day.hour_to - day.hour_from 
                max_hours += hour_diff
            
            max_hours = max_hours - calendar.break_duration
            if calendar and att.check_in and att.check_out and max_hours:
                max_late_minutes = calendar.max_late_minutes
                max_hours_per_day = max_hours
                active_tz = pytz.timezone(self._context.get("tz","UTC") if self._context else "UTC")
                check_out = datetime.strptime(att.check_out, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(active_tz)
                check_in = datetime.strptime(att.check_in, '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(active_tz)
                all_duration = self.get_inside_calendar_duration(calendar, check_in, check_out, att)
                att.inside_calendar_duration = all_duration[0]
                att.outside_calendar_duration = all_duration[1]
                working_hours = all_duration[2]
                period_deff = all_duration[3]
                late_minutes = self.minutes_late(calendar, check_in, max_late_minutes,att)/60.0
                if late_minutes-period_deff <= working_hours:
                    att.late_minutes = late_minutes
                else:
                    att.late_minutes = 0.0
            else:
                att.outside_calendar_duration = att.worked_hours
                att.inside_calendar_duration = 0.0
                att.late_minutes = 0.0
        
    outside_calendar_duration = fields.Float(compute='_get_attendance_duration', string="Duration (Out Work schedule)")
    inside_calendar_duration = fields.Float(compute='_get_attendance_duration', string="Duration (In Work schedule)")
    late_minutes = fields.Float(compute='_get_attendance_duration', string="Late Minutes")
