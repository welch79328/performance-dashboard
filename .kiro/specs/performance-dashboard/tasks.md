# performance-dashboard - 實作任務清單

> 更新時間：2026-05-14T11:00:00.000Z
> 版本：v3（四大評估維度）

---

## 任務 1：專案初始化 (P)

> 需求對應：1, 2, 10, 12, 13

### 1.1 建立後端 FastAPI 專案

建立 `backend/` 目錄，初始化 Python 虛擬環境，安裝 FastAPI、uvicorn、httpx、pydantic、python-jose、passlib、openpyxl、cachetools。建立 `app/main.py` 入口與 `app/config/settings.py`。建立 `.env` 範本（`MONDAY_API_TOKEN`、`JWT_SECRET`、`USERS_CONFIG`）。

- [x] `uvicorn app.main:app` 可正常啟動，`/docs` 顯示 Swagger
- [x] 環境變數從 `.env` 正確讀取

### 1.2 建立前端 Vue 3 專案

使用 `create-vue` 建立 `frontend/`（Vue 3 + TypeScript + Vue Router + Pinia + Vite）。安裝 Element Plus、vue-echarts、echarts、axios、tailwindcss。設定 vite API proxy。

- [ ] `npm run dev` 正常啟動
- [ ] API proxy 轉發至後端正常

### 1.3 建立 Pydantic Models 與欄位對應

建立所有 Pydantic models：`WorkOrder`（含 computed_field: status/total_days/dev_days/test_days）、`Campaign`（含 CampaignSubitem、computed_field: is_template/material_completeness）、四大維度 KPI models（PersonWorkload、EfficiencyMetrics、GanttItem、QualityMetrics 等）。建立 `column_mapping.py`（工單總表含 developer/tester/closed_by 欄位、Campaign 含 content_type/review_status/completion_status）。

- [ ] WorkOrder.status 依日期自動判定流程階段
- [ ] Campaign.is_template 正確識別範本項目
- [ ] 兩個看板的 column ID 正確對應

---

## 任務 2：Monday.com API 串接服務

> 需求對應：1, 10

### 2.1 實作 GraphQL API 呼叫與分頁

在 `app/services/monday_api.py` 使用 httpx 非同步呼叫 Monday.com GraphQL API。實作 `fetch_board_items(board_id)` 含 cursor-based 分頁。工單總表不需查詢 subitems。Campaign 需查詢 subitems（文案/視覺）與 group 資訊。實作指數退避重試與 429 Rate Limit 處理。

- [ ] 取得工單總表全部 895 items（含 developer/tester/closed_by 欄位）
- [ ] 取得 Campaign 115 items 含 subitems 與 group.title
- [ ] 429/失敗時正確重試

### 2.2 實作使用者查詢與整合同步

新增 `fetch_users()` 取得使用者清單。建立 `sync_all()` 整合函式搭配 TTLCache（15 分鐘）。

- [ ] `sync_all()` 一次取得兩個看板 + 使用者資料
- [ ] 快取 15 分鐘內不重複呼叫 API

---

## 任務 3：資料解析器

> 需求對應：2

### 3.1 實作工單與行銷資料解析器

在 `app/services/parsers.py` 實作：
- `parse_work_order(item)`：工單總表 item → WorkOrder（包含 developer、tester、closed_by 人員欄位解析）
- `parse_campaign(item, subitems, group)`：Campaign item → Campaign（包含子項目分類統一化：Copywriting/文案/Copywrite → "copywriting"）
- 過濾行銷範本項目（is_template=True 的不納入績效）

- [ ] 工單解析含所有人員角色欄位
- [ ] 行銷解析含子項目與素材完備度
- [ ] 範本項目自動過濾

---

## 任務 4：維度 1 — 工作量計算引擎

> 需求對應：3

### 4.1 實作 PM+RD 工作量計算

