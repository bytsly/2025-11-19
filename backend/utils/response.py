"""
响应帮助函数
"""
from flask import jsonify
from typing import Any, Dict


def success_response(data: Any = None, message: str = '操作成功') -> Dict:
    """
    成功响应
    
    Args:
        data: 响应数据
        message: 提示消息
        
    Returns:
        响应字典
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response)


def error_response(message: str = '操作失败', code: int = 400) -> tuple:
    """
    错误响应
    
    Args:
        message: 错误消息
        code: HTTP状态码
        
    Returns:
        响应元组
    """
    response = {
        'success': False,
        'message': message
    }
    
    return jsonify(response), code


def paginate_response(items: list, page: int, per_page: int, total: int) -> Dict:
    """
    分页响应
    
    Args:
        items: 数据列表
        page: 当前页
        per_page: 每页数量
        total: 总数
        
    Returns:
        分页响应字典
    """
    return {
        'success': True,
        'data': {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }
