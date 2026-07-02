<template>
  <view class="page" v-if="data">
    <view class="wallet">
      <view class="label">可用余额</view>
      <view class="amount">¥{{ yuan(data.wallet.available_cents) }}</view>
      <view class="sub">冻结 ¥{{ yuan(data.wallet.frozen_cents) }} · 待结算 ¥{{ yuan(data.wallet.pending_cents) }}</view>
      <view class="bonus">高级 AI 奖励次数：{{ data.wallet.bonus_ai_credits }}</view>
    </view>

    <view class="panel">
      <view class="title">支付宝沙箱充值</view>
      <input class="input" v-model="rechargeAmount" type="digit" placeholder="充值金额（元）" />
      <button class="primary" @click="recharge">支付宝沙箱充值</button>
      <view class="tip">将打开支付宝沙箱 H5 收银台，支付成功后自动入账到钱包余额。</view>
    </view>

    <view class="panel">
      <view class="title">支付宝提现申请</view>
      <view class="input readonly">提现方式：支付宝账号</view>
      <input class="input" v-model="withdraw.account_name" placeholder="收款人姓名" />
      <input class="input" v-model="withdraw.destination" placeholder="支付宝账号" />
      <input class="input" v-model="withdraw.amount" type="digit" placeholder="提现金额（元）" />
      <button class="secondary" @click="submitWithdraw">提交提现申请</button>
      <view class="tip">提现仍为后台审核后的模拟打款，不接入微信或银行卡。</view>
    </view>

    <view class="panel">
      <view class="title">邀请好友</view>
      <view class="code">邀请码：{{ data.referral.code }}</view>
      <image v-if="data.referral.qr_file_url" class="qr" :src="http.getAssetUrl(data.referral.qr_file_url)" />
      <view class="invite-url" @click="copyInvite">{{ data.referral.invite_url }}</view>
      <view class="tip">已邀请 {{ data.referral.invited_count }} 人；好友注册后双方获得高级 AI 次数。</view>
    </view>

    <view class="panel">
      <view class="title">分销合伙人</view>
      <view v-if="data.partner">状态：{{ partnerStatus(data.partner.status) }} · 佣金比例 {{ (data.partner.commission_bps/100).toFixed(2) }}%</view>
      <template v-else>
        <input class="input" v-model="partner.business_type" placeholder="类型：孕婴店/工商代办等" />
        <input class="input" v-model="partner.business_name" placeholder="门店或企业名称" />
        <input class="input" v-model="partner.contact_info" placeholder="联系方式" />
        <button class="partner-btn" @click="applyPartner">申请成为合伙人</button>
      </template>
    </view>

    <view class="panel" v-if="data.commissions.length">
      <view class="title">佣金记录</view>
      <view class="row" v-for="item in data.commissions" :key="item.id">
        <text>{{ item.commission_type === 'expert' ? '专家收入' : '分销佣金' }}</text>
        <text>¥{{ yuan(item.commission_cents) }} · {{ commissionStatus(item.status) }}</text>
      </view>
    </view>

    <view class="panel">
      <view class="title">资金流水</view>
      <view class="row" v-for="item in data.ledger" :key="item.id">
        <view>
          <view>{{ item.description }}</view>
          <view class="time">{{ item.created_at?.slice(0,16).replace('T',' ') }}</view>
        </view>
        <text :class="ledgerClass(item)">{{ ledgerDelta(item) }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const data = ref(null);
const rechargeAmount = ref('');
const withdraw = ref({ method: 'alipay', account_name: '', destination: '', amount: '' });
const partner = ref({ business_type: '', business_name: '', contact_info: '' });

const yuan = cents => (cents / 100).toFixed(2);
const load = async () => {
  try { data.value = await http.getGrowthCenter(); }
  finally { uni.stopPullDownRefresh(); }
};
const openPayUrl = pay => {
  if (!pay?.pay_url) return uni.showToast({ title: '支付订单状态异常', icon: 'none' });
  if (typeof window !== 'undefined') {
    const opened = window.open(pay.pay_url, '_blank');
    if (!opened) window.location.href = pay.pay_url;
    else uni.navigateTo({ url: `/pages/payment-result/payment-result?out_trade_no=${encodeURIComponent(pay.out_trade_no)}` });
    return;
  }
  uni.setClipboardData({ data: pay.pay_url });
  uni.showToast({ title: '支付链接已复制', icon: 'none' });
};
const recharge = async () => {
  const cents = Math.round(Number(rechargeAmount.value) * 100);
  if (cents < 100) return uni.showToast({ title: '最低充值 1 元', icon: 'none' });
  const order = await http.createRecharge(cents);
  const pay = await http.alipayRecharge(order.id);
  rechargeAmount.value = '';
  openPayUrl(pay);
};
const submitWithdraw = async () => {
  const w = withdraw.value;
  const cents = Math.round(Number(w.amount) * 100);
  if (cents < 100 || !w.account_name || !w.destination) {
    return uni.showToast({ title: '请完整填写支付宝提现信息', icon: 'none' });
  }
  await http.createWithdrawal({ amount_cents: cents, method: 'alipay', destination: w.destination, account_name: w.account_name });
  withdraw.value = { method: 'alipay', account_name: '', destination: '', amount: '' };
  uni.showToast({ title: '申请已提交' });
  load();
};
const applyPartner = async () => {
  await http.applyPartner(partner.value);
  uni.showToast({ title: '申请已提交' });
  load();
};
const ledgerDelta = item => {
  if (item.bonus_delta) return `${item.bonus_delta > 0 ? '+' : ''}${item.bonus_delta} 次`;
  return `${item.available_delta >= 0 ? '+' : ''}¥${yuan(item.available_delta)}`;
};
const ledgerClass = item => (item.bonus_delta || item.available_delta) >= 0 ? 'income' : 'expense';
const copyInvite = () => uni.setClipboardData({ data: data.value.referral.invite_url });
const partnerStatus = status => ({ pending: '审核中', approved: '已通过', rejected: '已驳回' })[status] || status;
const commissionStatus = status => ({ pending: '待结算', settled: '已结算', rejected: '已驳回' })[status] || status;
onLoad(load);
onPullDownRefresh(load);
</script>

<style scoped>
.page{min-height:100vh;padding:26rpx;background:#f3f5f8}.wallet{padding:38rpx;border-radius:22rpx;background:linear-gradient(135deg,#064e3b,#0f766e);color:#fff}.label{color:#a7f3d0}.amount{margin-top:8rpx;font-size:60rpx;font-weight:700}.sub,.bonus{margin-top:10rpx;color:#ccfbf1;font-size:23rpx}.panel{margin-top:22rpx;padding:28rpx;border-radius:18rpx;background:#fff}.title{margin-bottom:18rpx;font-size:30rpx;font-weight:700}.input{height:76rpx;padding:0 14rpx;border-bottom:1px solid #eee;line-height:76rpx}.readonly{color:#0f766e;background:#f8fafc}.primary,.secondary,.partner-btn{margin-top:20rpx;color:#fff}.primary{background:#1677ff}.secondary{background:#ea580c}.partner-btn{background:#0f766e}.tip{margin-top:14rpx;color:#94a3b8;font-size:21rpx}.code{text-align:center;font-size:31rpx;font-weight:700}.qr{display:block;width:300rpx;height:300rpx;margin:20rpx auto}.invite-url{word-break:break-all;color:#4f46e5;font-size:22rpx}.row{display:flex;justify-content:space-between;padding:16rpx 0;border-bottom:1px solid #f1f5f9;font-size:24rpx}.time{margin-top:5rpx;color:#94a3b8;font-size:20rpx}.income{color:#059669}.expense{color:#dc2626}
</style>
