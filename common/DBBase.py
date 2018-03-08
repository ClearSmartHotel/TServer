# -*- coding: UTF-8 -*-

import os
import web
import config

db = web.database (
    dbn = 'mysql',
    host = config.db_host,
    port = int(config.db_port),
    db = config.db_name,
    user = config.db_user,
    pw = config.db_pass,
    charset = 'utf8'
)

def db_replace(table,filter,data):

    # INSERT INTO GETWAY (MAC,LAST_TIMESTAMP) VALUES ("125",15) ON DUPLICATE KEY UPDATE LAST_TIMESTAMP = 15;

    ret = db.select(table, where=filter).first()
    if ret is None:
        db.insert(table, **data)
    else:
        db.update(table, where=filter, **data)
