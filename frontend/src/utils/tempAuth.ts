// 临时认证初始化，确保默认用户存在
export const initTempAuth = () => {
  const users = JSON.parse(localStorage.getItem('users') || '[]')
  const passwords = JSON.parse(localStorage.getItem('userPasswords') || '{}')
  
  if (users.length === 0) {
    const defaultAdmin = {
      id: 'admin-001',
      username: 'admin',
      role: 'admin',
      displayName: '系统管理员',
      email: 'admin@example.com',
      createdAt: new Date().toISOString()
    }
    
    users.push(defaultAdmin)
    passwords['admin'] = 'admin123'
    
    localStorage.setItem('users', JSON.stringify(users))
    localStorage.setItem('userPasswords', JSON.stringify(passwords))
    
    // 同时保存到备份键
    localStorage.setItem('backup_users_userList', JSON.stringify(users))
    localStorage.setItem('backup_users_userPasswords', JSON.stringify(passwords))
    
    console.log('默认管理员账号已创建: admin / admin123')
  }
}