<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  BookOpen,
  Bot,
  Check,
  ChevronRight,
  Copy,
  FileUp,
  MessageSquarePlus,
  Paperclip,
  Plus,
  RotateCcw,
  Send,
  Sparkles,
  Square,
  Trash2,
  X,
} from '@lucide/vue'
import AnswerRenderer from './AnswerRenderer.vue'

type DemoAgent = {
  id: string
  name: string
  description: string
  style: string
  skills: string[]
  knowledge: string[]
  builtIn: boolean
}
type KnowledgeSource = { id: string; name: string; kind: '内置资料' | '本地文件' }
type ChatMessage = { id: string; role: 'user' | 'assistant'; content: string; files?: string[] }

const STORAGE_KEY = 'presight-public-demo-agents-v1'
const baseAgents: DemoAgent[] = [
  { id: 'market-guide', name: '观潮', description: '用清楚的例子了解基金、股票和市场基础。', style: '先讲结论，再用简单例子解释。', skills: ['market-brief', 'chart-reading'], knowledge: ['market-basics', 'fund-basics'], builtIn: true },
  { id: 'research', name: '知几研究', description: '整理行情变化、主题线索和需要继续核对的信息。', style: '分点说明依据、影响和待确认事项。', skills: ['market-brief', 'news-context', 'valuation-check'], knowledge: ['market-basics', 'research-notes'], builtIn: true },
  { id: 'portfolio-helper', name: '组合观察', description: '从示例持仓出发，练习查看收益和市场关联。', style: '先概览组合，再逐项说明变化。', skills: ['portfolio-view', 'valuation-check'], knowledge: ['fund-basics', 'research-notes'], builtIn: true },
]
const skills = [
  { id: 'market-brief', name: '市场速览', description: '汇总指数与板块的演示变化' },
  { id: 'chart-reading', name: '图表解读', description: '说明示例走势和常见指标' },
  { id: 'news-context', name: '新闻脉络', description: '把示例资讯整理成主题' },
  { id: 'valuation-check', name: '估值观察', description: '查看示例估值及数据时间' },
  { id: 'portfolio-view', name: '持仓透视', description: '按演示持仓查看盈亏构成' },
]
const initialKnowledge: KnowledgeSource[] = [
  { id: 'market-basics', name: '市场基础资料', kind: '内置资料' },
  { id: 'fund-basics', name: '基金入门手册', kind: '内置资料' },
  { id: 'research-notes', name: '研究记录示例', kind: '内置资料' },
]

const agents = ref<DemoAgent[]>(baseAgents.map((agent) => ({ ...agent, skills: [...agent.skills], knowledge: [...agent.knowledge] })))
const knowledgeSources = ref<KnowledgeSource[]>([...initialKnowledge])
const selectedId = ref(baseAgents[0].id)
const messages = ref<ChatMessage[]>([
  { id: 'welcome-user', role: 'user', content: '帮我梳理一下观察基金时可以先看哪些信息。' },
  { id: 'welcome-assistant', role: 'assistant', content: '可以先看三件事：基金跟踪什么资产、近期表现与对应指数是否一致、持仓和行业有没有明显变化。\n\n下面是固定示例对话；后续回复会按当前模型配置使用本地示例或你配置的文本模型。' },
])
const prompt = ref('')
const pendingFiles = ref<string[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const knowledgeFileInput = ref<HTMLInputElement | null>(null)
const thinking = ref(false)
const modelConfigured = ref(false)
const chatError = ref('')
const copyNotice = ref('')
const newAgentOpen = ref(false)
const newAgentName = ref('')
const newAgentDescription = ref('')
const deleteOpen = ref(false)
const newAgentError = ref('')
let replyTimer: number | undefined
let activeController: AbortController | undefined

const selectedAgent = computed(() => agents.value.find((agent) => agent.id === selectedId.value) ?? agents.value[0] ?? null)
const selectedKnowledge = computed(() => knowledgeSources.value.filter((item) => selectedAgent.value?.knowledge.includes(item.id)))
const selectedSkills = computed(() => skills.filter((skill) => selectedAgent.value?.skills.includes(skill.id)))
const lastAssistant = computed(() => [...messages.value].reverse().find((message) => message.role === 'assistant') ?? null)

function makeId(prefix: string) {
  return prefix + '-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7)
}

function persistConfig() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ agents: agents.value, knowledgeSources: knowledgeSources.value }))
  } catch {
    copyNotice.value = '浏览器暂时无法保存本机演示配置。'
  }
}

