## 从注释生成文档
要使用从注释生成文档，你必须先按照我们的格式编写注释，然后执行我们提供的脚本代码，脚本会自动搜索代码中的注释，生成文档并且提交到易文档平台。
> 从注释导入还是测试版本，可能会有一些变化

## 注释例子 
首先来看个完整的例子：
```python
/**
	@easydoc api
	title: /一级目录/二级目录/标题
	url: /api/regist
	desc: 这里是简单的描述内容
	method: POST
	headers:
		authorization 	string 	 required 	登录授权
	params:
		username 	string 	 required  	用户名
		password 	string 	 required  	密码
	response:
		code int 	 required  		是否成功
		msg string 	 optional  		错误提示信息
		userData 	 dict optional 		用户数据（子参数）
			_id		string 	 	required  	用户ID
			nickname 	string		required 	昵称
			age 		int 		required	年龄
	markdown:
		## 返回示例
		```javascript
		{
			"error_code": 0,
			"data": {
				"uid": "1",
				"username": "12154545",
				"name": "吴系挂",
				"groupid": 2,
				"reg_time": "1436864169",
				"last_login_time": "0"
			}
		}
		```

		>d 这是一个红色的引用段

		>s 这是表示成功的绿色引用段
	mock: 1
	@end
*/
```

## 规则介绍
- 支持所有语言，只要按照上面的规则去添加注释，就可以自动扫描创建成一个易文档的接口文档。
- 缩进必须是对齐的
- `@easydoc api` `@end` 必须配套使用，分别表示开始和结束
- `title` 表示接口标题。支持多层级目录，用/分隔每层目录，不存在的目录会自动创建
- 参数块当前只支持3个，`headers` `params` `response`，分别表示请求头参数、请求参数、响应参数，支持子参数，只需要缩进一下。
- `markdown` 下面的内容会填入到接口文档的 "说明 / 示例" 区域，使用 markdown 语法
- `mock` 表示是否自动生成 Mock 接口
- `headers` `params` `response` `markdown` 这几个支持多行输入，必须换行，并且缩进。


## 使用脚本导入

要使用脚本自动生成文档，你首先需要到 易文档官网-个人中心-APIKEY 生成一个apikey，这个是脚本访问你账户的凭证，请不要泄露
另外脚本还需要知道你把文档生成到哪个项目，所以你还需要提供一个`branchId`，在文档编辑页面，地址栏尾部的字符就是他的`branchId`，如图所示：
![image.png](https://sjwx.easydoc.xyz/46901064/files/k7kj08ot.png)
> 请注意，要在文档编辑页面查看，如果是预览页面查看，就是倒数第二个编码。



