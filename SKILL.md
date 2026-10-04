---
name: dever-language
description: 开发、检查、测试或维护 Dever 语言应用（.dever、.dever.md），创建新项目，安装或更新 dever 命令，编写 App、Domain、Model、API、CMD、Job、Port/Adapter，接入 Dever Package 或 Python/JS/Go Lib 时使用。也用于 Dever 应用目录、权限、租户和命名约束检查。不要用于 Go Dever 框架、dever-go 或普通 Go 组件开发。
---

# Dever 语言开发

Dever 是独立语言。应用不写 Go、Rust，也不沿用 Go Dever 的 service、Page JSON 或 Provider 目录。

## 先确定版本和范围

1. 读取用户项目的 `AGENTS.md`、现有目录和 `config/setting.json`。回答、分析、诊断只做只读检查；用户要求修改时再实施，不擅自安装软件、改服务或改全局命令。
2. 若已安装机器版 Dever，新项目运行 `dever skill path`，已有项目运行 `dever skill path <project-root>`，读取返回目录中的 `SKILL.md` 与本次需要的参考文件。已经在那个目录读取本 skill 时不再递归加载。它由 `dever update` 与核心一起更新；已有项目按其可选 dever.version 选择对应指引，不能把活动版本新增语法强加给旧项目。
3. 尚无 `dever` 时按 [安装与更新](references/install.md) 引导安装；不能把 `dever-go` 当作 Dever 语言命令。公开发行包缺失时如实说明，不编造成功、不自动编译一套缺少 runtime 的开发二进制。
4. 新项目使用 `dever new <new-directory>`；Markdown 项目加 `--markdown`。不要手工猜模板，不覆盖已有目录。项目模板的用途和检查命令见 [项目开发](references/development.md)。

## 按需要阅读

| 工作 | 先读 |
| --- | --- |
| 新项目、目录、命名、测试与交付 | [development.md](references/development.md) |
| 类型、分句、函数、集合、失败和并发 | [language.md](references/language.md) |
| HTTP/CMD、Model、权限、租户、Job | [application.md](references/application.md) |
| 标准能力、外部生态、Package | [libraries.md](references/libraries.md) |
| Markdown 源码 | [markdown.md](references/markdown.md) |
| 安装命令、安装 skill、更新 | [install.md](references/install.md) |

只加载当前任务相关参考。当前版本的编译器检查和已验证模板决定语法；参考中没有的调用先查官方对应版本源码，不能按其它语言习惯杜撰方法。

## 必须遵守的应用边界

- 配置只在 `config/setting.json`；不通过环境变量读取配置、密码、数据库 URL 或选择工具链。不要把 Dever 的官方仓库地址、更新配置写入业务项目。
- 应用目录是 `module/<component>/<domain>/<role>.dever`；role 只有 `app/domain/model/port/adapter/api/job`。复杂职责再按主题拆分，不机械地每个函数建一个文件，不建 `common/utils/helper/base/service` 杂物目录。
- 不写 `package/import/exposes/main`。应用入口由 API、CMD、Job 声明生成。App 是对外领域能力；跨领域只调用目标 App，不直接调用其私有 Model、Domain、Adapter。
- API 只声明绑定或 REST，App 编排，Domain 保存内聚的业务规则，Model 声明持久化合同，Port/Adapter 隔离外部 I/O。已有标准能力直接复用，禁止重复手写 ID 解析、分页裁剪、JSON 拼装等碎片函数。
- 函数使用命名输出和互斥、穷尽的相邻分句；没有 `if/else/switch/match/return`、任意循环或递归。不要靠分句顺序隐藏重叠规则。
- HTTP 默认有权限，匿名入口才写 `public`。不添加 `auth.require`、客户端自报身份/权限或每个 API 重复鉴权。站点按配置里的 API 目录匹配，租户按数据库隔离。
- 测试放在 `test/<component>/<domain>/<topic>.dever`，入口为文件同名 `topic() ()`。外部调用使用 case-local Port fake，不在普通测试启动真实 Lib 或访问真实业务数据库。
- `run/build` 离线。依赖准备必须用显式 `dever package` / `dever lib` 命令；不扫描宿主 Python、Node、Go 或 PATH 来充当运行环境。

## 工作方式

修改前先查现有领域、App 调用链和标准能力。选最少且内聚的文件，复用相同业务规则；不要为了去重引入没有当前用途的新层。

完成后运行当前改动必需的 `dever fmt <root> --check`、`dever check <root>`，以及适当的应用测试。`dever test` 会运行这个项目的全部应用测试，没有筛选参数；已有大项目不擅自全量测试。新项目模板的小套件可完整验证。需要 `run/build`、启动 HTTP、接真实数据库或更改系统安装时先遵守用户的授权和运行约束。

交付说明实际改动、验证结果与未验证边界。能编译不等于业务验收、性能验收或已发布；不要伪造通过。
