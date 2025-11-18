/**
 * 管理后台 JavaScript
 */

// API基础URL
const API_BASE = '/api/admin';

// 全局变量
let candidates = [];
let lotteryHistory = [];
let socket = null;

// 标签页切换函数 - 移至全局作用域，确保HTML中可直接调用
function switchTab(tabName) {
    // 隐藏所有标签内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 移除所有标签的active类
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 显示选中的标签内容
    document.getElementById(tabName).classList.add('active');
    
    // 激活对应的标签按钮 - 修复：使用查询选择器而不是event.target
    document.querySelectorAll('.tab').forEach((tab, index) => {
        const tabs = ['dashboard', 'vote-config', 'candidates', 'network', 'lottery', 'account'];
        if (tabs[index] === tabName) {
            tab.classList.add('active');
        }
    });
    
    // 根据切换的标签加载相应数据
    switch(tabName) {
        case 'dashboard':
            refreshData();
            break;
        case 'vote-config':
            loadVoteConfig();
            break;
        case 'candidates':
            loadCandidates();
            break;
        case 'network':
            checkHotspotStatus();
            break;
        case 'lottery':
            loadLotteryHistory();
            updateAvailableCount();
            break;
        case 'account':
            loadAccountInfo();
            break;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('管理后台加载完成');
    
    // 检查登录状态
    checkLoginStatus();
    
    // 初始化数据
    initSocket();
    loadCandidates();
    loadLotteryHistory();
    loadSystemInfo();
    loadVoteConfig();
    refreshData();
    loadAccountInfo();
    
    // 添加退出登录按钮
    addLogoutButton();
    
    // 绑定投票配置表单提交
    const voteConfigForm = document.getElementById('voteConfigForm');
    if (voteConfigForm) {
        voteConfigForm.addEventListener('submit', function(e) {
            e.preventDefault();
            updateVoteConfig();
        });
    }
    
    // 绑定密码修改表单提交
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            changePassword();
        });
    }
    
    // 确保所有全局函数可用 - 直接绑定
    try {
        window.refreshData = refreshData;
        window.exportResults = exportResults;
        window.resetVotes = resetVotes;
        window.showAddModal = showAddModal;
        window.showQuickAddModal = showQuickAddModal;
        window.generateAdminQRCode = generateAdminQRCode;
        window.createHotspot = createHotspot;
        window.stopHotspot = stopHotspot;
        window.checkHotspotStatus = checkHotspotStatus;
        window.generateQRCode = generateQRCode;
        window.generateWiFiQRCode = generateWiFiQRCode;
        window.generateComboQRCode = generateComboQRCode;
        // 移除了与网络共享相关的函数绑定
        // switchTab已在全局作用域定义，无需再次绑定
        console.log('所有函数绑定成功');
    } catch (e) {
        console.error('函数绑定出错:', e);
    }
});

// ==================== 登录管理 ====================
function checkLoginStatus() {
    fetch(`${API_BASE}/check-auth`)
        .then(response => {
            // 先检查响应状态码
            if (response.status === 401) {
                // 未登录，跳转到登录页面
                window.location.href = '/admin/login';
                return Promise.reject('未登录');
            }
            // 只有状态码正常时才解析JSON
            return response.json();
        })
        .then(data => {
            if (data && data.success && !data.data.logged_in) {
                // 未登录，跳转到登录页面
                window.location.href = '/admin/login';
            } else if (data && data.success && data.data.logged_in) {
                // 已登录，更新账户信息
                document.getElementById('currentUsername').textContent = data.data.username || 'admin';
            }
        })
        .catch(error => {
            // 即使检查失败，也继续加载页面，避免因网络问题导致页面无法使用
            console.error('检查登录状态失败:', error);
            // 不要跳转，让用户可以继续使用页面
        });
}

// 退出登录功能已移至操作区按钮
function addLogoutButton() {
    // 不再在页面头部添加退出按钮
    return;
}

function logout() {
    if (!confirm('确定要退出登录吗？')) {
        return;
    }
    
    fetch(`${API_BASE}/logout`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 清除本地存储的任何认证信息
            localStorage.removeItem('admin_token');
            // 跳转到登录页面
            window.location.href = '/admin/login';
        } else {
            showMessage('退出失败', 'error');
        }
    })
    .catch(error => {
        console.error('退出失败:', error);
        // 即使API调用失败，也清除本地信息并跳转到登录页面
        localStorage.removeItem('admin_token');
        window.location.href = '/admin/login';
    });
}

// ==================== WebSocket连接 ====================
function initSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('WebSocket已连接');
    });
    
    socket.on('vote_update', function(data) {
        console.log('收到投票更新:', data);
        refreshData();
    });
    
    socket.on('lottery_result', function(data) {
        console.log('收到抽奖结果:', data);
        loadLotteryHistory();
    });
}

// ==================== 数据看板 ====================
function refreshData() {
    fetch(`${API_BASE}/candidates`)
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/admin/login';
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                candidates = data.data;
                updateDashboard();
                updateRankingTable();
            }
        })
        .catch(error => {
            console.error('加载数据失败:', error);
            showMessage('加载数据失败', 'error');
        });
}

