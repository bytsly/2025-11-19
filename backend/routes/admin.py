"""
管理后台路由

版权所有 (c) 2025 赵宏宇
"""
from flask import Blueprint, request, send_from_directory, current_app, session, redirect, url_for
from functools import wraps
from backend.models import db, Candidate, VoteConfig
from backend.services.hotspot_service import HotspotService
from backend.services.qrcode_service import QRCodeService
from backend.services.file_service import FileService
from backend.services.vote_service import VoteService
from backend.services.lottery_service import LotteryService
from backend.utils.response import success_response, error_response
import os
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ============ 登录验证装饰器 ============

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return error_response('未登录，请先登录', 401)
        return f(*args, **kwargs)
    return decorated_function


# ============ 登录管理 ============

@admin_bp.route('/login', methods=['POST'])
def login():
    """管理员登录"""
    try:
        from backend.models import AdminUser
        
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return error_response('用户名和密码不能为空')
        
        # 验证账号密码
        admin_username = current_app.config['ADMIN_USERNAME']
        
        # 首先检查是否是配置中的用户名
        if username == admin_username:
            # 从数据库获取用户
            admin_user = AdminUser.query.filter_by(username=username).first()
            
            # 如果数据库中没有用户，使用配置文件中的密码
            if not admin_user:
                admin_password = current_app.config['ADMIN_PASSWORD']
                if password == admin_password:
                    # 登录成功，设置session
                    session['admin_logged_in'] = True
                    session['admin_username'] = username
                    return success_response({
                        'username': username
                    }, '登录成功')
            else:
                # 使用数据库中的密码验证
                if admin_user.check_password(password):
                    # 登录成功，设置session
                    session['admin_logged_in'] = True
                    session['admin_username'] = username
                    return success_response({
                        'username': username
                    }, '登录成功')
        
        return error_response('用户名或密码错误')
    
    except Exception as e:
        return error_response(f'登录失败: {str(e)}')


