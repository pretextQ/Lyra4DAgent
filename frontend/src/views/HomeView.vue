<template>
  <div class="workspace">
    <div class="content-col">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-brand">
          <span class="empty-logo">Lyra<span class="empty-logo-accent">4D</span></span>
        </div>
        <p class="empty-desc">描述你的需求，AI Agent 将为你雕琢精准的提示词</p>
      </div>

      <!-- 管线章节标记 -->
      <div v-if="messages.length > 0" class="pipeline">
        <div class="pipeline-track">
          <div class="pipeline-stage" :class="stageClass('define')">
            <span class="stage-code">D1</span>
            <span class="stage-label">定义</span>
          </div>
          <span class="pipeline-connector" />
          <div class="pipeline-stage" :class="stageClass('design')">
            <span class="stage-code">D2</span>
            <span class="stage-label">设计</span>
          </div>
          <span class="pipeline-connector" />
          <div class="pipeline-stage" :class="stageClass('develop')">
            <span class="stage-code">D3</span>
            <span class="stage-label">迭代</span>
          </div>
          <span class="pipeline-connector" />
          <div class="pipeline-stage" :class="stageClass('deliver')">
            <span class="stage-code">D4</span>
            <span class="stage-label">交付</span>
          </div>
        </div>
      </div>

      <!-- 消息列表：排版流 -->
      <div v-for="msg in messages" :key="msg.id" class="message-block fade-in">
        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="user-block">
          <div class="user-text">{{ msg.content }}</div>
          <div v-if="msg.mode" class="user-meta">
            <span class="meta-label">{{ msg.mode === 'detail' ? '详细模式' : '基础模式' }}</span>
            <span class="meta-label">{{ getTargetLabel(msg.targetAI) }}</span>
          </div>
          <div class="section-divider" />
        </div>

        <!-- AI 加载 -->
        <div v-else-if="msg.type === 'loading'" class="ai-loading">
          <span>{{ msg.content }}</span>
          <span class="loading-dots"><span>.</span><span>.</span><span>.</span></span>
        </div>

        <!-- AI 草稿审阅 -->
        <div v-else-if="msg.type === 'review'" class="ai-card review-card">
          <div class="card-edge"></div>
          <div class="card-body">
            <div class="card-header">
              <span class="card-title">{{ msg.content }}</span>
              <span class="score-stamp">{{ msg.score }}<small>/10</small></span>
            </div>

            <div class="draft-section">
              <div class="section-label">当前草稿</div>
              <div class="draft-text" v-html="renderMarkdown(msg.draft)" />
            </div>

            <div v-if="msg.improvementPoints?.length" class="improvements">
              <div class="section-label">改进建议</div>
              <ul class="improvement-list">
                <li v-for="(point, i) in msg.improvementPoints" :key="i">{{ point }}</li>
              </ul>
            </div>

            <div v-if="isLatestReview(msg.id)" class="feedback-area">
              <textarea
                v-model="feedbackText"
                class="feedback-input"
                placeholder="输入修改意见..."
                rows="2"
                @keydown.enter.ctrl="submitFeedback"
              />
              <div class="feedback-actions">
                <span class="input-hint">Ctrl + Enter 发送</span>
                <div class="feedback-buttons">
                  <button class="btn btn-ghost" :disabled="loading" @click="onPass">通过</button>
                  <button class="btn btn-primary" :disabled="loading || !feedbackText.trim()" @click="submitFeedback">
                    <span v-if="loading">处理中...</span>
                    <span v-else>提交反馈</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI 最终结果 -->
        <div v-else-if="msg.type === 'result'" class="ai-card result-card">
          <div class="card-edge"></div>
          <div class="card-body">
            <div class="card-header">
              <span class="card-title">优化完成</span>
              <div class="result-meta">
                <span class="meta-label">迭代 {{ msg.result.total_iterations }} 轮</span>
                <span class="meta-label score-label">评分 {{ msg.result.final_score }}/10</span>
              </div>
            </div>

            <div class="draft-section">
              <div class="section-label-row">
                <span class="section-label">最终提示词</span>
                <button class="btn-text" @click="copyPrompt(msg.result.final_prompt)">复制</button>
              </div>
              <div class="draft-text" v-html="renderMarkdown(msg.result.final_prompt)" />
            </div>

            <div v-if="msg.result.optimization_summary || msg.result.usage_tips" class="result-notes">
              <div v-if="msg.result.optimization_summary" class="note-item">
                <div class="section-label">优化总结</div>
                <p class="note-text">{{ msg.result.optimization_summary }}</p>
              </div>
              <div v-if="msg.result.usage_tips" class="note-item">
                <div class="section-label">使用技巧</div>
                <p class="note-text">{{ msg.result.usage_tips }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- AI 错误 -->
        <div v-else-if="msg.type === 'error'" class="ai-card error-card">
          <div class="card-edge"></div>
          <div class="card-body">
            <span class="error-text">{{ msg.content }}</span>
          </div>
        </div>

        <!-- AI 普通文本 -->
        <div v-else class="ai-text-block">{{ msg.content }}</div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div v-if="showSettings" class="input-options">
          <select v-model="form.mode" class="select-inline">
            <option value="detail">详细模式</option>
            <option value="basic">基础模式</option>
          </select>
          <span class="options-sep">&middot;</span>
          <select v-model="form.target_ai" class="select-inline">
            <option v-for="p in platforms" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </div>

        <div class="input-row">
          <textarea
            ref="inputRef"
            v-model="form.user_input"
            class="main-input"
            :placeholder="inputPlaceholder"
            rows="1"
            :disabled="loading"
            @keydown.enter.exact.prevent="onSubmit"
            @input="autoResize"
          />
          <button
            class="btn btn-primary send-btn"
            :disabled="loading || !form.user_input.trim()"
            @click="onSubmit"
          >
            雕琢 &rarr;
          </button>
        </div>

        <div class="input-footer">
          <button v-if="messages.length > 0" class="btn-text" @click="clearChat">清空对话</button>
          <span class="input-hint">Enter 发送 · Shift + Enter 换行</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { marked } from 'marked'
import { useOptimizeStore } from '../stores/optimize'

const store = useOptimizeStore()
const { messages, loading, error, interrupted, draft, draftScore, improvementPoints, interruptMessage } = storeToRefs(store)

const inputRef = ref(null)
const feedbackText = ref('')

const form = ref({
  user_input: '',
  mode: 'detail',
  target_ai: 'general',
})

const platforms = [
  { value: 'general', label: '通用' },
  { value: 'chatgpt', label: 'ChatGPT' },
  { value: 'claude', label: 'Claude' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'doubao', label: '豆包' },
]

const showSettings = computed(() => {
  return messages.value.length === 0 || !interrupted.value
})

const inputPlaceholder = computed(() => {
  if (loading.value) return 'AI 正在处理中...'
  if (interrupted.value) return '输入修改意见，或点击「通过」直接交付'
  return '描述你想要什么样的提示词...'
})

function getTargetLabel(value) {
  return platforms.find(p => p.value === value)?.label || value
}

function isLatestReview(msgId) {
  const reviewMessages = messages.value.filter(m => m.type === 'review')
  return reviewMessages.length > 0 && reviewMessages[reviewMessages.length - 1].id === msgId
}

function renderMarkdown(text) {
  return text ? marked(text) : ''
}

function autoResize(e) {
  const textarea = e.target
  textarea.style.height = 'auto'
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
}

// 管线阶段状态
const pipelineStage = ref('define')

function updatePipelineStage() {
  const reviewMsgs = messages.value.filter(m => m.type === 'review')
  const resultMsgs = messages.value.filter(m => m.type === 'result')

  if (resultMsgs.length > 0) {
    pipelineStage.value = 'deliver'
  } else if (reviewMsgs.length >= 2) {
    pipelineStage.value = 'develop'
  } else if (reviewMsgs.length === 1) {
    pipelineStage.value = 'design'
  } else {
    pipelineStage.value = 'define'
  }
}

function stageClass(stage) {
  const order = { define: 0, design: 1, develop: 2, deliver: 3 }
  const current = order[pipelineStage.value]
  const s = order[stage]

  if (s < current) return 'done'
  if (s === current) return 'active'
  return 'pending'
}

async function onSubmit() {
  if (loading.value || !form.value.user_input.trim()) return

  if (interrupted.value) {
    await store.doResume(form.value.user_input)
  } else {
    await store.doOptimize({ ...form.value })
  }
  updatePipelineStage()

  form.value.user_input = ''
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
      inputRef.value.focus()
    }
  })
}

