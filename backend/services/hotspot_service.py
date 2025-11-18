"""
WiFi热点管理服务（仅保留基础热点功能，移除网络共享功能）
"""
import subprocess
import socket
import re
import sys
from typing import Dict, Optional, Any

# 导入DNS服务
try:
    from backend.services.dns_service import start_dns_server, stop_dns_server, is_dns_running
except ImportError:
    # 如果导入失败，提供空实现
    def start_dns_server(redirect_ip: str = '192.168.137.1') -> Dict[str, Any]:
        return {'success': False, 'message': 'DNS服务未安装'}
    def stop_dns_server() -> Dict[str, Any]:
        return {'success': True, 'message': 'DNS服务未启动'}
    def is_dns_running() -> bool:
        return False


class HotspotService:
    """WiFi热点服务类（仅保留基础热点功能）"""
    
    @staticmethod
    def _run_command(cmd: list) -> subprocess.CompletedProcess:
        """
        运行命令并处理编码问题
        
        Args:
            cmd: 命令列表
            
        Returns:
            命令执行结果
        """
        # 首先尝试UTF-8编码
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            # 检查是否成功解码
            if result.stdout and not ('\x00' in result.stdout or '??' in result.stdout):
                return result
        except:
            pass
        
        # 如果UTF-8失败，尝试CP936编码
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp936',
                errors='ignore'
            )
            if result.stdout and not ('\x00' in result.stdout or '??' in result.stdout):
                return result
        except:
            pass
        
        # 如果还是失败，使用二进制模式并尝试多种编码
        result_bin = subprocess.run(cmd, capture_output=True)
        if result_bin.returncode == 0:
            # 尝试多种编码解码
            for encoding in ['utf-8', 'gbk', 'cp936', 'utf-16']:
                try:
                    output = result_bin.stdout.decode(encoding, errors='ignore')
                    if output and not ('\x00' in output or '??' in output):
                        return subprocess.CompletedProcess(
                            args=result_bin.args,
                            returncode=result_bin.returncode,
                            stdout=output,
                            stderr=result_bin.stderr.decode(encoding, errors='ignore') if result_bin.stderr else ''
                        )
                except:
                    continue
        
        # 如果都失败，返回原始结果
        return result_bin
    
    @staticmethod
    def create_hotspot(ssid: str, password: str) -> Dict[str, Any]:
        """
        创建WiFi热点
        
        Args:
            ssid: 热点名称
            password: 热点密码（至少8位）
            
        Returns:
            结果字典，包含success状态和message信息
        """
        try:
            # 检查是否以管理员权限运行
            if sys.platform == 'win32':
                try:
                    result = subprocess.run(['net', 'session'], capture_output=True, text=True)
                    if result.returncode != 0:
                        return {
                            'success': False,
                            'message': '需要以管理员权限运行才能创建WiFi热点'
                        }
                except:
                    pass  # 如果检查失败，继续执行
            
            if len(password) < 8:
                return {
                    'success': False,
                    'message': '密码长度至少为8位'
                }
            
            # 配置热点
            config_cmd = [
                'netsh', 'wlan', 'set', 'hostednetwork',
                f'mode=allow',
                f'ssid={ssid}',
                f'key={password}'
            ]
            
            result = HotspotService._run_command(config_cmd)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'message': f'热点配置失败: {result.stderr}'
                }
            
            # 启动热点
            start_cmd = ['netsh', 'wlan', 'start', 'hostednetwork']
            result = HotspotService._run_command(start_cmd)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'message': f'热点启动失败: {result.stderr}'
                }
            
            # 获取本机IP
            local_ip = HotspotService.get_local_ip()
            
            # 获取热点IP
            hotspot_ip = HotspotService.get_hotspot_ip()
            
            # 启动DNS劫持服务（实现Captive Portal）
            print(f'🌐 正在启动DNS劫持服务...')
            dns_result = start_dns_server(hotspot_ip or '192.168.137.1')
            if dns_result.get('success'):
                print(f'✅ DNS劫持已启动: {dns_result.get("message")}')
            else:
                print(f'⚠️ DNS劫持启动失败: {dns_result.get("message")}')
            
            return {
                'success': True,
                'message': '热点创建成功' + (' (已启动DNS劫持)' if dns_result.get('success') else ' (警告: DNS劫持未启动)'),
                'ssid': ssid,
                'ip': hotspot_ip,  # 使用热点IP而不是本机IP
                'local_ip': local_ip,
                'dns_enabled': dns_result.get('success', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'创建热点异常: {str(e)}'
            }
    
    @staticmethod
    def stop_hotspot() -> Dict[str, Any]:
        """
        停止WiFi热点
        
        Returns:
            结果字典
        """
        try:
            # 先停止DNS服务
            print('🚫 正在停止DNS劫持服务...')
            dns_result = stop_dns_server()
            if dns_result.get('success'):
                print(f'✅ DNS劫持已停止')
            
            # 停止热点
            cmd = ['netsh', 'wlan', 'stop', 'hostednetwork']
            result = HotspotService._run_command(cmd)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'message': f'热点停止失败: {result.stderr}'
                }
            
            return {
                'success': True,
                'message': '热点已停止' + (' (DNS劫持也已停止)' if dns_result.get('success') else '')
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'停止热点异常: {str(e)}'
            }
    
    @staticmethod
    def get_hotspot_status() -> Dict[str, Any]:
        """
        获取热点状态
        
        Returns:
            热点状态信息
        """
        try:
            cmd = ['netsh', 'wlan', 'show', 'hostednetwork']
            result = HotspotService._run_command(cmd)
            
            if result.returncode != 0:
                return {
                    'success': True,
                    'running': False,
                    'message': '无法获取热点状态',
                    'ssid': None
                }
            
            output = result.stdout
            if output is None:
                output = ""
            
            # 解析状态 - 支持中英文系统
            # 中文："已启动" 或 英文："Started"
            is_running = False
            
            # 更精确的状态匹配 - 在"状态"or"Status"行中查找
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                # 中文系统：状态 : 已启动
                if '状态' in line and ('已启动' in line or 'Started' in line):
                    is_running = True
                    break
                # 英文系统：Status : Started
                if 'Status' in line and ('Started' in line or '已启动' in line):
                    is_running = True
                    break
            
            # 提取SSID - 支持中英文
            ssid = None
            # 中文系统： SSID 名称              :“VotingSystem”
            # 注意：使用的是中文引号“”，不是普通引号""
            ssid_match = re.search(r'SSID\s+名称\s+:“([^”]+)”', output)
            if not ssid_match:
                # 普通引号版本
                ssid_match = re.search(r'SSID\s+名称\s+:"([^"]+)"', output)
            if not ssid_match:
                # 英文系统
                ssid_match = re.search(r'SSID\s+name\s*:\s*"([^"]+)"', output, re.IGNORECASE)
            if not ssid_match:
                # 宽松匹配：各种引号
                ssid_match = re.search(r'SSID[^:]+:\s*["“]([^"”]+)["”]', output, re.IGNORECASE)
            if ssid_match:
                ssid = ssid_match.group(1)
            
            # 提取客户端数（从状态部分，不是最大值）
            client_count = 0
            # 中文：客户端数      : 0（注意不包含"最多"）
            # 使用负向预查确保前面不是"最多"
            client_match = re.search(r'(?<!最多)客户端数\s+:\s+(\d+)', output)
            if not client_match:
                # 英文：Number of clients : 0
                client_match = re.search(r'(?<!Maximum\s)Number\s+of\s+clients\s*:\s*(\d+)', output, re.IGNORECASE)
            if client_match:
                client_count = int(client_match.group(1))
            
            # 获取本机IP
            local_ip = HotspotService.get_local_ip() if is_running else None
            
            return {
                'success': True,
                'running': is_running,
                'ssid': ssid,
                'clients': client_count,
                'ip': local_ip,
                'status_text': '运行中' if is_running else '已停止'
            }
            
        except Exception as e:
            return {
                'success': False,
                'running': False,
                'message': f'获取状态异常: {str(e)}',
                'ssid': None
            }
    
    @staticmethod
    def get_local_ip() -> Optional[str]:
        """
        获取本机局域网IP地址
        
        Returns:
            IP地址字符串
        """
        try:
            # 方法1: 通过连接外部地址获取
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            try:
                # 方法2: 获取主机名对应IP
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                return ip
            except:
                return '127.0.0.1'
    
    @staticmethod
    def get_hotspot_ip() -> Optional[str]:
        """
        获取WiFi热点的IP地址（用于手机连接访问）
        
        Returns:
            热点IP地址，如果热点未启动则返回None
        """
        try:
            # Windows热点默认IP是192.168.137.1
            # 通过ipconfig命令获取精确的热点IP
            cmd = ['ipconfig']
            result = HotspotService._run_command(cmd)
            
            if result.returncode != 0:
                return '192.168.137.1'  # 返回默认值
            
            output = result.stdout
            if output is None:
                output = ""
                
            lines = output.split('\n')
            
            # 查找"本地连接* "或"Microsoft Wi-Fi Direct Virtual Adapter"相关的适配器
            # 这是Windows热点虚拟适配器
            in_hotspot_section = False
            for i, line in enumerate(lines):
                # 匹配热点适配器名称
                if ('本地连接*' in line and '适配器' in line) or \
                   ('Microsoft Wi-Fi Direct Virtual Adapter' in line):
                    in_hotspot_section = True
                    continue
                
                # 如果在热点适配器段落中
                if in_hotspot_section:
                    # 遇到新的适配器段落，退出
                    if '适配器' in line and line.strip().endswith(':'):
                        break
                    
                    # 查找IPv4地址
                    if 'IPv4' in line and ':' in line:
                        # 提取IP地址
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            hotspot_ip = ip_match.group(1)
                            # 验证是否是热点网段（通常是192.168.137.x）
                            if hotspot_ip.startswith('192.168.'):
                                return hotspot_ip
            
            # 如果没找到，返回默认的热点IP
            return '192.168.137.1'
            
        except Exception as e:
            # 出错时返回默认的Windows热点IP
            return '192.168.137.1'

    @staticmethod
    def _get_network_adapters() -> list:
        """
        获取网络适配器信息
        
        Returns:
            网络适配器列表
        """
        try:
            # 使用PowerShell获取网络适配器信息
            cmd = [
                'powershell', '-Command',
                'Get-NetAdapter | Select-Object Name, InterfaceDescription, ifIndex, InterfaceGuid, Status, MediaType | ConvertTo-Json'
            ]
            result = HotspotService._run_command(cmd)
            
            if result.returncode == 0 and result.stdout:
                import json
                adapters = json.loads(result.stdout)
                # 确保返回列表格式
                if isinstance(adapters, dict):
                    adapters = [adapters]
                elif not isinstance(adapters, list):
                    adapters = []
                return adapters
            else:
                print(f"获取网络适配器信息失败: {result.stderr if result.stderr else '无输出'}")
                return []
        except Exception as e:
            print(f"获取网络适配器信息异常: {str(e)}")
            return []

    @staticmethod
    def _get_active_internet_adapter() -> Optional[dict]:
        """
        获取活动的互联网连接适配器（具有默认路由的适配器）
        
        Returns:
            活动适配器信息或None
        """
        try:
            # 使用PowerShell获取具有默认路由的网络适配器
            cmd = [
                'powershell', '-Command',
                '''
                $routes = Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Where-Object {$_.NextHop -ne "0.0.0.0"}
                if ($routes) {
                    $mainRoute = $routes | Sort-Object RouteMetric | Select-Object -First 1
                    $adapter = Get-NetAdapter -ifIndex $mainRoute.ifIndex
                    $adapter | Select-Object Name, InterfaceDescription, ifIndex, InterfaceGuid | ConvertTo-Json
                }
                '''
            ]
            result = HotspotService._run_command(cmd)
            
            if result.returncode == 0 and result.stdout:
                import json
                adapter = json.loads(result.stdout)
                return adapter
            else:
                print(f"获取活动网络适配器失败: {result.stderr if result.stderr else '无输出'}")
                return None
        except Exception as e:
            print(f"获取活动网络适配器异常: {str(e)}")
            return None

    @staticmethod
    def _configure_virtual_adapter_dhcp() -> bool:
        """
        配置虚拟适配器的DHCP服务
        
        Returns:
            配置是否成功
        """
        try:
            # 启用虚拟适配器的DHCP服务器
            cmd = [
                'powershell', '-Command',
                '''
                try {
                    # 获取热点虚拟适配器
                    $adapters = Get-NetAdapter | Where-Object {$_.Name -like "*本地连接*" -and $_.InterfaceDescription -like "*Microsoft Wi-Fi Direct Virtual Adapter*"}
                    if ($adapters) {
                        $adapter = $adapters[0]
                        # 设置DHCP服务器范围
                        $ipAddress = $adapter | Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue
                        if ($ipAddress) {
                            $network = $ipAddress.IPAddress -replace "\.\d+$", ".0"
                            # 启用DHCP
                            netsh dhcp server add scope $network 255.255.255.0 "WiFi Hotspot"
                            netsh dhcp server $network set option 3 $ipAddress.IPAddress  # 默认网关
                            netsh dhcp server $network set option 6 $ipAddress.IPAddress  # DNS服务器
                            netsh dhcp server $network set state 1  # 启用作用域
                            Write-Output "DHCP配置成功"
                            return $true
                        }
                    }
                    Write-Output "未找到热点虚拟适配器"
                    return $false
                } catch {
                    Write-Output "DHCP配置失败: $($_.Exception.Message)"
                    return $false
                }
                '''
            ]
            result = HotspotService._run_command(cmd)
            
            if result.returncode == 0:
                print(f"DHCP配置结果: {result.stdout}")
                return "成功" in result.stdout
            else:
                print(f"DHCP配置失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"DHCP配置异常: {str(e)}")
            return False

    @staticmethod
    def enable_internet_sharing(enable: bool = True) -> Dict[str, Any]:
        """
        启用/禁用Internet连接共享(ICS)
        
        Args:
            enable: True启用共享，False禁用共享
            
        Returns:
            结果字典
        """
        try:
            if enable:
                # 启用网络共享
                print("正在启用网络共享...")
                
                # 1. 获取活动的互联网连接适配器
                main_adapter = HotspotService._get_active_internet_adapter()
                if not main_adapter:
                    return {
                        'success': False,
                        'message': '未找到活动的互联网连接适配器，请确保主机已连接到互联网',
                        'sharing_enabled': False
                    }
                
                print(f"主网卡: {main_adapter.get('Name', 'Unknown')}")
                
                # 2. 获取热点虚拟适配器
                cmd = [
                    'powershell', '-Command',
                    '''
                    $adapters = Get-NetAdapter | Where-Object {$_.Name -like "*本地连接*" -and $_.InterfaceDescription -like "*Microsoft Wi-Fi Direct Virtual Adapter*"}
                    if ($adapters) {
                        $adapters[0] | Select-Object Name, InterfaceDescription, ifIndex, InterfaceGuid | ConvertTo-Json
                    }
                    '''
                ]
                result = HotspotService._run_command(cmd)
                
                if result.returncode != 0 or not result.stdout:
                    return {
                        'success': False,
                        'message': '未找到WiFi热点虚拟适配器，请确保热点已启动',
                        'sharing_enabled': False
                    }
                
                import json
                virtual_adapter = json.loads(result.stdout)
                print(f"虚拟网卡: {virtual_adapter.get('Name', 'Unknown')}")
                
                # 3. 配置ICS
                cmd = [
                    'powershell', '-Command',
                    f'''
                    try {{
                        # 启用主网卡的ICS
                        $mainAdapter = Get-NetAdapter -ifIndex {main_adapter['ifIndex']}
                        $virtualAdapter = Get-NetAdapter -ifIndex {virtual_adapter['ifIndex']}
                        
                        # 检查是否已启用ICS
                        $regPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\FirewallRules"
                        $icsRule = Get-ItemProperty -Path $regPath -Name "IHSTK000" -ErrorAction SilentlyContinue
                        
                        if ($icsRule) {{
                            Write-Output "ICS已启用"
                        }} else {{
                            # 启用ICS
                            $netShare = New-Object -ComObject HNetCfg.HNetShare
                            $mainConnection = $netShare.EnumEveryConnection | Where-Object {{
                                $netShare.NetConnectionProps($_).DeviceName -eq $mainAdapter.Name
                            }}
                            if ($mainConnection) {{
                                $mainProps = $netShare.NetConnectionProps($mainConnection)
                                $mainConfig = $netShare.INetSharingConfigurationForINetConnection($mainConnection)
                                $mainConfig.EnableInternetConnectionSharing($true)
                                
                                $virtualConnection = $netShare.EnumEveryConnection | Where-Object {{
                                    $netShare.NetConnectionProps($_).DeviceName -eq $virtualAdapter.Name
                                }}
                                if ($virtualConnection) {{
                                    $virtualConfig = $netShare.INetSharingConfigurationForINetConnection($virtualConnection)
                                    $virtualConfig.EnableInternetConnectionSharing($false)
                                    Write-Output "ICS启用成功"
                                }} else {{
                                    Write-Output "未找到虚拟适配器连接"
                                }}
                            }} else {{
                                Write-Output "未找到主适配器连接"
                            }}
                        }}
                    }} catch {{
                        Write-Output "启用ICS失败: $($_.Exception.Message)"
                    }}
                    '''
                ]
                result = HotspotService._run_command(cmd)
                
                if result.returncode == 0 and "成功" in result.stdout:
                    # 配置虚拟适配器的DHCP
                    HotspotService._configure_virtual_adapter_dhcp()
                    
                    return {
                        'success': True,
                        'message': '网络共享已启用',
                        'sharing_enabled': True,
                        'details': f"主网卡: {main_adapter.get('Name')}, 虚拟网卡: {virtual_adapter.get('Name')}"
                    }
                else:
                    error_msg = result.stdout if result.stdout else result.stderr
                    return {
                        'success': False,
                        'message': f'启用网络共享失败: {error_msg}',
                        'sharing_enabled': False
                    }
            else:
                # 禁用网络共享
                print("正在禁用网络共享...")
                
                cmd = [
                    'powershell', '-Command',
                    '''
                    try {
                        $netShare = New-Object -ComObject HNetCfg.HNetShare
                        $connections = $netShare.EnumEveryConnection
                        foreach ($connection in $connections) {
                            $props = $netShare.NetConnectionProps($connection)
                            $config = $netShare.INetSharingConfigurationForINetConnection($connection)
                            if ($config.SharingEnabled) {
                                $config.DisableSharing()
                            }
                        }
                        Write-Output "网络共享已禁用"
                    } catch {
                        Write-Output "禁用网络共享失败: $($_.Exception.Message)"
                    }
                    '''
                ]
                result = HotspotService._run_command(cmd)
                
                if result.returncode == 0 and "已禁用" in result.stdout:
                    return {
                        'success': True,
                        'message': '网络共享已禁用',
                        'sharing_enabled': False
                    }
                else:
                    error_msg = result.stdout if result.stdout else result.stderr
                    return {
                        'success': False,
                        'message': f'禁用网络共享失败: {error_msg}',
                        'sharing_enabled': True
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'message': f'网络共享操作异常: {str(e)}',
                'sharing_enabled': not enable
            }

    @staticmethod
    def get_sharing_status() -> Dict[str, Any]:
        """
        获取网络共享状态
        
        Returns:
            共享状态信息
        """
        try:
            cmd = [
                'powershell', '-Command',
                '''
                try {
                    $netShare = New-Object -ComObject HNetCfg.HNetShare
                    $connections = $netShare.EnumEveryConnection
                    $sharingInfo = @()
                    foreach ($connection in $connections) {
                        $props = $netShare.NetConnectionProps($connection)
                        $config = $netShare.INetSharingConfigurationForINetConnection($connection)
                        if ($config.SharingEnabled) {
                            $sharingInfo += @{
                                Name = $props.Name
                                DeviceName = $props.DeviceName
                                SharingType = if ($config.SharingConnectionType -eq 0) { "Public" } else { "Private" }
                            }
                        }
                    }
                    @{
                        SharingEnabled = $sharingInfo.Count -gt 0
                        Connections = $sharingInfo
                    } | ConvertTo-Json
                } catch {
                    @{
                        SharingEnabled = $false
                        Error = $_.Exception.Message
                    } | ConvertTo-Json
                }
                '''
            ]
            result = HotspotService._run_command(cmd)
            
            if result.returncode == 0 and result.stdout:
                import json
                sharing_data = json.loads(result.stdout)
                
                return {
                    'success': True,
                    'sharing_enabled': sharing_data.get('SharingEnabled', False),
                    'details': sharing_data.get('Connections', []),
                    'message': '共享已启用' if sharing_data.get('SharingEnabled') else '共享未启用'
                }
            else:
                return {
                    'success': True,
                    'sharing_enabled': False,
                    'message': '共享未启用'
                }
                
        except Exception as e:
            return {
                'success': False,
                'sharing_enabled': False,
                'message': f'获取共享状态异常: {str(e)}'
            }