<template>
  <view class="page">
    <view class="tip">选择需要修改的内容</view>
    <view class="menu" @click="go('/pages/edit-profile/edit-profile')">
      <view><view class="title">修改个人资料</view><view class="desc">修改昵称和个人简介</view></view><text>›</text>
    </view>
    <view class="menu" @click="go('/pages/change-password/change-password')">
      <view><view class="title">修改密码</view><view class="desc">验证当前密码后设置新密码</view></view><text>›</text>
    </view>
  </view>
</template>
<script setup>
const go = url => uni.navigateTo({ url });
</script>
<style scoped>
.page{min-height:100vh;padding:28rpx;background:#f3f5f8}.tip{padding:20rpx 8rpx;color:#94a3b8;font-size:24rpx}.menu{display:flex;justify-content:space-between;align-items:center;margin-bottom:18rpx;padding:30rpx;border-radius:16rpx;background:#fff}.title{font-size:29rpx;font-weight:700;color:#1e293b}.desc{margin-top:8rpx;color:#94a3b8;font-size:23rpx}.menu>text{color:#94a3b8;font-size:48rpx}
</style>
