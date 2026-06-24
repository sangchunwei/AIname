<template>
  <view class="page">
    <view class="header">
      <view>
        <view class="header-title">专家工作台</view>
        <view class="header-subtitle">AI 初稿仅供内部辅助，最终报告须人工审核</view>
      </view>
      <view class="header-count">{{ orders.length }} 单</view>
    </view>

    <view v-if="!activeOrder" class="tabs">
      <view :class="{ active: currentTab === 'orders' }" @click="currentTab = 'orders'">订单列表</view>
      <view :class="{ active: currentTab === 'service' }" @click="currentTab = 'service'">发布服务</view>
    </view>

    <view v-if="!activeOrder && currentTab === 'orders'">
      <view class="filter-tabs">
        <view v-for="item in statusTabs" :key="item.value" :class="{ active: statusFilter === item.value }" @click="statusFilter = item.value">
          {{ item.label }} <text>{{ countByStatus(item.value) }}</text>
        </view>
      </view>

      <view v-if="!filteredOrders.length" class="empty">暂无匹配订单</view>
      <view class="order-row" v-for="item in filteredOrders" :key="item.id" @click="openOrder(item)">
        <view class="order-main">
          <view class="order-line">
            <text class="order-name">{{ item.selected_name }}</text>
            <text :class="['status', item.status]">{{ statusText(item.status) }}</text>
          </view>
          <view class="order-meta">
            <text>{{ item.customer_username || `用户 ${item.user_id}` }}</text>
            <text>{{ formatTime(item.created_at) }}</text>
            <text>¥{{ yuan(item.amount_cents) }}</text>
          </view>
        </view>
        <text class="arrow">›</text>
      </view>
    </view>

    <view v-if="!activeOrder && currentTab === 'service'" class="service-form">
      <view class="form-title">发布专家服务</view>
      <input v-model="serviceForm.name" placeholder="服务名称" />
      <textarea v-model="serviceForm.description" placeholder="服务内容说明（至少 10 字）"></textarea>
      <view class="row">
        <input v-model="serviceForm.price" type="digit" placeholder="价格（元）" />
        <input v-model="serviceForm.delivery_days" type="number" placeholder="交付天数" />
      </view>
      <button @click="createService">发布服务</button>
    </view>

    <view v-if="activeOrder" class="detail">
      <view class="detail-bar">
        <text @click="closeOrder">‹ 返回订单</text>
        <text :class="['status', activeOrder.status]">{{ statusText(activeOrder.status) }}</text>
      </view>

      <view class="detail-card">
        <view class="detail-title">{{ activeOrder.selected_name }}</view>
        <view class="detail-grid">
          <view><text>提交用户</text><text>{{ activeOrder.customer_username || `用户 ${activeOrder.user_id}` }}</text></view>
          <view><text>提交时间</text><text>{{ formatTime(activeOrder.created_at) }}</text></view>
          <view><text>订单金额</text><text>¥{{ yuan(activeOrder.amount_cents) }}</text></view>
          <view><text>订单号</text><text>{{ activeOrder.order_no }}</text></view>
        </view>
      </view>

      <view class="detail-card">
        <view class="section-title">用户需求</view>
        <view class="requirements">{{ activeOrder.requirements }}</view>
      </view>

      <view class="detail-card">
        <view class="section-head">
          <view class="section-title">AI 内部初稿</view>
          <button v-if="!activeOrder.ai_draft" size="mini" :loading="loadingId === activeOrder.id" @click="createDraft(activeOrder)">生成初稿</button>
        </view>
        <view v-if="activeOrder.ai_draft" class="draft">{{ activeOrder.ai_draft }}</view>
        <view v-else class="empty-small">尚未生成内部初稿</view>
      </view>

      <view class="detail-card">
        <view class="section-title">最终专家报告</view>
        <textarea class="report" v-model="reports[activeOrder.id]" placeholder="请在审核和修订后填写最终专家报告（至少 50 字）"></textarea>
        <button class="deliver" :disabled="activeOrder.status === 'delivered'" @click="deliver(activeOrder)">
          {{ activeOrder.status === 'delivered' ? '报告已交付' : '交付专家报告' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const currentTab = ref('orders');
const statusFilter = ref('all');
const orders = ref([]);
const reports = ref({});
const activeOrder = ref(null);
const loadingId = ref(null);
const serviceForm = ref({ name: '', description: '', price: '', delivery_days: '3' });
const statusTabs = [
  { label: '全部', value: 'all' },
  { label: '待处理', value: 'paid' },
  { label: '撰写中', value: 'drafting' },
  { label: '已交付', value: 'delivered' },
];

const filteredOrders = computed(() => {
  if (statusFilter.value === 'all') return orders.value;
  return orders.value.filter(item => item.status === statusFilter.value);
});

const load = async () => {
  try {
    orders.value = await http.getExpertWorkbenchOrders();
    orders.value.forEach(item => {
      if (item.final_report) reports.value[item.id] = item.final_report;
    });
    if (activeOrder.value) {
      const latest = orders.value.find(item => item.id === activeOrder.value.id);
      if (latest) activeOrder.value = latest;
    }
  } finally {
    uni.stopPullDownRefresh();
  }
};

const openOrder = item => {
  activeOrder.value = item;
  reports.value[item.id] = reports.value[item.id] || item.final_report || item.ai_draft || '';
};
const closeOrder = () => { activeOrder.value = null; };
const yuan = cents => (cents / 100).toFixed(2);
const formatTime = value => value ? value.replace('T', ' ').slice(0, 16) : '-';
const statusText = status => ({ paid: '待处理', drafting: '撰写中', delivered: '已交付' })[status] || status;
const countByStatus = status => status === 'all' ? orders.value.length : orders.value.filter(item => item.status === status).length;
const mergeOrder = updated => {
  const index = orders.value.findIndex(item => item.id === updated.id);
  if (index >= 0) {
    orders.value[index] = { ...orders.value[index], ...updated };
    activeOrder.value = orders.value[index];
  }
};

const createDraft = async item => {
  loadingId.value = item.id;
  try {
    const updated = await http.generateExpertDraft(item.id);
    mergeOrder(updated);
    reports.value[item.id] = updated.ai_draft || '';
  } finally {
    loadingId.value = null;
  }
};

const deliver = async item => {
  if (item.status === 'delivered') return;
  const report = reports.value[item.id];
  if (!report || report.length < 50) return uni.showToast({ title: '最终报告至少 50 字', icon: 'none' });
  const updated = await http.deliverExpertReport(item.id, report);
  mergeOrder(updated);
  uni.showToast({ title: '报告已交付' });
};

const createService = async () => {
  const data = serviceForm.value;
  if (!data.name || data.description.length < 10 || !Number(data.price)) {
    return uni.showToast({ title: '请完整填写服务信息', icon: 'none' });
  }
  await http.createExpertService({
    name: data.name,
    description: data.description,
    price_cents: Math.round(Number(data.price) * 100),
    delivery_days: Number(data.delivery_days) || 3,
  });
  serviceForm.value = { name: '', description: '', price: '', delivery_days: '3' };
  uni.showToast({ title: '服务发布成功' });
  currentTab.value = 'orders';
};

onLoad(load);
onPullDownRefresh(load);
</script>

<style scoped>
.page{min-height:100vh;padding:26rpx;box-sizing:border-box;background:#f3f5f8}.header{display:flex;align-items:center;justify-content:space-between;padding:30rpx;border-radius:18rpx;background:#172554;color:#fff}.header-title{font-size:38rpx;font-weight:700}.header-subtitle{margin-top:10rpx;color:#c7d2fe;font-size:21rpx}.header-count{padding:8rpx 18rpx;border-radius:999rpx;background:rgba(255,255,255,.14);font-size:23rpx}.tabs,.filter-tabs{display:flex;margin-top:22rpx;padding:8rpx;border-radius:14rpx;background:#fff}.tabs view,.filter-tabs view{flex:1;height:64rpx;line-height:64rpx;text-align:center;color:#64748b;font-size:25rpx}.tabs .active,.filter-tabs .active{border-radius:10rpx;background:#eef2ff;color:#4338ca;font-weight:700}.filter-tabs text{margin-left:6rpx;color:#94a3b8}.order-row{display:flex;align-items:center;margin-top:14rpx;padding:22rpx;border-radius:14rpx;background:#fff}.order-main{flex:1;min-width:0}.order-line{display:flex;align-items:center;gap:14rpx}.order-name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#1e293b;font-size:29rpx;font-weight:700}.status{flex-shrink:0;padding:5rpx 14rpx;border-radius:999rpx;background:#eef2ff;color:#4338ca;font-size:21rpx}.status.drafting{background:#fff7ed;color:#c2410c}.status.delivered{background:#ecfdf3;color:#027a48}.order-meta{display:flex;gap:18rpx;margin-top:10rpx;color:#94a3b8;font-size:21rpx;white-space:nowrap;overflow:hidden}.order-meta text{overflow:hidden;text-overflow:ellipsis}.arrow{margin-left:18rpx;color:#94a3b8;font-size:44rpx}.empty,.empty-small{padding:120rpx 0;text-align:center;color:#94a3b8}.empty-small{padding:36rpx 0}.detail-bar{display:flex;align-items:center;justify-content:space-between;margin-top:22rpx;color:#4338ca;font-size:26rpx}.detail-card,.service-form{margin-top:18rpx;padding:26rpx;border-radius:16rpx;background:#fff}.detail-title{font-size:36rpx;font-weight:800;color:#1e293b}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:18rpx;margin-top:22rpx}.detail-grid view text{display:block}.detail-grid view text:first-child{color:#94a3b8;font-size:21rpx}.detail-grid view text:last-child{margin-top:6rpx;color:#334155;font-size:24rpx;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.section-title,.form-title{font-size:29rpx;font-weight:700;color:#1e293b}.section-head{display:flex;align-items:center;justify-content:space-between;gap:18rpx}.section-head button{margin:0;background:#eef2ff;color:#4338ca}.requirements,.draft{margin-top:16rpx;color:#475569;font-size:25rpx;line-height:1.7;white-space:pre-wrap}.draft{padding:20rpx;border-radius:12rpx;background:#f8fafc}.report{width:100%;height:320rpx;margin-top:18rpx;padding:18rpx;box-sizing:border-box;border:1px solid #fde68a;border-radius:10rpx;background:#fffdf5}.deliver{margin-top:18rpx;background:#0f766e;color:#fff}.deliver[disabled]{background:#cbd5e1;color:#fff}.service-form input{height:74rpx;border-bottom:1px solid #eee}.service-form textarea{width:100%;height:150rpx;margin-top:12rpx;padding:14rpx;box-sizing:border-box;background:#f8fafc}.service-form .row{display:flex;gap:18rpx}.service-form .row input{flex:1}.service-form button{margin-top:16rpx;background:#0f766e;color:#fff}
</style>
