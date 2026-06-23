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
      <view class="panel-title">今日额度</view>
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
      <view class="order" v-for="order in orders" :key="order.id">
        <view><text class="order-name">{{ order.selected_name }}</text><text class="order-status">{{ statusText(order.status) }}</text></view>
        <view v-if="order.final_report" class="report">{{ order.final_report }}</view>
      </view>
    </view>

    <button v-if="info.is_expert" class="expert-btn" @click="goWorkbench">进入专家工作台</button>
    <button class="logout" @click="logout">退出登录</button>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const info = ref(null);
const plans = ref([]);
const orders = ref([]);

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
const statusText = status => ({pending_payment:'待付款',paid:'待专家处理',drafting:'专家撰写中',delivered:'已交付'})[status] || status;
const goWorkbench = () => uni.navigateTo({ url: '/pages/expert-workbench/expert-workbench' });
const goSettings = () => uni.navigateTo({ url: '/pages/account-settings/account-settings' });
const goWallet = () => uni.navigateTo({ url: '/pages/wallet-growth/wallet-growth' });
const logout = () => { uni.clearStorageSync(); uni.reLaunch({ url: '/pages/login/login' }); };
onShow(load);
</script>

<style scoped>
.page{min-height:100vh;padding:28rpx;box-sizing:border-box;background:#f3f5f8}.profile-card{display:flex;padding:36rpx;border-radius:22rpx;background:linear-gradient(135deg,#172554,#6d28d9);color:#fff}.avatar{display:flex;width:104rpx;height:104rpx;align-items:center;justify-content:center;border-radius:52rpx;background:rgba(255,255,255,.18);font-size:48rpx}.profile-main{margin-left:24rpx}.name-row{display:flex;align-items:center}.name{font-size:38rpx;font-weight:700}.vip-tag{margin-left:14rpx;padding:4rpx 13rpx;border-radius:20rpx;background:#64748b;font-size:20rpx}.vip-tag.active{background:#f59e0b}.email,.expires{margin-top:9rpx;color:#ddd6fe;font-size:23rpx}.panel{margin-top:22rpx;padding:28rpx;border-radius:18rpx;background:#fff}.panel-title{margin-bottom:20rpx;font-size:31rpx;font-weight:700}.quota{display:flex;justify-content:space-between;margin-top:18rpx;color:#475569;font-size:25rpx}.progress{height:12rpx;margin-top:9rpx;border-radius:8rpx;background:#e2e8f0;overflow:hidden}.progress view{height:100%;background:#6366f1}.info-row,.bio-row{display:flex;justify-content:space-between;padding:18rpx 0;border-bottom:1px solid #f0f2f5;color:#64748b;font-size:25rpx}.info-row text:last-child{max-width:440rpx;text-align:right;color:#1e293b}.bio-row{display:block}.bio-row text{display:block}.bio-row text:last-child{margin-top:12rpx;color:#1e293b;line-height:1.6}.settings-btn{margin-top:22rpx;background:#eef2ff;color:#4338ca}.wallet-btn{margin-top:22rpx;background:#0f766e;color:#fff}.plan{display:flex;justify-content:space-between;padding:20rpx 0;border-bottom:1px solid #f0f2f5}.plan-name,.order-name{font-weight:700}.plan-desc{max-width:430rpx;margin-top:8rpx;color:#8490a2;font-size:22rpx}.plan-side{text-align:right}.price{margin-bottom:8rpx;color:#e8590c;font-weight:700}.notice{margin-top:18rpx;color:#9a6700;font-size:21rpx}.order{padding:18rpx 0;border-bottom:1px solid #eee}.order-status{float:right;color:#6366f1;font-size:23rpx}.report{margin-top:12rpx;padding:16rpx;background:#f8fafc;color:#475569;font-size:23rpx;white-space:pre-wrap}.expert-btn{margin-top:24rpx;background:#0f766e;color:#fff}.logout{margin-top:24rpx;background:#fff;color:#dc2626}
.avatar-image{display:block;flex-shrink:0}
</style>
