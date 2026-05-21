<template>
  <div class="history">
    <h1 class="page-title">优化历史</h1>

    <div v-if="history.length === 0" class="empty card">
      <p>暂无历史记录</p>
      <router-link to="/" class="btn btn-ghost">去优化</router-link>
    </div>

    <div v-else class="history-list">
      <div v-for="item in history" :key="item.id" class="history-item card fade-in">
        <div class="item-header">
          <span class="item-intent">{{ item.core_intent || item.user_input }}</span>
          <div class="item-meta">
            <span class="meta-tag">{{ item.total_iterations }} 轮</span>
            <span class="meta-tag score">{{ item.final_score }}/10</span>
          </div>
        </div>
        <p class="item-preview">{{ truncate(item.final_prompt, 150) }}</p>
        <div class="item-footer">
          <span class="item-time">{{ formatTime(item.created_at) }}</span>
          <button class="btn btn-ghost btn-sm" @click="copyPrompt(item.final_prompt)">复制</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useOptimizeStore } from '../stores/optimize'

const store = useOptimizeStore()
const { history } = storeToRefs(store)

onMounted(() => {
  store.loadHistory()
})

function truncate(text, len) {
  return text?.length > len ? text.slice(0, len) + '...' : text
}

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString('zh-CN')
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
</script>

<style scoped>
.page-title {
  font-family: var(--font-body);
  font-size: 22px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-lg);
}

.empty {
  text-align: center;
  padding: 60px 24px;
  color: var(--text-secondary);
  font-family: var(--font-body);
}

.empty p {
  margin-bottom: var(--space-lg);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.history-item {
  transition: border-color 0.15s;
}

.history-item:hover {
  border-color: var(--accent);
}

.item-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.item-intent {
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 15px;
  color: var(--text-primary);
}

.item-meta {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.meta-tag {
  padding: 2px 10px;
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.meta-tag.score {
  color: var(--success);
}

.item-preview {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: var(--space-sm);
}

.item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.item-time {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}
</style>
