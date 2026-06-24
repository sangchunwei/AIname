<template>
  <view class="page">
    <view class="hero"><view class="hero-title">真人专家精批</view><view>AI 提效，专家审核，为重要名字提供更有分量的决策依据。</view></view>
    <view v-if="!services.length" class="empty">暂无已认证专家服务</view>
    <view class="service" v-for="item in services" :key="item.id">
      <view class="expert-row"><view class="avatar">{{ item.expert_name.slice(0,1) }}</view><view><view class="expert-name">{{ item.expert_name }} <text>已认证</text></view><view class="expert-title">{{ item.expert_title }} · {{ item.category }}</view></view></view>
      <view class="service-name">{{ item.name }}</view><view class="desc">{{ item.description }}</view>
      <view class="footer"><view><text class="price">¥{{ (item.price_cents/100).toFixed(2) }}</text><text class="days">约 {{ item.delivery_days }} 天交付</text></view><button size="mini" @click="selectService(item)">立即咨询</button></view>
    </view>
    <view class="order-panel" v-if="selectedService">
      <view class="close" @click="selectedService=null">×</view><view class="panel-title">提交精批需求</view><view class="chosen">{{ selectedService.expert_name }} · {{ selectedService.name }}</view>
      <input class="input" v-model="orderForm.selected_name" placeholder="需要精批的姓名或品牌名"/><textarea class="textarea" v-model="orderForm.requirements" placeholder="详细说明背景、用途和关注点"></textarea>
      <button class="submit" @click="submitOrder">创建订单</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';import { onShow } from '@dcloudio/uni-app';import http from '@/http/http.js';
const services=ref([]),selectedService=ref(null),orderForm=ref({selected_name:'',requirements:''});
const load=async()=>services.value=await http.getExpertServices();
const selectService=item=>selectedService.value=item;
const goRecharge=()=>uni.navigateTo({url:'/pages/wallet-growth/wallet-growth'});
const handlePayError=order=>uni.showModal({title:'余额不足',content:'订单已保留 10 分钟。是否前往钱包充值后继续支付？',confirmText:'去充值',cancelText:'暂不处理',success:res=>{if(res.confirm)goRecharge();else uni.showToast({title:'订单已进入待付款',icon:'none'})}});
const submitOrder=async()=>{if(!orderForm.value.selected_name||orderForm.value.requirements.length<5)return uni.showToast({title:'请完整填写需求',icon:'none'});const order=await http.createExpertOrder({service_id:selectedService.value.id,...orderForm.value});uni.showModal({title:'确认余额支付',content:`将从钱包支付 ¥${(order.amount_cents/100).toFixed(2)}`,success:async res=>{if(res.confirm){try{await http.payExpertWithBalance(order.id);uni.showToast({title:'余额支付成功'})}catch(_){handlePayError(order)}}else{uni.showToast({title:'订单已进入待付款',icon:'none'})}selectedService.value=null;orderForm.value={selected_name:'',requirements:''}}})};
onShow(load);
</script>

<style scoped>
.page{min-height:100vh;padding:26rpx;background:#f4f6f8}.hero{padding:38rpx;border-radius:22rpx;background:linear-gradient(135deg,#064e3b,#0f766e);color:#ccfbf1;font-size:24rpx;line-height:1.6}.hero-title{margin-bottom:10rpx;color:#fff;font-size:40rpx;font-weight:700}.service{margin-top:22rpx;padding:28rpx;border-radius:18rpx;background:#fff}.expert-row{display:flex;align-items:center}.avatar{display:flex;width:78rpx;height:78rpx;align-items:center;justify-content:center;border-radius:40rpx;background:#d1fae5;color:#047857;font-size:34rpx}.expert-name,.expert-title{margin-left:16rpx}.expert-name{font-weight:700}.expert-name text{margin-left:8rpx;color:#059669;font-size:20rpx}.expert-title{margin-top:6rpx;color:#8490a2;font-size:22rpx}.service-name{margin-top:22rpx;font-size:31rpx;font-weight:700}.desc{margin-top:10rpx;color:#64748b;font-size:24rpx;line-height:1.6}.footer{display:flex;justify-content:space-between;align-items:center;margin-top:22rpx}.price{color:#ea580c;font-size:32rpx;font-weight:700}.days{margin-left:12rpx;color:#94a3b8;font-size:21rpx}.footer button{margin:0;background:#0f766e;color:#fff}.empty{padding:160rpx 0;text-align:center;color:#94a3b8}.order-panel{position:fixed;left:24rpx;right:24rpx;bottom:30rpx;padding:30rpx;border-radius:22rpx;background:#fff;box-shadow:0 0 40rpx rgba(0,0,0,.18)}.close{float:right;font-size:42rpx}.panel-title{font-size:32rpx;font-weight:700}.chosen{margin-top:10rpx;color:#0f766e}.input{height:78rpx;margin-top:18rpx;border-bottom:1px solid #eee}.textarea{width:100%;height:150rpx;margin-top:16rpx;padding:16rpx;box-sizing:border-box;background:#f8fafc}.submit{margin-top:18rpx;background:#0f766e;color:#fff}
</style>