function updateDashboard() {
    const totalVotes = candidates.reduce((sum, c) => sum + c.votes, 0);
    const totalCandidates = candidates.length;
    const topVotes = candidates.length > 0 ? Math.max(...candidates.map(c => c.votes)) : 0;
    
    document.getElementById('totalVotes').textContent = totalVotes;
    document.getElementById('totalCandidates').textContent = totalCandidates;
    document.getElementById('topVotes').textContent = topVotes;
}

function updateRankingTable() {
    const tbody = document.querySelector('#rankingTable tbody');
    const table = tbody.closest('table');
    
    if (candidates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:30px;">暂无候选人数据</td></tr>';
        return;
    }
    
    const totalVotes = candidates.reduce((sum, c) => sum + c.votes, 0);
    const sorted = [...candidates].sort((a, b) => b.votes - a.votes);
    
    // 先淡出表格
    table.style.opacity = '0';
    table.style.transition = 'opacity 0.3s ease';
    
    // 使用 requestAnimationFrame 确保渲染在空闲时执行
    requestAnimationFrame(() => {
        // 使用 DocumentFragment 来批量添加DOM元素，避免多次重排
        const fragment = document.createDocumentFragment();
        
        sorted.forEach((candidate, index) => {
            const percentage = totalVotes > 0 ? ((candidate.votes / totalVotes) * 100).toFixed(1) : 0;
            const row = document.createElement('tr');
            // 修复图片URL显示逻辑 - 使用photo_path字段
            let photoSrc = '/static/default.jpg';
            // 如果photo_path不为空，使用photo_path字段
            if (candidate.photo_path && candidate.photo_path !== '') {
                // 如果是完整URL路径
                if (candidate.photo_path.startsWith('/')) {
                    photoSrc = candidate.photo_path;
                } else {
                    // 如果是相对路径，添加/uploads/photos/前缀
                    photoSrc = `/uploads/photos/${candidate.photo_path}`;
                }
            }
            
            row.innerHTML = `
                <td>${index + 1}</td>
                <td><img src="${photoSrc}" class="candidate-photo-small" alt="${candidate.name}" onerror="this.src='/static/default.jpg'"></td>
                <td>${candidate.name}</td>
                <td>${candidate.votes}</td>
                <td>${percentage}%</td>
            `;
            fragment.appendChild(row);
        });
        
        // 清空表格并一次性添加所有行
        tbody.innerHTML = '';
        tbody.appendChild(fragment);
        
        // 更新完成后淡入表格，增加延迟确保DOM更新完成
        setTimeout(() => {
            table.style.opacity = '1';
        }, 50);
    });
}

function exportResults() {
    showMessage('导出功能开发中...', 'error');
}

function resetVotes() {
    if (!confirm('确定要重置所有投票数据吗？此操作不可恢复！')) {
        return;
    }
    
    fetch(`${API_BASE}/votes/reset`, {
        method: 'POST'
    })
    .then(response => {
        if (response.status === 401) {
            window.location.href = '/admin/login';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            showMessage('投票数据已重置', 'success');
            refreshData();
        } else if (data) {
            showMessage(data.message || '重置失败', 'error');
        }
    })
    .catch(error => {
        console.error('重置失败:', error);
        showMessage('重置失败', 'error');
    });
}

// 下载模板函数
function downloadTemplate() {
    window.open('/api/admin/export/template', '_blank');
}

// ==================== 候选人管理 ====================
function loadCandidates() {
    fetch(`${API_BASE}/candidates`)
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/admin/login';
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                candidates = data.data;
                updateCandidatesTable();
            }
        })
        .catch(error => {
            console.error('加载候选人失败:', error);
            showMessage('加载候选人失败', 'error');
        });
}

function updateCandidatesTable() {
    const tbody = document.querySelector('#candidatesTable tbody');
    const table = tbody.closest('table');
    
    if (candidates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:30px;">暂无候选人数据</td></tr>';
        return;
    }
    
    // 先淡出表格
    table.style.opacity = '0';
    table.style.transition = 'opacity 0.3s ease';
    
    // 使用 requestAnimationFrame 确保渲染在空闲时执行
    requestAnimationFrame(() => {
        // 使用 DocumentFragment 来批量添加DOM元素，避免多次重排
        const fragment = document.createDocumentFragment();
        
        candidates.forEach(candidate => {
            const row = document.createElement('tr');
            // 修复图片URL显示逻辑 - 使用photo_path字段
            let photoSrc = '/static/default.jpg';
            // 如果photo_path不为空，使用photo_path字段
            if (candidate.photo_path && candidate.photo_path !== '') {
                // 如果是完整URL路径
                if (candidate.photo_path.startsWith('/')) {
                    photoSrc = candidate.photo_path;
                } else {
                    // 如果是相对路径，添加/uploads/photos/前缀
                    photoSrc = `/uploads/photos/${candidate.photo_path}`;
                }
            }
            
            row.innerHTML = `
                <td>${candidate.id}</td>
                <td><img src="${photoSrc}" class="candidate-photo-small" alt="${candidate.name}" onerror="this.src='/static/default.jpg'"></td>
                <td>${candidate.name}</td>
                <td>${candidate.description || '-'}</td>
                <td>${candidate.votes}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn edit" onclick="editCandidate(${candidate.id})">编辑</button>
                        <button class="action-btn delete" onclick="deleteCandidate(${candidate.id})">删除</button>
                    </div>
                </td>
            `;
            fragment.appendChild(row);
        });
        
        // 清空表格并一次性添加所有行
        tbody.innerHTML = '';
        tbody.appendChild(fragment);
        
        // 更新完成后淡入表格，增加延迟确保DOM更新完成
        setTimeout(() => {
            table.style.opacity = '1';
        }, 50);
    });
}

