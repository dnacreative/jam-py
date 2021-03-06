#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import traceback
import time
from threading import Lock

import common
import adm_server

class Server(object):
    def __init__(self):
        self.admin = adm_server.task
        self.admin.server = self
        self.task = None
        self.task_lock = Lock()
        self.users = {}
        self.roles = None
        self.last_users_update = common.now()
        self.task_server_modified = False
        self.task_client_modified = True
        self.under_maintenance = False

    def get_task(self):
        if self.task is None:
            with self.task_lock:
                self.task = adm_server.create_task(self)
        return self.task

    def release_connections(self):
        if self.task:
            self.task.release_connection_pool()

    def release_connection_pool(self):
        if self.task:
            self.task.release_connection_pool()

    def create_connection_pool(self):
        if self.task:
            self.task.create_connection_pool()

    def get_privileges(self, role_id):
        if self.roles is None:
            self.roles = adm_server.get_roles()
        return self.roles[role_id]

    def server_func(self, obj, func_name, params, env):
        result = None
        error = ''
        func = getattr(obj, func_name)
        if func:
            if func_name[-4:] == '_env':
                params = list(params)
                params.append(env)
            try:
                result = func(obj, *params)
            except Exception, e:
                print traceback.format_exc()
                error = e.message
                if not error:
                    error = '%s: apply_changes error' % obj.item_name
        else:
            error = 'item: %s no server function with name %s' % (obj.item_name, func_name)
        return {'error': error, 'result': result}

    def check_task_server_modified(self):
        if self.task_server_modified:
            adm_server.reload_task()
            self.task_server_modified = False

    def check_task_client_modified(self, file_name):
        if self.task_client_modified and file_name == 'index.html':
            adm_server.update_events_code()
            self.task_client_modified = False
        if not common.SETTINGS['DEBUGGING']:
            adm_server.update_js_files()

    def check_file_name(self, file_name):
        if not common.SETTINGS['DEBUGGING']:
            file_name = adm_server.get_minified_name(file_name)
        return file_name

    def init_client(self, user_info, is_admin):
        if is_admin:
            task = self.admin
        else:
            task = self.task
            self.check_task_server_modified()
        if user_info:
            priv = self.get_privileges(user_info['role_id'])
        else:
            priv = None
        return {
            'task': task.get_info(),
            'settings': self.admin.get_settings(),
            'language': self.admin.get_lang(),
            'user_info': user_info,
            'privileges': priv
        }

    def login(self, log, psw_hash, admin, env):
        privileges = None
        if not admin and self.task.on_login:
            user_uuid, user_info = self.task.on_login(self.task, env, admin, log, psw_hash)
        else:
            user_id, user_info = self.admin.login(log, psw_hash, admin)
            user_uuid = None
            if user_id:
                for key in self.users.iterkeys():
                    if self.users[key][0] == user_id:
                        del self.users[key]
                        break
                user_uuid = str(uuid.uuid4())
                self.users[user_uuid] = (user_id, user_info, common.now())
        return user_uuid

    def get_user_info(self, user_uuid, admin, env):
        if not admin and self.task.on_get_user_info:
            return self.task.on_get_user_info(self.task, user_uuid, env)
        else:
            user = self.users.get(user_uuid)
            if user:
                return user[1]

    def logout(self, user_uuid, admin, env):
        if not admin and self.task.on_logout:
            self.task.on_logout(self.task, user_uuid, env)
        else:
            user = self.users.get(user_uuid)
            if user:
                adm_server.logout(user[0])
                del user

    def update_users(self):
        now = common.now()
        for key in self.users.keys():
            if common.hour_diff(now - self.users[key][2]) > 12:
                self.logout(key)
        self.last_users_update = common.now()

    def find_privileges(self, user_info, item):
        if not self.admin.safe_mode or item.master or (item.task == self.admin) or (item == item.task):
            return {'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True}
        else:
            try:
                priv_dic = self.get_privileges(user_info['role_id'])[item.ID]
            except:
                priv_dic = None
            if priv_dic:
                return priv_dic
            else:
                return {'can_view': False, 'can_create': False, 'can_edit': False, 'can_delete': False}

    def has_privilege(self, user_info, item, priv_name):
        return self.find_privileges(user_info, item)[priv_name]

    def process_request(self, env, request, user_uuid=None, task_id=None, item_id=None, params=None, ext=None):
        #~ print ''
        #~ print 'process_request: ', request, user_uuid, task_id, item_id, params

        user_info = {}
        is_admin = task_id == 0
        if is_admin:
            task = self.admin
        else:
            task = self.get_task()
        if self.under_maintenance:
            return {'status': common.UNDER_MAINTAINANCE, 'data': None}
        if request == 'login':
            return {'status': common.RESPONSE, 'data': self.login(params[0], params[1], is_admin, env)}
        if ext:
            obj = task
        else:
            if self.admin.safe_mode:
                now = common.now()
                if common.hour_diff(now - self.last_users_update) > 1:
                    self.update_users()
                user_info = self.get_user_info(user_uuid, is_admin, env)
                if not user_info:
                    return {'status': common.NOT_LOGGED, 'data': common.NOT_LOGGED}
            obj = task
            if task:
                obj = task.item_by_ID(item_id)

        return {'status': common.RESPONSE, 'data': self.get_response(is_admin, env, request, user_info, task_id, obj, params, ext)}

    def get_response(self, is_admin, env, request, user_info, task_id, item, params, ext):
        if ext:
            if item.on_ext_request:
                return item.on_ext_request(item, request, params, env)
            else:
                raise Exception, u'Unknown request type %s' % request
        elif request[0:7] == 'server_':
            return self.server_func(item, request, params, env)
        elif request == 'open':
            if self.has_privilege(user_info, item, 'can_view'):
                return item.select_records(params, user_info, env)
            else:
                return [], item.task.lang['cant_view'] % item.item_caption
        elif request == 'get_record_count':
            return item.get_record_count(params, env)
        elif request == 'apply_changes':
            return item.apply_changes(params, self.find_privileges(user_info, item), user_info, env)
        elif request == 'print_report':
            if self.has_privilege(user_info, item, 'can_view'):
                return item.print_report(*params)
            else:
                return {'success': False,
                    'message': item.task.lang['cant_view'] % item.item_caption}
        elif request == 'delete_report':
            return item.delete_report(params)
        elif request == 'logout':
            return self.logout(params, is_admin, env)
        elif request == 'init_client':
            return self.init_client(user_info, is_admin)
        elif request == 'exit' and task_id == 0:
            return True;

server = Server()
