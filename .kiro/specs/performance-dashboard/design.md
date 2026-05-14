# performance-dashboard - 技術設計文件

> 更新時間：2026-05-14T11:00:00.000Z
> 版本：v3（基於實際資料盤查調整，四大評估維度）

---

## 1. 架構模式與邊界圖

### 1.1 整體架構

採用 **前後端分離架構**：Python FastAPI 後端提供 REST API，Vue 3 前端消費 API 並呈現 Dashboard。

```
┌──────────────────────────────────────────────────────────┐
│                      使用者瀏覽器                         │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Vue 3 SPA (Vite)                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐           │  │
│  │  │ 登入頁面  │ │ 團隊總覽  │ │ 個人績效  │           │  │
│  │  └──────────┘ └──────────┘ └──────────┘           │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │ 共用元件：篩選器、圖表、表格、匯出按鈕       │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────┬───────────────────────────┘  │
└───────────────────────────┼──────────────────────────────┘
                            │ HTTP REST API
                            ▼
┌───────────────────────────────────────────────────────────┐
│                   FastAPI Server                          │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              API Routes（路由層）                     │  │
│  │  /api/auth/*    /api/kpi/*    /api/sync   /api/export│  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │                                  │
│  ┌─────────────────────▼───────────────────────────────┐  │
│  │              Service Layer（服務層）                  │  │
│  │  ┌─────────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │ MondayAPI   │ │ KPI      │ │ Export           │  │  │
│  │  │ Service     │ │ Engine   │ │ Service          │  │  │
│  │  └──────┬──────┘ └──────────┘ └──────────────────┘  │  │
│  └─────────┼───────────────────────────────────────────┘  │
│            │                                              │
│  ┌─────────▼───────────────────────────────────────────┐  │
│  │              Data Layer（資料層）                     │  │
│  │  ┌──────────────┐  ┌─────────┐  ┌───────────────┐  │  │
│  │  │ Column       │  │ Models  │  │ Cache         │  │  │
│  │  │ Mapping      │  │ (Pydantic)│ │ (In-Memory)  │  │  │
│  │  └──────────────┘  └─────────┘  └───────────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────┬────────────────────────────────┘
                           │ GraphQL API
                           ▼
              ┌─────────────────────────┐
              │   Monday.com Platform   │
              │   api.monday.com/v2     │
              └─────────────────────────┘
```

### 1.2 資料流

```
Monday.com API ──GraphQL──► MondayAPIService ──parse──► Pydantic Models
                                                            │
                                                    ┌───────┴───────┐
                                                    ▼               ▼
                                              WorkOrder        Campaign
                                              (PM+RD)          (行銷)
                                                    │               │
                                                    └───────┬───────┘
                                                            ▼
                                                      KPI Engine
                                                    ┌─────────────┐
                                                    │ 按部門計算   │
                                                    │ 按人員彙總   │
                                                    │ 按時間篩選   │
                                                    └──────┬──────┘
                                                           │
                                       ┌───────────────────┼───────────────┐
                                       ▼                   ▼               ▼
                                 REST API JSON        Vue Dashboard    Excel 匯出
                                 /api/kpi/*           (ECharts)       (openpyxl)
```

---

## 2. 技術棧

| 類別 | 技術 | 版本 | 用途 | 需求對應 |
|------|------|------|------|---------|
| 後端框架 | FastAPI | 0.115+ | REST API + 自動文件（Swagger） | 全部 |
| 後端語言 | Python | 3.12+ | 業務邏輯 | 全部 |
| 資料驗證 | Pydantic | 2.x | 型別安全、API schema | 2, 3 |
| HTTP Client | httpx | 0.27+ | Monday.com GraphQL API（async） | 1 |
| 認證 | python-jose + passlib | - | JWT 生成/驗證 + 密碼 hash | 9 |
| Excel 匯出 | openpyxl | 3.x | server-side Excel 生成 | 8 |
| 快取 | cachetools | 5.x | TTL 記憶體快取（15 分鐘） | 7 |
| 前端框架 | Vue 3 | 3.5+ | Composition API + SPA | 全部 |
| 建置工具 | Vite | 6.x | 開發伺服器 + 打包 | 全部 |
| 路由 | Vue Router | 4.x | SPA 路由 | 5, 6 |
| 狀態管理 | Pinia | 2.x | 全域狀態（篩選器、使用者） | 4, 5, 6 |
| 圖表 | ECharts + vue-echarts | 5.x | 圖表視覺化 | 5, 6 |
| UI 框架 | Element Plus | 2.x | 元件庫（表格、按鈕、篩選器） | 全部 |
| HTTP Client | axios | 1.x | API 呼叫 | 全部 |
| CSS | Tailwind CSS | 4.x | 響應式佈局 | 10 |

