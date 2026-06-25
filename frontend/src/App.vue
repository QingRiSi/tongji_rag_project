<script setup>
import { ref, onMounted, computed } from 'vue';
import {
  Send,
  User,
  BookOpen,
  Calendar,
  Clock,
  Shield,
  Search,
  Menu,
  Database,
  X,
  Sparkles,
  Globe,
  Map,
  FileText,
  AlertCircle,
  LogIn,
  ChevronRight
} from 'lucide-vue-next';
import SynapseQShell from './components/SynapseQShell.vue';
import { authAPI, sessionAPI, chatAPI, getUserInfo, isAuthenticated } from './api/api.js';

const showLogin = ref(true);
const loggingIn = ref(false);
const loginError = ref('');
const loginForm = ref({ email: '', password: '' });
const rememberLogin = ref(false);
const rememberPassword = ref(false);

const currentMode = ref('visitor'); // visitor | scholar | student | denied
const currentUserInfo = ref(null); // 存储当前登录用户信息

// Type管理系统
const currentType = ref('public'); // 当前选择的type: public | academic | internal | personal
const typeConfig = {
  public: {
    label: '公开',
    description: '校务公开/FAQ',
    icon: Globe,
    color: 'green',
    badge: 'Standard 库已连接',
    title: '访客通道 (Public Access)'
  },
  academic: {
    label: '学术',
    description: '文献/知识库',
    icon: BookOpen,
    color: 'purple',
    badge: 'Knowledge 库已连接',
    title: '学术科研模式 (Academic Mode)'
  },
  internal: {
    label: '内部',
    description: '通知/办事',
    icon: FileText,
    color: 'blue',
    badge: 'Internal 库已连接',
    title: '校内服务通道 (Campus Services)'
  },
  personal: {
    label: '个人',
    description: '画像/推荐',
    icon: User,
    color: 'orange',
    badge: 'Personal 库已连接',
    title: '个人服务 (Personal Services)'
  }
};

// 根据用户角色获取可用的type列表
const getAvailableTypes = (role) => {
  const roleLower = (role || '').toLowerCase();
  const types = ['public']; // 所有人都可以访问public
  
  if (roleLower.includes('scholar') || roleLower.includes('visiting') || 
      roleLower.includes('student') || roleLower.includes('teacher')) {
    types.push('academic');
  }
  
  if (roleLower.includes('student') || roleLower.includes('teacher')) {
    types.push('internal', 'personal');
  }
  
  return types;
};

// 统一的会话和消息存储（按type管理）
const typeSessions = ref({
  public: { conversations: [], currentId: '', messages: [] },
  academic: { conversations: [], currentId: '', messages: [] },
  internal: { conversations: [], currentId: '', messages: [] },
  personal: { conversations: [], currentId: '', messages: [] }
});

// 当前可用type列表
const availableTypes = computed(() => {
  if (!currentUserInfo.value) {
    return ['public']; // 未登录只能访问public
  }
  const role = currentUserInfo.value.role || '';
  return getAvailableTypes(role);
});

// 当前type的会话和消息（计算属性）
const currentConversations = computed(() => {
  const type = currentType.value;
  if (!typeSessions.value[type]) {
    typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
  }
  return typeSessions.value[type]?.conversations || [];
});

const currentMessages = computed(() => {
  const type = currentType.value;
  if (!typeSessions.value[type]) {
    typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
  }
  return typeSessions.value[type]?.messages || [];
});

const currentConversationId = computed({
  get: () => {
    const type = currentType.value;
    if (!typeSessions.value[type]) {
      typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
    }
    return typeSessions.value[type]?.currentId || '';
  },
  set: (val) => {
    const type = currentType.value;
    if (!typeSessions.value[type]) {
      typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
    }
    if (typeSessions.value[type]) {
      typeSessions.value[type].currentId = val;
    }
  }
});

// 当前type的配置
const currentTypeConfig = computed(() => {
  return typeConfig[currentType.value] || typeConfig.public;
});

// 辅助函数：获取示例问题
const getExampleQuestions = (type) => {
  const questions = {
    public: ['嘉定校区图书馆在哪里？', '四平路校区地图', '校车时刻表(仅公开版)', '2025本科招生简章'],
    academic: ['汽车学院在自动驾驶领域最近有什么发表？', '查找IEEE关于机器学习的论文', 'CNKI中关于人工智能的最新研究', '同济大学2024年科研年报'],
    internal: ['嘉定校区图书馆几点关门？', '查看我今天有什么课程', '我的高数成绩是多少？', '校园卡余额查询'],
    personal: ['我的选课信息', '个人成绩单', '我的课程表', '个人推荐内容']
  };
  return questions[type] || questions.public;
};

// 辅助函数：获取热门问题
const getPopularQuestions = (type) => {
  const questions = {
    public: ['同济大学的校训是什么？', '同济大学创建于哪一年？', '同济大学是"985""211"高校吗？', '同济大学的土木工程在全国处于什么水平？'],
    academic: [],
    internal: [],
    personal: []
  };
  return questions[type] || [];
};

// 辅助函数：获取欢迎标题
const getWelcomeTitle = (type) => {
  if (type === 'personal' || type === 'internal') {
    return `欢迎回来，${currentUser.value.name}！`;
  }
  return `欢迎使用 SynapseQ ${typeConfig[type]?.label || ''}`;
};

// 辅助函数：获取连接的集合
const getConnectedCollections = (type) => {
  const collections = {
    public: [{ name: 'Standard (公开)', color: 'green', access: 'Read' }],
    academic: [
      { name: 'Standard (公开)', color: 'green', access: 'Read' },
      { name: 'Knowledge (学术)', color: 'purple', access: 'Read' }
    ],
    internal: [
      { name: 'Standard (公开)', color: 'green', access: 'Read' },
      { name: 'Internal (内部)', color: 'blue', access: 'Read' },
      { name: 'Person_info (个人)', color: 'orange', access: 'Private' }
    ],
    personal: [
      { name: 'Standard (公开)', color: 'green', access: 'Read' },
      { name: 'Person_info (个人)', color: 'orange', access: 'Private' }
    ]
  };
  return collections[type] || collections.public;
};

// 获取type按钮的class
const getTypeButtonClass = (type) => {
  const baseClass = 'px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 flex-shrink-0';
  if (currentType.value === type) {
    const color = typeConfig[type].color;
    const colorClasses = {
      green: 'bg-green-100 text-green-700 border-2 border-green-300 shadow-sm',
      purple: 'bg-purple-100 text-purple-700 border-2 border-purple-300 shadow-sm',
      blue: 'bg-blue-100 text-blue-700 border-2 border-blue-300 shadow-sm',
      orange: 'bg-orange-100 text-orange-700 border-2 border-orange-300 shadow-sm'
    };
    return `${baseClass} ${colorClasses[color] || colorClasses.blue}`;
  }
  return `${baseClass} bg-gray-50 text-gray-600 hover:bg-gray-100 border-2 border-transparent`;
};

