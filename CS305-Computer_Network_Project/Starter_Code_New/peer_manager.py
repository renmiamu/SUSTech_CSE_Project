import logging
import threading
import time
import json
from collections import defaultdict

from utils import generate_message_id
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

peer_status = {}  # {peer_id: 'ALIVE', 'UNREACHABLE' or 'UNKNOWN'}
last_ping_time = {}  # {peer_id: timestamp}
rtt_tracker = {}  # {peer_id: transmission latency}

PING_INTERVAL = 5  # 每隔 5 秒 ping 一次
PING_TIMEOUT = 10  # 超过 10 秒无响应就标记 UNREACHABLE

# 新 基础引导节点列表（不会被自动删除）
BOOTSTRAP_PEER_IDS = set([str(i) for i in range(5000, 5011)])  # 5000-5010为基础引导节点

# 节点删除超时时间（秒）
NODE_REMOVAL_TIMEOUT = 180  # 3分钟无响应则删除动态节点

# === Check if peers are alive ===

def start_ping_loop(self_id, peer_table):
    from outbox import enqueue_message

    def loop():
        # TODO: Define the JSON format of a `ping` message, which should include `{message typy, sender's ID,
        #  timestamp}`.

        # TODO: Send a `ping` message to each known peer periodically.
        while True:
            now = time.time()
            for peer_id, (ip, port) in peer_table.items():
                msg = {
                    "type": "PING",
                    "sender_id": self_id,
                    "timestamp": now,
                    "message_id": generate_message_id()
                }
                # 直接发送字典对象，不转换为字符串
                enqueue_message(peer_id, ip, port, msg)
            time.sleep(PING_INTERVAL)

    threading.Thread(target=loop, daemon=True).start()


def create_pong(sender, recv_ts):
    # TODO: Create the JSON format of a `pong` message, which should include `{message type, sender's ID,
    #  timestamp in the received ping message}`.
    return {
        "type": "PONG",
        "sender_id": sender,
        "timestamp": recv_ts,
        "message_id": generate_message_id()
    }


def handle_pong(msg):
    # TODO: Read the information in the received `pong` message.

    # TODO: Update the transmission latenty between the peer and the sender (`rtt_tracker`).
    sender_id = msg.get("sender_id")
    ping_ts = msg.get("timestamp")
    now = time.time()
    rtt = now - ping_ts

    rtt_tracker[sender_id] = rtt
    update_peer_heartbeat(sender_id)


def start_heartbeat_checker():
    import threading

    def loop():
        # TODO: Check the latest time to receive `ping` or `pong` message from each peer in `last_ping_time`.

        # TODO: If the latest time is earlier than the limit, mark the peer's status in `peer_status` as
        #  `UNREACHABLE` or otherwise `ALIVE`.

        while True:
            now = time.time()
            for peer_id, last_time in last_ping_time.items():
                if now - last_time > PING_TIMEOUT:
                    peer_status[peer_id] = 'UNREACHABLE'
                else:
                    peer_status[peer_id] = 'ALIVE'
            time.sleep(PING_INTERVAL)

    threading.Thread(target=loop, daemon=True).start()
    logger.info("节点心跳检查器已启动")


def start_peer_monitor():
    """启动节点监控器"""
    start_heartbeat_checker()
    start_dead_node_cleaner()  # 添加对新功能的调用
    logger.info("节点监控器已启动")


def update_peer_heartbeat(peer_id):
    # TODO: Update the `last_ping_time` of a peer when receiving its `ping` or `pong` message.
    last_ping_time[peer_id] = time.time()


# === Blacklist Logic ===

blacklist = set()  # The set of banned peers

peer_offense_counts = defaultdict(int)  # The offence times of peers


def record_offense(peer_id):
    # TODO: Record the offence times of a peer when malicious behaviors are detected.

    # TODO: Add a peer to `blacklist` if its offence times exceed 3. 

    peer_offense_counts[peer_id] += 1
    if peer_offense_counts[peer_id] > 0: #TODO:临时修改！我就是测试一下
        blacklist.add(peer_id)
        print(f"节点 {peer_id} 违规次数达到阈值，已加入黑名单")

# === Peer Status ===
def get_peer_status():
    """
    返回所有已知节点的状态信息
    
    Returns:
        dict: 包含所有节点状态的字典，格式为 {peer_id: status}
    """
    from peer_discovery import known_peers, peer_flags
    
    result = {}
    for peer_id, (ip, port) in known_peers.items():
        str_peer_id = str(peer_id)
        status = peer_status.get(str_peer_id, "UNKNOWN")
        
        # 获取节点RTT信息
        rtt = None
        if str_peer_id in rtt_tracker:
            rtt = rtt_tracker[str_peer_id]
        
        # 获取节点标志信息
        flags = peer_flags.get(str_peer_id, {})
        
        result[str_peer_id] = {
            "status": status,
            "rtt": rtt,
            "ip": ip,
            "port": port,
            "flags": flags,
            "blacklisted": str_peer_id in blacklist
        }
    
    return result

def start_dead_node_cleaner():
    """启动定期清理长时间未响应节点的服务"""
    from peer_discovery import known_peers, peer_flags
    import threading
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    
    def cleaner_loop():
        while True:
            try:
                current_time = time.time()
                nodes_to_remove = []
                
                # 检查所有标记为DEAD的节点
                for peer_id, status in peer_status.items():
                    # 跳过基础引导节点
                    if str(peer_id) in BOOTSTRAP_PEER_IDS:
                        continue
                        
                    # 检查是否为长时间未响应的节点
                    if status == "DEAD" and peer_id in last_ping_time:
                        dead_time = current_time - last_ping_time[peer_id]
                        if dead_time > NODE_REMOVAL_TIMEOUT:
                            nodes_to_remove.append(peer_id)
                
                # 删除符合条件的节点
                for peer_id in nodes_to_remove:
                    logger.info(f"自动清理长时间未响应的动态节点: {peer_id}")
                    
                    # 从各种数据结构中删除节点信息
                    if peer_id in known_peers:
                        del known_peers[peer_id]
                    if peer_id in peer_flags:
                        del peer_flags[peer_id]
                    if peer_id in peer_status:
                        del peer_status[peer_id]
                    if peer_id in last_ping_time:
                        del last_ping_time[peer_id]
                    if peer_id in rtt_tracker:
                        del rtt_tracker[peer_id]
                    
                    # 更新配置文件
                    from dynamic_node_manager import remove_from_global_config
                    remove_from_global_config(peer_id)
                    
                    # 通知仪表盘
                    try:
                        from dashboard import notify_node_left
                        notify_node_left(peer_id, "timeout_removed")
                    except ImportError:
                        pass
                
                # 每30秒检查一次
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"清理未响应节点时出错: {e}")
                time.sleep(60)  # 出错时等待时间更长
    
    # 启动清理线程
    threading.Thread(target=cleaner_loop, daemon=True).start()
    logger.info("已启动动态节点自动清理服务")