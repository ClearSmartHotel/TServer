# -*- coding:utf-8 -*-
'''
Created on

@author: hl
'''
import sys
sys.path.append("..")

import common.config as c
from memcache_ring import MemcacheRing

#使用方法
# 设置： mc.set('hello', 'world')
# 获取： mc.get('hello')
# 设置两秒后超时： mc.set('hello', 'world', 2)
def getMemcached():
    hosts = c.memcached_host.split(',')
    mc = MemcacheRing(hosts)
    return mc