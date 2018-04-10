# **上海清鹤智慧酒店客房控制系统第三方设备对接WebSocket接口**

[TOC]

- - -
#####  一、服务地址

- 服务器
```
服务地址：ws://iotd.cleartv.cn:9999
测试服务器：iotd.cleartv.cn
端口：9999
所有数据传输采用json格式
```

- - -
#####  一、保持一分钟一次心跳消息

- 方法
heartbeat

- 参数
```JSON
{
    "wsCmd": "heartbeat"
}
```
- 返回内容
```JSON
{
    "wsCmd": "getGowildList",
    "gowildId": "a4qns7akkb3o58o8bqf020180130172156",
    "rescode": "200",
    "errInfo": "None",
}
```

- - -
#####  二、绑定接口

- 方法
getGowildList,根据gowildId获取房间号

- 参数
```JSON
{
    "wsCmd": "getGowildList",
    "gowildId": "abcdefg"#不传这个参数，会返回所有房间列表
}
```

- 返回内容
```JSON
{"wsCmd": "getGowildList",
 "gowildList": 
     [
         {"gowildId": "abcdefg", "roomNo": "2507"}, 
         {"gowildId": "112233", "roomNo": "A101"}
     ], 
 "rescode": "200", 
 "errInfo": "None", 
 "cmdMessage": {"wsCmd": "getGowildList"}}

```

- - -
##### 三、获取场景列表

- 方法
```JSON
{
    "wsCmd": "getSceneList",
    "roomNo": "2507"
}
```

- 返回内容
```JSON
{"sceneList": 
[
"明亮模式", 
"睡眠模式", 
"起夜模式", 
"影音模式", 
"灯光全开", 
"灯光全关", 
"打开窗帘", 
"关闭窗帘"], 
"wsCmd": "getSceneList", 
"rescode": "200", 
"cmdMessage": {"wsCmd": "getSceneList", "roomNo": "2507"}}
```
- 出错返回
```JSON
{"wsCmd": "getSceneList", 
"rescode": "400", 
"errInfo": "no such roomNo", 
"cmdMessage": {"wsCmd": "getSceneList", "roomNo": "207"}}
```

- - -
##### 三、控制场景

- 方法
```JSON
{
    "wsCmd": "controlScene",
    "sceneName": "明亮模式",
    "roomNo": "2507"
}
```

- 返回内容
```JSON
{
"wsCmd": "controlScene", 
"rescode": "200", 
"errInfo": "None", 
"cmdMessage": {"sceneName": "明亮模式", "wsCmd": "controlScene", "roomNo": "2507"}}
```
- 出错返回
```JSON
{"wsCmd": "controlScene", 
"rescode": "400", 
"errInfo": "parameter error ,no devName or on such roomNo", 
"cmdMessage": {"sceneName": "明亮模式", "wsCmd": "controlScene", "roomNo": "507"}} 
```

- - -
##### 三、获取设备列表

- 方法
```JSON
{
    "wsCmd": "getDevList",
    "roomNo": "2507"
}
```

- 返回内容
```JSON
{
	"devList": [{
		"devStatus": null,
		"devName": "电视机",
		"actionCode": 2,
		"onLine": 1
	}, {
		"devStatus": null,
		"devName": "红外感应",
		"actionCode": 2,
		"onLine": 1
	}, {
		"devStatus": null,
		"devName": "红外感应",
		"actionCode": 1,
		"onLine": 1
	}, {
		"devName": "门锁",
		"actionCode": 0,
		"onLine": 0
	}, {
		"devStatus": {
			"cardStatus": 1,
			"statusInfo": "插卡"
		},
		"devName": "插卡取电",
		"actionCode": 1,
		"onLine": 1
	}, {
		"devStatus": {
			"switch": 1,
			"speed": 2,
			"mode": 1,
			"currentTemp": 16,
			"setTemp": 26
		},
		"devName": "空调",
		"actionCode": 1,
		"onLine": 1
	}, {
		"devStatus": null,
		"devName": "背景音乐",
		"actionCode": 2,
		"onLine": 1
	}, {
		"devName": "廊灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "背景灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "镜前灯副",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "卫灯副",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "镜前灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "卫灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "请退房",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "明亮模式",
		"actionCode": 1,
		"onLine": 1
	}, {
		"devName": "睡眠模式",
		"actionCode": 1,
		"onLine": 1
	}, {
		"devName": "起夜模式",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "影音模式",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "窗帘面板",
		"actionCode": null,
		"onLine": 1
	}, {
		"devName": "左夜灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "左阅读灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "背景灯带",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "右夜灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "右阅读灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "背景灯带副",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "吧台灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "纱帘",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "布帘",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "电视",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "天花灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "书桌灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "插座",
		"actionCode": null,
		"onLine": 0
	}, {
		"devName": "请勿扰",
		"actionCode": 1,
		"onLine": 1
	}, {
		"devName": "请稍候",
		"actionCode": 1,
		"onLine": 1
	}, {
		"devName": "请打扫",
		"actionCode": 0,
		"onLine": 1
	}],
	"wsCmd": "getDevList",
	"rescode": "200",
	"cmdMessage": {
		"wsCmd": "getDevList",
		"roomNo": "2507"
	}
}
```
- 出错返回
```JSON
{"wsCmd": "controlScene", 
"rescode": "400", 
"errInfo": "parameter error ,no devName or on such roomNo", 
"cmdMessage": {"sceneName": "明亮模式", "wsCmd": "controlScene", "roomNo": "507"}} 
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