async function submitFeedback() {
  if (loading.value || !feedbackText.value.trim()) return
  await store.doResume(feedbackText.value)
  updatePipelineStage()
  feedbackText.value = ''
}

async function onPass() {
  if (loading.value) return
  await store.doPass()
  updatePipelineStage()
}

function copyPrompt(text) {
  if (!text) return
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
  } else {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
}

function clearChat() {
  store.clearChat()
  form.value.user_input = ''
  feedbackText.value = ''
  pipelineStage.value = 'define'
}

onMounted(() => {
  inputRef.value?.focus()
})
</script>

<style scoped>
.workspace {
  flex: 1;
  display: flex;
  justify-content: center;
  overflow-y: auto;
  padding: var(--space-2xl) var(--space-lg);
}

.content-col {
  width: 100%;
  max-width: var(--content-width);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

.empty-brand {
  margin-bottom: var(--space-md);
}

.empty-logo {
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 500;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.empty-logo-accent {
  color: var(--accent);
}

.empty-desc {
  color: var(--text-secondary);
  font-size: 16px;
  font-family: var(--font-body);
}

/* 管线章节标记 */
.pipeline {
  margin-bottom: var(--space-xl);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--border-light);
}

.pipeline-track {
  display: flex;
  align-items: center;
  gap: 0;
}

.pipeline-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 10px;
  border-radius: var(--radius);
  transition: background-color 0.3s ease-out;
}

