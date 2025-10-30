/**
 * 课程配置文件
 *
 * 所有课程相关的时间限制和配置都在这里管理
 */

/**
 * 课程时间限制配置（单位：分钟）
 *
 *
 * 当学习时间达到此限制时，系统会自动跳转到训后检测
 * 防止课程拖堂，确保按时结束
 */
export const COURSE_TIME_LIMIT_MINUTES = 10  // 修改时间限制（分钟）

/**
 * 转换为秒（内部使用，不需要修改）
 */
export const COURSE_TIME_LIMIT_SECONDS = COURSE_TIME_LIMIT_MINUTES * 60

/**
 * 时间限制警告阈值（提前多少分钟提醒）
 */
export const TIME_WARNING_BEFORE_MINUTES = 5

/**
 * 时间限制警告阈值（秒）
 */
export const TIME_WARNING_BEFORE_SECONDS = TIME_WARNING_BEFORE_MINUTES * 60

/**
 * 课程类型
 */
export const COURSE_TYPES = {
  LEARNING: 'learning',   // 单词学习
  REVIEW: 'review'        // 抗遗忘复习
} as const

/**
 * 使用说明：
 *
 * 如果想测试自动跳转功能：
 * 1. 将 COURSE_TIME_LIMIT_MINUTES 改为 1（1分钟）
 * 2. 保存文件
 * 3. 重新构建前端：npm run build-only
 * 4. 部署到服务器测试
 * 5. 测试完成后改回 60
 *
 * 如果想修改正式课程时长：
 * 1. 根据实际需求修改 COURSE_TIME_LIMIT_MINUTES
 * 2. 常见值：30分钟（小课）、60分钟（大课）、90分钟（长课）
 * 3. 保存并重新部署
 */
