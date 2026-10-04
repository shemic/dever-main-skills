# Dever 应用

这是无需数据库、鉴权或第三方工具的最小 CMD 项目。

在项目目录运行：

```sh
dever check .
dever fmt . --check
dever test .
dever run . -- hello.greeting.greet '{"name":"Dever"}'
dever build . --output hello-app
./hello-app hello.greeting.greet '{"name":"Dever"}'
```

问候结果为 `Hello, Dever`。输入由 `api` 的 CMD 声明解析并传给 `app.greet`；业务不读取环境变量，配置在 `config/setting.json`。

AI 开发规范见本项目 `AGENTS.md` 和已安装的 `dever-language` skill。官方开发 skill：https://github.com/shemic/dever-main-skills；语言源码：https://github.com/shemic/dever-main。

普通 `.dever` 与 Markdown `.dever.md` 共享语言规则。用 `dever new <新目录> --markdown` 创建 Markdown 项目。目录必须不存在，生成器不会覆盖已有项目。
