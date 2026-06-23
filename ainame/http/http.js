// http/http.js

// 动态获取环境：开发模式连接本地后端，发行模式连接线上域名
const BASE_URL = "http://127.0.0.1:8000";

/**
 * 核心请求封装函数
 */
const request = (url, options) => {
  // 每次请求前，动态获取最新的 token
  const token = uni.getStorageSync("token");
  
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      header: {
        "content-type": "application/json",
        "authorization": token ? "Bearer " + token : ""
      },
      ...options,
      success: (res) => {
        // HTTP 状态码 200 代表完全成功
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          // --- 核心修复：智能解析 FastAPI 的错误格式 ---
          let errorMsg = '服务器请求失败';
          
          if (res.data && Array.isArray(res.data.detail)) {
            // 捕获 Pydantic 数据校验 422 错误 (Array 格式)
            // 取第一条错误信息并展示
            errorMsg = res.data.detail[0].msg || '表单参数校验失败';
          } else if (res.data && typeof res.data.detail === 'string') {
            // 捕获我们自定义的 HttpException 错误 (String 格式)
            errorMsg = res.data.detail;
          }
          
          // 确保 title 绝对是字符串，防止前端崩溃红屏
          uni.showToast({ 
            title: String(errorMsg), 
            icon: 'none', 
            duration: 3000 
          });
          
          // 将错误抛出，供业务层 catch 处理（比如用来关掉 loading 动画）
          reject(res.data);
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络连接断开，请检查网络', icon: 'none' });
        reject(err);
      }
    });
  });
};

/**
 * 专门处理文件上传的封装函数 (针对 RAG 私有知识库)
 */
const uploadFile = (url, filePath) => {
  const token = uni.getStorageSync("token");
  
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + url,
      filePath: filePath,
      name: 'file',
      header: { 
        "authorization": token ? "Bearer " + token : "" 
      },
      success: (res) => {
        if (res.statusCode === 200) {
          // uni.uploadFile 返回的 data 是字符串格式的 JSON，需要手动 parse
          resolve(JSON.parse(res.data));
        } else {
          let responseData = res.data;
          try {
            responseData = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
          } catch (_) {}
          const errorMsg = responseData && responseData.detail
            ? responseData.detail
            : '文件上传失败';
          uni.showToast({ title: String(errorMsg), icon: 'none', duration: 3000 });
          reject(responseData || res);
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络异常，上传中断', icon: 'none' });
        reject(err);
      }
    });
  });
};