function showAddModal() {
    document.getElementById('modalTitle').textContent = '添加候选人';
    document.getElementById('candidateForm').reset();
    document.getElementById('candidateId').value = '';
    document.getElementById('photoPreview').innerHTML = '';
    document.getElementById('candidateModal').classList.add('show');
}

function editCandidate(id) {
    const candidate = candidates.find(c => c.id === id);
    if (!candidate) return;
    
    document.getElementById('modalTitle').textContent = '编辑候选人';
    document.getElementById('candidateId').value = candidate.id;
    document.getElementById('candidateName').value = candidate.name;
    document.getElementById('candidateDescription').value = candidate.description || '';
    document.getElementById('candidatePhotoPath').value = candidate.photo_path || '';
    
    if (candidate.photo_path) {
        // 修复图片预览逻辑
        let photoSrc = '/static/default.jpg';
        if (candidate.photo_path && candidate.photo_path !== '') {
            // 如果是完整URL路径
            if (candidate.photo_path.startsWith('/')) {
                photoSrc = candidate.photo_path;
            } else {
                // 如果是相对路径，添加/uploads/photos/前缀
                photoSrc = `/uploads/photos/${candidate.photo_path}`;
            }
        }
        document.getElementById('photoPreview').innerHTML = 
            `<img src="${photoSrc}" style="max-width: 200px; margin-top: 10px;" onerror="this.src='/static/default.jpg'">`;
    } else {
        document.getElementById('photoPreview').innerHTML = '';
    }
    
    document.getElementById('candidateModal').classList.add('show');
}

function deleteCandidate(id) {
    if (!confirm('确定要删除这个候选人吗？')) {
        return;
    }
    
    fetch(`${API_BASE}/candidates/${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('删除成功', 'success');
            // 延迟加载，确保消息显示完整且视觉平滑
            setTimeout(() => {
                loadCandidates();
            }, 200);
        } else {
            showMessage(data.message || '删除失败', 'error');
        }
    })
    .catch(error => {
        console.error('删除失败:', error);
        showMessage('删除失败', 'error');
    });
}

function closeModal() {
    const modal = document.getElementById('candidateModal');
    modal.classList.add('hiding');
    setTimeout(() => {
        modal.classList.remove('show', 'hiding');
    }, 300);
}

// 文件选择预览
document.getElementById('candidatePhoto')?.addEventListener('change', function() {
    previewPhoto();
});

// 表单提交
document.getElementById('candidateForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const id = document.getElementById('candidateId').value;
    const fileInput = document.getElementById('candidatePhoto');
    const file = fileInput.files[0];
    
    // 如果是添加新候选人且有图片文件，先创建候选人再上传图片
    if (!id && file) {
        addCandidateWithPhoto();
    } else if (id && file) {
        // 更新候选人且有新图片，先上传图片再更新候选人
        updateCandidateWithPhoto();
    } else {
        // 没有图片或没有文件的情况，使用原有逻辑
        saveCandidate();
    }
});

function saveCandidate() {
    const id = document.getElementById('candidateId').value;
    const formData = {
        name: document.getElementById('candidateName').value,
        description: document.getElementById('candidateDescription').value,
        photo_path: document.getElementById('candidatePhotoPath').value
    };
    
    const url = id ? `${API_BASE}/candidates/${id}` : `${API_BASE}/candidates`;
    const method = id ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showMessage(id ? '更新成功' : '添加成功', 'success');
            // 先关闭模态框，然后延迟加载数据，避免页面抖动
            closeModal();
            setTimeout(() => {
                loadCandidates();
            }, 500); // 等待模态框关闭动画完成并留出足够缓冲时间
        } else {
            showMessage(data.message || '操作失败', 'error');
        }
    })
    .catch(error => {
        console.error('保存失败:', error);
        showMessage('保存失败: ' + error.message, 'error');
    });
}

function addCandidateWithPhoto() {
    const name = document.getElementById('candidateName').value;
    const description = document.getElementById('candidateDescription').value;
    const fileInput = document.getElementById('candidatePhoto');
    const file = fileInput.files[0];
    
    if (!name) {
        showMessage('姓名不能为空', 'error');
        return;
    }
    
    // 1. 先创建候选人（不带图片）
    const candidateData = {
        name: name,
        description: description,
        photo_path: ''
    };
    
    fetch(`${API_BASE}/candidates`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(candidateData)
    })
    .then(response => {
        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('服务器返回了非JSON响应，请检查登录状态');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const candidateId = data.data.id;
            
            // 2. 使用候选人ID上传图片
            const formData = new FormData();
            formData.append('file', file);
            formData.append('candidate_id', candidateId);
            
            return fetch(`${API_BASE}/upload/photo`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(photoData => {
                if (photoData.success) {
                    // 3. 更新候选人记录，设置图片路径
                    const updateData = {
                        name: name,
                        description: description,
                        photo_path: photoData.data.photo_path
                    };
                    
                    return fetch(`${API_BASE}/candidates/${candidateId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(updateData)
                    })
                    .then(response => response.json())
                    .then(updateData => {
                        if (updateData.success) {
                            showMessage('添加成功', 'success');
                            closeModal();
                            setTimeout(() => {
                                loadCandidates();
                            }, 500);
                        } else {
                            throw new Error(updateData.message || '更新候选人失败');
                        }
                    });
                } else {
                    throw new Error(photoData.message || '上传图片失败');
                }
            });
        } else {
            throw new Error(data.message || '创建候选人失败');
        }
    })
    .catch(error => {
        console.error('添加候选人失败:', error);
        showMessage('添加失败: ' + error.message, 'error');
    });
}