在 `app/services/workload_engine.py` 實作：
- 每人在 PM/開發/測試三角色的工單計數
- 客戶工單分布、類型分布
- 在手未結案量（status != "已結案" 的工單中該人出現的數量）
- 時間篩選（依指派日期過濾）

- [ ] 人員工作量三角色拆分正確
- [ ] 在手未結案量正確反映當前狀態
- [ ] 時間篩選正確

### 4.2 實作行銷工作量計算

計算行銷工作量：內容產出量、平台分布、內容類型比例、跨平台發佈率（同一內容名稱出現在多個 group 的計數）、發佈頻率（篇/週）、排程前瞻量（completion_status=Scheduled 且 publish_date > today）。

- [ ] 平台分布依 group_name 統計
- [ ] 跨平台發佈率正確計算
- [ ] 排程前瞻量正確

---

## 任務 5：維度 2 — 流程效率計算引擎

> 需求對應：4

### 5.1 實作流程效率計算

在 `app/services/efficiency_engine.py` 實作：
- 端到端平均天數、開發階段耗時、測試階段耗時
- 依類型（開發/臭蟲/異動/盤查）分別計算各項時效
- 結案率
- 卡關識別（指派超過 7 天未進測試）
- 每週結案率趨勢
- 行銷效率：完成率、發佈穩定度（週標準差）

- [ ] 依類型的平均耗時差異可見（異動 <1天 vs 開發 >3天）
- [ ] 卡關工單清單正確標記
- [ ] 週趨勢 12 筆資料正確

---

## 任務 6：維度 3 — 專案排程引擎

> 需求對應：5

### 6.1 實作排程視圖資料

在 `app/services/schedule_engine.py` 實作：
- 甘特圖資料：每張工單的 assign_date → close_date 區間
- 人員×週 熱力圖：每人每週的工單數量
- 客戶×週 熱力圖：每客戶每週的工單數量
- 未結案老化表：按已開天數排序，綠(≤3天)/黃(4-7天)/紅(>7天)

- [ ] 甘特圖資料含進行中工單（end_date=None）
- [ ] 熱力圖週次對齊 ISO 週
- [ ] 老化表顏色標記正確

---

## 任務 7：維度 4 — 品質指標引擎

> 需求對應：6

### 7.1 實作品質間接指標

在 `app/services/quality_engine.py` 實作：
- Bug 回流率：同一客戶在時間區間內「臭蟲」類型工單的數量
- 異動密集度：每週「異動」佔比趨勢
- 行銷素材完備度：所有非範本 Campaign 的平均 material_completeness

- [ ] Bug 回流率按客戶統計正確
- [ ] 異動密集度趨勢可看出變化
- [ ] 素材完備度排除範本項目

---

## 任務 8：認證與授權

> 需求對應：12

### 8.1 實作後端認證與前端登入

後端：JWT 認證（python-jose），使用者帳號從環境變數讀取，`get_current_user` dependency 做角色檢查。
前端：LoginView.vue（Element Plus 表單）、auth store（Pinia）、Vue Router 導航守衛、axios interceptor。

- [ ] 登入成功回傳 JWT 並跳轉 /dashboard
- [ ] 無效 token 回傳 401 並跳轉登入頁
- [ ] member 角色存取他人資料回傳 403

---

## 任務 9：API Route 層

> 需求對應：3, 4, 5, 6, 10, 11

### 9.1 建立四大維度 API Routes

建立所有 API routes：
- `/api/workload/team` + `/api/workload/member/{name}`
- `/api/efficiency/overview` + `/api/efficiency/stalled` + `/api/efficiency/trends`
- `/api/schedule/gantt` + `/api/schedule/heatmap/person` + `/api/schedule/heatmap/client` + `/api/schedule/aging` + `/api/schedule/calendar`
- `/api/quality/overview` + `/api/quality/bug-recurrence`
- `/api/sync` + `/api/export/weekly` + `/api/export/monthly`

- [ ] 所有 API endpoint 回傳正確 JSON
- [ ] department/time 篩選參數正常運作
- [ ] Excel 匯出含老化表與效率摘要

