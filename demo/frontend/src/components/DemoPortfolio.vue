<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Check,
  ChevronRight,
  Pencil,
  Plus,
  Trash2,
  WalletCards,
  X,
} from '@lucide/vue'

type HoldingType = 'fund' | 'stock'
type Holding = {
  id: string
  type: HoldingType
  name: string
  code: string
  market: string
  currentValue: number
  todayProfit: number
  totalProfit: number
  weekPercent: number
  monthPercent: number
  series: number[]
}
type HoldingDraft = Pick<Holding, 'type' | 'name' | 'code' | 'market'> & { currentValue: string }

const STORAGE_KEY = 'presight-public-demo-holdings-v1'
const seedHoldings: Holding[] = [
  { id: 'fund-demo-1', type: 'fund', name: '示例基金 · 均衡组合', code: 'DEMO01', market: '混合型', currentValue: 12580.4, todayProfit: 86.5, totalProfit: 630.2, weekPercent: 1.24, monthPercent: 3.8, series: [16, 18, 17, 23, 22, 28, 26, 34, 37, 35, 43, 48] },
  { id: 'fund-demo-2', type: 'fund', name: '示例基金 · 宽基指数', code: 'DEMO02', market: '指数型', currentValue: 8760.2, todayProfit: -22.1, totalProfit: -120.8, weekPercent: -0.34, monthPercent: 1.1, series: [48, 45, 47, 42, 45, 38, 41, 36, 39, 33, 34, 31] },
  { id: 'stock-demo-1', type: 'stock', name: '示例新能源', code: 'DEMO-SZ-300750', market: '创业板 · 电池', currentValue: 8200, todayProfit: 132.4, totalProfit: -380, weekPercent: 2.08, monthPercent: -4.6, series: [18, 21, 20, 27, 24, 34, 32, 42, 47, 58] },
  { id: 'stock-demo-2', type: 'stock', name: '示例银行', code: 'DEMO-SH-601398', market: '沪市主板 · 银行', currentValue: 4380.6, todayProfit: 21.8, totalProfit: 218.6, weekPercent: 0.72, monthPercent: 2.3, series: [28, 31, 29, 34, 33, 38, 36, 42, 40, 45] },
]

const holdings = ref<Holding[]>(seedHoldings.map((item) => ({ ...item, series: [...item.series] })))
const activeType = ref<HoldingType>('fund')
const selectedId = ref('fund-demo-1')
const editorOpen = ref(false)
const deleteId = ref('')
const error = ref('')
const notice = ref('')
const editingId = ref('')
const draft = ref<HoldingDraft>(emptyDraft('fund'))

const visibleHoldings = computed(() => holdings.value.filter((item) => item.type === activeType.value))
const activeHolding = computed(() => visibleHoldings.value.find((item) => item.id === selectedId.value) ?? visibleHoldings.value[0] ?? null)
const totalValue = computed(() => visibleHoldings.value.reduce((sum, item) => sum + item.currentValue, 0))
const todayTotal = computed(() => visibleHoldings.value.reduce((sum, item) => sum + item.todayProfit, 0))
const cumulativeTotal = computed(() => visibleHoldings.value.reduce((sum, item) => sum + item.totalProfit, 0))
const typeName = computed(() => activeType.value === 'fund' ? '基金' : '股票')
const pendingDelete = computed(() => holdings.value.find((item) => item.id === deleteId.value) ?? null)

function emptyDraft(type: HoldingType): HoldingDraft {
  return { type, name: '', code: '', market: type === 'fund' ? '基金' : 'A 股', currentValue: '' }
}

function currency(value: number) {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY', maximumFractionDigits: 2 }).format(value)
}

function signedCurrency(value: number) {
  return (value > 0 ? '+' : value < 0 ? '−' : '') + currency(Math.abs(value))
}

function percent(value: number) {
  return (value > 0 ? '+' : '') + value.toFixed(2) + '%'
}

function changeClass(value: number) {
  return value < 0 ? 'portfolio-down' : value > 0 ? 'portfolio-up' : 'portfolio-flat'
}