function updateCandidateWithPhoto() {
    const id = document.getElementById('candidateId').value;
    const name = document.getElementById('candidateName').value;
    const description = document.getElementById('candidateDescription').value;
    const fileInput = document.getElementById('candidatePhoto');
    const file = fileInput.files[0];
    
    if (!name) {
        showMessage('姓名不能为空', 'error');
        return;
    }
    
    // 1. 使用候选人ID上传图片
    const formData = new FormData();
    formData.append('file', file);
    formData.append('candidate_id', id);
    
    fetch(`${API_BASE}/upload/photo`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 2. 更新候选人记录，设置图片路径
            const updateData = {
                name: name,
                description: description,
                photo_path: data.data.photo_path
            };
            
            return fetch(`${API_BASE}/candidates/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });
        } else {
            throw new Error(data.message || '上传图片失败');
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('更新成功', 'success');
            closeModal();
            setTimeout(() => {
                loadCandidates();
            }, 500);
        } else {
            throw new Error(data.message || '更新候选人失败');
        }
    })
    .catch(error => {
        console.error('更新候选人失败:', error);
        showMessage('更新失败: ' + error.message, 'error');
    });
}

function previewPhoto() {
    const fileInput = document.getElementById('candidatePhoto');
    const file = fileInput.files[0];
    if (!file) return;
    
    // 创建本地预览URL
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('photoPreview').innerHTML = 
            `<img src="${e.target.result}" style="max-width: 200px; margin-top: 10px;">`;
    };
    reader.readAsDataURL(file);
}

function importFile() {
    const fileInput = document.getElementById('fileImport');
    const file = fileInput.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    showMessage('正在导入...', 'success');
    
    fetch(`${API_BASE}/import/file`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(`成功导入 ${data.data.imported_count || 0} 个候选人`, 'success');
            // 延迟加载，确保消息显示完整且视觉平滑
            setTimeout(() => {
                loadCandidates();
            }, 200);
        } else {
            showMessage(data.message || '导入失败', 'error');
        }
    })
    .catch(error => {
        console.error('导入失败:', error);
        showMessage('导入失败', 'error');
    });
}

// ==================== 快速拍照添加 ====================
function showQuickAddModal() {
    document.getElementById('quickAddForm').reset();
    document.getElementById('quickPhotoPath').value = '';
    document.getElementById('quickPhotoPreview').innerHTML = `
        <p style="font-size: 48px; margin-bottom: 10px;">📸</p>
        <p>点击或拖拽上传照片</p>
        <p style="color: #999; font-size: 14px;">支持 JPG、PNG 等格式</p>
    `;
    document.getElementById('quickAddModal').classList.add('show');
}

function closeQuickAddModal() {
    const modal = document.getElementById('quickAddModal');
    modal.classList.add('hiding');
    setTimeout(() => {
        modal.classList.remove('show', 'hiding');
    }, 300);
}

function handleQuickPhoto() {
    const fileInput = document.getElementById('quickPhoto');
    const file = fileInput.files[0];
    if (!file) return;
    
    // 创建本地预览，不立即上传
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('quickPhotoPreview').innerHTML = `
            <img src="${e.target.result}" style="max-width: 100%; max-height: 300px; margin-top: 10px; border-radius: 8px;">
            <p style="color: #4CAF50; margin-top: 10px;">📸 照片已选择，请在下方输入姓名后提交</p>
        `;
        showMessage('照片已选择，请输入姓名后提交', 'success');
        // 自动聚焦到姓名输入框
        document.getElementById('quickName').focus();
    };
    reader.readAsDataURL(file);
}

// 快速添加表单提交
document.getElementById('quickAddForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('quickPhoto');
    const file = fileInput.files[0];
    const name = document.getElementById('quickName').value;
    const description = document.getElementById('quickDescription').value;
    
    if (!file) {
        showMessage('请先选择照片', 'error');
        return;
    }
    
    if (!name) {
        showMessage('姓名不能为空', 'error');
        return;
    }
    
    showMessage('正在添加候选人...', 'success');
    
    // 修复：先上传照片，然后创建候选人
    const photoFormData = new FormData();
    photoFormData.append('file', file);
    
    fetch(`${API_BASE}/upload/photo`, {
        method: 'POST',
        body: photoFormData
    })
    .then(response => {
        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // 如果是HTML响应，可能是登录状态过期
            if (response.status === 401) {
                throw new Error('登录状态已过期，请重新登录');
            }
            throw new Error('服务器返回了非JSON响应，状态码: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 照片上传成功，现在创建候选人
            const candidateData = {
                name: name,
                description: description,
                photo_path: data.data.photo_path  // 使用上传后的照片路径
            };
            
            return fetch(`${API_BASE}/candidates`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(candidateData)
            });
        } else {
            throw new Error(data.message || '上传照片失败');
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('添加成功', 'success');
            closeQuickAddModal();
            setTimeout(() => {
                loadCandidates();
            }, 500);
        } else {
            throw new Error(data.message || '创建候选人失败');
        }
    })
    .catch(error => {
        console.error('添加候选人失败:', error);
        showMessage('添加失败: ' + error.message, 'error');
    });
});

// ==================== 网络设置 ====================
function createHotspot() {
    const ssid = document.getElementById('hotspotSSID').value;
    const password = document.getElementById('hotspotPassword').value;
    
    if (!ssid || !password) {
        showMessage('请输入热点名称和密码', 'error');
        return;
    }
    
    if (password.length < 8) {
        showMessage('密码至少需要8位', 'error');
        return;
    }
    
    showMessage('正在创建热点...', 'success');
    
    fetch(`${API_BASE}/hotspot/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ssid, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('热点创建成功！', 'success');
            checkHotspotStatus();
        } else {
            showMessage(data.message || '创建失败', 'error');
        }
    })
    .catch(error => {
        console.error('创建热点失败:', error);
        showMessage('创建热点失败', 'error');
    });
}

