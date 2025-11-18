"""
文件处理服务

版权所有 (c) 2025 赵宏宇
"""
import os
import pandas as pd
from typing import List, Dict, Optional
from werkzeug.utils import secure_filename
from backend.models import db, Candidate


class FileService:
    """文件处理服务类"""
    
    @staticmethod
    def allowed_file(filename: str, allowed_extensions: set) -> bool:
        """
        检查文件扩展名是否允许
        
        Args:
            filename: 文件名
            allowed_extensions: 允许的扩展名集合
            
        Returns:
            是否允许
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    @staticmethod
    def save_uploaded_file(file, upload_folder: str, candidate_id: int = None) -> Optional[str]:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件对象
            upload_folder: 上传目录
            candidate_id: 候选人ID，用于生成文件名
            
        Returns:
            保存的文件路径，失败返回None
        """
        try:
            if file and file.filename:
                filename = secure_filename(file.filename)
                # 添加时间戳避免重名
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # 如果提供了候选人ID，使用ID+时间戳作为文件名
                if candidate_id is not None:
                    name, ext = os.path.splitext(filename)
                    filename = f'{candidate_id}_{timestamp}{ext}'
                else:
                    name, ext = os.path.splitext(filename)
                    filename = f'{name}_{timestamp}{ext}'
                
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                return filepath
            return None
        except Exception as e:
            print(f'保存文件失败: {str(e)}')
            return None
    
    @staticmethod
    def import_candidates_from_excel(filepath: str) -> Dict[str, any]:
        """
        从Excel文件导入候选人
        
        Excel格式要求:
        - 第一列: 姓名（必填）
        - 第二列: 描述（可选）
        
        Args:
            filepath: Excel文件路径
            
        Returns:
            导入结果
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(filepath)
            
            if df.empty:
                return {
                    'success': False,
                    'message': 'Excel文件为空'
                }
            
            # 获取列名
            columns = df.columns.tolist()
            if len(columns) < 1:
                return {
                    'success': False,
                    'message': 'Excel格式错误，至少需要一列（姓名）'
                }
            
            success_count = 0
            error_list = []
            
            # 逐行处理
            for index, row in df.iterrows():
                try:
                    name = str(row[columns[0]]).strip()
                    if not name or name == 'nan':
                        continue
                    
                    description = ''
                    if len(columns) > 1:
                        desc = str(row[columns[1]])
                        if desc != 'nan':
                            description = desc.strip()
                    
                    # 检查是否已存在
                    existing = Candidate.query.filter_by(name=name).first()
                    if existing:
                        error_list.append(f'第{index+2}行: {name} 已存在')
                        continue
                    
                    # 创建候选人
                    candidate = Candidate(
                        name=name,
                        description=description
                    )
                    db.session.add(candidate)
                    success_count += 1
                    
                except Exception as e:
                    error_list.append(f'第{index+2}行: {str(e)}')
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'成功导入{success_count}个候选人',
                'count': success_count,
                'errors': error_list
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'导入失败: {str(e)}'
            }
    
    @staticmethod
    def import_candidates_from_csv(filepath: str) -> Dict[str, any]:
        """
        从CSV文件导入候选人
        
        Args:
            filepath: CSV文件路径
            
        Returns:
            导入结果
        """
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except:
                    continue
            
            if df is None:
                return {
                    'success': False,
                    'message': 'CSV文件编码不支持'
                }
            
            if df.empty:
                return {
                    'success': False,
                    'message': 'CSV文件为空'
                }
            
            # 与Excel相同的处理逻辑
            columns = df.columns.tolist()
            if len(columns) < 1:
                return {
                    'success': False,
                    'message': 'CSV格式错误，至少需要一列（姓名）'
                }
            
            success_count = 0
            error_list = []
            
            for index, row in df.iterrows():
                try:
                    name = str(row[columns[0]]).strip()
                    if not name or name == 'nan':
                        continue
                    
                    description = ''
                    if len(columns) > 1:
                        desc = str(row[columns[1]])
                        if desc != 'nan':
                            description = desc.strip()
                    
                    existing = Candidate.query.filter_by(name=name).first()
                    if existing:
                        error_list.append(f'第{index+2}行: {name} 已存在')
                        continue
                    
                    candidate = Candidate(
                        name=name,
                        description=description
                    )
                    db.session.add(candidate)
                    success_count += 1
                    
                except Exception as e:
                    error_list.append(f'第{index+2}行: {str(e)}')
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'成功导入{success_count}个候选人',
                'count': success_count,
                'errors': error_list
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'导入失败: {str(e)}'
            }
    
    @staticmethod
    def export_results_to_excel(filepath: str) -> Dict[str, any]:
        """
        导出投票结果到Excel
        
        Args:
            filepath: 导出文件路径
            
        Returns:
            导出结果
        """
        try:
            candidates = Candidate.query.order_by(Candidate.votes.desc()).all()
            
            data = []
            for idx, candidate in enumerate(candidates, 1):
                data.append({
                    '排名': idx,
                    '姓名': candidate.name,
                    '得票数': candidate.votes,
                    '描述': candidate.description or ''
                })
            
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False)
            
            return {
                'success': True,
                'message': '导出成功',
                'filepath': filepath
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'导出失败: {str(e)}'
            }
