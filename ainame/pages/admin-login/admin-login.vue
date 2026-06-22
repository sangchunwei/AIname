<template>
  <view class="container">
    <view class="badge">ADMIN</view>
    <view class="title">管理员身份验证</view>
    <view class="tip">此入口仅供授权管理员使用</view>

    <input class="input-box" v-model="form.email" placeholder="管理员邮箱" />
    <input class="input-box" v-model="form.password" type="password" placeholder="管理员密码" />
    <button class="btn" :loading="loading" @click="handleLogin">进入管理中心</button>
    <view class="back" @click="goBack">返回普通用户登录</view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import http from '@/http/http.js';

const form = ref({ email: '', password: '' });
const loading = ref(false);

const handleLogin = async () => {
  if (!form.value.email || !form.value.password) {
    return uni.showToast({ title: '请填写管理员账号和密码', icon: 'none' });
  }
  loading.value = true;
  try {
    const res = await http.adminLogin(form.value);
    uni.setStorageSync('token', res.token);
    uni.setStorageSync('admin', res.admin);
    uni.removeStorageSync('user');
    uni.reLaunch({ url: '/pages/admin-users/admin-users' });
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const goBack = () => uni.reLaunch({ url: '/pages/login/login' });
</script>

<style scoped>
.container { min-height: 100vh; padding: 100rpx 48rpx; box-sizing: border-box; background: #101827; color: #fff; }
.badge { width: fit-content; padding: 8rpx 18rpx; border: 1px solid #5b8cff; border-radius: 30rpx; color: #8aabff; font-size: 22rpx; }
.title { margin-top: 28rpx; font-size: 46rpx; font-weight: bold; }
.tip { margin: 16rpx 0 70rpx; color: #92a0b5; font-size: 26rpx; }
.input-box { height: 92rpx; margin-bottom: 28rpx; padding: 0 24rpx; border-radius: 14rpx; background: #1d2939; color: #fff; }
.btn { margin-top: 44rpx; border-radius: 14rpx; background: #3976f6; color: #fff; }
.back { margin-top: 36rpx; text-align: center; color: #92a0b5; font-size: 26rpx; }
</style>
