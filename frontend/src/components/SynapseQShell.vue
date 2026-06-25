<script setup>
import { ref, watch, computed } from 'vue';
import { Menu, Database, X, Shield, MessageSquare, Plus, Trash2, LogOut } from 'lucide-vue-next';

const props = defineProps({
  themeColor: { type: String, default: 'blue' },
  currentUser: { type: Object, required: true },
  headerTitle: { type: String, required: true },
  headerBadge: { type: String, default: '' },
  conversationHistory: { type: Array, default: () => [] },
  currentConversationId: { type: String, default: '' },
  messages: { type: Array, default: () => [] },
  rightPanelContent: { type: Object, default: null },
  exampleQuestions: { type: Array, default: () => [] },
  welcomeTitle: { type: String, default: '欢迎使用 SynapseQ' },
  welcomeDescription: { type: String, default: '我是SynapseQ智能助手，有什么可以帮您的吗？' }
});

const emit = defineEmits(['send-message', 'new-conversation', 'switch-conversation', 'delete-conversation', 'logout']);

const inputText = ref('');
const sidebarOpen = ref(true);
const rightPanelOpen = ref(true);
const messagesEndRef = ref(null);

watch(
  () => props.messages,
  () => {
    requestAnimationFrame(() => {
      messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' });
    });
  },
  { deep: true }
);

const themeStyles = computed(() => ({
  sidebarBg: 'bg-slate-900',
  avatarBg:
    props.themeColor === 'green'
      ? 'bg-green-600'
      : props.themeColor === 'purple'
        ? 'bg-purple-600'
        : 'bg-blue-600',
  botMsgBg:
    props.themeColor === 'green'
      ? 'bg-green-600'
      : props.themeColor === 'purple'
        ? 'bg-purple-600'
        : 'bg-blue-600',
  headerBadgeBorder:
    props.themeColor === 'green'
      ? 'border-green-100'
      : props.themeColor === 'purple'
        ? 'border-purple-100'
        : 'border-blue-100',
  headerBadgeBg:
    props.themeColor === 'green'
      ? 'bg-green-50'
      : props.themeColor === 'purple'
        ? 'bg-purple-50'
        : 'bg-blue-50',
  headerBadgeText:
    props.themeColor === 'green'
      ? 'text-green-700'
      : props.themeColor === 'purple'
        ? 'text-purple-700'
        : 'text-blue-700',
  headerBadgeDot:
    props.themeColor === 'green'
      ? 'bg-green-500'
      : props.themeColor === 'purple'
        ? 'bg-purple-500'
        : 'bg-blue-500'
}));

const handleSend = () => {
  if (!inputText.value.trim()) return;
  emit('send-message', inputText.value.trim());
  inputText.value = '';
};

const handleExampleClick = (question) => {
  emit('send-message', question);
};