.pipeline-stage.done {
  background: var(--bg-surface);
}

.pipeline-stage.done .stage-code {
  color: var(--accent);
}

.pipeline-stage.done .stage-label {
  color: var(--text-secondary);
}

.pipeline-stage.active {
  background: var(--bg-raised);
  border-left: 3px solid var(--accent-warm);
}

.pipeline-stage.active .stage-code {
  color: var(--accent-warm);
  font-weight: 600;
}

.pipeline-stage.active .stage-label {
  color: var(--text-primary);
  font-weight: 500;
}

.pipeline-stage.pending .stage-code {
  color: var(--text-muted);
}

.pipeline-stage.pending .stage-label {
  color: var(--text-muted);
}

.stage-code {
  font-family: var(--font-mono);
  font-size: 13px;
}

.stage-label {
  font-size: 11px;
  font-family: var(--font-ui);
}

.pipeline-connector {
  flex: 1;
  height: 1px;
  background: var(--border-light);
  margin: 0 2px;
}

/* 消息排版流 */
.message-block {
  margin-bottom: var(--space-lg);
}

/* 用户消息 */
.user-block {
  margin-bottom: var(--space-md);
}

.user-text {
  font-family: var(--font-body);
  font-size: 18px;
  line-height: 1.7;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.user-meta {
  display: flex;
  gap: var(--space-sm);
}

.meta-label {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-ui);
  padding: 2px 8px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
}

.section-divider {
  margin-top: var(--space-md);
  height: 1px;
  background: var(--border-light);
}

/* AI 加载 */
.ai-loading {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--text-secondary);
  font-size: 14px;
  font-family: var(--font-body);
}

.loading-dots span {
  animation: dotPulse 1.4s ease-in-out infinite both;
  font-size: 20px;
  line-height: 1;
}

.loading-dots span:nth-child(1) { animation-delay: 0s; }
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotPulse {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}

