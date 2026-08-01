<template>
  <div class="admin-container">
    <div class="admin-header">
      <div class="header-left">
        <h1>系统管理</h1>
        <el-tag type="danger" size="large">管理员</el-tag>
      </div>
      <div class="header-right">
        <span class="welcome-text">欢迎，{{ authStore.currentUser?.display_name }}</span>
        <el-dropdown @command="handleCommand">
          <el-button type="primary">
            <el-icon><Avatar /></el-icon>
            操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="dashboard">进入主页面</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="admin-content">
      <el-tabs v-model="activeTab" class="admin-tabs">
        <el-tab-pane label="用户管理" name="users">
          <!-- 用户管理区域 -->
          <el-card class="user-management">
        <template #header>
          <div class="card-header">
            <span>用户管理</span>
            <el-button type="primary" @click="showAddUserDialog">
              <el-icon><Plus /></el-icon>
              添加用户
            </el-button>
          </div>
        </template>

        <div class="users-list">
          <el-table :data="users" style="width: 100%">
            <el-table-column prop="display_name" label="姓名" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role" label="角色">
              <template #default="scope">
                <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'success'">
                  {{ scope.row.role === 'admin' ? '管理员' : '教师' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="createdAt" label="创建时间">
              <template #default="scope">
                {{ formatDate(scope.row.createdAt) }}
              </template>
            </el-table-column>
            <el-table-column prop="lastLoginAt" label="最后登录">
              <template #default="scope">
                {{ scope.row.lastLoginAt ? formatDate(scope.row.lastLoginAt) : '从未登录' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button
                  size="small"
                  @click="editUser(scope.row)"
                  :disabled="scope.row.id === authStore.currentUser?.id"
                >
                  编辑
                </el-button>
                <el-button
                  size="small"
                  @click="resetPassword(scope.row)"
                  :disabled="scope.row.id === authStore.currentUser?.id"
                >
                  重置密码
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="deleteUser(scope.row)"
                  :disabled="scope.row.id === authStore.currentUser?.id"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
        </el-tab-pane>

        <el-tab-pane label="教师数据管理" name="teacherData">
          <!-- 教师数据管理区域 -->
          <el-card class="teacher-data-management">
            <template #header>
              <div class="card-header">
                <span>教师数据管理</span>
                <div class="header-actions">
                  <el-alert 
                    v-if="teachers.length === 0" 
                    title="暂无教师账号"
                    description="请先在用户管理中创建教师账号，管理员专注系统管理工作"
                    type="info"
                    :closable="false"
                    show-icon
                    style="margin-right: 20px;"
                  />
                  <el-select 
                    v-model="selectedTeacherId" 
                    placeholder="选择教师"
                    @change="loadTeacherData"
                    style="width: 200px"
                    :disabled="teachers.length === 0"
                  >
                    <el-option
                      v-for="teacher in teachers"
                      :key="teacher.id"
                      :label="teacher.display_name"
                      :value="teacher.id"
                    />
                  </el-select>
                </div>
              </div>
            </template>

            <div v-if="selectedTeacherId" class="teacher-data-tabs">
              <el-tabs v-model="activeDataTab" class="data-tabs">
                <!-- 学生管理 -->
                <el-tab-pane label="学生管理" name="students">
                  <div class="data-section">
                    <div class="section-header">
                      <span>{{ getSelectedTeacherName() }} - 学生管理</span>
                      <el-button type="primary" @click="showAddStudentDialog">
                        <el-icon><Plus /></el-icon>
                        添加学生
                      </el-button>
                    </div>
                    <el-table :data="teacherStudents" style="width: 100%">
                      <el-table-column prop="name" label="姓名" />
                      <el-table-column prop="email" label="邮箱" />
                      <el-table-column label="剩余课时" width="120">
                        <template #default="scope">
                          <span :class="getHoursClass(scope.row.remaining_hours)">
                            {{ (scope.row.remaining_hours || 0).toFixed(1) }}h
                          </span>
                        </template>
                      </el-table-column>
                      <el-table-column label="操作" width="200">
                        <template #default="scope">
                          <el-button size="small" @click="editStudent(scope.row)">编辑</el-button>
                          <el-button size="small" type="primary" @click="editStudentHours(scope.row)">课时</el-button>
                          <el-button size="small" type="danger" @click="deleteStudent(scope.row)">删除</el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                </el-tab-pane>

                <!-- 单词管理 -->
                <el-tab-pane label="单词管理" name="words">
                  <div class="data-section">
                    <div class="section-header">
                      <span>{{ getSelectedTeacherName() }} - 单词管理</span>
                      <div>
                        <el-button @click="showAddWordSetDialog">
                          <el-icon><Plus /></el-icon>
                          添加单词集
                        </el-button>
                        <el-button type="success" @click="importWords">
                          <el-icon><Upload /></el-icon>
                          导入Excel
                        </el-button>
                      </div>
                    </div>
                    <div class="words-content">
                      <div class="word-sets-panel">
                        <h3>单词集列表</h3>
                        <div class="word-sets">
                          <div 
                            v-for="wordSet in teacherWordSets" 
                            :key="wordSet.name"
                            class="word-set-item"
                            :class="{ active: selectedWordSet === wordSet.name }"
                          >
                            <div class="word-set-content" @click="selectWordSet(wordSet.name)">
                              <span>{{ wordSet.name }}</span>
                              <span class="word-count">({{ wordSet.word_count || 0 }} 个单词)</span>
                            </div>
                            <el-button 
                              type="danger" 
                              size="small" 
                              :icon="Delete"
                              @click.stop="deleteWordSet(wordSet)"
                              class="delete-btn"
                            />
                          </div>
                        </div>
                      </div>
                      <div class="words-panel" v-if="selectedWordSet">
                        <h3>{{ selectedWordSet }} - 单词列表</h3>
                        <div class="words-list">
                          <div v-for="word in getCurrentWords()" :key="word.english" class="word-item">
                            <strong>{{ word.english }}</strong>
                            <span>{{ word.chinese }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-tab-pane>

                <!-- 日程管理 -->
                <el-tab-pane label="日程管理" name="schedule">
                  <div class="data-section">
                    <div class="section-header">
                      <span>{{ getSelectedTeacherName() }} - 日程管理</span>
                      <el-button type="primary" @click="showAddScheduleDialog">
                        <el-icon><Plus /></el-icon>
                        添加课程
                      </el-button>
                    </div>
                    <div class="schedule-list">
                      <div 
                        v-for="dateGroup in groupedTeacherSchedules" 
                        :key="dateGroup.date"
                        class="date-group"
                      >
                        <div class="date-header">
                          <span class="date-text">{{ formatDate(dateGroup.date) }}</span>
                          <span class="course-count">{{ dateGroup.schedules.length }} 门课程</span>
                        </div>
                        <div class="schedule-items">
                          <div
                            v-for="schedule in dateGroup.schedules"
                            :key="schedule.id"
                            class="schedule-item"
                          >
                            <div class="schedule-time">{{ schedule.time }}</div>
                            <div class="schedule-content">
                              <div class="schedule-info-row">
                                <span class="info-label">学生:</span>
                                <span class="info-value student">{{ schedule.student_name }}</span>
                                <span class="info-separator">|</span>
                                <span class="info-label">单词库:</span>
                                <span class="info-value wordset">{{ schedule.word_set_name }}</span>
                              </div>
                              <div class="schedule-type">
                                <el-tag
                                  :type="courseTypeTagType(schedule.course_type)"
                                  size="small"
                                >
                                  {{ courseTypeLabel(schedule.course_type) }}
                                </el-tag>
                                <el-tag
                                  type="primary"
                                  size="small"
                                  style="margin-left: 8px"
                                >
                                  大课
                                </el-tag>
                                <span class="duration-text">{{ schedule.duration || 60 }}分钟</span>
                              </div>
                            </div>
                            <div class="schedule-actions">
                              <el-button size="small" @click="editSchedule(schedule)">编辑</el-button>
                              <el-button size="small" type="warning" @click="resetTimer(schedule)">重置计时</el-button>
                              <el-button size="small" type="danger" @click="deleteSchedule(schedule)">删除</el-button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </div>

            <div v-else class="no-teacher-selected">
              <el-empty description="请选择一个教师开始管理数据" />
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="数据管理" name="dataManagement">
          <!-- 数据管理页面 -->
          <div class="data-management-section">
            <el-card>
              <template #header>
                <span>数据管理</span>
              </template>
              <div class="data-actions">
                <div class="action-grid">
                  <el-button 
                    type="primary" 
                    size="large"
                    @click="goToDataManagement"
                  >
                    <el-icon><Setting /></el-icon>
                    打开数据管理
                  </el-button>
                  <el-button 
                    type="success" 
                    size="large"
                    @click="exportAllData"
                  >
                    <el-icon><Download /></el-icon>
                    快速导出数据
                  </el-button>
                </div>
                <div class="data-info">
                  <p>数据管理功能包括：</p>
                  <ul>
                    <li>导出所有数据到JSON文件</li>
                    <li>从JSON文件导入数据</li>
                    <li>查看数据统计信息</li>
                    <li>清空所有数据（危险操作）</li>
                  </ul>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 添加用户对话框 -->
    <el-dialog 
      v-model="addUserDialogVisible" 
      title="添加用户"
      width="500px"
    >
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="userForm.confirmPassword" type="password" placeholder="请确认密码" />
        </el-form-item>
        <el-form-item label="姓名" prop="displayName">
          <el-input v-model="userForm.displayName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色">
            <el-option label="教师" value="teacher">
              <div>
                <div><strong>教师</strong></div>
                <div style="font-size: 12px; color: #999;">负责教学工作，管理自己的学生和课程</div>
              </div>
            </el-option>
            <el-option label="管理员" value="admin">
              <div>
                <div><strong>管理员</strong></div>
                <div style="font-size: 12px; color: #999;">系统管理员，不参与具体教学</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addUserDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddUser" :loading="submitting">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog 
      v-model="editUserDialogVisible" 
      title="编辑用户"
      width="500px"
    >
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="displayName">
          <el-input v-model="editForm.displayName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" placeholder="请选择角色">
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editUserDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEditUser" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog 
      v-model="resetPasswordDialogVisible" 
      title="重置密码"
      width="400px"
    >
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请确认密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitResetPassword" :loading="submitting">
          重置
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加学生对话框 -->
    <el-dialog
      v-model="addStudentDialogVisible"
      title="添加学生"
      width="500px"
    >
      <el-form :model="studentForm" label-width="100px">
        <el-form-item label="学生姓名" required>
          <el-input v-model="studentForm.name" placeholder="请输入学生姓名" />
        </el-form-item>

        <el-form-item label="登录用户名" required>
          <el-input v-model="studentForm.username" placeholder="请输入登录用户名" />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            学生将使用此用户名登录学生端
          </div>
        </el-form-item>

        <el-form-item label="登录密码" required>
          <el-input v-model="studentForm.password" type="password" placeholder="请输入登录密码" />
        </el-form-item>

        <el-form-item label="确认密码" required>
          <el-input v-model="studentForm.confirmPassword" type="password" placeholder="请确认密码" />
        </el-form-item>

        <el-form-item label="邮箱">
          <el-input v-model="studentForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>

        <el-form-item label="剩余课时">
          <el-input-number
            v-model="studentForm.remainingHours"
            :precision="1"
            :step="0.5"
            :min="0"
            :max="1000"
            placeholder="剩余课程时长（小时）"
            style="width: 100%"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            1节课 = 1.0小时
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addStudentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddStudent" :loading="submitting">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑学生对话框 -->
    <el-dialog
      v-model="editStudentDialogVisible"
      title="编辑学生信息"
      width="500px"
    >
      <el-form :model="editStudentForm" label-width="100px">
        <el-form-item label="学生姓名" required>
          <el-input v-model="editStudentForm.name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editStudentForm.email" placeholder="可选" />
        </el-form-item>
        <el-form-item v-if="editStudentForm.hasAccount" label="用户名">
          <el-input v-model="editStudentForm.username" disabled />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            账号已创建，不可修改用户名
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editStudentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEditStudent">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑学生课时对话框 -->
    <el-dialog 
      v-model="editHoursDialogVisible" 
      title="编辑学生课时"
      width="450px"
    >
      <el-form :model="editHoursForm" label-width="120px">
        <el-form-item label="学生姓名">
          <el-input v-model="editHoursForm.name" disabled />
        </el-form-item>
        <el-form-item label="所属教师">
          <el-input v-model="selectedTeacherName" disabled />
        </el-form-item>
        <el-form-item label="当前剩余课时">
          <el-input :value="(editHoursForm.currentHours || 0).toFixed(1) + 'h'" disabled />
        </el-form-item>
        <el-form-item label="调整方式">
          <el-radio-group v-model="hoursAdjustmentType">
            <el-radio value="set">直接设置</el-radio>
            <el-radio value="add">增加课时</el-radio>
            <el-radio value="subtract">扣除课时</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="getHoursAdjustmentLabel()">
          <el-input-number 
            v-model="hoursAdjustmentValue" 
            :precision="1"
            :step="0.5"
            :min="hoursAdjustmentType === 'subtract' ? 0 : hoursAdjustmentType === 'set' ? 0 : 0"
            :max="1000"
            style="width: 100%"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            1节课 = 1.0小时
          </div>
        </el-form-item>
        <el-form-item label="备注" v-if="hoursAdjustmentType !== 'set'">
          <el-input 
            v-model="hoursAdjustmentRemark" 
            type="textarea" 
            :rows="2" 
            placeholder="请填写调整原因（可选）" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editHoursDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitHoursAdjustment" :loading="savingHours">
          {{ getHoursSubmitText() }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加单词集对话框 -->
    <el-dialog 
      v-model="addWordSetDialogVisible" 
      title="添加单词集"
      width="500px"
    >
      <el-form :model="wordSetForm" label-width="100px">
        <el-form-item label="单词集名称" required>
          <el-input v-model="wordSetForm.name" placeholder="请输入单词集名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="wordSetForm.description" type="textarea" placeholder="可选" />
        </el-form-item>
        <el-form-item label="单词列表" required>
          <el-input 
            v-model="wordSetForm.wordsText" 
            type="textarea" 
            :rows="10"
            placeholder="请输入单词列表，格式：英文单词 中文意思（每行一个）&#10;例如：&#10;apple 苹果&#10;banana 香蕉"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addWordSetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddWordSet">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加课程对话框 -->
    <el-dialog
      v-model="addScheduleDialogVisible"
      title="添加课程"
      width="620px"
      :close-on-click-modal="false"
    >
      <el-form :model="scheduleForm" label-width="100px">
        <el-form-item label="选择学生" required>
          <el-select v-model="scheduleForm.studentId" placeholder="请选择学生" style="width: 100%">
            <el-option
              v-for="student in teacherStudents"
              :key="student.id"
              :label="student.name"
              :value="student.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item v-if="scheduleForm.type !== 'listening'" label="选择单词集" required>
          <el-select v-model="scheduleForm.wordSet" placeholder="请选择单词集" style="width: 100%">
            <el-option
              v-for="set in teacherWordSets"
              :key="set.name"
              :label="set.name"
              :value="set.name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="课程类型" required>
          <el-radio-group v-model="scheduleForm.type" @change="onCourseTypeChange">
            <el-radio value="learning">单词课</el-radio>
            <el-radio value="review">抗遗忘</el-radio>
            <el-radio value="reading">阅读课</el-radio>
            <el-radio value="listening">听力课</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- ── 阅读课专属配置 ────────────────────── -->
        <template v-if="scheduleForm.type === 'reading'">
          <el-form-item label="选词数量" required>
            <el-select v-model="readingConfig.wordsCount" style="width: 160px" @change="onWordsCountChange">
              <el-option label="5个单词" :value="5" />
              <el-option label="10个单词" :value="10" />
              <el-option label="15个单词" :value="15" />
              <el-option label="20个单词" :value="20" />
              <el-option label="自定义" :value="0" />
            </el-select>
            <el-input-number
              v-if="readingConfig.wordsCount === 0"
              v-model="readingConfig.customCount"
              :min="1"
              :max="readingConfig.learnedWords.length"
              style="width: 120px; margin-left: 10px"
            />
            <span style="color: #909399; font-size: 12px; margin-left: 10px">
              可用已学单词：{{ readingConfig.learnedWords.length }} 个
            </span>
          </el-form-item>

          <el-form-item label="选词方式" required>
            <el-radio-group v-model="readingConfig.wordSelectMode">
              <el-radio value="random">随机选取（格子1-7）</el-radio>
              <el-radio value="search">搜索选取</el-radio>
              <el-radio value="manual">完全自定义</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="readingConfig.wordSelectMode === 'search'" label="搜索单词">
            <div style="width: 100%">
              <el-input
                v-model="readingConfig.searchKeyword"
                placeholder="输入字母实时搜索已学单词..."
                clearable
                style="margin-bottom: 8px"
              />
              <div class="search-results" v-if="readingConfig.searchKeyword">
                <el-tag
                  v-for="word in filteredLearnedWords"
                  :key="word.id"
                  class="search-word-tag"
                  @click="addSearchWord(word)"
                  style="cursor: pointer; margin: 3px"
                >{{ word.english }}</el-tag>
                <span v-if="filteredLearnedWords.length === 0" style="color: #909399; font-size: 13px">无匹配单词</span>
              </div>
              <div v-if="readingConfig.selectedWords.length > 0" style="margin-top: 8px">
                <div style="font-size: 13px; color: #606266; margin-bottom: 4px">
                  已选 {{ readingConfig.selectedWords.length }} 个：
                </div>
                <el-tag
                  v-for="(word, idx) in readingConfig.selectedWords"
                  :key="idx"
                  closable type="success"
                  @close="removeSelectedWord(idx)"
                  style="margin: 3px"
                >{{ word.english }}</el-tag>
              </div>
            </div>
          </el-form-item>

          <el-form-item v-if="readingConfig.wordSelectMode === 'manual'" label="输入单词">
            <div style="width: 100%">
              <div style="display: flex; gap: 8px; margin-bottom: 8px">
                <el-input v-model="readingConfig.manualInput.english" placeholder="英文" style="flex: 1" />
                <el-input v-model="readingConfig.manualInput.chinese" placeholder="中文释义" style="flex: 1" />
                <el-button type="primary" @click="addManualWord">添加</el-button>
              </div>
              <div v-if="readingConfig.selectedWords.length > 0">
                <el-tag
                  v-for="(word, idx) in readingConfig.selectedWords"
                  :key="idx"
                  closable type="success"
                  @close="removeSelectedWord(idx)"
                  style="margin: 3px"
                >{{ word.english }}</el-tag>
              </div>
            </div>
          </el-form-item>

          <el-form-item label=" ">
            <el-button
              type="primary"
              :loading="readingConfig.generating"
              :disabled="!canGenerateArticle"
              @click="generateArticle"
            >
              {{ readingConfig.generating ? '生成中...' : '生成文章' }}
            </el-button>
            <span v-if="readingConfig.article" style="color: #67c23a; margin-left: 12px; font-size: 13px">
              ✓ 已生成（{{ readingConfig.wordCount }} 词）
              <el-button link type="primary" @click="regenerateArticle" style="margin-left: 8px">重新生成</el-button>
            </span>
          </el-form-item>

          <el-form-item v-if="readingConfig.article" label="文章预览">
            <div style="width: 100%">

              <!-- 按段显示：英文 + 中文翻译 -->
              <div
                v-for="(para, pIdx) in articleParagraphs"
                :key="pIdx"
                class="preview-paragraph"
              >
                <!-- 英文段落 -->
                <div v-if="!readingConfig.editing" class="preview-en" v-html="highlightParagraph(para)" />
                <el-input
                  v-else
                  v-model="editableParagraphs[pIdx]"
                  type="textarea"
                  :autosize="{ minRows: 2 }"
                  style="width: 100%; margin-bottom: 4px"
                  @input="onParagraphEdit"
                />

                <!-- 中文翻译：点击标题折叠/展开，展开时可编辑 -->
                <div
                  class="preview-zh-header"
                  @click="toggleTranslationCollapse(pIdx)"
                >
                  <span class="zh-toggle-icon">{{ collapsedTranslations[pIdx] ? '▶' : '▼' }}</span>
                  <span class="zh-toggle-label">译文</span>
                </div>
                <div v-show="!collapsedTranslations[pIdx]">
                  <el-input
                    v-model="readingConfig.translation[pIdx]"
                    type="textarea"
                    :autosize="{ minRows: 1 }"
                    placeholder="中文翻译（可编辑）"
                    class="preview-zh-input"
                    resize="none"
                  />
                </div>
              </div>

              <!-- 操作栏 -->
              <div style="margin-top: 10px; display: flex; gap: 8px; align-items: center">
                <el-button size="small" @click="toggleArticleEdit">
                  {{ readingConfig.editing ? '完成编辑' : '编辑英文' }}
                </el-button>
                <span style="color: #909399; font-size: 12px">Word count: {{ readingConfig.wordCount }}</span>
                <span v-if="!isWordCountInRange" style="color: #f56c6c; font-size: 12px">
                  ⚠ 建议范围：{{ wordCountRange[0] }}-{{ wordCountRange[1] }} 词
                </span>
              </div>
            </div>
          </el-form-item>
        </template>
        <!-- ── 阅读课配置结束 ────────────────────── -->

        <!-- ── 听力课专属配置 ────────────────────── -->
        <template v-if="scheduleForm.type === 'listening'">
          <el-form-item label="材料标题">
            <el-input v-model="listeningConfig.title" placeholder="可选，如：餐厅推荐对话" style="width: 100%" />
          </el-form-item>

          <el-form-item label="原文录入" required>
            <div style="width: 100%">
              <el-radio-group v-model="listeningConfig.inputMode" style="margin-bottom: 12px">
                <el-radio value="paste">粘贴文本</el-radio>
                <el-radio value="ocr">截图识别</el-radio>
              </el-radio-group>

              <div v-if="listeningConfig.inputMode === 'ocr'" style="margin-bottom: 12px">
                <el-upload
                  drag
                  :auto-upload="false"
                  :show-file-list="false"
                  accept="image/*"
                  :on-change="handleOcrImageChange"
                  class="upload-drag-area"
                >
                  <el-icon v-if="!listeningConfig.ocrUploading" class="upload-drag-icon"><Upload /></el-icon>
                  <el-icon v-else class="upload-drag-icon is-loading"><Loading /></el-icon>
                  <div class="el-upload__text">
                    {{ listeningConfig.ocrUploading ? '识别中...' : '将截图拖到此处，或点击上传' }}
                  </div>
                </el-upload>
                <span style="color: #909399; font-size: 12px">可连续上传多张，识别结果会追加到下方文本框</span>
              </div>

              <el-input
                v-model="listeningConfig.articleText"
                type="textarea"
                :rows="8"
                placeholder="原文内容，用空行分隔段落，可随时手动编辑"
                style="width: 100%"
              />
            </div>
          </el-form-item>

          <el-form-item label="段落翻译">
            <div style="width: 100%">
              <el-button
                size="small"
                :loading="listeningConfig.translating"
                :disabled="!listeningParagraphs.length"
                @click="translateListeningArticle"
              >
                {{ listeningConfig.translating ? '翻译中...' : 'AI 翻译' }}
              </el-button>
              <span style="color: #909399; font-size: 12px; margin-left: 8px">如果原文自带翻译，可直接在下方填写，不必点击此按钮</span>

              <div class="translation-scroll-box">
                <div
                  v-for="(para, pIdx) in listeningParagraphs"
                  :key="pIdx"
                  class="translation-para-item"
                >
                  <div class="translation-para-en">{{ para }}</div>
                  <el-input
                    v-model="listeningConfig.translation[pIdx]"
                    type="textarea"
                    :autosize="{ minRows: 1, maxRows: 4 }"
                    placeholder="中文翻译（可编辑）"
                    resize="none"
                  />
                </div>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="音频文件" required>
            <div style="width: 100%">
              <el-upload
                drag
                :auto-upload="false"
                :show-file-list="false"
                accept="audio/mp3,audio/wav,audio/ogg,audio/mp4,audio/x-m4a,.mp3,.wav,.ogg,.m4a"
                :on-change="handleAudioFileChange"
                class="upload-drag-area"
              >
                <el-icon v-if="!listeningConfig.audioUploading" class="upload-drag-icon"><Upload /></el-icon>
                <el-icon v-else class="upload-drag-icon is-loading"><Loading /></el-icon>
                <div class="el-upload__text">
                  {{ listeningConfig.audioUploading ? '上传中...' : '将音频文件拖到此处，或点击上传' }}
                </div>
                <div class="el-upload__tip">支持 mp3 / wav / ogg / m4a 格式</div>
              </el-upload>
              <span v-if="listeningConfig.tempAudioId" style="color: #67c23a; font-size: 13px">
                ✓ 已上传（{{ listeningConfig.audioDuration.toFixed(1) }}秒）
              </span>
            </div>
          </el-form-item>

          <el-form-item label=" ">
            <el-button
              type="primary"
              :loading="listeningConfig.aligning"
              :disabled="!canAlignTimestamps"
              @click="doAlignTimestamps"
            >
              {{ listeningConfig.aligning ? '识别中...' : '自动对齐时间戳' }}
            </el-button>
          </el-form-item>

          <el-form-item v-if="listeningConfig.alignmentPreview.length > 0" label="时间戳确认">
            <div style="width: 100%">
              <TimelineEditor
                v-model="listeningConfig.alignmentPreview"
                :audio-duration="listeningConfig.audioDuration"
                @preview="previewSegment"
              />
              <audio ref="previewAudioEl" :src="previewAudioSrc" style="display: none" />
              <el-checkbox v-model="listeningConfig.alignmentConfirmed" style="margin-top: 10px">
                我已核对以上时间戳，确认无误
              </el-checkbox>
            </div>
          </el-form-item>
        </template>
        <!-- ── 听力课配置结束 ────────────────────── -->

        <el-form-item label="课程时长">
          <el-input-number
            v-model="scheduleForm.duration"
            :min="15"
            :max="120"
            :step="15"
            style="width: 100%"
          />
          <span style="color: #999; font-size: 12px; margin-left: 8px;">分钟</span>
        </el-form-item>

        <el-form-item label="上课日期" required>
          <el-date-picker
            v-model="scheduleForm.date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="上课时间" required>
          <el-select
            v-model="scheduleForm.time"
            placeholder="选择时间"
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option
              v-for="timeSlot in timeSlots"
              :key="timeSlot"
              :label="timeSlot"
              :value="timeSlot"
            />
          </el-select>
          <div class="form-help">可选择预设时间或输入自定义时间（如：14:15）</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addScheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddSchedule">添加课程</el-button>
      </template>
    </el-dialog>

    <!-- Excel导入对话框 -->
    <el-dialog 
      v-model="importWordsDialogVisible" 
      title="导入Excel单词"
      width="800px"
    >
      <div class="import-content">
        <el-alert
          title="导入说明"
          description="Excel文件第一列必须是英文，第二列必须是中文。支持多个Sheet，每个Sheet会被识别为一个单词集。"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />
        
        <el-form label-width="100px">
          <el-form-item label="选择文件" required>
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls"
              :on-change="handleFileChange"
              :file-list="fileList"
              :before-remove="handleFileRemove"
            >
              <el-button type="primary">
                <el-icon><Upload /></el-icon>
                选择Excel文件
              </el-button>
              <template #tip>
                <div class="el-upload__tip">
                  只能上传xlsx/xls文件，且不超过10MB
                </div>
              </template>
            </el-upload>
          </el-form-item>
          
          <!-- 显示解析结果 -->
          <div v-if="excelSheets.length > 0" class="sheets-preview">
            <h4>检测到的Sheet：</h4>
            <div class="sheets-list">
              <el-card 
                v-for="(sheet, index) in excelSheets" 
                :key="index"
                style="margin-bottom: 15px"
              >
                <div class="sheet-header">
                  <div class="sheet-info">
                    <h5>{{ sheet.name }}</h5>
                    <span class="word-count-badge">{{ sheet.wordCount }} 个单词</span>
                  </div>
                  <div class="sheet-actions">
                    <el-input 
                      v-model="sheet.customName" 
                      placeholder="自定义单词集名称"
                      style="width: 250px; margin-right: 10px"
                    />
                    <el-checkbox v-model="sheet.selected">导入</el-checkbox>
                  </div>
                </div>
                
                <!-- 预览前几个单词 -->
                <div class="word-preview">
                  <div 
                    v-for="(word, wordIndex) in sheet.preview" 
                    :key="wordIndex"
                    class="preview-word"
                  >
                    <span class="english">{{ word.english }}</span>
                    <span class="chinese">{{ word.chinese }}</span>
                  </div>
                  <div v-if="sheet.wordCount > 3" class="more-words">
                    还有 {{ sheet.wordCount - 3 }} 个单词...
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="importWordsDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="importWordsFromExcel" 
          :loading="importing"
          :disabled="!hasSelectedSheets"
        >
          开始导入 ({{ selectedSheetsCount }} 个Sheet)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Plus, Avatar, ArrowDown, Upload, Setting, Download, Delete, Loading } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { useAuthStore } from '@/stores/auth'
import { useStudentsStore } from '@/stores/students'
import { useWordsStore } from '@/stores/words'
import { useScheduleStore } from '@/stores/schedule'
import { useReadingStore, type WordItem } from '@/stores/reading'
import { useListeningStore } from '@/stores/listening'
import TimelineEditor from '@/components/TimelineEditor.vue'
import tutorDB from '@/utils/localDatabase'
import type { User } from '@/stores/auth'
import type { Student } from '@/stores/students'
import type { WordSet } from '@/stores/words'
import type { Schedule } from '@/stores/schedule'

const router = useRouter()
const authStore = useAuthStore()
const studentsStore = useStudentsStore()
const wordsStore = useWordsStore()
const scheduleStore = useScheduleStore()
const readingStore = useReadingStore()
const listeningStore = useListeningStore()

// 课程类型 -> 标签文字/颜色映射（与Dashboard.vue/TeacherHome.vue保持一致）
const courseTypeLabel = (type: string): string => {
  const map: Record<string, string> = {
    review: '抗遗忘',
    reading: '阅读课',
    listening: '听力课',
    learning: '单词学习'
  }
  return map[type] || '单词学习'
}

const courseTypeTagType = (type: string): string => {
  const map: Record<string, string> = {
    review: 'warning',
    reading: 'primary',
    listening: 'info',
    learning: 'success'
  }
  return map[type] || 'success'
}

// 标签页状态
const activeTab = ref('users')
const activeDataTab = ref('students')

// 教师数据管理状态
const selectedTeacherId = ref('')
const selectedWordSet = ref('')

// 教师数据
const teacherStudents = ref<Student[]>([])
const teacherWordSets = ref<WordSet[]>([])
const teacherSchedules = ref<Schedule[]>([])

// 计算属性
const teachers = computed(() => {
  // 只显示teacher角色的用户，排除管理员
  return users.value.filter(user => user.role === 'teacher')
})

const hasSelectedSheets = computed(() => {
  return excelSheets.value.some(sheet => sheet.selected)
})

const selectedSheetsCount = computed(() => {
  return excelSheets.value.filter(sheet => sheet.selected).length
})

const groupedTeacherSchedules = computed(() => {
  const groups: { date: string, schedules: Schedule[] }[] = []
  const schedulesByDate: { [key: string]: Schedule[] } = {}

  // 获取今天的日期（本地时区）
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  const todayStr = `${year}-${month}-${day}`

  // 只包含今天及未来的课程
  teacherSchedules.value.forEach(schedule => {
    if (schedule.date >= todayStr) {
      if (!schedulesByDate[schedule.date]) {
        schedulesByDate[schedule.date] = []
      }
      schedulesByDate[schedule.date].push(schedule)
    }
  })

  Object.keys(schedulesByDate)
    .sort()
    .forEach(date => {
      groups.push({
        date,
        schedules: schedulesByDate[date].sort((a, b) => a.time.localeCompare(b.time))
      })
    })

  return groups
})

// 表单引用
const userFormRef = ref<InstanceType<typeof ElForm>>()
const editFormRef = ref<InstanceType<typeof ElForm>>()
const passwordFormRef = ref<InstanceType<typeof ElForm>>()

// 用户列表
const users = ref<User[]>([])

// 对话框状态
const addUserDialogVisible = ref(false)
const editUserDialogVisible = ref(false)
const resetPasswordDialogVisible = ref(false)
const submitting = ref(false)

// 添加用户表单
const userForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  displayName: '',
  role: 'teacher',
  email: ''
})

// 编辑用户表单
const editForm = reactive({
  id: '',
  username: '',
  displayName: '',
  role: 'teacher',
  email: ''
})

// 重置密码表单
const passwordForm = reactive({
  userId: '',
  newPassword: '',
  confirmPassword: ''
})

// 表单验证规则
const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== userForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  displayName: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const editRules = {
  displayName: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const passwordRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 方法
const loadUsers = async () => {
  users.value = await authStore.getAllUsers()
}

const formatDate = (dateString: string) => {
  // 处理日期字符串，避免时区转换问题
  // 如果是纯日期格式（YYYY-MM-DD），直接格式化
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    const [year, month, day] = dateString.split('-')
    return `${year}年${month}月${day}日`
  }

  // 如果包含时间，使用Date对象处理
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'dashboard') {
    router.push('/')
  }
}

const showAddUserDialog = () => {
  Object.assign(userForm, {
    username: '',
    password: '',
    confirmPassword: '',
    displayName: '',
    role: 'teacher',
    email: ''
  })
  addUserDialogVisible.value = true
}

const submitAddUser = async () => {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    submitting.value = true
    
    const result = await authStore.registerUser({
      username: userForm.username,
      password: userForm.password,
      display_name: userForm.displayName,
      role: userForm.role as 'admin' | 'teacher',
      email: userForm.email || undefined
    })
    
    if (result.success) {
      ElMessage.success(result.message)
      addUserDialogVisible.value = false
      await loadUsers()
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('Add user validation failed:', error)
  } finally {
    submitting.value = false
  }
}

const editUser = (user: User) => {
  Object.assign(editForm, {
    id: user.id,
    username: user.username,
    displayName: user.display_name,
    role: user.role,
    email: user.email || ''
  })
  editUserDialogVisible.value = true
}

const submitEditUser = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    submitting.value = true
    
    const result = await authStore.updateUser(editForm.id, {
      display_name: editForm.displayName,
      role: editForm.role as 'admin' | 'teacher',
      email: editForm.email || undefined
    })
    
    if (result.success) {
      ElMessage.success(result.message)
      editUserDialogVisible.value = false
      loadUsers()
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('Edit user validation failed:', error)
  } finally {
    submitting.value = false
  }
}

const resetPassword = (user: User) => {
  passwordForm.userId = user.id
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  resetPasswordDialogVisible.value = true
}

const submitResetPassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    submitting.value = true
    
    const result = await authStore.changePassword(
      passwordForm.userId,
      '', // 管理员重置密码不需要旧密码
      passwordForm.newPassword
    )
    
    if (result.success) {
      ElMessage.success(result.message)
      resetPasswordDialogVisible.value = false
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('Reset password validation failed:', error)
  } finally {
    submitting.value = false
  }
}