function linePoints(values: number[]) {
  const max = Math.max(...values)
  const min = Math.min(...values)
  const range = max - min || 1
  return values.map((value, index) => {
    const x = (index / Math.max(values.length - 1, 1)) * 100
    const y = 34 - ((value - min) / range) * 28
    return x + ',' + y
  }).join(' ')
}

function openEditor(item?: Holding) {
  error.value = ''
  notice.value = ''
  editingId.value = item?.id ?? ''
  draft.value = item
    ? { type: item.type, name: item.name, code: item.code, market: item.market, currentValue: String(item.currentValue) }
    : emptyDraft(activeType.value)
  editorOpen.value = true
}

function saveHolding() {
  const name = draft.value.name.trim()
  const code = draft.value.code.trim().toUpperCase()
  const amount = Number(draft.value.currentValue)
  if (!name || !code || !Number.isFinite(amount) || amount < 0) {
    error.value = '请填写名称、代码和不小于 0 的持有金额。'
    return
  }
  if (holdings.value.some((item) => item.code === code && item.id !== editingId.value)) {
    error.value = '这个演示代码已经在持仓列表中。'
    return
  }
  const old = holdings.value.find((item) => item.id === editingId.value)
  const updated: Holding = {
    id: old?.id ?? 'demo-' + Date.now(),
    type: draft.value.type,
    name,
    code,
    market: draft.value.market.trim() || (draft.value.type === 'fund' ? '基金' : 'A 股'),
    currentValue: amount,
    todayProfit: old?.todayProfit ?? 0,
    totalProfit: old?.totalProfit ?? 0,
    weekPercent: old?.weekPercent ?? 0,
    monthPercent: old?.monthPercent ?? 0,
    series: old?.series ?? [18, 21, 20, 24, 23, 27, 28, 31, 29, 34],
  }
  holdings.value = old
    ? holdings.value.map((item) => item.id === old.id ? updated : item)
    : [updated, ...holdings.value]
  activeType.value = updated.type
  selectedId.value = updated.id
  editorOpen.value = false
  notice.value = old ? '持仓示例已更新。' : '持仓示例已添加。'
}

function confirmDelete() {
  if (!pendingDelete.value) return
  const removed = pendingDelete.value
  holdings.value = holdings.value.filter((item) => item.id !== removed.id)
  if (selectedId.value === removed.id) selectedId.value = holdings.value.find((item) => item.type === activeType.value)?.id ?? ''
  deleteId.value = ''
  notice.value = removed.name + ' 已从本机演示持仓中移除。'
}

onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved) as Holding[]
      if (Array.isArray(parsed)) holdings.value = parsed
    }
  } catch {
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      // Some browsers block storage in private or restricted contexts.
    }
  }
})

watch(holdings, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
  } catch {
    notice.value = '浏览器暂时无法保存本地演示数据。'
  }
}, { deep: true })
</script>

