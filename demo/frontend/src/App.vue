<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Clock3,
  CircleHelp,
  ExternalLink,
  LayoutDashboard,
  Newspaper,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  WalletCards,
} from '@lucide/vue'

type IndexItem = { name: string; value: number; change_percent: number }
type DemoFund = {
  code: string
  name: string
  category: string
  estimate_percent: number
  nav_label: string
  series: number[]
}
type DemoStock = {
  code: string
  name: string
  market: string
  sector: string
  price: number
  change_percent: number
  open: number
  high: number
  low: number
  turnover: string
  series: number[]
}
type Sector = { name: string; change_percent: number; related_funds: number }
type Headline = { title: string; category: string; summary: string; source: string; published_at: string }
type Overview = {
  data_mode: string
  snapshot_at: string
  snapshot_label: string
  notice: string
  indices: IndexItem[]
  funds: DemoFund[]
  stocks: DemoStock[]
  sectors: Sector[]
  headlines: Headline[]
}
type WatchlistEntry = { id: number; code: string; name: string; created_at: string }

type Page = 'funds' | 'stocks' | 'news' | 'agent'
const page = ref<Page>('funds')
const overview = ref<Overview | null>(null)
const watchlist = ref<WatchlistEntry[]>([])
const search = ref('')
const loading = ref(true)
const updating = ref(false)
const error = ref('')
const notice = ref('')
const pendingCode = ref('')

const funds = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  if (!keyword) return overview.value?.funds ?? []
  return (overview.value?.funds ?? []).filter((fund) =>
    `${fund.name} ${fund.code} ${fund.category}`.toLowerCase().includes(keyword),
  )
})

const stocks = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  if (!keyword) return overview.value?.stocks ?? []
  return (overview.value?.stocks ?? []).filter((stock) =>
    `${stock.name} ${stock.code} ${stock.sector} ${stock.market}`.toLowerCase().includes(keyword),
  )
})

const isTracked = (code: string) => watchlist.value.some((item) => item.code === code)
const titles: Record<Page, string> = {
  funds: '基金中心',
  stocks: '股票中心',
  news: '市场热点',
  agent: '智能体工作区',
}
const title = computed(() => titles[page.value])

function formatPercent(value: number) {
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

function sparkline(values: number[]) {
  if (!values.length) return ''
  const max = Math.max(...values)
  const min = Math.min(...values)
  const range = max - min || 1
  return values.map((value, index) => {
    const x = (index / Math.max(values.length - 1, 1)) * 100
    const y = 30 - ((value - min) / range) * 25
    return `${x},${y}`
  }).join(' ')
}

function formatSnapshotTime(value: string) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function loadData(showRefresh = false) {
  updating.value = showRefresh
  if (!overview.value) loading.value = true
  error.value = ''
  try {
    const [overviewResponse, watchlistResponse] = await Promise.all([
      fetch('/api/demo/overview'),
      fetch('/api/demo/watchlist'),
    ])
    if (!overviewResponse.ok || !watchlistResponse.ok) throw new Error('本地 API 返回异常，请检查后端是否启动。')
    overview.value = await overviewResponse.json() as Overview
    watchlist.value = await watchlistResponse.json() as WatchlistEntry[]
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : '无法连接本地 API。'
  } finally {
    loading.value = false
    updating.value = false
  }
}

async function addFund(fund: DemoFund) {
  if (isTracked(fund.code)) return
  pendingCode.value = fund.code
  notice.value = ''
  try {
    const response = await fetch('/api/demo/watchlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: fund.code, name: fund.name }),
    })
    if (!response.ok) {
      const payload = await response.json().catch(() => ({})) as { detail?: string }
      throw new Error(payload.detail || '暂时无法加入自选。')
    }
    const entry = await response.json() as WatchlistEntry
    watchlist.value = [entry, ...watchlist.value]
    notice.value = `${fund.name} 已加入本地自选。`
  } catch (exc) {
    notice.value = exc instanceof Error ? exc.message : '暂时无法加入自选。'
  } finally {
    pendingCode.value = ''
  }
}

