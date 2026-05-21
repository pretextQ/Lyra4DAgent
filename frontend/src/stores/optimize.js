import { defineStore } from 'pinia'
import { ref, nextTick } from 'vue'
import { optimize, resumeOptimize, getHistory } from '../api'

export const useOptimizeStore = defineStore('optimize', () => {
  // 对话消息列表
  const messages = ref([])
  const loading = ref(false)
  const history = ref([])
  const error = ref('')

  // 人类介入状态
  const interrupted = ref(false)
  const threadId = ref('')
  const draft = ref('')
  const draftScore = ref(0)
  const improvementPoints = ref([])
  const interruptMessage = ref('')

  // 滚动到底部
  async function scrollToBottom() {
    await nextTick()
    const container = document.querySelector('.chat-messages')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  }

  // 添加消息
  function addMessage(msg) {
    messages.value.push({
      id: Date.now() + Math.random(),
      timestamp: new Date().toLocaleTimeString(),
      ...msg,
    })
    scrollToBottom()
  }

  function _clearInterrupt() {
    interrupted.value = false
    threadId.value = ''
    draft.value = ''
    draftScore.value = 0
    improvementPoints.value = []
    interruptMessage.value = ''
  }

  // 优化
  async function doOptimize(form) {
    loading.value = true
    error.value = ''
    _clearInterrupt()

    // 添加用户消息
    addMessage({
      role: 'user',
      content: form.user_input,
      mode: form.mode,
      targetAI: form.target_ai,
    })

    // 添加 AI 处理中消息
    const aiMsgId = Date.now() + Math.random()
    addMessage({
      id: aiMsgId,
      role: 'ai',
      type: 'loading',
      content: '正在分析需求、检索知识、生成提示词...',
    })

    try {
      const data = await optimize(form)

      // 移除 loading 消息
      messages.value = messages.value.filter(m => m.id !== aiMsgId)

      if (data.status === 'interrupted') {
        interrupted.value = true
        threadId.value = data.thread_id
        draft.value = data.draft
        draftScore.value = data.score
        improvementPoints.value = data.improvement_points || []
        interruptMessage.value = data.message

        // 添加草稿审阅消息
        addMessage({
          role: 'ai',
          type: 'review',
          content: data.message || '草稿已生成，请审阅',
          draft: data.draft,
          score: data.score,
          improvementPoints: data.improvement_points || [],
        })
      } else {
        // 添加最终结果消息
        addMessage({
          role: 'ai',
          type: 'result',
          content: '优化完成！',
          result: data,
        })
      }
    } catch (e) {
      messages.value = messages.value.filter(m => m.id !== aiMsgId)
      error.value = e.message || '优化请求失败'
      addMessage({
        role: 'ai',
        type: 'error',
        content: error.value,
      })
    } finally {
      loading.value = false
    }
  }

  // 恢复被中断的优化
  async function doResume(feedback) {
    loading.value = true
    interrupted.value = false
    error.value = ''

    // 添加用户反馈消息
    addMessage({
      role: 'user',
      content: feedback,
      isFeedback: true,
    })

    // 添加 AI 处理中消息
    const aiMsgId = Date.now() + Math.random()
    addMessage({
      id: aiMsgId,
      role: 'ai',
      type: 'loading',
      content: '正在处理反馈、继续优化...',
    })

    try {
      const data = await resumeOptimize(threadId.value, feedback)

      // 移除 loading 消息
      messages.value = messages.value.filter(m => m.id !== aiMsgId)

      if (data.status === 'interrupted') {
        interrupted.value = true
        threadId.value = data.thread_id
        draft.value = data.draft
        draftScore.value = data.score
        improvementPoints.value = data.improvement_points || []
        interruptMessage.value = data.message

        addMessage({
          role: 'ai',
          type: 'review',
          content: data.message || '草稿已更新，请再次审阅',
          draft: data.draft,
          score: data.score,
          improvementPoints: data.improvement_points || [],
        })
      } else {
        addMessage({
          role: 'ai',
          type: 'result',
          content: '优化完成！',
          result: data,
        })
        _clearInterrupt()
      }
    } catch (e) {
      messages.value = messages.value.filter(m => m.id !== aiMsgId)
      error.value = e.message || '恢复请求失败'
      addMessage({
        role: 'ai',
        type: 'error',
        content: error.value,
      })
    } finally {
      loading.value = false
    }
  }

  // 直接通过草稿
  async function doPass() {
    await doResume('通过')
  }

  // 清空对话
  function clearChat() {
    messages.value = []
    _clearInterrupt()
    error.value = ''
  }

  // 加载历史
  async function loadHistory() {
    try {
      history.value = await getHistory()
    } catch (e) {
      console.error('加载历史失败:', e)
    }
  }

  return {
    messages, loading, history, error,
    interrupted, threadId, draft, draftScore, improvementPoints, interruptMessage,
    doOptimize, doResume, doPass, clearChat, loadHistory,
  }
})
