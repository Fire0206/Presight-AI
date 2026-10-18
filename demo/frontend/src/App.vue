<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  CircleHelp,
  Clock3,
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
type Sector = { name: string; change_percent: number; related_funds: number }
type Headline = { title: string; category: string; summary: string }
type Overview = {
  data_mode: string
  notice: string
  indices: IndexItem[]
  funds: DemoFund[]
  sectors: Sector[]
  headlines: Headline[]
}
type WatchlistEntry = { id: number; code: string; name: string; created_at: string }

const page = ref<'funds' | 'news'>('funds')
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

const isTracked = (code: string) => watchlist.value.some((item) => item.code === code)
const title = computed(() => page.value === 'funds' ? '基金中心' : '市场热点')

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
        <button :class="['nav-item', { active: page === 'news' }]" @click="page = 'news'">
          <Newspaper :size="18" />
          <span>市场热点</span>
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
          <span class="demo-badge"><span class="status-dot"></span>示例数据 · 非实时</span>
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
              <p class="eyebrow">市场快照</p>
              <h2>先看市场，再看基金</h2>
              <p class="intro-copy">指数、板块和基金示例放在同一页，适合体验页面和 API 的基本连接。</p>
            </div>
            <button class="button button-light refresh-button" :disabled="updating" @click="loadData(true)">
              <RefreshCw :size="15" :class="{ spinning: updating }" /> 刷新示例
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
              <div><p class="eyebrow">基金行情</p><h2>盘中估值示例</h2></div>
              <label class="search-box">
                <Search :size="16" />
                <input v-model="search" type="search" placeholder="搜索示例基金" aria-label="搜索示例基金" />
              </label>
            </div>
            <p class="data-disclaimer"><Clock3 :size="14" /> 下方估值和曲线为虚构数据，只演示前端展示方式。</p>

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
            <div class="section-heading"><div><p class="eyebrow">市场观察</p><h2>板块表现</h2></div><span class="muted-note">仅供界面演示</span></div>
            <div class="sector-grid">
              <article v-for="sector in overview?.sectors ?? []" :key="sector.name" class="sector-card">
                <div><b>{{ sector.name }}</b><small>{{ sector.related_funds }} 只关联示例基金</small></div>
                <strong :class="sector.change_percent < 0 ? 'negative' : 'positive'">{{ formatPercent(sector.change_percent) }}</strong>
              </article>
            </div>
          </section>
        </template>

        <template v-else>
          <section class="intro-row">
            <div>
              <p class="eyebrow">热点资讯</p>
              <h2>新闻与市场主题</h2>
              <p class="intro-copy">真实产品中可以结合新闻和行情继续研究；这个公开示例不会接入新闻源。</p>
            </div>
            <span class="demo-badge"><span class="status-dot"></span>虚构资讯</span>
          </section>
          <section class="news-list">
            <article v-for="(headline, index) in overview?.headlines ?? []" :key="headline.title" class="news-card">
              <div class="news-index">{{ String(index + 1).padStart(2, '0') }}</div>
              <div class="news-content"><span class="news-category">{{ headline.category }}</span><h3>{{ headline.title }}</h3><p>{{ headline.summary }}</p></div>
              <ArrowRight class="news-arrow" :size="18" />
            </article>
          </section>
        </template>

        <p v-if="notice" class="action-notice" role="status">{{ notice }}</p>
      </main>
    </div>

    <aside class="context-panel">
      <div class="context-heading"><span class="context-icon"><Sparkles :size="17" /></span><div><b>使用说明</b><small>本地示例与线上产品的区别</small></div></div>
      <article class="context-card">
        <span class="context-tag">本地 API</span>
        <h2>可以启动，也可以改</h2>
        <p>页面通过 FastAPI 读取示例行情，并把自选列表保存到本地 SQLite 文件。</p>
        <div class="context-check"><CheckCircle2 :size="16" /><span>包含前端、后端和测试</span></div>
        <div class="context-check"><CheckCircle2 :size="16" /><span>没有账号或线上密钥</span></div>
      </article>
      <article class="context-card subtle-card">
        <span class="context-tag">线上知几</span>
        <h2>体验完整功能</h2>
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
      <button :class="{ active: page === 'news' }" @click="page = 'news'"><Newspaper :size="18" /><span>热点</span></button>
      <a href="https://presight.cloud" target="_blank" rel="noreferrer"><ExternalLink :size="18" /><span>线上体验</span></a>
    </nav>
  </div>
</template>