function toggleSkill(skillId: string, checked: boolean) {
  if (!selectedAgent.value) return
  const next = new Set(selectedAgent.value.skills)
  if (checked) next.add(skillId)
  else next.delete(skillId)
  selectedAgent.value.skills = [...next]
}

function toggleKnowledge(sourceId: string, checked: boolean) {
  if (!selectedAgent.value) return
  const next = new Set(selectedAgent.value.knowledge)
  if (checked) next.add(sourceId)
  else next.delete(sourceId)
  selectedAgent.value.knowledge = [...next]
}

function handleFiles(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files ?? [])
  if (files.length) {
    const current = new Set(pendingFiles.value)
    for (const file of files) current.add(file.name)
    pendingFiles.value = [...current]
    copyNotice.value = '已在演示界面中选择文件名；文件内容没有上传或读取。'
  }
  target.value = ''
}

function addKnowledgeFiles(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files ?? [])
  if (!selectedAgent.value || !files.length) return
  for (const file of files) {
    const existing = knowledgeSources.value.find((source) => source.name === file.name)
    const source = existing ?? { id: makeId('local-file'), name: file.name, kind: '本地文件' as const }
    if (!existing) knowledgeSources.value = [...knowledgeSources.value, source]
    if (!selectedAgent.value.knowledge.includes(source.id)) selectedAgent.value.knowledge.push(source.id)
  }
  copyNotice.value = '文件名已加入本机演示知识库；没有上传或读取文件内容。'
  target.value = ''
}

function openNewAgent() {
  newAgentError.value = ''
  newAgentName.value = ''
  newAgentDescription.value = ''
  newAgentOpen.value = true
}

function createAgent() {
  const name = newAgentName.value.trim()
  if (!name) {
    newAgentError.value = '请先填写智能体名称。'
    return
  }
  if (agents.value.length >= 12) {
    newAgentError.value = '本机演示最多创建 12 个智能体。'
    return
  }
  const agent: DemoAgent = {
    id: makeId('agent'),
    name,
    description: newAgentDescription.value.trim() || '自定义智能体简介',
    style: '先说明重点，再列出判断依据。',
    skills: [],
    knowledge: [],
    builtIn: false,
  }
  agents.value = [...agents.value, agent]
  selectedId.value = agent.id
  newAgentOpen.value = false
  resetChat()
}

function removeAgent() {
  if (!selectedAgent.value || agents.value.length < 2) return
  const id = selectedAgent.value.id
  agents.value = agents.value.filter((agent) => agent.id !== id)
  selectedId.value = agents.value[0].id
  deleteOpen.value = false
  resetChat()
}

function resetChat() {
  if (replyTimer) window.clearTimeout(replyTimer)
  activeController?.abort()
  activeController = undefined
  thinking.value = false
  chatError.value = ''
  prompt.value = ''
  pendingFiles.value = []
  messages.value = [{ id: makeId('hello'), role: 'assistant', content: '你好，我是' + (selectedAgent.value?.name ?? '知几') + '。这里可以体验文字对话；未配置模型接口时会显示本机示例回复。' }]
}

function makeDemoReply(query: string) {
  const focus = query.trim().slice(0, 80) || '你选择的材料'
  const knowledgeNames = selectedKnowledge.value.map((item) => item.name).join('、') || '暂无选中资料'
  const skillNames = selectedSkills.value.map((item) => item.name).join('、') || '未选择技能'
  return '## 简要结论\n\n围绕“' + focus + '”，可以先确认观察对象和数据时点，再结合相同区间的资料进行比较。\n\n### 建议核对\n\n1. 确认基金或股票代码，以及比较的时间范围。\n2. 对照已确认数据与估算数据，留意它们的更新时间。\n3. 把暂时无法从示例资料确认的内容列为待核实问题。\n\n| 数据 | 查看重点 |\n| --- | --- |\n| 已确认净值 | 作为持仓份额与历史对照的依据 |\n| 盘中估值 | 只作当日变化参考，注意更新时间 |\n\n**本机演示配置：**' + skillNames + '；' + knowledgeNames + '。\n\n> 这是固定示例回复，不代表实时研究结论。'
}

async function loadModelStatus() {
  try {
    const response = await fetch('/api/demo/model-status')
    if (!response.ok) throw new Error('status')
    const payload = await response.json() as { configured?: boolean }
    modelConfigured.value = payload.configured === true
  } catch {
    modelConfigured.value = false
  }
}

function recentMessages() {
  const selected: Array<{ role: 'user' | 'assistant'; content: string }> = []
  let total = 0
  for (const message of [...messages.value].slice(-12).reverse()) {
    const content = message.content.trim()
    if (!content || total + content.length > 16_000) break
    selected.push({ role: message.role, content })
    total += content.length
  }
  return selected.reverse()
}