function stopHotspot() {
    fetch(`${API_BASE}/hotspot/stop`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('热点已停止', 'success');
            checkHotspotStatus();
        } else {
            showMessage(data.message || '停止失败', 'error');
        }
    })
    .catch(error => {
        console.error('停止热点失败:', error);
        showMessage('停止热点失败', 'error');
    });
}

function checkHotspotStatus() {
    fetch(`${API_BASE}/hotspot/status`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const statusDiv = document.getElementById('hotspotStatus');
                if (data.data.running) {
                    statusDiv.className = 'hotspot-status running';
                    let html = `<strong>状态:</strong> ${data.data.status_text || '运行中'}`;
                    if (data.data.ssid) {
                        html += `<br><strong>SSID:</strong> ${data.data.ssid}`;
                    }
                    if (data.data.ip) {
                        html += `<br><strong>IP地址:</strong> ${data.data.ip}`;
                    }
                    if (data.data.clients !== undefined) {
                        html += `<br><strong>已连接设备:</strong> ${data.data.clients} 个`;
                    }
                    statusDiv.innerHTML = html;
                } else {
                    statusDiv.className = 'hotspot-status stopped';
                    statusDiv.innerHTML = `<strong>状态:</strong> ${data.data.status_text || '未运行'}`;
                }
            } else {
                const statusDiv = document.getElementById('hotspotStatus');
                statusDiv.className = 'hotspot-status stopped';
                statusDiv.innerHTML = `<strong>状态:</strong> 无法获取 - ${data.message || ''}`;
            }
        })
        .catch(error => {
            console.error('检查热点状态失败:', error);
            const statusDiv = document.getElementById('hotspotStatus');
            statusDiv.className = 'hotspot-status stopped';
            statusDiv.innerHTML = '<strong>状态:</strong> 检查失败';
        });
}

