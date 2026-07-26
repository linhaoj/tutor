<template>
  <div class="audio-player-bar">
    <audio
      ref="audioEl"
      :src="src"
      @loadedmetadata="onLoadedMetadata"
      @timeupdate="onTimeUpdate"
      @ended="onEnded"
      preload="metadata"
    />

    <div class="player-controls-row">
      <el-button
        circle
        size="small"
        :icon="ArrowLeftBold"
        :disabled="disablePrev"
        @click="$emit('prev')"
      />
      <el-button
        circle
        :icon="isPlaying ? VideoPause : VideoPlay"
        type="primary"
        @click="togglePlay"
      />
      <el-button
        circle
        size="small"
        :icon="ArrowRightBold"
        :disabled="disableNext"
        @click="$emit('next')"
      />

      <span class="time-info">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>

      <el-dropdown trigger="click" @command="onSpeedChange" class="speed-dropdown">
        <el-button size="small" plain>{{ playbackRate }}x</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-for="rate in speedOptions"
              :key="rate"
              :command="rate"
            >{{ rate }}x</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div class="progress-row">
      <el-slider
        v-model="sliderValue"
        :max="duration || 0"
        :step="0.1"
        class="progress-slider"
        :show-tooltip="false"
        @change="onSeek"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { VideoPlay, VideoPause, ArrowLeftBold, ArrowRightBold } from '@element-plus/icons-vue'

const props = defineProps<{ src: string; disablePrev?: boolean; disableNext?: boolean }>()
const emit = defineEmits<{
  (e: 'timeupdate', currentTime: number): void
  (e: 'prev'): void
  (e: 'next'): void
}>()

const audioEl = ref<HTMLAudioElement>()
const isPlaying = ref(false)
const currentTime = ref(0)
const sliderValue = ref(0)
const duration = ref(0)
const playbackRate = ref(1)
const speedOptions = [0.75, 1, 1.25, 1.5]

// 用于"只播放某一段"的临时区间限制
let segmentEndLimit: number | null = null

const onLoadedMetadata = () => {
  if (audioEl.value) duration.value = audioEl.value.duration || 0
}

const onTimeUpdate = () => {
  if (!audioEl.value) return
  currentTime.value = audioEl.value.currentTime
  sliderValue.value = audioEl.value.currentTime
  emit('timeupdate', audioEl.value.currentTime)

  if (segmentEndLimit !== null && audioEl.value.currentTime >= segmentEndLimit) {
    audioEl.value.pause()
    isPlaying.value = false
    segmentEndLimit = null
  }
}

const onEnded = () => {
  isPlaying.value = false
}

const togglePlay = () => {
  if (!audioEl.value) return
  if (isPlaying.value) {
    audioEl.value.pause()
    isPlaying.value = false
  } else {
    segmentEndLimit = null
    audioEl.value.play()
    isPlaying.value = true
  }
}

const onSeek = (value: number | number[]) => {
  if (!audioEl.value) return
  const v = Array.isArray(value) ? value[0] : value
  audioEl.value.currentTime = v
  segmentEndLimit = null
}

const onSpeedChange = (rate: number) => {
  playbackRate.value = rate
  if (audioEl.value) audioEl.value.playbackRate = rate
}

const formatTime = (seconds: number): string => {
  if (!seconds || isNaN(seconds)) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// 跳转到指定时间并播放（供父组件点击段落/上一句/下一句时调用）
const seekTo = (seconds: number) => {
  if (!audioEl.value) return
  audioEl.value.currentTime = seconds
  segmentEndLimit = null
  audioEl.value.play()
  isPlaying.value = true
}

// 只播放某个区间（供"试听这一段"功能调用）
const playSegment = (start: number, end: number) => {
  if (!audioEl.value) return
  audioEl.value.currentTime = start
  segmentEndLimit = end
  audioEl.value.play()
  isPlaying.value = true
}

const pause = () => {
  if (audioEl.value) {
    audioEl.value.pause()
    isPlaying.value = false
  }
}

defineExpose({ seekTo, playSegment, pause })

onBeforeUnmount(() => {
  if (audioEl.value) {
    audioEl.value.pause()
  }
})
</script>

<style scoped>
.audio-player-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px 20px 10px;
  background: #fff;
  border-top: 1px solid #e4e7ed;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.player-controls-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-info {
  font-size: 13px;
  color: #606266;
  min-width: 96px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.speed-dropdown {
  margin-left: 4px;
}

.progress-row {
  width: 100%;
  display: flex;
  justify-content: center;
}

.progress-slider {
  width: 33%;
  min-width: 200px;
}
</style>