---

## 3. 後端元件與介面契約

### 3.1 Pydantic Models（`app/models/`）

```python
# app/models/monday.py — Monday.com API 回應模型
# 對應需求 2.1, 2.2

class MondayColumnValue(BaseModel):
    id: str
    text: str | None
    value: str | None

class MondaySubitem(BaseModel):
    id: str
    name: str
    column_values: list[MondayColumnValue]

class MondayItem(BaseModel):
    id: str
    name: str
    column_values: list[MondayColumnValue]
    subitems: list[MondaySubitem] = []

class MondayUser(BaseModel):
    id: str
    name: str
    email: str
```

```python
# app/models/work_order.py — 結構化工單模型
# 對應需求 2.1（工單總表不使用子項目，扁平化管理）

class WorkOrder(BaseModel):
    id: str
    name: str
    client: str = "未指定"
    type: str = "未指定"          # 開發/臭蟲/異動/盤查
    pm: str = "未指定"
    developer: str = "未指定"     # 指派開發
    tester: str = "未指定"        # 指派測試
    test_completed_by: str = "未指定"  # 測試完成
    closed_by: str = "未指定"     # 結案
    assign_date: date | None = None
    test_assign_date: date | None = None
    test_complete_date: date | None = None
    close_date: date | None = None
    order_number: str = ""

    @computed_field
    def status(self) -> str:
        """依日期欄位判定流程階段"""
        if self.close_date: return "已結案"
        if self.test_assign_date: return "測試中"
        if self.assign_date: return "開發中"
        return "未指派"

    @computed_field
    def total_days(self) -> float | None:
        """端到端處理天數"""
        if self.assign_date and self.close_date:
            return (self.close_date - self.assign_date).days
        return None

    @computed_field
    def dev_days(self) -> float | None:
        """開發階段耗時"""
        if self.assign_date and self.test_assign_date:
            return (self.test_assign_date - self.assign_date).days
        return None

    @computed_field
    def test_days(self) -> float | None:
        """測試階段耗時"""
        if self.test_assign_date and self.close_date:
            return (self.close_date - self.test_assign_date).days
        return None
```

```python
# app/models/campaign.py — 行銷活動模型
# 對應需求 2.2, 2.3

class CampaignSubitem(BaseModel):
    id: str
    name: str           # "Copywriting" / "Visual" / "文案" / "視覺"
    status: str = "未指定"
    has_files: bool = False

    @computed_field
    def subitem_type(self) -> str:
        """統一子項目分類（處理命名不一致）"""
        name_lower = self.name.lower()
        if any(k in name_lower for k in ["copy", "文案"]): return "copywriting"
        if any(k in name_lower for k in ["visual", "視覺", "內容"]): return "visual"
        return "other"

class Campaign(BaseModel):
    id: str
    name: str
    owner: str = "未指定"
    content_type: str = "未指定"    # color_mm0dy0by: Holiday/Brand Positioning 等
    publish_date: date | None = None
    review_status: str = "未指定"   # color_mm0dtqem: Direct-Go/Approved
    completion_status: str = "未指定"  # color_mm0gy6kv: Completed/Scheduled/Paused
    platform: str = "未指定"        # platform_1
    has_ads: bool = False           # boolean_mm1397yf
    language: str = "未指定"
    group_name: str = "未指定"      # group.title（平台分類）
    subitems: list[CampaignSubitem] = []

    @computed_field
    def is_template(self) -> bool:
        """識別範本/規範項目（非實際發佈內容）"""
        return self.review_status == "Cancelled" and self.completion_status == "Paused"

    @computed_field
    def material_completeness(self) -> float:
        """素材完備度：文案+視覺都完成 = 100%"""
        if not self.subitems: return 0
        completed = sum(1 for s in self.subitems if s.status == "Done")
        return (completed / len(self.subitems)) * 100
```