async function queueReply(query: string, attachmentOnly = false) {
  if (replyTimer) window.clearTimeout(replyTimer)
  activeController?.abort()
  chatError.value = ''
  thinking.value = true
  if (modelConfigured.value && !attachmentOnly) {
    const controller = new AbortController()
    activeController = controller
    try {
      const response = await fetch('/api/demo/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: recentMessages() }),
        signal: controller.signal,
      })
      const payload = await response.json().catch(() => ({})) as { answer?: string; detail?: string }
      if (!response.ok || !payload.answer) throw new Error(payload.detail || '模型请求失败，请检查后端配置后重试。')
      messages.value = [...messages.value, { id: makeId('assistant'), role: 'assistant', content: payload.answer }]
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        chatError.value = error instanceof Error ? error.message : '模型请求失败，请稍后重试。'
      }
    } finally {
      if (activeController === controller) activeController = undefined
      thinking.value = false
    }
    return
  }

  replyTimer = window.setTimeout(() => {
    const content = attachmentOnly
      ? '目前的公开示例只记录附件文件名，不会读取或上传文件内容。请把需要讨论的文字粘贴到输入框。'
      : makeDemoReply(query)
    messages.value = [...messages.value, { id: makeId('assistant'), role: 'assistant', content }]
    thinking.value = false
    replyTimer = undefined
  }, 450)
}

function sendMessage() {
  const text = prompt.value.trim()
  if ((!text && !pendingFiles.value.length) || thinking.value) return
  const attachments = [...pendingFiles.value]
  const query = text || '请查看我选中的文件'
  messages.value = [...messages.value, { id: makeId('user'), role: 'user', content: text || '请查看附件', files: attachments }]
  prompt.value = ''
  pendingFiles.value = []
  void queueReply(query, attachments.length > 0 && !text)
}

function stopDemoReply() {
  if (replyTimer) window.clearTimeout(replyTimer)
  replyTimer = undefined
  activeController?.abort()
  activeController = undefined
  thinking.value = false
  chatError.value = ''
  messages.value = [...messages.value, { id: makeId('assistant'), role: 'assistant', content: '已停止本次生成。' }]
}

function retryLast() {
  const lastUser = [...messages.value].reverse().find((message) => message.role === 'user')
  if (lastUser) void queueReply(lastUser.content, lastUser.content === '请查看附件')
}

async function copyAnswer(message: ChatMessage) {
  try {
    await navigator.clipboard.writeText(message.content)
    copyNotice.value = '已复制回答。'
  } catch {
    copyNotice.value = '复制失败，请检查浏览器剪贴板权限。'
  }
}

onMounted(() => {
  void loadModelStatus()
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved) as { agents?: DemoAgent[]; knowledgeSources?: KnowledgeSource[] }
      if (Array.isArray(parsed.agents) && parsed.agents.length) agents.value = parsed.agents
      if (Array.isArray(parsed.knowledgeSources)) knowledgeSources.value = parsed.knowledgeSources
      if (!agents.value.some((agent) => agent.id === selectedId.value)) selectedId.value = agents.value[0].id
    }
  } catch {
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      // Some browsers block storage in private or restricted contexts.
    }
  }
})

watch([agents, knowledgeSources], persistConfig, { deep: true })
watch(selectedId, resetChat)
onBeforeUnmount(() => {
  if (replyTimer) window.clearTimeout(replyTimer)
  activeController?.abort()
})
</script>

