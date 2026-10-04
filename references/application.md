# 应用接口、数据与后台任务

## API 和 CMD

`module/news/article/api/admin/manage.dever`：

```dever
get list = app.list
get detail = app.detail
post create = app.create
put replace = app.replace
delete remove = app.remove
post publish = app.publish
```

API 无函数体，继承 App 输入/输出签名。支持 get/post/put/delete，当前没有 patch、旧 get_ 前缀或源码内 site 声明。`cmd greet = app.greet` 生成 `component.domain.greet` 命令，参数来自单个 JSON 对象；main.dever 不存在，也不读取命令行参数。

GET/DELETE 从 query 读标量参数，POST/PUT 从 JSON body 读参数；额外、重复或缺少必填字段均拒绝。无需自己读 body 或构造 dever.http.Response。成功统一为 `{"code":0,"message":"ok","data":...}`；错误 data 为 null，code 对应状态码。接口必须绑定一个可序列化输出，输出名可自定。

`dever.api.Error` 中 Invalid/Unauthorized/Forbidden/NotFound/Conflict/TooManyRequests 对应 400/401/403/404/409/429；未知内部失败记录脱敏日志并返回安全的 500。

写 HTTP/CMD/Job 调用链由入口建立事务；GET 调用链不能写库或入队。密码 hash/verify 是例外：不能让昂贵密码运算占用入口长事务，实际写入必须放显式短 transaction，并在其中重新检查依赖状态。不能为了“默认有事务”而删除这种短事务。

## 站点、身份与权限

`sites.admin.path = "admin"` 匹配领域内 `api/admin/**`，front 同理。文件名 topic 也进入 URL；上述 publish 是 `/news/article/admin/manage/publish`。每条 HTTP 声明只能匹配一个站点，重叠或遗漏配置会失败；path 不改写 URL，也不匹配 `api/admin.dever`。

所有 HTTP 默认鉴权并校验精确权限。只有明确匿名操作写 `public post login = app.login` 等单条 public 声明；没有 public rest、public cmd、auth.require 或每个业务文件的权限注册代码。

配置的 auth provider 引用一个项目自己的 `verify` App 方法，验证账号、会话、成员和租户关系。输入是 `dever.auth.Claims`，输出 record 必须且只能包含 `id: Text`、`user_id: <UserModelId>?`、`tenant_id: <TenantModelId>?`；只能读 global Model，不能写库、拿原始 Header 或返回自报权限。

认证成功的受保护 App 可读取 `dever.auth.id()`、`session()`、`user_id()`、`tenant_id()`、`dever.site.key()`；来源是隐藏可信上下文，不能让客户端提交 user_id/tenant_id 当作身份。名义 ID 必须与站点 verify 的类型对应，可空 ID 经分句处理后才能使用。public/CMD/Job/普通测试不会自动获得身份读取能力。

核心生成 `component.domain.site.action` 权限目录，method 是元数据，不额外拼进权限键。REST 的 action 固定为 read/create/replace/delete。核心维护角色、用户角色、角色权限；项目无需重建这些表。App 用 `dever.auth.permissions/save_role/grant_role/revoke_role/disable_role` 实现后台授权入口，具体参数查当前库签名。它们只能从受保护写 API 到达。资源所有权可用 `dever.auth.owns_user(id)`，不等同于接口角色权限。

Cookie 登录/退出用 `dever.auth.issue_cookie(subject, session, tenant)` 与 `clear_cookie()`。Header/Cookie 使用 `dever.api` 读取/设置，无需显式 context 参数。密钥来自部署配置；Cookie 写入和 Cookie 认证的写请求需要精确同源校验，站点配置 origin。敏感头不能当普通 Text 读取。

## Model、CRUD 与业务编排

`module/news/article/model.dever` 的主记录应为 Article：

```dever
type Article {
  title: Text(1, 200)
  body: Text
}
```

自动有只读 `id` 与 `created_at`。字段支持 default、private、unique、index；范围和长度在存储边界验证。关系使用目标 Model 专有 id 字段，不用 Int 代替外键。

同领域 App 可用 `model.create({...})`、`model.get(id)`、`model.update(id,{...})`、`model.delete(id)`、`model.list({where=...,order=[created_at.desc,id.desc],page=1,size=20})`。这是编译器静态 DSL，不是动态字典 SQL；不用手写 repository。聚合、关联和插入流程仍由 App 明确编排，不能自动推测关联图级联写入。

纯粹 CRUD 可在 API 写 `rest model`，多 Model 时指定 `rest model.<topic>`。Model 中 `create = expr`、`replace = expr`、`search = expr` 控制 REST 字段来源/查询；引用 input 表示客户端同名输入转换，不引用 input 表示服务端提供且禁止客户端提交。不要改成 post/put/get 字段关键字。

`private owner user_id: ... = dever.auth.user_id()` 在创建时赋值，并将所有权条件加入全部读写 SQL；不是只在输出隐藏 user_id。owner 策略、关联查询、复杂输入输出或发布状态机需要 App，不能把它们做成 CRUD 重复包装或藏在 API 里。App 对外用明确 View，别泄漏 Model 私有字段。

## 租户、任务与部署配置

配置只有 database 租户隔离：`tenant.database` 选控制连接，`global type` 使用平台库，其余持久 Model 与 Job 使用租户库。没有 field/table/mode 配置。租户缺失、未迁移或 schema 过期明确失败，不回退平台库。

运维命令：`dever tenant migrate <root> <id>`；`dever tenant owner <root> <id> <site> <user-id>` 建立核心 Owner；`dever tenant component enable|disable <root> <id> <component>` 控制租户功能。可用租户组件从 Model/Job 推导，不手写 Profile 分组。

job.dever 声明持久任务并绑定 App；enqueue 与事务、重试、调度、权限重验使用核心机制，不另写后台死循环。实际 Job 声明从对应版本指南和 CMS publishing/schedule 示例复用，不能把第三方 Worker 当持久 Job。

部署配置的真实结构可查官方 CMS `config/setting.json`，只添加项目用到的 database、tenant、auth、sites、http、job、runtime、log。最小 CMD 项目只需模板配置。密码、token 与真实数据库连接不提交 Git。
