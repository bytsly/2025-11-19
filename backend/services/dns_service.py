"""
DNS劫持服务 - 用于Captive Portal强制门户
"""
import socket
import threading
import struct
from typing import Optional


class DNSServer:
    """简单的DNS服务器，用于劫持所有DNS请求指向热点IP"""
    
    def __init__(self, redirect_ip: str = '192.168.137.1', port: int = 53):
        """
        初始化DNS服务器
        
        Args:
            redirect_ip: 要重定向到的IP地址（热点IP）
            port: DNS端口，默认53
        """
        self.redirect_ip = redirect_ip
        self.port = port
        self.running = False
        self.server_thread = None
        self.socket = None
        
    def start(self):
        """启动DNS服务器"""
        if self.running:
            return {'success': False, 'message': 'DNS服务器已在运行'}
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            
            self.running = True
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            return {
                'success': True,
                'message': f'DNS服务器已启动，监听端口 {self.port}',
                'redirect_ip': self.redirect_ip
            }
        except Exception as e:
            self.running = False
            return {
                'success': False,
                'message': f'启动DNS服务器失败: {str(e)}'
            }
    
    def stop(self):
        """停止DNS服务器"""
        if not self.running:
            return {'success': False, 'message': 'DNS服务器未运行'}
        
        try:
            self.running = False
            if self.socket:
                self.socket.close()
            
            return {
                'success': True,
                'message': 'DNS服务器已停止'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'停止DNS服务器失败: {str(e)}'
            }
    
    def _run_server(self):
        """运行DNS服务器主循环"""
        print(f'🌐 DNS服务器启动，劫持所有请求到 {self.redirect_ip}')
        
        while self.running:
            try:
                if self.socket is None:
                    break
                    
                # 接收DNS查询
                data, addr = self.socket.recvfrom(512)
                
                # 解析查询的域名（用于日志）
                domain = self._parse_domain(data)
                
                # 生成DNS响应，将所有域名解析到热点IP
                response = self._build_response(data, self.redirect_ip)
                
                # 发送响应
                self.socket.sendto(response, addr)
                
                # 打印日志（仅记录非系统域名）
                if domain and not any(x in domain.lower() for x in [
                    'msftconnecttest', 'msftncsi', 'google', 'apple', 'android',
                    'connectivitycheck', 'hicloud', 'microsoft', 'ncsi', ' captive'
                ]):
                    print(f'📡 DNS劫持: {domain} -> {self.redirect_ip} (来自 {addr[0]})')
                
            except Exception as e:
                if self.running:  # 只在运行时报错
                    print(f'DNS服务器错误: {str(e)}')
    
    def _parse_domain(self, data: bytes) -> Optional[str]:
        """
        解析DNS查询中的域名
        
        Args:
            data: DNS查询数据包
            
        Returns:
            域名字符串
        """
        try:
            # DNS查询格式：12字节header + 域名（QNAME）+ 4字节type/class
            # 跳过12字节header
            pos = 12
            labels = []
            
            while pos < len(data):
                length = data[pos]
                if length == 0:
                    break
                pos += 1
                labels.append(data[pos:pos + length].decode('utf-8'))
                pos += length
            
            return '.'.join(labels) if labels else None
        except:
            return None
    
    def _build_response(self, query: bytes, ip: str) -> bytes:
        """
        构建DNS响应包
        
        Args:
            query: 原始DNS查询包
            ip: 要返回的IP地址
            
        Returns:
            DNS响应数据包
        """
        try:
            # 复制查询包作为基础
            response = bytearray(query)
            
            # 修改header flags
            # QR=1(响应), Opcode=0(标准查询), AA=1(权威), TC=0, RD=1, RA=1, Z=0, RCODE=0(无错误)
            response[2] = 0x81  # 10000001
            response[3] = 0x80  # 10000000
            
            # ANCOUNT = 1（1个回答）
            response[6] = 0x00
            response[7] = 0x01
            
            # 添加回答部分
            # NAME: C00C（指向查询部分的域名，使用压缩指针）
            answer = bytes([0xC0, 0x0C])
            
            # TYPE: A记录(0x0001)
            answer += bytes([0x00, 0x01])
            
            # CLASS: IN(0x0001)
            answer += bytes([0x00, 0x01])
            
            # TTL: 60秒
            answer += struct.pack('>I', 60)
            
            # RDLENGTH: 4字节（IPv4地址长度）
            answer += bytes([0x00, 0x04])
            
            # RDATA: IP地址
            ip_parts = [int(x) for x in ip.split('.')]
            answer += bytes(ip_parts)
            
            # 添加到响应包
            response += answer
            
            return bytes(response)
        except Exception as e:
            print(f'构建DNS响应失败: {str(e)}')
            return query  # 返回原查询包


# 全局DNS服务器实例
_dns_server = None


def get_dns_server(redirect_ip: str = '192.168.137.1') -> DNSServer:
    """
    获取DNS服务器单例
    
    Args:
        redirect_ip: 重定向IP地址
        
    Returns:
        DNS服务器实例
    """
    global _dns_server
    if _dns_server is None:
        _dns_server = DNSServer(redirect_ip)
    else:
        # 更新重定向IP
        _dns_server.redirect_ip = redirect_ip
    return _dns_server


def start_dns_server(redirect_ip: str = '192.168.137.1') -> dict:
    """
    启动DNS劫持服务器
    
    Args:
        redirect_ip: 重定向到的IP地址
        
    Returns:
        结果字典
    """
    dns = get_dns_server(redirect_ip)
    return dns.start()


def stop_dns_server() -> dict:
    """
    停止DNS劫持服务器
    
    Returns:
        结果字典
    """
    global _dns_server
    if _dns_server is None:
        return {'success': False, 'message': 'DNS服务器未初始化'}
    return _dns_server.stop()


def is_dns_running() -> bool:
    """
    检查DNS服务器是否运行中
    
    Returns:
        True表示运行中
    """
    global _dns_server
    return _dns_server is not None and _dns_server.running