<template>
  <div class="timeline-editor">
    <div class="linked-mode-toggle">
      <el-switch v-model="linkedMode" size="small" />
      <span class="linked-mode-label">
        联动相邻段（开启后调整某段的开头/结尾，相邻段的对应边界会一起变动）
      </span>
    </div>

    <div class="timeline-track" ref="trackEl">
      <div
        v-for="(seg, idx) in segments"
        :key="idx"
        class="timeline-segment"
        :class="{ 'low-score': (seg.match_score ?? 1) < 0.7 }"
        :style="segStyle(seg)"
        @click="$emit('preview', idx)"
      >
        <div
          class="handle handle-start"
          @mousedown.stop="startDrag(idx, 'start', $event)"
        />
        <span class="seg-label">{{ idx + 1 }}</span>
        <div
          class="handle handle-end"
          @mousedown.stop="startDrag(idx, 'end', $event)"
        />
      </div>
    </div>

    <div class="segment-list">
      <div v-for="(seg, idx) in segments" :key="idx" class="segment-row">
        <div class="segment-row-top">
          <span class="seg-index">第{{ idx + 1 }}段</span>
          <span class="seg-text">{{ truncate(seg.text, 30) }}</span>
          <el-tag
            v-if="seg.match_score !== undefined"
            :type="seg.match_score >= 0.7 ? 'success' : 'danger'"
            size="small"
          >
            置信度 {{ Math.round(seg.match_score * 100) }}%
          </el-tag>
        </div>
        <div class="segment-row-bottom">
          <el-input-number
            :model-value="seg.start"
            :min="0"
            :max="audioDuration"
            :step="0.1"
            :precision="1"
            size="small"
            controls-position="right"
            style="width: 110px"
            @change="(val: number) => onStartInputChange(idx, val)"
          />
          <span class="seg-sep">→</span>
          <el-input-number
            :model-value="seg.end"
            :min="0"
            :max="audioDuration"
            :step="0.1"
            :precision="1"
            size="small"
            controls-position="right"
            style="width: 110px"
            @change="(val: number) => onEndInputChange(idx, val)"
          />
          <el-button size="small" type="primary" plain @click="$emit('preview', idx)">试听</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

export interface TimelineSegment {
  index: number
  text: string
  start: number
  end: number
  match_score?: number
}

const props = defineProps<{
  modelValue: TimelineSegment[]
  audioDuration: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: TimelineSegment[]): void
  (e: 'preview', index: number): void
}>()

const segments = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const trackEl = ref<HTMLElement>()

const segStyle = (seg: TimelineSegment) => {
  const duration = props.audioDuration || 1
  const left = (seg.start / duration) * 100
  const width = ((seg.end - seg.start) / duration) * 100
  return {
    left: `${left}%`,
    width: `${Math.max(width, 0.5)}%`
  }
}

const truncate = (text: string, len: number) => {
  return text.length > len ? text.slice(0, len) + '…' : text
}

// 联动模式：开启后，调整某段的开头/结尾时，相邻段的对应边界会一起变动，
// 这样只需要反复调整x+1段的开头，就能同时把x段的结尾对准，不用来回试听两段
const linkedMode = ref(true)

// 统一的边界设置入口：无论是拖拽还是手动输入，都走这里，保证联动逻辑一致
const setSegmentEdge = (idx: number, edge: 'start' | 'end', value: number) => {
  const seg = segments.value[idx]
  const clamped = Math.max(0, Math.min(props.audioDuration, value))

  if (edge === 'start') {
    seg.start = Math.min(clamped, seg.end - 0.1)
    if (linkedMode.value && idx > 0) {
      // 联动上一段的结尾，让它跟当前段的开头对齐
      const prev = segments.value[idx - 1]
      prev.end = Math.max(seg.start, prev.start + 0.1)
    }
  } else {
    seg.end = Math.max(clamped, seg.start + 0.1)
    if (linkedMode.value && idx < segments.value.length - 1) {
      // 联动下一段的开头，让它跟当前段的结尾对齐
      const next = segments.value[idx + 1]
      next.start = Math.min(seg.end, next.end - 0.1)
    }
  }
  emit('update:modelValue', segments.value)
}

const onStartInputChange = (idx: number, val: number) => {
  if (val === null || val === undefined || Number.isNaN(val)) return
  setSegmentEdge(idx, 'start', val)
}

const onEndInputChange = (idx: number, val: number) => {
  if (val === null || val === undefined || Number.isNaN(val)) return
  setSegmentEdge(idx, 'end', val)
}

// 拖拽逻辑：拖动某段的开始或结束边界
let dragState: { idx: number; edge: 'start' | 'end'; startX: number; origValue: number } | null = null

const startDrag = (idx: number, edge: 'start' | 'end', event: MouseEvent) => {
  dragState = {
    idx,
    edge,
    startX: event.clientX,
    origValue: edge === 'start' ? segments.value[idx].start : segments.value[idx].end
  }
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}

const onDrag = (event: MouseEvent) => {
  if (!dragState || !trackEl.value) return
  const trackWidth = trackEl.value.getBoundingClientRect().width
  if (trackWidth <= 0) return

  const deltaX = event.clientX - dragState.startX
  const deltaSeconds = (deltaX / trackWidth) * props.audioDuration
  let newValue = Math.max(0, Math.min(props.audioDuration, dragState.origValue + deltaSeconds))
  newValue = Math.round(newValue * 10) / 10

  setSegmentEdge(dragState.idx, dragState.edge, newValue)
}

const stopDrag = () => {
  dragState = null
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}
</script>

<style scoped>
.timeline-editor {
  width: 100%;
}

.linked-mode-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.linked-mode-label {
  font-size: 12px;
  color: #909399;
}

.timeline-track {
  position: relative;
  height: 48px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.timeline-segment {
  position: absolute;
  top: 4px;
  bottom: 4px;
  background: #a0cfff;
  border: 1px solid #409eff;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  min-width: 8px;
}

.timeline-segment.low-score {
  background: #fde2e2;
  border-color: #f56c6c;
}

.seg-label {
  font-size: 11px;
  color: #303133;
  pointer-events: none;
  user-select: none;
}

.handle {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: ew-resize;
  background: rgba(64, 158, 255, 0.6);
}

.handle-start {
  left: 0;
  border-radius: 3px 0 0 3px;
}

.handle-end {
  right: 0;
  border-radius: 0 3px 3px 0;
}

.segment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.segment-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.segment-row-top {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.segment-row-bottom {
  display: flex;
  align-items: center;
  gap: 10px;
}

.seg-index {
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
  min-width: 48px;
}

.seg-text {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.seg-sep {
  color: #909399;
}
</style>
