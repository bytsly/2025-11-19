"""
抽奖路由

版权所有 (c) 2025 赵宏宇
"""
from flask import Blueprint
from backend.models import Candidate
from backend.services.lottery_service import LotteryService
from backend.utils.response import success_response, error_response

lottery_bp = Blueprint('lottery', __name__, url_prefix='/api/lottery')


@lottery_bp.route('/candidates', methods=['GET'])
def get_candidates():
    """获取所有候选人（用于抽奖展示）"""
    try:
        candidates = Candidate.query.all()
        return success_response([c.to_dict() for c in candidates])
    except Exception as e:
        return error_response(f'获取候选人列表失败: {str(e)}')


@lottery_bp.route('/history', methods=['GET'])
def get_history():
    """获取抽奖历史（公开）"""
    try:
        history = LotteryService.get_lottery_history()
        return success_response(history)
    except Exception as e:
        return error_response(f'获取历史失败: {str(e)}')
