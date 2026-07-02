export const CURRENT_VERSION_NAME = '1.0.4';
export const CURRENT_VERSION_CODE = 104;

export const getCurrentAppVersion = () => {
  return new Promise((resolve) => {
    if (typeof plus !== 'undefined' && plus.runtime && plus.runtime.getProperty) {
      plus.runtime.getProperty(plus.runtime.appid, (widgetInfo) => {
        resolve({
          versionName: widgetInfo.version || CURRENT_VERSION_NAME,
          versionCode: Number(widgetInfo.versionCode || CURRENT_VERSION_CODE)
        });
      });
      return;
    }
    resolve({
      versionName: CURRENT_VERSION_NAME,
      versionCode: CURRENT_VERSION_CODE
    });
  });
};

export const getPlatform = () => {
  const info = uni.getSystemInfoSync();
  return info.platform || 'app';
};
