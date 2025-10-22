/**
 * 时区工具函数
 *
 * 核心原则：
 * - 后端存储：UTC时间
 * - 前端显示：用户本地时区
 * - 用户输入：本地时区（自动转换为UTC发送给后端）
 */

/**
 * 将本地时间转换为UTC时间字符串
 * @param localDateStr 本地日期字符串 "2025-10-21"
 * @param localTimeStr 本地时间字符串 "15:00"
 * @returns UTC时间的ISO 8601字符串 "2025-10-21T07:00:00Z"
 */
export function localToUTC(localDateStr: string, localTimeStr: string): string {
  // 创建本地时间的Date对象
  const dateTimeParts = `${localDateStr}T${localTimeStr}:00`
  const localDate = new Date(dateTimeParts)

  // 自动转换为UTC（toISOString()返回UTC时间）
  return localDate.toISOString()
}

/**
 * 将UTC时间字符串转换为本地日期
 * @param utcDateTimeStr UTC时间字符串 "2025-10-21T07:00:00Z"
 * @returns 本地日期字符串 "2025-10-21"
 */
export function utcToLocalDate(utcDateTimeStr: string): string {
  const date = new Date(utcDateTimeStr)
  // 获取本地日期
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * 将UTC时间字符串转换为本地时间
 * @param utcDateTimeStr UTC时间字符串 "2025-10-21T07:00:00Z"
 * @returns 本地时间字符串 "15:00"
 */
export function utcToLocalTime(utcDateTimeStr: string): string {
  const date = new Date(utcDateTimeStr)
  // 获取本地时间
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

/**
 * 将UTC时间字符串转换为本地日期时间
 * @param utcDateTimeStr UTC时间字符串 "2025-10-21T07:00:00Z"
 * @returns 本地日期和时间 { date: "2025-10-21", time: "15:00" }
 */
export function utcToLocalDateTime(utcDateTimeStr: string): { date: string; time: string } {
  return {
    date: utcToLocalDate(utcDateTimeStr),
    time: utcToLocalTime(utcDateTimeStr)
  }
}

/**
 * 格式化显示时区信息
 * @returns 时区偏移字符串，如 "UTC+8" 或 "UTC-5"
 */
export function getTimezoneDisplay(): string {
  const offset = -new Date().getTimezoneOffset() / 60
  const sign = offset >= 0 ? '+' : ''
  return `UTC${sign}${offset}`
}

/**
 * 格式化本地时间显示（用于UI）
 * @param utcDateTimeStr UTC时间字符串
 * @returns 格式化的本地时间，如 "2025年10月21日 15:00 (UTC+8)"
 */
export function formatLocalDateTime(utcDateTimeStr: string, showTimezone: boolean = false): string {
  const date = new Date(utcDateTimeStr)

  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  const formatted = `${year}年${month}月${day}日 ${hours}:${minutes}`

  if (showTimezone) {
    return `${formatted} (${getTimezoneDisplay()})`
  }

  return formatted
}