<template>
  <div class="demo-agent-studio">
    <section class="intro-row agent-studio-intro">
      <div>
        <p class="eyebrow">智能体中心 · 本机演示</p>
        <h2>管理智能体与对话</h2>
        <p class="intro-copy">选择智能体、勾选资料与技能，然后在右侧对话区体验交互。所有配置只保存在当前浏览器。</p>
      </div>
      <button class="button button-primary agent-create-trigger" @click="openNewAgent"><Plus :size="16" /> 添加智能体</button>
    </section>

    <div class="agent-studio-layout">
      <aside class="agent-list-card" aria-label="智能体列表">
        <div class="agent-list-heading"><div><p class="eyebrow">我的智能体</p><b>{{ agents.length }} 个</b></div><button class="icon-button" aria-label="新建智能体" title="新建智能体" @click="openNewAgent"><Plus :size="17" /></button></div>
        <button v-for="agent in agents" :key="agent.id" :class="['agent-list-item', { active: selectedId === agent.id }]" @click="selectedId = agent.id">
          <span class="agent-list-icon"><Sparkles :size="16" /></span>
          <span class="agent-list-copy"><b>{{ agent.name }}</b><small>{{ agent.builtIn ? '系统智能体' : '自定义智能体' }}</small></span>
          <ChevronRight :size="15" />
        </button>
        <button class="agent-add-card" @click="openNewAgent"><span><Plus :size="16" /></span><b>创建新智能体</b><small>设置名称、风格和资料</small></button>
      </aside>

      <div v-if="selectedAgent" class="agent-workspace-demo">
        <section class="agent-config-card">
          <header class="agent-config-header">
            <span class="agent-config-mark"><Bot :size="20" /></span>
            <div><p class="eyebrow">{{ selectedAgent.builtIn ? '内置智能体' : '自定义智能体' }}</p><b>{{ selectedAgent.name }}</b></div>
            <button v-if="agents.length > 1" class="icon-button agent-delete" aria-label="删除当前智能体" title="删除当前智能体" @click="deleteOpen = true"><Trash2 :size="16" /></button>
          </header>
          <div class="agent-edit-fields">
            <label>智能体名称<input v-model="selectedAgent.name" maxlength="32" aria-label="智能体名称" /></label>
            <label>简介<textarea v-model="selectedAgent.description" rows="2" maxlength="180" aria-label="智能体简介"></textarea></label>
            <label>回答风格<textarea v-model="selectedAgent.style" rows="2" maxlength="180" aria-label="回答风格"></textarea></label>
          </div>
          <div class="agent-config-grid">
            <section class="agent-option-section">
              <div class="agent-option-heading"><span><BookOpen :size="16" /> 参考资料</span><b>{{ selectedKnowledge.length }} 个</b></div>
              <label v-for="source in knowledgeSources" :key="source.id" class="agent-check-row">
                <input type="checkbox" :checked="selectedAgent.knowledge.includes(source.id)" @change="toggleKnowledge(source.id, ($event.target as HTMLInputElement).checked)" />
                <span><b>{{ source.name }}</b><small>{{ source.kind }}</small></span>
              </label>
              <button type="button" class="agent-upload-button" @click="knowledgeFileInput?.click()"><FileUp :size="15" /> 添加本地文件</button>
              <input ref="knowledgeFileInput" class="visually-hidden-file" type="file" multiple accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg" @change="addKnowledgeFiles" />
              <small class="agent-local-note">演示版只保存文件名，不上传或读取文件内容。</small>
            </section>
            <section class="agent-option-section">
              <div class="agent-option-heading"><span><Sparkles :size="16" /> 可用技能</span><b>{{ selectedSkills.length }} 个</b></div>
              <label v-for="skill in skills" :key="skill.id" class="agent-check-row">
                <input type="checkbox" :checked="selectedAgent.skills.includes(skill.id)" @change="toggleSkill(skill.id, ($event.target as HTMLInputElement).checked)" />
                <span><b>{{ skill.name }}</b><small>{{ skill.description }}</small></span>
              </label>
              <p class="agent-local-note">这里记录可用配置；选择某项不代表每次对话都会调用它。</p>
            </section>
          </div>
        </section>

        <section class="agent-chat-card">
          <header class="agent-chat-header">
            <div><span class="agent-chat-status"><span :class="{ connected: modelConfigured }"></span> {{ modelConfigured ? '已配置模型 API' : '本地示例回复' }}</span><h3>与{{ selectedAgent.name }}对话</h3></div>
            <button class="button button-light new-chat-button" @click="resetChat"><MessageSquarePlus :size="15" /> 新建对话</button>
          </header>
          <div class="agent-chat-messages" aria-live="polite">
            <article v-for="message in messages" :key="message.id" :class="['demo-chat-message', message.role === 'user' ? 'user' : 'assistant']">
              <span v-if="message.role === 'assistant'" class="demo-message-avatar"><Sparkles :size="15" /></span>
              <div class="demo-message-body">
                <b>{{ message.role === 'user' ? '你' : selectedAgent.name }}</b>
                <AnswerRenderer v-if="message.role === 'assistant'" :content="message.content" />
                <p v-else>{{ message.content }}</p>
                <div v-if="message.files?.length" class="demo-message-files"><span v-for="file in message.files" :key="file">{{ file }}</span></div>
                <div v-if="message.role === 'assistant'" class="demo-message-actions">
                  <button class="icon-button" aria-label="复制回答" title="复制回答" @click="copyAnswer(message)"><Copy :size="14" /></button>
                  <button v-if="lastAssistant?.id === message.id" class="icon-button" aria-label="重新分析" title="重新分析" @click="retryLast"><RotateCcw :size="14" /></button>
                </div>
              </div>
            </article>
            <div v-if="thinking" class="demo-thinking"><span class="thinking-dot"></span><span>{{ modelConfigured ? '正在等待模型回复…' : '正在生成示例回复…' }}</span><button class="icon-button" aria-label="停止生成" title="停止生成" @click="stopDemoReply"><Square :size="13" /></button></div>
          </div>
          <p v-if="chatError" class="agent-chat-error" role="alert">{{ chatError }} <button type="button" @click="retryLast">重试</button></p>
          <div v-if="pendingFiles.length" class="pending-file-list">
            <span v-for="file in pendingFiles" :key="file">{{ file }}<button :aria-label="'移除' + file" @click="pendingFiles = pendingFiles.filter((name) => name !== file)"><X :size="12" /></button></span>
          </div>
          <form class="agent-composer-live" @submit.prevent="sendMessage">
            <textarea v-model="prompt" rows="2" maxlength="8000" aria-label="输入问题" placeholder="输入问题，或选择一份文件作为附件…" @keydown.ctrl.enter.prevent="sendMessage"></textarea>
            <div class="agent-composer-toolbar">
              <div class="agent-composer-options">
                <button type="button" class="icon-button attach-button" aria-label="选择附件" title="选择附件" @click="fileInput?.click()"><Paperclip :size="17" /></button>
                <input ref="fileInput" class="visually-hidden-file" type="file" multiple accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg" @change="handleFiles" />
                <span class="agent-count-chip"><BookOpen :size="13" /> {{ selectedKnowledge.length }} 个资料</span>
                <span class="agent-count-chip"><Sparkles :size="13" /> {{ selectedSkills.length }} 个技能</span>
              </div>
              <button class="button button-primary agent-send-button" :disabled="thinking || (!prompt.trim() && !pendingFiles.length)" type="submit"><Send :size="15" /> 发送</button>
            </div>
          </form>
          <p class="agent-demo-footnote">{{ modelConfigured ? '文字会发送到你在后端 .env 配置的模型接口；密钥不会进入浏览器。附件内容、知识库和技能仍为本机界面示例。' : '当前使用本机示例回复。配置后端 .env 后可连接模型；附件内容、知识库和技能不会上传或调用。' }}</p>
        </section>
      </div>
    </div>

    <p v-if="copyNotice" class="agent-local-notice" role="status"><Check :size="14" />{{ copyNotice }}</p>

    <div v-if="newAgentOpen" class="agent-modal-backdrop" @click.self="newAgentOpen = false" @keydown.esc="newAgentOpen = false">
      <section class="agent-modal" role="dialog" aria-modal="true" aria-labelledby="new-agent-title">
        <header><div><p class="eyebrow">本机演示配置</p><h3 id="new-agent-title">创建智能体</h3></div><button class="icon-button" aria-label="关闭" @click="newAgentOpen = false"><X :size="18" /></button></header>
        <form @submit.prevent="createAgent">
          <label>名称<input v-model="newAgentName" maxlength="32" required autocomplete="off" placeholder="给智能体起个名字" /></label>
          <label>简介<textarea v-model="newAgentDescription" maxlength="180" rows="3" placeholder="它擅长帮助你做什么？"></textarea></label>
          <p v-if="newAgentError" class="agent-form-error" role="alert">{{ newAgentError }}</p>
          <div class="agent-modal-actions"><button type="button" class="button button-light" @click="newAgentOpen = false">取消</button><button type="submit" class="button button-primary"><Plus :size="15" /> 创建</button></div>
        </form>
      </section>
    </div>

    <div v-if="deleteOpen && selectedAgent" class="agent-modal-backdrop" @click.self="deleteOpen = false" @keydown.esc="deleteOpen = false">
      <section class="agent-modal" role="alertdialog" aria-modal="true" aria-labelledby="delete-agent-title">
        <header><div><p class="eyebrow">确认操作</p><h3 id="delete-agent-title">删除“{{ selectedAgent.name }}”？</h3></div><button class="icon-button" aria-label="关闭" @click="deleteOpen = false"><X :size="18" /></button></header>
        <p class="agent-delete-copy">只会从当前浏览器的演示列表中移除。</p>
        <div class="agent-modal-actions"><button class="button button-light" @click="deleteOpen = false">取消</button><button class="button button-danger" @click="removeAgent"><Trash2 :size="15" /> 删除</button></div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.demo-agent-studio { display: grid; gap: 15px; }
