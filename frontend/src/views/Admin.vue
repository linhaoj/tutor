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
                              <div class="schedule-title">{{ schedule.wordSet }}</div>
                              <div class="schedule-student">{{ schedule.studentName }}</div>
                              <div class="schedule-type">
                                <el-tag 
                                  :type="schedule.type === 'review' ? 'warning' : 'success'" 
                                  size="small"
                                >
                                  {{ schedule.type === 'review' ? '抗遗忘' : '单词学习' }}
                                </el-tag>
                              </div>
                            </div>
                            <div class="schedule-actions">
                              <el-button size="small" @click="editSchedule(schedule)">编辑</el-button>
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
            大课60分钟 = 1.0h，小课30分钟 = 0.5h
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
            大课60分钟 = 1.0h，小课30分钟 = 0.5h
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
      width="600px"
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
        
        <el-form-item label="选择单词集" required>
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
          <el-radio-group v-model="scheduleForm.type">
            <el-radio value="learning">单词学习</el-radio>
            <el-radio value="review">抗遗忘</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="课程规模">
          <el-radio-group v-model="scheduleForm.classType" @change="updateScheduleDuration">
            <el-radio value="big">大课 (60分钟)</el-radio>
            <el-radio value="small">小课 (30分钟)</el-radio>
          </el-radio-group>
        </el-form-item>
        
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
          <div class="form-help">
            可选择预设时间或输入自定义时间（如：14:15）
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addScheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddSchedule">
          添加课程
        </el-button>
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Plus, Avatar, ArrowDown, Upload, Setting, Download, Delete } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { useAuthStore } from '@/stores/auth'
import { useStudentsStore } from '@/stores/students'
import { useWordsStore } from '@/stores/words'
import { useScheduleStore } from '@/stores/schedule'
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
  
  teacherSchedules.value.forEach(schedule => {
    if (!schedulesByDate[schedule.date]) {
      schedulesByDate[schedule.date] = []
    }
    schedulesByDate[schedule.date].push(schedule)
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
  if (!scheduleForm.studentId || !scheduleForm.wordSet || !scheduleForm.date || !scheduleForm.time) {
    ElMessage.error('请填写完整的课程信息')
    return
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
      word_set_name: scheduleForm.wordSet,
      course_type: scheduleForm.type,
      duration: scheduleForm.duration,
      class_type: scheduleForm.classType,
      teacher_id: selectedTeacherId.value  // 管理员为指定教师创建课程
    })

    if (result.success) {
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

.schedule-student {
  color: #606266;
  font-size: 14px;
  margin-bottom: 5px;
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
</style>