# 📱 WiFi投票一码通使用说明

## 功能说明

提供**两种二维码方案**，让用户扫码后能轻松连接WiFi并参与投票：

### 方案1: WiFi连接二维码 ⭐推荐
**一个二维码** - 扫描后直接连接WiFi
- ✅ Android/iOS原生支持
- ✅ 一键连接，无需输入密码
- ✅ 连接后自动弹出欢迎页（配合DNS劫持）

### 方案2: WiFi + 投票双二维码
**两个二维码** - 分步操作
- 📶 第一个：WiFi连接二维码
- 🗳️ 第二个：投票页面二维码

## 🌐 WiFi二维码格式

### 标准格式
```
WIFI:T:WPA;S:投票抽奖系统;P:12345678;;
```

**参数说明**:
- `T`: 加密类型 (WPA/WEP/nopass)
- `S`: SSID (WiFi名称)
- `P`: Password (密码)
- `H`: Hidden (可选，隐藏网络)

### 设备兼容性
- ✅ **Android 10+**: 完美支持，扫码即连
- ✅ **iOS 11+**: 完美支持，弹出连接提示
- ⚠️ **Windows**: 不支持，需手动输入
- ⚠️ **旧设备**: 可能不支持

## 🚀 使用方法

### 后端API

#### 1. 生成WiFi二维码
```http
GET /api/admin/qrcode/wifi?password=12345678
```

**响应**:
```json
{
  "success": true,
  "data": {
    "qrcode": "base64图片数据",
    "ssid": "投票抽奖系统",
    "type": "wifi",
    "instruction": "扫描此二维码即可连接WiFi"
  }
}
```

#### 2. 生成WiFi+投票组合二维码
```http
GET /api/admin/qrcode/wifi-vote?password=12345678
```

**响应**:
```json
{
  "success": true,
  "data": {
    "wifi_qrcode": "WiFi二维码base64",
    "vote_qrcode": "投票页面二维码base64",
    "wifi_info": "WiFi: 投票抽奖系统",
    "vote_info": "投票地址: http://192.168.137.1:5000/vote",
    "instruction": "先扫描上方二维码连接WiFi，再扫描下方二维码访问投票页面"
  }
}
```

### 前端调用示例

```javascript
// 生成WiFi二维码
function generateWiFiQRCode() {
    const password = '12345678'; // 从配置或用户输入获取
    
    fetch(`/api/admin/qrcode/wifi?password=${password}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const qrcode = data.data.qrcode;
                document.getElementById('wifiQR').src = 
                    `data:image/png;base64,${qrcode}`;
                console.log('WiFi二维码生成成功');
            }
        })
        .catch(error => {
            console.error('生成失败:', error);
        });
}