@admin_bp.route('/logout', methods=['POST'])
def logout():
    """管理员登出"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return success_response(message='登出成功')


@admin_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """检查登录状态"""
    if session.get('admin_logged_in'):
        return success_response({
            'logged_in': True,
            'username': session.get('admin_username')
        })
    else:
        return success_response({
            'logged_in': False
        })


# ============ 候选人管理 ============

@admin_bp.route('/candidates', methods=['GET'])
@login_required
def get_candidates():
    """获取所有候选人"""
    try:
        candidates = Candidate.query.order_by(Candidate.votes.desc()).all()
        return success_response([c.to_dict() for c in candidates])
    except Exception as e:
        return error_response(f'获取候选人列表失败: {str(e)}')


@admin_bp.route('/candidates', methods=['POST'])
@login_required
def add_candidate():
    """添加候选人"""
    try:
        # 验证请求数据
        if not request.is_json:
            return error_response('请求数据必须是JSON格式')
        
        data = request.get_json()
        if not data:
            return error_response('无效的JSON数据')
        
        name = data.get('name', '').strip()
        
        if not name:
            return error_response('姓名不能为空')
        
        # 检查重名
        existing = Candidate.query.filter_by(name=name).first()
        if existing:
            return error_response('该候选人已存在')
        
        # 处理photo_path，避免None值导致问题
        photo_path = data.get('photo_path', '')
        if photo_path is None:
            photo_path = ''
        
        # 处理photo_url，避免None值导致问题
        photo_url = data.get('photo_url', '')
        if photo_url is None:
            photo_url = ''
        
        # 优先使用photo_path，如果没有则使用photo_url
        final_photo_path = photo_path or photo_url
        
        # 使用photo_path作为图片路径
        candidate = Candidate(
            name=name,
            description=data.get('description', ''),
            photo_path=final_photo_path
        )
        
        db.session.add(candidate)
        db.session.commit()
        
        return success_response(candidate.to_dict(), '添加成功')
        
    except ValueError as ve:
        db.session.rollback()
        return error_response(f'数据格式错误: {str(ve)}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'添加失败: {str(e)}')


@admin_bp.route('/candidates/<int:candidate_id>', methods=['PUT'])
@login_required
def update_candidate(candidate_id):
    """更新候选人"""
    try:
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return error_response('候选人不存在', 404)
        
        # 验证请求数据
        if not request.is_json:
            return error_response('请求数据必须是JSON格式')
        
        data = request.get_json()
        if not data:
            return error_response('无效的JSON数据')
        
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return error_response('姓名不能为空')
            candidate.name = name
        
        if 'description' in data:
            candidate.description = data['description']
        
        if 'photo_path' in data:
            # 处理photo_path，避免None值导致问题
            photo_path = data['photo_path']
            if photo_path is None:
                photo_path = ''
            candidate.photo_path = photo_path
        elif 'photo_url' in data:
            # 如果提供了photo_url但没有photo_path，使用photo_url
            photo_url = data['photo_url']
            if photo_url is not None:
                candidate.photo_path = photo_url
        
        db.session.commit()
        
        return success_response(candidate.to_dict(), '更新成功')
        
    except ValueError as ve:
        db.session.rollback()
        return error_response(f'数据格式错误: {str(ve)}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新失败: {str(e)}')


@admin_bp.route('/candidates/<int:candidate_id>', methods=['DELETE'])
@login_required
def delete_candidate(candidate_id):
    """删除候选人"""
    try:
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return error_response('候选人不存在', 404)
        
        # 如果候选人有照片，尝试删除照片文件
        if candidate.photo_path:
            try:
                # 获取应用配置
                from flask import current_app
                import os
                
                # 构建完整的文件路径
                if candidate.photo_path.startswith('/uploads/'):
                    # 从URL路径转换为文件系统路径
                    relative_path = candidate.photo_path[len('/uploads/'):].replace('/', os.sep)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path)
                    
                    # 检查文件是否存在并删除
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"已删除候选人照片: {file_path}")
            except Exception as e:
                # 记录错误但不中断删除操作
                print(f"删除候选人照片时出错: {str(e)}")
        
        db.session.delete(candidate)
        db.session.commit()
        
        return success_response(message='删除成功')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除失败: {str(e)}')


# ============ 文件上传与导入 ============

@admin_bp.route('/upload/photo', methods=['POST'])
@login_required
def upload_photo():
    """上传照片"""
    try:
        if 'file' not in request.files:
            return error_response('没有上传文件')
        
        file = request.files['file']
        if file.filename == '':
            return error_response('文件名为空')
        
        if not FileService.allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            return error_response('不支持的文件格式')
        
        # 保存文件
        photo_folder = current_app.config['PHOTO_FOLDER']
        filepath = FileService.save_uploaded_file(file, photo_folder)
        
        if not filepath:
            return error_response('文件保存失败')
        
        # 获取相对路径（用于访问）
        relative_path = os.path.relpath(filepath, current_app.config['UPLOAD_FOLDER'])
        photo_url = f'/uploads/{relative_path.replace(os.sep, "/")}'
        
        # 返回photo_path而不是path，与前端保持一致
        return success_response({
            'photo_path': photo_url,  # 使用photo_path字段
            'path': photo_url,  # 保留原有字段以兼容性
            'filename': os.path.basename(filepath)
        }, '上传成功')
        
    except Exception as e:
        return error_response(f'上传失败: {str(e)}')


@admin_bp.route('/import/file', methods=['POST'])
def import_from_file():
    """从文件导入候选人"""
    try:
        if 'file' not in request.files:
            return error_response('没有上传文件')
        
        file = request.files['file']
        if file.filename == '':
            return error_response('文件名为空')
        
        # 检查文件类型
        if not FileService.allowed_file(file.filename, {'xlsx', 'xls', 'csv'}):
            return error_response('不支持的文件格式，请使用Excel或CSV文件')
        
        # 保存文件
        file_folder = current_app.config['FILE_FOLDER']
        filepath = FileService.save_uploaded_file(file, file_folder)
        
        if not filepath:
            return error_response('文件保存失败')
        
        # 根据文件类型导入
        ext = filepath.rsplit('.', 1)[1].lower()
        if ext in ['xlsx', 'xls']:
            result = FileService.import_candidates_from_excel(filepath)
        else:
            result = FileService.import_candidates_from_csv(filepath)
        
        if result['success']:
            return success_response(result, result['message'])
        else:
            return error_response(result['message'])
        
    except Exception as e:
        return error_response(f'导入失败: {str(e)}')


@admin_bp.route('/export/template', methods=['GET'])
def export_template():
    """导出候选人导入模板"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # 创建模板数据
        template_data = [
            {'姓名': '张三', '描述': '优秀员工'},
            {'姓名': '李四', '描述': '销售冠军'},
            {'姓名': '王五', '描述': '技术专家'}
        ]
        
        df = pd.DataFrame(template_data)
        
        # 将DataFrame保存到内存中的Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='候选人导入模板')
        
        # 准备响应
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d')
        # 修复文件名编码问题，使用英文文件名
        filename = f'candidate_import_template_{timestamp}.xlsx'
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        print(f"导出模板错误: {str(e)}")  # 添加调试信息
        import traceback
        traceback.print_exc()  # 打印详细的错误堆栈
        return error_response(f'导出模板失败: {str(e)}')