.agent-studio-intro { margin-bottom: 0; align-items: center; }
.agent-create-trigger { min-height: 42px; }
.agent-studio-layout { display: grid; grid-template-columns: 218px minmax(0, 1fr); align-items: start; gap: 13px; }
.agent-list-card, .agent-config-card, .agent-chat-card { background: #fff; border: 1px solid var(--line); border-radius: 16px; box-shadow: var(--shadow); }
.agent-list-card { display: grid; gap: 7px; padding: 12px; }
.agent-list-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 1px 3px 6px; }
.agent-list-heading .eyebrow { margin: 0 0 4px; color: var(--blue); }
.agent-list-heading b { color: #6f7b96; font-size: 11px; }
.agent-list-heading .icon-button { width: 36px; height: 36px; color: var(--blue); background: var(--blue-soft); }
.agent-list-item { display: flex; align-items: center; gap: 9px; min-width: 0; min-height: 53px; padding: 7px 8px; color: #56627b; background: transparent; border: 1px solid transparent; border-radius: 11px; cursor: pointer; text-align: left; transition: background .18s, border-color .18s; }
.agent-list-item:hover { background: #f7f8ff; }
.agent-list-item.active { color: var(--ink); background: #f0f2ff; border-color: #dce0ff; }
.agent-list-icon, .agent-config-mark { display: grid; flex: 0 0 auto; place-items: center; color: var(--blue); background: #e9ecff; border-radius: 10px; }
.agent-list-icon { width: 34px; height: 34px; }
.agent-list-copy { display: grid; min-width: 0; flex: 1; gap: 3px; }
.agent-list-copy b, .agent-list-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.agent-list-copy b { font-size: 11px; }
.agent-list-copy small { color: #8a95aa; font-size: 9px; }
.agent-list-item > svg { color: #a0a9bb; }
.agent-add-card { display: grid; grid-template-columns: 29px 1fr; align-items: center; gap: 2px 8px; margin-top: 3px; padding: 10px 9px; color: #66728b; background: #fafbff; border: 1px dashed #d9def2; border-radius: 11px; cursor: pointer; text-align: left; }
.agent-add-card > span { display: grid; width: 28px; height: 28px; grid-row: span 2; place-items: center; color: var(--blue); background: #eff1ff; border-radius: 8px; }
.agent-add-card b { font-size: 10px; }
.agent-add-card small { color: #929cb0; font-size: 9px; }
.agent-workspace-demo { display: grid; min-width: 0; gap: 13px; }
.agent-config-card { overflow: hidden; }
.agent-config-header { display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-bottom: 1px solid #f0f2f7; }
.agent-config-mark { width: 39px; height: 39px; color: #fff; background: var(--blue); border-radius: 12px; }
.agent-config-header > div { display: grid; min-width: 0; flex: 1; gap: 3px; }
.agent-config-header .eyebrow { margin: 0; color: var(--blue); }
.agent-config-header b { overflow: hidden; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.agent-delete { color: #8b96aa; }
.agent-delete:hover { color: #d84e57; background: #fff0f0; }
.agent-edit-fields { display: grid; grid-template-columns: 1fr 1.3fr 1.3fr; gap: 10px; padding: 13px 15px; border-bottom: 1px solid #f0f2f7; }
.agent-edit-fields label, .agent-modal label { display: grid; align-content: start; gap: 6px; min-width: 0; color: #63708b; font-size: 10px; font-weight: 750; }
.agent-edit-fields input, .agent-edit-fields textarea, .agent-modal input, .agent-modal textarea { width: 100%; min-width: 0; min-height: 39px; padding: 8px 10px; color: var(--ink); background: #fafbfe; border: 1px solid #e7eaf2; border-radius: 9px; font: inherit; font-size: 11px; line-height: 1.5; resize: vertical; }
.agent-edit-fields input:focus, .agent-edit-fields textarea:focus, .agent-modal input:focus, .agent-modal textarea:focus { outline: 3px solid rgb(89 101 245 / 15%); border-color: #9ea7ff; }
.agent-config-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.agent-option-section { min-width: 0; padding: 13px 15px 15px; }
.agent-option-section + .agent-option-section { border-left: 1px solid #f0f2f7; }
.agent-option-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 7px; color: #52607c; }
.agent-option-heading > span { display: flex; align-items: center; gap: 7px; font-size: 11px; font-weight: 800; }
.agent-option-heading svg { color: var(--blue); }
.agent-option-heading > b { color: #7d88a0; font-size: 9px; }
.agent-check-row { display: flex; align-items: flex-start; gap: 8px; min-width: 0; padding: 7px 1px; cursor: pointer; }
.agent-check-row input { width: 15px; height: 15px; flex: 0 0 auto; margin: 2px 0 0; accent-color: var(--blue); }
.agent-check-row > span { display: grid; min-width: 0; gap: 3px; }
.agent-check-row b { color: #4f5d79; font-size: 10px; }
.agent-check-row small { color: #929cb0; font-size: 9px; line-height: 1.4; }
.agent-upload-button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 34px; margin-top: 5px; padding: 0 10px; color: var(--blue); background: #f2f3ff; border: 1px solid #e7e9ff; border-radius: 9px; cursor: pointer; font-size: 10px; font-weight: 750; }
.agent-local-note { display: block; margin: 7px 0 0; color: #919bb0; font-size: 9px; line-height: 1.5; }
.agent-chat-card { overflow: hidden; }
.agent-chat-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 15px; border-bottom: 1px solid #f0f2f7; }
.agent-chat-header h3 { margin: 5px 0 0; font-size: 14px; }
.agent-chat-status { display: inline-flex; align-items: center; gap: 5px; color: #77839e; font-size: 9px; font-weight: 700; }
.agent-chat-status span { width: 6px; height: 6px; border-radius: 50%; background: #b7c0d0; }
.agent-chat-status span.connected { background: #30b887; }
.new-chat-button { min-height: 36px; font-size: 10px; }
.agent-chat-messages { display: grid; align-content: start; gap: 12px; max-height: 390px; min-height: 170px; overflow-y: auto; padding: 15px; background: #fcfcfe; }
.demo-chat-message { display: flex; width: 100%; min-width: 0; max-width: 100%; align-items: flex-start; gap: 8px; }
.demo-chat-message.user { justify-self: stretch; justify-content: flex-end; }
.demo-chat-message.assistant { justify-self: stretch; justify-content: flex-start; }
.demo-message-avatar { display: grid; width: 28px; height: 28px; flex: 0 0 auto; place-items: center; color: #fff; background: var(--blue); border-radius: 9px; }
.demo-message-body { box-sizing: border-box; min-width: 0; max-width: calc(100% - 36px); padding: 10px 12px; background: #fff; border: 1px solid #eceef5; border-radius: 4px 12px 12px; }
.demo-chat-message.user .demo-message-body { max-width: 94%; color: #fff; background: var(--blue); border-color: var(--blue); border-radius: 12px 4px 12px 12px; }
.demo-message-body > b { color: var(--blue); font-size: 9px; }
.demo-chat-message.user .demo-message-body > b { color: rgb(255 255 255 / 80%); }
.demo-message-body p { max-width: 100%; margin: 5px 0 0; color: #56627b; font-size: 11px; line-height: 1.7; white-space: pre-line; overflow-wrap: anywhere; }
.demo-chat-message.user .demo-message-body p { color: #fff; }
.demo-message-files { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 7px; }
.demo-message-files span { padding: 4px 6px; color: #5765df; background: #f0f1ff; border-radius: 6px; font-size: 9px; overflow-wrap: anywhere; }
.demo-message-actions { display: flex; gap: 2px; margin: 7px -5px -5px; }
.demo-message-actions .icon-button { width: 31px; height: 31px; }
.demo-thinking { display: flex; align-items: center; gap: 7px; color: #77839e; font-size: 10px; }
.thinking-dot { width: 7px; height: 7px; background: #6b76f4; border-radius: 50%; animation: pulse 1s ease-in-out infinite alternate; }
@keyframes pulse { to { opacity: .35; transform: scale(.82); } }
.demo-thinking .icon-button { width: 30px; height: 30px; }
.agent-chat-error { margin: 8px 15px 0; color: #b53c45; font-size: 11px; line-height: 1.55; }
.agent-chat-error button { margin-left: 4px; padding: 4px 8px; color: #4d5fe0; background: #f0f2ff; border: 0; border-radius: 7px; cursor: pointer; font: inherit; font-weight: 700; }
.pending-file-list { display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 13px 0; }
.pending-file-list > span { display: inline-flex; align-items: center; gap: 5px; max-width: 100%; padding: 5px 7px; color: #5f6c86; background: #f3f5fa; border-radius: 7px; font-size: 9px; overflow-wrap: anywhere; }
.pending-file-list button { display: grid; width: 20px; height: 20px; place-items: center; color: #7a859b; background: transparent; border: 0; border-radius: 6px; cursor: pointer; }
.agent-composer-live { display: grid; gap: 8px; margin: 11px 13px 0; padding: 10px; border: 1px solid #e7eaf2; border-radius: 12px; }
.agent-composer-live textarea { width: 100%; min-height: 54px; padding: 4px; color: var(--ink); background: transparent; border: 0; outline: none; font: inherit; font-size: 11px; line-height: 1.6; resize: vertical; }
.agent-composer-live textarea::placeholder { color: #9aa4b7; }
.agent-composer-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.agent-composer-options { display: flex; align-items: center; flex-wrap: wrap; gap: 5px; min-width: 0; }
.agent-composer-options .icon-button { width: 34px; height: 34px; }
.agent-count-chip { display: inline-flex; align-items: center; gap: 4px; min-height: 28px; padding: 0 7px; color: #687590; background: #f5f6fb; border: 1px solid #eceef5; border-radius: 8px; font-size: 9px; font-weight: 700; white-space: nowrap; }
.agent-send-button { min-height: 38px; }
.agent-send-button:disabled { opacity: .55; }
.visually-hidden-file { display: none; }
.agent-demo-footnote { margin: 8px 14px 12px; color: #929cb0; font-size: 9px; line-height: 1.5; }
.agent-local-notice { display: inline-flex; align-items: center; gap: 6px; width: fit-content; margin: 0; padding: 8px 11px; color: #247a65; background: #effaf6; border: 1px solid #d7f0e7; border-radius: 9px; font-size: 10px; }
.agent-modal-backdrop { position: fixed; z-index: 30; inset: 0; display: grid; place-items: center; padding: 18px; background: rgb(19 30 55 / 42%); }
.agent-modal { width: min(100%, 430px); max-height: min(90dvh, 690px); overflow: auto; padding: 20px; background: #fff; border: 1px solid var(--line); border-radius: 17px; box-shadow: 0 24px 70px rgb(15 26 52 / 24%); }
.agent-modal header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.agent-modal header .eyebrow { margin: 0 0 4px; color: var(--blue); }
.agent-modal h3 { margin: 0; font-size: 16px; }
.agent-modal form { display: grid; gap: 12px; }
.agent-modal input, .agent-modal textarea { min-height: 43px; font-size: 13px; }
.agent-form-error { margin: 0; color: #bd424a; font-size: 11px; }
.agent-delete-copy { color: #687590; font-size: 12px; line-height: 1.6; }
.agent-modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; }
.agent-modal-actions .button { min-height: 40px; }
.button-danger { color: #fff; background: #d94f59; }
.button-danger:hover { background: #c8404a; }

@media (max-width: 760px) {
  .demo-agent-studio { gap: 11px; }
  .agent-studio-intro { align-items: flex-start; }
  .agent-create-trigger { min-height: 40px; padding: 0 10px; font-size: 10px; }
  .agent-studio-layout { grid-template-columns: 1fr; gap: 10px; }
  .agent-list-card { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; padding: 9px; }
  .agent-list-heading { grid-column: 1 / -1; padding: 1px 3px; }
  .agent-list-item { min-height: 52px; padding: 6px; }
  .agent-list-icon { width: 30px; height: 30px; }
  .agent-list-item > svg { display: none; }
  .agent-add-card { grid-column: 1 / -1; }
  .agent-edit-fields { grid-template-columns: 1fr; gap: 9px; padding: 11px; }
  .agent-edit-fields input, .agent-edit-fields textarea { min-height: 42px; font-size: 13px; }
  .agent-config-header { padding: 12px; }
  .agent-config-grid { grid-template-columns: 1fr; }
  .agent-option-section { padding: 11px 12px; }
  .agent-option-section + .agent-option-section { border-top: 1px solid #f0f2f7; border-left: 0; }
  .agent-check-row { min-height: 39px; }
  .agent-check-row input { width: 18px; height: 18px; }
  .agent-upload-button { min-height: 42px; }
  .agent-chat-header { align-items: flex-start; padding: 11px 12px; }
  .new-chat-button { min-height: 40px; }
  .agent-chat-messages { min-height: 210px; max-height: 48dvh; padding: 12px; }
  .demo-chat-message { max-width: 100%; }
  .demo-message-body p { font-size: 12px; }
  .agent-composer-live { margin: 9px 10px 0; padding: 9px; }
  .agent-composer-live textarea { min-height: 62px; font-size: 16px; }
  .agent-send-button { min-height: 42px; padding: 0 10px; }
  .agent-count-chip { min-height: 30px; }
  .agent-demo-footnote { margin: 8px 11px 11px; }
  .agent-modal { padding: 17px; }
}

@media (prefers-reduced-motion: reduce) {
  .thinking-dot { animation: none; }
}
</style>