// 获取右侧面板渐变背景class
const getRightPanelGradientClass = () => {
  const color = currentTypeConfig.value.color;
  const gradients = {
    green: 'bg-gradient-to-br from-green-500 to-emerald-600',
    purple: 'bg-gradient-to-br from-purple-500 to-pink-600',
    blue: 'bg-gradient-to-br from-blue-500 to-indigo-600',
    orange: 'bg-gradient-to-br from-orange-500 to-amber-600'
  };
  return `${gradients[color] || gradients.blue} rounded-xl p-4 text-white shadow-lg relative overflow-hidden`;
};

// 获取集合项的class
const getCollectionItemClass = (color) => {
  const classes = {
    green: 'flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-100',
    purple: 'flex items-center justify-between p-3 bg-purple-50 rounded-lg border border-purple-100',
    blue: 'flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-100',
    orange: 'flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-100'
  };
  return classes[color] || classes.green;
};

// 获取集合点的class
const getCollectionDotClass = (color) => {
  const classes = {
    green: 'w-2 h-2 rounded-full bg-green-500',
    purple: 'w-2 h-2 rounded-full bg-purple-500',
    blue: 'w-2 h-2 rounded-full bg-blue-500',
    orange: 'w-2 h-2 rounded-full bg-orange-500'
  };
  return classes[color] || classes.green;
};

// 获取热门问题按钮的class
const getPopularQuestionButtonClass = () => {
  const color = currentTypeConfig.value.color;
  const classes = {
    green: 'w-full p-3 bg-white border border-gray-100 rounded-lg text-xs text-gray-600 hover:border-green-200 hover:text-green-700 cursor-pointer transition-colors flex items-center justify-between group text-left',
    purple: 'w-full p-3 bg-white border border-gray-100 rounded-lg text-xs text-gray-600 hover:border-purple-200 hover:text-purple-700 cursor-pointer transition-colors flex items-center justify-between group text-left',
    blue: 'w-full p-3 bg-white border border-gray-100 rounded-lg text-xs text-gray-600 hover:border-blue-200 hover:text-blue-700 cursor-pointer transition-colors flex items-center justify-between group text-left',
    orange: 'w-full p-3 bg-white border border-gray-100 rounded-lg text-xs text-gray-600 hover:border-orange-200 hover:text-orange-700 cursor-pointer transition-colors flex items-center justify-between group text-left'
  };
  return classes[color] || classes.blue;
};

// 根据用户角色获取信息面板的渐变背景class
const getUserPanelGradientClass = () => {
  if (!currentUserInfo.value) {
    return 'bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl p-4 text-white shadow-lg relative overflow-hidden';
  }
  
  const role = (currentUserInfo.value.role || '').toLowerCase();
  
  if (role.includes('scholar') || role.includes('visiting')) {
    return 'bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl p-4 text-white shadow-lg relative overflow-hidden';
  } else if (role.includes('student') || role.includes('teacher')) {
    return 'bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl p-4 text-white shadow-lg relative overflow-hidden';
  } else {
    return 'bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl p-4 text-white shadow-lg relative overflow-hidden';
  }
};

// 根据用户角色获取连接的集合（而不是根据type）
const getUserConnectedCollections = () => {
  if (!currentUserInfo.value) {
    return [{ name: 'Standard (公开)', color: 'green', access: 'Read' }];
  }
  
  const role = (currentUserInfo.value.role || '').toLowerCase();
  const collections = [{ name: 'Standard (公开)', color: 'green', access: 'Read' }];
  
  if (role.includes('scholar') || role.includes('visiting') || 
      role.includes('student') || role.includes('teacher')) {
    collections.push({ name: 'Knowledge (学术)', color: 'purple', access: 'Read' });
  }
  
  if (role.includes('student') || role.includes('teacher')) {
    collections.push({ name: 'Internal (内部)', color: 'blue', access: 'Read' });
    collections.push({ name: 'Person_info (个人)', color: 'orange', access: 'Private' });
  }
  
  return collections;
};

// 根据用户角色获取常用服务链接
const getUserCommonServices = () => {
  if (!currentUserInfo.value) {
    return [];
  }
  
  const role = (currentUserInfo.value.role || '').toLowerCase();
  
  if (role.includes('scholar') || role.includes('visiting')) {
    return [
      { name: '学术知识库', url: 'https://ir.tongji.edu.cn/tongji/' },
      { name: '同济大学图书馆', url: 'https://www.lib.tongji.edu.cn/' }
    ];
  } else if (role.includes('student') || role.includes('teacher')) {
    return [
      { name: '教学信息管理系统', url: 'https://1.tongji.edu.cn/' },
      { name: 'canvas', url: 'https://canvas.tongji.edu.cn/' },
      { name: '同济邮箱', url: 'https://mail.tongji.edu.cn/' }
    ];
  }
  
  return [];
};

// 根据用户角色获取服务链接的样式class
const getServiceLinkClass = () => {
  if (!currentUserInfo.value) {
    return 'w-full p-3 bg-white border border-gray-100 rounded-lg text-xs text-gray-600 cursor-pointer transition-colors flex items-center justify-between group text-left hover:bg-gray-50';
  }
  
  const role = (currentUserInfo.value.role || '').toLowerCase();
  
  if (role.includes('scholar') || role.includes('visiting')) {
    return 'w-full p-3 bg-white border border-purple-200 text-purple-700 rounded-lg text-xs cursor-pointer transition-colors flex items-center justify-between group text-left hover:bg-purple-50 hover:border-purple-300';
  } else if (role.includes('student') || role.includes('teacher')) {
    return 'w-full p-3 bg-white border border-blue-200 text-blue-700 rounded-lg text-xs cursor-pointer transition-colors flex items-center justify-between group text-left hover:bg-blue-50 hover:border-blue-300';
  }
  
  return 'w-full p-3 bg-white border border-gray-100 rounded-lg text-xs text-gray-600 cursor-pointer transition-colors flex items-center justify-between group text-left hover:bg-gray-50';
};

// 根据用户角色决定显示模式（保留向后兼容）
const getModeByRole = (role) => {
  const roleLower = (role || '').toLowerCase();
  // 根据角色映射到对应模式
  if (roleLower.includes('scholar') || roleLower.includes('visiting')) {
    return 'scholar';
  } else if (roleLower.includes('student') || roleLower.includes('teacher') || roleLower.includes('teacher')) {
    return 'student';
  }
  // 默认返回student模式
  return 'student';
};

const formatTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
const formatDate = (date = new Date()) => date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });

// ========== 统一的Type会话管理 ==========

// 加载指定type的会话列表
const loadTypeSessions = async (type) => {
  try {
    // 确保type存在
    if (!typeSessions.value[type]) {
      typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
    }
    
    const response = await sessionAPI.getSessionList(type);
    typeSessions.value[type].conversations = (response.data || []).map(session => ({
      id: session.session_id,
      title: session.title || '新对话',
      time: formatDate(new Date(session.created_at)),
      updatedAt: formatTime(),
      type: session.type || type
    }));
  } catch (error) {
    console.error(`加载${type}会话列表失败:`, error);
    // 确保即使出错也有空数组
    if (!typeSessions.value[type]) {
      typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
    }
  }
};

