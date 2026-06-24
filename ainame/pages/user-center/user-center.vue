<template>
  <view class="page" v-if="info">
    <view class="profile-card">
      <image v-if="info.avatar_url" class="avatar avatar-image" :src="http.getAssetUrl(info.avatar_url)" mode="aspectFill" />
      <view v-else class="avatar">{{ info.username.slice(0, 1) }}</view>
      <view class="profile-main">
        <view class="name-row"><text class="name">{{ info.username }}</text><text :class="['vip-tag', info.subscription.is_vip ? 'active' : '']">{{ info.subscription.is_vip ? 'VIP' : '普通用户' }}</text></view>
        <view class="email">{{ info.email }}</view>
        <view v-if="info.subscription.is_vip" class="expires">到期：{{ formatTime(info.subscription.expires_at) }}</view>
      </view>
    </view>

    <view class="panel">
      <view class="panel-title">本周额度</view>
      <view class="quota"><text>智能起名</text><text>{{ info.usage.name_used }} / {{ info.usage.name_limit }}</text></view>
      <view class="progress"><view :style="{width: percent(info.usage.name_used, info.usage.name_limit)}"></view></view>
      <view class="quota"><text>视觉生成</text><text>{{ info.usage.visual_used }} / {{ info.usage.visual_limit }}</text></view>
      <view class="progress"><view :style="{width: percent(info.usage.visual_used, info.usage.visual_limit)}"></view></view>
    </view>

    <view class="panel">
      <view class="panel-title">个人资料</view>
      <view class="info-row"><text>昵称</text><text>{{ info.username }}</text></view>
      <view class="info-row"><text>邮箱</text><text>{{ info.email }}</text></view>
      <view class="info-row"><text>账号类型</text><text>{{ info.is_expert ? '认证专家' : '普通用户' }}</text></view>
      <view class="info-row"><text>注册时间</text><text>{{ formatTime(info.created_at) }}</text></view>
      <view class="bio-row"><text>个人简介</text><text>{{ info.bio || '暂未填写' }}</text></view>
      <button class="settings-btn" @click="goSettings">修改个人信息</button>
    </view>
    <button class="wallet-btn" @click="goWallet">钱包、邀请与合伙人</button>
    <button class="developer-btn" @click="goDeveloper">B 端开放平台</button>

    <view class="panel">
      <view class="panel-title">VIP 套餐</view>
      <view class="plan" v-for="plan in plans" :key="plan.id">
        <view><view class="plan-name">{{ plan.name }}</view><view class="plan-desc">{{ plan.description }}</view></view>
        <view class="plan-side"><view class="price">¥{{ (plan.price_cents / 100).toFixed(2) }}</view><button size="mini" @click="buyPlan(plan)">购买</button></view>
      </view>
      <view class="notice">当前为支付测试阶段。只有后端开启模拟支付后，测试购买才会自动开通。</view>
    </view>

    <view class="panel" v-if="orders.length">
      <view class="panel-title">专家订单</view>
      <view class="order" v-for="order in displayedOrders" :key="order.id" @click="showReport(order)">
        <view class="order-head">
          <text class="order-name">{{ order.selected_name }}</text>
          <text :class="['order-status', ['pending_payment', 'payment_timeout', 'canceled'].includes(order.status) ? 'warning' : '']">{{ statusText(order) }}</text>
        </view>
        <view class="order-meta">
          <text>订单号 {{ order.order_no }}</text>
          <text>¥{{ (order.amount_cents / 100).toFixed(2) }}</text>
        </view>
        <view v-if="order.status === 'pending_payment'" class="payment-countdown">支付剩余 {{ remainingText(order) }}</view>
        <view v-if="order.status === 'payment_timeout'" class="timeout-text">订单支付超时，自动取消</view>
        <view class="order-summary">{{ order.requirements }}</view>
        <view v-if="order.status === 'pending_payment'" class="order-actions">
          <button size="mini" @click.stop="continuePay(order)">继续付款</button>
          <button size="mini" class="cancel-order" @click.stop="cancelOrder(order)">取消订单</button>
        </view>
        <view v-if="canViewReport(order)" class="report-entry">
          <text>专家回复已送达</text>
          <button size="mini" @click.stop="showReport(order)">查看详情</button>
        </view>
      </view>
      <view v-if="sortedOrders.length > 2" class="more-orders" @click="showAllOrders = !showAllOrders">
        {{ showAllOrders ? '收起订单' : `查看更多 ${sortedOrders.length - 2} 条订单` }}
      </view>
    </view>

    <view v-if="activeReport" class="modal-mask" @click="closeReport">
      <view class="report-modal" @click.stop>
        <view class="modal-head">
          <view>
            <view class="modal-title">{{ activeReport.selected_name }}</view>
            <view class="modal-subtitle">{{ formatTime(activeReport.delivered_at) }} 交付</view>
          </view>
          <text class="modal-close" @click="closeReport">×</text>
        </view>
        <scroll-view scroll-y class="report-scroll">
          <view class="report-full">{{ activeReport.final_report }}</view>
        </scroll-view>
      </view>
    </view>

    <button v-if="info.is_expert" class="expert-btn" @click="goWorkbench">进入专家工作台</button>
    <button class="logout" @click="logout">退出登录</button>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onHide, onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const info = ref(null);
