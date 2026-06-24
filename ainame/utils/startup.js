export const getStartupTarget = () => {
  const admin = uni.getStorageSync('admin');
  if (admin) {
    return '/pages/admin-users/admin-users';
  }

  const token = uni.getStorageSync('token');
  if (token) {
    return '/pages/index/index';
  }

  return '/pages/login/login';
};

export const redirectToStartupTarget = () => {
  uni.reLaunch({ url: getStartupTarget() });
};
