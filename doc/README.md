# **客控微信端接口**

[TOC]

- - -
#####  一、MQTT订阅topic

- 服务器
```
服务器：183.134.4.158
端口：1883
```

- 设备状态更新以及设备列表通过mqtt返回
```
项目名+房间号:tzgjhotel2507
```


- - -
#####  二、获取token

- 接口地址
http://iotdtest.cleartv.cn/iotd_backend/getRoomToken

- 方法
GET

- 参数
```JSON
房间号：roomNo//2507
项目名: projectName//tzgjhotel
```

- 返回内容
```JSON
{
    "wxAuthToken": "a4qns7akkb3o58o8bqf020180130172156",
    "wxQrcode": "a4qns7akkb3o58o8bqf020180130172156",
    "rescode": "200",
    "errInfo": "None",
}
```

- - -
##### 三、重置token

- 接口地址
http://iotdtest.cleartv.cn/iotd_backend/updateRoomWxToken

- 方法
POST

- 参数
```JSON
{
    "roomNo":"2507",//房间号
    "projectName":"tzgjhotel"//项目名
}
```

- 返回内容
```JSON
{
    "rescode": "200",
    "errInfo": "None",
}
```

- - -
##### 四、微信端指令

- 接口地址
http://iotdtest.cleartv.cn/iotd_backend/wxCmd

- 方法
POST 所有指令通过mqtt订阅项目名+房间号返回

- 参数
- 1、控制情景模式
```JSON
{
"wxAuthToken": "uu4trxipgrfu0wa3v7or20180307201204",
"wxCmd":"sceneControl",
"sceneName":"灯光全关"//情景名称
}
```
- 返回
```JSON
{
    "wxCmd":"devStatus",
    "devName": "灯光全关"
}
```

- 2、控制设备开关
```
{
"wxAuthToken": "kuidara56bm963fapw2t20180130093902",
"wxCmd":"devControl",
"devName":"空调",//设备id
"actionCode":0,//开:1，关:0
"devStatus":{//除了空调，其它设备不用传
        "mode": 2,//1制冷，2制热，3保持，4通风
        "setTemp": 25,//15-32
        "currentTemp": 16,//只读
        "speed": 2,//1低速，2中速，3高速，4自动，5保持
        "switch": 2//1开，2关
    }
}
```
- mqtt返回设备状态
```Json
{
    "wxCmd":"devStatus",
    "devName": "射灯",
    "onLine": 1,
    "actionCode": 0，
    "devStatus": {//空调才有
			"switch": 1,
			"speed": 2,
			"setTemp": 25,
			"currentTemp": 18,
			"mode": 2
		}
}
```

- 3、获取列表
```
{
"wxAuthToken": "uu4trxipgrfu0wa3v7or20180307201204",
"wxCmd":"devList"
}

```
- 返回内容
```JSON
成功
{
    "rescode": "200",
    "errInfo": "None",
}
```

```
token过期
{
    'rescode':'401',
    'errInfo':'Token Timeout'
}
```

- mqtt返回设备列表
```Json
{
    "wxCmd":"devList",
    "devList": [ {
		"devName": "射灯",
		"onLine": 1,
		"actionCode": 0
	}, {
		"devStatus": {
			"switch": 1,
			"speed": 2,
			"setTemp": 25,
			"currentTemp": 18,
			"mode": 2
		},
		"devName": "温控器",
		"onLine": 1,
		"actionCode": 1
	}],
	"rescode": "200"
}

```

- - -
##### 五、TV端控制指令，

- 接口地址
http://iotdtest.cleartv.cn/iotd_backend/tvCmd

- 方法
POST

- 参数
-json
```
{
"projectName":"tzgjhotel",
"roomNo":"2508",
"wxCmd":"sceneControl",//其余参照上面微信端指令
"sceneName":"灯光全关"//情景名称
}
```
- - -
##### 六、设备网关场景

- 接口地址
http://iotdtest.cleartv.cn/iotd_backend/setScene

- 方法
GET 

- 参数
```
projectName:tzgjhotel//项目名
roomNo：A101//房间号
sceneName:allScene//设备所有场景包括灯光分组，起夜//单个场景设备
```

- - -
##### 七、设备网关分组

- 接口地址
http://iotdtest.cleartv.cn/iotd_backend/setGroup

- 方法
GET 

- 参数
```
projectName:tzgjhotel//项目名
roomNo：A101//房间号
groupName:all_light//灯光分组，起夜;All设备所有分组信息
```