<template>
  <view class="page"><view class="panel">
    <view class="notice">密码修改成功后，所有已登录设备都需要重新登录。</view>
    <input class="input" v-model="form.current_password" type="password" placeholder="当前密码" />
    <input class="input" v-model="form.new_password" type="password" placeholder="新密码（至少 6 位）" />
    <input class="input" v-model="form.confirm_password" type="password" placeholder="再次输入新密码" />
    <button class="save" :loading="loading" @click="submit">确认修改</button>
  </view></view>
</template>
<script setup>
import { ref } from 'vue';import http from '@/http/http.js';
const form=ref({current_password:'',new_password:'',confirm_password:''}),loading=ref(false);
const submit=async()=>{const data=form.value;if(!data.current_password||data.new_password.length<6)return uni.showToast({title:'请完整填写密码',icon:'none'});if(data.new_password!==data.confirm_password)return uni.showToast({title:'两次新密码不一致',icon:'none'});loading.value=true;try{await http.changePassword(data);uni.showToast({title:'修改成功，请重新登录',icon:'none',duration:1800});setTimeout(()=>{uni.clearStorageSync();uni.reLaunch({url:'/pages/login/login'})},1800)}finally{loading.value=false}};
</script>
<style scoped>
.page{min-height:100vh;padding:28rpx;background:#f3f5f8}.panel{padding:30rpx;border-radius:18rpx;background:#fff}.notice{margin-bottom:20rpx;padding:18rpx;border-radius:10rpx;background:#fff7ed;color:#9a3412;font-size:23rpx}.input{height:82rpx;margin-bottom:18rpx;padding:0 16rpx;border-radius:10rpx;background:#f8fafc}.save{margin-top:22rpx;background:#172554;color:#fff}
</style>