```python
# app/models/kpi.py — 四大維度績效模型
# 對應需求 3, 4, 5, 6

# === 維度 1：工作量 ===
class PersonWorkload(BaseModel):
    user_name: str
    pm_count: int = 0           # 擔任 PM 的工單數
    dev_count: int = 0          # 擔任開發的工單數
    test_count: int = 0         # 擔任測試的工單數
    total_count: int = 0        # 合計
    in_progress_count: int = 0  # 在手未結案量

class MarketingWorkload(BaseModel):
    user_name: str
    content_count: int = 0
    platform_distribution: dict[str, int] = {}   # FB: 27, EDM: 24...
    content_type_distribution: dict[str, int] = {}  # Holiday: 21...
    cross_platform_count: int = 0  # 跨平台發佈數
    scheduled_count: int = 0    # 排程前瞻量
    posts_per_week: float = 0   # 發佈頻率

# === 維度 2：流程效率 ===
class EfficiencyMetrics(BaseModel):
    avg_total_days: float = 0       # 端到端平均天數
    avg_dev_days: float = 0         # 開發階段平均天數
    avg_test_days: float = 0        # 測試階段平均天數
    close_rate: float = 0           # 結案率 (0-100)
    stalled_rate: float = 0         # 卡關率 (>7天未進測試)
    stalled_orders: list[str] = []  # 卡關工單 ID 列表

class EfficiencyByType(BaseModel):
    type_name: str                  # 開發/臭蟲/異動/盤查
    count: int = 0
    avg_total_days: float = 0
    avg_dev_days: float = 0
    avg_test_days: float = 0
    close_rate: float = 0

class MarketingEfficiency(BaseModel):
    completion_rate: float = 0       # Completed 佔比
    weekly_std_dev: float = 0        # 每週發佈量標準差（穩定度）
    material_completeness: float = 0  # 素材完備度

# === 維度 3：專案排程 ===
class GanttItem(BaseModel):
    id: str
    name: str
    client: str
    developer: str
    start_date: date
    end_date: date | None          # None = 仍在進行中
    status: str

class HeatmapCell(BaseModel):
    label: str          # 人名 or 客戶名
    week: str           # "2026-W19"
    count: int

class AgingOrder(BaseModel):
    id: str
    name: str
    client: str
    developer: str
    assign_date: date
    days_open: int
    severity: str       # "green" ≤3 / "yellow" 4-7 / "red" >7

# === 維度 4：品質間接指標 ===
class QualityMetrics(BaseModel):
    bug_recurrence: dict[str, int] = {}   # 客戶 → 重複 Bug 數
    change_density: float = 0              # 異動佔比 (0-100)
    change_density_trend: list[float] = [] # 每週異動佔比趨勢

# === 彙總 ===
class TeamKPI(BaseModel):
    department: str
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    close_rate: float = 0
    avg_processing_days: float = 0
    member_workloads: list[PersonWorkload | MarketingWorkload] = []
    efficiency: EfficiencyMetrics | MarketingEfficiency | None = None
    efficiency_by_type: list[EfficiencyByType] = []
    quality: QualityMetrics | None = None
    type_distribution: dict[str, int] = {}
    client_distribution: dict[str, int] = {}

class WeeklyTrend(BaseModel):
    week_start: str
    week_end: str
    task_count: int = 0
    close_rate: float = 0
    avg_days: float = 0
    bug_count: int = 0
    change_count: int = 0

class DateRangeRequest(BaseModel):
    preset: str | None = None  # "this-week" | "this-month" | "last-month"
    start: date | None = None
    end: date | None = None
    department: str = "all"    # "all" | "pm_rd" | "marketing"
```

### 3.2 API Routes（`app/routers/`）

