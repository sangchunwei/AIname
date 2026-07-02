<template>
  <view class="page">
    <view class="panel">
      <view class="status" :class="statusClass">{{ statusTitle }}</view>
      <view class="desc">{{ statusDesc }}</view>
      <view v-if="payment" class="meta">
        <view><text>交易号</text><text>{{ payment.out_trade_no }}</text></view>
        <view><text>金额</text><text>¥{{ yuan(payment.amount_cents) }}</text></view>
      </view>
      <button class="primary" :loading="loading" @click="refreshStatus(true)">刷新支付状态</button>
      <button class="secondary" @click="goBack">返回</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const outTradeNo = ref('');
const payment = ref(null);
const loading = ref(false);
const successHandled = ref(false);

const yuan = cents => (cents / 100).toFixed(2);

const loadLocalStatus = async () => {
  if (!outTradeNo.value) return;
  payment.value = await http.getPaymentStatus(outTradeNo.value);
};

const showInProgress = () => {
  uni.showModal({
    title: '支付正在进行中',
    content: '暂未从支付宝沙箱查询到支付成功，请稍后再刷新。',
    showCancel: false
  });
};

const showSuccessAndBack = () => {
  if (successHandled.value) return;
  successHandled.value = true;
  uni.showModal({
    title: '购买成功',
    content: '支付已确认，权益或钱包余额已更新。',
    showCancel: false,
    success: () => goBack()
  });
};

const refreshStatus = async (manual = true) => {
  if (!outTradeNo.value || loading.value || successHandled.value) return;
  loading.value = true;
  try {
    payment.value = await http.syncAlipayPayment(outTradeNo.value);
    if (payment.value?.status === 'paid') {
      showSuccessAndBack();
    } else if (manual) {
      showInProgress();
    }
  } catch (_) {
    try { await loadLocalStatus(); } catch (error) { console.error(error); }
    if (manual) showInProgress();
  } finally {
    loading.value = false;
  }
};

const statusTitle = computed(() => {
  if (!payment.value) return loading.value ? '正在查询支付状态' : '等待支付结果';
  return payment.value.status === 'paid' ? '支付成功' : '支付待确认';
});

const statusDesc = computed(() => {
  if (!payment.value) return '付款后点击刷新支付状态，系统会主动查询支付宝沙箱交易。';
  return payment.value.status === 'paid'
    ? '业务权益和钱包余额已更新。'
    : '点击刷新支付状态，确认成功后会自动返回。';
});

const statusClass = computed(() => payment.value?.status === 'paid' ? 'success' : 'pending');

const goBack = () => {
  const type = payment.value?.business_type;
  if (type === 'recharge') return uni.reLaunch({ url: '/pages/wallet-growth/wallet-growth' });
  return uni.reLaunch({ url: '/pages/user-center/user-center' });
};

onLoad(query => {
  outTradeNo.value = query?.out_trade_no || '';
  loadLocalStatus();
});
</script>

<style scoped>
.page{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:32rpx;background:#f3f5f8;box-sizing:border-box}.panel{width:100%;padding:44rpx 32rpx;border-radius:18rpx;background:#fff;text-align:center}.status{font-size:42rpx;font-weight:800}.status.success{color:#059669}.status.pending{color:#f97316}.desc{margin-top:18rpx;color:#64748b;font-size:26rpx;line-height:1.6}.meta{margin-top:28rpx;padding:20rpx;background:#f8fafc;text-align:left}.meta view{display:flex;justify-content:space-between;padding:10rpx 0;color:#334155;font-size:24rpx}.primary,.secondary{margin-top:24rpx}.primary{background:#1677ff;color:#fff}.secondary{background:#eef2ff;color:#4338ca}
</style>
