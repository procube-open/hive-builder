#!/usr/bin/env python3
import sys
from powerdnsadmin import create_app
from powerdnsadmin.models.user import User
from powerdnsadmin.models.setting import Setting

app = create_app()

with app.app_context():
    user = User(
        username='admin',
        plain_text_password=sys.argv[1],
        firstname='Administrator',
        role_id='Administrator')
    user.create_local_user()
    setting = Setting()
    forward_records_allow_edit = setting.get('forward_records_allow_edit')
    forward_records_allow_edit['LUA'] = True
    setting.set('forward_records_allow_edit', forward_records_allow_edit)
    setting.set('pdns_api_url', 'http://powerdns:8081/')
    setting.set('pdns_api_key', sys.argv[1])
