<template>
  <view class="page">
    <view class="tabs">
      <view :class="{active: !showComposer}" @click="changeFilter('name_poll')">灵感投票</view>
      <view :class="{active: showComposer}" @click="openComposer">发布</view>
    </view>

    <view class="composer" v-if="showComposer">
      <picker mode="selector" :range="['讨论','名字投票']" @change="e => draft.post_type = e.detail.value == 1 ? 'name_poll' : 'discussion'">
        <view class="input">类型：{{ draft.post_type === 'name_poll' ? '名字投票' : '讨论' }}</view>
      </picker>
      <input class="input" v-model="draft.title" placeholder="标题" />
      <textarea class="textarea" v-model="draft.content" placeholder="分享背景、需求或你的想法"></textarea>
      <view v-if="draft.post_type === 'name_poll'" class="options">
        <view v-for="(option,index) in draft.options" :key="index" class="option-edit">
          <input v-model="option.name" placeholder="候选名字"/>
          <text @click="draft.options.splice(index,1)">删除</text>
        </view>
        <button size="mini" @click="draft.options.push({name:'',moral:''})">增加候选</button>
      </view>
      <button class="publish" @click="publish">发布到社区</button>
    </view>

    <block v-if="!showComposer">
      <view class="post" v-for="post in posts" :key="post.id">
        <view class="author">{{ post.author_name }} · {{ formatTime(post.created_at) }}</view>
        <view class="title">{{ post.title }}</view>
        <view class="content">{{ post.content }}</view>

        <view v-if="post.post_type === 'name_poll'" class="poll">
          <view class="vote-head">
            <text :class="['vote-badge', post.my_vote_option_id ? 'voted' : 'unvoted']">
              {{ post.my_vote_option_id ? '已投票' : '未投票' }}
            </text>
            <view class="vote-actions">
              <button size="mini" class="vote-btn" @click="openVoteDialog(post)">
                {{ post.my_vote_option_id ? '修改投票' : '点击投票' }}
              </button>
              <button v-if="post.my_vote_option_id" size="mini" class="cancel-vote-btn" @click="cancelVote(post)">取消投票</button>
            </view>
          </view>
          <view v-for="option in post.options" :key="option.id" :class="['poll-option', post.my_vote_option_id === option.id ? 'selected' : '']">
            <text>{{ option.name }}</text>
            <text>{{ option.vote_count }} 票</text>
          </view>
        </view>

        <view class="actions">
          <text @click="like(post)">{{ post.liked_by_me ? '已赞' : '点赞' }} {{ post.like_count }}</text>
          <text @click="toggleComments(post)">{{ isCommentsExpanded(post) ? '收起评论' : '评论' }} {{ post.comment_count }}</text>
          <text v-if="post.post_type === 'name_poll'">投票 {{ post.vote_count }}</text>
        </view>

        <view v-if="!isCommentsExpanded(post) && previewComments(post).length" class="comment-preview">
          <view class="preview-comment" v-for="item in previewComments(post)" :key="item.id">
            <text class="comment-author">{{ item.author_name }}</text>
            <text class="comment-time"> · {{ formatTime(item.created_at) }}</text>
            <text v-if="item.reply_to_author" class="reply-to"> 回复 {{ item.reply_to_author }}</text>
            <text>：{{ item.content }}</text>
          </view>
        </view>
        <button v-if="!isCommentsExpanded(post) && post.comment_count > 2" class="expand-comments" size="mini" @click="toggleComments(post)">
          展开全部评论
        </button>

        <view v-if="isCommentsExpanded(post)" class="inline-comments">
          <view class="inline-title">全部评论</view>
          <scroll-view class="comments-scroll" scroll-y>
            <view v-if="!topLevelComments(post).length" class="empty-comments">暂无评论</view>
            <block v-for="row in commentRows(post)" :key="row.key">
              <view
                v-if="row.type === 'comment'"
                :class="['comment-item', row.level > 0 ? 'reply-item' : '']"
                :style="{ marginLeft: row.level * 34 + 'rpx' }"
              >
                <view class="comment-main">
                  <text class="comment-author">{{ row.comment.author_name }}</text>
                  <text v-if="row.comment.reply_to_author" class="reply-to"> 回复 {{ row.comment.reply_to_author }}</text>
                  <text>：{{ row.comment.content }}</text>
                </view>
                <view class="comment-meta">
                  <text>{{ formatTime(row.comment.created_at) }}</text>
                  <text @click="likeComment(row.comment)">{{ row.comment.liked_by_me ? '已赞' : '点赞' }} {{ row.comment.like_count }}</text>
                  <text @click="startReply(post, row.comment)">回复</text>
                </view>
              </view>
              <view
                v-else
                class="reply-toggle"
                :style="{ marginLeft: row.level * 34 + 'rpx' }"
                @click="toggleReplies(row.parentId)"
              >
                {{ replyToggleText(row) }}
              </view>
            </block>
          </scroll-view>
        </view>

        <view v-if="replyTargets[post.id]" class="replying">
          正在回复 {{ replyTargets[post.id].author_name }}
          <text @click="clearReply(post)">取消</text>
        </view>
        <view class="comment-row">
          <input v-model="commentDraft[post.id]" :placeholder="replyTargets[post.id] ? '写下回复' : '写下建议'"/>
          <button size="mini" @click="comment(post)">发送</button>
        </view>
      </view>
    </block>

    <view v-if="voteDialogVisible" class="modal-mask">
      <view class="vote-modal">
        <view class="modal-title">{{ voteDialogPost?.my_vote_option_id ? '修改投票' : '完成投票' }}</view>
        <view class="modal-subtitle" v-if="lastVoteName">上次选择：{{ lastVoteName }}</view>
        <view v-for="option in voteDialogPost?.options || []" :key="option.id" :class="['vote-choice', selectedVoteOptionId === option.id ? 'active' : '']" @click="selectedVoteOptionId = option.id">
          <text>{{ option.name }}</text>
          <text>{{ option.vote_count }} 票</text>
        </view>
        <view class="modal-actions">
          <button size="mini" class="cancel" @click="closeVoteDialog">取消</button>
          <button size="mini" class="confirm" @click="submitVote">完成投票</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app';
