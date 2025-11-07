<template>
  <div class="version-info">
    <span class="version-text">版本: {{ version }}</span>
    <span class="build-time">构建: {{ buildTime }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import packageJson from '../../package.json'

const version = ref(packageJson.version)
const buildTime = ref(import.meta.env.VITE_BUILD_TIME || '开发模式')
</script>

<style scoped>
.version-info {
  position: fixed;
  bottom: 10px;
  right: 10px;
  display: flex;
  gap: 15px;
  padding: 8px 15px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e4e7ed;
  border-radius: 20px;
  font-size: 12px;
  color: #909399;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.version-text,
.build-time {
  white-space: nowrap;
}

@media (max-width: 768px) {
  .version-info {
    display: none; /* 手机端隐藏版本信息 */
  }
}
</style>
