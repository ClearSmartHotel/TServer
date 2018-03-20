
# -*- coding: UTF-8 -*-

import ConfigParser
import os

_config = ConfigParser.ConfigParser()
_config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

db_host = _config.get('database', 'host')
db_port = _config.get('database', 'port')
db_name = _config.get('database', 'name')
db_user = _config.get('database', 'user')
db_pass = _config.get('database', 'pass')

mqtt_host = _config.get('mqtt', 'host')
mqtt_port = _config.get('mqtt', 'port')

haier_rcu_host = _config.get('HaierRcu', 'host')
haier_rcu_project_autoken = _config.get('HaierRcu', 'projectToken')

project_name = _config.get('project', 'name')