```
# 認證
POST   /api/auth/login              → { access_token, user }
GET    /api/auth/me                  → { user }

# 維度 1：工作量
GET    /api/workload/team            → TeamKPI（query: preset, start, end, department）
GET    /api/workload/member/{name}   → PersonWorkload + 工單明細

# 維度 2：流程效率
GET    /api/efficiency/overview      → EfficiencyMetrics + EfficiencyByType[]
GET    /api/efficiency/stalled       → AgingOrder[]（卡關工單清單）
GET    /api/efficiency/trends        → list[WeeklyTrend]

# 維度 3：專案排程
GET    /api/schedule/gantt           → list[GanttItem]
GET    /api/schedule/heatmap/person  → list[HeatmapCell]（人員×週）
GET    /api/schedule/heatmap/client  → list[HeatmapCell]（客戶×週）
GET    /api/schedule/aging           → list[AgingOrder]（未結案老化表）
GET    /api/schedule/calendar        → list[Campaign]（行銷日曆）

# 維度 4：品質
GET    /api/quality/overview         → QualityMetrics
GET    /api/quality/bug-recurrence   → dict[client, count]
GET    /api/quality/change-density   → trend data

# 通用
POST   /api/sync                     → { last_sync_time }
GET    /api/sync/status              → { last_sync_time }
GET    /api/export/weekly            → Excel file download
GET    /api/export/monthly           → Excel file download
GET    /api/users                    → 使用者清單
```

### 3.3 Service Layer（`app/services/`）

**MondayAPIService**（`monday_api.py`）
- `async fetch_board_items(board_id) -> list[MondayItem]`：cursor-based 分頁
- `async fetch_subitems(item_ids) -> dict[str, list[MondaySubitem]]`
- `async fetch_users() -> list[MondayUser]`
- `async sync_all() -> SyncResult`：整合同步

**WorkOrderParser**（`parsers.py`）
- `parse_work_order(item) -> WorkOrder`：解析工單總表 item（不含 subitems）
- `parse_campaign(item, subitems, group) -> Campaign`：解析行銷活動含子項目與群組

**WorkloadEngine**（`workload_engine.py`）— 維度 1
- `calculate_person_workload(orders, person_name, date_range) -> PersonWorkload`
- `calculate_marketing_workload(campaigns, person_name, date_range) -> MarketingWorkload`
- `calculate_team_workload(orders, date_range) -> TeamKPI`

**EfficiencyEngine**（`efficiency_engine.py`）— 維度 2
- `calculate_efficiency(orders, date_range) -> EfficiencyMetrics`
- `calculate_efficiency_by_type(orders, date_range) -> list[EfficiencyByType]`
- `find_stalled_orders(orders, threshold_days=7) -> list[AgingOrder]`
- `calculate_weekly_trends(orders, weeks=12) -> list[WeeklyTrend]`
- `calculate_marketing_efficiency(campaigns) -> MarketingEfficiency`

**ScheduleEngine**（`schedule_engine.py`）— 維度 3
- `generate_gantt(orders, date_range) -> list[GanttItem]`
- `generate_heatmap(orders, dimension, date_range) -> list[HeatmapCell]`
- `generate_aging_table(orders) -> list[AgingOrder]`

**QualityEngine**（`quality_engine.py`）— 維度 4
- `calculate_bug_recurrence(orders, date_range) -> dict[str, int]`
- `calculate_change_density(orders, weeks=12) -> QualityMetrics`
- `calculate_material_completeness(campaigns) -> float`

**ExportService**（`export_service.py`）
- `generate_weekly_report(team_kpi, items, date_range) -> bytes`
- `generate_monthly_report(trends, team_kpi, date_range) -> bytes`

**AuthService**（`auth_service.py`）
- `authenticate(email, password) -> User | None`
- `create_token(user) -> str`
- `verify_token(token) -> User`

### 3.4 Column Mapping Config（`app/config/column_mapping.py`）

