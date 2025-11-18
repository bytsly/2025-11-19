"""入口点脚本，用于PyInstaller打包"""
import sys
import os
import importlib.util
import logging
from typing import Callable, Any
from datetime import datetime

# 配置日志
def setup_logging():
    """设置日志配置"""
    # 创建logs目录（如果不存在）
    log_dir = os.path.join(get_base_path(), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 日志文件路径
    log_file = os.path.join(log_dir, f"vote_lottery_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def get_base_path():
    """获取基础路径，兼容PyInstaller打包环境"""
    try:
        # PyInstaller打包环境
        if getattr(sys, 'frozen', False):
            return getattr(sys, '_MEIPASS', '')  # type: ignore
    except:
        pass
    
    # 开发环境
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except:
        # 如果__file__不可用，使用当前工作目录
        return os.getcwd()

def import_gui_app(logger) -> Callable[[], Any]:
    """导入gui_app模块"""
    base_path = get_base_path()
    logger.info(f"基础路径: {base_path}")
    
    # 确保基础路径在sys.path中
    if base_path not in sys.path:
        sys.path.insert(0, base_path)
        logger.info("已将基础路径添加到sys.path")
    
    # 简化导入方法：直接导入
    try:
        logger.info("尝试导入gui_app模块...")
        from gui_app import VotingLotteryGUI
        import tkinter as tk
        logger.info("成功导入gui_app模块")
        
        # 创建main函数
        def main():
            root = tk.Tk()
            app = VotingLotteryGUI(root)
            root.mainloop()
        
        logger.info("创建main函数成功")
        return main
            
    except Exception as e:
        error_msg = f"导入gui_app模块失败: {e}"
        logger.error(error_msg)
        raise ImportError(error_msg)

if __name__ == "__main__":
    # 设置日志
    logger = setup_logging()
    logger.info("启动投票抽奖系统...")
    print("启动投票抽奖系统...")  # 保持控制台输出
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # 命令行模式
        logger.info("正在启动命令行模式...")
        print("正在启动命令行模式...")
        from backend.app import create_app, socketio
        import os
        from dotenv import load_dotenv
        
        # 加载环境变量
        load_dotenv()
        logger.info("环境变量加载完成")
        
        # 创建应用
        config_name = os.getenv('FLASK_ENV', 'development')
        app = create_app(config_name)
        logger.info(f"应用创建完成，配置: {config_name}")
        
        # 获取配置
        host = app.config.get('HOST', '0.0.0.0')
        port = app.config.get('PORT', '5000')
        logger.info(f"服务器配置 - 主机: {host}, 端口: {port}")
        
        print(f"服务器启动成功！")
        print(f"本地访问: http://localhost:{port}")
        print(f"管理后台: http://localhost:{port}/admin")
        print(f"投票页面: http://localhost:{port}/vote")
        print(f"抽奖页面: http://localhost:{port}/lottery")
        print("按 Ctrl+C 停止服务器")
        
        logger.info("服务器启动成功！")
        logger.info(f"本地访问: http://localhost:{port}")
        logger.info(f"管理后台: http://localhost:{port}/admin")
        logger.info(f"投票页面: http://localhost:{port}/vote")
        logger.info(f"抽奖页面: http://localhost:{port}/lottery")
        
        try:
            # 启动服务器
            logger.info("正在启动服务器...")
            socketio.run(app, host=host, port=int(port), debug=False, use_reloader=False, async_mode='threading')
        except KeyboardInterrupt:
            logger.info("服务器已停止（用户中断）")
        except Exception as e:
            logger.error(f"服务器运行出错: {e}")
    else:
        # GUI模式
        logger.info("正在启动GUI模式...")
        print("正在启动GUI模式...")
        try:
            main_func = import_gui_app(logger)
            logger.info("成功获取main函数，准备执行...")
            print("成功获取main函数，准备执行...")
            # 确保在主线程中执行GUI
            main_func()
            logger.info("GUI主循环已结束")
            print("GUI主循环已结束")
        except Exception as e:
            error_msg = f"启动GUI失败: {e}"
            logger.error(error_msg)
            print(error_msg)
            import traceback
            logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            traceback.print_exc()
            # 避免"lost sys.stdin"错误
            try:
                input("按任意键退出...")
            except:
                print("按任意键退出...")
                import time
                time.sleep(5)