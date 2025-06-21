import socket
import threading
import json
import logging
from message_handler import dispatch_message

# 初始化日志器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_socket_server(self_id, self_ip, port):

    def listen_loop():
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 确保绑定正确的网络接口
            if self_ip == "127.0.0.1" or self_ip == "localhost":
                # 本地测试用
                bind_ip = self_ip
            else:
                # 使用0.0.0.0接收所有网络接口的连接
                bind_ip = "0.0.0.0"
                
            logger.info(f"节点 {self_id} 尝试在 {bind_ip}:{port} 上监听连接 (实际IP: {self_ip})")
            server_socket.bind((bind_ip, port))
            server_socket.listen(10)  # 增加队列大小
            logger.info(f"节点 {self_id} 成功在 {bind_ip}:{port} 上开始监听连接")

        except Exception as e:
            logger.error(f"节点 {self_id} 启动失败：{str(e)}")
            return

        while True:
            try:
                client_socket, addr = server_socket.accept()
                logger.info(f"节点 {self_id} 接收到来自 {addr} 的连接")

                def handle_client(sock):
                    try:
                        # 设置超时时间，防止连接被无限阻塞
                        sock.settimeout(30)
                        buffer = b""
                        
                        # 持续接收数据直到连接关闭
                        while True:
                            try:
                                chunk = sock.recv(4096)
                                if not chunk:  # 连接已关闭
                                    break
                                
                                buffer += chunk
                                logger.debug(f"接收到数据块: {len(chunk)} 字节，当前缓冲区大小: {len(buffer)} 字节")
                                
                                # 处理缓冲区中所有完整的消息
                                while b"\n" in buffer:
                                    # 分割第一个完整消息和剩余部分
                                    msg_bytes, buffer = buffer.split(b"\n", 1)
                                    
                                    if msg_bytes:  # 确保不是空消息
                                        try:
                                            msg_str = msg_bytes.decode()
                                            json_data = json.loads(msg_str)
                                            sender_id = json_data.get('sender_id')
                                            if not sender_id:
                                                sender_id = json_data.get('peer_id')
                                            logger.info(f"接收到消息: 类型={json_data.get('type', 'UNKNOWN')}, 发送者={sender_id}")
                                            dispatch_message(json_data, self_id, self_ip)
                                        except json.JSONDecodeError:
                                            logger.warning(f"节点 {self_id} 收到非法JSON：{msg_bytes[:100]}")
                                        except Exception as e:
                                            logger.error(f"处理消息时出错: {str(e)}")
                            
                            except socket.timeout:
                                # 超时但连接可能仍然有效，继续尝试接收
                                continue
                            except ConnectionResetError:
                                # 连接被对方重置
                                logger.warning(f"连接被重置: {addr}")
                                break
                            except Exception as e:
                                logger.error(f"接收数据时出错: {str(e)}")
                                break

                    except Exception as e:
                        logger.error(f"处理客户端消息失败：{str(e)}")
                    finally:
                        sock.close()
                        logger.debug(f"关闭与客户端 {addr} 的连接")

                threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

            except Exception as e:
                logger.error(f"接收连接出错：{str(e)}")

    threading.Thread(target=listen_loop, daemon=True).start()
