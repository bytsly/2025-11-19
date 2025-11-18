"""
抽奖服务
"""
import random
from typing import Dict, List, Optional, Any
from backend.models import db, Candidate, LotteryRecord


class LotteryService:
    """抽奖服务类"""
    
    @staticmethod
    def draw_lottery(count: int = 1, prize_name: str = '', 
                     exclude_winners: bool = True) -> Dict[str, Any]:
        """
        执行抽奖
        
        Args:
            count: 抽取人数
            prize_name: 奖项名称
            exclude_winners: 是否排除已中奖者
            
        Returns:
            抽奖结果
        """
        try:
            # 获取候选池
            query = Candidate.query
            
            if exclude_winners:
                # 获取已中奖者ID
                winner_ids = LotteryRecord.get_winners_ids()
                if winner_ids:
                    query = query.filter(~Candidate.id.in_(winner_ids))
            
            candidates = query.all()
            
            if len(candidates) == 0:
                return {
                    'success': False,
                    'message': '没有可抽奖的候选人'
                }
            
            if count > len(candidates):
                return {
                    'success': False,
                    'message': f'可抽奖人数不足，当前只有{len(candidates)}人'
                }
            
            # 随机抽取
            winners = random.sample(candidates, count)
            
            # 获取当前轮次
            current_round = LotteryRecord.get_max_round() + 1
            
            # 保存抽奖记录
            winner_list = []
            for winner in winners:
                record = LotteryRecord(
                    candidate_id=winner.id,
                    round=current_round,
                    prize_name=prize_name
                )
                db.session.add(record)
                winner_list.append(winner.to_dict())
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'抽奖成功，共抽取{count}人',
                'round': current_round,
                'prize_name': prize_name,
                'winners': winner_list
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'抽奖失败: {str(e)}'
            }
    
    @staticmethod
    def get_lottery_history() -> List[Dict]:
        """
        获取抽奖历史记录
        
        Returns:
            抽奖记录列表
        """
        try:
            records = LotteryRecord.query.order_by(
                LotteryRecord.round.desc(),
                LotteryRecord.drawn_at.desc()
            ).all()
            
            return [r.to_dict() for r in records]
            
        except Exception as e:
            print(f'获取抽奖历史失败: {str(e)}')
            return []
    
    @staticmethod
    def get_lottery_by_round(round_num: int) -> List[Dict]:
        """
        获取指定轮次的抽奖记录
        
        Args:
            round_num: 轮次号
            
        Returns:
            该轮次的中奖者列表
        """
        try:
            records = LotteryRecord.query.filter_by(round=round_num).all()
            return [r.to_dict() for r in records]
        except Exception as e:
            print(f'获取轮次记录失败: {str(e)}')
            return []
    
    @staticmethod
    def reset_lottery() -> Dict[str, Any]:
        """
        重置抽奖记录
        
        Returns:
            重置结果
        """
        try:
            LotteryRecord.query.delete()
            db.session.commit()
            
            return {
                'success': True,
                'message': '抽奖记录已重置'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'重置失败: {str(e)}'
            }
    
    @staticmethod
    def get_available_count(exclude_winners: bool = True) -> int:
        """
        获取可抽奖人数
        
        Args:
            exclude_winners: 是否排除已中奖者
            
        Returns:
            可抽奖人数
        """
        try:
            query = Candidate.query
            
            if exclude_winners:
                winner_ids = LotteryRecord.get_winners_ids()
                if winner_ids:
                    query = query.filter(~Candidate.id.in_(winner_ids))
            
            return query.count()
            
        except Exception as e:
            print(f'获取可抽奖人数失败: {str(e)}')
            return 0