async function removeFund(item: WatchlistEntry) {
  notice.value = ''
  try {
    const response = await fetch(`/api/demo/watchlist/${item.id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error('移除失败，请稍后重试。')
    watchlist.value = watchlist.value.filter((saved) => saved.id !== item.id)
    notice.value = `${item.name} 已从本地自选移除。`
  } catch (exc) {
    notice.value = exc instanceof Error ? exc.message : '移除失败，请稍后重试。'
  }
}

onMounted(() => loadData())
</script>

<template>
  <div class="workspace-shell">
    <aside class="sidebar">
      <a class="brand" href="https://presight.cloud" aria-label="前往知几 Presight 官网">
        <span class="brand-mark"><Sparkles :size="19" :stroke-width="2.5" /></span>
        <span class="brand-name">知几</span>
      </a>

      <div class="sidebar-label">工作台</div>
      <nav class="nav-list" aria-label="演示导航">
        <button :class="['nav-item', { active: page === 'funds' }]" @click="page = 'funds'">
          <LayoutDashboard :size="18" />
          <span>基金中心</span>
        </button>
        <button :class="['nav-item', { active: page === 'stocks' }]" @click="page = 'stocks'">
          <Activity :size="18" />
          <span>股票中心</span>
        </button>
        <button :class="['nav-item', { active: page === 'news' }]" @click="page = 'news'">
          <Newspaper :size="18" />
          <span>市场热点</span>
        </button>
        <button :class="['nav-item', { active: page === 'agent' }]" @click="page = 'agent'">
          <Sparkles :size="18" />
          <span>智能体</span>
        </button>
      </nav>

      <div class="sidebar-bottom">
        <div class="demo-identity"><span class="identity-mark">访</span><span><b>本地体验</b><small>仅使用示例数据</small></span></div>
        <a class="help-link" href="https://presight.cloud" target="_blank" rel="noreferrer">
          <CircleHelp :size="16" /> 查看线上产品 <ExternalLink :size="13" />
        </a>
      </div>
    </aside>

    <div class="main-column">
      <header class="topbar">
        <div>
          <p class="eyebrow">本地可运行示例</p>
          <h1>{{ title }}</h1>
        </div>
        <div class="topbar-actions">
          <span class="snapshot-time"><Clock3 :size="14" />截至 {{ overview?.snapshot_label ?? '固定快照' }}</span>
          <span class="demo-badge"><span class="status-dot"></span>固定快照 · 非实时</span>
          <a class="website-link" href="https://presight.cloud" target="_blank" rel="noreferrer">
            体验线上产品 <ArrowRight :size="15" />
          </a>
        </div>
      </header>

      <main class="content">
        <div v-if="error" class="connection-error" role="alert">
          <div><b>暂时无法读取演示数据</b><span>{{ error }}</span></div>
          <button class="button button-light" @click="loadData(true)"><RefreshCw :size="15" /> 重试</button>
        </div>

        <template v-if="page === 'funds'">
          <section class="intro-row">
            <div>
              <p class="eyebrow">基金市场 · 固定快照</p>
              <h2>基金行情</h2>
              <p class="intro-copy">指数、板块和基金示例来自同一份静态快照，可浏览行情布局并试用本地自选。</p>
            </div>
            <button class="button button-light refresh-button" :disabled="updating" @click="loadData(true)">
              <RefreshCw :size="15" :class="{ spinning: updating }" /> 重新载入快照
            </button>
          </section>

          <div class="index-grid" aria-label="指数示例">
            <article v-for="index in overview?.indices ?? []" :key="index.name" class="index-card">
              <div class="index-card-top"><span>{{ index.name }}</span><Activity :size="16" /></div>
              <strong>{{ index.value.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</strong>
              <span :class="['change-pill', index.change_percent < 0 ? 'down' : 'up']">
                {{ formatPercent(index.change_percent) }}
              </span>
            </article>
          </div>

          <section class="section-block">
            <div class="section-heading">
              <div><p class="eyebrow">基金行情</p><h2>基金列表</h2></div>
              <label class="search-box">
                <Search :size="16" />
                <input v-model="search" type="search" placeholder="搜索示例基金" aria-label="搜索示例基金" />
              </label>
            </div>
            <p class="data-disclaimer"><Clock3 :size="14" /> {{ overview?.snapshot_label }} · 估值、净值和曲线均为固定演示数据。</p>

            <div v-if="loading" class="loading-panel">正在连接本地演示 API…</div>
            <div v-else-if="funds.length" class="fund-list">
              <article v-for="fund in funds" :key="fund.code" class="fund-row">
                <div class="fund-identity">
                  <span class="fund-avatar"><WalletCards :size="17" /></span>
                  <div><b>{{ fund.name }}</b><small>{{ fund.code }} <span>·</span> {{ fund.category }}</small></div>
                </div>
                <div class="fund-sparkline" aria-hidden="true">
                  <svg viewBox="0 0 100 34" preserveAspectRatio="none"><polyline :points="sparkline(fund.series)" /></svg>
                </div>
                <div class="fund-value"><span>{{ fund.nav_label }}</span><b :class="fund.estimate_percent < 0 ? 'negative' : 'positive'">{{ formatPercent(fund.estimate_percent) }}</b></div>
                <button
                  :class="['button', isTracked(fund.code) ? 'button-saved' : 'button-primary']"
                  :disabled="isTracked(fund.code) || pendingCode === fund.code"
                  @click="addFund(fund)"
                >
                  <CheckCircle2 v-if="isTracked(fund.code)" :size="15" />
                  <Plus v-else :size="15" />
                  {{ isTracked(fund.code) ? '已自选' : pendingCode === fund.code ? '正在添加' : '加入自选' }}
                </button>
              </article>
            </div>
            <p v-else class="empty-state">没有找到匹配的示例基金。</p>
          </section>

          <section class="section-block sector-section">
            <div class="section-heading"><div><p class="eyebrow">市场观察</p><h2>板块表现</h2></div><span class="muted-note">固定快照</span></div>
            <div class="sector-grid">
              <article v-for="sector in overview?.sectors ?? []" :key="sector.name" class="sector-card">
                <div><b>{{ sector.name }}</b><small>{{ sector.related_funds }} 只关联示例基金</small></div>
                <strong :class="sector.change_percent < 0 ? 'negative' : 'positive'">{{ formatPercent(sector.change_percent) }}</strong>
              </article>
            </div>
          </section>
        </template>

        <template v-else-if="page === 'stocks'">
          <section class="intro-row">
            <div>
              <p class="eyebrow">股票市场 · 固定快照</p>
              <h2>股票行情</h2>
              <p class="intro-copy">展示价格、涨跌、日内区间和走势组件。接入自己的数据源后，可按供应商字段映射。</p>
            </div>
            <span class="demo-badge"><span class="status-dot"></span>{{ overview?.snapshot_label }}</span>
          </section>
          <section class="section-block stock-section">
            <div class="section-heading">
              <div><p class="eyebrow">A 股示例</p><h2>股票列表</h2></div>
              <label class="search-box">
                <Search :size="16" />
                <input v-model="search" type="search" placeholder="搜索示例股票" aria-label="搜索示例股票" />
              </label>
            </div>
            <p class="data-disclaimer"><Clock3 :size="14" /> 固定于 {{ formatSnapshotTime(overview?.snapshot_at ?? '') }}（北京时间），不是实时行情。</p>
            <div v-if="loading" class="loading-panel">正在读取本地快照…</div>
            <div v-else-if="stocks.length" class="stock-list">
              <article v-for="stock in stocks" :key="stock.code" class="stock-row">
                <div class="stock-identity">
                  <span class="stock-avatar"><Activity :size="17" /></span>
                  <div><b>{{ stock.name }}</b><small>{{ stock.code }} · {{ stock.market }} · {{ stock.sector }}</small></div>
                </div>
                <div class="fund-sparkline stock-sparkline" aria-hidden="true">
                  <svg viewBox="0 0 100 34" preserveAspectRatio="none"><polyline :points="sparkline(stock.series)" /></svg>
                </div>
                <div class="stock-quote">
                  <strong>{{ stock.price.toFixed(2) }}</strong>
                  <span :class="stock.change_percent < 0 ? 'negative' : 'positive'">{{ formatPercent(stock.change_percent) }}</span>
                </div>
                <div class="stock-range"><span>开 {{ stock.open.toFixed(2) }}</span><span>高 {{ stock.high.toFixed(2) }}</span><span>低 {{ stock.low.toFixed(2) }}</span><small>{{ stock.turnover }}</small></div>
              </article>
            </div>
            <p v-else class="empty-state">没有找到匹配的示例股票。</p>
          </section>
          <section class="stock-note"><Activity :size="18" /><div><b>数据源接入位置</b><p>后端已留出基金与股票数据接口。请在本地配置自己的供应商 URL 和认证信息，密钥只由后端读取。</p></div></section>
        </template>

        <template v-else-if="page === 'news'">
          <section class="intro-row">
            <div>
              <p class="eyebrow">市场热点 · 固定快照</p>
              <h2>新闻与市场主题</h2>
              <p class="intro-copy">浏览带有发布时间的示例新闻卡片。当前列表与行情快照一同固定，不会自动拉取网络内容。</p>
            </div>
            <span class="demo-badge"><span class="status-dot"></span>固定资讯快照</span>
          </section>
          <section class="news-list">
            <article v-for="(headline, index) in overview?.headlines ?? []" :key="headline.title" class="news-card">
              <div class="news-index">{{ String(index + 1).padStart(2, '0') }}</div>
              <div class="news-content"><span class="news-category">{{ headline.category }}</span><h3>{{ headline.title }}</h3><p>{{ headline.summary }}</p><small class="news-meta">{{ headline.source }} · {{ formatSnapshotTime(headline.published_at) }}</small></div>
            </article>
          </section>
        </template>

        <template v-else>
          <section class="intro-row">
            <div>
              <p class="eyebrow">智能体 · 对话界面预览</p>
              <h2>知几研究助手</h2>
              <p class="intro-copy">保留对话工作区的布局和交互入口。此页面使用静态示例，不会发送问题或调用模型。</p>
            </div>
            <span class="agent-status"><span></span>本地预览</span>
          </section>
          <section class="agent-preview">
            <div class="agent-preview-head"><span class="agent-mark"><Sparkles :size="18" /></span><div><b>观潮</b><small>市场入门助手 · 对话预览</small></div></div>
            <div class="agent-thread">
              <div class="agent-message user-message">能不能帮我看看基金和股票的市场信息？</div>
              <div class="agent-reply"><span class="agent-reply-mark"><Sparkles :size="15" /></span><div><b>观潮</b><p>这里会显示智能体的结构化回复。你可以在本地为对话接入自己的模型服务；当前仓库只展示界面，不会发出 AI 请求。</p><div class="reply-tags"><span>市场数据</span><span>个人资料</span><span>Skills</span></div></div></div>
            </div>
            <div class="agent-composer"><div class="composer-placeholder">接入 AI 服务后，可在这里输入问题</div><button class="button button-primary" disabled><Sparkles :size="15" /> 发送</button></div>
            <p class="agent-footnote">示例对话为静态内容；模型、提示词、工具调用和知识检索没有在此处实现。</p>
          </section>
          <section class="agent-capabilities">
            <article><span>01</span><b>对话与回答</b><p>消息列表、输入区和回复排版的前端结构。</p></article>
            <article><span>02</span><b>智能体资料</b><p>可用于展示风格、Skills 与知识资料选择状态。</p></article>
            <article><span>03</span><b>数据上下文</b><p>可在本地将行情服务和用户自己的数据连接进来。</p></article>
          </section>
        </template>

        <p v-if="notice" class="action-notice" role="status">{{ notice }}</p>
      </main>
    </div>

    <aside class="context-panel">
      <div class="context-heading"><span class="context-icon"><Sparkles :size="17" /></span><div><b>工作台说明</b><small>数据与功能状态</small></div></div>
      <article class="context-card">
        <span class="context-tag">{{ overview?.snapshot_label ?? '固定快照' }}</span>
        <h2>静态市场数据</h2>
        <p>指数、基金、股票和资讯共用同一时点的演示快照，打开页面不会抓取行情或新闻。</p>
        <div class="context-check"><CheckCircle2 :size="16" /><span>自选列表保存在本地</span></div>
        <div class="context-check"><CheckCircle2 :size="16" /><span>数据源密钥仅由后端读取</span></div>
      </article>
      <article class="context-card subtle-card">
        <span class="context-tag">线上知几</span>
        <h2>打开知几工作台</h2>
        <p>线上产品提供基金估值、股票行情、市场热点和可配置的 AI 研究助手。</p>
        <a href="https://presight.cloud" target="_blank" rel="noreferrer">打开 presight.cloud <ExternalLink :size="14" /></a>
      </article>
      <div class="watchlist-card">
        <div class="watchlist-heading"><span><WalletCards :size="16" /> 本地自选</span><b>{{ watchlist.length }}</b></div>
        <div v-if="watchlist.length" class="watchlist-items">
          <div v-for="item in watchlist" :key="item.id" class="watchlist-item"><span><b>{{ item.name }}</b><small>{{ item.code }}</small></span><button class="icon-button" :aria-label="`移除${item.name}`" @click="removeFund(item)"><Trash2 :size="15" /></button></div>
        </div>
        <p v-else class="watchlist-empty">加入示例基金后会显示在这里。</p>
      </div>
      <div class="api-note"><CircleHelp :size="15" /><span>{{ overview?.notice ?? '演示数据与真实行情无关。' }}</span></div>
    </aside>

    <nav class="mobile-nav" aria-label="移动端演示导航">
      <button :class="{ active: page === 'funds' }" @click="page = 'funds'"><LayoutDashboard :size="18" /><span>基金</span></button>
      <button :class="{ active: page === 'stocks' }" @click="page = 'stocks'"><Activity :size="18" /><span>股票</span></button>
      <button :class="{ active: page === 'news' }" @click="page = 'news'"><Newspaper :size="18" /><span>热点</span></button>
      <button :class="{ active: page === 'agent' }" @click="page = 'agent'"><Sparkles :size="18" /><span>智能体</span></button>
    </nav>
  </div>
</template>