function generateQRCode() {
    showMessage('正在生成二维码...', 'success');
    
    fetch(`${API_BASE}/qrcode/vote`)
        .then(response => {
            console.log('二维码API响应状态:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('二维码API返回数据:', data);
            if (data.success) {
                document.getElementById('qrcodeDisplay').innerHTML = `
                    <img src="data:image/png;base64,${data.data.qrcode}" alt="投票二维码" style="max-width: 300px;">
                    <div class="url-display">${data.data.url}</div>
                    <p style="margin-top: 15px;">请用户扫描二维码参与投票</p>
                `;
                showMessage('二维码生成成功', 'success');
            } else {
                showMessage(data.message || '生成失败', 'error');
            }
        })
        .catch(error => {
            console.error('生成二维码失败:', error);
            showMessage('生成二维码失败: ' + error.message, 'error');
        });
}

// 生成WiFi连接二维码
function generateWiFiQRCode() {
    const password = document.getElementById('hotspotPassword').value;
    
    if (!password) {
        showMessage('请先输入WiFi热点密码', 'error');
        return;
    }
    
    showMessage('正在生成WiFi二维码...', 'success');
    
    fetch(`${API_BASE}/qrcode/wifi?password=${encodeURIComponent(password)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('qrcodeDisplay').innerHTML = `
                    <img src="data:image/png;base64,${data.data.qrcode}" alt="WiFi二维码" style="max-width: 300px;">
                    <div class="url-display">
                        <strong>📱 WiFi连接二维码</strong><br>
                        SSID: ${data.data.ssid}<br>
                        <small>支持 Android 10+ / iOS 11+</small>
                    </div>
                    <p style="margin-top: 15px; line-height: 1.6;">
                        📱 扫描此二维码即可自动连接WiFi<br>
                        <small>连接后将自动跳转到欢迎页面</small>
                    </p>
                `;
                showMessage('WiFi二维码生成成功', 'success');
            } else {
                showMessage(data.message || '生成失败', 'error');
            }
        })
        .catch(error => {
            console.error('生成WiFi二维码失败:', error);
            showMessage('生成WiFi二维码失败', 'error');
        });
}

// 生成管理后台二维码
function generateAdminQRCode() {
    showMessage('正在生成管理后台二维码...', 'success');
    
    fetch(`${API_BASE}/qrcode/admin`)
        .then(response => {
            console.log('管理后台二维码API响应状态:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('管理后台二维码API返回数据:', data);
            if (data.success) {
                document.getElementById('adminQrcodeDisplay').innerHTML = `
                    <img src="data:image/png;base64,${data.data.qrcode}" alt="管理后台二维码" style="max-width: 300px;">
                    <div class="url-display">${data.data.url}</div>
                    <p style="margin-top: 15px;">请扫描二维码访问管理后台</p>
                `;
                showMessage('管理后台二维码生成成功', 'success');
            } else {
                showMessage(data.message || '生成失败', 'error');
            }
        })
        .catch(error => {
            console.error('生成管理后台二维码失败:', error);
            showMessage('生成管理后台二维码失败: ' + error.message, 'error');
        });
}

// 生成WiFi+投票组合二维码
function generateComboQRCode() {
    const password = document.getElementById('hotspotPassword').value;
    
    if (!password) {
        showMessage('请先输入WiFi热点密码', 'error');
        return;
    }
    
    showMessage('正在生成组合二维码...', 'success');
    
    fetch(`${API_BASE}/qrcode/wifi-vote?password=${encodeURIComponent(password)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('qrcodeDisplay').innerHTML = `
                    <div style="display: flex; gap: 30px; justify-content: center; flex-wrap: wrap;">
                        <div style="text-align: center;">
                            <div style="background: #4CAF50; color: white; padding: 10px; border-radius: 8px 8px 0 0;">
                                <strong>① 连接WiFi</strong>
                            </div>
                            <img src="data:image/png;base64,${data.data.wifi_qrcode}" alt="WiFi二维码" style="max-width: 250px; border: 3px solid #4CAF50;">
                            <div style="background: #f5f5f5; padding: 10px; border-radius: 0 0 8px 8px;">
                                ${data.data.wifi_info}
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; font-size: 48px; color: #667eea;">
                            ➡️
                        </div>
                        <div style="text-align: center;">
                            <div style="background: #667eea; color: white; padding: 10px; border-radius: 8px 8px 0 0;">
                                <strong>② 打开投票</strong>
                            </div>
                            <img src="data:image/png;base64,${data.data.vote_qrcode}" alt="投票二维码" style="max-width: 250px; border: 3px solid #667eea;">
                            <div style="background: #f5f5f5; padding: 10px; border-radius: 0 0 8px 8px;">
                                ${data.data.vote_info}
                            </div>
                        </div>
                    </div>
                    <p style="margin-top: 20px; line-height: 1.8; background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                        <strong>💡 使用说明：</strong><br>
                        1️⃣ 先扫描左侧二维码连接WiFi<br>
                        2️⃣ 连接成功后扫描右侧二维码进入投票页面
                    </p>
                `;
                showMessage('组合二维码生成成功', 'success');
            } else {
                showMessage(data.message || '生成失败', 'error');
            }
        })
        .catch(error => {
            console.error('生成组合二维码失败:', error);
            showMessage('生成组合二维码失败', 'error');
        });
}

function loadSystemInfo() {
    fetch(`${API_BASE}/system/info`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('systemInfo').innerHTML = `
                    <p><strong>本机IP:</strong> ${data.data.ip || '-'}</p>
                    <p><strong>服务器端口:</strong> ${data.data.port || '5000'}</p>
                    <p><strong>投票地址:</strong> <a href="${data.data.vote_url}" target="_blank">${data.data.vote_url}</a></p>
                    <p><strong>管理地址:</strong> <a href="${data.data.admin_url}" target="_blank">${data.data.admin_url}</a></p>
                `;
            }
        })
        .catch(error => {
            console.error('加载系统信息失败:', error);
            document.getElementById('systemInfo').innerHTML = '<p>加载失败</p>';
        });
}

// ==================== 网络共享管理 ====================
function enableSharing() {
    if (!confirm('确定要启用外网共享吗？\n这将允许连接到热点的设备访问互联网。')) {
        return;
    }
    
    showMessage('正在启用外网共享...', 'success');
    
    fetch(`${API_BASE}/hotspot/sharing/enable`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message || '外网共享已启用', 'success');
            checkSharingStatus();
        } else {
            showMessage(data.message || '启用失败', 'error');
        }
    })
    .catch(error => {
        console.error('启用外网共享失败:', error);
        showMessage('启用外网共享失败', 'error');
    });
}