// 生成WiFi+投票组合二维码
function generateComboQRCode() {
    const password = '12345678';
    
    fetch(`/api/admin/qrcode/wifi-vote?password=${password}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 显示WiFi二维码
                document.getElementById('wifiQR').src = 
                    `data:image/png;base64,${data.data.wifi_qrcode}`;
                
                // 显示投票二维码
                document.getElementById('voteQR').src = 
                    `data:image/png;base64,${data.data.vote_qrcode}`;
                
                console.log('组合二维码生成成功');
            }
        });
}
```

## 📋 完整使用流程

### 方案1: 仅WiFi二维码（配合DNS劫持）⭐

```
1. 管理员操作：
   - 启动WiFi热点
   - 启动DNS劫持服务
   - 生成WiFi二维码
   - 打印或投影显示

2. 用户操作：
   - 扫描WiFi二维码
   - 自动连接WiFi
   - 自动弹出欢迎页
   - 3秒后跳转投票页

3. 优势：
   ✅ 用户操作最简单
   ✅ 一次扫码完成所有步骤
   ✅ 体验最好
```

### 方案2: WiFi + 投票双二维码

```
1. 管理员操作：
   - 启动WiFi热点
   - 生成组合二维码
   - 并排显示两个二维码

2. 用户操作：
   - 扫描第一个二维码（WiFi）
   - 连接WiFi
   - 扫描第二个二维码（投票）
   - 打开投票页面

3. 适用场景：
   ✅ DNS劫持未启用
   ✅ 需要明确指引
   ✅ 用户设备较老
```

## 🎨 界面展示建议

### 单二维码展示
```html
<div class="qrcode-card">
    <h3>📱 扫码连接WiFi并投票</h3>
    <img id="wifiQR" alt="WiFi二维码">
    <p class="instruction">
        1. 使用手机相机扫描此二维码<br>
        2. 点击"连接到网络"<br>
        3. 自动打开投票页面
    </p>
    <div class="wifi-info">
        WiFi名称: 投票抽奖系统<br>
        <small>已自动配置密码，无需手动输入</small>
    </div>
</div>
```

### 双二维码展示
```html
<div class="combo-qrcode-container">
    <div class="qr-step">
        <span class="step-number">1</span>
        <h3>扫码连接WiFi</h3>
        <img id="wifiQR" alt="WiFi二维码">
        <p>WiFi: 投票抽奖系统</p>
    </div>
    
    <div class="arrow">➡️</div>
    
    <div class="qr-step">
        <span class="step-number">2</span>
        <h3>扫码参与投票</h3>
        <img id="voteQR" alt="投票二维码">
        <p>扫码打开投票页面</p>
    </div>
</div>
```

## ⚙️ 配置说明

### 后端配置

1. **热点密码** - 需要提供给API
```python
# 从配置或数据库获取
hotspot_password = '12345678'
```

2. **安全考虑** - 不建议在响应中返回密码
```python
# ❌ 不安全
return {'password': password}

# ✅ 安全
# 只在生成二维码时使用密码，不返回给客户端
```

### 前端配置

1. **密码输入** - 让管理员输入密码
```html
<input type="password" id="hotspotPassword" 
       placeholder="输入热点密码以生成WiFi二维码">
<button onclick="generateWithPassword()">生成二维码</button>
```

2. **记住密码** - 使用sessionStorage
```javascript
// 保存密码（仅当前会话）
sessionStorage.setItem('hotspot_password', password);

// 读取密码
const savedPassword = sessionStorage.getItem('hotspot_password');
```

## 🧪 测试步骤

### 测试WiFi二维码

1. **生成二维码**
```bash
# 确保热点已启动
# 访问API
curl "http://localhost:5000/api/admin/qrcode/wifi?password=12345678"
```

2. **手机测试**
```
- iPhone/iPad: 打开相机，扫描二维码，弹出"加入网络"提示
- Android: 打开相机或扫码应用，自动识别WiFi并提示连接
```

3. **验证连接**
```
- 连接成功后，检查WiFi名称
- 打开浏览器，访问任意网址
- 应该自动跳转到欢迎页（如果DNS劫持已启用）
```

### 测试组合二维码

1. **生成双二维码**
```bash
curl "http://localhost:5000/api/admin/qrcode/wifi-vote?password=12345678"
```

2. **分步测试**
```
第一步：扫描WiFi二维码
- 验证WiFi连接成功

第二步：扫描投票二维码
- 验证打开投票页面
```

## ❌ 常见问题

### Q1: WiFi二维码扫描后没反应
**原因**:
- 设备不支持WiFi二维码
- 二维码格式错误
- 相机应用版本过旧

**解决**:
```
1. 确认设备系统版本（Android 10+/iOS 11+）
2. 更新相机应用
3. 使用专门的WiFi二维码扫描应用
4. 备选方案：显示明文WiFi信息，让用户手动连接
```

### Q2: 扫码后显示"无效的网络"
**原因**:
- 热点未启动
- SSID名称有特殊字符
- 密码格式问题

**解决**:
```
1. 确认热点已启动
2. 检查SSID和密码中是否有特殊字符（;,:等需要转义）
3. 使用简单的SSID和密码进行测试
```

### Q3: iPhone扫码后不提示连接
**原因**:
- iOS系统限制
- 二维码格式不符合标准

**解决**:
```
1. 确保二维码格式完全正确
2. 检查是否有额外的空格或字符
3. 使用iOS原生相机（不是第三方应用）
```

### Q4: 生成失败，提示"热点未启动"
**原因**:
- WiFi热点未启动
- API无法获取热点状态

**解决**:
```
1. 先启动WiFi热点
2. 确认热点状态为"运行中"
3. 再生成WiFi二维码
```

## 🎯 最佳实践

### 1. 推荐流程
```
✅ 启动WiFi热点
✅ 启动DNS劫持
✅ 仅生成WiFi二维码
✅ 用户扫码自动完成所有步骤
```

### 2. 展示方式
```
✅ 投影在大屏幕上
✅ 打印在入口处
✅ 制作易拉宝展架
✅ 添加详细操作说明
```

### 3. 安全建议
```
✅ 不在前端显示密码明文
✅ API调用需要管理员权限
✅ 使用强密码（至少8位）
✅ 活动结束后更改密码
```

### 4. 用户引导
```
✅ 添加图文并茂的操作说明
✅ 标注设备兼容性
✅ 提供备用方案（手动连接）
✅ 现场安排工作人员协助
```

## 📊 功能对比

| 方案 | 操作步骤 | 用户体验 | 技术要求 | 兼容性 |
|------|---------|---------|---------|--------|
| WiFi二维码 | 1步 | ⭐⭐⭐⭐⭐ | 需DNS劫持 | 📱新设备 |
| 双二维码 | 2步 | ⭐⭐⭐ | 无 | 📱所有设备 |
| 手动连接 | 3+步 | ⭐⭐ | 无 | 💻所有设备 |

## 🔄 更新日志

**v1.0 - 2025-10-17**
- ✅ 新增WiFi二维码生成服务
- ✅ 新增WiFi+投票组合二维码
- ✅ 支持Android/iOS原生WiFi连接
- ✅ API接口完整实现

---

**文档版本**: v1.0  
**最后更新**: 2025-10-17  
**维护者**: AI助手