<template>
  <div class="demo-portfolio">
    <section class="intro-row portfolio-intro">
      <div>
        <p class="eyebrow">持仓管理 · 本机示例</p>
        <h2>我的持仓</h2>
        <p class="intro-copy">添加、查看和编辑基金或股票示例。修改仅保存在当前浏览器，不会连接账户或交易服务。</p>
      </div>
      <button class="button button-primary portfolio-add" @click="openEditor()"><Plus :size="16" /> 添加{{ typeName }}持仓</button>
    </section>

    <section class="portfolio-summary" aria-label="持仓概览">
      <article class="portfolio-summary-card"><span>持有金额</span><WalletCards :size="17" /><strong>{{ currency(totalValue) }}</strong></article>
      <article class="portfolio-summary-card"><span>今日盈亏</span><component :is="todayTotal < 0 ? ArrowDownRight : ArrowUpRight" :size="17" :class="changeClass(todayTotal)" /><strong :class="changeClass(todayTotal)">{{ signedCurrency(todayTotal) }}</strong></article>
      <article class="portfolio-summary-card"><span>累计盈亏</span><component :is="cumulativeTotal < 0 ? ArrowDownRight : ArrowUpRight" :size="17" :class="changeClass(cumulativeTotal)" /><strong :class="changeClass(cumulativeTotal)">{{ signedCurrency(cumulativeTotal) }}</strong></article>
    </section>

    <section class="portfolio-list-card">
      <div class="portfolio-toolbar">
        <div class="portfolio-tabs" role="tablist" aria-label="选择持仓类型">
          <button :class="{ active: activeType === 'fund' }" role="tab" :aria-selected="activeType === 'fund'" @click="activeType = 'fund'; selectedId = visibleHoldings[0]?.id ?? ''">基金持仓</button>
          <button :class="{ active: activeType === 'stock' }" role="tab" :aria-selected="activeType === 'stock'" @click="activeType = 'stock'; selectedId = visibleHoldings[0]?.id ?? ''">股票持仓</button>
        </div>
        <span class="portfolio-snapshot">示例数据 · 2026-10-16 收盘</span>
      </div>
      <div v-if="visibleHoldings.length" class="portfolio-holdings">
        <div class="portfolio-table-head"><span>{{ typeName }}名称</span><span>持有金额</span><span>今日盈亏</span><span>累计盈亏</span><span>操作</span></div>
        <article v-for="item in visibleHoldings" :key="item.id" :class="['portfolio-holding-row', { selected: activeHolding?.id === item.id }]">
          <button class="holding-main" @click="selectedId = item.id">
            <span class="holding-icon"><WalletCards v-if="item.type === 'fund'" :size="17" /><Activity v-else :size="17" /></span>
            <span class="holding-identity"><b>{{ item.name }}</b><small>{{ item.code }} · {{ item.market }}</small></span><ChevronRight class="holding-chevron" :size="15" />
          </button>
          <span class="holding-value">{{ currency(item.currentValue) }}</span>
          <span :class="['holding-profit', changeClass(item.todayProfit)]">{{ signedCurrency(item.todayProfit) }}</span>
          <span :class="['holding-profit', changeClass(item.totalProfit)]">{{ signedCurrency(item.totalProfit) }}</span>
          <span class="holding-actions">
            <button class="icon-button" :aria-label="'编辑' + item.name" title="编辑" @click="openEditor(item)"><Pencil :size="15" /></button>
            <button class="icon-button danger-action" :aria-label="'删除' + item.name" title="删除" @click="deleteId = item.id"><Trash2 :size="15" /></button>
          </span>
        </article>
      </div>
      <div v-else class="portfolio-empty"><WalletCards :size="22" /><b>还没有{{ typeName }}持仓</b><span>添加一条示例记录，体验持仓页面的查看与编辑流程。</span><button class="button button-light" @click="openEditor()">添加{{ typeName }}持仓</button></div>
    </section>

    <section v-if="activeHolding" class="holding-detail-card">
      <div class="holding-detail-heading">
        <div><p class="eyebrow">{{ activeHolding.type === 'fund' ? '基金持仓详情' : '股票持仓详情' }}</p><h3>{{ activeHolding.name }}</h3><span>{{ activeHolding.code }} · {{ activeHolding.market }}</span></div>
        <button class="button button-light detail-edit" @click="openEditor(activeHolding)"><Pencil :size="14" /> 编辑持仓</button>
      </div>
      <div class="holding-detail-grid">
        <div class="holding-chart">
          <div class="holding-chart-title"><span>示例走势</span><small>固定快照，不代表实时价格</small></div>
          <svg viewBox="0 0 100 40" preserveAspectRatio="none" role="img" :aria-label="activeHolding.name + '示例走势'"><polyline :points="linePoints(activeHolding.series)" /></svg>
          <div class="chart-axis"><span>10/12</span><span>10/14</span><span>10/16</span></div>
        </div>
        <div class="holding-periods">
          <div><span>持有金额</span><b>{{ currency(activeHolding.currentValue) }}</b></div>
          <div><span>今日盈亏</span><b :class="changeClass(activeHolding.todayProfit)">{{ signedCurrency(activeHolding.todayProfit) }}</b></div>
          <div><span>本周涨幅</span><b :class="changeClass(activeHolding.weekPercent)">{{ percent(activeHolding.weekPercent) }}</b></div>
          <div><span>本月涨幅</span><b :class="changeClass(activeHolding.monthPercent)">{{ percent(activeHolding.monthPercent) }}</b></div>
        </div>
      </div>
    </section>
    <p v-if="notice" class="portfolio-notice" role="status"><Check :size="15" />{{ notice }}</p>

    <div v-if="editorOpen" class="portfolio-modal-backdrop" @click.self="editorOpen = false" @keydown.esc="editorOpen = false">
      <section class="portfolio-modal" role="dialog" aria-modal="true" aria-labelledby="holding-modal-title">
        <header><div><p class="eyebrow">本机演示数据</p><h3 id="holding-modal-title">{{ editingId ? '编辑持仓' : '添加持仓' }}</h3></div><button class="icon-button" aria-label="关闭" @click="editorOpen = false"><X :size="18" /></button></header>
        <form @submit.prevent="saveHolding">
          <label class="holding-field">类型<select v-model="draft.type"><option value="fund">基金</option><option value="stock">股票</option></select></label>
          <label class="holding-field">名称<input v-model="draft.name" required maxlength="60" autocomplete="off" placeholder="例如：示例基金 · 均衡组合" /></label>
          <label class="holding-field">代码<input v-model="draft.code" required maxlength="24" autocomplete="off" placeholder="例如：DEMO01" /></label>
          <label class="holding-field">分类<input v-model="draft.market" maxlength="40" placeholder="例如：混合型 / 沪市主板" /></label>
          <label class="holding-field">持有金额（元）<input v-model="draft.currentValue" type="number" inputmode="decimal" min="0" step="0.01" required placeholder="0.00" /></label>
          <p v-if="error" class="portfolio-form-error" role="alert">{{ error }}</p>
          <div class="portfolio-modal-actions"><button type="button" class="button button-light" @click="editorOpen = false">取消</button><button type="submit" class="button button-primary"><Check :size="15" /> 保存</button></div>
        </form>
      </section>
    </div>

    <div v-if="pendingDelete" class="portfolio-modal-backdrop" @click.self="deleteId = ''" @keydown.esc="deleteId = ''">
      <section class="portfolio-modal delete-modal" role="alertdialog" aria-modal="true" aria-labelledby="delete-modal-title" aria-describedby="delete-modal-copy">
        <header><div><p class="eyebrow">确认操作</p><h3 id="delete-modal-title">移除这条持仓？</h3></div><button class="icon-button" aria-label="关闭" @click="deleteId = ''"><X :size="18" /></button></header>
        <p id="delete-modal-copy">“{{ pendingDelete.name }}”只会从当前浏览器的演示数据中移除。</p>
        <div class="portfolio-modal-actions"><button class="button button-light" @click="deleteId = ''">取消</button><button class="button button-danger" @click="confirmDelete"><Trash2 :size="15" /> 移除</button></div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.demo-portfolio { display: grid; gap: 16px; }