function disableSharing() {
    if (!confirm('确定要禁用外网共享吗？')) {
        return;
    }
    
    showMessage('正在禁用外网共享...', 'success');
    
    fetch(`${API_BASE}/hotspot/sharing/disable`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message || '外网共享已禁用', 'success');
            checkSharingStatus();
        } else {
            showMessage(data.message || '禁用失败', 'error');
        }
    })
    .catch(error => {
        console.error('禁用外网共享失败:', error);
        showMessage('禁用外网共享失败', 'error');
    });
}

function checkSharingStatus() {
    fetch(`${API_BASE}/hotspot/sharing/status`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const statusDiv = document.getElementById('sharingStatus');
                if (data.data.sharing_enabled) {
                    statusDiv.className = 'hotspot-status running';
                    statusDiv.innerHTML = `<strong>状态:</strong> 已启用 ✅`;
                    if (data.data.details) {
                        statusDiv.innerHTML += `<br><small>${data.data.details}</small>`;
                    }
                } else {
                    statusDiv.className = 'hotspot-status stopped';
                    statusDiv.innerHTML = `<strong>状态:</strong> 未启用`;
                }
            } else {
                const statusDiv = document.getElementById('sharingStatus');
                statusDiv.className = 'hotspot-status stopped';
                statusDiv.innerHTML = `<strong>状态:</strong> 无法获取 - ${data.message || ''}`;
            }
        })
        .catch(error => {
            console.error('检查共享状态失败:', error);
            const statusDiv = document.getElementById('sharingStatus');
            statusDiv.className = 'hotspot-status stopped';
            statusDiv.innerHTML = '<strong>状态:</strong> 检查失败';
        });
}

// ==================== 投票配置管理 ====================
function loadVoteConfig() {
    fetch(`${API_BASE}/vote/config`)
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/admin/login';
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                const config = data.data;
                const voteNameInput = document.getElementById('voteName');
                const maxVotesInput = document.getElementById('maxVotesPerUser');
                if (voteNameInput) voteNameInput.value = config.vote_name || '';
                if (maxVotesInput) maxVotesInput.value = config.max_votes_per_user || 1;
                
                // 加载投票统计
                loadVoteStatistics();
            }
        })
        .catch(error => {
            console.error('加载投票配置失败:', error);
        });
}

// 加载投票统计
function loadVoteStatistics() {
    fetch(`${API_BASE}/votes/statistics`)
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/admin/login';
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                const stats = data.data;
                
                // 更新统计信息
                const totalVotesElement = document.getElementById('totalVotes');
                const totalCandidatesElement = document.getElementById('totalCandidates');
                const uniqueVotersElement = document.getElementById('uniqueVoters');
                const maxVotesPerUserElement = document.getElementById('maxVotesPerUser');
                const avgVotesPerCandidateElement = document.getElementById('avgVotesPerCandidate');
                const voteCompletionRateElement = document.getElementById('voteCompletionRate');
                
                if (totalVotesElement) totalVotesElement.textContent = stats.total_votes || 0;
                if (totalCandidatesElement) totalCandidatesElement.textContent = stats.total_candidates || 0;
                if (uniqueVotersElement) uniqueVotersElement.textContent = stats.unique_voters || 0;
                if (maxVotesPerUserElement) maxVotesPerUserElement.textContent = stats.max_votes_per_user || 1;
                if (avgVotesPerCandidateElement) avgVotesPerCandidateElement.textContent = stats.avg_votes_per_candidate || '0.0';
                if (voteCompletionRateElement) voteCompletionRateElement.textContent = stats.vote_completion_rate + '%' || '0%';
            }
        })
        .catch(error => {
            console.error('加载投票统计失败:', error);
        });
}

function updateVoteConfig() {
    const voteName = document.getElementById('voteName')?.value.trim();
    const maxVotes = parseInt(document.getElementById('maxVotesPerUser')?.value);
    
    if (!voteName) {
        showMessage('投票名称不能为空', 'error');
        return;
    }
    
    if (isNaN(maxVotes) || maxVotes < 1) {
        showMessage('每人最大投票数必须为大于0的整数', 'error');
        return;
    }
    
    fetch(`${API_BASE}/vote/config`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            vote_name: voteName,
            max_votes_per_user: maxVotes
        })
    })
    .then(response => {
        if (response.status === 401) {
            window.location.href = '/admin/login';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            showMessage('投票配置更新成功', 'success');
        } else if (data) {
            showMessage(data.message || '更新失败', 'error');
        }
    })
    .catch(error => {
        console.error('更新配置失败:', error);
        showMessage('更新失败', 'error');
    });
}

