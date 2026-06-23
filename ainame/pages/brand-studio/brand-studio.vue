<template>
  <view class="page">
    <view class="hero">
      <view class="eyebrow">BRAND LAUNCH KIT</view>
      <view class="brand-name">{{ selected.name }}</view>
      <view class="moral">{{ selected.moral }}</view>
    </view>

    <view class="panel" v-if="!project">
      <view class="panel-title">完善品牌信息</view>
      <input class="input" v-model="form.industry" placeholder="所属行业（必填）" />
      <input class="input" v-model="form.audience" placeholder="目标用户，例如：年轻职场女性" />
      <picker mode="selector" :range="styleOptions" @change="changeStyle">
        <view class="input">视觉风格：{{ form.style }}</view>
      </picker>
      <input class="input" v-model="form.color_preference" placeholder="颜色偏好，例如：深蓝与银色" />
      <button class="primary" :loading="strategyLoading" @click="buildStrategy">生成一键品牌方案</button>
    </view>

    <template v-else>
      <view class="panel">
        <view class="panel-title">品牌定位</view>
        <view class="brief">{{ project.brand_brief }}</view>
        <view class="keywords">
          <text v-for="keyword in keywordList" :key="keyword" class="keyword">{{ keyword }}</text>
        </view>
      </view>

      <view class="panel">
        <view class="panel-title">选择品牌 Slogan</view>
        <view
          v-for="item in slogans"
          :key="item.id"
          :class="['slogan-card', selectedSloganId === item.id ? 'selected' : '']"
          @click="selectedSloganId = item.id"
        >
          <view class="slogan-text">{{ item.text }}</view>
          <view class="slogan-reason">{{ item.rationale }}</view>
        </view>
      </view>

      <view class="panel">
        <view class="panel-title">生成品牌视觉</view>
        <view class="visual-tip">先生成 Logo 概念，再用选中的 Slogan 生成名片排版。</view>
        <view class="visual-actions">
          <button class="primary half" :loading="visualLoading" @click="generateVisuals('logo')">生成 Logo</button>
          <button class="secondary half" :loading="visualLoading" @click="generateVisuals('business_card')">生成名片</button>
        </view>
        <view v-if="jobStatus" class="job-status">{{ jobStatus }}</view>
      </view>

      <view class="panel" v-if="assets.length">
        <view class="panel-title">品牌素材</view>
        <view class="gallery">
          <view class="asset" v-for="asset in assets" :key="asset.id" @click="previewAsset(asset)">
            <image class="asset-image" :src="http.getAssetUrl(asset.file_url)" mode="aspectFill" />
            <view class="asset-label">{{ asset.asset_type === 'logo' ? 'Logo 概念' : '名片排版' }}</view>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onLoad, onUnload } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const selected = ref({ name: '', reference: '', moral: '', category: '企业名', requirement: '' });
const form = ref({ industry: '', audience: '', style: '现代简约', color_preference: '' });
const styleOptions = ['现代简约', '科技未来', '东方文化', '自然治愈', '高端奢华', '年轻潮流'];
const project = ref(null);
const projectId = ref(null);
const slogans = ref([]);
const assets = ref([]);
const selectedSloganId = ref(null);
const strategyLoading = ref(false);
const visualLoading = ref(false);
const jobStatus = ref('');
let pollTimer = null;

const keywordList = computed(() => project.value?.visual_keywords?.split('、').filter(Boolean) || []);

const changeStyle = (event) => {
  form.value.style = styleOptions[event.detail.value];
};

const buildStrategy = async () => {
  if (!form.value.industry.trim()) {
    return uni.showToast({ title: '请填写所属行业', icon: 'none' });
  }
  strategyLoading.value = true;
  uni.showLoading({ title: '构建品牌策略...' });
  try {
    if (!projectId.value) {
      const created = await http.createBrandProject({
        selected_name: selected.value.name,
        category: selected.value.category,
        name_reference: selected.value.reference,
        name_moral: selected.value.moral,
        ...form.value
      });
      projectId.value = created.id;
    }
    const result = await http.generateBrandStrategy(projectId.value);
    project.value = result.project;
    slogans.value = result.slogans;
    selectedSloganId.value = result.slogans[0]?.id || null;
  } catch (error) {
    console.error(error);
  } finally {
    strategyLoading.value = false;
    uni.hideLoading();
  }
};