const deleteUser = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.display_name}" (${user.username}) 吗？\n\n删除后该用户的所有数据将被永久清除！`,
      '确认删除用户',
      {
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )
    
    const result = await authStore.deleteUser(user.id)
    if (result.success) {
      ElMessage.success(result.message)
      loadUsers()
      // 如果删除的是当前选中的教师，清空选择
      if (selectedTeacherId.value === user.id) {
        selectedTeacherId.value = ''
        clearTeacherData()
      }
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消删除
  }
}

// 教师数据管理方法
const loadTeacherData = async () => {
  if (!selectedTeacherId.value) {
    clearTeacherData()
    return
  }

  try {
    // 加载教师的学生数据 - 使用API
    await studentsStore.fetchStudents(selectedTeacherId.value)
    teacherStudents.value = studentsStore.students

    // 加载教师的单词数据 - 使用全局单词集
    await wordsStore.fetchWordSets()
    teacherWordSets.value = wordsStore.wordSets

    // 加载教师的日程数据 - 使用API
    await scheduleStore.fetchSchedules(selectedTeacherId.value)
    teacherSchedules.value = scheduleStore.schedules
  } catch (error) {
    console.error('加载教师数据失败:', error)
    ElMessage.error('加载教师数据失败')
  }
}

const clearTeacherData = () => {
  teacherStudents.value = []
  teacherWordSets.value = []
  teacherSchedules.value = []
  selectedWordSet.value = ''
}

const getSelectedTeacherName = () => {
  const teacher = teachers.value.find(t => t.id === selectedTeacherId.value)
  return teacher ? teacher.display_name : ''
}

const selectWordSet = async (wordSetName: string) => {
  selectedWordSet.value = wordSetName
  // 加载该单词集的单词
  await wordsStore.fetchWords(wordSetName)
}

const getCurrentWords = () => {
  // 从wordsStore获取当前单词集的单词
  return wordsStore.words || []
}

// 学生管理状态
const addStudentDialogVisible = ref(false)
const editStudentDialogVisible = ref(false)
const editHoursDialogVisible = ref(false)
const savingHours = ref(false)

const studentForm = reactive({
  name: '',
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  remainingHours: 0
})

const editStudentForm = reactive({
  id: 0,
  name: '',
  username: '',
  email: '',
  hasAccount: false
})

// 课时编辑状态
const editHoursForm = reactive({
  id: 0,
  name: '',
  currentHours: 0
})

const hoursAdjustmentType = ref('set') // 'set', 'add', 'subtract'
const hoursAdjustmentValue = ref(0)
const hoursAdjustmentRemark = ref('')

// 单词管理状态
const addWordSetDialogVisible = ref(false)

const wordSetForm = reactive({
  name: '',
  description: '',
  wordsText: ''
})

// 日程管理状态
const addScheduleDialogVisible = ref(false)

// Excel导入状态
const importWordsDialogVisible = ref(false)
const importing = ref(false)
const excelSheets = ref<ExcelSheet[]>([])
const fileList = ref([])
const selectedFile = ref<File | null>(null)

// Excel Sheet 接口定义
interface ExcelSheet {
  name: string
  customName: string
  selected: boolean
  wordCount: number
  preview: Array<{ english: string; chinese: string }>
  data: Array<{ english: string; chinese: string }>
}

const scheduleForm = reactive({
  studentId: '',
  wordSet: '',
  type: 'learning',
  date: '',
  time: '',
  duration: 60,
  classType: 'big'
})

// ── 阅读课专属状态 ────────────────────────────────────────
const readingConfig = reactive({
  wordsCount: 10,
  customCount: 10,
  wordSelectMode: 'random' as 'random' | 'search' | 'manual',
  learnedWords: [] as Array<{ id: number; english: string; chinese: string; stage: number; index: number }>,
  searchKeyword: '',
  selectedWords: [] as WordItem[],
  manualInput: { english: '', chinese: '' },
  generating: false,
  article: '',
  translation: [] as string[],
  wordCount: 0,
  editing: false,
  savedArticleId: null as number | null,
})

// ── 听力课专属状态 ────────────────────────────────────────
const listeningConfig = reactive({
  title: '',
  inputMode: 'paste' as 'paste' | 'ocr',
  articleText: '',
  translation: [] as string[],
  translating: false,
  ocrUploading: false,
  audioUploading: false,
  tempAudioId: '',
  audioOriginalFilename: '',
  audioMimetype: '',
  audioDuration: 0,
  aligning: false,
  alignmentPreview: [] as Array<{ index: number; text: string; start: number; end: number; match_score?: number }>,
  alignmentConfirmed: false,
  savedArticleId: null as number | null,
})

const previewAudioEl = ref<HTMLAudioElement>()
const previewAudioSrc = ref('')

// 听力课按单个换行分段（不是双换行/空行），换行本身决定原文翻译对应关系和时间戳切分
const listeningParagraphs = computed(() => {
  return listeningConfig.articleText
    .split(/\n/)
    .map((p: string) => p.trim())
    .filter((p: string) => p.length > 0)
})

const canAlignTimestamps = computed(() => {
  return listeningParagraphs.value.length > 0 && !!listeningConfig.tempAudioId
})

const finalReadingWordsCount = computed(() =>
  readingConfig.wordsCount === 0 ? readingConfig.customCount : readingConfig.wordsCount
)

const wordCountRange = computed((): [number, number] => {
  const n = finalReadingWordsCount.value
  if (n <= 5) return [100, 200]
  if (n <= 10) return [200, 350]
  return [300, 500]
})

const isWordCountInRange = computed(() => {
  const [min, max] = wordCountRange.value
  return readingConfig.wordCount >= min && readingConfig.wordCount <= max
})

const filteredLearnedWords = computed(() => {
  const kw = readingConfig.searchKeyword.toLowerCase()
  if (!kw) return []
  const selectedEnglish = new Set(readingConfig.selectedWords.map(w => w.english.toLowerCase()))
  return readingConfig.learnedWords.filter(
    w => w.english.toLowerCase().includes(kw) && !selectedEnglish.has(w.english.toLowerCase())
  )
})

// 按段落拆分文章（只读）
const articleParagraphs = computed(() => {
  if (!readingConfig.article) return []
  return readingConfig.article.split(/\n\n+/).map((p: string) => p.trim()).filter((p: string) => p.length > 0)
})

// 编辑时每段独立的 ref
const editableParagraphs = ref<string[]>([])

// 每段译文的折叠状态（true=折叠），用 reactive 保证响应式
const collapsedTranslations = reactive<Record<number, boolean>>({})

const toggleTranslationCollapse = (pIdx: number) => {
  collapsedTranslations[pIdx] = !collapsedTranslations[pIdx]
}

// 单段高亮 - 直接用 selectedWords（生成后已固定，不再随机）
const highlightParagraph = (para: string) => {
  let text = para.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  readingConfig.selectedWords.forEach((w: WordItem) => {
    const escaped = w.english.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`\\b(${escaped})\\b`, 'gi')
    text = text.replace(regex, '<mark>$1</mark>')
  })
  return `<span style="line-height:1.9">${text}</span>`
}

// 切换英文编辑模式
const toggleArticleEdit = () => {
  if (readingConfig.editing) {
    // 完成编辑：把各段合并回 article
    readingConfig.article = editableParagraphs.value.join('\n\n')
    onArticleEdit()
  } else {
    // 进入编辑：初始化可编辑段落
    editableParagraphs.value = articleParagraphs.value.slice()
  }
  readingConfig.editing = !readingConfig.editing
}

// 编辑某段英文时实时更新 wordCount
const onParagraphEdit = () => {
  const merged = editableParagraphs.value.join('\n\n')
  const words = merged.match(/\b[a-zA-Z']+\b/g) || []
  readingConfig.wordCount = words.length
}

const canGenerateArticle = computed(() => {
  if (!scheduleForm.studentId || !scheduleForm.wordSet) return false
  if (readingConfig.wordSelectMode === 'random') {
    return readingConfig.learnedWords.length >= finalReadingWordsCount.value
  }
  return readingConfig.selectedWords.length > 0
})

function getArticleWords(): WordItem[] {
  if (readingConfig.wordSelectMode === 'random') {
    const shuffled = [...readingConfig.learnedWords].sort(() => Math.random() - 0.5)
    return shuffled.slice(0, finalReadingWordsCount.value).map(w => ({ english: w.english, chinese: w.chinese }))
  }
  return readingConfig.selectedWords
}

const onCourseTypeChange = async () => {
  if (scheduleForm.type === 'reading') {
    await loadLearnedWordsForReading()
  }
}

// ── 听力课方法 ────────────────────────────────────────
const handleOcrImageChange = async (file: any) => {
  if (!file.raw) return
  listeningConfig.ocrUploading = true
  try {
    const result = await listeningStore.ocrImage(file.raw)
    const recognized = result.recognized_text?.trim()
    if (recognized) {
      listeningConfig.articleText = listeningConfig.articleText
        ? `${listeningConfig.articleText}\n\n${recognized}`
        : recognized
      ElMessage.success('识别成功，已追加到文本框')
    } else {
      ElMessage.warning('未识别到文字')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '识别失败，请重试')
  } finally {
    listeningConfig.ocrUploading = false
  }
}

const translateListeningArticle = async () => {
  if (!listeningParagraphs.value.length) return
  listeningConfig.translating = true
  try {
    const result = await listeningStore.translateArticle(listeningConfig.articleText)
    listeningConfig.translation = result.translation
    ElMessage.success('翻译完成')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '翻译失败，请重试')
  } finally {
    listeningConfig.translating = false
  }
}

const handleAudioFileChange = async (file: any) => {
  if (!file.raw) return
  listeningConfig.audioUploading = true
  try {
    const result = await listeningStore.uploadAudio(file.raw)
    listeningConfig.tempAudioId = result.temp_audio_id
    listeningConfig.audioDuration = result.duration_seconds
    listeningConfig.audioOriginalFilename = result.original_filename
    listeningConfig.audioMimetype = file.raw.type || 'audio/mpeg'
    // 本地生成blob URL用于排课预览阶段的试听，不经过后端（此时文章还未保存，没有article_id）
    if (previewAudioSrc.value) URL.revokeObjectURL(previewAudioSrc.value)
    previewAudioSrc.value = URL.createObjectURL(file.raw)
    // 音频上传成功后立即生成空白时间戳表，让"时间戳确认"区域直接可用（无需先点自动对齐）
    initBlankAlignmentPreview()
    ElMessage.success('音频上传成功，可点击"自动对齐时间戳"或直接手动填写')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '音频上传失败')
  } finally {
    listeningConfig.audioUploading = false
  }
}

// 生成一份起止时间都为0的空白时间戳表，供手动填写；如果原文有更新会保留已有的手动输入
const initBlankAlignmentPreview = () => {
  listeningConfig.alignmentPreview = listeningParagraphs.value.map((text, index) => ({
    index,
    text,
    start: 0,
    end: 0,
    match_score: undefined,
  }))
  listeningConfig.alignmentConfirmed = false
}

// 音频上传后如果又编辑了原文（增删段落），同步时间戳表的段落数量，
// 已经手动填过的时间戳按段落文字是否相同尽量保留，避免白填一遍
watch(listeningParagraphs, (newParas) => {
  if (!listeningConfig.tempAudioId || listeningConfig.alignmentPreview.length === 0) return

  const oldByText = new Map(listeningConfig.alignmentPreview.map(p => [p.text, p]))
  const samePlainList =
    newParas.length === listeningConfig.alignmentPreview.length &&
    newParas.every((text, i) => text === listeningConfig.alignmentPreview[i].text)
  if (samePlainList) return // 内容完全没变，不用重建

  listeningConfig.alignmentPreview = newParas.map((text, index) => {
    const existing = oldByText.get(text)
    return existing
      ? { ...existing, index }
      : { index, text, start: 0, end: 0, match_score: undefined }
  })
  listeningConfig.alignmentConfirmed = false
})

const doAlignTimestamps = async () => {
  listeningConfig.aligning = true
  try {
    const result = await listeningStore.alignTimestamps(listeningConfig.tempAudioId, listeningConfig.articleText)
    listeningConfig.alignmentPreview = result.paragraphs
    listeningConfig.audioDuration = result.audio_duration_seconds
    listeningConfig.alignmentConfirmed = false
    ElMessage.success('自动对齐完成，请核对每段时间戳')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '自动对齐失败')
  } finally {
    listeningConfig.aligning = false
  }
}

// 试听某一段（用于排课预览阶段核对时间戳是否准确，直接用本地blob URL播放）
const previewSegment = (idx: number) => {
  const seg = listeningConfig.alignmentPreview[idx]
  const el = previewAudioEl.value
  if (!seg || !el || !previewAudioSrc.value) return
  el.currentTime = seg.start
  el.play()
  const onTimeUpdate = () => {
    if (el.currentTime >= seg.end) {
      el.pause()
      el.removeEventListener('timeupdate', onTimeUpdate)
    }
  }
  el.addEventListener('timeupdate', onTimeUpdate)
}

