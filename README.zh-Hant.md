# gjl

**針對 LLM 流量的自我託管原則邊界。**

檢查出站請求，透過有序規則運算式規則阻止敏感內容或改寫已解碼的請求主體，並在您掌控的邊界內嚴格控管提供者憑證。

[English](README.md) · [한국어](README.ko.md) · [简体中文](README.zh-Hans.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md)

[官方網站](https://gjl.io/) · [版本發布](https://github.com/gjl-io/gjl/releases) ·
[安裝與驗證](docs/install.md) · [安全漏洞回報](SECURITY.md) ·
[遠端存取說明](docs/remote-exposure.md) ·
[連線觀察工具](docs/connection-observer.md) ·
[授權條款](LICENSE.md)

## 快速安裝與上手

只需一行指令即可完成 gjl 的安裝。安裝程式會自動偵測您的作業系統、CPU 架構與桌面顯示環境，設定 `PATH` 環境變數並安裝對應元件。

### Windows (PowerShell)

```powershell
irm https://gjl.io/install.ps1 | iex
```

*或使用 `curl.exe`：*
```powershell
curl.exe -fsSL https://gjl.io/install.ps1 | powershell -Command -
```

### macOS 與 Linux (curl)

```bash
curl -fsSL https://gjl.io/install.sh | sh
```

### 僅安裝 CLI（排除桌面 GUI）

若您希望在具備圖形介面的系統中僅安裝獨立版 `gjl` CLI：

* **Windows：**
  ```powershell
  $env:GJL_CLI_ONLY=1; irm https://gjl.io/install.ps1 | iex
  # 或: & ([scriptblock]::Create((irm https://gjl.io/install.ps1))) -CliOnly
  ```
* **macOS 與 Linux：**
  ```bash
  curl -fsSL https://gjl.io/install.sh | sh -s -- --cli-only
  # 或: curl -fsSL https://gjl.io/install.sh | GJL_CLI_ONLY=1 sh
  ```

> [!TIP]
> **無周邊（Headless）與伺服器環境**：在沒有顯示伺服器的系統（例如 Linux 伺服器、無周邊 SSH 工作階段或 Windows Server Core）上，安裝程式會自動略過下載 Flutter Desktop，僅安裝獨立版 `gjl` CLI。

### 執行

安裝完成後，在目前終端機中直接執行：

- **桌面 GUI：**
  ```bash
  gjl gui
  ```
- **終端機 / 無周邊環境 (Headless)：**
  ```bash
  gjl run
  ```

### 更新 gjl

使用 `gjl update` 隨時保持元件處於最新狀態：

```bash
gjl update             # 更新本機已安裝的所有元件 (CLI 和/或 Desktop)
gjl update --cli-only  # 僅更新 gjl CLI
gjl update --gui-only  # 僅更新 Desktop GUI
gjl update --dry-run   # 僅檢查更新，不執行下載
```

手動二進位檔案下載與總和檢查碼驗證，請參閱[安裝與驗證指南](docs/install.md)。

## gjl 的適用對象

- **注重安全的個人與團隊**：希望在敏感內容送達提供者前進行攔截或遮罩，將提供者憑證保留在可控邊界內，並可選擇性地於本機日誌中擷取 LLM 請求及淨化後的內部回應複本。
- **追求更佳 LLM 成果的使用者**：在可受檢查的請求中，利用路由規則調整提示詞語句，或依特定工作流程將模型重新導向至提供者支援的較新版本。
- **在單一 LLM 提供者擁有多個帳戶的組織**：為每組憑證設定獨立路由，明確控制用戶端所使用的帳戶。gjl 不會在多個帳戶間進行自動負載平衡或容錯移轉。
- **使用多種編碼代理（Coding Agent）的開發者與團隊**：跨不同代理或工作流程追蹤 Token 消耗量、估算費用支出並比較使用模式。
- **團隊主管與管理者**：在共用基礎設施中依成員、用戶端識別碼或憑證彙整 Token 使用量與預估成本。

## gjl 的核心功能

gjl 運作於 LLM 用戶端（如編碼代理、IDE 擴充功能、開發者工具）與 LLM 提供者之間。每個路由（Route）嚴格歸屬於 Door 或 Gate，並獨立擁有其目標提供者、憑證來源、輸入驗證原則及遮罩規則。

受保護的請求流程為：

```text
已解碼請求主體
  → 阻止規則預檢 (Block precheck)
  → 有序替換規則 (Ordered replacements)
  → 憑證邊界 (Credential boundary)
  → 提供者 (Provider)
```

- **阻止或替換受檢請求中的相符內容**：路由規則於注入提供者驗證資訊前執行。涵蓋支援的已解碼 HTTP 請求主體、未壓縮的 Connect JSON 承載資料以及 WebSocket 文字訊息。不檢查 gRPC、Connect Protobuf 承載資料、壓縮的 Connect 訊框、WebSocket 二進位訊息、標頭或 URL 路徑與查詢參數。規則僅在受支援的路徑上保護實際符合的內容。
- **有目標地調整請求內容**：當解碼後的請求主體結構清晰固定時，路由可改寫提示詞語句或替換模型欄位。此機制與用於機密資料防護的主體規則完全相同。
- **透過路由隔離憑證，防止洩漏至用戶端**：每個路由綁定單一憑證來源，僅在出站邊界替換真實驗證資訊，避免上游金鑰殘留在用戶端設定中。
- **透過 Vault 向配對轉發節點仲介憑證**：Vault 不代理 LLM 流量，而是透過 Door-Vault mTLS RPC 提供靜態 API 金鑰並管理 OAuth 權杖重新整理週期。針對 OAuth，轉發節點僅於需要時借用短效存取權杖，重新整理材料絕不離開 Vault。
- **追蹤 Token 用量與預估費用**：gjl 在受所有者保護的帳本中記錄提供者回報的 Prompt、Completion 與 Cache Token，並結合離線美元單價計算預估費用。用量追蹤獨立於流量記錄，不儲存提示詞內文或秘密資訊，亦無需外部監控服務。
- **保留提供者回應原貌**：路由遮罩絕不修改傳遞給用戶端的回應主體；它僅針對大小受限的本機日誌複本進行淨化（sanitize）。轉發節點在轉發回應時會依標準移除必要的 HTTP hop-by-hop 標頭。
- **無流量內文的審計中繼資料外發**：管理者可設定遠端審計接收端（Sink）來收集事件與 Token 中繼資料，但接收端僅接收中繼資料。請求與淨化後的回應主體嚴格保存在受所有者保護的本機審計資料庫中，直至被明確刪除。
- **零廠商雲端相依的完全自我託管**：gjl 沒有廠商託管的控制平面、產品帳戶、登入機制、授權伺服器、裝置註冊或遙測收集。

## Door、Gate 與 Vault

Door、Gate 與 Vault 是單一守護行程（透過 `gjl run` 啟動）並行運作的角色能力，而非彼此分割的獨立版本。

| 角色 | 用途 | 典型部署邊界 |
| --- | --- | --- |
| **Door** | 本機轉發與路由交換中心 | 開發者工作站或本機伺服器 |
| **Gate** | 共用 TLS 閘道、組織原則邊界與憑證注入點 | 使用者或組織營運的網路邊界 |
| **Vault** | 提供 API 金鑰並持有重新整理材料的憑證代理仲介 | 專用的憑證安全隔離區 |

支援的部署路徑包含：

```text
LLM 用戶端 --> Door --------------------> 提供者
LLM 用戶端 --> Door --> Gate -----------> 提供者
LLM 用戶端 ------------> Gate -----------> 提供者
               Door <-> Vault
              僅憑證 RPC 通訊
```

Vault 絕不接收任何提示詞、原始碼、一般提供者請求或原始回應。

## 下載 gjl

請由 [GitHub Releases](https://github.com/gjl-io/gjl/releases) 取得適用於您作業系統與架構的安裝套件。
Alpha 版本標記為 **Pre-release**。在安裝前請詳閱發行說明並[驗證下載檔案](docs/install.md)。桌面安裝套件內已包含對應架構的 `gjl`。

初期預先發布版本尚未具備 Windows/macOS 平台受信任發行者簽章與 macOS 公證。因此暫不提供 Windows MSIX 套件；macOS 系統可能需要使用者手動確認 **強制開啟 (Open Anyway)**。具體信任限制與驗證步驟請參閱安裝文件。

| 平台 | Desktop + `gjl` | 獨立版 `gjl` |
| --- | --- | --- |
| Windows x64 | `gjl-windows-amd64.zip` | `gjl-windows-amd64.exe` |
| Windows Arm64 | — | `gjl-windows-arm64.exe` |
| Linux x64 | `gjl-linux-amd64.deb` 或 `gjl-linux-amd64.zip` | `gjl-linux-amd64` |
| Linux Arm64 | `gjl-linux-arm64.deb` 或 `gjl-linux-arm64.zip` | `gjl-linux-arm64` |
| macOS Intel | `gjl-darwin-amd64.pkg` 或 `gjl-darwin-amd64.zip` | `gjl-darwin-amd64` |
| macOS Apple silicon | `gjl-darwin-arm64.pkg` 或 `gjl-darwin-arm64.zip` | `gjl-darwin-arm64` |

### 桌面多語系支援

桌面應用程式支援 8 種介面語言。它會依循系統地區設定，當未比對到支援的語系時預設使用英文。核心產品名稱 gjl、Door、Gate 與 Vault 在所有語系環境中皆保持英文表示。

### Alpha 階段設定檔相容性說明

Alpha 版本不保證不同 Alpha 版本間狀態檔案的向下相容性。嘗試新版本時建議使用全新的設定檔 Profile。gjl 不會自動刪除或轉換既有 Profile。在切換 Profile 前，請明確備份或匯出所需的設定、憑證、TLS 憑證、配對記錄、審計日誌與用量資料，並妥善留存前一版本的二進位檔案以供還原。

## 開始使用

桌面安裝套件內含 `gjl` CLI 與守護程序。桌面應用程式透過受所有者保護的本機 IPC 管理守護程序。憑證在介面輸入後傳遞予守護程序持久化儲存並強制執行原則。

透過 gjl 轉發 LLM 流量通常需要三項基礎元素：

1. **路由 (Route)**：針對 Door 或 Gate 定義上游提供者目標、遮罩規則與驗證原則。預設情況下用戶端憑證維持原樣直通（passthrough），流量日誌與遮罩審計預設為關閉。
2. **相符的監聽器 (Listener)**：與該路由繫結的用戶端入口——工作站使用 Door（本機回環 loopback），共用網路存取使用 Gate（TLS）。（監聽器僅能繫結相同角色的路由。）
3. **LLM 用戶端的 Base URL**：將您的編碼代理、IDE 擴充功能或開發工具導向該監聽器位址。

### 桌面端設定

在桌面應用程式中，您可以透過設定精靈或手動進行配置：

- **快速設定 (精靈)**：按一下頂端儀表板 HUD 中的 **+ (新增)**。選取 **在此裝置上使用** 可一步自動完成前兩步，建立具備憑證直通的本機 Door 路由與回環監聽器。選取 **與團隊共享** 則會引導您設定共用的 **Gate** 端點或 **Vault** 憑證代理仲介。
- **手動設定**：開啟 **路由** 檢視個別建立並檢查路由與監聽器。

> [!TIP]
> **提供者憑證管理（可選）：** 預設情況下，gjl 僅將用戶端傳入的憑證直通至提供者而不進行儲存。若您希望由 gjl 在邊界統一管理、注入或代理憑證，請先在獨立的 **憑證** 目錄中完成登記，隨後再於路由中引用。

### 無周邊（Headless）或 CLI 管理

在無周邊環境或命令列終端機中，直接執行守護程序並透過隨附的 `gjl` 進行管理：

```console
$ gjl run
```

在另一個終端機視窗中：

```console
$ gjl status
$ gjl doctor
$ gjl route --help
$ gjl listener --help
$ gjl --help
```

CLI 與 Desktop 在 macOS/Linux 上透過 Unix 域通訊端通訊，在 Windows 上透過具名管道通訊。兩者絕不直接讀寫受守護程序保護的設定檔、憑證或審計資料庫。

## 使用路由替換規則

`replace`（替換）屬於請求主體規則，不僅用於機密資訊遮罩。在範圍嚴格限定的路由中，若經驗證特定用詞能提升任務品質，可將 `an apple` 改寫為 `the green apple`。同樣地，若提供者已支援新模型但用戶端工具尚未更新，可將請求中的模型欄位由 `gpt-5.6-sol` 自動升級為 `gpt-6-sol`。請注意：重寫無法憑空提供無法使用的模型，亦無法變更僅存在於標頭或 URL 中的模型名稱。

**務必依據實際解碼後的請求主體設計比對模式。** 在啟用規則前，請評估規則運算式是否能唯一鎖定目標文字。單獨的模型名稱或日常字詞可能頻繁出現在 Prompt、程式碼、範例或其他欄位中。建議暫時開啟路由的流量日誌，在桌面端活動記錄中或透過 `gjl audit query`、`gjl audit bodies`、`gjl audit body-save` 檢視本機擷取的請求主體（`body`）結構，據此設計模式。標頭數值不屬於主體替換範疇。若需檢視用戶端傳送的原始主體，請在啟用重寫前擷取：審計記錄中的請求主體記錄的是替換後送達提供者的內容。流量日誌預設為關閉，且在明確刪除前會持續留存於本機，請審慎評估保留需求後啟用。儲存至獨立檔案的主體需另外個別刪除。

例如，某次擷取到的 WebSocket `response.create` 請求主體為無空格緊湊 JSON：`{"type":"response.create","model":"gpt-6-sol",...}`，模型欄位前後由逗號圍繞。對於仍傳送舊模型名稱的用戶端，可配置如下規則：

```json
{
  "id": "upgrade-model",
  "mode": "replace",
  "pattern": ",\"model\":\"gpt-5\\.6-sol\",",
  "replacement": ",\"model\":\"gpt-6-sol\","
}
```

此範例高度依賴特定 JSON 結構：對於已排版（pretty-printed）JSON 或位於其他位置的 `model` 欄位將無法比對。請實際檢查用戶端的請求主體並依真實結構調整規則。gjl 採用 Go RE2 規則運算式語法，在對原始已解碼請求主體完成所有阻止（block）規則檢查後，依路由清單順序依次套用替換（replace）規則。規則絕不改寫送往用戶端的回應主體，僅對本機留存的記錄複本進行淨化。

針對敏感文字規則，可在用戶端 AI 的系統提示詞中宣告出站請求將於網路邊界進行遮罩改寫。說明預留位置與預期行為，而無需揭露機密本身。提供者接收到的已經是替換後的請求，因此請求內部的指令無法迫使其還原原始文字。對於設定使用 `<GJL_MASKED>` 的路由，可在代理指示中加入：

> gjl replaces matching sensitive text with `<GJL_MASKED>` before the provider receives the request. Keep that placeholder intact; do not try to reconstruct its original value.

規則變更後請透過實際請求進行驗證，隨後關閉暫時性流量日誌並明確清除不必要的審計事件。

關於從擷取之請求結構出發、驗證規則特異性的完整流程，請參閱[路由替換規則技能](skills/route-replacements/SKILL.md)。

## 安全模型

- 路由嚴格歸屬於 Door 或 Gate。Door 監聽器僅繫結 Door 路由，Gate 監聽器僅繫結 Gate 路由；單一路由無法跨角色共用。
- 遮罩規則歸屬於路由。在執行任何替換前，所有阻止規則皆會優先檢查原始已解碼請求；隨後替換規則依清單順序套用。
- 提供者驗證獨立於主體遮罩處理，根據提供者通訊協定機制選擇，而不取決於特定編碼代理的名稱。
- 提供者請求與憑證絕不流經 gjl 開發者營運的基礎設施。
- Door 採本機優先策略。針對遠端或共用存取，請使用啟用了 TLS 與 CIDR 存取控制的 Gate。嚴禁在缺乏嚴密邊界控制的情況下向外公開 Door。
- 本機流量主體不會自動過期。資料刪除必須透過明確、具備篩選條件或雙重確認的管理作業完成。
- Gate 可在受所有者保護的獨立本機儲存空間中盡力（best-effort）記錄觀察到的用戶端（Observed Client）中繼資料（來源 IP、受限的 User-Agent 及輔助宣告、驗證 HMAC 指紋等）。此類記錄並非經權威驗證的真實身分，刪除審計事件不會清除該獨立儲存庫。
- 管理者設定的遠端審計接收端可收集事件與 Token 用量等中繼資料，但絕不包含流量主體或未經處理的原生觀察訊號。在設定保留原則與遠端存取時應將此類中繼資料視為具潛在敏感性。
- 更新檢查僅具諮詢性質。正式發布版守護程序僅從本 GitHub 存放庫讀取公開標籤，絕不會自動下載或安裝更新。

在將任何監聽器向主機外部公開前，請詳閱[透過 Gate 進行遠端存取](docs/remote-exposure.md)。

## 為何保持原始碼私有

我們認為，隨著 AI 時代的演進，重現基礎轉發節點的門檻大幅降低，公開完整實作帶來的實質效益有限。gjl 處理極具隱私性的 LLM 流量與憑證，我們評估全面公開原始碼將使攻擊者更容易尋找潛在漏洞。因此，將產品核心原始碼保持私有是我們安全防禦策略的一環。

您可以透過公開的 Python [連線觀察工具](docs/connection-observer.md)隨時檢查執行中的 gjl 程序所建立的網路連線。該工具會自動標示可識別的路由上游、Gate/Vault 連線、已知 OAuth 伺服器與 GitHub；無法識別的目的地將標示為 `UNKNOWN` 供您檢視。該工具不作主觀安全判定，亦不讀取請求主體或憑證。

啟動 gjl 後，於存放庫根目錄執行：

```sh
python -m pip install -r tools/requirements.txt
python tools/observe_connections.py --duration 600
```

## 存放庫結構

本存放庫為 gjl 的公開發布中心，包含：

- 官方發布版本下載與標準版本標籤；
- 公開的營運與安全說明文件；
- 可標示可見網路對等連線的開源[本機連線觀察工具](docs/connection-observer.md)；
- 協助安全設定受支援工作流程的智慧體技能（Agent Skills）；
- 指向 CLI、Desktop 與產品文件的 AI 工作指南 [`llms.txt`](llms.txt)。

目前提供的智慧體技能包含：

- [`skills/gjl-operations`](skills/gjl-operations/SKILL.md) — 檢查已安裝的 CLI，指引 Desktop 畫面與本機管理操作。
- [`skills/route-replacements`](skills/route-replacements/SKILL.md) — 引導根據擷取的請求主體結構設計封鎖與替換規則（包含敏感文字、提示詞語句與模型欄位）。
- [`skills/remote-exposure`](skills/remote-exposure/SKILL.md) — 引導 Door 與 Gate 間的 mTLS 配對並檢查遠端存取邊界。

## 漏洞回報與授權

安全漏洞請透過 [GitHub 私密漏洞回報機制](https://github.com/gjl-io/gjl/security/advisories/new)提交。
非安全性相關的一般 Bug 請使用 [GitHub Issues](https://github.com/gjl-io/gjl/issues/new) 反映。請勿在公開 Issue 中包含金鑰或私密流量資料。詳情參閱 [SECURITY.md](SECURITY.md)。

存放庫授權條款與產品二進位授權統一彙整於 [LICENSE.md](LICENSE.md)。公開安裝指令碼、Python 工具與智慧體技能採用 [MIT 授權條款](LICENSE-MIT)。官方產品二進位檔案依據[產品二進位授權](PRODUCT-LICENSE.md)作為專有軟體發布。適用範圍詳見[存放庫聲明 (NOTICE.md)](NOTICE.md)及[第三方聲明 (THIRD-PARTY-NOTICES.md)](THIRD-PARTY-NOTICES.md)。

## 專案承諾與保證

gjl 始終堅持本機優先與操作者完全自主原則：

- 無廠商營運的後端或雲端執行階段服務；
- 無產品帳戶、登入、付費功能鎖定或裝置登記；
- 無任何遙測（Telemetry）；
- 檢查更新時絕不傳送提供者請求、憑證、設定檔或審計資料；
- 絕不自動下載、安裝或復原更新。

唯一存在的廠商端網路互動僅限於對公開 GitHub 標籤的免驗證讀取、在使用者明確執行 `gjl update` 時下載官方發布檔案，以及在使用者明確要求時透過 Desktop GUI 在瀏覽器中開啟公開發布頁面。
