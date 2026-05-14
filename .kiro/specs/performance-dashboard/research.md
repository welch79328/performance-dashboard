# performance-dashboard - 研究記錄

> 更新時間：2026-05-13T19:10:00.000Z

## 摘要

本次研究為全面探索型（Full Discovery），涵蓋 Monday.com API 分頁機制、Next.js 15 ISR 策略、Auth.js v5 角色存取控制、Recharts 圖表庫整合、以及 Excel 匯出方案。

---

## 研究記錄

### 主題 1：Monday.com GraphQL API 分頁機制

**來源**：[Monday.com 官方文件 - Items Page](https://developer.monday.com/api-reference/reference/items-page)、[分頁變更日誌](https://developer.monday.com/api-reference/changelog/new-next_items_page-object-for-cursor-based-pagination)

**發現**：
- 使用 cursor-based pagination，`items_page` 每次最多回傳 500 items
- 首次查詢使用 `items_page(limit: 500)`，後續使用 `next_items_page(cursor: "...")`
- Cursor 有效期為 60 分鐘
- 支援多 board 同時查詢但分頁需個別處理

**影響**：
- API 串接層需實作 cursor 迴圈，逐頁取得所有工單
- 需考慮 cursor 過期問題（大量資料同步時可能超過 60 分鐘）
- 子項目（subitems）需另外查詢，無法在 items_page 中一次取得

---

### 主題 2：Next.js 15 ISR 與 Revalidation

**來源**：[Next.js 官方 ISR 指南](https://nextjs.org/docs/app/guides/incremental-static-regeneration)、[revalidatePath 文件](https://nextjs.org/docs/app/api-reference/functions/revalidatePath)

**發現**：
- App Router 中使用 `export const revalidate = 900`（15 分鐘）設定 ISR
- 支援 `revalidatePath()` 和 `revalidateTag()` 做 on-demand revalidation
- Stale-while-revalidate 模式：先返回快取資料，背景重新生成
- Route Handler 可作為 BFF（Backend-for-Frontend）層

**影響**：
- 績效資料以 ISR 15 分鐘自動更新，「立即同步」按鈕觸發 `revalidatePath`
- Route Handler 集中處理 Monday.com API 呼叫與資料轉換
- Server Components 用於初始資料載入，Client Components 用於互動圖表

---

### 主題 3：Auth.js v5 角色存取控制

**來源**：[Auth.js RBAC 指南](https://authjs.dev/guides/role-based-access-control)、[Next.js RBAC with Auth.js v5](https://nextjslaunchpad.com/article/nextjs-role-based-access-control-authjs-v5-middleware-server-component-authorization)

**發現**：
- Credentials Provider + JWT 策略適合小型團隊（無需外部 OAuth）
- 角色透過 `jwt()` callback 寫入 token，再透過 `session()` callback 暴露給 client
- 需拆分 `auth.config.ts`（edge 相容，middleware 用）與 `auth.ts`（完整設定）
- Middleware 提供路由級保護，Server Action 提供操作級保護

**影響**：
- 13 人小團隊，使用 Credentials Provider + 環境變數管理帳號即可
- Middleware 攔截未認證請求，重導至登入頁
- JWT token 包含 role 欄位（admin / member），用於前後端權限判斷

---

### 主題 4：Recharts 圖表庫

**來源**：[Recharts 官方](https://github.com/recharts/recharts)、[Next.js Recharts 整合指南](https://app-generator.dev/docs/technologies/nextjs/integrate-recharts.html)

**發現**：
- 必須使用 `"use client"` 指令，因內部依賴 D3.js 操作 DOM
- 每週 360 萬+ 下載量，生態穩定
- 宣告式 API，與 React 元件模式一致
- 大量資料點（>1000）時 SVG 效能可能下降

**影響**：
- 所有圖表元件需標記為 Client Component
- 13 人團隊 × 12 週 = ~156 資料點，效能無虞
- 支援 BarChart、PieChart、LineChart、ResponsiveContainer 滿足所有需求

---

### 主題 5：Excel 匯出方案

**來源**：[SheetJS 官方文件](https://docs.sheetjs.com/docs/demos/static/nextjs/)、[Next.js Route Handler 下載 XLSX](https://www.davegray.codes/posts/how-to-download-xlsx-files-from-a-nextjs-route-handler)

**發現**：
- SheetJS（xlsx 套件）是最主流的 JavaScript Excel 處理庫
- 可在 Next.js Route Handler 中 server-side 生成 Excel buffer
- 回傳 Response 時設定 `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- 支援多 sheet、格式化、公式

**影響**：
- 匯出 API route 在 server 端產生 Excel，避免 client 端記憶體壓力
- 週報/月報各自建立不同的 worksheet
- 大量資料時可搭配 streaming 方式處理

---

## 架構決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| 前端框架 | Next.js 15 (App Router) | SSR/ISR 支援、Route Handler 作為 BFF、Server Components |
| 圖表庫 | Recharts | 宣告式 API、React 原生整合、資料量級適合 |
| 認證方案 | Auth.js v5 (Credentials) | 小團隊不需 OAuth、JWT 策略輕量 |
| Excel 匯出 | SheetJS (xlsx) | 最穩定、支援 server-side 生成 |
| CSS 框架 | Tailwind CSS | 快速開發、響應式設計原生支援 |
| 資料快取 | Next.js ISR + revalidatePath | 時間型 + 手動型雙重策略 |

## 風險

| 風險 | 等級 | 緩解策略 |
|------|------|---------|
| Monday.com API Rate Limit | 中 | ISR 快取減少 API 呼叫、指數退避重試 |
| Cursor 過期（60 分鐘） | 低 | 資料量小（~100 工單），同步可在數秒內完成 |
| 欄位 ID 變更 | 中 | Column ID 集中管理於設定檔，方便維護 |