.portfolio-intro { margin-bottom: 0; align-items: center; }
.portfolio-add { min-height: 42px; }
.portfolio-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 11px; }
.portfolio-summary-card { position: relative; display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 10px; min-width: 0; padding: 16px 17px; background: #fff; border: 1px solid var(--line); border-radius: 15px; box-shadow: var(--shadow); }
.portfolio-summary-card > span { color: #77839e; font-size: 11px; font-weight: 700; }
.portfolio-summary-card > svg { color: #7883fa; }
.portfolio-summary-card strong { grid-column: 1 / -1; color: var(--ink); font-size: clamp(17px, 2vw, 22px); font-variant-numeric: tabular-nums; letter-spacing: -.035em; }
.portfolio-summary-card strong.portfolio-up, .holding-periods .portfolio-up { color: var(--red); }
.portfolio-summary-card strong.portfolio-down, .holding-periods .portfolio-down { color: var(--green); }
.portfolio-up { color: var(--red); }
.portfolio-down { color: var(--green); }
.portfolio-flat { color: #687590; }
.portfolio-list-card, .holding-detail-card { overflow: hidden; background: #fff; border: 1px solid var(--line); border-radius: 17px; box-shadow: var(--shadow); }
.portfolio-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 16px; border-bottom: 1px solid #f0f2f7; }
.portfolio-tabs { display: inline-flex; gap: 4px; padding: 4px; background: #f4f6fb; border-radius: 11px; }
.portfolio-tabs button { min-height: 36px; padding: 0 13px; color: #73809a; background: transparent; border: 0; border-radius: 8px; cursor: pointer; font-size: 11px; font-weight: 750; }
.portfolio-tabs button.active { color: var(--blue); background: #fff; box-shadow: 0 2px 8px rgb(45 63 119 / 8%); }
.portfolio-snapshot { color: #8a95aa; font-size: 10px; }
.portfolio-table-head, .portfolio-holding-row { display: grid; grid-template-columns: minmax(220px, 1.6fr) minmax(100px, 1fr) minmax(100px, 1fr) minmax(100px, 1fr) 78px; align-items: center; gap: 12px; }
.portfolio-table-head { padding: 11px 16px; color: #8792a8; background: #fafbfe; font-size: 10px; font-weight: 700; }
.portfolio-holding-row { min-height: 69px; padding: 9px 16px; border-top: 1px solid #f0f2f7; transition: background .18s; }
.portfolio-holding-row.selected { background: #f7f8ff; }
.holding-main { display: flex; align-items: center; gap: 10px; min-width: 0; padding: 0; color: inherit; background: transparent; border: 0; cursor: pointer; text-align: left; }
.holding-icon { display: grid; width: 34px; height: 34px; flex: 0 0 auto; place-items: center; color: var(--blue); background: #f0f1ff; border-radius: 10px; }
.holding-identity { display: grid; min-width: 0; gap: 4px; }
.holding-identity b, .holding-identity small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.holding-identity b { font-size: 11px; }
.holding-identity small { color: #8a95aa; font-size: 9px; }
.holding-chevron { display: none; margin-left: auto; color: #a3acc0; }
.holding-value, .holding-profit { font-size: 11px; font-weight: 750; font-variant-numeric: tabular-nums; white-space: nowrap; }
.holding-actions { display: flex; justify-content: flex-end; gap: 2px; }
.holding-actions .icon-button { width: 34px; height: 34px; }
.danger-action:hover { color: #d84e57; background: #fff0f0; }
.portfolio-empty { display: grid; justify-items: center; gap: 8px; padding: 30px 16px; color: #8792a8; text-align: center; }
.portfolio-empty > svg { color: #7b84f4; }
.portfolio-empty b { color: var(--ink); font-size: 13px; }
.portfolio-empty span { font-size: 11px; line-height: 1.6; }
.portfolio-empty .button { margin-top: 5px; }
.holding-detail-card { padding: 17px; }
.holding-detail-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-bottom: 14px; border-bottom: 1px solid #f0f2f7; }
.holding-detail-heading .eyebrow { margin: 0 0 5px; color: var(--blue); }
.holding-detail-heading h3 { margin: 0; font-size: 15px; }
.holding-detail-heading span { display: inline-block; margin-top: 5px; color: #8792a8; font-size: 10px; }
.detail-edit { min-height: 38px; }
.holding-detail-grid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(220px, 1fr); gap: 18px; padding-top: 16px; }
.holding-chart { min-width: 0; padding: 13px; background: #fafbff; border: 1px solid #edf0f7; border-radius: 13px; }
.holding-chart-title { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
.holding-chart-title span { color: #586581; font-size: 11px; font-weight: 750; }
.holding-chart-title small { color: #929cb0; font-size: 9px; }
.holding-chart svg { display: block; width: 100%; height: 110px; overflow: visible; }
.holding-chart polyline { fill: none; stroke: #6672f6; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.8; vector-effect: non-scaling-stroke; }
.chart-axis { display: flex; justify-content: space-between; margin-top: 4px; color: #9aa4b7; font-size: 9px; }
.holding-periods { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
.holding-periods > div { display: grid; align-content: center; gap: 7px; min-width: 0; padding: 12px; background: #fafbfe; border: 1px solid #eef0f6; border-radius: 12px; }
.holding-periods span { color: #8792a8; font-size: 10px; }
.holding-periods b { overflow: hidden; color: var(--ink); font-size: 12px; font-variant-numeric: tabular-nums; text-overflow: ellipsis; white-space: nowrap; }
.portfolio-notice { display: inline-flex; align-items: center; gap: 7px; width: fit-content; margin: 0; padding: 9px 12px; color: #247a65; background: #effaf6; border: 1px solid #d7f0e7; border-radius: 10px; font-size: 11px; }
.portfolio-modal-backdrop { position: fixed; z-index: 30; inset: 0; display: grid; place-items: center; padding: 18px; background: rgb(19 30 55 / 42%); }
.portfolio-modal { width: min(100%, 430px); max-height: min(90dvh, 720px); overflow: auto; padding: 20px; background: #fff; border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 24px 70px rgb(15 26 52 / 24%); }
.portfolio-modal header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 17px; }
.portfolio-modal header .eyebrow { margin: 0 0 4px; color: var(--blue); }
.portfolio-modal h3 { margin: 0; font-size: 17px; }
.portfolio-modal form { display: grid; gap: 12px; }
.holding-field { display: grid; gap: 6px; color: #56627b; font-size: 11px; font-weight: 700; }
.holding-field input, .holding-field select { width: 100%; min-height: 42px; padding: 0 11px; color: var(--ink); background: #fafbfe; border: 1px solid #e5e9f2; border-radius: 10px; font-size: 13px; }
.holding-field input:focus, .holding-field select:focus { outline: 3px solid rgb(89 101 245 / 16%); border-color: #9ea7ff; }
.portfolio-form-error { margin: 0; color: #bd424a; font-size: 11px; }
.portfolio-modal-actions { display: flex; justify-content: flex-end; gap: 9px; margin-top: 8px; }
.portfolio-modal-actions .button { min-height: 40px; }
.button-danger { color: #fff; background: #d94f59; }
.button-danger:hover { background: #c8404a; }
.delete-modal > p { color: #687590; font-size: 12px; line-height: 1.65; }

@media (max-width: 760px) {
  .demo-portfolio { gap: 11px; }
  .portfolio-intro { align-items: flex-start; }
  .portfolio-add { min-height: 40px; padding: 0 10px; font-size: 10px; }
  .portfolio-summary { gap: 7px; }
  .portfolio-summary-card { gap: 7px; padding: 11px 10px; border-radius: 12px; }
  .portfolio-summary-card > span { font-size: 10px; }
  .portfolio-summary-card strong { font-size: clamp(13px, 4vw, 17px); }
  .portfolio-summary-card > svg { width: 15px; }
  .portfolio-toolbar { align-items: flex-start; flex-direction: column; gap: 8px; padding: 11px; }
  .portfolio-tabs { width: 100%; }
  .portfolio-tabs button { flex: 1; min-height: 40px; }
  .portfolio-snapshot { font-size: 9px; }
  .portfolio-table-head { display: none; }
  .portfolio-holding-row { grid-template-columns: minmax(0, 1fr) auto; gap: 7px 10px; padding: 12px; }
  .holding-main { grid-column: 1; grid-row: 1; min-height: 42px; }
  .holding-chevron { display: block; }
  .holding-value { grid-column: 1; grid-row: 2; padding-left: 44px; color: #5e6a83; }
  .holding-profit { display: none; }
  .holding-actions { grid-column: 2; grid-row: 1 / span 2; align-items: center; }
  .holding-actions .icon-button { width: 40px; height: 40px; }
  .holding-detail-card { padding: 13px; border-radius: 14px; }
  .holding-detail-heading h3 { font-size: 14px; }
  .holding-detail-grid { grid-template-columns: 1fr; gap: 10px; padding-top: 12px; }
  .holding-chart svg { height: 92px; }
  .holding-periods { gap: 7px; }
  .holding-periods > div { min-height: 65px; padding: 9px; }
  .holding-periods span { font-size: 9px; }
  .holding-periods b { font-size: 11px; }
  .portfolio-modal { padding: 17px; border-radius: 16px; }
  .holding-field input, .holding-field select { min-height: 46px; font-size: 16px; }
}
</style>
