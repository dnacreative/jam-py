# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys, os
if not hasattr(sys, 'db_multiprocessing'):
    sys.db_multiprocessing = False

import Queue
import multiprocessing
#from multiprocessing.managers import BaseManager
import zipfile
from xml.dom.minidom import parseString
from xml.sax.saxutils import escape
import datetime, time
import traceback
import inspect
import json

import common, db.db_modules as db_modules
from items import *
from dataset import *
from sql import *

class ServerDataset(Dataset, SQL):
    def __init__(self, table_name='', view_template='', edit_template='', filter_template='', soft_delete=True):
        Dataset.__init__(self)
        self.ID = None
        self.table_name = table_name
        self.view_template = view_template
        self.edit_template = edit_template
        self.filter_template = filter_template
        self.filter_template = filter_template
        self._order_by = []
        self.values = None
        self.on_select = None
        self.on_apply = None
        self.on_record_count = None
        self.on_get_field_text = None
        self.id_field_name = None
        self.deleted_field_name = None
        self.soft_delete = soft_delete

    def copy(self, filters=True, details=True, handlers=True):
        result = super(ServerDataset, self).copy(filters, details, handlers)
        result.table_name = self.table_name
        result._order_by = self._order_by
        result.id_field_name = self.id_field_name
        result.deleted_field_name = self.deleted_field_name
        result.soft_delete = self.soft_delete
        return result

    def get_event(self, caption):
        return getattr(caption)

    def add_field(self, field_id, field_name, field_caption, data_type, required = False,
        item = None, object_field = None,
        visible = True, index=0, edit_visible = True, edit_index = 0, read_only = False, expand = False,
        word_wrap = False, size = 0, default = False, calculated = False, editable = False, master_field = None, alignment=None, value_list=None):
        field_def = self.add_field_def(field_id, field_name, field_caption, data_type, required, item, object_field, visible,
            index, edit_visible, edit_index, read_only, expand, word_wrap, size, default, calculated, editable, master_field, alignment, value_list)
        field = DBField(self, field_def)
        self._fields.append(field)
        return field

    def add_filter(self, name, caption, field_name, filter_type = common.FILTER_EQ, data_type = None, visible = True):
        filter_def = self.add_filter_def(name, caption, field_name, filter_type, data_type, visible)
        fltr = DBFilter(self, filter_def)
        self.filters.append(fltr)
        return fltr

    def do_internal_open(self, params):
        return self.select_records(params)

    def do_apply(self, params=None):
        result = True
        if not self.master and self.log_changes:
            if self.item_state != common.STATE_BROWSE:
                raise Exception, u'Item: %s is not in browse state. Apply requires browse state.'
            changes = {}
            self.change_log.get_changes(changes)
            if changes['data']:
                data = self.apply_changes((changes, params),
                    {'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True})
                if data:
                    if data['error']:
                        raise Exception, data['error']
                    else:
                        self.change_log.update(data['result'])
        return result

    def get_fields_info(self):
        result = []
        for field in self._fields:
            result.append(field.get_info())
        return result

    def get_filters_info(self):
        result = []
        for fltr in self.filters:
            result.append(fltr.get_info())
        return result

    def add_detail(self, table):
        detail = ServerDetail(self, table.item_name, table.item_caption, table.table_name)
        self.details.append(detail)
        detail.owner = self
        detail.init_fields()
        return detail

    def detail_by_name(self, caption):
        for table in self.details:
            if table.item_name == caption:
                return table

    def change_order(self, *fields):
        self._order_by = []
        for field in fields:
            field_name = field
            desc = False
            if field[0] == '-':
                desc = True
                field_name = field[1:]
            try:
                fld = self._field_by_name(field_name)
            except:
                raise RuntimeError('%s: change_order method arument error - %s' % (self.item_name, field))
            self._order_by.append([fld.ID, desc])
        return self

    def get_record_count(self, params, user_info=None, enviroment=None):
        result = 0;
        if self.on_record_count:
            result, error_mes = self.on_record_count(self, params, user_info, enviroment)
        else:
            error_mes = ''
            result = 0
            sql = self.get_record_count_query(params)
            try:
                rows = self.task.execute_select(sql)
                result = rows[0][0]
            except Exception, e:
                error_mes = e.message
        return result, error_mes

    def select_records(self, params, user_info=None, enviroment=None):
        if self.on_select:
            rows, error_mes = self.on_select(self, params, user_info, enviroment)
        else:
            sql = self.get_select_statement(params)
            error_mes = ''
            rows = []
            try:
                rows = self.task.execute_select(sql)
            except Exception, e:
                error_mes = e.message
        return rows, error_mes

    def apply_changes(self, data, privileges, user_info=None, enviroment=None):
        error = None
        result = None
        try:
            changes, params = data
            if not params:
                params = {}
            delta = self.delta(changes)
            if self.on_apply:
                result, error = self.on_apply(self, delta, params, privileges, user_info, enviroment)
            else:
                sql = delta.apply_sql(privileges)
                result, error = self.task.execute(sql)
        except Exception, e:
            error = e.message
            if not error:
                error = '%s: apply_changes error' % self.item_name
            print traceback.format_exc()
        return {'error': error, 'result': result}

    def update_deleted(self):
        if self.is_delta and len(self.details):
            rec_no = self.rec_no
            try:
                for it in self:
                    if it.rec_deleted():
                        for detail in self.details:
                            fields = []
                            for field in detail.fields:
                                fields.append(field.field_name)
                            det = self.task.item_by_name(detail.item_name).copy()
                            det.set_where(owner_id=self.ID, owner_rec_id=self.id.value)
                            det.open(fields=fields, expanded=detail.expanded)
                            it.edit()
                            for d in det:
                                detail.append()
                                for field in detail.fields:
                                    f = det.field_by_name(field.field_name)
                                    field.set_value(f.value, f.lookup_value)
                                detail.post()
                            it.post()
                            for d in detail:
                                d.record_status = common.RECORD_DELETED
            finally:
                self.rec_no = rec_no

    def field_by_id(self, id_value, field_name):
        return self.get_field_by_id((id_value, field_name))

    def get_field_by_id(self, params):
        id_value, fields = params
        if not (isinstance(fields, tuple) or isinstance(fields, list)):
            fields = [fields]
        copy = self.copy()
        copy.set_where(id=id_value)
        copy.open(fields=fields)
        if copy.record_count() == 1:
            result = []
            for field_name in fields:
                result.append(copy.field_by_name(field_name).value)
            if len(fields) == 1:
                return result[0]
            else:
                return result
        return

class ServerItem(Item, ServerDataset):
    def __init__(self, owner, name, caption, visible = True,
            table_name='', view_template='', edit_template='', filter_template='', soft_delete=True):
        Item.__init__(self, owner, name, caption, visible)
        ServerDataset.__init__(self, table_name, view_template, edit_template, filter_template, soft_delete)
        self.item_type_id = None
        self.reports = []

    def get_reports_info(self):
        result = []
        for report in self.reports:
            result.append(report.ID)
        return result


class ServerParam(DBField):
    def __init__(self, owner, param_def):
        DBField.__init__(self, owner, param_def)
        self.field_type = common.PARAM_FIELD
        if self.data_type == common.TEXT:
            self.field_size = 1000
        else:
            self.field_size = 0
        self.param_name = self.field_name
        self.param_caption = self.field_caption
        self._value = None
        self._lookup_value = None
        setattr(owner, self.param_name, self)


    def system_field(self):
        return False

    def get_data(self):
        return self._value

    def set_data(self, value):
        self._value = value

    def get_lookup_data(self):
        return self._lookup_value

    def set_lookup_data(self, value):
        self._lookup_value = value

    def do_before_changed(self, new_value, new_lookup_value):
        pass

    def do_on_change_lookup_field(self, lookup_value=None, slave_field_values=None):
        pass

    def raw_display_text(self):
        result = ''
        if self.lookup_item:
            result = self.lookup_text
        else:
            result = self.text
        return result

    def copy(self, owner):
        result = ServerParam(owner, self.param_caption, self.field_name, self.data_type,
            self.lookup_item, self.lookup_field, self.required,
            self.edit_visible, self.alignment)
        return result


class ServerReport(Report):
    def __init__(self, owner, name='', caption='', visible = True,
            table_name='', view_template='', edit_template='', filter_template=''):
        Report.__init__(self, owner, name, caption, visible)
        self.param_defs = []
        self.params = []
        self.template = view_template
        self.band_tags = []
        self.bands = {}
        self.header = None
        self.footer = None
        self.on_before_generate_report = None
        self.on_generate_report = None
        self.on_report_generated = None
        self.on_before_save_report = None

        self.on_before_append = None
        self.on_after_append = None
        self.on_before_edit = None
        self.on_after_edit = None
        self.on_before_open = None
        self.on_after_open = None
        self.on_before_post = None
        self.on_after_post = None
        self.on_before_delete = None
        self.on_after_delete = None
        self.on_before_cancel = None
        self.on_after_cancel = None
        self.on_before_apply = None
        self.on_after_apply = None
        self.on_before_scroll = None
        self.on_after_scroll = None
        self.on_filter_record = None
        self.on_field_changed = None
        self.on_filter_applied = None
        self.on_before_field_changed = None
        self.on_filter_value_changed = None
        self.on_field_validate = None
        self.on_get_field_text = None


    def add_param(self, caption='', name='', data_type=common.INTEGER, obj=None, obj_field=None, required=True, visible=True, value=None):
        param_def = self.add_param_def(caption, name, data_type, obj, obj_field, required, visible, value)
        param = ServerParam(self, param_def)
        self.params.append(param)

    def add_param_def(self, param_caption='', param_name='', data_type=common.INTEGER, lookup_item=None, lookup_field=None, required=True, visible=True, alignment=0):
        param_def = [None for i in range(len(FIELD_DEF))]
        param_def[FIELD_NAME] = param_name
        param_def[NAME] = param_caption
        param_def[FIELD_DATA_TYPE] = data_type
        param_def[REQUIRED] = required
        param_def[LOOKUP_ITEM] = lookup_item
        param_def[LOOKUP_FIELD] = lookup_field
        param_def[FIELD_EDIT_VISIBLE] = visible
        param_def[FIELD_ALIGNMENT] = alignment
        self.param_defs.append(param_def)
        return param_def

    def prepare_params(self):
        for param in self.params:
            if param.lookup_item and type(param.lookup_item) == int:
                param.lookup_item = self.task.item_by_ID(param.lookup_item)
            if param.lookup_field and type(param.lookup_field) == int:
                param.lookup_field = param.lookup_item._field_by_ID(param.lookup_field).field_name

    def copy(self):
        result = self.__class__(self.owner, self.item_name, self.item_caption, self.visible,
            '', self.template, '', '');
        result.on_before_generate_report = self.on_before_generate_report
        result.on_generate_report = self.on_generate_report
        result.on_report_generated = self.on_report_generated
        result.on_before_save_report = self.on_before_save_report
        result.param_defs = self.param_defs
        for param_def in result.param_defs:
            param = ServerParam(result, param_def)
            result.params.append(param)
        result.prepare_params()
        return  result

    def print_report(self, param_values, url, ext=None):
        copy_report = self.copy()
        return copy_report.generate(param_values, url, ext)

    def get_report_file_name(self, ext=None):
        if not ext:
            ext = 'ods'
        os_system = os.name
        if os_system == "nt":
            file_name = self.item_name + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f') + '.' + ext
        else:
            file_name = self.item_caption + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f') + '.' + ext
        file_name = escape(file_name, {':': '-', '/': '_', '\\': '_'})
        return os.path.abspath(os.path.join(self.task.work_dir, 'static', 'reports', file_name))

    def generate(self, param_values, url, ext):
        self.extension = ext
        self.url = url
        for i, param in enumerate(self.params):
            param.value = param_values[i]
        if self.on_before_generate_report:
            self.on_before_generate_report(self)
        if self.template:
            if not len(self.bands):
                self.parse_template()
            self.content_name = os.path.join(self.task.work_dir, 'reports', 'content%s.xml' % time.time())
            self.content = open(self.content_name, 'wb')
            try:
                #~ file_name = self.item_caption + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f') + '.ods'
                #~ file_name = escape(file_name, {':': '-', '/': '_', '\\': '_'})
                #~ self.report_filename = os.path.abspath(os.path.join(self.task.work_dir, 'static', 'reports', file_name))
                self.report_filename = self.get_report_file_name()
                file_name = os.path.basename(self.report_filename)
                static_dir = os.path.dirname(self.report_filename)
                if not os.path.exists(static_dir):
                    os.makedirs(static_dir)
                if self.header:
                    self.content.write(self.header)
                if self.on_generate_report:
                    self.on_generate_report(self)
                if self.footer:
                    self.content.write(self.footer)
                self.save()
            finally:
                if not self.content.closed:
                    self.content.close()
                os.remove(self.content_name)
            if ext and (ext != 'ods'):
                converted = False
                if self.owner.on_convert_report:
                    try:
                        self.owner.on_convert_report(self)
                        converted = True
                    except:
                        pass
                if not converted:
                    # OpenOffice must be running in server mode
                    # soffice --headless --accept="socket,host=127.0.0.1,port=2002;urp;"
                    ext_file_name = self.report_filename.replace('.ods', '.' + ext)
                    try:
                        from third_party.DocumentConverter import DocumentConverter
                        converter = DocumentConverter()
                        converter.convert(self.report_filename, ext_file_name)
                        converted = True
                    except:
                        pass
                if not converted:
                    try:
                        from subprocess import Popen, STDOUT, PIPE
                        os_system = os.name
                        if os_system == "nt":
                            import _winreg
                            regpath = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\soffice.exe"
                            root = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, regpath)
                            s_office = _winreg.QueryValue(root, "")
                        else:
                            s_office = "soffice"
                        convertion = Popen([s_office, '--headless', '--convert-to', ext,
                            self.report_filename, '--outdir', os.path.join(self.task.work_dir, 'static', 'reports') ],
                            stderr=STDOUT,stdout = PIPE)#, shell=True)
                        out, err = convertion.communicate()
                        converted = True
                    except:
                        pass
                converted_file = self.report_filename.replace('.ods', '.' + ext)
                if converted and os.path.exists(converted_file):
                    self.delete_report(self.report_filename)
                    file_name = file_name.replace('.ods', '.' + ext)
            self.report_filename = os.path.join(self.task.work_dir, 'static', 'reports', file_name)
            self.report_url = self.report_filename
            if self.url:
                self.report_url = '%s/static/reports/%s' % (self.url, file_name)
        else:
            if self.on_generate_report:
                self.on_generate_report(self)
        if self.on_report_generated:
            self.on_report_generated(self)
        return self.report_url

    def delete_report(self, file_name):
        report_name = os.path.join(self.task.work_dir, 'static', 'reports', file_name)
        os.remove(report_name)

    def parse_template(self):
        self.template_name = os.path.join(self.task.work_dir, 'reports', self.template)
        z = zipfile.ZipFile(self.template_name, 'r')
        try:
            data = unicode(z.read('content.xml'), 'utf-8')
        finally:
            z.close()

        self.band_tags = []
        self.bands = {}
        repeated_rows = None
        if data:
            dom = parseString(data)
            try:
                tables = dom.getElementsByTagName('table:table')
                if len(tables) > 0:
                    table = tables[0]
                    for child in table.childNodes:
                        if child.nodeName == 'table:table-row':
                            repeated = child.getAttribute('table:number-rows-repeated')
                            if repeated and repeated.isdigit():
                                repeated_rows = repeated
                            for row_child in child.childNodes:
                                if row_child.nodeName == 'table:table-cell':
                                    text = row_child.getElementsByTagName('text:p')
                                    if text.length > 0:
                                        self.band_tags.append(text[0].childNodes[0].nodeValue)
                                    break

                assert len(self.band_tags) > 0, u'No bands in report template'
                positions = []
                start = 0
                for tag in self.band_tags:
                    text = str('>%s<' % tag)
                    i = data.find(text)
                    i = data.rfind('<table:table-row', start, i)
                    positions.append(i)
                    start = i
                if repeated_rows and int(repeated_rows) > 1000:
                    i = data.find(repeated_rows)
                    i = data.rfind('<table:table-row', start, i)
                    self.band_tags.append('$$$end_of_report')
                    positions.append(i)
                self.header = data[0:positions[0]]
                for i, tag in enumerate(self.band_tags):
                    start = positions[i]
                    try:
                        end = positions[i + 1]
                    except:
                        end = data.find('</table:table>', start)
                    self.bands[tag] = data[start: end].replace(str(tag), '')
                self.footer = data[end:len(data)]
            finally:
                dom.unlink()
                del(dom)

    def print_band(self, band, dic=None, update_band_text=None):
        text = self.bands[band]
        if dic:
            d = dic.copy()
            for key, value in d.items():
                if type(value) in (str, unicode):
                    d[key] = escape(value)
            try:
                cell_start = 0
                cell_start_tag = '<table:table-cell'
                cell_type_tag = 'office:value-type="string"'
                calcext_type_tag = 'calcext:value-type="string"'
                start_tag = '<text:p>'
                end_tag = '</text:p>'
                while True:
                    cell_start = text.find(cell_start_tag, cell_start)
                    if cell_start == -1:
                        break
                    else:
                        start = text.find(start_tag, cell_start)
                        if start != -1:
                            end = text.find(end_tag, start + len(start_tag))
                            if end != -1:
                                text_start = start+len(start_tag)
                                text_end = end
                                cell_text = text[text_start:text_end]
                                cell_text_start = cell_text.find('%(', 0)
                                if cell_text_start != -1:
                                    end = cell_text.find(')s', cell_text_start + 2)
                                    if end != -1:
                                        end += 2
                                        val = cell_text[cell_text_start:end]
                                        key = val[2:-2]
                                        value = d.get(key)
                                        if not value is None:
                                            val = val % d
                                            if type(value) == float:
                                                val = val.replace('.', common.DECIMAL_POINT)
                                        else:
                                            if not key in d.keys():
                                                print 'Report: "%s" band: "%s" key "%s" not found in the dictionary' % (self.item_name, band, key)
                                        cell_text = cell_text[:cell_text_start] + val + cell_text[end:]
                                        text = text[:text_start] + cell_text + text[text_end:]
                                        if type(value) in (int, float):
                                            start_text = text[cell_start:start]
                                            office_value = str(value)
                                            start_text = start_text.replace(cell_type_tag, 'office:value-type="float" office:value="%s"' % office_value)
                                            start_text = start_text.replace(calcext_type_tag, 'calcext:value-type="float"')
                                            text = text[:cell_start] + start_text + text[start:]
                        cell_start += 1
                if update_band_text:
                    text = update_band_text(text)
            except Exception, e:
                print traceback.format_exc()
                print ('Report: "%s" band: "%s" error: "%s"') % (self.item_name, band, e)
        self.content.write(text.encode('utf-8'))

    def save(self):
        self.content.close()
        z = None
        self.zip_file = None
        try:
            self.zip_file = zipfile.ZipFile(self.report_filename, 'w', zipfile.ZIP_DEFLATED)
            z = zipfile.ZipFile(self.template_name, 'r')
            if self.on_before_save_report:
                self.on_before_save_report(self)
            for file_name in z.namelist():
                data = z.read(file_name)
                if file_name == 'content.xml':
                    self.zip_file.write(self.content_name, file_name)
                else:
                    self.zip_file.writestr(file_name, data)
        finally:
            if z:
                z.close()
            if self.zip_file:
                self.zip_file.close()
#            os.remove(self.content_name)

    def cur_to_str(self, value):
        return common.cur_to_str(value)

    def date_to_str(self, value):
        return common.date_to_str(value)

    def datetime_to_str(self, value):
        return common.datetime_to_str(value)



delta_result = None

def execute_sql(db_module, db_database, db_user, db_password,
    db_host, db_port, db_encoding, connection, command,
    params=None, result_set=None, call_proc=False, commit=True):

    def execute_command(cursor, command, params=None):
        try:
            #~ print ''
            #~ print command
            #~ print params

            result = None
            if params:
                cursor.execute(command, params)
            else:
                cursor.execute(command)
            if result_set == 'ONE':
                result = cursor.fetchone()
            elif result_set == 'ALL':
                result = cursor.fetchall()

            #~ if command.upper().find('SELECT') == -1:
                #~ try:
                    #~ with open("sql_log.txt", "a") as f:
                        #~ f.write('\n')
                        #~ f.write(command + '\n')
                        #~ f.write(json.dumps(params) + '\n')
                #~ except:
                    #~ pass
            return result
        except Exception, x:
            print '\nError: %s\n command: %s\n params: %s' % (str(x), command, params)
            raise

    def get_next_id(cursor, sql):
        cursor.execute(sql)
        rec = cursor.fetchone()
        return int(rec[0])

    def execute_delta(cursor, command):

        def process_delta(delta, master_rec_id, result):
            ID, sqls = delta
            result['ID'] = ID
            changes = []
            result['changes'] = changes
            for sql in sqls:
                (command, params, info), details = sql
                if info:
                    rec_id = info['id']
                    if info['status'] == common.RECORD_INSERTED:
                        if rec_id:
                            pass
                        else:
                            next_sequence_value_sql = db_module.next_sequence_value_sql(info['table_name'])
                            if next_sequence_value_sql:
                                rec_id = get_next_id(cursor, next_sequence_value_sql)
                                params[info['id_index']] = rec_id
                    if info['status'] == common.RECORD_INSERTED and info['owner_rec_id_index']:
                        params[info['owner_rec_id_index']] = master_rec_id
                    if command:
                        execute_command(cursor, command, params)
                    if not rec_id and info['status'] == common.RECORD_INSERTED:
                        new_id = db_module.get_lastrowid(cursor)
                        if new_id:
                            rec_id = new_id
                    result_details = []
                    if rec_id:
                        changes.append({'log_id': info['log_id'], 'rec_id': rec_id, 'details': result_details})
                    for detail in details:
                        result_detail = {}
                        result_details.append(result_detail)
                        process_delta(detail, rec_id, result_detail)
                else:
                    if command:
                        execute_command(cursor, command, params)

        global delta_result
        delta = command['delta']
        delta_result = {}
        process_delta(delta, None, delta_result)

    def execute_list(cursor, command):
        res = None
        if command:
            for com in command:
                if com:
                    if isinstance(com, unicode) or isinstance(com, str):
                        res = execute_command(cursor, com)
                    elif isinstance(com, list):
                        res = execute_list(cursor, com)
                    elif isinstance(com, dict):
                        res = execute_delta(cursor, com)
                    elif isinstance(com, tuple):
                        res = execute_command(cursor, com[0], com[1])
                    else:
                        raise Exception, 'server_classes execute_list: invalid argument - command: %s' % command
            return res

    def execute(connection):
        global delta_result
        result = None
        error = None
        try:
            cursor = connection.cursor()
            if call_proc:
                try:
                    cursor.callproc(command, params)
                    result = cursor.fetchone()
                except Exception, x:
                    print '\nError: %s in command: %s' % (str(x), command)
                    raise
            else:
                if isinstance(command, str) or isinstance(command, unicode):
                    result = execute_command(cursor, command, params)
                elif isinstance(command, dict):
                    res = execute_delta(cursor, command)
                elif isinstance(command, list):
                    result = execute_list(cursor, command)
                elif isinstance(command, tuple):
                    result = execute_command(cursor, command[0], command[1])
            if commit:
                connection.commit()
            if delta_result:
                result = delta_result
        except Exception, x:
            try:
                if connection:
                    connection.rollback()
                    connection.close()
                error = str(x)
                if not error:
                    error = 'Execute error'
                print traceback.format_exc()
            finally:
                connection = None
        return connection, (result, error)

    global delta_result
    delta_result = None
    if not db_host:
        db_host = 'localhost'
    if connection is None:
        connection = db_module.connect(db_database, db_user, db_password, db_host, db_port, db_encoding)
    return execute(connection)

def process_request(name, queue, db_type, db_database, db_user, db_password, db_host, db_port, db_encoding, mod_count):
    con = None
    counter = 0
    db_module = db_modules.get_db_module(db_type)
    while True:
        request = queue.get()
        if request:
#            print name, 'process id:', os.getpid()
            result_queue = request['queue']
            command = request['command']
            params = request['params']
            result_set = request['result_set']
            call_proc = request['call_proc']
            commit = request['commit']
            cur_mod_count = request['mod_count']
            if cur_mod_count != mod_count or counter > 1000:
                if con:
                    con.rollback()
                    con.close()
                con = None
                mod_count = cur_mod_count
                counter = 0
            if command == 'QUIT':
                if con:
                    con.commit()
                    con.close()
                result_queue.put('QUIT')
                break
            else:
                con, result = execute_sql(db_module, db_database, db_user, db_password,
                    db_host, db_port, db_encoding, con, command, params, result_set, call_proc, commit)
                counter += 1
                result_queue.put(result)

class AbstractServerTask(Task):
    def __init__(self, name, caption, template, edit_template, db_type, db_database = '',
            db_user = '', db_password = '', host='', port='', encoding='', con_pool_size=1):
        Task.__init__(self, None, None, None, None)
        self.items = []
        self.ID = None
        self.item_name = name
        self.item_caption = caption
        self.template = template
        self.db_type = db_type
        self.db_database = db_database
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = host
        self.db_port = port
        self.db_encoding = encoding
        self.db_module = db_modules.get_db_module(self.db_type)
        self.work_dir = os.getcwd()
        self.con_pool_size = 0
        self.mod_count = 0
        self.modules = []
        self.processes = []
        self._busy = 0
        if sys.db_multiprocessing and con_pool_size:
            self.queue = multiprocessing.Queue()
            self.manager = multiprocessing.Manager()
            self.con_pool_size = con_pool_size
            self.create_connection_pool()
        else:
            self.connection = None

    def create_connection_pool(self):
        if self.con_pool_size:
            for i in range(self.con_pool_size):
                p = multiprocessing.Process(target=process_request, args=(self.item_name,
                    self.queue, self.db_type, self.db_database, self.db_user,
                    self.db_password, self.db_host, self.db_port,
                    self.db_encoding, self.mod_count))
                self.processes.append(p)
                p.daemon = True
                p.start()

    def release_connection_pool(self):
        if self.con_pool_size:
            for i in range(self.con_pool_size):
                self.execute('QUIT')
            self.processes = []

    def execute(self, command, params=None, result_set=None, call_proc=False, commit=True):
        if self.con_pool_size:
            result_queue = self.manager.Queue()
            request = {}
            request['queue'] = result_queue
            request['command'] = command
            request['command'] = command
            request['params'] = params
            request['result_set'] = result_set
            request['call_proc'] = call_proc
            request['commit'] = commit
            request['mod_count'] = self.mod_count
            self._busy += 1
            try:
                self.queue.put(request)
                result = result_queue.get()
            finally:
                self._busy -= 1
            return result
        else:
            result = execute_sql(self.db_module, self.db_database, self.db_user,
                self.db_password, self.db_host, self.db_port,
                self.db_encoding, self.connection, command, params, result_set, call_proc, commit)
            self.connection = result[0]
            return result[1]

    def callproc(self, command, params=None):
        result_set, error = self.execute(command, params, call_proc=True)
        if not error:
            return result_set

    def execute_select(self, command, params=None):
        result, error = self.execute(command, params, result_set='ALL', commit=False)
        if error:
            raise Exception, error
        else:
            return result


    def execute_select_one(self, command, params=None):
        result, error = self.execute(command, params, result_set='ONE', commit=False)
        if error:
            raise Exception, error
        else:
            return result

    def get_module_name(self):
        return str(self.item_name + '_' + 'server')

    def compile_item(self, item):
        item.module_name = None
        code = item.server_code
        item.module_name = item.get_module_name()
        item_module = type(sys)(item.module_name)
        item_module.__dict__['this'] = item
        sys.modules[item.module_name] = item_module
        item.task.modules.append(item.module_name)
        if item.owner:
            sys.modules[item.owner.get_module_name()].__dict__[item.module_name] = item_module
        if code:
            try:
                code = code.encode('utf-8')
            except Exception, e:
                print e
            try:
                comp_code = compile(code, item.module_name, "exec")
            except Exception, e:
                print e
            exec comp_code in item_module.__dict__
            funcs = inspect.getmembers(item_module, inspect.isfunction)
            item._events = []
            for func_name, func in funcs:
                item._events.append((func_name, func))
                setattr(item, func_name, func)
        del code

    def login(self, params):
        return 1

    def add_item(self, item):
        self.items.append(item)
        item.owner = self
        return item

    def find_item(self, g_index, i_index):
        return self.items[g_index].items[i_index]

    def copy_database_data(self, db_type, db_database=None, db_user=None, db_password=None,
        db_host=None, db_port=None, db_encoding=None):
        connection = None
        limit = 1024
        db_module = db_modules.get_db_module(db_type)
        for group in self.items:
            for item in group.items:
                handlers = item.store_handlers()
                item.clear_handlers()
                try:
                    if item.item_type != 'report':
                        self.execute(self.db_module.set_case('DELETE FROM %s' % item.table_name))
                        item.open(expanded=False, open_empty=True)
                        params = {'__fields': [], '__filters': [], '__expanded': False, '__loaded': 0, '__limit': 0}
                        sql = item.get_record_count_query(params, db_module)
                        connection, (result, error) = \
                        execute_sql(db_module, db_database, db_user, db_password,
                            db_host, db_port, db_encoding, connection, sql, None, 'ALL')
                        record_count = result[0][0]
                        loaded = 0
                        max_id = 0
                        if record_count:
                            while True:
                                params['__loaded'] = loaded
                                params['__limit'] = limit
                                sql = item.get_select_statement(params, db_module)
                                connection, (result, error) = \
                                execute_sql(db_module, db_database, db_user, db_password,
                                    db_host, db_port, db_encoding, connection, sql, None, 'ALL')
                                if not error:
                                    for i, r in enumerate(result):
                                        item.append()
                                        j = 0
                                        for field in item.fields:
                                            if not field.master_field:
                                                field.value = r[j]
                                                j += 1
                                        if item.id.value > max_id:
                                            max_id = item.id.value
                                        item.post()
                                    item.apply()
                                else:
                                    raise Exception, error
                                records = len(result)
                                loaded += records
                                print 'coping table %s: %d%%' % (item.item_name, int(loaded * 100 / record_count))
                                if records == 0 or records < limit:
                                    break
                            if self.db_module.restart_sequence_sql:
                                sql = self.db_module.restart_sequence_sql(item.table_name, max_id + 1)
                                self.execute(sql)
                finally:
                    item.load_handlers(handlers)



class ServerTask(AbstractServerTask):
    def __init__(self, name, caption, template, edit_template,
        db_type, db_database = '', db_user = '', db_password = '',
        host='', port='', encoding='', con_pool_size=4):
        AbstractServerTask.__init__(self, name, caption, template, edit_template,
            db_type, db_database, db_user, db_password,
            host, port, encoding, con_pool_size)
        self.on_created = None
        self.on_login = None
        self.on_get_user_info = None
        self.on_logout = None
        self.on_ext_request = None
        self.init_dict = {}
        for key, value in self.__dict__.items():
            self.init_dict[key] = value

    def find_user(self, login, password_hash=None):
        return self.admin.find_user(login, password_hash)

class AdminServerTask(AbstractServerTask):
    def __init__(self, name, caption, template, edit_template,
        db_type, db_database = '', db_user = '', db_password = '',
        host='', port='', encoding=''):
        AbstractServerTask.__init__(self, name, caption, template, edit_template,
            db_type, db_database, db_user, db_password, host, port, encoding, 1)
        filepath, filename = os.path.split(__file__)
        self.cur_path = filepath


class ServerGroup(Group):
    def __init__(self, owner, name, caption, view_template = None, edit_template = None, filter_template = None, visible = True, item_type_id=0):
        Group.__init__(self, owner, name, caption, True, item_type_id)
        self.ID = None
        self.view_template = view_template
        self.edit_template = edit_template
        self.filter_template = filter_template
        if item_type_id == common.REPORTS_TYPE:
            self.on_convert_report = None

    def get_view_template(self):
        return self.view_template

    def get_edit_template(self):
        return self.edit_template

    def get_filter_template(self):
        return self.filter_template

    def add_ref(self, name, caption, table_name, visible = True, view_template = '', edit_template = '', filter_template='', soft_delete=True):
        result = ServerItem(self, name, caption, visible, table_name, view_template, edit_template, filter_template, soft_delete)
        result.item_type_id = common.CATALOG_TYPE
        return result

    def add_journal(self, name, caption, table_name, visible = True, view_template = '', edit_template = '', filter_template='', soft_delete=True):
        result = ServerItem(self, name, caption, visible, table_name, view_template, edit_template, filter_template, soft_delete)
        result.item_type_id = common.JOURNAL_TYPE
        return result

    def add_table(self, name, caption, table_name, visible = True, view_template = '', edit_template = '', filter_template='', soft_delete=True):
        result = ServerItem(self, name, caption, visible, table_name, view_template, edit_template, filter_template, soft_delete)
        result.item_type_id = common.TABLE_TYPE
        return result

    def add_report(self, name, caption, table_name, visible = True, view_template = '', edit_template = '', filter_template='', soft_delete=True):
        result = ServerReport(self, name, caption, visible, table_name, view_template, edit_template, filter_template)
        result.item_type_id = common.REPORT_TYPE
        return result


class ServerDetail(Detail, ServerDataset):
    def __init__(self, owner, name, caption, table_name):
        Detail.__init__(self, owner, name, caption, True)
        ServerDataset.__init__(self, table_name)
        self.prototype = self.task.item_by_name(self.item_name)
        self.master = owner

    def init_fields(self):
        self.field_defs = []
        for field_def in self.prototype.field_defs:
            self.field_defs.append(list(field_def))
        for field_def in self.field_defs:
            field = DBField(self, field_def)
            self._fields.append(field)

    def do_internal_post(self):
        return {'success': True, 'id': None, 'message': '', 'detail_ids': None}

    def where_clause(self, query, db_module):
        owner_id = query['__owner_id']
        owner_rec_id = query['__owner_rec_id']
        if type(owner_id) == int and type(owner_rec_id) == int:
            result = super(ServerDetail, self).where_clause(query, db_module)
            clause = '"%s"."OWNER_ID"=%s AND "%s"."OWNER_REC_ID"=%s' % \
            (self.table_name.upper(), str(owner_id), self.table_name.upper(), str(owner_rec_id))
            if result:
                result += ' AND ' + clause
            else:
                result = ' WHERE ' + clause
            return db_module.set_case(result)
        else:
            raise Exception, 'Invalid request parameter'

    def get_filters(self):
        return self.prototype.filters

    def get_reports_info(self):
        return []
