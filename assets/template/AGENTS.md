# Dever 应用开发

先读取已安装的 `dever-language` skill；缺失时从官方仓库 https://github.com/shemic/dever-main-skills 安装。这里使用 Dever 语言，不是 Go Dever 框架。

- 源码放在 `module/<组件>/<领域>/`，按职责使用 `app`、`domain`、`model`、`api`、`port`、`adapter`、`job`；只创建实际需要的角色。
- 不写 `main.dever`、`package`、`import` 或 `expose`。API/CMD/Job 是入口；跨领域调用 App。
- 配置只用 `config/setting.json`，不增加环境变量配置。普通测试位于 `test/<组件>/<领域>/`，用与文件同名的零输入零输出函数。
- 修改前先读相关代码并复用既有逻辑；避免 `utils`、`common` 垃圾桶和无意义的碎片函数。
- 保持当前项目源码格式一致。Markdown 源码只编译顶层 `dever` 围栏，声明文档必须与源码一致。
- 修改后运行与改动对应的 `dever check .`、`dever fmt . --check`、`dever test .`；不得擅自修改生产数据、启动外部服务或运行全量压测。
- 安装、升级、依赖准备与业务运行分开；`run/build` 不隐式联网。没有用户要求，不提交或推送 Git。
