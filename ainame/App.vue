<script setup>
import { onLaunch } from '@dcloudio/uni-app';
import { redirectToStartupTarget } from '@/utils/startup.js';

onLaunch(() => {
  // #ifndef APP-PLUS
  redirectToStartupTarget();
  // #endif
});
</script>

<style>
/* #ifdef H5 */
body {
  min-height: 100vh;
  background-color: #0f172a;
  background-image: url('/static/launch-cover.jpg'), url('/static/launch-cover.jpg');
  background-repeat: no-repeat, no-repeat;
  background-position: left center, right center;
  background-size: max(260px, calc((100vw - 750px) / 2)) 100vh, max(260px, calc((100vw - 750px) / 2)) 100vh;
  background-attachment: fixed, fixed;
}

#app {
  max-width: 750px;
  min-height: 100vh;
  margin: 0 auto;
  background: #f5f7fa;
}
/* #endif */
</style>