const resetListeningConfig = () => {
  Object.assign(listeningConfig, {
    title: '', inputMode: 'paste', articleText: '', translation: [],
    translating: false, ocrUploading: false, audioUploading: false,
    tempAudioId: '', audioOriginalFilename: '', audioMimetype: '',
    audioDuration: 0, aligning: false, alignmentPreview: [],
    alignmentConfirmed: false, savedArticleId: null,
  })
}

const loadLearnedWordsForReading = async () => {
  if (!scheduleForm.studentId || !scheduleForm.wordSet) return
  try {
    readingConfig.learnedWords = await readingStore.getLearnedWords(
      parseInt(scheduleForm.studentId), scheduleForm.wordSet
    )
  } catch { ElMessage.error('加载已学单词失败') }
}

watch(() => [scheduleForm.studentId, scheduleForm.wordSet], async () => {
  if (scheduleForm.type === 'reading' && scheduleForm.studentId && scheduleForm.wordSet) {
    await loadLearnedWordsForReading()
  }
})

const onWordsCountChange = () => {
  if (readingConfig.wordsCount === 0) {
    readingConfig.customCount = Math.min(10, readingConfig.learnedWords.length)
  }
}

const addSearchWord = (word: { english: string; chinese: string }) => {
  if (readingConfig.selectedWords.some(w => w.english === word.english)) return
  readingConfig.selectedWords.push({ english: word.english, chinese: word.chinese })
  readingConfig.searchKeyword = ''
}

const addManualWord = () => {
  const eng = readingConfig.manualInput.english.trim()
  const chn = readingConfig.manualInput.chinese.trim()
  if (!eng) { ElMessage.warning('请输入英文单词'); return }
  if (readingConfig.selectedWords.some(w => w.english.toLowerCase() === eng.toLowerCase())) {
    ElMessage.warning('该单词已添加'); return
  }
  readingConfig.selectedWords.push({ english: eng, chinese: chn || '—' })
  readingConfig.manualInput.english = ''
  readingConfig.manualInput.chinese = ''
}

const removeSelectedWord = (idx: number) => { readingConfig.selectedWords.splice(idx, 1) }

const generateArticle = async () => {
  if (readingConfig.wordSelectMode === 'random') {
    const need = finalReadingWordsCount.value
    const have = readingConfig.learnedWords.length
    if (have < need) {
      ElMessageBox.alert(
        `可用已学单词不足！\n需要：${need} 个\n可用：${have} 个\n\n请减少选词数量，或先完成更多单词学习。`,
        '单词不足', { confirmButtonText: '知道了', type: 'warning' }
      )
      return
    }
  }
  readingConfig.generating = true
  readingConfig.article = ''
  readingConfig.savedArticleId = null
  try {
    const wordsToUse = getArticleWords()
    const result = await readingStore.generateArticle(scheduleForm.wordSet, wordsToUse)
    readingConfig.article = result.article
    readingConfig.translation = result.translation || []
    readingConfig.wordCount = result.word_count
    editableParagraphs.value = result.article.split(/\n\n+/).map((p: string) => p.trim()).filter((p: string) => p.length > 0)
    if (readingConfig.wordSelectMode === 'random') readingConfig.selectedWords = wordsToUse
    ElMessage.success(`文章生成成功（${result.word_count} 词，${readingConfig.translation.length} 段翻译）`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '生成文章失败，请重试')
  } finally {
    readingConfig.generating = false
  }
}

const regenerateArticle = async () => { readingConfig.savedArticleId = null; await generateArticle() }