// ==================== 抽奖管理 ====================
function drawLottery() {
    const rounds = parseInt(document.getElementById('lotteryCount').value);
    const prizeName = document.getElementById('prizeName').value;
    const excludeWinners = document.getElementById('excludeWinners').value === 'true';
    
    // 验证输入
    if (!prizeName) {
        showMessage('请输入奖品名称', 'error');
        return;
    }
    
    if (rounds < 1) {
        showMessage('抽奖轮数至少为1', 'error');
        return;
    }
    
    // 保存抽奖设置到服务器
    fetch(`${API_BASE}/lottery/settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            count: 1,  // 每轮只抽1人
            prize_name: prizeName,
            exclude_winners: excludeWinners,
            rounds: rounds  // 保存轮数信息
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(`✅ 抽奖设置已保存: ${prizeName} (${rounds}轮)`, 'success');
        } else {
            showMessage('❌ ' + (data.message || '保存失败'), 'error');
        }
    })
    .catch(error => {
        console.error('保存抽奖设置失败:', error);
        showMessage('❌ 保存抽奖设置失败: ' + error.message, 'error');
    });
}

function loadLotteryHistory() {
    fetch(`${API_BASE}/lottery/history`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                lotteryHistory = data.data;
                updateLotteryHistoryTable();
            }
        })
        .catch(error => {
            console.error('加载抽奖历史失败:', error);
        });
}

function updateLotteryHistoryTable() {
    const tbody = document.querySelector('#lotteryHistoryTable tbody');
    const table = tbody.closest('table');
    
    if (lotteryHistory.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:30px;">暂无抽奖记录</td></tr>';
        return;
    }
    
    // 先淡出表格
    table.style.opacity = '0';
    table.style.transition = 'opacity 0.3s ease';
    
    // 使用 requestAnimationFrame 确保渲染在空闲时执行
    requestAnimationFrame(() => {
        // 使用 DocumentFragment 来批量添加DOM元素，避免多次重排
        const fragment = document.createDocumentFragment();
        
        lotteryHistory.forEach(lottery => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${lottery.round}</td>
                <td>${lottery.prize_name || '-'}</td>
                <td>${lottery.candidate_name || '未知'}</td>
                <td>${lottery.drawn_at ? new Date(lottery.drawn_at).toLocaleString() : '-'}</td>
            `;
            fragment.appendChild(row);
        });
        
        // 清空表格并一次性添加所有行
        tbody.innerHTML = '';
        tbody.appendChild(fragment);
        
        // 更新完成后淡入表格，增加延迟确保DOM更新完成
        setTimeout(() => {
            table.style.opacity = '1';
        }, 50);
    });
}

function resetLottery() {
    if (!confirm('确定要重置所有抽奖数据吗？此操作不可恢复！')) {
        return;
    }
    
    fetch(`${API_BASE}/lottery/reset`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('抽奖数据已重置', 'success');
            loadLotteryHistory();
            updateAvailableCount();
        } else {
            showMessage(data.message || '重置失败', 'error');
        }
    })
    .catch(error => {
        console.error('重置失败:', error);
        showMessage('重置失败', 'error');
    });
}

function updateAvailableCount() {
    fetch(`${API_BASE}/lottery/available`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('availableCount').textContent = data.data.count;
            }
        })
        .catch(error => {
            console.error('获取可抽奖人数失败:', error);
        });
}

// ==================== 账户管理 ====================
function loadAccountInfo() {
    fetch(`${API_BASE}/check-auth`)
        .then(response => response.json())
        .then(data => {
            if (data && data.success && data.data.logged_in) {
                document.getElementById('currentUsername').textContent = data.data.username || 'admin';
            }
        })
        .catch(error => {
            console.error('加载账户信息失败:', error);
        });
}

function changePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (!currentPassword || !newPassword || !confirmPassword) {
        showMessage('所有字段都不能为空', 'error');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showMessage('新密码和确认密码不一致', 'error');
        return;
    }
    
    if (newPassword.length < 6) {
        showMessage('新密码长度至少为6位', 'error');
        return;
    }
    
    fetch(`${API_BASE}/change-password`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
            confirm_password: confirmPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('密码修改成功，请记住新密码', 'success');
            // 清空表单
            document.getElementById('changePasswordForm').reset();
        } else {
            showMessage(data.message || '密码修改失败', 'error');
        }
    })
    .catch(error => {
        console.error('密码修改失败:', error);
        showMessage('密码修改失败: ' + error.message, 'error');
    });
}

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const type = input.type === 'password' ? 'text' : 'password';
    input.type = type;
}

// ==================== 工具函数 ====================
function showMessage(text, type = 'success') {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type} show`;
    
    setTimeout(() => {
        messageDiv.classList.remove('show');
    }, 3000);
}

// 点击模态框外部关闭
document.getElementById('candidateModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// 点击快速添加模态框外部关闭
document.getElementById('quickAddModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeQuickAddModal();
    }
});

// 切换排除已中奖者状态
function toggleExcludeWinners() {
    const btn = document.getElementById('excludeWinnersBtn');
    const hiddenInput = document.getElementById('excludeWinners');
    
    if (hiddenInput.value === 'true') {
        // 当前是勾选状态，切换到未勾选
        btn.innerHTML = '☐ 排除已中奖者';
        btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        hiddenInput.value = 'false';
    } else {
        // 当前是未勾选状态，切换到勾选
        btn.innerHTML = '✅ 排除已中奖者';
        btn.style.background = 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)';
        hiddenInput.value = 'true';
    }
}

// 页面加载完成后初始化排除已中奖者按钮状态
document.addEventListener('DOMContentLoaded', function() {
    // 确保按钮状态正确初始化
    const hiddenInput = document.getElementById('excludeWinners');
    if (hiddenInput && hiddenInput.value === 'true') {
        const btn = document.getElementById('excludeWinnersBtn');
        if (btn) {
            btn.innerHTML = '✅ 排除已中奖者';
            btn.style.background = 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)';
        }
    }
});
