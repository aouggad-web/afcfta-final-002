export const mobileDetect = {
  isMobile: () => window.innerWidth < 768,

  isTablet: () => window.innerWidth >= 768 && window.innerWidth < 1024,

  isDesktop: () => window.innerWidth >= 1024,

  isTouchDevice: () => 'ontouchstart' in window || navigator.maxTouchPoints > 0,

  getDeviceType: () => {
    if (mobileDetect.isMobile()) return 'mobile';
    if (mobileDetect.isTablet()) return 'tablet';
    return 'desktop';
  },

  onResize: (callback) => {
    if (typeof callback !== 'function') return () => {};
    const handler = () => callback(mobileDetect.getDeviceType());
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  },
};