const formatContent = (text) => {
  if (!text) return '';
  let formatted = text;

  // 1. 基础 Markdown 加粗
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="text-cyan-400">$1</strong>');

  // 2. 核心：检测并智能拆分大模型的“思维链”四大板块
  const hasCoT = /1\.\s*意图解析[：:]/i.test(formatted);
  if (hasCoT) {
    formatted = formatted
      // 替换第一部分：意图解析
      .replace(/1\.\s*意图解析[：:](.*?)(?=2\.\s*数据提取与核对[：:]|$)/is, 
        '<div class="mb-3 bg-slate-900 border border-slate-700 rounded-lg overflow-hidden"><div class="px-3 py-1.5 bg-slate-800 border-b border-slate-700 text-[10px] text-slate-400 font-mono flex items-center gap-2"><div class="w-1.5 h-1.5 rounded-full bg-blue-500"></div> STEP 01: 意图解析 (INTENT)</div><div class="p-3 text-[13px] text-slate-300 leading-relaxed">$1</div></div>')
      // 替换第二部分：数据提取与核对
      .replace(/2\.\s*数据提取与核对[：:](.*?)(?=3\.\s*隐私边界检查[：:]|$)/is, 
        '<div class="mb-3 bg-slate-900 border border-slate-700 rounded-lg overflow-hidden"><div class="px-3 py-1.5 bg-slate-800 border-b border-slate-700 text-[10px] text-slate-400 font-mono flex items-center gap-2"><div class="w-1.5 h-1.5 rounded-full bg-purple-500"></div> STEP 02: 数据提取 (EXTRACTION)</div><div class="p-3 text-[13px] text-slate-300 leading-relaxed">$1</div></div>')
      // 替换第三部分：隐私边界检查
      .replace(/3\.\s*隐私边界检查[：:](.*?)(?=4\.\s*回复构建[：:]|$)/is, 
        '<div class="mb-3 bg-slate-900 border border-slate-700 rounded-lg overflow-hidden"><div class="px-3 py-1.5 bg-slate-800 border-b border-slate-700 text-[10px] text-slate-400 font-mono flex items-center gap-2"><div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> STEP 03: 隐私校验 (PRIVACY CHECK)</div><div class="p-3 text-[13px] text-slate-300 leading-relaxed">$1</div></div>')
      // 替换第四部分：最终回复（高亮显示）
      .replace(/4\.\s*回复构建[：:](.*)/is, 
        '<div class="mt-4 pt-4 border-t border-slate-700/80"><div class="text-[11px] text-cyan-500 font-mono mb-2 uppercase tracking-widest flex items-center gap-2"><div class="w-1.5 h-1.5 rounded-full bg-cyan-500 shadow-[0_0_5px_#06b6d4] animate-pulse"></div> 最终生成结果 (FINAL OUTPUT)</div><div class="text-[15px] font-bold text-slate-200 leading-relaxed">$1</div></div>');
  } else {
    // 如果大模型回答的是普通话语（没有这4个步骤），就只做基本的换行处理
    formatted = formatted.replace(/\n/g, '<br>');
  }

  return formatted;
};
const showWelcome = computed(() => {
  // 只有当完全没有消息时才显示欢迎页面
  return props.messages.length === 0;
});
</script>

