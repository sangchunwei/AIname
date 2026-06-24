<template>
  <view class="page">
    <view class="topbar">
      <view class="topcopy">
        <view class="title">B 端开放平台</view>
        <view class="subtitle">面向游戏 NPC、小说角色和地名的自动命名 API 演示</view>
      </view>
      <button class="btn ghost" size="mini" @click="load">刷新</button>
    </view>

    <view class="panel create-panel">
      <input class="input" v-model="newAppName" placeholder="应用名称" />
      <button class="btn primary" @click="createApp">创建应用</button>
    </view>

    <view v-if="apps.length" class="app-tabs">
      <button
        v-for="app in apps"
        :key="app.id"
        :class="['btn', 'tab', selectedApp && selectedApp.id === app.id ? 'active' : '']"
        @click="selectApp(app)"
      >
        {{ appDisplayName(app.name) }}
      </button>
    </view>

    <view v-if="selectedApp" class="panel app-panel">
      <view class="section-head">
        <view>
          <view class="section-title">当前应用</view>
          <view class="muted">{{ appDisplayName(selectedApp.name) }}</view>
        </view>
        <button class="btn danger" size="mini" @click="deleteApp">删除应用</button>
      </view>
    </view>

    <view v-if="selectedApp" class="panel">
      <view class="section-title">调用额度</view>
      <view class="quota-row">
        <view class="metric-card">
          <view class="metric">{{ selectedApp.remaining_quota }}</view>
          <view class="metric-label">剩余调用次数</view>
        </view>
        <view class="metric-card">
          <view class="metric">{{ selectedApp.total_quota }}</view>
          <view class="metric-label">演示总额度</view>
        </view>
        <button class="btn ghost" size="mini" @click="demoRecharge">演示充值</button>
      </view>
    </view>

    <view v-if="selectedApp" class="panel">
      <view class="section-head">
        <view class="section-title">API 密钥</view>
        <button class="btn ghost" size="mini" @click="openCreateKeyDialog">新建密钥</button>
      </view>
      <view v-for="key in keys" :key="key.id" class="key-row">
        <view class="key-main">
          <view class="key-name">{{ keyDisplayName(key.name) }}</view>
          <view class="key-meta">{{ maskedKey(key) }} · {{ keyStatusText(key.status) }}</view>
        </view>
        <view class="key-actions">
          <button class="btn ghost" size="mini" @click="openRenameKeyDialog(key)">改名</button>
          <button v-if="key.status === 'active'" class="btn warn" size="mini" @click="disableKey(key.id)">禁用</button>
          <button v-if="key.status === 'disabled'" class="btn ghost" size="mini" @click="enableKey(key.id)">启用</button>
          <button class="btn danger" size="mini" @click="deleteKey(key.id)">删除</button>
        </view>
      </view>
      <view v-if="!keys.length" class="empty">暂无 API 密钥。</view>
    </view>

    <view v-if="selectedApp" class="panel">
      <view class="section-title">调用示例</view>
      <view class="endpoint">POST /open/v1/names/game-npc</view>
      <text selectable class="code">{{ sampleCode }}</text>
    </view>

    <view v-if="selectedApp" class="panel">
      <view class="section-title">调用统计</view>
      <view v-if="usage" class="usage-grid">
        <view><text>{{ usage.total_calls }}</text><text>总调用</text></view>
        <view><text>{{ usage.success_calls }}</text><text>成功</text></view>
        <view><text>{{ usage.failed_calls }}</text><text>失败</text></view>
        <view><text>{{ usage.charged_calls }}</text><text>已扣费</text></view>
      </view>
      <view v-for="log in logs" :key="log.id" class="log-row">
        <view>
          <view class="log-main">{{ log.endpoint }} · {{ usageStatusText(log.status) }}</view>
          <view class="log-sub">{{ formatTime(log.created_at) }} · {{ log.latency_ms }} ms</view>
        </view>
        <view class="charged">-{{ log.charged_calls }}</view>
      </view>
      <view v-if="!logs.length" class="empty">暂无调用日志。</view>
    </view>

    <view v-if="!apps.length" class="empty-state">
      创建应用后即可获得测试 API 密钥和演示额度。
    </view>

    <view v-if="nameDialogVisible" class="modal-mask">
      <view class="modal">
        <view class="modal-title">{{ nameDialogTitle }}</view>
        <input class="input modal-input" v-model="nameDialogValue" placeholder="请输入密钥名称" />
        <view class="modal-actions">
          <button class="btn ghost" @click="closeNameDialog">取消</button>
          <button class="btn primary" @click="confirmNameDialog">确定</button>
        </view>
      </view>
    </view>

    <view v-if="fullKeyVisible" class="modal-mask">
      <view class="modal wide">
        <view class="modal-title">完整 API 密钥</view>
        <view class="modal-note">请立即复制保存。关闭后，列表中只会展示中间加密后的密钥，无法再次查看完整内容。</view>
        <text selectable class="secret">{{ fullKey }}</text>
        <view class="modal-actions">
          <button class="btn ghost" @click="copyFullKey">复制密钥</button>
          <button class="btn primary" @click="closeFullKey">关闭</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const apps = ref([]);
