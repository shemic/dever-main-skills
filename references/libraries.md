# 标准能力与依赖

内置 package 不需要 import、下载或把标准库复制到 module/。先查已有能力，避免项目里堆积 parse_id、page_slice、trim 包装函数。

| 能力 | 入口 |
| --- | --- |
| 文本 | `text.trim/lower/upper/contains/starts_with/ends_with/split/replace/join` |
| 数字 | `int.parse/to_text`、`decimal.parse/round/from_int`、`float.parse`、`math` |
| 字节 | `dever.bytes.from_text/to_text/from_ints/length/at/slice/concat` |
| 时间 | `dever.time.now/parse_datetime/format_datetime/parse_date/format_date/duration/add/subtract/difference` |
| 密码与摘要 | `dever.crypto.password_hash/password_verify/token/sha256/hmac_sha256/constant_time_eq` |
| 类型化 JSON | `dever.json`，API/CMD 通常直接复用自动 wire codec |
| HTTP/网络/文件 | `dever.http`、`dever.net`、`dever.io`，业务外部 I/O 按 Port 边界使用 |
| 请求与身份 | `dever.api`、`dever.auth`、`dever.site`，受入口可达性限制 |

这是查找索引，不保证省略的参数/返回值。精确函数签名在官方核心仓库同版本 `library/`，复杂标准能力先读取对应文件和 LANGUAGE.md。`parse` 常返回可空值，不能假定失败得到 0。新版本发布前 skill 索引与库签名须一起验证。

## Dever Package

Package 是可复用 Dever 组件。通过项目 setting.json 中的 `package.registry` 与 `package.use` 声明；显式 `dever package add|list|update|remove|doctor <root> ...` 管理。`dever.lock` 固定版本、摘要和传递依赖；Package 不能覆盖本地同名组件。不要在业务源码中引入 import 或自建 vendor 查找规则。

## 外部 Lib 与普通二进制

第三方生态叫 Lib。项目 `config/setting.json` 的根 lib 数组声明 `pip:name@version`、`npm:name@version` 或 Go 依赖，使用 `dever lib add/list/install/update/remove/doctor` 管理。add/update 自动准备实际需要的运行环境与构建工具；install 按已有锁精确恢复，不改变配置或锁。run/build 只消费锁，不联网，也不读取系统 Python、Node、Go 或 PATH。

锁记录原始来源、摘要、固定构建输入和产物。新机器缺少已构建产物时，install 使用固定输入重建并核对输出摘要；第三方构建不能重现相同字节时会明确失败，不能用更新锁或偷偷重新解析版本冒充恢复。检查详细错误后，由用户决定是否执行 update 重新生成锁。

Lib 必须通过领域 Port/Adapter 使用。Port 声明类型与失败合同，Adapter 实现它；App 只调用 Port。声明的类型、返回值、业务失败、超时和 capability 使用统一 Worker 协议，各语言 SDK 不替代编译器类型检查。Python/JS/Go SDK 与可用 runtime 必须匹配 Dever 发行版本。

普通 Linux 二进制不需要 Worker 协议。领域 `port.dever`：

```dever
execute(args: List<Text>, stdin: Bytes?) (output: dever.process.Output) fails dever.process.Error
```

`adapter.dever`：

```dever
external command "bin/tool" {}
```

将相应架构 ELF 放在领域的 bin/tool，App 调用 `port.execute(["--version"], null)`。结果有 code、stdout、stderr，字节显式转文本；参数不是 shell 字符串。非零退出码仍是结果，启动失败/超时/超限是错误。文件、网络、子进程能力显式声明且受配置授权，不能关闭沙箱来掩盖部署问题。

测试必须使用 Port fake，不执行真实第三方程序。跨到 ARM 时必须提供目标架构的库和二进制，Dever 不转换已有 x86 ELF。