import http from '@/http/http.js';

const posts = ref([]);
const filter = ref('name_poll');
const showComposer = ref(false);
const commentDraft = ref({});
const replyTargets = ref({});
const expandedComments = ref({});
const repliesExpanded = ref({});
const voteDialogVisible = ref(false);
const voteDialogPost = ref(null);
const selectedVoteOptionId = ref(null);
const draft = ref({ post_type: 'discussion', title: '', content: '', options: [] });

const lastVoteName = computed(() => {
  if (!voteDialogPost.value?.my_vote_option_id) return '';
  const option = voteDialogPost.value.options?.find(item => item.id === voteDialogPost.value.my_vote_option_id);
  return option?.name || '';
});

const load = async () => {
  try {
    posts.value = (await http.getCommunityPosts(filter.value)).posts;
  } finally {
    uni.stopPullDownRefresh();
  }
};

const topLevelComments = post => (post.comments || []).filter(item => !item.parent_comment_id);
const previewComments = post => topLevelComments(post).slice(0, 2);
const childComments = (post, parentId) => (post.comments || []).filter(item => item.parent_comment_id === parentId);
const toggleReplies = parentId => {
  repliesExpanded.value[parentId] = !repliesExpanded.value[parentId];
};
const replyToggleText = row => repliesExpanded.value[row.parentId] ? '收起回复' : `展开 ${row.hiddenCount} 条回复`;
const commentRows = post => {
  const rows = [];
  const walk = (comments, level) => {
    comments.forEach(comment => {
      rows.push({ type: 'comment', key: `comment-${comment.id}`, comment, level });
      const children = childComments(post, comment.id);
      const visibleChildren = repliesExpanded.value[comment.id] ? children : children.slice(0, 2);
      walk(visibleChildren, level + 1);
      if (children.length > 2) {
        rows.push({
          type: 'toggle',
          key: `toggle-${comment.id}`,
          parentId: comment.id,
          hiddenCount: children.length - 2,
          level: level + 1,
        });
      }
    });
  };
  walk(topLevelComments(post), 0);
  return rows;
};
const isCommentsExpanded = post => Boolean(expandedComments.value[post.id]);
const toggleComments = post => {
  expandedComments.value[post.id] = !expandedComments.value[post.id];
  if (!expandedComments.value[post.id]) clearReply(post);
};
const changeFilter = value => { filter.value = value; showComposer.value = false; load(); };
const openComposer = () => { showComposer.value = true; closeVoteDialog(); };
const publish = async () => {
  await http.createCommunityPost(draft.value);
  draft.value = { post_type: 'discussion', title: '', content: '', options: [] };
  showComposer.value = false;
  uni.removeStorageSync('namePollDraft');
  load();
};
const like = async post => {
  const res = await http.likeCommunityPost(post.id);
  post.liked_by_me = res.liked;
  post.like_count = res.like_count;
};
const openVoteDialog = post => {
  voteDialogPost.value = post;
  selectedVoteOptionId.value = post.my_vote_option_id || null;
  voteDialogVisible.value = true;
};
const closeVoteDialog = () => { voteDialogVisible.value = false; voteDialogPost.value = null; selectedVoteOptionId.value = null; };
const submitVote = async () => {
  if (!voteDialogPost.value || !selectedVoteOptionId.value) return uni.showToast({ title: '请选择一个候选项', icon: 'none' });
  await http.voteCommunityPoll(voteDialogPost.value.id, selectedVoteOptionId.value);
  closeVoteDialog();
  await load();
};
const cancelVote = async post => {
  await http.cancelCommunityVote(post.id);
  await load();
  uni.showToast({ title: '已取消投票', icon: 'none' });
};
const startReply = (post, item) => {
  replyTargets.value[post.id] = item;
  commentDraft.value[post.id] = '';
};
const clearReply = post => {
  delete replyTargets.value[post.id];
};
const comment = async post => {
  const value = commentDraft.value[post.id];
  if (!value?.trim()) return;
  await http.commentCommunityPost(post.id, value.trim(), replyTargets.value[post.id]?.id || null);
  commentDraft.value[post.id] = '';
  clearReply(post);
  expandedComments.value[post.id] = true;
  await load();
};
const likeComment = async item => {
  const res = await http.likeCommunityComment(item.id);
  item.liked_by_me = res.liked;
  item.like_count = res.like_count;
};
const formatTime = value => value?.replace('T', ' ').slice(0, 16);

