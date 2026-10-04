# 核心语法

以下片段说明语法。将它们放进正确角色文件并补完整调用链后检查，不能当作免配置 HTTP 项目。

## 类型和函数

```dever
type Greeting {
  message: Text
}

greet(name: Text) (response: Greeting) {
  response = Greeting { message = "Hello, " + text.trim(name) }
}
```

函数是 `name(输入) (命名输出) { 线性语句 }`，没有 function/return。调用按位置传参。零输入或零输出也写 `()`。单输出直接得到值；多输出调用返回只能按输出名访问的结果。App 的输入、输出和向外传播错误均为公开合同，不暴露 Domain/Adapter 私有类型。

常用类型：`Bool`、`Int`（检查溢出）、`Float`、精确 `Decimal`、`Text`、`Bytes`、`Uuid`、`Id`、`DateTime`、`Date`、`Time`、`Duration`、`Secret`、`Json`。可空用 `T?`，集合用 `List<T>`、`Map<K,V>`。Model ID 是每个 Model 独有的名义类型，不等于任意 Int。不得把不同表的 ID 混用。

record 用字段初始化；choice 用分支构造：

```dever
type State {
  Draft
  Published
  Rejected(reason: Text)
}

label(state: State.Published) (text: Text) {
  text = "published"
}

label(state: State.Rejected(reason)) (text: Text) {
  text = reason
}

label(state: other) (text: Text) {
  text = "draft"
}
```

## 分支与边界

没有 if、else、switch、match、条件表达式或递归。同名、同参数数量的分句必须连续，相同输出合同，互斥且穷尽；没有先匹配谁的顺序优先级。`other` 是同一参数位置所有明确模式的补集。

```dever
display(value: Text) (text: Text) {
  text = value
}

display(value: null) (text: Text) {
  text = "missing"
}

grade(score: Int < 60) (text: Text) {
  text = "fail"
}

grade(score: Int >= 60) (text: Text) {
  text = "pass"
}
```

支持完整类型、choice 分支、null、Bool/Text/数值字面量、Int/Decimal 范围与 other 模式；多输入检查全部输入组合。任一函数都必须为命名输出赋值。不要写 `return` 提前退出，按分句表示结果与失败。

集合遍历使用语言的 `map/filter/reduce/each` 等核心操作及静态 handler，不能加入 for/while。handler 的签名和可达调用链由编译器检查，不是运行期闭包或动态插件。具体签名查当前版本 `library/` 与核心语言指南，不杜撰 lambda 语法。

## 失败和能力

业务错误通过 choice 的 `error` 分支声明，`fail` 传播，`result(call)` 显式捕获；普通调用直接得到成功值。不能用字符串/任意 JSON 代替类型化失败，不能捕获后悄悄吞掉错误。错误映射到 HTTP 的方式见 application.md。

纯 Domain 函数可声明 `pure`，编译器检查其调用链；要从 Model REST 字段来源调用的业务转换必须是合规的同领域 pure Domain。外部文件/网络 I/O 经 Port/Adapter，不把系统调用塞入普通 App 或 Domain。

Dever 推断挂起，无需 async/await。直接调用按顺序完成；`run` 显式启动结构化子任务，`wait/stop` 消费 Task，任务不能逃逸所属作用域。Group/Channel/Stream 具有静态资源约束；不能跨挂起、线程或请求随意保存句柄。`result` 不改变调度，也不绕开 effect 检查。

`Secret` 不可打印、比较或转为普通 Text。密码使用现有 crypto 能力；不要自制哈希。声明类型、分句和 effect 报错时修正真实边界，不添加无意义中转函数、泛用返回包装或吞错分句来绕过检查。

更多完整语法以官方核心仓库同版本 `LANGUAGE.md` 为准；新建项目先使用本 skill 的已验证模板。