// 导出所有后端接口
export default {
  // ================= 1. 账号鉴权接口 =================
  getEmailCode: (email) => request("/auth/code?email=" + email, { method: 'GET' }),
  register: (data) => request("/auth/register", { method: 'POST', data }),
  login: (data) => request("/auth/login", { method: 'POST', data }),

  // ================= 管理员接口 =================
  adminLogin: (data) => request("/admin/login", { method: 'POST', data }),
  getAdminUsers: ({ page = 1, pageSize = 20, keyword = '' } = {}) =>
    request(`/admin/users?page=${page}&page_size=${pageSize}&keyword=${encodeURIComponent(keyword)}`, { method: 'GET' }),
  freezeUser: (userId, isFrozen) => request(`/admin/users/${userId}/freeze`, {
    method: 'PATCH', data: { is_frozen: isFrozen }
  }),
  resetUserPassword: (userId, newPassword) => request(`/admin/users/${userId}/reset-password`, {
    method: 'POST', data: { new_password: newPassword }
  }),
  deleteUser: (userId) => request(`/admin/users/${userId}`, { method: 'DELETE' }),
  grantVip: (userId, planCode = 'vip_monthly') => request('/vip/admin/grant', { method: 'POST', data: { user_id: userId, plan_code: planCode } }),
  verifyExpert: (data) => request('/experts/admin/verify', { method: 'POST', data }),
  
  // ================= 2. 智能体核心工作流 =================
  generateName: (data) => request("/names/generate", { method: 'POST', data }), // 首次起名 (无记忆)
  feedbackName: (data) => request("/names/feedback", { method: 'POST', data }), // 多轮微调 (带记忆 thread_id)
  
  // ================= 3. RAG 知识库接口 =================
  uploadKnowledge: (filePath) => uploadFile("/knowledge/upload", filePath),

  // ================= 4. 品牌视觉工作台 =================
  createBrandProject: (data) => request("/brands", { method: 'POST', data }),
  getBrandProjects: () => request("/brands", { method: 'GET' }),
  getBrandProject: (projectId) => request(`/brands/${projectId}`, { method: 'GET' }),
  generateBrandStrategy: (projectId) => request(`/brands/${projectId}/strategy`, { method: 'POST' }),
  generateBrandVisuals: (projectId, data) => request(`/brands/${projectId}/visuals`, { method: 'POST', data }),
  getVisualJob: (jobId) => request(`/brands/visual-jobs/${jobId}`, { method: 'GET' }),
  getAssetUrl: (fileUrl) => fileUrl && fileUrl.startsWith('http') ? fileUrl : BASE_URL + fileUrl,

  // ================= 5. 用户中心与 VIP =================
  getUserCenter: () => request('/me', { method: 'GET' }),
  updateProfile: (data) => request('/me/profile', { method: 'PATCH', data }),
  uploadAvatar: (filePath) => uploadFile('/me/avatar', filePath),
  deleteAvatar: () => request('/me/avatar', { method: 'DELETE' }),
  getDefaultAvatars: () => request('/me/avatar/defaults', { method: 'GET' }),
  selectDefaultAvatar: (avatarKey) => request('/me/avatar/default', { method: 'PUT', data: { avatar_key: avatarKey } }),
  changePassword: (data) => request('/me/password', { method: 'POST', data }),
  getVipPlans: () => request('/vip/plans', { method: 'GET' }),
  createVipOrder: (planCode) => request('/vip/orders', { method: 'POST', data: { plan_code: planCode } }),
  mockPayVipOrder: (orderId) => request(`/vip/orders/${orderId}/mock-pay`, { method: 'POST' }),
  getVipOrders: () => request('/vip/orders', { method: 'GET' }),

  // ================= 6. 社区与灵感投票 =================
  getCommunityPosts: (postType = '') => request(`/community/posts${postType ? `?post_type=${postType}` : ''}`, { method: 'GET' }),
  createCommunityPost: (data) => request('/community/posts', { method: 'POST', data }),
  likeCommunityPost: (postId) => request(`/community/posts/${postId}/like`, { method: 'POST' }),
  commentCommunityPost: (postId, content) => request(`/community/posts/${postId}/comments`, { method: 'POST', data: { content } }),
  voteCommunityPoll: (postId, optionId) => request(`/community/posts/${postId}/vote`, { method: 'POST', data: { option_id: optionId } }),

  // ================= 7. 专家精批 =================
  getExpertServices: () => request('/experts/services', { method: 'GET' }),
  createExpertOrder: (data) => request('/experts/orders', { method: 'POST', data }),
  mockPayExpertOrder: (orderId) => request(`/experts/orders/${orderId}/mock-pay`, { method: 'POST' }),
  getExpertOrders: () => request('/experts/orders', { method: 'GET' }),
  getExpertWorkbenchOrders: () => request('/experts/workbench/orders', { method: 'GET' }),
  createExpertService: (data) => request('/experts/workbench/services', { method: 'POST', data }),
  generateExpertDraft: (orderId) => request(`/experts/workbench/orders/${orderId}/ai-draft`, { method: 'POST' }),
  deliverExpertReport: (orderId, finalReport) => request(`/experts/workbench/orders/${orderId}/report`, { method: 'POST', data: { final_report: finalReport } }),

  // ================= 8. 钱包、邀请与分销 =================
  getGrowthCenter: () => request('/growth', { method: 'GET' }),
  createRecharge: (amountCents) => request('/growth/recharges', { method: 'POST', data: { amount_cents: amountCents } }),
  mockPayRecharge: (orderId) => request(`/growth/recharges/${orderId}/mock-pay`, { method: 'POST' }),
  createWithdrawal: (data) => request('/growth/withdrawals', { method: 'POST', data }),
  applyPartner: (data) => request('/growth/partner/apply', { method: 'POST', data }),
  payVipWithBalance: (orderId) => request(`/growth/pay/vip/${orderId}`, { method: 'POST' }),
  payExpertWithBalance: (orderId) => request(`/growth/pay/expert/${orderId}`, { method: 'POST' }),
  getGrowthReviews: () => request('/growth/admin/review', { method: 'GET' }),
  reviewWithdrawal: (id, approved, note = '') => request(`/growth/admin/withdrawals/${id}/review`, { method: 'POST', data: { approved, note } }),
  reviewPartner: (id, approved, commissionBps = 1000, note = '') => request(`/growth/admin/partners/${id}/review`, { method: 'POST', data: { approved, commission_bps: commissionBps, note } }),
  settleCommission: (id) => request(`/growth/admin/commissions/${id}/settle`, { method: 'POST' })
};
