# **上海清鹤客控系统第三方设备WebSocket对接接口**

[TOC]
- - -
###  一、服务连接

```
测试服务地址：ws://iotd.cleartv.cn:9999
服务器地址，每个项目可能不同，需要配置，端口：9999
所有数据传输采用json格式
```

- - -
###  二、保持一分钟一次心跳消息

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
###  三、绑定接口

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
### 四、获取场景列表

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
### 五、控制场景

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
### 六、获取设备列表

- 方法
```JSON
{
    "wsCmd": "getDevList",
    "roomNo": "clear3f1"
}
```

- 返回内容
```JSON
{
	"devList": [{
		"devType": "hr_lock",
		"devName": "门锁",
		"devId": "011000000000630f110fffffffffffff",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devStatus": {
			"cardStatus": 0,
			"statusInfo": "拔卡"
		},
		"devId": "011000000000630f120fffffffffffff",
		"onLine": 1,
		"devName": "插卡取电",
		"devType": "hr_card",
		"actionCode": 2
	}, {
		"devStatus": {
			"switch": 1,
			"speed": 4,
			"mode": 4,
			"currentTemp": 21,
			"setTemp": 32
		},
		"devId": "011000000000630f80ffffffffffffff",
		"onLine": 1,
		"devName": "空调",
		"devType": "hr_airCondition",
		"actionCode": 1
	}, {
		"devType": "sz_curtain",
		"devName": "纱帘",
		"devId": "010000124b000e31d29f8",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devType": "sz_switch",
		"devName": "夜灯",
		"devId": "010000124b0014bfe5b71",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devType": "sz_switch",
		"devName": "廊灯",
		"devId": "010000124b0014bfe5b72",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devType": "sz_switch",
		"devName": "卫灯",
		"devId": "010000124b0014bfe5b73",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devType": "sz_switch",
		"devName": "天花灯",
		"devId": "010000124b0014c592fd1",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devType": "sz_switch",
		"devName": "书桌灯",
		"devId": "010000124b0014c592fd2",
		"actionCode": 0,
		"onLine": 1
	}, {
		"devType": "sz_switch",
		"devName": "吧台灯",
		"devId": "010000124b0014c592fd3",
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
### 七、控制设备

- 方法
```JSON
{
    "wsCmd": "controlDevice",
    "devId": "010000124b000e0bd0113",
    "roomNo": "clear3f",
    "devType": "sz_switch",
    "actionCode":0,//开:1，关:0，空调控制这个参数不生效
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
		"devType": "sz_switch",
		"wsCmd": "controlDevice",
		"devId": "010000124b0014bfe5b71",
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
	"errInfo": "no such device",
	"cmdMessage": {
		"devType": "sz_switch",
		"wsCmd": "controlDevice",
		"devId": "010000124b0014bfe5b712",
		"roomNo": "clear3f",
		"actionCode": 0
	}
}
```

- - -
### 八、设备状态变化通知消息
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

---
### 九、设备类型列表，（x）代表硬件类型不唯一,需匹配'_'后面字段
|设备分类|devType|actionCode|onLine|devId|devStatus|备注|
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|灯光开关面板|(x)_switch|0-关/1-开|0-在线/1-离线|string|无|
|空调面板|(x)_airCondition|0-关/1-开|0-在线/1-离线|string|详见空调属性|
|门锁|(x)_lock|0-关/1-开|0-在线/1-离线|string|无|只能控制开|
|窗帘电机|(x)_curtain|0-100,打开百分比|0-在线/1-离线|string|无|
|插卡取电|(x)_card|2|0-在线/1-离线|string|cardStatus:0-拔卡,1-插卡|只读|
|智能插座|(x)_adapter|0-关/1-开|0-在线/1-离线|string|无||

---
#### 1、空调属性
参数|类型|范围|说明|读写
|:-:|:-:|:-:|:-:|:-:|
|mode|unit8|1-制冷，2-制热，3-保持，4-通风|模式|读写|
|setTemp|unit8|15-32|设置温度|读写|
|currentTemp|unit8|15-32|当前温度|只读|
|speed|unit8|1-低速，2-中速，3-高速，4-自动，5-保持|风速|读写|
|switch|unit8|1-开，2-关|电源开关|读写|