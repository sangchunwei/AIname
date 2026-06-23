<template>
  <view class="page">
    <view class="panel">
      <view class="avatar-editor" @click="chooseAvatar">
        <image v-if="form.avatar_url" class="avatar" :src="http.getAssetUrl(form.avatar_url)" mode="aspectFill" />
        <view v-else class="avatar avatar-fallback">{{ avatarInitial }}</view>
        <view class="avatar-tip">{{ avatarUploading ? '上传中…' : '点击更换头像' }}</view>
      </view>
      <button v-if="form.avatar_url" class="reset-avatar" size="mini" :disabled="avatarUploading" @click="removeAvatar">恢复默认头像</button>

      <view class="default-title">选择可爱卡通头像</view>
      <view class="default-avatars">
        <view
          v-for="avatar in defaultAvatars"
          :key="avatar.key"
          :class="['default-item', form.avatar_url === avatar.url ? 'selected' : '']"
          @click="selectDefault(avatar)"
        >
          <image class="default-image" :src="http.getAssetUrl(avatar.url)" mode="aspectFill" />
          <text>{{ avatar.name }}</text>
        </view>
      </view>

      <view class="label">昵称</view><input class="input" v-model="form.username" placeholder="请输入昵称" />
      <view class="label">个人简介</view><textarea class="textarea" v-model="form.bio" placeholder="介绍一下自己"></textarea>
      <button class="save" :loading="loading" @click="save">保存修改</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const form = ref({ username: '', bio: '', avatar_url: null });
const loading = ref(false);
const avatarUploading = ref(false);
const defaultAvatars = ref([]);
const avatarInitial = computed(() => (form.value.username || '用').trim().slice(0, 1));

const updateCachedAvatar = (avatarUrl) => {
  const user = uni.getStorageSync('user') || {};
  user.avatar_url = avatarUrl;
  uni.setStorageSync('user', user);
};

onLoad(async () => {
  const [info, avatars] = await Promise.all([http.getUserCenter(), http.getDefaultAvatars()]);
  defaultAvatars.value = avatars;
  form.value = { username: info.username, bio: info.bio || '', avatar_url: info.avatar_url };
});

const selectDefault = async (avatar) => {
  if (avatarUploading.value || form.value.avatar_url === avatar.url) return;
  avatarUploading.value = true;
  try {
    const response = await http.selectDefaultAvatar(avatar.key);
    form.value.avatar_url = response.avatar_url;
    updateCachedAvatar(response.avatar_url);
    uni.showToast({ title: '头像已更新' });
  } finally { avatarUploading.value = false; }
};

const chooseAvatar = () => {
  if (avatarUploading.value) return;
  uni.chooseImage({
    count: 1,
    sizeType: ['original', 'compressed'],
    sourceType: ['album', 'camera'],
    success: async (result) => {
      const selected = result.tempFiles && result.tempFiles[0];
      if (selected && selected.size > 5 * 1024 * 1024) {
        uni.showToast({ title: '头像文件不能超过 5 MB', icon: 'none' });
        return;
      }
      const filePath = (selected && (selected.path || selected.tempFilePath)) || result.tempFilePaths[0];
      if (!filePath) return;
      avatarUploading.value = true;
      try {
        const response = await http.uploadAvatar(filePath);
        form.value.avatar_url = response.avatar_url;
        updateCachedAvatar(response.avatar_url);
        uni.showToast({ title: '头像已更新' });
      } finally { avatarUploading.value = false; }
    }
  });
};

const removeAvatar = async () => {
  if (avatarUploading.value) return;
  avatarUploading.value = true;
  try {
    await http.deleteAvatar();
    form.value.avatar_url = null;
    updateCachedAvatar(null);
    uni.showToast({ title: '已恢复默认头像' });
  } finally { avatarUploading.value = false; }
};

const save = async () => {
  if (form.value.username.trim().length < 2) return uni.showToast({ title: '昵称至少 2 个字符', icon: 'none' });
  loading.value = true;
  try {
    await http.updateProfile({ username: form.value.username, bio: form.value.bio });
    const user = uni.getStorageSync('user') || {};
    user.username = form.value.username;
    user.avatar_url = form.value.avatar_url;
    uni.setStorageSync('user', user);
    uni.showToast({ title: '保存成功' });
    setTimeout(() => uni.navigateBack(), 700);
  } finally { loading.value = false; }
};
</script>

<style scoped>
.page{min-height:100vh;padding:28rpx;background:#f3f5f8}.panel{padding:30rpx;border-radius:18rpx;background:#fff}.avatar-editor{display:flex;flex-direction:column;align-items:center}.avatar{width:160rpx;height:160rpx;border-radius:80rpx;background:#eef2ff}.avatar-fallback{display:flex;align-items:center;justify-content:center;color:#4f46e5;font-size:68rpx;font-weight:700}.avatar-tip{margin-top:14rpx;color:#6366f1;font-size:24rpx}.reset-avatar{display:block;margin:16rpx auto 28rpx;background:#fff;color:#64748b}.default-title{margin:8rpx 0 18rpx;color:#475569;font-size:25rpx;font-weight:600}.default-avatars{display:grid;grid-template-columns:repeat(3,1fr);gap:20rpx;margin-bottom:30rpx}.default-item{display:flex;padding:12rpx 6rpx;box-sizing:border-box;flex-direction:column;align-items:center;border:4rpx solid transparent;border-radius:18rpx;background:#f8fafc;color:#64748b;font-size:20rpx}.default-item.selected{border-color:#6366f1;background:#eef2ff;color:#4338ca}.default-image{width:112rpx;height:112rpx;margin-bottom:8rpx;border-radius:56rpx}.label{margin:18rpx 0 10rpx;color:#475569;font-size:25rpx}.input{height:78rpx;padding:0 16rpx;border-radius:10rpx;background:#f8fafc}.textarea{width:100%;height:180rpx;padding:16rpx;box-sizing:border-box;border-radius:10rpx;background:#f8fafc}.save{margin-top:34rpx;background:#4f46e5;color:#fff}
</style>
