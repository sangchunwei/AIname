<template>
  <view class="page">
    <view class="tabs"><view :class="{active:filter===''}" @click="changeFilter('')">全部</view><view :class="{active:filter==='name_poll'}" @click="changeFilter('name_poll')">灵感投票</view><view @click="showComposer=!showComposer">发布</view></view>
    <view class="composer" v-if="showComposer">
      <picker mode="selector" :range="['讨论','名字投票']" @change="e=>draft.post_type=e.detail.value==1?'name_poll':'discussion'"><view class="input">类型：{{ draft.post_type==='name_poll'?'名字投票':'讨论' }}</view></picker>
      <input class="input" v-model="draft.title" placeholder="标题" />
      <textarea class="textarea" v-model="draft.content" placeholder="分享背景、需求或你的想法"></textarea>
      <view v-if="draft.post_type==='name_poll'" class="options"><view v-for="(option,index) in draft.options" :key="index" class="option-edit"><input v-model="option.name" placeholder="候选名字"/><text @click="draft.options.splice(index,1)">删除</text></view><button size="mini" @click="draft.options.push({name:'',moral:''})">增加候选</button></view>
      <button class="publish" @click="publish">发布到社区</button>
    </view>
    <view class="post" v-for="post in posts" :key="post.id">
      <view class="author">{{ post.author_name }} · {{ formatTime(post.created_at) }}</view><view class="title">{{ post.title }}</view><view class="content">{{ post.content }}</view>
      <view v-if="post.post_type==='name_poll'" class="poll"><view v-for="option in post.options" :key="option.id" :class="['poll-option',post.my_vote_option_id===option.id?'selected':'']" @click="vote(post,option)"><text>{{ option.name }}</text><text>{{ option.vote_count }} 票</text></view></view>
      <view class="actions"><text @click="like(post)">{{ post.liked_by_me?'已赞':'点赞' }} {{ post.like_count }}</text><text>评论 {{ post.comment_count }}</text><text v-if="post.post_type==='name_poll'">投票 {{ post.vote_count }}</text></view>
      <view class="comment-row"><input v-model="commentDraft[post.id]" placeholder="写下建议"/><button size="mini" @click="comment(post)">发送</button></view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'; import { onLoad,onPullDownRefresh } from '@dcloudio/uni-app'; import http from '@/http/http.js';
const posts=ref([]),filter=ref(''),showComposer=ref(false),commentDraft=ref({});
const draft=ref({post_type:'discussion',title:'',content:'',options:[]});
const load=async()=>{try{posts.value=(await http.getCommunityPosts(filter.value)).posts}finally{uni.stopPullDownRefresh()}};
const changeFilter=value=>{filter.value=value;load()};
const publish=async()=>{await http.createCommunityPost(draft.value);draft.value={post_type:'discussion',title:'',content:'',options:[]};showComposer.value=false;uni.removeStorageSync('namePollDraft');load()};
const like=async post=>{const res=await http.likeCommunityPost(post.id);post.liked_by_me=res.liked;post.like_count=res.like_count};
const vote=async(post,option)=>{await http.voteCommunityPoll(post.id,option.id);load()};
const comment=async post=>{const value=commentDraft.value[post.id];if(!value?.trim())return;await http.commentCommunityPost(post.id,value);commentDraft.value[post.id]='';post.comment_count++};
const formatTime=value=>value?.replace('T',' ').slice(0,16);
onLoad(options=>{const cached=uni.getStorageSync('namePollDraft');if(options.createPoll&&cached?.length){showComposer.value=true;draft.value={post_type:'name_poll',title:'请帮我选一个好名字',content:'这些是 AI 生成的候选名字，欢迎投票并提出建议。',options:cached}}load()});onPullDownRefresh(load);
</script>

<style scoped>
.page{min-height:100vh;padding:24rpx;background:#f4f6f9}.tabs{display:flex;justify-content:space-around;padding:20rpx;border-radius:16rpx;background:#fff}.tabs view{color:#64748b}.tabs .active{color:#4f46e5;font-weight:700}.composer,.post{margin-top:20rpx;padding:26rpx;border-radius:18rpx;background:#fff}.input{height:76rpx;border-bottom:1px solid #eee;line-height:76rpx}.textarea{width:100%;height:150rpx;margin-top:16rpx;padding:16rpx;box-sizing:border-box;background:#f8fafc}.publish{margin-top:20rpx;background:#4f46e5;color:#fff}.option-edit{display:flex;padding:12rpx 0}.option-edit input{flex:1}.option-edit text{color:#dc2626;font-size:23rpx}.author{color:#94a3b8;font-size:22rpx}.title{margin-top:14rpx;font-size:32rpx;font-weight:700}.content{margin-top:12rpx;color:#475569;font-size:26rpx;line-height:1.6}.poll-option{display:flex;justify-content:space-between;margin-top:12rpx;padding:20rpx;border-radius:12rpx;background:#f1f5f9}.poll-option.selected{background:#ede9fe;color:#6d28d9}.actions{display:flex;gap:34rpx;margin-top:20rpx;color:#64748b;font-size:23rpx}.comment-row{display:flex;margin-top:18rpx}.comment-row input{flex:1;padding:0 16rpx;background:#f8fafc}.comment-row button{margin-left:12rpx}
</style>
