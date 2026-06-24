<template>
  <view class="page">
    <view class="tip">选择需要修改的内容</view>
    <view class="menu" @click="go('/pages/edit-profile/edit-profile')">
      <view><view class="title">修改个人资料</view><view class="desc">修改昵称和个人简介</view></view><text>›</text>
    </view>
    <view class="menu" @click="go('/pages/change-password/change-password')">
      <view><view class="title">修改密码</view><view class="desc">验证当前密码后设置新密码</view></view><text>›</text>
    </view>
    <view class="menu" @click="checkUpdate">
      <view><view class="title">版本更新</view><view class="desc">当前版本 {{ versionText }}</view></view><text>›</text>
    </view>
    <view class="version">AIName v{{ versionText }}</view>
  </view>
</template>
<script setup>
import { computed, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import http from '@/http/http.js';
import { getCurrentAppVersion, getPlatform } from '@/utils/app-version.js';

const versionName = ref('1.0.3');
const versionCode = ref(103);
const versionText = computed(() => `${versionName.value} (${versionCode.value})`);

const go = url => uni.navigateTo({ url });

const loadVersion = async () => {
  const version = await getCurrentAppVersion();
  versionName.value = version.versionName;
  versionCode.value = version.versionCode;
};

const installUpdate = (downloadUrl) => {
  if (!downloadUrl) {
    uni.showToast({ title: '暂未配置更新下载地址', icon: 'none' });
    return;
  }
  const isApk = downloadUrl.split('?')[0].toLowerCase().endsWith('.apk');
  if (isApk && typeof plus !== 'undefined' && plus.runtime && plus.runtime.install) {
    uni.showLoading({ title: '正在下载更新' });
    uni.downloadFile({
      url: downloadUrl,
      success: (res) => {
        uni.hideLoading();
        if (res.statusCode !== 200) {
          uni.showToast({ title: '更新包下载失败', icon: 'none' });
          return;
        }
        plus.runtime.install(res.tempFilePath, { force: false }, () => {
          plus.runtime.restart();
        }, () => {
          uni.showToast({ title: '安装更新失败', icon: 'none' });
        });
      },
      fail: () => {
        uni.hideLoading();
        uni.showToast({ title: '更新包下载失败', icon: 'none' });
      }
    });
    return;
  }
  if (typeof plus !== 'undefined' && plus.runtime && plus.runtime.openURL) {
    plus.runtime.openURL(downloadUrl);
    return;
  }
  if (typeof window !== 'undefined' && window.location) {
    window.location.href = downloadUrl;
    return;
  }
  uni.setClipboardData({
    data: downloadUrl,
    success: () => uni.showToast({ title: '更新地址已复制', icon: 'none' })
  });
};

const checkUpdate = async () => {
  await loadVersion();
  const result = await http.checkAppVersion({
    platform: getPlatform(),
    versionCode: versionCode.value
  });
  if (!result.has_update) {
    uni.showToast({ title: '当前已是最新版本', icon: 'none' });
    return;
  }
  uni.showModal({
    title: `发现新版本 v${result.latest_version_name}`,
    content: result.release_notes || '检测到新版本，是否立即更新？',
    showCancel: !result.force_update,
    confirmText: '立即更新',
    success: (res) => {
      if (res.confirm) installUpdate(result.download_url);
    }
  });
};

onShow(loadVersion);
</script>
<style scoped>
.page{min-height:100vh;padding:28rpx;background:#f3f5f8}.tip{padding:20rpx 8rpx;color:#94a3b8;font-size:24rpx}.menu{display:flex;justify-content:space-between;align-items:center;margin-bottom:18rpx;padding:30rpx;border-radius:16rpx;background:#fff}.title{font-size:29rpx;font-weight:700;color:#1e293b}.desc{margin-top:8rpx;color:#94a3b8;font-size:23rpx}.menu>text{color:#94a3b8;font-size:48rpx}
.version{margin-top:34rpx;text-align:center;color:#94a3b8;font-size:22rpx}
</style>