---

## 任務 10：Excel 匯出服務

> 需求對應：11

### 10.1 實作週報與月報生成

在 `app/services/export_service.py` 使用 openpyxl 實作：
- 週報：Sheet 1 = 工作量 KPI 摘要、Sheet 2 = 流程效率摘要（分類型）、Sheet 3 = 未結案老化列表、Sheet 4 = 工單明細
- 月報：額外含 Sheet = 週趨勢比較

- [ ] 週報 4 sheets 內容正確
- [ ] 月報含趨勢比較
- [ ] 老化表含紅黃綠標記

---

## 任務 11：團隊總覽儀表板頁面

> 需求對應：7, 13

### 11.1 建立 Layout、導航與篩選器

建立 AppNavbar（含頁面 tabs：總覽/效率/排程/品質/行銷）、MemberSidebar、DepartmentFilter、DateRangeFilter。篩選器狀態存入 Pinia + localStorage。

- [ ] 頁面 tabs 切換正常
- [ ] 篩選器持久化生效

### 11.2 建立團隊總覽圖表與卡片

建立 KPISummaryCards（PM+RD: 總工單量/結案率/平均天數/未結案量；行銷: 產出量/完成率/頻率/前瞻量）、WorkloadBarChart（堆疊：PM/開發/測試）、TypePieChart、ClientPieChart、TrendLineChart（週工單量趨勢）。

- [ ] KPI 卡片依部門動態切換
- [ ] 堆疊長條圖正確顯示三角色
- [ ] 篩選器互動即時更新

---

## 任務 12：流程效率分析頁面

> 需求對應：9, 13

### 12.1 建立效率分析頁面

建立 EfficiencyView，整合：EfficiencyBarChart（各類型平均耗時）、StageStackChart（開發 vs 測試耗時）、結案率趨勢折線圖、StalledTable（卡關工單清單，紅色標記）。

- [ ] 各類型耗時差異清晰可見
- [ ] 卡關工單列表可點擊跳轉 Monday.com

---

## 任務 13：專案排程頁面

> 需求對應：5, 13

### 13.1 建立排程視圖頁面

建立 ScheduleView，整合：GanttChart（ECharts 甘特圖）、HeatmapChart（人員×週、客戶×週 切換）、AgingTable（未結案老化表，紅黃綠標記）。行銷區塊含 CalendarView（月曆式發佈排程）。

- [ ] 甘特圖含進行中工單（無結束線）
- [ ] 熱力圖深淺對應工單密度
- [ ] 老化表排序與顏色正確
- [ ] 行銷日曆顯示各平台內容

---

## 任務 14：品質分析與個人績效頁面

> 需求對應：6, 8, 13

### 14.1 建立品質分析頁面

建立 QualityView：Bug 回流率（各客戶的臭蟲工單數量排行）、異動密集度趨勢圖、行銷素材完備度指標。

- [ ] Bug 回流率按客戶排序
- [ ] 異動趨勢可看出上升/下降

### 14.2 建立個人績效頁面

建立 MemberView：個人 KPI 卡片（依角色動態）、12 週趨勢圖、工單明細表（含篩選/排序/Monday.com 連結）。行銷人員顯示平台分布與內容類型。

- [ ] PM+RD 顯示三角色工作量
- [ ] 行銷顯示平台分布與素材完備度
- [ ] 工單表格支援篩選排序

---

## 任務 15：端對端整合與驗證

> 需求對應：全部

### 15.1 端對端功能驗證

使用實際 Monday.com API 執行完整流程：登入 → 四個頁面切換 → 部門/時間篩選 → 個人績效 → 匯出報表 → 手動同步。驗證數據正確性。

- [ ] 四大維度頁面數據一致
- [ ] 篩選器跨頁面狀態保持
- [ ] Excel 匯出資料正確
- [ ] 權限控制正確
- [ ] 響應式佈局正確