const onArticleEdit = () => {
  const words = readingConfig.article.match(/\b[a-zA-Z']+\b/g) || []
  readingConfig.wordCount = words.length
}

const resetReadingConfig = () => {
  Object.assign(readingConfig, {
    wordsCount: 10, customCount: 10, wordSelectMode: 'random',
    learnedWords: [], searchKeyword: '', selectedWords: [],
    manualInput: { english: '', chinese: '' },
    generating: false, article: '', translation: [], wordCount: 0, editing: false, savedArticleId: null
  })
  editableParagraphs.value = []
  Object.keys(collapsedTranslations).forEach(k => delete collapsedTranslations[k as any])
}
// ── 阅读课配置结束 ─────────────────────────────────────────

// 生成时间选项（6:00-22:00，每30分钟一个）
const timeSlots = computed(() => {
  const slots = []
  for (let hour = 6; hour <= 22; hour++) {
    slots.push(`${hour.toString().padStart(2, '0')}:00`)
    if (hour < 22) {
      slots.push(`${hour.toString().padStart(2, '0')}:30`)
    }
  }
  return slots
})

// 学生管理方法
const showAddStudentDialog = () => {
  if (!selectedTeacherId.value) {
    ElMessage.error('请先选择一个教师')
    return
  }

  Object.assign(studentForm, {
    name: '',
    username: '',
    password: '',
    confirmPassword: '',
    email: '',
    remainingHours: 0
  })
  addStudentDialogVisible.value = true
}

const submitAddStudent = async () => {
  if (!studentForm.name) {
    ElMessage.error('请输入学生姓名')
    return
  }

  if (!studentForm.username) {
    ElMessage.error('请输入登录用户名')
    return
  }

  if (!studentForm.password) {
    ElMessage.error('请输入登录密码')
    return
  }

  if (studentForm.password !== studentForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }

  submitting.value = true

  try {
    // 第一步：创建学生登录账号（User表，role=student）
    const userResult = await authStore.registerUser({
      username: studentForm.username,
      password: studentForm.password,
      display_name: studentForm.name,
      role: 'student',
      email: studentForm.email || undefined
    })

    if (!userResult.success) {
      ElMessage.error(`创建学生账号失败: ${userResult.message}`)
      return
    }

    // 获取创建的用户ID
    const createdUser = userResult.data
    if (!createdUser || !createdUser.id) {
      ElMessage.error('创建学生账号失败：未返回用户ID')
      return
    }

    // 第二步：创建学生教学记录（Student表）
    const studentResult = await studentsStore.addStudent({
      user_id: createdUser.id,  // 关联刚创建的用户账号
      name: studentForm.name,
      email: studentForm.email || undefined,
      remaining_hours: studentForm.remainingHours || 0,
      teacher_id: selectedTeacherId.value  // 指定所属教师
    })

    if (!studentResult.success) {
      ElMessage.error(`创建学生记录失败: ${studentResult.message}`)
      // 注意：这里学生账号已经创建了，但学生记录创建失败，需要手动处理
      return
    }

    ElMessage.success('学生添加成功')
    addStudentDialogVisible.value = false
    await loadTeacherData()
  } catch (error) {
    console.error('创建学生失败:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

const editStudent = (student: Student) => {
  Object.assign(editStudentForm, {
    id: student.id,
    name: student.name,
    username: student.username || '',
    email: student.email || '',
    hasAccount: student.hasAccount || false
  })
  editStudentDialogVisible.value = true
}

const submitEditStudent = async () => {
  if (!editStudentForm.name) {
    ElMessage.error('请输入学生姓名')
    return
  }

  try {
    const result = await studentsStore.updateStudent(editStudentForm.id, {
      name: editStudentForm.name,
      email: editStudentForm.email || undefined
    })

    if (result.success) {
      ElMessage.success(result.message)
      editStudentDialogVisible.value = false
      await loadTeacherData()
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('更新学生信息失败:', error)
    ElMessage.error('更新学生信息失败')
  }
}

// 课时管理相关函数
const editStudentHours = (student: Student) => {
  Object.assign(editHoursForm, {
    id: student.id,
    name: student.name,
    currentHours: student.remaining_hours || 0
  })
  hoursAdjustmentType.value = 'set'
  hoursAdjustmentValue.value = student.remaining_hours || 0
  hoursAdjustmentRemark.value = ''
  editHoursDialogVisible.value = true
}

const getHoursAdjustmentLabel = () => {
  switch (hoursAdjustmentType.value) {
    case 'set': return '设置课时'
    case 'add': return '增加课时'
    case 'subtract': return '扣除课时'
    default: return '调整课时'
  }
}

const getHoursSubmitText = () => {
  switch (hoursAdjustmentType.value) {
    case 'set': return '确认设置'
    case 'add': return '确认增加'
    case 'subtract': return '确认扣除'
    default: return '确认调整'
  }
}

const getHoursClass = (hours: number) => {
  if (!hours || hours <= 0) return 'hours-empty'
  if (hours <= 1) return 'hours-low'
  if (hours <= 5) return 'hours-medium'
  return 'hours-high'
}

const selectedTeacherName = computed(() => {
  const teacher = users.value.find(u => u.id === selectedTeacherId.value)
  return teacher?.display_name || ''
})

const submitHoursAdjustment = async () => {
  const value = hoursAdjustmentValue.value || 0

  if (value < 0) {
    ElMessage.error('调整数值不能为负数')
    return
  }

  savingHours.value = true

  try {
    let newHours = 0
    const currentHours = editHoursForm.currentHours || 0

    switch (hoursAdjustmentType.value) {
      case 'set':
        newHours = value
        break
      case 'add':
        newHours = currentHours + value
        break
      case 'subtract':
        newHours = Math.max(0, currentHours - value)
        break
      default:
        newHours = currentHours
    }

    const result = await studentsStore.updateStudent(editHoursForm.id, {
      remaining_hours: newHours
    })

    if (result.success) {
      await loadTeacherData()
      const actionText = hoursAdjustmentType.value === 'set' ? '设置' :
                        hoursAdjustmentType.value === 'add' ? '增加' : '扣除'
      ElMessage.success(`学生课时${actionText}成功：${editHoursForm.name} 现剩余 ${newHours.toFixed(1)}h`)
      editHoursDialogVisible.value = false
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('课时调整失败:', error)
    ElMessage.error('课时调整失败')
  } finally {
    savingHours.value = false
  }
}

const resetStudentPassword = async (student: Student) => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt(
      `为学生 ${student.name} 设置新密码`,
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPlaceholder: '请输入新密码',
        inputType: 'password'
      }
    )

    if (!newPassword) {
      ElMessage.warning('密码不能为空')
      return
    }

    // 通过username找到用户并重置密码
    const users = await authStore.getAllUsers()
    const user = users.find((u: any) => u.username === student.username)

    if (user) {
      const result = await authStore.changePassword(user.id, '', newPassword)
      if (result.success) {
        ElMessage.success('密码重置成功')
      } else {
        ElMessage.error(result.message)
      }
    } else {
      ElMessage.error('未找到对应的用户账号')
    }
  } catch {
    // 用户取消操作
  }
}

const deleteStudent = async (student: Student) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除学生 "${student.name}" 吗？这将同时删除其账号和所有学习数据。`,
      '确认删除',
      { type: 'warning' }
    )

    const result = await studentsStore.deleteStudent(student.id)

    if (result.success) {
      ElMessage.success(result.message)
      await loadTeacherData()
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消
  }
}

// 单词管理方法
const showAddWordSetDialog = () => {
  if (!selectedTeacherId.value) {
    ElMessage.error('请先选择一个教师')
    return
  }
  
  Object.assign(wordSetForm, {
    name: '',
    description: '',
    wordsText: ''
  })
  addWordSetDialogVisible.value = true
}

const submitAddWordSet = async () => {
  if (!wordSetForm.name || !wordSetForm.wordsText) {
    ElMessage.error('请输入单词集名称和单词列表')
    return
  }

  try {
    // 1. 创建单词集
    const createResult = await wordsStore.createWordSet({
      name: wordSetForm.name,
      is_global: true
    })

    if (!createResult.success) {
      ElMessage.error(createResult.message)
      return
    }

    // 2. 解析单词列表
    const words = wordSetForm.wordsText.trim().split('\n').map(line => {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 2) {
        return {
          english: parts[0],
          chinese: parts.slice(1).join(' ')
        }
      }
      return null
    }).filter(word => word !== null) as Array<{ english: string, chinese: string }>

    if (words.length === 0) {
      ElMessage.error('请输入有效的单词列表')
      return
    }

    // 3. 批量添加单词
    const addResult = await wordsStore.batchAddWords(wordSetForm.name, words)

    if (addResult.success) {
      ElMessage.success(`单词集添加成功，共 ${words.length} 个单词`)
      addWordSetDialogVisible.value = false
      await loadTeacherData()
    } else {
      ElMessage.error(addResult.message)
    }
  } catch (error) {
    console.error('添加单词集失败:', error)
    ElMessage.error('添加单词集失败')
  }
}

// Excel导入方法
const showImportWordsDialog = () => {
  if (!selectedTeacherId.value) {
    ElMessage.error('请先选择一个教师')
    return
  }
  
  fileList.value = []
  selectedFile.value = null
  excelSheets.value = []
  importWordsDialogVisible.value = true
}

const handleFileChange = async (file: any) => {
  selectedFile.value = file.raw
  
  try {
    const arrayBuffer = await file.raw.arrayBuffer()
    const workbook = XLSX.read(arrayBuffer)
    
    excelSheets.value = []
    
    // 解析每个Sheet
    workbook.SheetNames.forEach(sheetName => {
      const worksheet = workbook.Sheets[sheetName]
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      
      // 过滤空行并提取单词数据
      const wordData: Array<{ english: string; chinese: string }> = []
      
      for (let i = 0; i < jsonData.length; i++) {
        const row = jsonData[i] as any[]
        if (row && row.length >= 2 && row[0] && row[1]) {
          const english = String(row[0]).trim()
          const chinese = String(row[1]).trim()
          
          if (english && chinese) {
            wordData.push({ english, chinese })
          }
        }
      }
      
      if (wordData.length > 0) {
        excelSheets.value.push({
          name: sheetName,
          customName: sheetName,
          selected: true,
          wordCount: wordData.length,
          preview: wordData.slice(0, 3),
          data: wordData
        })
      }
    })
    
    if (excelSheets.value.length === 0) {
      ElMessage.error('Excel文件中没有找到有效的单词数据')
    } else {
      ElMessage.success(`成功解析 ${excelSheets.value.length} 个Sheet`)
    }
    
  } catch (error) {
    ElMessage.error('解析Excel文件失败，请检查文件格式')
    console.error('Excel解析错误:', error)
  }
}

const handleFileRemove = () => {
  selectedFile.value = null
  excelSheets.value = []
}

const importWordsFromExcel = async () => {
  if (!selectedFile.value) {
    ElMessage.error('请选择文件')
    return
  }

  importing.value = true

  try {
    const selectedSheets = excelSheets.value.filter(sheet => sheet.selected)

    if (selectedSheets.length === 0) {
      ElMessage.error('请至少选择一个Sheet导入')
      return
    }

    let totalWords = 0

    for (const sheet of selectedSheets) {
      const wordSetName = sheet.customName || sheet.name

      // 1. 创建单词集
      const createResult = await wordsStore.createWordSet({
        name: wordSetName,
        is_global: true
      })

      if (!createResult.success) {
        ElMessage.error(`创建单词集 "${wordSetName}" 失败: ${createResult.message}`)
        continue
      }

      // 2. 批量添加单词
      const addResult = await wordsStore.batchAddWords(wordSetName, sheet.data)

      if (addResult.success) {
        totalWords += sheet.data.length
      } else {
        ElMessage.error(`导入单词失败: ${addResult.message}`)
      }
    }

    ElMessage.success(`成功导入 ${totalWords} 个单词，来自 ${selectedSheets.length} 个Sheet`)
    importWordsDialogVisible.value = false
    await loadTeacherData()

  } catch (error) {
    ElMessage.error('导入失败')
    console.error('导入错误:', error)
  } finally {
    importing.value = false
  }
}

const deleteWordSet = async (wordSet: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除单词集 "${wordSet.name}" 吗？这将删除该单词集下的所有 ${wordSet.word_count || 0} 个单词。`,
      '确认删除单词集',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )

    const result = await wordsStore.deleteWordSet(wordSet.name)

    if (result.success) {
      // 如果删除的是当前选中的单词集，清空选择
      if (selectedWordSet.value === wordSet.name) {
        selectedWordSet.value = ''
      }

      ElMessage.success(result.message)
      await loadTeacherData()
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消删除
  }
}

const importWords = () => {
  showImportWordsDialog()
}

// 日程管理方法
const showAddScheduleDialog = () => {
  if (!selectedTeacherId.value) {
    ElMessage.error('请先选择一个教师')
    return
  }
  
  Object.assign(scheduleForm, {
    studentId: '',
    wordSet: '',
    type: 'learning',
    date: '',
    time: '',
    duration: 60,
    classType: 'big'
  })
  resetReadingConfig()
  resetListeningConfig()
  addScheduleDialogVisible.value = true
}

const updateScheduleDuration = () => {
  if (scheduleForm.classType === 'big') {
    scheduleForm.duration = 60
  } else if (scheduleForm.classType === 'small') {
    scheduleForm.duration = 30
  }
}

const submitAddSchedule = async () => {
  const isListening = scheduleForm.type === 'listening'

  if (!scheduleForm.studentId || (!isListening && !scheduleForm.wordSet) || !scheduleForm.date || !scheduleForm.time) {
    ElMessage.error('请填写完整的课程信息')
    return
  }

  if (isListening) {
    if (!listeningConfig.articleText.trim()) {
      ElMessage.error('请录入听力材料原文')
      return
    }
    if (!listeningConfig.tempAudioId) {
      ElMessage.error('请上传听力材料音频')
      return
    }
    if (listeningConfig.alignmentPreview.length > 0 && !listeningConfig.alignmentConfirmed) {
      ElMessage.error('请先核对并确认自动对齐的时间戳')
      return
    }
  }

  try {
// 修复时区问题：确保使用本地日期
      let dateStr
      if (scheduleForm.date instanceof Date) {
        // Date对象：格式化为YYYY-MM-DD（本地时间）
        const year = scheduleForm.date.getFullYear()
        const month = String(scheduleForm.date.getMonth() + 1).padStart(2, '0')
        const day = String(scheduleForm.date.getDate()).padStart(2, '0')
        dateStr = `${year}-${month}-${day}`
      } else {
        // 字符串：直接使用
        dateStr = scheduleForm.date
      }

    const result = await scheduleStore.addSchedule({
      student_id: parseInt(scheduleForm.studentId),
      date: dateStr,
      time: scheduleForm.time,
      word_set_name: isListening ? (listeningConfig.title || '听力课') : scheduleForm.wordSet,
      course_type: scheduleForm.type,
      duration: scheduleForm.duration,
      class_type: 'big',
      teacher_id: selectedTeacherId.value  // 管理员为指定教师创建课程
    })

    if (result.success) {
      // 阅读课：保存文章并绑定课程
      if (scheduleForm.type === 'reading' && readingConfig.article) {
        try {
          let articleId = readingConfig.savedArticleId
          if (!articleId) {
            const saved = await readingStore.saveArticle(
              scheduleForm.wordSet,
              readingConfig.selectedWords,
              readingConfig.article,
              readingConfig.translation,
              readingConfig.wordCount
            )
            articleId = saved.id
          }
          // 从 store 里取刚创建的课程（最后一条）
          const scheduleStore2 = useScheduleStore()
          const newSchedule = scheduleStore2.schedules[scheduleStore2.schedules.length - 1]
          if (newSchedule?.id) {
            await readingStore.bindArticleToSchedule(articleId, newSchedule.id)
          }
        } catch (e) {
          console.error('保存文章失败:', e)
        }
      }

      // 听力课：保存文章并绑定课程
      if (isListening) {
        try {
          let articleId = listeningConfig.savedArticleId
          if (!articleId) {
            const saved = await listeningStore.saveArticle({
              title: listeningConfig.title || undefined,
              articleContent: listeningConfig.articleText,
              translation: listeningConfig.translation,
              paragraphTimestamps: listeningConfig.alignmentPreview.map(p => ({
                index: p.index, start: p.start, end: p.end, match_score: p.match_score
              })),
              tempAudioId: listeningConfig.tempAudioId,
              audioOriginalFilename: listeningConfig.audioOriginalFilename,
              audioMimetype: listeningConfig.audioMimetype,
              audioDurationSeconds: listeningConfig.audioDuration,
            })
            articleId = saved.id
          }
          const scheduleStore2 = useScheduleStore()
          const newSchedule = scheduleStore2.schedules[scheduleStore2.schedules.length - 1]
          if (newSchedule?.id) {
            await listeningStore.bindArticleToSchedule(articleId, newSchedule.id)
          }
        } catch (e) {
          console.error('保存听力材料失败:', e)
        }
      }

      ElMessage.success(result.message)
      addScheduleDialogVisible.value = false
      await loadTeacherData()
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('添加课程失败:', error)
    ElMessage.error('添加课程失败')
  }
}

const editSchedule = (schedule: Schedule) => {
  ElMessage.info('编辑课程功能开发中...')
}

const deleteSchedule = async (schedule: Schedule) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除这个课程安排吗？`,
      '确认删除',
      { type: 'warning' }
    )

    const result = await scheduleStore.deleteSchedule(schedule.id)

    if (result.success) {
      ElMessage.success(result.message)
      await loadTeacherData()
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消
  }
}

const resetTimer = async (schedule: Schedule) => {
  try {
    await ElMessageBox.confirm(
      `确定要重置这个课程的计时器吗？\n重置后，教师下次点击学习/复习时会重新开始计时。`,
      '确认重置',
      { type: 'warning' }
    )

    const result = await scheduleStore.resetTimer(schedule.id)

    if (result.success) {
      ElMessage.success(result.message + ` (版本: ${result.timer_version})`)
      await loadTeacherData()
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消
  }
}

// 数据管理方法
const goToDataManagement = () => {
  router.push('/data-management')
}

const exportAllData = async () => {
  try {
    await tutorDB.backupToFile()
    ElMessage.success('数据导出成功！')
  } catch (error) {
    console.error('数据导出失败:', error)
    ElMessage.error('数据导出失败')
  }
}

// 生命周期
onMounted(() => {
  // 检查管理员权限
  if (!authStore.isAdmin) {
    ElMessage.error('权限不足，只有管理员可以访问此页面')
    router.push('/')
    return
  }
  
  loadUsers()
})
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.admin-header {
  background: white;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.welcome-text {
  color: #606266;
  font-size: 14px;
}

.admin-content {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.user-management {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.card-header span {
  font-size: 18px;
  font-weight: 600;
}

.users-list {
  margin-top: 20px;
}

/* 表格样式优化 */
:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-table th) {
  background: #fafafa;
  color: #303133;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .admin-header {
    padding: 15px 20px;
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .admin-content {
    padding: 20px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
}

/* 教师数据管理样式 */
.admin-tabs {
  margin-top: 20px;
}

.teacher-data-management {
  margin-bottom: 30px;
}

.data-tabs {
  margin-top: 20px;
}

.data-section {
  padding: 20px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.section-header span {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.section-header .el-button-group,
.section-header div {
  display: flex;
  gap: 10px;
}

.no-teacher-selected {
  padding: 60px 0;
  text-align: center;
}

/* 单词管理样式 */
.words-content {
  display: flex;
  gap: 20px;
  min-height: 400px;
}

.word-sets-panel {
  flex: 0 0 300px;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.word-sets-panel h3 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.word-sets {
  max-height: 350px;
  overflow-y: auto;
}

.word-set-item {
  padding: 12px 15px;
  margin-bottom: 8px;
  background: white;
  border-radius: 6px;
  transition: all 0.3s;
  border: 2px solid transparent;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.word-set-content {
  flex: 1;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.delete-btn {
  margin-left: 10px;
  opacity: 0;
  transition: opacity 0.3s;
}

.word-set-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
}

.word-set-item:hover .delete-btn {
  opacity: 1;
}

.word-set-item.active {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.word-count {
  font-size: 12px;
  opacity: 0.8;
}

.words-panel {
  flex: 1;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.words-panel h3 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.words-list {
  max-height: 350px;
  overflow-y: auto;
}

.word-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 15px;
  margin-bottom: 8px;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.word-item strong {
  color: #303133;
}

.word-item span {
  color: #606266;
}

/* 日程管理样式 */
.schedule-list {
  max-height: 500px;
  overflow-y: auto;
}

.date-group {
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.date-header {
  background: #f5f7fa;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
}

.date-text {
  font-weight: 600;
  color: #303133;
}

.course-count {
  color: #909399;
  font-size: 14px;
}

.schedule-items {
  background: white;
}

.schedule-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.schedule-item:last-child {
  border-bottom: none;
}

.schedule-time {
  font-weight: bold;
  color: #409eff;
  min-width: 80px;
  margin-right: 20px;
}

.schedule-content {
  flex: 1;
}

.schedule-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
}

.schedule-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 15px;
}

.info-label {
  color: #909399;
  font-size: 13px;
}

.info-value {
  font-weight: 600;
}

.info-value.student {
  color: #409eff;
}

.info-value.wordset {
  color: #67c23a;
}

.info-separator {
  color: #dcdfe6;
  margin: 0 4px;
}

.schedule-type {
  display: flex;
  align-items: center;
  gap: 8px;
}

.duration-text {
  color: #909399;
  font-size: 13px;
  margin-left: 4px;
}

.schedule-actions {
  display: flex;
  gap: 10px;
}

/* 数据管理样式 */
.data-management-section {
  padding: 20px 0;
}

.data-actions {
  padding: 20px 0;
}

.action-grid {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.action-grid .el-button {
  flex: 1;
  height: 60px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.data-info {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.data-info p {
  margin: 0 0 10px 0;
  font-weight: 600;
  color: #303133;
}

.data-info ul {
  margin: 0;
  padding-left: 20px;
}

.data-info li {
  color: #606266;
  margin-bottom: 8px;
}

/* 表单帮助文本样式 */
.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* Excel导入相关样式 */
.sheets-preview {
  margin-top: 20px;
}

.sheets-preview h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.sheet-info h5 {
  margin: 0 0 5px 0;
  color: #303133;
}

.word-count-badge {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.sheet-actions {
  display: flex;
  align-items: center;
}

.word-preview {
  background: #f9f9f9;
  padding: 10px;
  border-radius: 4px;
}

.preview-word {
  display: flex;
  gap: 20px;
  margin-bottom: 5px;
}

.preview-word .english {
  font-weight: 600;
  color: #303133;
  min-width: 120px;
}

.preview-word .chinese {
  color: #606266;
}

.more-words {
  color: #909399;
  font-size: 12px;
  margin-top: 10px;
}

/* 剩余时长颜色样式 */
.hours-empty {
  color: #f56c6c;
  font-weight: bold;
}

.hours-low {
  color: #e6a23c;
  font-weight: bold;
}

.hours-medium {
  color: #409eff;
  font-weight: bold;
}

.hours-high {
  color: #67c23a;
  font-weight: bold;
}

/* 阅读课文章预览 */
.article-preview {
  background: #fafafa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 14px 16px;
  font-size: 15px;
  color: #303133;
  max-height: 260px;
  overflow-y: auto;
  line-height: 1.9;
}

.article-preview :deep(mark) {
  background: #fff3b0;
  color: #303133;
  border-radius: 2px;
  padding: 0 2px;
  font-weight: 600;
}

.search-results {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 8px;
  max-height: 140px;
  overflow-y: auto;
}

.search-word-tag:hover {
  background: #409eff;
  color: white;
}

/* 文章预览 - 按段显示 */
.preview-paragraph {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #e4e7ed;
}

.preview-paragraph:last-child {
  border-bottom: none;
}

.preview-en {
  font-size: 15px;
  line-height: 1.9;
  color: #303133;
  margin-bottom: 6px;
  padding: 8px 10px;
  background: #fafafa;
  border-radius: 4px;
}

.preview-en :deep(mark) {
  background: #fff3b0;
  color: #303133;
  border-radius: 2px;
  padding: 0 2px;
  font-weight: 600;
}

.preview-zh-header {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 3px 6px;
  margin-top: 4px;
  border-radius: 4px;
  user-select: none;
  width: fit-content;
}

.preview-zh-header:hover {
  background: #e8f5e0;
}

.zh-toggle-icon {
  font-size: 10px;
  color: #67c23a;
}

.zh-toggle-label {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}

.preview-zh-input :deep(.el-textarea__inner) {
  background: #f0f9eb;
  color: #4a6741;
  font-size: 14px;
  border-color: #b7d9a8;
  line-height: 1.7;
  resize: none;
}

/* 听力课：拖拽上传区域 */
.upload-drag-area :deep(.el-upload) {
  width: 100%;
}

.upload-drag-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 110px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-drag-icon {
  font-size: 28px;
  color: #909399;
  margin-bottom: 6px;
}

.upload-drag-icon.is-loading {
  animation: rotating 1.2s linear infinite;
  color: #409eff;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.upload-drag-area :deep(.el-upload__text) {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
}

.upload-drag-area :deep(.el-upload__tip) {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

/* 听力课：段落翻译可滚动长框 */
.translation-scroll-box {
  margin-top: 10px;
  max-height: 320px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 8px;
  background: #fff;
}

.translation-para-item {
  padding: 8px;
  margin-bottom: 8px;
  background: #fafafa;
  border-radius: 4px;
}

.translation-para-item:last-child {
  margin-bottom: 0;
}

.translation-para-en {
  font-size: 13px;
  color: #303133;
  margin-bottom: 4px;
  line-height: 1.5;
}
</style>