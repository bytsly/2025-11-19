"""
Flask应用工厂

版权所有 (c) 2025 赵宏宇
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
import logging
from backend.config import config
from backend.models import db
import os
from pathlib import Path

# 创建SocketIO实例
# 兼容性：先尝试使用线程模式（避免 eventlet/greenlet 导致的 ssl 问题），
# 如果该模式在当前环境下被视为无效（某些 engineio 版本/打包组合会抛出
# ValueError('Invalid async_mode specified')），则回退到不显式传递 async_mode
# 让库自动检测可用模式。
logger = logging.getLogger('backend.app')
try:
    socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
except ValueError as e:
    logger.warning('threading async_mode rejected by engineio (%s), falling back to auto-detect', e)
    # 不传 async_mode，让 Flask-SocketIO/engineio 自动选择
    socketio = SocketIO(cors_allowed_origins="*")


def create_app(config_name='default'):
    """
    创建Flask应用
    
    Args:
        config_name: 配置名称
        
    Returns:
        Flask应用实例
    """
    app = Flask(__name__, static_folder='../frontend/static')
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 配置session密钥
    app.secret_key = app.config['SECRET_KEY']
    
    # 初始化扩展
    from backend.models import db
    db.init_app(app)
    CORS(app)
    # 在某些 Python 环境或打包组合中，engineio 在初始化时可能抛出
    # ValueError('Invalid async_mode specified')。为了对抗不同解释器/site-packages
    # 的差异，这里对 socketio.init_app 做保护：如果发生 ValueError，
    # 我们会重建一个不带显式 async_mode 的 SocketIO 实例并重试初始化。
    try:
        socketio.init_app(app)
    except ValueError as e:
        # 记录警告并回退到自动检测模式
        logger = logging.getLogger('backend.app')
        logger.warning('socketio.init_app raised %s; retrying with auto-detect', e)
        from flask_socketio import SocketIO as _SocketIO
        # 覆盖模块级 socketio 变量，后续模块会使用新的实例
        globals()['socketio'] = _SocketIO(cors_allowed_origins="*")
        socketio.init_app(app)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员用户（如果不存在）
        from backend.models import AdminUser
        admin_username = app.config['ADMIN_USERNAME']
        admin_password = app.config['ADMIN_PASSWORD']
        
        # 检查是否已存在管理员用户
        existing_admin = AdminUser.query.filter_by(username=admin_username).first()
        if not existing_admin:
            # 创建默认管理员用户
            admin_user = AdminUser(username=admin_username)
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            print(f'创建默认管理员用户: {admin_username}')
    
    # 注册蓝图
    from backend.routes.admin import admin_bp
    from backend.routes.vote import vote_bp
    from backend.routes.lottery import lottery_bp
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(vote_bp)
    app.register_blueprint(lottery_bp)
    
    # 获取项目根目录
    base_dir = Path(__file__).resolve().parent.parent
    frontend_dir = base_dir / 'frontend'
    
    # 静态文件路由
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """提供上传文件访问"""
        # 正确处理子目录路径
        upload_folder = app.config['UPLOAD_FOLDER']
        
        # 如果路径包含子目录，需要分离目录和文件名
        if '/' in filename:
            directory, filename = filename.rsplit('/', 1)
            file_path = upload_folder / directory
            return send_from_directory(file_path, filename)
        else:
            return send_from_directory(upload_folder, filename)
    
    @app.route('/')
    def index():
        """首页 - 智能检测移动端并跳转到欢迎页"""
        from flask import request, redirect
        
        # 检测是否是移动设备
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(x in user_agent for x in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
        
        # 检测是否是Captive Portal探测请求
        is_captive_probe = any([
            'captivenetworksupport' in user_agent,  # iOS
            'connectivitycheck' in user_agent,      # Android/Google
            'hicloud' in user_agent,                # Huawei
            'ncsi' in user_agent,                   # Windows NCSI
            'requesturi' in user_agent,             # Generic probe
            request.path == '/generate_204',        # Android
            request.path == '/gen_204',             # Chrome
            request.path == '/hotspot-detect.html', # iOS
            request.path == '/connecttest.txt',     # Windows
            request.path == '/ncsi.txt',            # Windows NCSI
            request.path == '/redirect',            # Generic redirect
            request.path == '/success.txt',         # Generic success
            request.path == '/library/test/success.html',  # macOS
        ])
        
        # Captive Portal探测请求跳转到主页
        if is_captive_probe:
            return redirect('/')
        # 移动端跳转到欢迎页
        elif is_mobile:
            return redirect('/welcome')
        
        # PC端显示完整首页
        return send_from_directory(frontend_dir, 'index.html')
    
    @app.route('/welcome')
    def welcome():
        """欢迎页面 - 连接WiFi后的引导页"""
        return send_from_directory(frontend_dir, 'welcome.html')
    
    @app.route('/wifi-guide')
    def wifi_guide():
        """WiFi连接引导页 - 一码通方案"""
        return send_from_directory(frontend_dir, 'wifi_guide.html')
    
    # Captive Portal探测端点
    @app.route('/generate_204')
    @app.route('/gen_204')
    def captive_portal_check():
        """Android/Chrome系统Captive Portal检测"""
        from flask import redirect
        return redirect('/')
    
    @app.route('/hotspot-detect.html')
    def captive_portal_apple():
        """iOS系统Captive Portal检测"""
        from flask import redirect
        return redirect('/')
    
    @app.route('/connecttest.txt')
    def captive_portal_windows():
        """Windows系统Captive Portal检测"""
        from flask import redirect
        return redirect('/')
    
    @app.route('/ncsi.txt')
    def captive_portal_windows_ncsi():
        """Windows NCSI检测"""
        from flask import redirect
        return redirect('/')
    
    @app.route('/redirect')
    def captive_portal_redirect():
        """通用重定向检测"""
        from flask import redirect
        return redirect('/')
    
    @app.route('/success.txt')
    def captive_portal_success():
        """通用成功检测"""
        from flask import redirect
        return redirect('/')
    
    # 前端静态资源 - 必须在精确路由之前注册
    @app.route('/admin/<path:filename>')
    def admin_static(filename):
        """管理后台静态文件"""
        print(f'请求静态文件: /admin/{filename}')  # 调试日志
        return send_from_directory(frontend_dir / 'admin', filename)
    
    @app.route('/vote/<path:filename>')
    def vote_static(filename):
        """投票页面静态文件"""
        return send_from_directory(frontend_dir / 'vote', filename)
    
    @app.route('/lottery/<path:filename>')
    def lottery_static(filename):
        """抽奖页面静态文件"""
        return send_from_directory(frontend_dir / 'lottery', filename)
    
    # 页面路由 - 在静态资源路由之后注册
    @app.route('/admin')
    @app.route('/admin/')
    def admin():
        """管理后台页面 - 需要登录"""
        from flask import session
        # 检查是否已登录
        if not session.get('admin_logged_in'):
            # 未登录，跳转到登录页面
            return send_from_directory(frontend_dir / 'admin', 'login.html')
        # 已登录，显示管理后台
        return send_from_directory(frontend_dir / 'admin', 'index.html')
    
    @app.route('/admin/login')
    def admin_login():
        """管理后台登录页面"""
        return send_from_directory(frontend_dir / 'admin', 'login.html')
    
    @app.route('/vote')
    @app.route('/vote/')
    def vote():
        """投票页面"""
        return send_from_directory(frontend_dir / 'vote', 'index.html')
    
    @app.route('/lottery')
    @app.route('/lottery/')
    def lottery():
        """抽奖页面"""
        return send_from_directory(frontend_dir / 'lottery', 'index.html')
    
    # WebSocket事件
    @socketio.on('connect')
    def handle_connect():
        """客户端连接"""
        print('客户端已连接')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开"""
        print('客户端已断开')
    
    return app


def broadcast_vote_update(candidate_data):
    """
    广播投票更新
    
    Args:
        candidate_data: 候选人数据
    """
    socketio.emit('vote_update', candidate_data, namespace='/')


def broadcast_lottery_result(lottery_data):
    """
    广播抽奖结果
    
    Args:
        lottery_data: 抽奖数据
    """
    socketio.emit('lottery_result', lottery_data, namespace='/')