```python
BOARDS = {
    "work_orders": {
        "board_id": "7960591450",
        "name": "工單總表",
        "department": "pm_rd",
        "columns": {
            "client": "dropdown_mkkzznt3",
            "type": "color_mkxfd8jn",
            "pm": "color_mkxfxqs2",
            "developer": "color_mkxfagvd",          # 指派開發
            "tester": "color_mkxfdhzv",              # 指派測試
            "test_completed_by": "color_mkxfk0mh",   # 測試完成
            "closed_by": "color_mkxfvdj3",           # 結案
            "assign_date": "date_mkxfdt3d",
            "test_assign_date": "date_mkxfjy8s",
            "test_complete_date": "date_mkxfyb3x",
            "close_date": "date_mkxfregq",
            "order_number": "pulse_id_mkxf8pt9",
        },
    },
    "campaigns": {
        "board_id": "18398984308",
        "name": "Campaign Planning & Status",
        "department": "marketing",
        "columns": {
            "owner": "person",
            "content_type": "color_mm0dy0by",         # 內容分類
            "publish_date": "date_mm0dmy4j",
            "review_status": "color_mm0dtqem",        # Direct-Go/Approved
            "completion_status": "color_mm0gy6kv",    # Completed/Scheduled/Paused
            "platform": "platform_1",
            "has_ads": "boolean_mm1397yf",
            "language": "color_mm0fa2jj",
        },
    },
}

# 行銷子項目欄位（文案/視覺）
CAMPAIGN_SUBITEM_COLUMNS = {
    "text_content": "text_mm0hrgjg",
    "status": "status",
    "files": "files",
}
```

### 3.5 Cache Strategy（`app/services/cache.py`）

```python
# TTLCache 15 分鐘，手動同步時清除
# 對應需求 7.1, 7.2

from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=900)  # 15 min

def get_cached(key: str) -> Any | None
def set_cached(key: str, value: Any) -> None
def clear_cache() -> None  # 手動同步用
```

---

## 4. 前端元件結構

### 4.1 路由規劃（Vue Router）

```
/login                          # 登入頁面
/dashboard                      # 團隊總覽（工作量儀表板）
/dashboard/efficiency           # 流程效率分析
/dashboard/schedule             # 專案排程視圖
/dashboard/quality              # 品質指標
/dashboard/member/:name         # 個人績效頁面
/dashboard/marketing            # 行銷績效（日曆+產出量）
```

### 4.2 前端元件結構

```
src/
├── views/
│   ├── LoginView.vue              # /login
│   ├── DashboardView.vue          # /dashboard（團隊總覽）
│   ├── EfficiencyView.vue         # /dashboard/efficiency
│   ├── ScheduleView.vue           # /dashboard/schedule
│   ├── QualityView.vue            # /dashboard/quality
│   ├── MemberView.vue             # /dashboard/member/:name
│   └── MarketingView.vue          # /dashboard/marketing
├── components/
│   ├── layout/
│   │   ├── AppNavbar.vue          # 導航列（含頁面切換 tabs）
│   │   └── MemberSidebar.vue      # 成員列表側邊欄
│   ├── filters/
│   │   ├── DateRangeFilter.vue    # 時間篩選器
│   │   └── DepartmentFilter.vue   # 部門篩選器
│   ├── charts/
│   │   ├── WorkloadBarChart.vue   # 成員工作量堆疊長條圖（PM/開發/測試）
│   │   ├── TypePieChart.vue       # 工單類型分布圓餅圖
│   │   ├── ClientPieChart.vue     # 客戶分布圓餅圖
│   │   ├── TrendLineChart.vue     # 趨勢折線圖（通用）
│   │   ├── EfficiencyBarChart.vue # 各類型平均耗時長條圖
│   │   ├── StageStackChart.vue    # 開發 vs 測試階段耗時堆疊圖
│   │   ├── GanttChart.vue         # 工單甘特圖（時間軸）
│   │   ├── HeatmapChart.vue       # 人員/客戶×週 熱力圖
│   │   ├── CalendarView.vue       # 行銷發佈日曆
│   │   └── PlatformPieChart.vue   # 行銷平台分布圓餅圖
│   ├── cards/
│   │   └── KPISummaryCards.vue    # KPI 摘要卡片（依部門動態）
│   ├── tables/
│   │   ├── WorkOrderTable.vue     # 工單明細表格
│   │   ├── AgingTable.vue         # 未結案工單老化表（紅黃綠）
│   │   └── StalledTable.vue       # 卡關工單清單
│   └── common/
│       ├── SyncStatusBar.vue      # 同步狀態列
│       └── ExportButtons.vue      # 匯出按鈕組
├── stores/
│   ├── auth.ts                    # 認證狀態（Pinia）
│   ├── filters.ts                 # 篩選器狀態（持久化）
│   └── data.ts                    # API 資料快取
├── api/
│   └── index.ts                   # axios instance + API 呼叫函式
└── router/
    └── index.ts                   # 路由定義 + 導航守衛
```

