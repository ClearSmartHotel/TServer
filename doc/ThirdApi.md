# **上海清鹤客控系统第三方设备WebSocket对接接口**

[TOC]
- - -
#####  一、服务连接

```
测试服务地址：ws://iotd.cleartv.cn:9999
服务器地址，每个项目可能不同，需要配置，端口：9999
所有数据传输采用json格式
```

- - -
#####  二、保持一分钟一次心跳消息

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
	"heartSuccessTime": "2018-04-11 17:52:01",
	"wsCmd": "heartbeat",
	"rescode": "200",
	"errInfo": "None",
	"cmdMessage": {
		"wsCmd": "heartbeat"
	}
}
```

- - -
#####  三、绑定接口

- 方法
getGowildList,根据gowildId获取房间号

- 参数
```JSON
{
    "wsCmd": "getGowildList",
    "gowildId": "112233"#不传这个参数，会返回所有房间列表
}
```

- 返回内容
```JSON
{"wsCmd": "getGowildList",
 "gowildList": 
     [
         {"gowildId": "abcdefg", "roomNo": "A101"}, 
         {"gowildId": "112233", "roomNo": "clear3f"}
     ], 
 "rescode": "200", 
 "errInfo": "None", 
 "cmdMessage": {"wsCmd": "getGowildList"}}

```

- - -
##### 四、获取场景列表

- 方法
```JSON
{
    "wsCmd": "getSceneList",
    "roomNo": "clear3f"
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
"cmdMessage": {"wsCmd": "getSceneList", "roomNo": "clear3f"}}
```
- 出错返回
```JSON
{"wsCmd": "getSceneList", 
"rescode": "400", 
"errInfo": "no such roomNo", 
"cmdMessage": {"wsCmd": "getSceneList", "roomNo": "clear3f"}}
```

- - -
##### 五、控制场景

- 方法
```JSON
{
    "wsCmd": "controlScene",
    "sceneName": "明亮模式",
    "roomNo": "clear3f"
}
```

- 返回内容
```JSON
{
"wsCmd": "controlScene", 
"rescode": "200", 
"errInfo": "None", 
"cmdMessage": {"sceneName": "明亮模式", "wsCmd": "controlScene", "roomNo": "clear3f"}}
```
- 出错返回
```JSON
{"wsCmd": "controlScene", 
"rescode": "400", 
"errInfo": "parameter error ,no devName or on such roomNo", 
"cmdMessage": {"sceneName": "明亮模式", "wsCmd": "controlScene", "roomNo": "clear3"}} 
```

- - -
##### 六、获取设备列表

- 方法
```JSON
{
    "wsCmd": "getDevList",
    "roomNo": "clear3f"
}
```

- 返回内容
```JSON
{
	"devList": [{
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
		"devName": "左夜灯",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devName": "左阅读灯",
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
		"roomNo": "clear3f"
	}
}
```
- 出错返回
```JSON
{"wsCmd": "getDevList", 
"rescode": "400", 
"errInfo": "Bad Request", 
"cmdMessage": {"wsCmd": "getDevList", "roomNo": "clearf"}} 
```

- - -
##### 七、控制设备

- 方法
```JSON
{
    "wsCmd": "controlDevice",
    "devName": "空调",//设备名
    "roomNo": "clear3f",
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

- 返回内容
```JSON
{
	"wsCmd": "controlDevice",
	"rescode": "200",
	"errInfo": "None",
	"cmdMessage": {
		"wsCmd": "controlDevice",
		"devName": "空调",
		"roomNo": "clear3f",
		"actionCode": 0
	}
}
```
- 出错返回
```JSON
{
	"wsCmd": "controlDevice",
	"rescode": "400",
	"errInfo": "cant find device:'空调'",
	"cmdMessage": {
		"wsCmd": "controlDevice",
		"devName": "空调",
		"roomNo": "clear3f",
		"actionCode": 0
	}
}
```

- - -
##### 八、设备状态变化通知消息
```JSON
{
	"devStatus": {
		"switch": 1,
		"speed": 2,
		"mode": 2,
		"currentTemp": 24,
		"setTemp": 18
	},
	"devName": "空调",
	"onLine": 1,
	"wsCmd": "devStatus",
	"roomNo": "clear3f",
	"actionCode": 1
}
```