const plans = ref([]);
const orders = ref([]);
const activeReport = ref(null);
const showAllOrders = ref(false);
const nowTs = ref(Date.now());
const timer = ref(null);
const refreshingTimeout = ref(false);

const load = async () => {
  try {
    const [center, vipPlans, expertOrders] = await Promise.all([http.getUserCenter(), http.getVipPlans(), http.getExpertOrders()]);
    info.value = center; plans.value = vipPlans; orders.value = expertOrders;
  } catch (error) { console.error(error); }
};
const buyPlan = (plan) => uni.showModal({ title: `购买${plan.name}`, content: '当前将创建测试订单并尝试模拟付款。', success: async res => {
  if (!res.confirm) return; const order = await http.createVipOrder(plan.code); await http.payVipWithBalance(order.id); uni.showToast({ title: '余额支付成功' }); load();
}});
const percent = (used, limit) => `${Math.min(100, limit ? used / limit * 100 : 0)}%`;
const formatTime = value => value ? value.replace('T', ' ').slice(0, 16) : '-';
const deadlineTs = order => new Date(order.created_at).getTime() + 10 * 60 * 1000;
const remainingSeconds = order => Math.max(0, Math.floor((deadlineTs(order) - nowTs.value) / 1000));
const remainingText = order => {
  const seconds = remainingSeconds(order);
  const minutes = Math.floor(seconds / 60);
  return `${String(minutes).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
};
const sortedOrders = computed(() => [...orders.value].sort((a, b) => {
  const priority = status => ({ pending_payment: 0, paid: 1, drafting: 1 })[status] ?? 2;
  const diff = priority(a.status) - priority(b.status);
  if (diff !== 0) return diff;
  return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
}));
const displayedOrders = computed(() => showAllOrders.value ? sortedOrders.value : sortedOrders.value.slice(0, 2));
const statusText = order => {
  if (order.status === 'delivered' && !order.paid_at) return '已交付（未记录付款）';
  return ({ pending_payment: '待付款', paid: '已付款，待专家处理', drafting: '专家撰写中', delivered: '已交付', canceled: '已取消', payment_timeout: '订单支付超时，自动取消' })[order.status] || order.status;
};
const canViewReport = order => order.status === 'delivered' && !!order.final_report;
const showReport = order => {
  if (!canViewReport(order)) {
    const title = order.status === 'pending_payment' ? '订单待付款，付款后专家才能处理' : '专家回复尚未交付';
    return uni.showToast({ title, icon: 'none' });
  }
  activeReport.value = order;
};
const closeReport = () => { activeReport.value = null; };
const continuePay = async order => {
  if (remainingSeconds(order) <= 0) return load();
  try {
    await http.payExpertWithBalance(order.id);
    uni.showToast({ title: '余额支付成功' });
    load();
  } catch (_) {
    uni.showModal({ title: '余额不足', content: '是否前往钱包充值后继续支付？', confirmText: '去充值', cancelText: '取消', success: res => {
      if (res.confirm) goWallet();
    }});
  }
};
const cancelOrder = order => uni.showModal({ title: '取消订单', content: '确认取消该待付款订单？', success: async res => {
  if (!res.confirm) return;
  await http.cancelExpertOrder(order.id);
  uni.showToast({ title: '订单已取消' });
  load();
}});
const startTimer = () => {
  if (timer.value) return;
  timer.value = setInterval(async () => {
    nowTs.value = Date.now();
    if (refreshingTimeout.value) return;
    if (orders.value.some(order => order.status === 'pending_payment' && remainingSeconds(order) <= 0)) {
      refreshingTimeout.value = true;
      try { await load(); } finally { refreshingTimeout.value = false; }
    }
  }, 1000);
};
const stopTimer = () => {
  if (!timer.value) return;
  clearInterval(timer.value);
  timer.value = null;
};
const goWorkbench = () => uni.navigateTo({ url: '/pages/expert-workbench/expert-workbench' });
const goSettings = () => uni.navigateTo({ url: '/pages/account-settings/account-settings' });
const goWallet = () => uni.navigateTo({ url: '/pages/wallet-growth/wallet-growth' });
const goDeveloper = () => uni.navigateTo({ url: '/pages/developer-dashboard/developer-dashboard' });
const logout = () => { uni.clearStorageSync(); uni.reLaunch({ url: '/pages/login/login' }); };
onShow(() => { load(); startTimer(); });
onHide(stopTimer);
</script>

<style scoped>
.page{min-height:100vh;padding:28rpx;box-sizing:border-box;background:#f3f5f8}.profile-card{display:flex;padding:36rpx;border-radius:22rpx;background:linear-gradient(135deg,#172554,#6d28d9);color:#fff}.avatar{display:flex;width:104rpx;height:104rpx;align-items:center;justify-content:center;border-radius:52rpx;background:rgba(255,255,255,.18);font-size:48rpx}.profile-main{margin-left:24rpx}.name-row{display:flex;align-items:center}.name{font-size:38rpx;font-weight:700}.vip-tag{margin-left:14rpx;padding:4rpx 13rpx;border-radius:20rpx;background:#64748b;font-size:20rpx}.vip-tag.active{background:#f59e0b}.email,.expires{margin-top:9rpx;color:#ddd6fe;font-size:23rpx}.panel{margin-top:22rpx;padding:28rpx;border-radius:18rpx;background:#fff}.panel-title{margin-bottom:20rpx;font-size:31rpx;font-weight:700}.quota{display:flex;justify-content:space-between;margin-top:18rpx;color:#475569;font-size:25rpx}.progress{height:12rpx;margin-top:9rpx;border-radius:8rpx;background:#e2e8f0;overflow:hidden}.progress view{height:100%;background:#6366f1}.info-row,.bio-row{display:flex;justify-content:space-between;padding:18rpx 0;border-bottom:1px solid #f0f2f5;color:#64748b;font-size:25rpx}.info-row text:last-child{max-width:440rpx;text-align:right;color:#1e293b}.bio-row{display:block}.bio-row text{display:block}.bio-row text:last-child{margin-top:12rpx;color:#1e293b;line-height:1.6}.settings-btn{margin-top:22rpx;background:#eef2ff;color:#4338ca}.wallet-btn{margin-top:22rpx;background:#0f766e;color:#fff}.plan{display:flex;justify-content:space-between;padding:20rpx 0;border-bottom:1px solid #f0f2f5}.plan-name,.order-name{font-weight:700}.plan-desc{max-width:430rpx;margin-top:8rpx;color:#8490a2;font-size:22rpx}.plan-side{text-align:right}.price{margin-bottom:8rpx;color:#e8590c;font-weight:700}.notice{margin-top:18rpx;color:#9a6700;font-size:21rpx}.order{padding:20rpx 0;border-bottom:1px solid #eee}.order-head,.order-meta,.report-entry{display:flex;align-items:center;justify-content:space-between;gap:18rpx}.order-status{flex-shrink:0;color:#6366f1;font-size:23rpx}.order-status.warning{color:#f97316}.order-meta{margin-top:10rpx;color:#94a3b8;font-size:21rpx}.order-summary{margin-top:12rpx;color:#64748b;font-size:23rpx;line-height:1.55;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}.report-entry{margin-top:16rpx;padding:16rpx;background:#f8fafc;color:#0f766e;font-size:24rpx}.report-entry button{margin:0;background:#0f766e;color:#fff}.modal-mask{position:fixed;left:0;right:0;top:0;bottom:0;z-index:99;display:flex;align-items:center;justify-content:center;padding:34rpx;background:rgba(15,23,42,.45)}.report-modal{width:660rpx;max-width:100%;max-height:78vh;padding:30rpx;box-sizing:border-box;border-radius:18rpx;background:#fff}.modal-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20rpx}.modal-title{font-size:34rpx;font-weight:800;color:#1e293b}.modal-subtitle{margin-top:8rpx;color:#94a3b8;font-size:23rpx}.modal-close{font-size:44rpx;color:#64748b;line-height:1}.report-scroll{max-height:56vh;margin-top:22rpx}.report-full{color:#334155;font-size:27rpx;line-height:1.75;white-space:pre-wrap}.expert-btn{margin-top:24rpx;background:#0f766e;color:#fff}.logout{margin-top:24rpx;background:#fff;color:#dc2626}
.avatar-image{display:block;flex-shrink:0}
.developer-btn{margin-top:22rpx;background:#1570ef;color:#fff}
.payment-countdown{margin-top:12rpx;color:#f97316;font-size:23rpx}
.timeout-text{margin-top:12rpx;color:#dc2626;font-size:23rpx}
.order-actions{display:flex;gap:14rpx;margin-top:16rpx}
.order-actions button{flex:1;margin:0;background:#0f766e;color:#fff}
.order-actions .cancel-order{background:#f1f5f9;color:#475569}
.more-orders{padding:22rpx 0 4rpx;text-align:center;color:#4338ca;font-size:25rpx;font-weight:700}
</style>
