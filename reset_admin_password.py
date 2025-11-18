"""
重置管理员密码
"""
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置环境变量
os.environ['FLASK_APP'] = 'run.py'

from backend.app import create_app
from backend.models import db, AdminUser


def reset_admin_password():
    """重置管理员密码"""
    print("=" * 60)
    print("重置管理员密码")
    print("=" * 60)
    
    # 创建应用
    app = create_app('development')
    
    with app.app_context():
        # 检查数据库中的管理员用户
        print("\n[1] 检查数据库中的管理员用户...")
        admin_username = app.config.get('ADMIN_USERNAME', 'admin')
        admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
        
        admin_user = AdminUser.query.filter_by(username=admin_username).first()
        
        if admin_user:
            print(f"  找到管理员用户: {admin_user.username}")
            print(f"  当前密码哈希: {admin_user.password_hash}")
            
            # 重置密码
            print(f"  重置密码为: {admin_password}")
            admin_user.set_password(admin_password)
            db.session.commit()
            
            print("  ✓ 密码重置成功")
            
            # 验证新密码
            if admin_user.check_password(admin_password):
                print("  ✓ 新密码验证成功")
            else:
                print("  ✗ 新密码验证失败")
        else:
            print(f"  未找到管理员用户: {admin_username}")
            print("  创建新的管理员用户...")
            
            # 创建新的管理员用户
            admin_user = AdminUser(username=admin_username)
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            
            print("  ✓ 管理员用户创建成功")
            
            # 验证新用户
            if admin_user.check_password(admin_password):
                print("  ✓ 新用户密码验证成功")
            else:
                print("  ✗ 新用户密码验证失败")
    
    print("\n" + "=" * 60)
    print("密码重置完成")
    print("=" * 60)
    print(f"用户名: {admin_username}")
    print(f"密码: {admin_password}")
    print("请使用以上信息登录管理后台")


if __name__ == '__main__':
    try:
        reset_admin_password()
    except Exception as e:
        print(f"重置密码出错: {str(e)}")
        import traceback
        traceback.print_exc()