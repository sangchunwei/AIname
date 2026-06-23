<template>
  <view class="page"><view class="header">专家工作台<text>AI 初稿仅供内部辅助，最终报告须人工审核</text></view>
    <view class="service-form"><view class="form-title">发布专家服务</view><input v-model="serviceForm.name" placeholder="服务名称"/><textarea v-model="serviceForm.description" placeholder="服务内容说明（至少 10 字）"></textarea><view class="row"><input v-model="serviceForm.price" type="digit" placeholder="价格（元）"/><input v-model="serviceForm.delivery_days" type="number" placeholder="交付天数"/></view><button @click="createService">发布服务</button></view>
    <view v-if="!orders.length" class="empty">暂无待处理订单</view>
    <view class="order" v-for="item in orders" :key="item.id"><view class="top"><text>{{ item.selected_name }}</text><text>{{ statusText(item.status) }}</text></view><view class="requirements">{{ item.requirements }}</view>
      <button v-if="!item.ai_draft" class="draft-btn" :loading="loadingId===item.id" @click="createDraft(item)">生成 AI 分析初稿</button>
      <view v-if="item.ai_draft" class="draft"><view class="label">AI 内部初稿</view>{{ item.ai_draft }}</view>
      <textarea class="report" v-model="reports[item.id]" placeholder="请在审核和修订后填写最终专家报告（至少 50 字）"></textarea><button class="deliver" @click="deliver(item)">交付专家报告</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';import { onLoad,onPullDownRefresh } from '@dcloudio/uni-app';import http from '@/http/http.js';
const orders=ref([]),reports=ref({}),loadingId=ref(null);
const serviceForm=ref({name:'',description:'',price:'',delivery_days:'3'});
const load=async()=>{try{orders.value=await http.getExpertWorkbenchOrders();orders.value.forEach(item=>{if(item.final_report)reports.value[item.id]=item.final_report})}finally{uni.stopPullDownRefresh()}};
const createDraft=async item=>{loadingId.value=item.id;try{const updated=await http.generateExpertDraft(item.id);Object.assign(item,updated);reports.value[item.id]=updated.ai_draft||''}finally{loadingId.value=null}};
const deliver=async item=>{const report=reports.value[item.id];if(!report||report.length<50)return uni.showToast({title:'最终报告至少 50 字',icon:'none'});await http.deliverExpertReport(item.id,report);uni.showToast({title:'报告已交付'});load()};
const createService=async()=>{const data=serviceForm.value;if(!data.name||data.description.length<10||!Number(data.price))return uni.showToast({title:'请完整填写服务信息',icon:'none'});await http.createExpertService({name:data.name,description:data.description,price_cents:Math.round(Number(data.price)*100),delivery_days:Number(data.delivery_days)||3});serviceForm.value={name:'',description:'',price:'',delivery_days:'3'};uni.showToast({title:'服务发布成功'})};
const statusText=s=>({paid:'已付款',drafting:'撰写中',delivered:'已交付'})[s]||s;onLoad(load);onPullDownRefresh(load);
</script>

<style scoped>
.page{min-height:100vh;padding:26rpx;background:#f3f5f8}.header{padding:30rpx;border-radius:18rpx;background:#172554;color:#fff;font-size:38rpx;font-weight:700}.header text{display:block;margin-top:10rpx;color:#c7d2fe;font-size:21rpx;font-weight:400}.order{margin-top:22rpx;padding:28rpx;border-radius:18rpx;background:#fff}.top{display:flex;justify-content:space-between;font-size:30rpx;font-weight:700}.top text:last-child{color:#4f46e5;font-size:23rpx}.requirements{margin-top:16rpx;color:#64748b;line-height:1.6}.draft-btn{margin-top:18rpx;background:#eef2ff;color:#4338ca}.draft{margin-top:18rpx;padding:20rpx;background:#f8fafc;color:#475569;font-size:23rpx;line-height:1.65;white-space:pre-wrap}.label{margin-bottom:8rpx;color:#7c3aed;font-weight:700}.report{width:100%;height:300rpx;margin-top:18rpx;padding:18rpx;box-sizing:border-box;background:#fffdf5;border:1px solid #fde68a}.deliver{margin-top:18rpx;background:#0f766e;color:#fff}.empty{padding:160rpx 0;text-align:center;color:#94a3b8}
.service-form{margin-top:22rpx;padding:26rpx;border-radius:18rpx;background:#fff}.form-title{font-size:29rpx;font-weight:700}.service-form input{height:74rpx;border-bottom:1px solid #eee}.service-form textarea{width:100%;height:120rpx;margin-top:12rpx;padding:14rpx;box-sizing:border-box;background:#f8fafc}.service-form .row{display:flex;gap:18rpx}.service-form .row input{flex:1}.service-form button{margin-top:16rpx;background:#0f766e;color:#fff}
</style>
