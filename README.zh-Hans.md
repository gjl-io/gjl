# gjl

**面向 LLM 流量的自托管策略边界。**

检查出站请求，通过有序正则表达式规则阻止敏感内容或重写已解码的请求体，并在您掌控的边界内严格管控提供商凭据。

[English](README.md) · [한국어](README.ko.md) · [简体中文](README.zh-Hans.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md)

[官方网站](https://gjl.io/) · [版本发布](https://github.com/gjl-io/gjl/releases) ·
[安装与验证](docs/install.md) · [安全漏洞报告](SECURITY.md) ·
[远程访问说明](docs/remote-exposure.md) ·
[连接观察工具](docs/connection-observer.md) ·
[许可证](LICENSE.md)

## 快速安装与上手

只需一条命令即可完成 gjl 的安装。安装脚本会自动检测您的操作系统、CPU 架构以及桌面显示环境，配置 `PATH` 环境变量并安装相应组件。

### Windows (PowerShell)

```powershell
irm https://gjl.io/install.ps1 | iex
```

*或使用 `curl.exe`：*
```powershell
curl.exe -fsSL https://gjl.io/install.ps1 | powershell -Command -
```

### macOS 与 Linux (curl)

```bash
curl -fsSL https://gjl.io/install.sh | sh
```

### 仅安装 CLI（排除桌面 GUI）

如果您希望在带有图形界面的系统中仅安装独立的 `gjl` CLI：

* **Windows：**
  ```powershell
  $env:GJL_CLI_ONLY=1; irm https://gjl.io/install.ps1 | iex
  # 或: & ([scriptblock]::Create((irm https://gjl.io/install.ps1))) -CliOnly
  ```
* **macOS 与 Linux：**
  ```bash
  curl -fsSL https://gjl.io/install.sh | sh -s -- --cli-only
  # 或: curl -fsSL https://gjl.io/install.sh | GJL_CLI_ONLY=1 sh
  ```

> [!TIP]
> **无头（Headless）与服务器环境**：在没有显示服务器的系统（如 Linux 服务器、无头 SSH 会话或 Windows Server Core）上，安装程序会自动跳过 Flutter Desktop 的下载，仅安装独立版 `gjl` CLI。

### 运行

安装完成后，在当前终端中直接执行：

- **桌面 GUI：**
  ```bash
  gjl gui
  ```
- **终端 / 无头环境 (Headless)：**
  ```bash
  gjl run
  ```

### 更新 gjl

使用 `gjl update` 随时保持组件处于最新状态：

```bash
gjl update             # 更新本地已安装的所有组件 (CLI 和/或 Desktop)
gjl update --cli-only  # 仅更新 gjl CLI
gjl update --gui-only  # 仅更新 Desktop GUI
gjl update --dry-run   # 仅检查更新，不执行下载
```

手动二进制下载与校验和验证，请参阅[安装与验证指南](docs/install.md)。

## gjl 的适用人群

- **注重安全的个人与团队**：希望在敏感内容到达提供商之前进行拦截或脱敏遮蔽，将提供商凭据保留在可控边界内，并选择性地在本地日志中捕获 LLM 请求及净化后的响应副本。
- **追求更优 LLM 效果的用户**：在可检查的请求中，利用路由规则调整提示词用语，或根据具体工作流将模型重定向至提供商支持的更新版本。
- **在单一 LLM 提供商拥有多个账号的组织**：为不同凭据配置独立路由，显式控制客户端所使用的账户。gjl 不会在多个账户间进行自动负载均衡或故障转移。
- **使用多种编码智能体（Coding Agent）的开发者与团队**：跨不同智能体或工作流追踪 Token 消耗量、估算费用支出并对比使用模式。
- **团队主管与管理者**：在共享基础设施中按成员、客户端标识或凭据聚合 Token 使用量与预估成本。

## gjl 的核心功能

gjl 运行在 LLM 客户端（如编码智能体、IDE 扩展、开发者工具）与 LLM 提供商之间。每个路由（Route）严格归属于 Door 或 Gate，并独立拥有其目标提供商、凭据来源、入站认证策略和脱敏遮蔽规则。

受保护的请求流向为：

```text
已解码请求体
  → 阻止规则预检 (Block precheck)
  → 有序替换规则 (Ordered replacements)
  → 凭据边界 (Credential boundary)
  → 提供商 (Provider)
```

- **阻止或替换受检请求中的匹配内容**：路由规则在注入提供商认证之前执行。覆盖受支持的已解码 HTTP 请求体、未压缩的 Connect JSON 载荷以及 WebSocket 文本消息。不检查 gRPC、Connect Protobuf 载荷、压缩的 Connect 帧、WebSocket 二进制消息、请求头或 URL 路径与查询参数。规则仅在受支持的路径上保护实际匹配的内容。
- **有针对性地调整请求内容**：当解码后的请求体结构清晰固定时，路由可改写提示词短语或替换模型字段。这与用于敏感数据防护的规则采用相同机制。
- **通过路由隔离凭据，防止泄漏至客户端**：每个路由绑定单一凭据源，仅在出站边界注入真实认证信息，避免上游密钥留存在客户端配置中。
- **通过 Vault 向配对中继代理分发凭据**：Vault 不代理 LLM 流量，而是通过 Door-Vault mTLS RPC 提供静态 API 密钥并管理 OAuth 刷新生命周期。对于 OAuth，中继仅在按需时借用短期访问令牌，刷新材料绝不离开 Vault。
- **追踪 Token 用量与预估费用**：gjl 在受属主保护的账本中记录提供商报告的 Prompt、Completion 与 Cache Token，并结合离线美元单价计算预估费用。用量追踪独立于流量日志，不存储提示词正文或密钥，也无需外部监控服务。
- **保留提供商响应原貌**：路由脱敏绝不改写转发给客户端的响应正文；它仅对大小受限的本地日志副本进行净化（sanitize）。中继在转发响应时会自动移除必要的 HTTP hop-by-hop 头。
- **无流量正文的审计元数据外发**：管理员可配置远程审计接收端（Sink）来收集事件与 Token 元数据，但其仅接收元数据。请求与净化后的响应正文严格保存在受属主保护的本地审计数据库中，直至被显式删除。
- **零厂商云依赖的完全自托管**：gjl 没有厂商托管的控制平面、产品账号、登录机制、许可证服务器、设备注册或遥测收集。

## Door、Gate 与 Vault

Door、Gate 与 Vault 是单个守护进程（通过 `gjl run` 启动）并发运行的角色功能，而非相互割裂的独立软件版本。

| 角色 | 用途 | 典型部署边界 |
| --- | --- | --- |
| **Door** | 本地中继与路由交换中心 | 开发者工作站或本地服务器 |
| **Gate** | 共享 TLS 网关、组织策略边界与凭据注入点 | 用户或组织自建的网络边界 |
| **Vault** | 提供 API 密钥并持有刷新材料的凭据代理 | 专用的凭据安全隔离区 |

支持的部署路径包括：

```text
LLM 客户端 --> Door --------------------> 提供商
LLM 客户端 --> Door --> Gate -----------> 提供商
LLM 客户端 ------------> Gate -----------> 提供商
               Door <-> Vault
              仅凭据 RPC 通信
```

Vault 绝不接收任何提示词、源代码、普通提供商请求或原始响应。

## 下载 gjl

请从 [GitHub Releases](https://github.com/gjl-io/gjl/releases) 获取适合您操作系统与架构的安装包。
Alpha 版本标记为 **Pre-release**。在安装前请阅读发布说明并[验证下载完整性](docs/install.md)。桌面安装包内已包含对应架构的 `gjl`。

初始预发布版本尚未包含 Windows/macOS 平台受信任发布者签名与 macOS 公证。因此暂不提供 Windows MSIX 包；macOS 系统可能需要用户手动确认 **仍要打开 (Open Anyway)**。具体信任限制与验证步骤请参阅安装指南。

| 平台 | Desktop + `gjl` | 独立版 `gjl` |
| --- | --- | --- |
| Windows x64 | `gjl-windows-amd64.zip` | `gjl-windows-amd64.exe` |
| Windows Arm64 | — | `gjl-windows-arm64.exe` |
| Linux x64 | `gjl-linux-amd64.deb` 或 `gjl-linux-amd64.zip` | `gjl-linux-amd64` |
| Linux Arm64 | `gjl-linux-arm64.deb` 或 `gjl-linux-arm64.zip` | `gjl-linux-arm64` |
| macOS Intel | `gjl-darwin-amd64.pkg` 或 `gjl-darwin-amd64.zip` | `gjl-darwin-amd64` |
| macOS Apple silicon | `gjl-darwin-arm64.pkg` 或 `gjl-darwin-arm64.zip` | `gjl-darwin-arm64` |

### 桌面多语言支持

桌面端应用支持 8 种界面语言。它会遵从系统区域设置，当未匹配到支持的语言时默认使用英语。核心产品名称 gjl、Door、Gate 与 Vault 在所有语言环境中均保持英文表记。

### Alpha 阶段配置隔离注意事项

Alpha 版本不保证不同 Alpha 版本间的状态文件向后兼容性。体验新版本时建议使用全新的配置 Profile。gjl 不会自动删除或转换历史 Profile。在更换 Profile 前，请显式备份或导出所需的配置、凭据、TLS 证书、配对记录、审计日志与用量数据，并妥善保留前一版本的二进制文件以备恢复。

## 开始使用

桌面安装包自带 `gjl` CLI 与守护进程。桌面应用通过属主保护的本地 IPC 管理守护进程。凭据在界面录入后交由守护进程持久化存储并执行策略。

通过 gjl 转发 LLM 流量通常需要三项基础配置：

1. **路由 (Route)**：针对 Door 或 Gate 定义上游提供商目标、脱敏规则与认证策略。默认情况下客户端凭据保持原样透传（passthrough），流量日志与脱敏审计默认关闭。
2. **匹配的监听器 (Listener)**：与该路由绑定的客户端入口——工作站使用 Door（本地回环 loopback），共享网络访问使用 Gate（TLS）。（监听器仅能绑定相同角色的路由。）
3. **LLM 客户端的 Base URL**：将您的编码智能体、IDE 扩展或开发工具指向该监听器地址。

### 桌面端配置

在桌面端应用中，您可以通过向导或手动完成配置：

- **快速配置 (向导)**：点击顶部仪表盘 HUD 中的 **+ (添加)**。选择 **在此设备上使用** 可一步自动完成前两步，生成带有凭据透传的本地 Door 路由与回环监听器。选择 **与团队共享** 则会引导您配置共享 **Gate** 端点或 **Vault** 凭据代理。
- **手动配置**：进入 **路由** 视图分别创建和查看路由与监听器。

> [!TIP]
> **提供商凭据管理（可选）：** 默认情况下，gjl 仅将客户端传入的凭据透传至提供商而不做存储。如果您希望由 gjl 在边界统一托管、注入或代理凭据，请先在独立的 **凭据** 目录中完成登记，然后再在路由中引用。

### 无头（Headless）或 CLI 管理

在无头环境或命令行终端中，直接运行守护进程并通过内置的 `gjl` 进行管理：

```console
$ gjl run
```

在另一个终端窗口中：

```console
$ gjl status
$ gjl doctor
$ gjl route --help
$ gjl listener --help
$ gjl --help
```

CLI 与 Desktop 在 macOS/Linux 上通过 Unix 域套接字通信，在 Windows 上通过命名管道通信。它们从不直接读写受守护进程保护的配置文件、凭据或审计数据库。

## 使用路由替换规则

`replace`（替换）属于请求体规则，不仅用于机密脱敏。在范围严格限定的路由中，若经过验证某种用词能提升任务质量，可将 `an apple` 改写为 `the green apple`。类似地，如果提供商已支持新模型但客户端工具尚未收录，可将请求中的模型字段由 `gpt-5.6-sol` 自动升级为 `gpt-6-sol`。请注意：重写无法凭空提供不可用的模型，也无法修改仅存在于 Header 或 URL 中的模型名称。

**务必依据实际解码后的请求体设计匹配模式。** 在启用规则前，请评估正则表达式是否能唯一确定目标文本。单独的模型名称或日常短语可能频繁出现在 Prompt、代码、示例或其他字段中。建议临时开启路由的流量日志，在桌面端活动记录或通过 `gjl audit query`、`gjl audit bodies`、`gjl audit body-save` 查看本地捕获的请求体（`body`）结构，据此设计模式。Header 值不属于请求体替换范畴。若需查看客户端发送的原始正文，请在激活重写前抓取：审计记录中的请求体记录的是替换后发送给提供商的内容。流量日志默认关闭，且在显式删除前将持续保留在本地，请根据保留需求合理开启。保存到单独文件的正文需要单独清理。

例如，某次捕获到的 WebSocket `response.create` 请求体为无空格紧凑 JSON：`{"type":"response.create","model":"gpt-6-sol",...}`，模型字段前后被逗号包裹。对于仍发送旧模型名称的客户端，可配置如下规则：

```json
{
  "id": "upgrade-model",
  "mode": "replace",
  "pattern": ",\"model\":\"gpt-5\\.6-sol\",",
  "replacement": ",\"model\":\"gpt-6-sol\","
}
```

该示例高度依赖特定 JSON 结构：对于格式化（pretty-printed）JSON 或位置不同的 `model` 字段不会生效。请实际抓取客户端请求体并按真实结构调整规则。gjl 采用 Go RE2 正则表达式语法，在对原始已解码请求体完成所有阻止（block）规则检查后，按路由列表顺序依次执行替换（replace）规则。规则绝不改写发往客户端的响应正文，仅对本地留存的副本进行脱敏。

针对敏感文本规则，可以在客户端 AI 的系统提示词中声明出站请求将在网络边界进行脱敏重写。告知其占位符和预期行为，而无需包含机密本身。提供商接收到的已经是替换后的请求，因此请求内部的指令无法使其还原原始文本。对于配置使用 `<GJL_MASKED>` 的路由，可在智能体指令中加入：

> gjl replaces matching sensitive text with `<GJL_MASKED>` before the provider receives the request. Keep that placeholder intact; do not try to reconstruct its original value.

规则修改后请通过真实请求进行测试，随后关闭临时流量日志并显式清理无用的审计事件。

关于从捕获请求结构出发、验证规则特异性的完整流程，请参阅[路由替换规则技能](skills/route-replacements/SKILL.md)。

## 安全模型

- 路由严格归属于 Door 或 Gate。Door 监听器仅绑定 Door 路由，Gate 监听器仅绑定 Gate 路由；单一路由无法跨角色复用。
- 脱敏规则归属于路由。在执行任何替换前，所有阻止规则都会优先检查原始已解码请求；随后替换规则按列表顺序执行。
- 提供商认证独立于正文脱敏，根据提供商的有线通信协议机制选择，而不依赖任何特定编码智能体的名称。
- 提供商请求与凭据绝不流经 gjl 开发者运营的基础设施。
- Door 采用本地优先策略。对于远程或共享访问，请使用启用了 TLS 与 CIDR 访问控制的 Gate。严禁在缺少严格边界控制的情况下向公网暴露 Door。
- 本地流量正文不会自动过期。数据删除必须通过显式、带过滤条件或双重确认的管理操作完成。
- Gate 可在属主保护的独立本地存储中尽力（best-effort）记录观测到的客户端（Observed Client）元数据（来源 IP、有限的 User-Agent 及补充凭据、认证 HMAC 指纹等）。这些记录并非经权威验证的人类身份，删除审计事件不会抹除该独立存储。
- 管理员配置的远程审计接收端可收集元数据（包括观测到的客户端/操作者标识以及提供商报告的 Token 用量），但绝不包含流量正文或原始观测信号。在配置保留策略与远程访问时应将此类元数据视为潜在敏感信息。
- 更新检查仅具建议性质。发布版守护进程仅从本 GitHub 仓库读取公开 Tag，绝不会自动下载或安装更新。

在将任何监听器暴露至主机外部前，请仔细阅读[通过 Gate 实现远程访问](docs/remote-exposure.md)。

## 为何闭源产品核心代码

我们认为，随着 AI 技术的进步，复刻基础中继变得更加容易，公开完整实现的边际收益正在降低。gjl 承载高度敏感的 LLM 流量与凭据，我们评估认为公开全部源码会降低攻击者挖掘潜在弱点的门槛。因此，保持产品源码私有化是我们安全防护策略的一部分。

您可以通过公开的 Python [连接观察工具](docs/connection-observer.md)随时审查正在运行的 gjl 进程建立的网络连接。它会自动标记可识别的路由上游、Gate/Vault 连接、已知 OAuth 服务器与 GitHub；未识别的目的地将标记为 `UNKNOWN` 供您审查。该工具不做主观安全判定，也不读取请求正文或凭据。

启动 gjl 后，在仓库根目录下运行：

```sh
python -m pip install -r tools/requirements.txt
python tools/observe_connections.py --duration 600
```

## 仓库结构

本仓库为 gjl 的公开分发中心，包含：

- 官方版本下载与权威版本标签；
- 公开的运维与安全文档；
- 可标记可见网络连接的开源[本地连接观察工具](docs/connection-observer.md)；
- 协助安全配置受支持工作流的智能体技能（Agent Skills）；
- 指向 CLI、Desktop 和产品文档的 AI 任务指南 [`llms.txt`](llms.txt)。

目前提供的智能体技能包括：

- [`skills/gjl-operations`](skills/gjl-operations/SKILL.md) — 检查已安装的 CLI，指引 Desktop 页面和本地管理操作。
- [`skills/route-replacements`](skills/route-replacements/SKILL.md) — 指导根据捕获的请求体结构设计阻断与替换规则（包含敏感文本、提示词短语及模型字段）。
- [`skills/remote-exposure`](skills/remote-exposure/SKILL.md) — 指导 Door 与 Gate 之间的 mTLS 配对并核查远程访问边界。

## 漏洞报告与许可证

安全漏洞请通过 [GitHub 私密漏洞报告渠道](https://github.com/gjl-io/gjl/security/advisories/new)提交。
非安全相关的普通 Bug 请通过 [GitHub Issues](https://github.com/gjl-io/gjl/issues/new) 反馈。切勿在公开 Issue 中包含密钥或私密流量数据。详情参阅 [SECURITY.md](SECURITY.md)。

仓库许可证条款与产品二进制许可证统一汇总于 [LICENSE.md](LICENSE.md)。公开安装脚本、Python 工具及智能体技能采用 [MIT 许可证](LICENSE-MIT)。官方产品二进制文件遵循[产品二进制许可证](PRODUCT-LICENSE.md)（专有软件）。具体范围详见[仓库声明 (NOTICE.md)](NOTICE.md)及[第三方声明 (THIRD-PARTY-NOTICES.md)](THIRD-PARTY-NOTICES.md)。

## 项目承诺

gjl 始终遵循本地优先与操作者全权掌控原则：

- 无厂商运营的后端或云端运行时服务；
- 无产品账号、登录、付费功能锁定或设备登记；
- 无任何遥测（Telemetry）；
- 更新检查绝不包含提供商请求、凭据、配置或审计数据；
- 绝不自动下载、安装或回滚更新。

唯一存在的厂商端网络交互仅限于对公开 GitHub Tag 的免认证读取、在用户明确执行 `gjl update` 时下载官方发布文件，以及在用户明确要求时通过 Desktop GUI 在浏览器中打开公开 Release 页面。