const selectedApp = ref(null);
const keys = ref([]);
const usage = ref(null);
const logs = ref([]);
const newAppName = ref('演示命名客户端');
const fullKey = ref('');
const fullKeyVisible = ref(false);
const nameDialogVisible = ref(false);
const nameDialogMode = ref('create');
const nameDialogTitle = ref('');
const nameDialogValue = ref('');
const editingKey = ref(null);

const sampleCode = computed(() => `curl -X POST http://127.0.0.1:8000/open/v1/names/game-npc \\
  -H "Authorization: Bearer ak_test_your_api_key" \\
  -H "Content-Type: application/json" \\
  -d '{"scenario":"MMORPG 任务发布 NPC","style":"东方幻想","worldview":"浮空岛世界","gender":"不限","count":5,"avoid_words":[]}'`);

const load = async () => {
  try {
    apps.value = await http.getDeveloperApps();
    if (!apps.value.length) {
      selectedApp.value = null;
      keys.value = [];
      usage.value = null;
      logs.value = [];
      return;
    }
    const current = selectedApp.value && apps.value.find(app => app.id === selectedApp.value.id);
    selectedApp.value = current || apps.value[0];
    await loadSelected();
  } catch (error) {
    console.error(error);
  }
};

const loadSelected = async () => {
  if (!selectedApp.value) return;
  const [keyRows, usageData] = await Promise.all([
    http.getDeveloperKeys(selectedApp.value.id),
    http.getDeveloperUsage(selectedApp.value.id)
  ]);
  keys.value = keyRows;
  usage.value = usageData;
  logs.value = usageData.logs || [];
};

const selectApp = async (app) => {
  selectedApp.value = app;
  closeFullKey();
  await loadSelected();
};

const createApp = async () => {
  const name = newAppName.value.trim();
  if (!name) return uni.showToast({ title: '请输入应用名称', icon: 'none' });
  selectedApp.value = await http.createDeveloperApp(name);
  newAppName.value = '演示命名客户端';
  await load();
};

const deleteApp = () => {
  if (!selectedApp.value) return;
  uni.showModal({
    title: '删除应用',
    content: `确定删除「${appDisplayName(selectedApp.value.name)}」吗？该应用下的 API 密钥也会失效。`,
    confirmText: '删除',
    confirmColor: '#d92d20',
    success: async res => {
      if (!res.confirm) return;
      await http.deleteDeveloperApp(selectedApp.value.id);
      selectedApp.value = null;
      await load();
      uni.showToast({ title: '应用已删除', icon: 'none' });
    }
  });
};

const openCreateKeyDialog = () => {
  nameDialogMode.value = 'create';
  nameDialogTitle.value = '新建 API 密钥';
  nameDialogValue.value = '控制台密钥';
  editingKey.value = null;
  nameDialogVisible.value = true;
};

const openRenameKeyDialog = (key) => {
  nameDialogMode.value = 'rename';
  nameDialogTitle.value = '修改密钥名称';
  nameDialogValue.value = keyDisplayName(key.name);
  editingKey.value = key;
  nameDialogVisible.value = true;
};

const closeNameDialog = () => {
  nameDialogVisible.value = false;
  editingKey.value = null;
};

const confirmNameDialog = async () => {
  const name = nameDialogValue.value.trim();
  if (!name) return uni.showToast({ title: '请输入密钥名称', icon: 'none' });
  if (nameDialogMode.value === 'create') {
    const created = await http.createDeveloperKey(selectedApp.value.id, name);
    fullKey.value = created.api_key;
    fullKeyVisible.value = true;
  } else if (editingKey.value) {
    await http.renameDeveloperKey(editingKey.value.id, name);
    uni.showToast({ title: '密钥名称已更新', icon: 'none' });
  }
  closeNameDialog();
  await loadSelected();
};

const disableKey = async (keyId) => {
  await http.disableDeveloperKey(keyId);
  await loadSelected();
};

const enableKey = async (keyId) => {
  await http.enableDeveloperKey(keyId);
  await loadSelected();
};

const deleteKey = (keyId) => {
  uni.showModal({
    title: '删除密钥',
    content: '确定删除这个 API 密钥吗？删除后将不能继续调用开放接口。',
    confirmText: '删除',
    confirmColor: '#d92d20',
    success: async res => {
      if (!res.confirm) return;
      await http.deleteDeveloperKey(keyId);
      await loadSelected();
      uni.showToast({ title: '密钥已删除', icon: 'none' });
    }
  });
};

