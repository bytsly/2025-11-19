"""
投票路由

版权所有 (c) 2025 赵宏宇
"""
from flask import Blueprint, request, session
from backend.models import Candidate, VoteConfig
from backend.services.vote_service import VoteService
from backend.utils.response import success_response, error_response

vote_bp = Blueprint('vote', __name__, url_prefix='/api/vote')


@vote_bp.route('/check-admin', methods=['GET'])
def check_admin():
    """检查是否为管理员"""
    try:
        # 从session检查是否为管理员
        is_admin = session.get('admin_logged_in', False)
        
        return success_response({
            'is_admin': is_admin
        })
    except Exception as e:
        return error_response(f'检查失败: {str(e)}')


@vote_bp.route('/candidates', methods=['GET'])
def get_candidates():
    """获取所有候选人（用于投票页面）"""
    try:
        # 检查是否为管理员
        is_admin = session.get('admin_logged_in', False)
        
        candidates = Candidate.query.order_by(Candidate.id).all()
        
        # 如果不是管理员，隐藏得票数
        candidates_data = []
        for candidate in candidates:
            candidate_dict = candidate.to_dict()
            if not is_admin:
                candidate_dict['votes'] = 0  # 对非管理员隐藏得票数
            candidates_data.append(candidate_dict)
            
        return success_response(candidates_data)
    except Exception as e:
        return error_response(f'获取候选人列表失败: {str(e)}')


@vote_bp.route('/submit', methods=['POST'])
def submit_vote():
    """提交投票"""
    try:
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        
        if not candidate_id:
            return error_response('请选择候选人')
        
        # 获取投票者信息
        voter_ip = request.remote_addr or ''
        fingerprint = data.get('fingerprint')
        user_agent = request.headers.get('User-Agent')
        
        # 提交投票
        result = VoteService.submit_vote(
            candidate_id=candidate_id,
            ip=voter_ip,
            fingerprint=fingerprint,
            user_agent=user_agent
        )
        
        if result['success']:
            return success_response(result, result['message'])
        else:
            return error_response(result['message'])
            
    except Exception as e:
        return error_response(f'投票失败: {str(e)}')


@vote_bp.route('/config', methods=['GET'])
def get_vote_config():
    """获取投票配置"""
    try:
        config = VoteConfig.get_config()
        
        # 获取当前用户的投票次数
        voter_ip = request.remote_addr
        fingerprint = request.args.get('fingerprint')
        
        from backend.models import Vote
        user_vote_count = Vote.get_vote_count_by_ip(voter_ip, fingerprint)
        
        return success_response({
            'max_votes_per_user': config.max_votes_per_user,
            'user_vote_count': user_vote_count
        })
        
    except Exception as e:
        return error_response(f'获取配置失败: {str(e)}')


@vote_bp.route('/check', methods=['GET'])
def check_voted():
    """检查是否已投票"""
    try:
        voter_ip = request.remote_addr
        fingerprint = request.args.get('fingerprint')
        
        from backend.models import Vote
        has_voted = Vote.has_voted(voter_ip, fingerprint)
        
        # 获取投票配置
        config = VoteConfig.get_config()
        user_vote_count = Vote.get_vote_count_by_ip(voter_ip, fingerprint)
        
        return success_response({
            'has_voted': has_voted,
            'user_vote_count': user_vote_count,
            'max_votes_per_user': config.max_votes_per_user
        })
        
    except Exception as e:
        return error_response(f'检查失败: {str(e)}')


@vote_bp.route('/my-votes', methods=['GET'])
def get_my_votes():
    """获取当前用户投票的候选人信息（仅返回候选人名称）"""
    try:
        # 检查是否为管理员
        is_admin = session.get('admin_logged_in', False)
        
        # 获取当前用户的投票信息
        voter_ip = request.remote_addr
        fingerprint = request.args.get('fingerprint')
        
        from backend.models import Vote
        if is_admin:
            # 管理员可以看到所有投票记录
            votes = Vote.query.order_by(Vote.voted_at.desc()).limit(50).all()
            # 返回完整投票记录
            return success_response([v.to_dict() for v in votes])
        else:
            # 普通用户只能看到自己投票的候选人名称
            votes = Vote.get_votes_by_user(voter_ip, fingerprint)
            # 只返回候选人名称列表
            candidate_names = [vote.candidate.name if vote.candidate else "未知候选人" for vote in votes]
            return success_response({
                'candidate_names': list(set(candidate_names)),  # 去重
                'vote_count': len(candidate_names)
            })
        
    except Exception as e:
        return error_response(f'获取投票信息失败: {str(e)}')


@vote_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取实时投票统计（公开数据）"""
    try:
        stats = VoteService.get_vote_statistics()
        if stats['success']:
            # 只返回候选人和票数，不返回投票记录
            return success_response({
                'total_votes': stats['total_votes'],
                'candidates': stats['candidates']
            })
        else:
            return error_response(stats['message'])
    except Exception as e:
        return error_response(f'获取统计失败: {str(e)}')