### 4.2 狀態管理（Pinia Stores）

```typescript
// stores/filters.ts — 篩選器狀態
// 對應需求 4.5（記住選擇）

interface FiltersState {
  department: 'all' | 'pm_rd' | 'marketing'
  preset: 'this-week' | 'this-month' | 'last-month' | 'custom'
  customStart: string | null
  customEnd: string | null
}
// 使用 localStorage plugin 持久化
```

---

## 5. 認證設計

**對應需求**：9.1, 9.2, 9.3, 9.4

```
Login (Vue) ──POST /api/auth/login──► FastAPI ──驗證──► JWT Token
                                                          │
Vue localStorage ◄── { access_token, user } ◄─────────────┘

每次 API 請求 ──Authorization: Bearer {token}──► FastAPI Depends(get_current_user)
                                                          │
                                                    ┌─────┴─────┐
                                                    │ 解碼 JWT  │
                                                    │ 驗證角色  │
                                                    └───────────┘
```

- 使用者帳號存於 `users.json` 或環境變數
- JWT token 含 `user_id`, `email`, `role`, `monday_user_id`
- Vue Router 導航守衛：無 token 跳轉 `/login`
- API 端：`Depends(get_current_user)` 驗證 + 角色檢查

---

## 6. 專案目錄結構

```
performancePlatform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config/
│   │   │   ├── settings.py      # 環境變數設定
│   │   │   └── column_mapping.py
│   │   ├── models/
│   │   │   ├── monday.py
│   │   │   ├── work_order.py
│   │   │   ├── campaign.py
│   │   │   ├── kpi.py
│   │   │   └── auth.py
│   │   ├── services/
│   │   │   ├── monday_api.py
│   │   │   ├── parsers.py
│   │   │   ├── kpi_engine.py
│   │   │   ├── export_service.py
│   │   │   ├── auth_service.py
│   │   │   └── cache.py
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── kpi.py
│   │       ├── sync.py
│   │       └── export.py
│   ├── requirements.txt
│   ├── .env
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   ├── components/
│   │   ├── stores/
│   │   ├── api/
│   │   ├── router/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
└── docker-compose.yml
```

---

## 7. 需求追溯矩陣

| 需求 | 後端元件 | 前端元件 |
|------|---------|---------|
| 1. Monday.com 資料串接 | MondayAPIService, column_mapping | - |
| 2. 工單欄位解析 | parsers.py, WorkOrder/Campaign Models | - |
| 3. 工作量指標 | workload_engine.py, /api/workload/* | DashboardView, WorkloadBarChart, TypePie, ClientPie |
| 4. 流程效率指標 | efficiency_engine.py, /api/efficiency/* | EfficiencyView, EfficiencyBarChart, StageStackChart, StalledTable |
| 5. 專案排程視圖 | schedule_engine.py, /api/schedule/* | ScheduleView, GanttChart, HeatmapChart, AgingTable, CalendarView |
| 6. 品質間接指標 | quality_engine.py, /api/quality/* | QualityView, TrendLineChart |
| 7. 團隊總覽儀表板 | /api/workload/team | DashboardView, KPISummaryCards, 篩選器 |
| 8. 個人績效頁面 | /api/workload/member/{name} | MemberView, WorkOrderTable |
| 9. 流程效率儀表板 | /api/efficiency/overview | EfficiencyView |
| 10. 資料同步與快取 | cache.py, /api/sync | SyncStatusBar |
| 11. 週報/月報匯出 | export_service.py, /api/export | ExportButtons |
| 12. 權限與認證 | auth_service.py, JWT middleware | LoginView, auth store, router guard |
| 13. 響應式設計 | - | Tailwind + Element Plus responsive |