const generateVisuals = async (assetType) => {
  if (assetType === 'business_card' && !selectedSloganId.value) {
    return uni.showToast({ title: '请先选择一条 Slogan', icon: 'none' });
  }
  visualLoading.value = true;
  jobStatus.value = '视觉任务已提交，正在生成...';
  try {
    const job = await http.generateBrandVisuals(project.value.id, {
      asset_type: assetType,
      count: 4,
      slogan_id: selectedSloganId.value
    });
    pollJob(job.id, 0);
  } catch (error) {
    visualLoading.value = false;
    jobStatus.value = '';
    console.error(error);
  }
};

const pollJob = async (jobId, attempts) => {
  try {
    const job = await http.getVisualJob(jobId);
    if (job.status === 'completed') {
      assets.value = job.assets.concat(assets.value);
      visualLoading.value = false;
      jobStatus.value = `已生成 ${job.assets.length} 份品牌素材`;
      return;
    }
    if (job.status === 'failed') {
      visualLoading.value = false;
      jobStatus.value = '生成失败，请稍后重试';
      return;
    }
    if (attempts >= 90) {
      visualLoading.value = false;
      jobStatus.value = '生成时间较长，请稍后返回查看';
      return;
    }
    pollTimer = setTimeout(() => pollJob(jobId, attempts + 1), 2000);
  } catch (error) {
    visualLoading.value = false;
    jobStatus.value = '任务状态查询失败';
  }
};

const previewAsset = (asset) => {
  const urls = assets.value.map(item => http.getAssetUrl(item.file_url));
  uni.previewImage({ current: http.getAssetUrl(asset.file_url), urls });
};

onLoad(() => {
  const cached = uni.getStorageSync('selectedNameForBrand');
  if (!cached?.name) {
    uni.showToast({ title: '请先选择一个企业名称', icon: 'none' });
    return setTimeout(() => uni.navigateBack(), 800);
  }
  selected.value = cached;
  form.value.industry = cached.requirement || '';
});

onUnload(() => {
  if (pollTimer) clearTimeout(pollTimer);
});
</script>

<style scoped>
.page { min-height: 100vh; padding: 28rpx; box-sizing: border-box; background: #f1f4f8; color: #182033; }
.hero { padding: 48rpx 36rpx; border-radius: 24rpx; background: linear-gradient(135deg, #172554, #5b21b6); color: #fff; }
.eyebrow { font-size: 20rpx; letter-spacing: 5rpx; color: #c4b5fd; }
.brand-name { margin-top: 18rpx; font-size: 58rpx; font-weight: 700; }
.moral { margin-top: 14rpx; color: #ddd6fe; font-size: 25rpx; line-height: 1.6; }
.panel { margin-top: 24rpx; padding: 30rpx; border-radius: 20rpx; background: #fff; }
.panel-title { margin-bottom: 24rpx; font-size: 32rpx; font-weight: 700; }
.input { height: 84rpx; padding: 0 18rpx; border-bottom: 1px solid #e5e7eb; font-size: 27rpx; line-height: 84rpx; }
.primary, .secondary { margin-top: 30rpx; border-radius: 50rpx; color: #fff; }
.primary { background: #4f46e5; }
.secondary { background: #0f766e; }
.brief { color: #475569; font-size: 27rpx; line-height: 1.8; }
.keywords { display: flex; flex-wrap: wrap; margin-top: 20rpx; gap: 12rpx; }
.keyword { padding: 8rpx 18rpx; border-radius: 30rpx; background: #eef2ff; color: #4338ca; font-size: 23rpx; }
.slogan-card { margin-bottom: 16rpx; padding: 22rpx; border: 2rpx solid #edf0f4; border-radius: 14rpx; }
.slogan-card.selected { border-color: #6366f1; background: #f5f3ff; }
.slogan-text { font-size: 29rpx; font-weight: 600; }
.slogan-reason { margin-top: 10rpx; color: #7c8799; font-size: 23rpx; line-height: 1.5; }
.visual-tip { color: #7c8799; font-size: 24rpx; }
.visual-actions { display: flex; gap: 18rpx; }
.half { flex: 1; }
.job-status { margin-top: 22rpx; text-align: center; color: #6366f1; font-size: 24rpx; }
.gallery { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18rpx; }
.asset { overflow: hidden; border-radius: 14rpx; background: #f8fafc; }
.asset-image { width: 100%; height: 300rpx; background: #eef2f7; }
.asset-label { padding: 14rpx; text-align: center; color: #64748b; font-size: 23rpx; }
</style>
