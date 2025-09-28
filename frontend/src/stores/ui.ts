import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  // 是否处于课程模式（隐藏导航栏）
  const isInCourseMode = ref<boolean>(false)

  // 课程返回路径
  const courseReturnPath = ref<string>('/')

  // 进入课程模式
  const enterCourseMode = (returnPath: string = '/') => {
    isInCourseMode.value = true
    courseReturnPath.value = returnPath
    console.log('进入课程模式，返回路径:', returnPath)
  }

  // 退出课程模式
  const exitCourseMode = () => {
    isInCourseMode.value = false
    courseReturnPath.value = '/'
    console.log('退出课程模式')
  }

  // 临时退出课程模式（保留计时）
  const temporaryExitCourseMode = () => {
    isInCourseMode.value = false
    console.log('临时退出课程模式，保留计时')
  }

  // 完全结束课程（清除计时）
  const endCourse = () => {
    isInCourseMode.value = false
    courseReturnPath.value = '/'
    // 清除计时开始时间
    sessionStorage.removeItem('courseStartTime')
    console.log('课程结束，清除计时')
  }

  return {
    isInCourseMode,
    courseReturnPath,
    enterCourseMode,
    exitCourseMode,
    temporaryExitCourseMode,
    endCourse
  }
})