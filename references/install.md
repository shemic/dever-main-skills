# 安装与更新

官方仓库：核心 `https://github.com/shemic/dever-main`，本 skill `https://github.com/shemic/dever-main-skills`。Git 源码仓库和可运行发行包不同；安装器从核心仓库 Releases 下载，不把仓库地址写到业务项目配置。

## 先安装 skill

将本仓库放到 AI 工具的 skill 发现目录，目录名为 `dever-language`，其下直接有 SKILL.md。例如用户明确选择 Codex 的个人 skills 目录后，可以克隆到 `/用户实际主目录/.agents/skills/dever-language`；不要把示例路径当作当前用户真实路径，不自动修改全机其它人的目录。

```sh
git clone git@github.com:shemic/dever-main-skills.git <AI技能目录>/dever-language
```

也可从 HTTPS 仓库克隆，或由支持 Git 仓库的 skill 安装器安装整个根目录。重载工具的 skill 列表后，用户请求“用 Dever 新建项目”即可触发本 skill。这是 Dever 语言的 dever-language，不是 Go 框架的 shemic-dever。

## 安装 dever

先检查 `dever --help`。机器版提供 new、install、update、target、version、skill；仅源码开发二进制不管理机器安装。不要把已有同名命令直接删掉或覆盖，先识别归属。

初次安装需要 Linux、Python 3 和 `/usr/bin/openssl`；它们只用于校验和安装，生成的应用不依赖 Python、Node、Go 或 Rust。检查本 skill 的安装脚本后，由用户授权执行：

还须满足所选发行包的主机 ABI 要求；当前准备的 Linux x86_64 编译器要求 glibc 2.39。ARM64 应用交叉构建可在 x86_64 主机使用，不能据此宣称 ARM64 宿主编译器包已经发布。

```sh
sudo python3 <skill目录>/scripts/install.py
```

该命令下载当前平台最新已签名基础包。先用独立公钥校验发行目录，再验证引导程序及其私有库的摘要，由引导程序解压 Zstandard 包；无需系统 zstd。安装 `/opt/dever`、`/usr/local/bin/dever`、机器共享服务和必要沙箱策略，默认启动服务。`--no-start` 可仅安装。没有对应正式资产时明确失败，不修改已安装版本。

基础包包含 Dever 编译器、本机应用编译资源、四种数据库运行库和配套 skill。Python、Node、Go、第三方原生构建工具与 ARM 应用目标按需安装，保存在机器共享资源目录；同一版本的多个用户和项目共用一份。

## 按需准备资源

首次添加或更新 Lib 时，`dever lib add/update <project-root> ...` 自动准备相应生态，只有进入源码构建流程时才准备构建工具。已有 `dever.lock` 的项目在新机器运行 `dever lib install <project-root>`，按锁恢复依赖，保持配置和锁文件不变；没有 Lib 的 Python/JS/Go Adapter 也可通过该命令准备环境。缺少锁时先显式 `dever lib update <project-root>` 生成锁。不要把 install 当作重新选版本的 update。

在 x86_64 机器准备 ARM64 应用目标：

```sh
dever target add linux-aarch64
dever lib install <project-root> --target linux-aarch64
dever build <project-root> --target linux-aarch64 --output <新文件>
```

只用 Dever、没有外部依赖的项目省略 lib install。目标 Lib 必须已有匹配目标的锁；首次生成 ARM 锁使用 lib add/update 的同名 target 参数。准备会显式联网，后续 run/build 离线；缺资源时执行提示的准备命令，不改用系统解释器。target add 准备当前活动版本，锁定其它编译器版本的项目先准备并选择对应版本。

已准备本地发行包时：

```sh
sudo python3 <skill目录>/scripts/install.py --release /可信发行目录 --trusted-key /独立确认的公钥文件
```

测试或镜像制作增加 `--system-root /已有的自有镜像目录`；不会启动宿主服务。安装器生成的临时 `config/setting.json` 仅供机器 bootstrap 使用，包含本地发行路径、安装根和公钥路径；不是业务配置，不写发行仓库地址或环境变量。

公钥可公开提交；签名私钥绝不能进 skill、源码仓库或发行包。只有已独立确认的公钥才可作为 `--trusted-key`，不能从未知下载包顺手取一把钥匙作为信任依据。

## 一条命令更新核心与 skill

```sh
sudo dever update
dever version
dever skill path
```

update 只访问内置官方发行源，先准备核心、同版本完整 skill，以及当前活动版本已安装的扩展，再切换活动版本。未使用的扩展不会一起下载；任一准备失败保留原活动版本。普通 check/test/run/build 不检查更新、不隐式联网。

本仓库直接安装的 skill 在开始开发时先运行 `dever skill path` 并加载该版本的完整 skill，不必每个项目 git pull。也可以用 `dever skill install <新的AI技能目录>/dever-language` 安装稳定的薄入口，之后每次自动解析当前机器版本；已有目录不会被覆盖。不要把新入口嵌套装进已经存在的完整 skill 目录。

项目可选 `config/setting.json` 的 `dever.version` 锁定准确 `major.minor.patch`，未锁定时使用机器活动版本。`dever install 版本` 准备指定版本；`dever use 版本` 显式切换活动版本。update 不改业务项目文件或数据库。锁定项目用 `dever skill path <project-root>` 读取对应指引，不能仅凭活动版指南采用新语法。

## 源码维护者

```sh
git clone --recurse-submodules git@github.com:shemic/dever-main.git
```

`skills/` 是独立仓库的 submodule，核心固定一个经验证的提交；修改 skill 先提交/推送 skill，再在核心提交其引用。普通应用开发者无需克隆核心或编译 Rust。首个正式发行资产发布前，安装器的默认下载会明确报告未发布；可用已准备的本地发行包验证流程。
