"""
二维码生成服务
"""
import qrcode
from io import BytesIO
import base64
from typing import Optional


class QRCodeService:
    """二维码服务类"""
    
    @staticmethod
    def generate_qrcode(data: str, size: int = 10, border: int = 2) -> Optional[str]:
        """
        生成二维码
        
        Args:
            data: 要编码的数据（通常是URL）
            size: 二维码大小
            border: 边框大小
            
        Returns:
            Base64编码的二维码图片字符串（不包含 data:image 前缀）
        """
        try:
            # 创建二维码对象
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border,
            )
            
            # 添加数据
            qr.add_data(data)
            qr.make(fit=True)
            
            # 生成图片
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为Base64（只返回纯字符串，不包含data:image前缀）
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            print(f'生成二维码失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def generate_vote_qrcode(ip: str, port: int = 5000) -> Optional[str]:
        """
        生成投票页面二维码
        
        Args:
            ip: 服务器IP地址
            port: 服务器端口
            
        Returns:
            Base64编码的二维码图片
        """
        url = f'http://{ip}:{port}/vote'
        return QRCodeService.generate_qrcode(url)
    
    @staticmethod
    def generate_lottery_qrcode(ip: str, port: int = 5000) -> Optional[str]:
        """
        生成抽奖页面二维码
        
        Args:
            ip: 服务器IP地址
            port: 服务器端口
            
        Returns:
            Base64编码的二维码图片
        """
        url = f'http://{ip}:{port}/lottery'
        return QRCodeService.generate_qrcode(url)
    
    @staticmethod
    def generate_admin_qrcode(ip: str, port: int = 5000) -> Optional[str]:
        """
        生成管理后台二维码
        
        Args:
            ip: 服务器IP地址
            port: 服务器端口
            
        Returns:
            Base64编码的二维码图片
        """
        url = f'http://{ip}:{port}/admin'
        return QRCodeService.generate_qrcode(url)
    
    @staticmethod
    def generate_wifi_qrcode(ssid: str, password: str, vote_url: Optional[str] = None) -> Optional[str]:
        """
        生成WiFi连接二维码（支持Android/iOS）
        
        格式: WIFI:T:WPA;S:SSID;P:PASSWORD;;
        T = 加密类型 (WPA/WEP/nopass)
        S = SSID (网络名称)
        P = 密码
        H = 隐藏网络 (true/false)
        
        Args:
            ssid: WiFi名称
            password: WiFi密码
            vote_url: 投票页面URL（可选，如果提供则生成组合二维码）
            
        Returns:
            Base64编码的二维码图片
        """
        try:
            # WiFi二维码标准格式
            # 注意：特殊字符需要转义
            wifi_data = f'WIFI:T:WPA;S:{ssid};P:{password};;'
            
            # 如果提供了投票URL，添加到描述中（仅供参考）
            if vote_url:
                # 注意：WiFi二维码格式不支持直接嵌入URL
                # 这里只生成WiFi连接信息
                pass
            
            return QRCodeService.generate_qrcode(wifi_data, size=10, border=2)
            
        except Exception as e:
            print(f'生成WiFi二维码失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def generate_wifi_vote_combo_qrcode(ssid: str, password: str, vote_url: str) -> dict:
        """
        生成WiFi+投票组合二维码（返回两个二维码）
        
        Args:
            ssid: WiFi名称
            password: WiFi密码
            vote_url: 投票页面URL
            
        Returns:
            包含WiFi二维码和投票二维码的字典
        """
        return {
            'wifi_qrcode': QRCodeService.generate_wifi_qrcode(ssid, password),
            'vote_qrcode': QRCodeService.generate_qrcode(vote_url),
            'wifi_info': f'WiFi: {ssid}',
            'vote_info': f'投票地址: {vote_url}'
        }
