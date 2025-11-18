"""
应用启动脚本
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
from backend.app import create_app, socketio

# 加载环境变量
load_dotenv()

# 创建应用
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # 获取配置
    host = app.config['HOST']
    port = app.config['PORT']
    debug = app.config['DEBUG']
    
    print('=' * 60)
    print('投票抽奖系统启动中...')
    print('=' * 60)
    print(f'访问地址: http://{host}:{port}')
    print(f'管理后台: http://{host}:{port}/admin')
    print(f'投票页面: http://{host}:{port}/vote')
    print(f'抽奖页面: http://{host}:{port}/lottery')
    print('=' * 60)
    
    # 启动应用（使用SocketIO）
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=False
    )