
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