# ============ 投票管理 ============

@admin_bp.route('/votes/statistics', methods=['GET'])
def get_vote_statistics():
    """获取投票统计"""
    try:
        stats = VoteService.get_vote_statistics()
        if stats['success']:
            return success_response(stats)
        else:
            return error_response(stats['message'])
    except Exception as e:
        return error_response(f'获取统计失败: {str(e)}')


@admin_bp.route('/votes/recent', methods=['GET'])
def get_recent_votes():
    """获取最近投票记录"""
    try:
        limit = request.args.get('limit', 10, type=int)
        votes = VoteService.get_recent_votes(limit)
        return success_response(votes)
    except Exception as e:
        return error_response(f'获取记录失败: {str(e)}')


@admin_bp.route('/votes/reset', methods=['POST'])
@login_required
def reset_votes():
    """重置投票"""
    try:
        result = VoteService.reset_votes()
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'])
    except Exception as e:
        return error_response(f'重置失败: {str(e)}')


@admin_bp.route('/votes/export', methods=['GET'])
def export_votes():
    """导出投票结果"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'vote_results_{timestamp}.xlsx'
        filepath = os.path.join(current_app.config['FILE_FOLDER'], filename)
        
        result = FileService.export_results_to_excel(filepath)
        
        if result['success']:
            return send_from_directory(
                current_app.config['FILE_FOLDER'],
                filename,
                as_attachment=True
            )
        else:
            return error_response(result['message'])
            
    except Exception as e:
        return error_response(f'导出失败: {str(e)}')


# ============ 抽奖管理 ============

@admin_bp.route('/lottery/draw', methods=['POST'])
@login_required
def draw_lottery():
    """执行抽奖"""
    try:
        data = request.get_json()
        count = data.get('count', 1)
        prize_name = data.get('prize_name', '')
        exclude_winners = data.get('exclude_winners', True)
        
        result = LotteryService.draw_lottery(count, prize_name, exclude_winners)
        
        if result['success']:
            return success_response(result, result['message'])
        else:
            return error_response(result['message'])
            
    except Exception as e:
        return error_response(f'抽奖失败: {str(e)}')


@admin_bp.route('/lottery/history', methods=['GET'])
def get_lottery_history():
    """获取抽奖历史"""
    try:
        history = LotteryService.get_lottery_history()
        return success_response(history)
    except Exception as e:
        return error_response(f'获取历史失败: {str(e)}')


@admin_bp.route('/lottery/available', methods=['GET'])
def get_available_lottery_count():
    """获取可抽奖人数"""
    try:
        exclude_winners = request.args.get('exclude_winners', 'true').lower() == 'true'
        count = LotteryService.get_available_count(exclude_winners)
        return success_response({'count': count})
    except Exception as e:
        return error_response(f'获取人数失败: {str(e)}')


@admin_bp.route('/lottery/reset', methods=['POST'])
@login_required
def reset_lottery():
    """重置抽奖"""
    try:
        result = LotteryService.reset_lottery()
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'])
    except Exception as e:
        return error_response(f'重置失败: {str(e)}')


# 获取和保存抽奖设置的路由
@admin_bp.route('/lottery/settings', methods=['POST'])
@login_required
def save_lottery_settings():
    """保存抽奖设置"""
    try:
        data = request.get_json()
        count = data.get('count', 1)
        prize_name = data.get('prize_name', '')
        exclude_winners = data.get('exclude_winners', True)
        rounds = data.get('rounds', 1)  # 获取轮数信息
        
        # 验证输入
        if not prize_name:
            return error_response('奖项名称不能为空')
        
        if count < 1:
            return error_response('每次抽奖人数必须大于0')
            
        if rounds < 1:
            return error_response('抽奖轮数必须大于0')
        
        # 保存设置到会话中，同时保存已抽奖轮数和总轮数
        from flask import session
        session['lottery_settings'] = {
            'count': count,
            'prize_name': prize_name,
            'exclude_winners': exclude_winners,
            'rounds': rounds,
            'completed_rounds': 0  # 已完成的轮数，初始为0
        }
        
        return success_response(message='抽奖设置已保存')
    except Exception as e:
        return error_response(f'保存设置失败: {str(e)}')


@admin_bp.route('/lottery/settings', methods=['GET'])
@login_required
def get_lottery_settings():
    """获取抽奖设置"""
    try:
        # 从会话中获取设置，如果没有则使用默认值
        from flask import session
        settings = session.get('lottery_settings', {
            'count': 1,
            'prize_name': '幸运奖',
            'exclude_winners': True,
            'rounds': 1,
            'completed_rounds': 0
        })
        return success_response(settings)
    except Exception as e:
        return error_response(f'获取设置失败: {str(e)}')


# ============ 网络与系统 ============

@admin_bp.route('/hotspot/create', methods=['POST'])
@login_required
def create_hotspot():
    """创建WiFi热点"""
    try:
        data = request.get_json()
        ssid = data.get('ssid', current_app.config['HOTSPOT_SSID'])
        password = data.get('password', current_app.config['HOTSPOT_PASSWORD'])
        
        result = HotspotService.create_hotspot(ssid, password)
        
        if result['success']:
            return success_response(result, result['message'])
        else:
            return error_response(result['message'])
            
    except Exception as e:
        return error_response(f'创建热点失败: {str(e)}')


@admin_bp.route('/hotspot/stop', methods=['POST'])
@login_required
def stop_hotspot():
    """停止WiFi热点"""
    try:
        result = HotspotService.stop_hotspot()
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'])
            
    except Exception as e:
        return error_response(f'停止热点失败: {str(e)}')


@admin_bp.route('/hotspot/status', methods=['GET'])
def get_hotspot_status():
    """获取热点状态"""
    try:
        result = HotspotService.get_hotspot_status()
        return success_response(result)
    except Exception as e:
        return error_response(f'获取状态失败: {str(e)}')


@admin_bp.route('/hotspot/sharing/enable', methods=['POST'])
@login_required
def enable_internet_sharing():
    """启用外网共享"""
    try:
        result = HotspotService.enable_internet_sharing(True)
        
        if result['success']:
            return success_response(result, result['message'])
        else:
            return error_response(result['message'])
            
    except Exception as e:
        return error_response(f'启用共享失败: {str(e)}')


@admin_bp.route('/hotspot/sharing/disable', methods=['POST'])
@login_required
def disable_internet_sharing():
    """禁用外网共享"""
    try:
        result = HotspotService.enable_internet_sharing(False)
        
        if result['success']:
            return success_response(result, result['message'])
        else:
            return error_response(result['message'])
            
    except Exception as e:
        return error_response(f'禁用共享失败: {str(e)}')


@admin_bp.route('/hotspot/sharing/status', methods=['GET'])
def get_sharing_status():
    """获取共享状态"""
    try:
        result = HotspotService.get_sharing_status()
        return success_response(result)
    except Exception as e:
        return error_response(f'获取共享状态失败: {str(e)}')


@admin_bp.route('/qrcode/vote', methods=['GET'])
def get_vote_qrcode():
    """获取投票二维码"""
    try:
        # 优先使用热点IP（如果热点已启动）
        hotspot_status = HotspotService.get_hotspot_status()
        if hotspot_status.get('running', False):
            ip = HotspotService.get_hotspot_ip()
        else:
            ip = HotspotService.get_local_ip()
        
        port = current_app.config['PORT']
        qr_image = QRCodeService.generate_vote_qrcode(ip, port)
        
        if qr_image:
            return success_response({
                'qrcode': qr_image,
                'url': f'http://{ip}:{port}/vote',
                'ip': ip,
                'using_hotspot': hotspot_status.get('running', False)
            })
        else:
            return error_response('生成二维码失败')
            
    except Exception as e:
        return error_response(f'生成失败: {str(e)}')


@admin_bp.route('/qrcode/lottery', methods=['GET'])
def get_lottery_qrcode():
    """获取抽奖二维码"""
    try:
        # 优先使用热点IP（如果热点已启动）
        hotspot_status = HotspotService.get_hotspot_status()
        if hotspot_status.get('running', False):
            ip = HotspotService.get_hotspot_ip()
        else:
            ip = HotspotService.get_local_ip()
        
        port = current_app.config['PORT']
        qr_image = QRCodeService.generate_lottery_qrcode(ip, port)
        
        if qr_image:
            return success_response({
                'qrcode': qr_image,
                'url': f'http://{ip}:{port}/lottery',
                'ip': ip,
                'using_hotspot': hotspot_status.get('running', False)
            })
        else:
            return error_response('生成二维码失败')
            
    except Exception as e:
        return error_response(f'生成失败: {str(e)}')


@admin_bp.route('/qrcode/admin', methods=['GET'])
def get_admin_qrcode():
    """获取管理后台二维码"""
    try:
        # 优先使用热点IP（如果热点已启动）
        hotspot_status = HotspotService.get_hotspot_status()
        if hotspot_status.get('running', False):
            ip = HotspotService.get_hotspot_ip()
        else:
            ip = HotspotService.get_local_ip()
        
        port = current_app.config['PORT']
        qr_image = QRCodeService.generate_admin_qrcode(ip, port)
        
        if qr_image:
            return success_response({
                'qrcode': qr_image,
                'url': f'http://{ip}:{port}/admin',
                'ip': ip,
                'using_hotspot': hotspot_status.get('running', False)
            })
        else:
            return error_response('生成二维码失败')
            
    except Exception as e:
        return error_response(f'生成失败: {str(e)}')


@admin_bp.route('/qrcode/wifi-guide', methods=['GET'])
def get_wifi_guide_qrcode():
    """获取WiFi引导页面二维码（一码通方案）"""
    try:
        # 获取参数
        password = request.args.get('password', current_app.config['HOTSPOT_PASSWORD'])
        ssid = request.args.get('ssid', current_app.config['HOTSPOT_SSID'])
        
        # 优先使用热点IP（如果热点已启动）
        hotspot_status = HotspotService.get_hotspot_status()
        if hotspot_status.get('running', False):
            ip = HotspotService.get_hotspot_ip()
        else:
            ip = HotspotService.get_local_ip()
        
        port = current_app.config['PORT']
        
        # 生成WiFi引导页面URL
        guide_url = f'http://{ip}:{port}/wifi-guide?ssid={ssid}&password={password}'
        
        # 生成二维码
        qr_image = QRCodeService.generate_qrcode(guide_url)
        
        if qr_image:
            return success_response({
                'qrcode': qr_image,
                'url': guide_url,
                'ssid': ssid,
                'type': 'wifi_guide',
                'instruction': '扫描此二维码，查看WiFi连接信息并引导投票'
            })
        else:
            return error_response('生成二维码失败')
            
    except Exception as e:
        return error_response(f'生成失败: {str(e)}')


@admin_bp.route('/qrcode/wifi-vote', methods=['GET'])
def get_wifi_vote_combo_qrcode():
    """获取WiFi+投票组合二维码"""
    try:
        # 获取参数
        password = request.args.get('password', current_app.config['HOTSPOT_PASSWORD'])
        ssid = request.args.get('ssid', current_app.config['HOTSPOT_SSID'])
        
        # 优先使用热点IP（如果热点已启动）
        hotspot_status = HotspotService.get_hotspot_status()
        if hotspot_status.get('running', False):
            ip = HotspotService.get_hotspot_ip()
        else:
            ip = HotspotService.get_local_ip()
        
        port = current_app.config['PORT']
        
        # 生成投票页面URL
        vote_url = f'http://{ip}:{port}/vote'
        
        # 生成组合二维码
        combo_data = QRCodeService.generate_wifi_vote_combo_qrcode(ssid, password, vote_url)
        
        if combo_data:
            combo_data.update({
                'vote_url': vote_url,
                'type': 'wifi_vote_combo'
            })
            return success_response(combo_data)
        else:
            return error_response('生成二维码失败')
            
    except Exception as e:
        return error_response(f'生成失败: {str(e)}')


@admin_bp.route('/qrcode/wifi', methods=['GET'])
def get_wifi_qrcode():
    """获取WiFi连接二维码"""
    try:
        # 获取参数
        password = request.args.get('password', current_app.config['HOTSPOT_PASSWORD'])
        ssid = request.args.get('ssid', current_app.config['HOTSPOT_SSID'])
        
        # 生成WiFi二维码
        qr_image = QRCodeService.generate_wifi_qrcode(ssid, password)
        
        if qr_image:
            return success_response({
                'qrcode': qr_image,
                'ssid': ssid,
                'type': 'wifi'
            })
        else:
            return error_response('生成二维码失败')
            
    except Exception as e:
        return error_response(f'生成失败: {str(e)}')


@admin_bp.route('/system/info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    try:
        # 获取热点状态
        hotspot_status = HotspotService.get_hotspot_status()
        
        # 根据热点状态选择IP
        if hotspot_status.get('running', False):
            # 热点已启动，使用热点IP
            hotspot_ip = HotspotService.get_hotspot_ip()
            local_ip = HotspotService.get_local_ip()
            primary_ip = hotspot_ip
        else:
            # 热点未启动，使用局域网IP
            local_ip = HotspotService.get_local_ip()
            hotspot_ip = None
            primary_ip = local_ip
        
        port = current_app.config['PORT']
        
        return success_response({
            'ip': primary_ip,
            'local_ip': local_ip,
            'hotspot_ip': hotspot_ip,
            'port': port,
            'vote_url': f'http://{primary_ip}:{port}/vote',
            'lottery_url': f'http://{primary_ip}:{port}/lottery',
            'admin_url': f'http://{primary_ip}:{port}/admin',
            'hotspot_running': hotspot_status.get('running', False),
            'hotspot_ssid': hotspot_status.get('ssid')
        })
        
    except Exception as e:
        return error_response(f'获取信息失败: {str(e)}')


@admin_bp.route('/system/network-diag', methods=['GET'])
@login_required
def network_diagnosis():
    """网络诊断"""
    try:
        # 移除网络诊断相关代码
        return error_response('网络诊断功能已移除')
        
    except Exception as e:
        return error_response(f'诊断失败: {str(e)}')


@admin_bp.route('/system/network-troubleshoot', methods=['POST'])
@login_required
def network_troubleshoot():
    """网络故障排除"""
    try:
        # 移除网络故障排除相关代码
        return error_response('网络故障排除功能已移除')
        
    except Exception as e:
        return error_response(f'故障排除失败: {str(e)}')


@admin_bp.route('/system/fix-dhcp', methods=['POST'])
@login_required
def fix_dhcp_service():
    """修复DHCP服务"""
    try:
        # 移除DHCP修复相关代码
        return error_response('DHCP修复功能已移除')
        
    except Exception as e:
        return error_response(f'DHCP修复失败: {str(e)}')


@admin_bp.route('/system/fix-hotspot-network', methods=['POST'])
@login_required
def fix_hotspot_network():
    """修复热点网络配置"""
    try:
        # 移除热点网络配置修复相关代码
        return error_response('热点网络配置修复功能已移除')
        
    except Exception as e:
        return error_response(f'热点网络配置修复失败: {str(e)}')


# ============ 账户管理 ============

@admin_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改管理员密码"""
    try:
        from backend.models import AdminUser
        
        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        if not current_password or not new_password or not confirm_password:
            return error_response('所有字段都不能为空')
        
        if new_password != confirm_password:
            return error_response('新密码和确认密码不一致')
        
        if len(new_password) < 6:
            return error_response('新密码长度至少为6位')
        
        # 获取管理员用户
        admin_username = current_app.config['ADMIN_USERNAME']
        admin_user = AdminUser.query.filter_by(username=admin_username).first()
        
        # 如果数据库中没有管理员用户，创建一个
        if not admin_user:
            admin_user = AdminUser(username=admin_username)
            admin_user.set_password(new_password)
            db.session.add(admin_user)
            db.session.commit()
            # 更新配置中的密码
            current_app.config['ADMIN_PASSWORD'] = new_password
            # 更新session中的用户名
            session['admin_username'] = admin_username
            return success_response(message='密码修改成功，请记住新密码')
        
        # 验证当前密码
        if not admin_user.check_password(current_password):
            return error_response('当前密码错误')
        
        # 更新密码
        admin_user.set_password(new_password)
        db.session.commit()
        
        # 更新配置中的密码
        current_app.config['ADMIN_PASSWORD'] = new_password
        
        # 更新session中的用户名
        session['admin_username'] = admin_username
        
        return success_response(message='密码修改成功，请记住新密码')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'密码修改失败: {str(e)}')


# ============ 投票配置管理 ============

@admin_bp.route('/vote/config', methods=['GET'])
@login_required
def get_vote_config():
    """获取投票配置"""
    try:
        config = VoteConfig.get_config()
        return success_response(config.to_dict())
    except Exception as e:
        return error_response(f'获取配置失败: {str(e)}')


@admin_bp.route('/vote/config', methods=['PUT'])
@login_required
def update_vote_config():
    """更新投票配置"""
    try:
        data = request.get_json()
        if not data:
            return error_response('无效的JSON数据')
        
        vote_name = data.get('vote_name')
        max_votes_per_user = data.get('max_votes_per_user')
        
        # 验证数据
        if vote_name is not None and not isinstance(vote_name, str):
            return error_response('投票名称必须是字符串')
        
        if max_votes_per_user is not None:
            if not isinstance(max_votes_per_user, int) or max_votes_per_user < 1:
                return error_response('每人最大投票数必须是大于0的整数')
        
        # 更新配置
        config = VoteConfig.update_config(vote_name, max_votes_per_user)
        return success_response(config.to_dict(), '配置更新成功')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新失败: {str(e)}')