const demoRecharge = async () => {
  selectedApp.value = await http.demoRechargeDeveloperApp(selectedApp.value.id);
  await loadSelected();
};

const copyFullKey = () => {
  uni.setClipboardData({
    data: fullKey.value,
    success: () => uni.showToast({ title: '已复制', icon: 'none' })
  });
};

const closeFullKey = () => {
  fullKeyVisible.value = false;
  fullKey.value = '';
};

const maskedKey = key => `${key.key_prefix}****${key.key_tail}`;
const formatTime = value => value ? value.replace('T', ' ').slice(0, 16) : '-';
const keyStatusText = status => ({ active: '启用中', disabled: '已禁用' })[status] || status;
const usageStatusText = status => ({ success: '成功', failed: '失败' })[status] || status;
const appDisplayName = name => ({ 'Demo Naming Client': '演示命名客户端' })[name] || name;
const keyDisplayName = name => ({
  'Dashboard Key': '控制台密钥',
  'Default API Key': '默认 API 密钥'
})[name] || name;

onShow(load);
</script>

<style scoped>
.page{min-height:100vh;padding:28rpx;box-sizing:border-box;background:#f4f6f8;color:#182230}.page button{display:inline-flex;align-items:center;justify-content:center;width:auto;margin:0;padding:0 28rpx;border-radius:8rpx;line-height:1.2}.page button::after{border:0}.topbar{display:flex;align-items:flex-start;justify-content:space-between;gap:24rpx;margin-bottom:22rpx}.topcopy{min-width:0}.title{font-size:42rpx;font-weight:800}.subtitle{margin-top:6rpx;color:#667085;font-size:23rpx}.btn{height:58rpx;white-space:nowrap}.primary{background:#1570ef;color:#fff}.ghost{background:#eef4ff;color:#175cd3}.danger{background:#fef3f2;color:#b42318}.warn{background:#fff7ed;color:#c2410c}.panel{margin-top:20rpx;padding:26rpx;border-radius:12rpx;background:#fff;border:1px solid #e4e7ec}.create-panel{display:flex;align-items:center;gap:16rpx}.input{flex:1;height:76rpx;padding:0 20rpx;border:1px solid #d0d5dd;border-radius:8rpx;background:#fff;box-sizing:border-box}.create-panel .primary{height:76rpx;min-width:190rpx}.app-tabs{display:flex;justify-content:flex-start;gap:14rpx;margin-top:20rpx;overflow-x:auto}.tab{height:72rpx;min-width:180rpx;background:#fff;color:#344054;border:1px solid #d0d5dd}.tab.active{background:#101828;color:#fff}.section-head,.key-row,.log-row{display:flex;align-items:center;justify-content:space-between;gap:24rpx}.section-title{font-size:30rpx;font-weight:800}.muted{margin-top:8rpx;color:#667085;font-size:23rpx}.quota-row{display:grid;grid-template-columns:1fr 1fr auto;align-items:center;gap:28rpx;margin-top:18rpx}.metric-card{min-width:0}.metric{font-size:40rpx;font-weight:800}.metric-label,.key-meta,.log-sub{margin-top:6rpx;color:#667085;font-size:22rpx}.key-row,.log-row{padding:18rpx 0;border-bottom:1px solid #eaecf0}.key-main,.log-row>view:first-child{min-width:0;flex:1}.key-name,.log-main{font-weight:700}.key-actions{display:flex;align-items:center;gap:12rpx;flex-shrink:0}.endpoint{margin-top:12rpx;color:#175cd3;font-weight:700}.code,.secret{display:block;margin-top:10rpx;white-space:pre-wrap;word-break:break-all;font-family:monospace;font-size:22rpx;color:#1d2939}.usage-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12rpx;margin-top:18rpx}.usage-grid view{padding:18rpx 10rpx;border-radius:8rpx;background:#f8fafc;text-align:center}.usage-grid text{display:block}.usage-grid text:first-child{font-size:31rpx;font-weight:800}.usage-grid text:last-child{margin-top:4rpx;color:#667085;font-size:20rpx}.charged{font-weight:800;color:#b42318}.empty,.empty-state{padding:28rpx;color:#667085;text-align:center}.empty-state{margin-top:80rpx}.modal-mask{position:fixed;z-index:99;left:0;right:0;top:0;bottom:0;display:flex;align-items:center;justify-content:center;padding:32rpx;background:rgba(15,23,42,.45)}.modal{width:620rpx;max-width:100%;padding:30rpx;border-radius:12rpx;background:#fff;box-sizing:border-box}.modal.wide{width:760rpx}.modal-title{font-size:32rpx;font-weight:800}.modal-note{margin-top:12rpx;color:#667085;font-size:23rpx;line-height:1.6}.modal-input{width:100%;margin-top:24rpx}.modal-actions{display:flex;justify-content:flex-end;gap:16rpx;margin-top:28rpx}
</style>
