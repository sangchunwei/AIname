<template>
  <view class="page">
    <view class="header">
      <view>
        <view class="title">用户管理</view>
        <view class="summary">普通用户 {{ total }} 人</view>
      </view>
      <button class="logout" size="mini" @click="logout">退出</button>
    </view>

    <view class="search-row">
      <input class="search" v-model="keyword" confirm-type="search" placeholder="搜索用户名或邮箱" @confirm="searchUsers" />
      <button class="search-btn" size="mini" @click="searchUsers">搜索</button>
    </view>

    <view v-if="!loading && users.length === 0" class="empty">暂无符合条件的用户</view>

    <view v-for="user in users" :key="user.id" class="card">
      <view class="user-main">
        <view class="user-name">{{ user.username }}</view>
        <view class="user-email">{{ user.email }}</view>
        <view class="meta">ID {{ user.id }} · {{ formatTime(user.created_at) }}</view>
      </view>
      <view :class="['status', user.is_frozen ? 'frozen' : 'normal']">
        {{ user.is_frozen ? '已冻结' : '正常' }}
      </view>
      <view class="actions">
        <button size="mini" @click="toggleFreeze(user)">{{ user.is_frozen ? '解冻' : '冻结' }}</button>
        <button size="mini" class="warning" @click="resetPassword(user)">重置密码</button>
        <button size="mini" class="danger" @click="deleteAccount(user)">删除</button>
      </view>
    </view>

    <button v-if="users.length < total" class="load-more" :loading="loading" @click="loadMore">加载更多</button>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const users = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;
const keyword = ref('');
const loading = ref(false);

const fetchUsers = async (append = false) => {
  loading.value = true;
  try {
    const res = await http.getAdminUsers({ page: page.value, pageSize, keyword: keyword.value });
    users.value = append ? users.value.concat(res.users) : res.users;
    total.value = res.total;
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
    uni.stopPullDownRefresh();
  }
};

const searchUsers = () => {
  page.value = 1;
  fetchUsers();
};

const loadMore = () => {
  page.value += 1;
  fetchUsers(true);
};

const toggleFreeze = async (user) => {
  await http.freezeUser(user.id, !user.is_frozen);
  user.is_frozen = !user.is_frozen;
  uni.showToast({ title: user.is_frozen ? '账号已冻结' : '账号已解冻' });
};

const resetPassword = (user) => {
  uni.showModal({
    title: `重置 ${user.username} 的密码`,
    editable: true,
    placeholderText: '请输入至少 6 位的新密码',
    success: async (res) => {
      if (!res.confirm) return;
      if (!res.content || res.content.length < 6) {
        return uni.showToast({ title: '新密码至少 6 位', icon: 'none' });
      }
      await http.resetUserPassword(user.id, res.content);
      uni.showToast({ title: '密码重置成功' });
    }
  });
};

const deleteAccount = (user) => {
  uni.showModal({
    title: '确认删除账号',
    content: `将删除 ${user.username}（${user.email}），此操作不可在管理端恢复。`,
    confirmColor: '#d93025',
    success: async (res) => {
      if (!res.confirm) return;
      await http.deleteUser(user.id);
      users.value = users.value.filter(item => item.id !== user.id);
      total.value = Math.max(0, total.value - 1);
      uni.showToast({ title: '账号已删除' });
    }
  });
};

const logout = () => {
  uni.removeStorageSync('token');
  uni.removeStorageSync('admin');
  uni.reLaunch({ url: '/pages/login/login' });
};

const formatTime = (value) => value ? value.replace('T', ' ').slice(0, 16) : '-';

onLoad(() => {
  if (!uni.getStorageSync('admin')) return logout();
  fetchUsers();
});
onPullDownRefresh(() => {
  page.value = 1;
  fetchUsers();
});
</script>

<style scoped>
.page { min-height: 100vh; padding: 28rpx; box-sizing: border-box; background: #f3f5f8; }
.header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 28rpx; }
.title { font-size: 42rpx; font-weight: bold; color: #17202e; }
.summary { margin-top: 8rpx; color: #7a8494; font-size: 25rpx; }
.logout { margin: 0; color: #536174; }
.search-row { display: flex; margin-bottom: 24rpx; }
.search { flex: 1; height: 72rpx; padding: 0 22rpx; border-radius: 12rpx; background: #fff; }
.search-btn { width: 130rpx; margin-left: 16rpx; line-height: 72rpx; background: #3976f6; color: #fff; }
.card { position: relative; margin-bottom: 22rpx; padding: 28rpx; border-radius: 16rpx; background: #fff; box-shadow: 0 4rpx 16rpx rgba(30, 45, 65, .05); }
.user-name { font-size: 32rpx; font-weight: 600; color: #202938; }
.user-email { margin-top: 8rpx; color: #536174; font-size: 27rpx; }
.meta { margin-top: 10rpx; color: #98a1af; font-size: 22rpx; }
.status { position: absolute; top: 28rpx; right: 28rpx; padding: 6rpx 16rpx; border-radius: 24rpx; font-size: 22rpx; }
.normal { background: #e8f7ee; color: #248a4b; }
.frozen { background: #fff0e5; color: #c15c10; }
.actions { display: flex; margin-top: 24rpx; gap: 12rpx; }
.actions button { flex: 1; margin: 0; font-size: 23rpx; }
.warning { color: #b86a00; }
.danger { color: #d93025; }
.empty { padding: 120rpx 0; text-align: center; color: #98a1af; }
.load-more { margin: 30rpx 0; background: #fff; color: #536174; }
</style>