/* AI 卡片（草稿/结果/错误） */
.ai-card {
  display: flex;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.card-edge {
  width: 3px;
  flex-shrink: 0;
  transition: background-color 0.5s ease-in-out;
}

.review-card .card-edge { background: var(--accent); }
.result-card .card-edge { background: var(--success); }
.error-card .card-edge { background: var(--error); }

.card-body {
  flex: 1;
  padding: var(--space-md) var(--space-lg);
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.card-title {
  font-family: var(--font-ui);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.score-stamp {
  font-family: var(--font-body);
  font-size: 20px;
  font-weight: 500;
  color: var(--accent-warm);
}

.score-stamp small {
  font-size: 12px;
  color: var(--text-muted);
}

/* 草稿内容 */
.draft-section {
  margin-bottom: var(--space-md);
}

.section-label {
  font-family: var(--font-ui);
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: var(--space-sm);
}

.section-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.draft-text {
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 360px;
  overflow-y: auto;
}

.draft-text :deep(h1),
.draft-text :deep(h2),
.draft-text :deep(h3) {
  font-family: var(--font-body);
  color: var(--text-primary);
  margin: 12px 0 6px;
}

.draft-text :deep(h1) { font-size: 18px; }
.draft-text :deep(h2) { font-size: 16px; }
.draft-text :deep(h3) { font-size: 15px; }

.draft-text :deep(code) {
  font-family: var(--font-mono);
  font-size: 13px;
  background: var(--bg-surface);
  padding: 2px 6px;
  border-radius: var(--radius);
}

.draft-text :deep(strong) {
  color: var(--accent);
}

/* 改进建议 */
.improvements {
  margin-bottom: var(--space-md);
}

.improvement-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.improvement-list li {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-secondary);
  padding: 6px 0;
  border-bottom: 1px solid var(--border-light);
}

.improvement-list li:last-child {
  border-bottom: none;
}

.improvement-list li::before {
  content: "→ ";
  color: var(--accent-warm);
}

/* 反馈区 */
.feedback-area {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-light);
}

.feedback-input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-page);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  transition: border-color 0.15s;
}

.feedback-input:focus {
  outline: none;
  border-color: var(--accent);
}

.feedback-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: var(--space-sm);
}

.feedback-buttons {
  display: flex;
  gap: var(--space-sm);
}

/* 结果卡片 */
.result-meta {
  display: flex;
  gap: var(--space-sm);
}

.score-label {
  color: var(--success);
  border-color: var(--success);
}

.result-notes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}

.note-item {
  background: var(--bg-page);
  padding: var(--space-md);
  border-radius: var(--radius);
}

.note-text {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 错误卡片 */
.error-text {
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--error);
}

/* AI 文本块 */
.ai-text-block {
  font-family: var(--font-body);
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.7;
}

/* 输入区域 */
.input-area {
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border);
}

.input-options {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.select-inline {
  background: none;
  border: none;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 12px;
  cursor: pointer;
  padding: 2px 4px;
}

.select-inline:focus {
  outline: none;
  color: var(--text-primary);
}

.options-sep {
  color: var(--border);
  font-size: 12px;
}

.input-row {
  display: flex;
  gap: var(--space-md);
  align-items: flex-start;
}

.main-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 15px;
  line-height: 1.5;
  resize: none;
  min-height: 24px;
  max-height: 160px;
  padding: 4px 0;
}

.main-input:focus {
  outline: none;
}

.main-input::placeholder {
  color: var(--text-muted);
  font-family: var(--font-body);
  font-style: italic;
}

.main-input:disabled {
  opacity: 0.5;
}

.send-btn {
  padding: 8px 18px;
  font-size: 14px;
  flex-shrink: 0;
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: var(--space-sm);
}

.btn-text {
  background: none;
  border: none;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 12px;
  cursor: pointer;
  padding: 2px 4px;
  transition: color 0.15s;
}

.btn-text:hover {
  color: var(--text-secondary);
}

.input-hint {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-ui);
}

/* 响应式 */
@media (max-width: 768px) {
  .workspace {
    padding: var(--space-lg) var(--space-md);
  }

  .result-notes {
    grid-template-columns: 1fr;
  }
}
</style>