<template>
  <div class="flex h-full bg-slate-950 font-sans text-slate-300 overflow-hidden p-3 gap-3">
    
    <aside :class="`${sidebarOpen ? 'w-64' : 'w-0 opacity-0'} flex-shrink-0 bg-slate-900 rounded-2xl border border-slate-800 flex flex-col transition-all duration-300 overflow-hidden z-20 shadow-2xl`">
      
      <div class="p-5 border-b border-slate-800 flex items-center gap-3 bg-slate-950/50">
        <div class="w-8 h-8 rounded-lg bg-cyan-600 flex items-center justify-center text-white font-black text-xs shadow-[0_0_15px_rgba(8,145,178,0.4)]">
          SQ
        </div>
        <span class="font-black text-white tracking-widest uppercase text-sm">Terminal</span>
      </div>

      <div class="flex-1 overflow-y-auto py-4 flex flex-col">
        <div class="px-4 mb-4">
          <button @click="emit('new-conversation')" class="w-full py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-cyan-400 text-sm font-bold flex items-center justify-center gap-2 transition-all">
            <Plus size="16" /> 新建查询进程
          </button>
        </div>
        
        <div class="px-5 mb-2 text-[10px] font-mono text-slate-500 uppercase tracking-widest">
          Session History
        </div>
        
        <nav class="space-y-1 px-3 flex-1">
          <div v-for="conversation in conversationHistory" :key="conversation.id" class="group relative">
            <button @click="emit('switch-conversation', conversation.id)"
              class="w-full text-left px-3 py-2.5 rounded-xl flex items-center gap-3 transition-colors text-sm"
              :class="currentConversationId === conversation.id ? 'bg-cyan-900/30 text-cyan-400 border border-cyan-800/50 font-bold' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'">
              <MessageSquare size="14" class="flex-shrink-0" />
              <span class="truncate flex-1">{{ conversation.title || '新对话' }}</span>
            </button>
            <button @click.stop="emit('delete-conversation', conversation.id)" class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-slate-800 opacity-0 group-hover:opacity-100 transition-all">
              <Trash2 size="14" />
            </button>
          </div>
          <div v-if="conversationHistory.length === 0" class="px-3 py-6 text-center text-slate-600 text-xs font-mono">
            [ NO RECORDS ]
          </div>
        </nav>
      </div>

      <div class="p-4 border-t border-slate-800 bg-slate-950/30">
        <div class="flex items-center gap-3 mb-4 px-1">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-white text-sm font-black border border-slate-600">
            {{ currentUser.avatar }}
          </div>
          <div class="flex-1 overflow-hidden">
            <div class="font-bold text-sm text-slate-200 truncate">{{ currentUser.name }}</div>
            <div class="text-[10px] text-cyan-500 font-mono tracking-tight">{{ currentUser.role }}</div>
          </div>
        </div>
        <button @click="emit('logout')" class="w-full px-3 py-2.5 rounded-xl text-slate-400 hover:text-red-400 hover:bg-red-950/50 hover:border-red-900/50 border border-transparent text-sm font-bold flex items-center justify-center gap-2 transition-all">
          <LogOut size="16" /> 退出登录
        </button>
      </div>
    </aside>

    <main class="flex-1 bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 flex flex-col min-w-0 relative z-10 overflow-hidden">
      
      <header class="h-14 border-b border-slate-800 flex items-center justify-between px-4 bg-slate-950/50 backdrop-blur z-20 shrink-0">
        <div class="flex items-center gap-3">
          <button @click="sidebarOpen = !sidebarOpen" class="p-1.5 text-slate-400 hover:text-cyan-400 hover:bg-slate-800 rounded-lg transition-colors">
            <Menu size="18" />
          </button>
          <div class="h-4 w-px bg-slate-700 mx-1"></div>
          <h1 class="font-bold text-slate-200 text-sm tracking-wide">{{ headerTitle }}</h1>
          <span class="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-900/30 border border-emerald-800 text-emerald-400 uppercase">
            <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
            {{ headerBadge }}
          </span>
        </div>
        
        <button @click="rightPanelOpen = !rightPanelOpen" class="p-1.5 flex items-center gap-2 text-slate-400 hover:text-cyan-400 hover:bg-slate-800 rounded-lg transition-colors" :class="rightPanelOpen ? 'bg-slate-800 text-cyan-400' : ''">
          <Database size="16" />
          <span class="text-xs font-mono hidden sm:block">STATUS_PANEL</span>
        </button>
      </header>

      <div class="flex-1 overflow-y-auto p-4 md:p-6 scroll-smooth bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800/20 via-slate-900 to-slate-900 relative">
        
        <div v-if="showWelcome" class="h-full flex items-center justify-center">
          <div class="max-w-xl text-center space-y-6">
            <div class="w-16 h-16 mx-auto rounded-2xl bg-slate-800 flex items-center justify-center border border-slate-700 shadow-[0_0_30px_rgba(8,145,178,0.15)]">
              <Sparkles class="w-8 h-8 text-cyan-400" />
            </div>
            <div>
              <h2 class="text-2xl font-black text-slate-200 mb-2 tracking-tight">{{ welcomeTitle }}</h2>
              <p class="text-slate-500 text-sm font-mono">{{ welcomeDescription }}</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4">
              <button v-for="q in exampleQuestions" :key="q" @click="handleExampleClick(q)" class="text-left p-4 rounded-xl border border-slate-700 hover:border-cyan-500 hover:bg-slate-800/50 transition-all group bg-slate-900 shadow-inner">
                <div class="text-sm font-medium text-slate-300 group-hover:text-cyan-400">{{ q }}</div>
                <div class="text-[10px] text-slate-500 mt-2 font-mono flex items-center justify-between">
                  EXEC QUERY <ChevronRight size="12" class="opacity-0 group-hover:opacity-100 transition-opacity text-cyan-500" />
                </div>
              </button>
            </div>
          </div>
        </div>

        <div v-else class="space-y-6 max-w-4xl mx-auto pb-2">
          <div v-for="msg in messages" :key="msg.id" class="flex w-full" :class="msg.sender === 'user' ? 'justify-end' : 'justify-start'">
            
            <div v-if="msg.sender === 'user'" class="flex gap-3 max-w-[85%] flex-row-reverse">
              <div class="w-8 h-8 rounded-lg bg-slate-800 flex-shrink-0 flex items-center justify-center text-slate-400 text-xs font-bold border border-slate-700">
                USR
              </div>
              <div class="bg-slate-800 border border-slate-700 text-slate-200 px-5 py-3 rounded-2xl rounded-tr-sm shadow-md text-[14px] leading-relaxed">
                <div v-html="formatContent(msg.content)" />
              </div>
            </div>

            <div v-else class="flex gap-3 max-w-[90%]">
              <div class="w-8 h-8 rounded-lg bg-cyan-900/50 flex-shrink-0 flex items-center justify-center text-cyan-400 text-xs font-bold border border-cyan-800/50">
                SQ
              </div>
              <div class="space-y-2">
                <div class="bg-slate-950 border border-slate-800 border-l-2 border-l-cyan-500 text-slate-300 px-5 py-4 rounded-2xl rounded-tl-sm shadow-lg text-[14px] leading-relaxed">
                  <div v-html="formatContent(msg.content)" />
                </div>
                
                <div v-if="msg.sources?.length" class="flex flex-wrap gap-2 pt-1">
                  <div v-for="(src, idx) in msg.sources" :key="idx" class="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-[11px] text-slate-400 cursor-pointer hover:border-cyan-500 hover:text-cyan-400 transition-colors">
                    <component :is="src.icon" class="w-3 h-3" />
                    <span class="font-mono font-bold text-slate-500">[{{ src.label }}]</span>
                    <span class="truncate max-w-[150px]">{{ src.title }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div ref="messagesEndRef" class="h-1" />
        </div>
      </div>

      <div class="p-4 bg-slate-900 border-t border-slate-800">
        <div class="max-w-4xl mx-auto relative flex items-end gap-2 bg-slate-950 border border-slate-700 rounded-2xl focus-within:border-cyan-500 focus-within:ring-1 focus-within:ring-cyan-500 transition-all p-1 shadow-inner">
          <textarea v-model="inputText" @keydown.enter.prevent="!$event.shiftKey && handleSend()"
            placeholder="[输入系统指令...] Shift+Enter 换行"
            class="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 resize-none text-[14px] text-slate-200 px-4 py-3 min-h-[44px] max-h-[160px] placeholder-slate-600 font-mono" rows="1" />
          <button @click="handleSend" :disabled="!inputText.trim()"
            class="flex-shrink-0 w-10 h-10 bg-cyan-600 text-white rounded-xl flex items-center justify-center hover:bg-cyan-500 transition-colors shadow-[0_0_10px_rgba(8,145,178,0.3)] disabled:opacity-30 disabled:shadow-none mb-0.5 mr-0.5">
            <svg viewBox="0 0 24 24" class="w-5 h-5 ml-0.5" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </main>

    <aside :class="`${rightPanelOpen ? 'w-80 opacity-100' : 'w-0 opacity-0'} flex-shrink-0 bg-slate-900 rounded-2xl border border-slate-800 transition-all duration-300 overflow-hidden flex flex-col z-20 shadow-2xl`">
      <div class="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/50">
        <h3 class="font-black text-cyan-500 text-[11px] uppercase tracking-widest flex items-center gap-2">
          <Database size="14" />
          System Metrics
        </h3>
        <button @click="rightPanelOpen = false" class="p-1 text-slate-500 hover:text-slate-200 hover:bg-slate-800 rounded transition-colors">
          <X size="14" />
        </button>
      </div>
      
      <div class="p-4 flex-1 overflow-y-auto custom-scrollbar">
        <slot name="right-panel">
          <div class="text-sm text-gray-500">右侧内容未提供</div>
        </slot>
      </div>
    </aside>

  </div>
</template>

<style scoped>
/* 自定义极客风滚动条 */
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #06b6d4; }
</style>