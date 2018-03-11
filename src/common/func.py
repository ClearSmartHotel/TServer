# -*- coding: UTF-8 -*-

import json,time


def getCurrentTime():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def list2Str(list):
    strOut = ""
    first = 1
    for id in list:
        if first == 0:
            strOut += ","
        strOut += str(id)
        first = 0
    return strOut

def str2List(str):
    if str == "" or str is None:
        return []
    else:
        return str.split(',')