onLoad(options => {
  const cached = uni.getStorageSync('namePollDraft');
  if (options.createPoll && cached?.length) {
    showComposer.value = true;
    draft.value = {
      post_type: 'name_poll',
      title: '请帮我选一个好名字',
      content: '这些是 AI 生成的候选名字，欢迎投票并提出建议。',
      options: cached,
    };
  }
  load();
});
onPullDownRefresh(load);
</script>

<style scoped>
.page{min-height:100vh;padding:24rpx;background:#f4f6f9}.tabs{display:flex;justify-content:space-around;padding:20rpx;border-radius:16rpx;background:#fff}.tabs view{color:#64748b;font-size:28rpx}.tabs .active{color:#4f46e5;font-weight:700}.composer,.post{margin-top:20rpx;padding:26rpx;border-radius:18rpx;background:#fff}.input{height:76rpx;border-bottom:1px solid #eee;line-height:76rpx}.textarea{width:100%;height:150rpx;margin-top:16rpx;padding:16rpx;box-sizing:border-box;background:#f8fafc}.publish{margin-top:20rpx;background:#4f46e5;color:#fff}.option-edit{display:flex;padding:12rpx 0}.option-edit input{flex:1}.option-edit text{color:#dc2626;font-size:23rpx}.author{color:#94a3b8;font-size:22rpx}.title{margin-top:14rpx;font-size:32rpx;font-weight:700}.content{margin-top:12rpx;color:#475569;font-size:26rpx;line-height:1.6}.vote-head{display:flex;align-items:center;justify-content:space-between;gap:18rpx;margin-top:18rpx}.vote-actions{display:flex;align-items:center;gap:12rpx}.vote-badge{padding:8rpx 18rpx;border-radius:999rpx;font-size:24rpx;font-weight:700}.vote-badge.voted{background:#ecfdf3;color:#027a48}.vote-badge.unvoted{background:#fff7ed;color:#c2410c}.vote-btn{margin:0;background:#4f46e5;color:#fff}.cancel-vote-btn{margin:0;background:#fef3f2;color:#b42318}.poll-option{display:flex;justify-content:space-between;margin-top:12rpx;padding:20rpx;border-radius:12rpx;background:#f1f5f9}.poll-option.selected{background:#ede9fe;color:#6d28d9}.actions{display:flex;gap:34rpx;margin-top:22rpx;color:#64748b;font-size:28rpx}.comment-preview,.inline-comments{margin-top:16rpx;padding:16rpx;border-radius:12rpx;background:#f8fafc}.preview-comment{font-size:24rpx;color:#475569;line-height:1.7}.comment-author{font-weight:700;color:#334155}.comment-time{color:#94a3b8}.reply-to{color:#7c3aed}.expand-comments{margin-top:12rpx;background:#eef2ff;color:#4338ca}.inline-title{font-size:25rpx;font-weight:700;color:#334155}.comments-scroll{height:320rpx;margin-top:10rpx;padding-right:8rpx}.comment-item{padding:16rpx 0;border-bottom:1px solid #e5e7eb}.comment-item.reply-item{padding-left:16rpx;border-left:4rpx solid #ddd6fe;background:rgba(255,255,255,.55)}.comment-main{color:#334155;font-size:25rpx;line-height:1.6}.comment-meta{display:flex;gap:28rpx;margin-top:10rpx;color:#64748b;font-size:24rpx}.reply-toggle{padding:12rpx 0;color:#4f46e5;font-size:24rpx}.empty-comments{padding:44rpx 0;text-align:center;color:#94a3b8}.replying{display:flex;justify-content:space-between;margin-top:14rpx;padding:14rpx;border-radius:10rpx;background:#f5f3ff;color:#6d28d9;font-size:24rpx}.comment-row{display:flex;margin-top:18rpx}.comment-row input{flex:1;padding:0 16rpx;background:#f8fafc}.comment-row button{margin-left:12rpx}.modal-mask{position:fixed;left:0;right:0;top:0;bottom:0;z-index:99;display:flex;align-items:center;justify-content:center;padding:34rpx;background:rgba(15,23,42,.45)}.vote-modal{width:660rpx;max-width:100%;padding:30rpx;border-radius:18rpx;background:#fff;box-sizing:border-box}.modal-title{font-size:34rpx;font-weight:800}.modal-subtitle{margin-top:10rpx;color:#64748b;font-size:24rpx}.vote-choice{display:flex;justify-content:space-between;margin-top:16rpx;padding:22rpx;border-radius:14rpx;background:#f8fafc;color:#334155}.vote-choice.active{background:#ede9fe;color:#6d28d9;font-weight:700}.modal-actions{display:flex;justify-content:flex-end;gap:16rpx;margin-top:28rpx}.cancel{background:#f1f5f9;color:#334155}.confirm{background:#4f46e5;color:#fff}
</style>