// 加载指定type的会话历史
const loadTypeHistory = async (type, sessionId) => {
  try {
    // 确保type存在
    if (!typeSessions.value[type]) {
      typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
    }
    
    const response = await sessionAPI.getSessionHistory(sessionId);
    typeSessions.value[type].messages = (response.messages || []).map((msg, idx) => ({
      id: idx + 1,
      sender: msg.role === 'user' ? 'user' : 'bot',
      timestamp: formatTime(new Date(msg.timestamp * 1000)),
      content: msg.content
    }));
  } catch (error) {
    console.error(`加载${type}历史失败:`, error);
    // 确保即使出错也有空数组
    if (!typeSessions.value[type]) {
      typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
    }
    if (typeSessions.value[type]) {
      typeSessions.value[type].messages = [];
    }
  }
};

// 创建新会话（指定type）
const handleTypeNewConversation = async (type) => {
  try {
    // 确保type存在
    if (!typeSessions.value[type]) {
      typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
    }
    
    const response = await sessionAPI.createSession(type);
    const newSession = {
      id: response.session_id,
      title: response.title || '新对话',
      time: formatDate(new Date(response.created_at)),
      updatedAt: formatTime(),
      type: response.type || type
    };
    typeSessions.value[type].conversations.unshift(newSession);
    typeSessions.value[type].currentId = response.session_id;
    typeSessions.value[type].messages = [];
  } catch (error) {
    console.error(`创建${type}会话失败:`, error);
    alert(`创建会话失败: ${error.message}`);
    // 确保即使出错也有空状态
    if (!typeSessions.value[type]) {
      typeSessions.value[type] = { conversations: [], currentId: '', messages: [] };
    }
  }
};

// 切换会话（指定type）
const handleTypeSwitchConversation = async (type, id) => {
  typeSessions.value[type].currentId = id;
  await loadTypeHistory(type, id);
};

// 删除会话（指定type）
const handleTypeDeleteConversation = async (type, id) => {
  try {
    await sessionAPI.deleteSession(id);
    const index = typeSessions.value[type].conversations.findIndex(c => c.id === id);
    if (index !== -1) {
      typeSessions.value[type].conversations.splice(index, 1);
      if (typeSessions.value[type].currentId === id) {
        if (typeSessions.value[type].conversations.length > 0) {
          typeSessions.value[type].currentId = typeSessions.value[type].conversations[0].id;
          await loadTypeHistory(type, typeSessions.value[type].conversations[0].id);
        } else {
          typeSessions.value[type].messages = [];
          typeSessions.value[type].currentId = '';
        }
      }
    }
  } catch (error) {
    console.error(`删除${type}会话失败:`, error);
    alert(`删除会话失败: ${error.message}`);
  }
};

// 发送消息（指定type）
const handleTypeSend = async (type, text) => {
  if (!typeSessions.value[type].currentId) {
    await handleTypeNewConversation(type);
  }
  
  // 添加用户消息
  const userMessage = {
    id: typeSessions.value[type].messages.length + 1,
    sender: 'user',
    timestamp: formatTime(),
    content: text
  };
  typeSessions.value[type].messages.push(userMessage);
  
  // 更新对话标题
  const conversation = typeSessions.value[type].conversations.find(
    c => c.id === typeSessions.value[type].currentId
  );
  if (conversation && conversation.title === '新对话') {
    conversation.title = text.length > 20 ? text.substring(0, 20) + '...' : text;
    conversation.updatedAt = formatTime();
  }
  
  // 创建AI回复消息占位符
  const botMessageId = typeSessions.value[type].messages.length + 1;
  const botMessage = {
    id: botMessageId,
    sender: 'bot',
    timestamp: formatTime(),
    content: ''
  };
  typeSessions.value[type].messages.push(botMessage);
  
  // 发送消息到后端
  try {
    await chatAPI.sendMessage(
      type,
      text,
      typeSessions.value[type].currentId,
      (chunk) => {
        // 流式更新消息内容
        const msg = typeSessions.value[type].messages.find(m => m.id === botMessageId);
        if (msg) {
          msg.content += chunk;
        }
      },
      (error) => {
        console.error('发送消息失败:', error);
        const msg = typeSessions.value[type].messages.find(m => m.id === botMessageId);
        if (msg) {
          msg.content = '抱歉，发生了错误: ' + error.message;
        }
      },
      () => {
        // 完成
      }
    );
  } catch (error) {
    console.error('发送消息失败:', error);
    const msg = typeSessions.value[type].messages.find(m => m.id === botMessageId);
    if (msg) {
      msg.content = '抱歉，发生了错误: ' + error.message;
    }
  }
};

// 切换type
const handleTypeChange = async (newType) => {
  if (newType === currentType.value) return;
  
  try {
    // 确保type存在
    if (!typeSessions.value[newType]) {
      typeSessions.value[newType] = { conversations: [], currentId: '', messages: [] };
    }
    
    // 先切换type，让UI立即更新
    currentType.value = newType;
    
    // 如果该type还没有加载会话，则加载
    if (typeSessions.value[newType].conversations.length === 0) {
      await loadTypeSessions(newType);
    }
    
    // 如果有会话但当前没有选中，则选中第一个
    if (typeSessions.value[newType].conversations.length > 0) {
      if (!typeSessions.value[newType].currentId) {
        typeSessions.value[newType].currentId = typeSessions.value[newType].conversations[0].id;
      }
      // 加载当前会话的历史
      if (typeSessions.value[newType].currentId) {
        await loadTypeHistory(newType, typeSessions.value[newType].currentId);
      }
    } else {
      // 如果没有会话，创建新会话
      await handleTypeNewConversation(newType);
    }
  } catch (error) {
    console.error(`切换type到${newType}失败:`, error);
    // 如果出错，确保至少有一个空的状态
    if (!typeSessions.value[newType]) {
      typeSessions.value[newType] = { conversations: [], currentId: '', messages: [] };
    }
    if (!typeSessions.value[newType].messages) {
      typeSessions.value[newType].messages = [];
    }
  }
};

// Conversation management
// Visitor
const visitorConversations = ref([]);
const currentVisitorConversationId = ref('');
const visitorMessages = ref([]);
const visitorExampleQuestions = [
  '嘉定校区图书馆在哪里？',
  '四平路校区地图',
  '校车时刻表(仅公开版)',
  '2025本科招生简章'
];

const visitorPopularQuestions = [
  '同济大学的校训是什么？',
  '同济大学创建于哪一年？',
  '同济大学是"985""211"高校吗？',
  '同济大学的土木工程在全国处于什么水平？'
];

// 加载访客会话列表
const loadVisitorSessions = async () => {
  try {
    const response = await sessionAPI.getSessionList('public');
    visitorConversations.value = (response.data || []).map(session => ({
      id: session.session_id,
      title: session.title || '新对话',
      time: formatDate(new Date(session.created_at)),
      updatedAt: formatTime()
    }));
  } catch (error) {
    console.error('加载会话列表失败:', error);
  }
};

