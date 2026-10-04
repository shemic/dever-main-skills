# 项目开发

新建最小项目：

```sh
dever new my_app
dever fmt my_app --check
dever check my_app
dever test my_app
dever run my_app -- hello.greeting.greet '{"name":"Dever"}'
dever build my_app --output my_app/program
./my_app/program hello.greeting.greet '{"name":"Dever"}'
```

创建 Markdown 项目用 `dever new my_app --markdown`。两种模板使用相同代码和行为，Markdown 另加编译器校验的说明。目标目录必须不存在，父目录必须已存在；不接受向现有项目合并或覆盖。build 输出也必须不存在。

模板只包含 CMD、App、配置、一个测试和开发指引，无需数据库或 HTTP 服务。实际项目在它的目录合同上扩展，替换演示领域，删除不再使用的示例与测试。添加 HTTP 时须完成 [站点与身份配置](application.md)，不能只把 cmd 换成 get。

```text
my_app/
  AGENTS.md
  README.md
  config/setting.json
  module/
    news/article/
      app.dever
      domain.dever
      model.dever
      port.dever
      adapter.dever
      job.dever
      api/
        admin/manage.dever
        front/browse.dever
  test/news/article/publish.dever
```

这是可用职责位置，不是要求创建全部文件。component、domain 和文件主题使用有业务意义的 ASCII 小写蛇形命名；类型用 PascalCase，方法和字段用 snake_case。不要增加任意第三层领域目录。组件按业务能力划分，领域按一致的数据和业务边界划分。

| 位置 | 责任和访问规则 |
| --- | --- |
| App | 跨领域公开能力，校验与业务编排；同领域用 `app.publish`，外部用 `news.article.publish` |
| Domain | 同领域内部业务规则；纯计算优先放这里，不承接数据库/外部 I/O |
| Model | 存储字段、索引、关系、迁移、Seed、静态 SQL；同领域 App 使用 ORM |
| Port | 外部能力的类型、操作与失败合同 |
| Adapter | 实现 Port；私有，不反调 App/Domain/Model |
| API | HTTP/CMD 入口绑定与自动 REST，无业务函数体 |
| Job | 持久任务声明，绑定同领域 App |
| Test | 文件同名、零输入零输出的唯一测试入口 |

简单领域保留角色单文件；复杂角色可以拆为 `app/publish.dever`、`app/search.dever` 等内聚主题，调用名不带文件名。非 API topic 目录不递归；不要只放一个 topic 文件形成空架构。App/Domain/Port/Adapter/Job 单文件与同名目录二选一；Model/API 主文件与 topic 目录可按编译器合同共存。只有 `api/` 可按站点和资源继续嵌套，目录会影响 URL。

单文件内允许多个相关类型、方法和分句。不要把每次字符串 trim、ID 转换、分页参数截断提成一个私有 helper。先使用标准能力、类型约束与 Model 自带分页。只有有独立业务含义、稳定不变量或真实复用的逻辑才抽取。

## 测试与检查

`test/hello/greeting/greet.dever`：

```dever
greet() () {
  assert_eq(hello.greeting.greet("Dever"), "Hello, Dever")
}
```

模板中的实际字符串以生成文件为准。测试只执行文件同名函数，不需要 main 或注解。`assert` 接受 Bool，`assert_eq` 要求同类型。测试可访问同领域 App/Domain，跨领域仅 App，不能直接写 Model CRUD。使用 Model 时运行器使用临时 SQLite；不使用 Model 时不需要数据库。它不会读取生产 setting.json 或生产 data。对业务失败使用 `result(call)` 配合 choice 分句验证。

常用命令：`fmt --check` 查格式，`check` 查语法/类型/目录/分句/配置，`api` 输出 API 合同，`test` 运行应用套件，`run` 开发执行，`build` 生成独立程序。不要发明 `test --filter`、`run api` 或 `dever init`。

源码放 module/，测试放 test/，部署配置放 config/，运行数据放 data/。生成程序从二进制同级 config/setting.json 读取配置。应用无需打包编译器；使用外部 Lib 时相关 runtime/依赖由 build 嵌入。只读 check 不证明真实数据库或部署验收。

## 核心与业务的区别

官方核心仓库是 `shemic/dever-main`：`crates/dever-core` 负责语言检查/编译，`crates/dever-runtime` 负责运行时，`crates/dever-cli` 负责命令，`library/` 是随版本提供的标准 Dever 源码。维护中的完整业务示例是 `examples/cms/dever` 与 `examples/cms/md`；`examples/old` 是历史回归，不作新项目模板。

开发普通应用无需复制或修改这些核心目录。可复用业务组件作为 Dever Package；外部 Python/JS/Go 生态称 Lib。多个项目共享机器安装的 Dever。
