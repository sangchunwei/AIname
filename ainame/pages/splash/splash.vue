<template>
  <view class="splash-page">
    <image class="cover-image" src="/static/launch-cover.jpg" mode="aspectFill" />
    <view class="cover-shade"></view>

    <button class="skip-button" @click="skipSplash">
      跳过 {{ secondsLeft }}s
    </button>

    <view class="brand-copy">
      <text class="app-name">智能起名助手</text>
      <text class="app-desc">--一款使用ai大模型帮助起名的软件</text>
    </view>
  </view>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { redirectToStartupTarget } from '@/utils/startup.js';

const secondsLeft = ref(3);
let countdownTimer = null;
let hasRedirected = false;

const goNext = () => {
  if (hasRedirected) return;
  hasRedirected = true;
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
  redirectToStartupTarget();
};

const skipSplash = () => {
  goNext();
};

onMounted(() => {
  // #ifndef APP-PLUS
  goNext();
  // #endif

  // #ifdef APP-PLUS
  countdownTimer = setInterval(() => {
    secondsLeft.value -= 1;
    if (secondsLeft.value <= 0) {
      goNext();
    }
  }, 1000);
  // #endif
});

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
});
</script>

<style scoped>
.splash-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #111827;
}

.cover-image,
.cover-shade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.cover-image {
  z-index: 1;
}

.cover-shade {
  z-index: 2;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.48), rgba(0, 0, 0, 0.08) 45%, rgba(0, 0, 0, 0.4));
}

.skip-button {
  position: absolute;
  z-index: 3;
  top: calc(28rpx + var(--status-bar-height));
  right: 28rpx;
  min-width: 148rpx;
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 26rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.55);
}

.skip-button::after {
  border: 0;
}

.brand-copy {
  position: absolute;
  z-index: 3;
  top: calc(112rpx + var(--status-bar-height));
  left: 52rpx;
  right: 52rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  color: #fff;
  text-shadow: 0 4rpx 18rpx rgba(0, 0, 0, 0.42);
}

.app-name {
  font-size: 56rpx;
  line-height: 1.2;
  font-weight: 700;
}

.app-desc {
  margin-top: 18rpx;
  font-size: 26rpx;
  line-height: 1.45;
}
</style>