// 加载会话历史
const loadVisitorHistory = async (sessionId) => {
  try {
    const response = await sessionAPI.getSessionHistory(sessionId);
    visitorMessages.value = (response.messages || []).map((msg, idx) => ({
      id: idx + 1,
      sender: msg.role === 'user' ? 'user' : 'bot',
      timestamp: formatTime(new Date(msg.timestamp * 1000)),
      content: msg.content
    }));
  } catch (error) {
    console.error('加载历史失败:', error);
  }
};

const handleVisitorNewConversation = async () => {
  try {
    const response = await sessionAPI.createSession('public');
    const newSession = {
      id: response.session_id,
      title: response.title || '新对话',
      time: formatDate(new Date(response.created_at)),
      updatedAt: formatTime()
    };
    visitorConversations.value.unshift(newSession);
    currentVisitorConversationId.value = response.session_id;
    visitorMessages.value = [];
  } catch (error) {
    console.error('创建会话失败:', error);
    alert('创建会话失败: ' + error.message);
  }
};

const handleVisitorSwitchConversation = async (id) => {
  currentVisitorConversationId.value = id;
  await loadVisitorHistory(id);
};

const handleVisitorDeleteConversation = async (id) => {
  try {
    await sessionAPI.deleteSession(id);
    const index = visitorConversations.value.findIndex(c => c.id === id);
    if (index !== -1) {
      visitorConversations.value.splice(index, 1);
      if (currentVisitorConversationId.value === id) {
        if (visitorConversations.value.length > 0) {
          currentVisitorConversationId.value = visitorConversations.value[0].id;
          await loadVisitorHistory(visitorConversations.value[0].id);
        } else {
          visitorMessages.value = [];
          currentVisitorConversationId.value = '';
        }
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error);
    alert('删除会话失败: ' + error.message);
  }
};

const handleVisitorSend = async (text) => {
  if (!currentVisitorConversationId.value) {
    await handleVisitorNewConversation();
  }
  
  // 添加用户消息
  const userMessage = {
    id: visitorMessages.value.length + 1,
    sender: 'user',
    timestamp: formatTime(),
    content: text
  };
  visitorMessages.value.push(userMessage);
  
  // 更新对话标题
  const conversation = visitorConversations.value.find(c => c.id === currentVisitorConversationId.value);
  if (conversation && conversation.title === '新对话') {
    conversation.title = text.length > 20 ? text.substring(0, 20) + '...' : text;
    conversation.updatedAt = formatTime();
  }
  
  // 创建AI回复消息占位符
  const botMessageId = visitorMessages.value.length + 1;
  const botMessage = {
    id: botMessageId,
    sender: 'bot',
    timestamp: formatTime(),
    content: ''
  };
  visitorMessages.value.push(botMessage);
  
  // 发送消息到后端
  try {
    await chatAPI.sendMessage(
      'public',
      text,
      currentVisitorConversationId.value,
      (chunk) => {
        // 流式更新消息内容
        const msg = visitorMessages.value.find(m => m.id === botMessageId);
        if (msg) {
          msg.content += chunk;
        }
      },
      (error) => {
        console.error('发送消息失败:', error);
        const msg = visitorMessages.value.find(m => m.id === botMessageId);
        if (msg) {
          msg.content = '抱歉，发生了错误: ' + error.message;
        }
      },
      () => {
        // 完成
      }
    );
  } catch (error) {
    console.error('发送消息失败:', error);
    const msg = visitorMessages.value.find(m => m.id === botMessageId);
    if (msg) {
      msg.content = '抱歉，发生了错误: ' + error.message;
    }
  }
};

// Scholar
const scholarConversations = ref([]);
const currentScholarConversationId = ref('');
const scholarMessages = ref([]);
const scholarExampleQuestions = [
  '汽车学院在自动驾驶领域最近有什么发表？',
  '查找IEEE关于机器学习的论文',
  'CNKI中关于人工智能的最新研究',
  '同济大学2024年科研年报'
];

const loadScholarSessions = async () => {
  try {
    const response = await sessionAPI.getSessionList('academic');
    scholarConversations.value = (response.data || []).map(session => ({
      id: session.session_id,
      title: session.title || '新对话',
      time: formatDate(new Date(session.created_at)),
      updatedAt: formatTime()
    }));
  } catch (error) {
    console.error('加载会话列表失败:', error);
  }
};

const loadScholarHistory = async (sessionId) => {
  try {
    const response = await sessionAPI.getSessionHistory(sessionId);
    scholarMessages.value = (response.messages || []).map((msg, idx) => ({
      id: idx + 1,
      sender: msg.role === 'user' ? 'user' : 'bot',
      timestamp: formatTime(new Date(msg.timestamp * 1000)),
      content: msg.content
    }));
  } catch (error) {
    console.error('加载历史失败:', error);
  }
};

const handleScholarNewConversation = async () => {
  try {
    const response = await sessionAPI.createSession('academic');
    const newSession = {
      id: response.session_id,
      title: response.title || '新对话',
      time: formatDate(new Date(response.created_at)),
      updatedAt: formatTime()
    };
    scholarConversations.value.unshift(newSession);
    currentScholarConversationId.value = response.session_id;
    scholarMessages.value = [];
  } catch (error) {
    console.error('创建会话失败:', error);
    alert('创建会话失败: ' + error.message);
  }
};

const handleScholarSwitchConversation = async (id) => {
  currentScholarConversationId.value = id;
  await loadScholarHistory(id);
};

const handleScholarDeleteConversation = async (id) => {
  try {
    await sessionAPI.deleteSession(id);
    const index = scholarConversations.value.findIndex(c => c.id === id);
    if (index !== -1) {
      scholarConversations.value.splice(index, 1);
      if (currentScholarConversationId.value === id) {
        if (scholarConversations.value.length > 0) {
          currentScholarConversationId.value = scholarConversations.value[0].id;
          await loadScholarHistory(scholarConversations.value[0].id);
        } else {
          scholarMessages.value = [];
          currentScholarConversationId.value = '';
        }
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error);
    alert('删除会话失败: ' + error.message);
  }
};

const handleScholarSend = async (text) => {
  if (!currentScholarConversationId.value) {
    await handleScholarNewConversation();
  }
  
  const userMessage = {
    id: scholarMessages.value.length + 1,
    sender: 'user',
    timestamp: formatTime(),
    content: text
  };
  scholarMessages.value.push(userMessage);
  
  const conversation = scholarConversations.value.find(c => c.id === currentScholarConversationId.value);
  if (conversation && conversation.title === '新对话') {
    conversation.title = text.length > 20 ? text.substring(0, 20) + '...' : text;
    conversation.updatedAt = formatTime();
  }
  
  const botMessageId = scholarMessages.value.length + 1;
  const botMessage = {
    id: botMessageId,
    sender: 'bot',
    timestamp: formatTime(),
    content: ''
  };
  scholarMessages.value.push(botMessage);
  
  try {
    await chatAPI.sendMessage(
      'academic',
      text,
      currentScholarConversationId.value,
      (chunk) => {
        const msg = scholarMessages.value.find(m => m.id === botMessageId);
        if (msg) {
          msg.content += chunk;
        }
      },
      (error) => {
        console.error('发送消息失败:', error);
        const msg = scholarMessages.value.find(m => m.id === botMessageId);
        if (msg) {
          msg.content = '抱歉，发生了错误: ' + error.message;
        }
      },
      () => {}
    );
  } catch (error) {
    console.error('发送消息失败:', error);
    const msg = scholarMessages.value.find(m => m.id === botMessageId);
    if (msg) {
      msg.content = '抱歉，发生了错误: ' + error.message;
    }
  }
};

// Student
const studentConversations = ref([]);
const currentStudentConversationId = ref('');
const studentMessages = ref([]);
const studentExampleQuestions = [
  '嘉定校区图书馆几点关门？',
  '查看我今天有什么课程',
  '我的高数成绩是多少？',
  '校园卡余额查询'
];

const loadStudentSessions = async () => {
  try {
    const response = await sessionAPI.getSessionList('internal');
    studentConversations.value = (response.data || []).map(session => ({
      id: session.session_id,
      title: session.title || '新对话',
      time: formatDate(new Date(session.created_at)),
      updatedAt: formatTime()
    }));
  } catch (error) {
    console.error('加载会话列表失败:', error);
  }
};

const loadStudentHistory = async (sessionId) => {
  try {
    const response = await sessionAPI.getSessionHistory(sessionId);
    studentMessages.value = (response.messages || []).map((msg, idx) => ({
      id: idx + 1,
      sender: msg.role === 'user' ? 'user' : 'bot',
      timestamp: formatTime(new Date(msg.timestamp * 1000)),
      content: msg.content
    }));
  } catch (error) {
    console.error('加载历史失败:', error);
  }
};

const handleStudentNewConversation = async () => {
  try {
    const response = await sessionAPI.createSession('internal');
    const newSession = {
      id: response.session_id,
      title: response.title || '新对话',
      time: formatDate(new Date(response.created_at)),
      updatedAt: formatTime()
    };
    studentConversations.value.unshift(newSession);
    currentStudentConversationId.value = response.session_id;
    studentMessages.value = [];
  } catch (error) {
    console.error('创建会话失败:', error);
    alert('创建会话失败: ' + error.message);
  }
};

const handleStudentSwitchConversation = async (id) => {
  currentStudentConversationId.value = id;
  await loadStudentHistory(id);
};

const handleStudentDeleteConversation = async (id) => {
  try {
    await sessionAPI.deleteSession(id);
    const index = studentConversations.value.findIndex(c => c.id === id);
    if (index !== -1) {
      studentConversations.value.splice(index, 1);
      if (currentStudentConversationId.value === id) {
        if (studentConversations.value.length > 0) {
          currentStudentConversationId.value = studentConversations.value[0].id;
          await loadStudentHistory(studentConversations.value[0].id);
        } else {
          studentMessages.value = [];
          currentStudentConversationId.value = '';
        }
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error);
    alert('删除会话失败: ' + error.message);
  }
};

const handleStudentSend = async (text) => {
  if (!currentStudentConversationId.value) {
    await handleStudentNewConversation();
  }
  
  const userMessage = {
    id: studentMessages.value.length + 1,
    sender: 'user',
    timestamp: formatTime(),
    content: text
  };
  studentMessages.value.push(userMessage);
  
  const conversation = studentConversations.value.find(c => c.id === currentStudentConversationId.value);
  if (conversation && conversation.title === '新对话') {
    conversation.title = text.length > 20 ? text.substring(0, 20) + '...' : text;
    conversation.updatedAt = formatTime();
  }
  
  const botMessageId = studentMessages.value.length + 1;
  const botMessage = {
    id: botMessageId,
    sender: 'bot',
    timestamp: formatTime(),
    content: ''
  };
  studentMessages.value.push(botMessage);
  
  try {
    await chatAPI.sendMessage(
      'internal',
      text,
      currentStudentConversationId.value,
      (chunk) => {
        const msg = studentMessages.value.find(m => m.id === botMessageId);
        if (msg) {
          msg.content += chunk;
        }
      },
      (error) => {
        console.error('发送消息失败:', error);
        const msg = studentMessages.value.find(m => m.id === botMessageId);
        if (msg) {
          msg.content = '抱歉，发生了错误: ' + error.message;
        }
      },
      () => {}
    );
  } catch (error) {
    console.error('发送消息失败:', error);
    const msg = studentMessages.value.find(m => m.id === botMessageId);
    if (msg) {
      msg.content = '抱歉，发生了错误: ' + error.message;
    }
  }
};
// 根据当前模式和用户信息返回用户对象（计算属性）
const currentUser = computed(() => {
  if (currentMode.value === 'visitor') {
    return { name: 'Anonymous Guest', id: 'Guest', role: 'Visitor', avatar: 'V', department: '访客' };
  } else if (currentMode.value === 'denied') {
    return { name: 'Anonymous Guest', id: 'Guest', role: 'Visitor', avatar: 'V', department: '访客' };
  } else if (currentUserInfo.value) {
    // 使用从API返回的真实用户信息
    const userInfo = currentUserInfo.value;
    const name = userInfo.name || '用户';
    const role = userInfo.role || 'student';
    const roleLower = role.toLowerCase();
    
    // 根据角色生成头像和部门信息
    let avatar = name.substring(0, 2).toUpperCase();
    let department = '';
    let displayRole = '';
    let userId = '';
    
    if (roleLower.includes('scholar') || roleLower.includes('visiting')) {
      displayRole = 'Visiting Scholar';
      department = userInfo.department || '访问学者';
      avatar = 'Dr';
      userId = userInfo.id || userInfo.username || 'Scholar';
    } else if (roleLower.includes('student')) {
      displayRole = '在校师生 (Student)';
      department = userInfo.department || '学生';
      avatar = name.substring(0, 2).toUpperCase();
      userId = userInfo.id || userInfo.username || 'Student';
    } else if (roleLower.includes('teacher')) {
      displayRole = '教师 (Teacher)';
      department = userInfo.department || '教师';
      avatar = name.substring(0, 2).toUpperCase();
      userId = userInfo.id || userInfo.username || 'Faculty';
    } else {
      displayRole = role;
      department = userInfo.department || '';
      avatar = name.substring(0, 2).toUpperCase();
      userId = userInfo.id || userInfo.username || 'User';
    }
    
    return {
      name: name,
      id: userId,
      role: displayRole,
      avatar: avatar,
      department: department
    };
  } else {
    // 默认值
    if (currentMode.value === 'scholar') {
      return { name: 'Prof. Zhang', id: 'SCH-2024', role: 'Visiting Scholar', avatar: 'Dr', department: '访问学者' };
    } else {
      return { name: '用户', id: 'User', role: '在校师生 (Student)', avatar: 'U', department: '学生' };
    }
  }
});

const studentWelcomeTitle = computed(() => {
  return `欢迎回来，${currentUser.value.name}！`;
});

// 根据用户身份返回对应的ID Card英文标题
const userCardTitle = computed(() => {
  const role = currentUser.value.role || '';
  const roleLower = role.toLowerCase();
  
  if (roleLower.includes('visitor') || roleLower.includes('guest')) {
    return 'Visitor Card';
  } else if (roleLower.includes('scholar') || roleLower.includes('visiting')) {
    return 'Scholar ID Card';
  } else if (roleLower.includes('teacher') || roleLower.includes('faculty')) {
    return 'Faculty ID Card';
  } else if (roleLower.includes('student')) {
    return 'Student ID Card';
  } else {
    // 默认根据模式判断
    if (currentMode.value === 'scholar') {
      return 'Scholar ID Card';
    } else if (currentMode.value === 'student') {
      return 'Student ID Card';
    } else {
      return 'Visitor Card';
    }
  }
});

// 根据用户身份返回对应的英文身份标识
const userRoleEnglish = computed(() => {
  const role = currentUser.value.role || '';
  const roleLower = role.toLowerCase();
  
  if (roleLower.includes('visitor') || roleLower.includes('guest')) {
    return 'Visitor';
  } else if (roleLower.includes('scholar') || roleLower.includes('visiting')) {
    return 'Visiting Scholar';
  } else if (roleLower.includes('teacher') || roleLower.includes('faculty')) {
    return 'Faculty';
  } else if (roleLower.includes('student')) {
    return 'Student';
  } else {
    // 默认根据模式判断
    if (currentMode.value === 'scholar') {
      return 'Visiting Scholar';
    } else if (currentMode.value === 'student') {
      return 'Student';
    } else {
      return 'Visitor';
    }
  }
});

// Access denied
const deniedConversations = ref([]);
const currentDeniedConversationId = ref('');
const deniedMessages = ref([]);
const deniedExampleQuestions = [
  '帮我查一下我的高数期末成绩',
  '查看我的个人课表',
  '我的选课信息',
  '四平路校区地图'
];

const handleDeniedNewConversation = () => {
  // Denied模式使用本地生成的ID，不需要API调用
  const newId = `denied_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  deniedConversations.value.unshift({
    id: newId,
    title: '新对话',
    time: formatDate(),
    updatedAt: formatTime()
  });
  currentDeniedConversationId.value = newId;
  deniedMessages.value = [];
};

const handleDeniedSwitchConversation = (id) => {
  currentDeniedConversationId.value = id;
  deniedMessages.value = [];
};

const handleDeniedDeleteConversation = (id) => {
  const index = deniedConversations.value.findIndex(c => c.id === id);
  if (index !== -1) {
    deniedConversations.value.splice(index, 1);
    if (currentDeniedConversationId.value === id) {
      if (deniedConversations.value.length > 0) {
        currentDeniedConversationId.value = deniedConversations.value[0].id;
        deniedMessages.value = [];
      } else {
        handleDeniedNewConversation();
      }
    }
  }
};

const handleDeniedSend = async (text) => {
  if (!currentDeniedConversationId.value) {
    await handleDeniedNewConversation();
  }
  
  const userMessage = {
    id: deniedMessages.value.length + 1,
    sender: 'user',
    timestamp: formatTime(),
    content: text
  };
  deniedMessages.value.push(userMessage);
  
  const conversation = deniedConversations.value.find(c => c.id === currentDeniedConversationId.value);
  if (conversation && conversation.title === '新对话') {
    conversation.title = text.length > 20 ? text.substring(0, 20) + '...' : text;
    conversation.updatedAt = formatTime();
  }
  
  // 权限不足提示
  setTimeout(() => {
    deniedMessages.value.push({
      id: deniedMessages.value.length + 1,
      sender: 'bot',
      timestamp: formatTime(),
      content: '权限不足。请点击左下角登录。'
    });
  }, 800);
};

const handleLogin = async () => {
  if (loggingIn.value) return;
  if (!loginForm.value.email || !loginForm.value.password) {
    loginError.value = '请输入用户名和密码';
    return;
  }
  
  loggingIn.value = true;
  loginError.value = '';
  
  try {
    // 使用email字段作为username
    const response = await authAPI.login(loginForm.value.email, loginForm.value.password);
    
    // 保存用户信息
    currentUserInfo.value = response.user_info || {};
    
    // 处理"记住登录"功能
    if (rememberLogin.value) {
      // 保存用户名到localStorage
      localStorage.setItem('remembered_username', loginForm.value.email);
    } else {
      // 清除保存的用户名
      localStorage.removeItem('remembered_username');
    }
    
    // 处理"记住密码"功能
    if (rememberPassword.value) {
      // 保存密码到localStorage（注意：实际应用中应该加密存储）
      localStorage.setItem('remembered_password', loginForm.value.password);
    } else {
      // 清除保存的密码
      localStorage.removeItem('remembered_password');
    }
    
    // 根据返回的角色决定模式
    const role = currentUserInfo.value.role || 'student';
    currentMode.value = getModeByRole(role);
    
    // 登录成功
    loggingIn.value = false;
    showLogin.value = false;
    
    // 根据角色设置默认type
    const available = getAvailableTypes(role);
    currentType.value = available[0] || 'public';
    
    // 加载所有可用type的会话列表
    for (const type of available) {
      await loadTypeSessions(type);
    }
    
    // 为当前type初始化会话
    if (typeSessions.value[currentType.value].conversations.length === 0) {
      await handleTypeNewConversation(currentType.value);
    } else {
      typeSessions.value[currentType.value].currentId = 
        typeSessions.value[currentType.value].conversations[0].id;
      await loadTypeHistory(
        currentType.value,
        typeSessions.value[currentType.value].conversations[0].id
      );
    }
  } catch (error) {
    loggingIn.value = false;
    loginError.value = error.message || '登录失败，请检查用户名和密码';
    console.error('登录失败:', error);
  }
};

const handleGuestLogin = async () => {
  try {
    const response = await authAPI.guestLogin();
    // 保存访客用户信息
    currentUserInfo.value = response.user_info || {};
    showLogin.value = false;
    currentMode.value = 'visitor';
    currentType.value = 'public';
    await loadTypeSessions('public');
    if (typeSessions.value.public.conversations.length === 0) {
      await handleTypeNewConversation('public');
    } else {
      typeSessions.value.public.currentId = typeSessions.value.public.conversations[0].id;
      await loadTypeHistory('public', typeSessions.value.public.conversations[0].id);
    }
  } catch (error) {
    console.error('访客登录失败:', error);
    alert('访客登录失败: ' + error.message);
  }
};

const handleLogout = async () => {
  try {
    await authAPI.logout();
  } catch (error) {
    console.error('登出失败:', error);
  }
  
  // 重置所有状态
  showLogin.value = true;
  currentMode.value = 'visitor';
  currentType.value = 'public';
  
  // 清空所有type的会话数据
  typeSessions.value = {
    public: { conversations: [], currentId: '', messages: [] },
    academic: { conversations: [], currentId: '', messages: [] },
    internal: { conversations: [], currentId: '', messages: [] },
    personal: { conversations: [], currentId: '', messages: [] }
  };
  
  // 保留向后兼容（清空旧的独立状态）
  visitorConversations.value = [];
  scholarConversations.value = [];
  studentConversations.value = [];
  deniedConversations.value = [];
  
  currentVisitorConversationId.value = '';
  currentScholarConversationId.value = '';
  currentStudentConversationId.value = '';
  currentDeniedConversationId.value = '';
  
  visitorMessages.value = [];
  scholarMessages.value = [];
  studentMessages.value = [];
  deniedMessages.value = [];
  
  // 重置登录表单和用户信息
  loginError.value = '';
  currentUserInfo.value = null;
  
  // 恢复"记住登录"和"记住密码"的内容
  const rememberedUsername = localStorage.getItem('remembered_username');
  const rememberedPassword = localStorage.getItem('remembered_password');
  
  if (rememberedUsername) {
    loginForm.value.email = rememberedUsername;
    rememberLogin.value = true;
  } else {
    loginForm.value.email = '';
    rememberLogin.value = false;
  }
  
  if (rememberedPassword) {
    loginForm.value.password = rememberedPassword;
    rememberPassword.value = true;
  } else {
    loginForm.value.password = '';
    rememberPassword.value = false;
  }
};

// 检查是否已登录
onMounted(async () => {
  // 恢复"记住登录"的用户名
  const rememberedUsername = localStorage.getItem('remembered_username');
  if (rememberedUsername) {
    loginForm.value.email = rememberedUsername;
    rememberLogin.value = true;
  }
  
  // 恢复"记住密码"的密码
  const rememberedPassword = localStorage.getItem('remembered_password');
  if (rememberedPassword) {
    loginForm.value.password = rememberedPassword;
    rememberPassword.value = true;
  }
  
  if (isAuthenticated()) {
    const userInfo = getUserInfo();
    if (userInfo) {
      // 恢复用户信息
      currentUserInfo.value = userInfo;
      // 根据角色决定模式
      const role = userInfo.role || 'student';
      currentMode.value = getModeByRole(role);
      showLogin.value = false;
      
      // 根据角色设置默认type
      const available = getAvailableTypes(role);
      currentType.value = available[0] || 'public';
      
      // 加载所有可用type的会话列表
      for (const type of available) {
        await loadTypeSessions(type);
      }
      
      // 为当前type初始化会话
      if (typeSessions.value[currentType.value].conversations.length > 0) {
        typeSessions.value[currentType.value].currentId = 
          typeSessions.value[currentType.value].conversations[0].id;
        await loadTypeHistory(
          currentType.value,
          typeSessions.value[currentType.value].conversations[0].id
        );
      }
    } else {
      showLogin.value = true;
    }
  }
});
</script>

<template>
  <div v-if="showLogin" class="min-h-screen bg-slate-950 text-slate-300 flex items-center justify-center p-6 relative overflow-hidden font-sans">
    <div class="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_70%,transparent_100%)] opacity-30"></div>

    <div class="max-w-6xl w-full grid md:grid-cols-12 gap-8 relative z-10">
      <div class="hidden md:flex md:col-span-7 flex-col justify-between border border-slate-800 bg-slate-900/50 backdrop-blur-md rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-500"></div>
        
        <div>
          <div class="flex items-center gap-4 mb-10">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-[0_0_30px_rgba(6,182,212,0.3)]">
              <span class="text-2xl font-black text-white tracking-tighter">SQ</span>
            </div>
            <div>
              <h1 class="text-3xl font-black text-white tracking-tight">SynapseQ 校园问答助手</h1>
              <p class="text-cyan-400 font-medium text-sm mt-1">同济师生的专属智能向导</p>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-5 mb-8 text-sm">
            <div class="p-5 border border-slate-800 bg-slate-950/80 rounded-2xl shadow-inner transition-colors hover:border-emerald-500/50">
              <div class="text-emerald-400 font-bold text-lg flex items-center gap-2 mb-2">
                <div class="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_10px_#10b981]"></div> 拒绝胡编乱造
              </div>
              <div class="text-slate-400 leading-relaxed text-xs">
                不再给出模棱两可的答案。我们只基于同济真实的校规、通知和官方数据，为你提供百分之百准确的解答。
              </div>
            </div>
            <div class="p-5 border border-slate-800 bg-slate-950/80 rounded-2xl shadow-inner transition-colors hover:border-blue-500/50">
              <div class="text-blue-400 font-bold text-lg mb-2 flex items-center gap-2">
                <div class="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-[0_0_10px_#3b82f6]"></div> 保护你的隐私
              </div>
              <div class="text-slate-400 leading-relaxed text-xs">
                你的成绩、课表和余额仅你自己可见。底层数据严格隔离，绝不会用于大模型训练，更不会泄露给任何其他人。
              </div>
            </div>
            <div class="col-span-2 p-5 border border-slate-800 bg-slate-950/80 rounded-2xl shadow-inner">
              <div class="flex justify-between items-end mb-3">
                <div>
                  <div class="text-slate-300 font-bold text-lg">包揽你的校园生活</div>
                  <div class="text-slate-500 text-xs mt-1">查校车、找教室、搜文献、问成绩... 统统交给我</div>
                </div>
              </div>
              <div class="flex gap-2 mt-4 text-[11px] font-medium text-slate-400">
                <span class="px-3 py-1 bg-slate-800 rounded-full border border-slate-700"># 新生指南</span>
                <span class="px-3 py-1 bg-slate-800 rounded-full border border-slate-700"># 办事流程</span>
                <span class="px-3 py-1 bg-slate-800 rounded-full border border-slate-700"># 论文检索</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="text-xs text-slate-400 border-t border-slate-800 pt-5 mt-6 space-y-2">
          <div class="flex items-center gap-2">
            <Globe class="w-4 h-4 text-emerald-500" /> 校园公开资讯库已就绪
          </div>
          <div class="flex items-center gap-2">
            <BookOpen class="w-4 h-4 text-purple-500" /> 学术文献索引服务正常
          </div>
          <div class="flex items-center gap-2 text-cyan-400 font-medium pt-2">
            ✨ 随时准备为您解答关于同济的一切疑问...
          </div>
        </div>
      </div>

      <div class="md:col-span-5 bg-slate-900 border border-slate-700 rounded-3xl shadow-2xl p-8 lg:p-10 relative flex flex-col justify-center">
        <div class="absolute -top-10 -right-10 w-40 h-40 bg-blue-600 rounded-full mix-blend-screen filter blur-[80px] opacity-30"></div>
        
        <div class="mb-10 relative z-10">
          <h2 class="text-2xl font-bold text-white mb-2 tracking-wide">统一身份认证</h2>
          <p class="text-sm text-slate-400">使用学号或教工号登录，解锁所有功能</p>
        </div>

        <div class="space-y-6 relative z-10">
          <div v-if="loginError" class="p-3 bg-red-900/30 border border-red-500/50 rounded-xl text-sm text-red-400 shadow-inner">
            {{ loginError }}
          </div>
          
          <div class="space-y-5">
            <div>
              <label class="text-[11px] text-slate-400 block mb-2 uppercase tracking-widest">学号 / 教工号</label>
              <input v-model="loginForm.email" type="text" placeholder="输入学号或教工号" class="w-full px-5 py-4 rounded-xl bg-slate-950 border border-slate-700 focus:outline-none focus:border-cyan-500 text-white text-sm transition-colors shadow-inner" />
            </div>
            <div>
              <label class="text-[11px] text-slate-400 block mb-2 uppercase tracking-widest">认证密码</label>
              <input v-model="loginForm.password" type="password" placeholder="••••••••" class="w-full px-5 py-4 rounded-xl bg-slate-950 border border-slate-700 focus:outline-none focus:border-cyan-500 text-white text-sm transition-colors shadow-inner" />
            </div>
          </div>

          <div class="pt-4 space-y-4">
            <button class="w-full py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold tracking-widest shadow-[0_0_20px_rgba(8,145,178,0.3)] hover:shadow-[0_0_30px_rgba(8,145,178,0.6)] transition-all disabled:opacity-50 disabled:shadow-none" :disabled="loggingIn || !loginForm.email || !loginForm.password" @click="handleLogin">
              <span v-if="!loggingIn">登录系统</span>
              <span v-else class="animate-pulse">身份校验中...</span>
            </button>
            
            <button @click="handleGuestLogin" class="w-full py-3.5 rounded-xl bg-transparent border-2 border-slate-700 hover:border-slate-500 hover:bg-slate-800 text-slate-300 text-sm font-bold tracking-wider transition-all flex items-center justify-center gap-2">
              <Globe class="w-4 h-4 text-slate-400" /> 访客免密浏览
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="h-screen flex flex-col bg-slate-950 font-sans">
    <div class="border-b border-slate-800 bg-slate-900 px-5 py-3 flex items-center gap-2 overflow-x-auto shadow-md z-30 shrink-0">
      <div class="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-widest mr-3 flex-shrink-0 flex items-center gap-2">
        <Database size="14" class="text-cyan-600" />
        Data Modules
      </div>
      <div class="flex gap-2">
        <button
          v-for="type in availableTypes"
          :key="type"
          @click="handleTypeChange(type)"
          class="px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 flex-shrink-0 border"
          :class="currentType === type 
            ? 'bg-cyan-900/30 text-cyan-400 border-cyan-700/50 shadow-[0_0_10px_rgba(8,145,178,0.2)]' 
            : 'bg-slate-950 text-slate-500 border-slate-800 hover:bg-slate-800 hover:text-slate-300'"
        >
          <component :is="typeConfig[type].icon" size="14" />
          <span class="tracking-wider">{{ typeConfig[type].label }}</span>
        </button>
      </div>
    </div>
    
    <div class="flex-1 overflow-hidden relative">
      <div class="w-full h-full bg-slate-950 overflow-hidden">
        <SynapseQShell
          :key="currentType"
          :themeColor="currentTypeConfig.color"
          :headerTitle="currentTypeConfig.title"
          :headerBadge="currentTypeConfig.badge"
          :currentUser="currentUser"
          :conversationHistory="currentConversations"
          :currentConversationId="currentConversationId"
          :messages="currentMessages"
          :exampleQuestions="getExampleQuestions(currentType)"
          :welcomeTitle="getWelcomeTitle(currentType)"
          @send-message="(text) => handleTypeSend(currentType, text)"
          @new-conversation="() => handleTypeNewConversation(currentType)"
          @switch-conversation="(id) => handleTypeSwitchConversation(currentType, id)"
          @delete-conversation="(id) => handleTypeDeleteConversation(currentType, id)"
          @logout="handleLogout"
        >
          <template #right-panel>
            <div class="mb-8 flex items-center gap-3 p-3 bg-slate-900/50 border border-slate-800 rounded-xl">
              <div class="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-cyan-500 shadow-inner">
                {{ currentUser.avatar }}
              </div>
              <div>
                <div class="text-sm font-bold text-slate-200">{{ currentUser.name }}</div>
                <div class="text-[10px] text-slate-500 font-mono mt-0.5">{{ currentUser.department }} | {{ currentUser.role }}</div>
              </div>
            </div>

            <div class="mb-8">
              <h4 class="text-xs font-bold text-slate-400 mb-3 flex items-center gap-2">
                <Database size="14" class="text-slate-500" />
                当前连入数据源
              </h4>
              <div class="flex flex-wrap gap-2">
                <div v-for="collection in getUserConnectedCollections()" :key="collection.name"
                  class="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300 shadow-sm">
                  <div class="w-1.5 h-1.5 rounded-full shadow-sm" 
                       :class="collection.color === 'green' ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' 
                             : (collection.color === 'purple' ? 'bg-purple-500 shadow-[0_0_5px_#a855f7]' 
                             : (collection.color === 'orange' ? 'bg-orange-500 shadow-[0_0_5px_#f97316]' : 'bg-cyan-500 shadow-[0_0_5px_#06b6d4]'))"></div>
                  {{ collection.name }}
                </div>
              </div>
              <p class="text-[10px] text-slate-600 mt-2 px-1">安全审计：底层检索范围已被物理隔离</p>
            </div>

            <div class="mb-8" v-if="getUserCommonServices().length > 0">
              <h4 class="text-xs font-bold text-slate-400 mb-3 flex items-center gap-2">
                <FileText v-if="currentMode === 'student'" size="14" class="text-slate-500" />
                <Search v-else size="14" class="text-slate-500" />
                快速直达
              </h4>
              <div class="grid grid-cols-2 gap-2">
                <a
                  v-for="service in getUserCommonServices()"
                  :key="service.name"
                  :href="service.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="p-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs font-medium text-slate-400 text-center hover:border-cyan-900 hover:text-cyan-400 hover:bg-slate-800 transition-colors truncate"
                >
                  {{ service.name }}
                </a>
              </div>
            </div>

            <div v-if="currentMode === 'visitor' && getPopularQuestions('public').length > 0">
              <h4 class="text-xs font-bold text-slate-400 mb-3 flex items-center gap-2">
                <Sparkles size="14" class="text-slate-500" />
                高频检索
              </h4>
              <div class="space-y-2">
                <button
                  v-for="q in getPopularQuestions('public')"
                  :key="q"
                  @click="handleTypeSend('public', q)"
                  class="w-full p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs font-medium text-slate-400 text-left hover:border-cyan-900 hover:text-cyan-400 hover:bg-slate-800 transition-all flex items-center justify-between group"
                >
                  <span class="truncate pr-2">{{ q }}</span>
                  <ChevronRight size="14" class="opacity-50 group-hover:opacity-100 transition-opacity text-cyan-500 flex-shrink-0" />
                </button>
              </div>
            </div>

          </template>
        </SynapseQShell>
      </div>
    </div>
  </div>
</template>

