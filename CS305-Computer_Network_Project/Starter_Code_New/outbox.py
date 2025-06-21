import socket
import threading
import time
import json
import random
from collections import defaultdict, deque
from threading import Lock
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# === Per-peer Rate Limiting ===
RATE_LIMIT = 10  # max messages
TIME_WINDOW = 10  # per seconds
peer_send_timestamps = defaultdict(list) # the timestamps of sending messages to each peer

MAX_RETRIES = 3
RETRY_INTERVAL = 5  # seconds
QUEUE_LIMIT = 50

# Priority levels
PRIORITY_HIGH = {"PING", "PONG", "BLOCK", "INV", "GETDATA"}
PRIORITY_MEDIUM = {"TX", "HELLO"}
PRIORITY_LOW = {"RELAY"}

DROP_PROB = 0.05
LATENCY_MS = (20, 100)
SEND_RATE_LIMIT = 5  # messages per second

drop_stats = {
    "BLOCK": 0,
    "TX": 0,
    "HELLO": 0,
    "PING": 0,
    "PONG": 0,
    "OTHER": 0
}

priority_order = {
    "BLOCK": 1,
    "TX": 2,
    "PING": 3,
    "PONG": 4,
    "HELLO": 5
}

# Queues per peer and priority
queues = defaultdict(lambda: defaultdict(deque))
retries = defaultdict(int)
lock = threading.Lock()

# === Sending Rate Limiter ===
class RateLimiter:
    def __init__(self, rate=SEND_RATE_LIMIT):
        self.capacity = rate               # Max burst size
        self.tokens = rate                # Start full
        self.refill_rate = rate           # Tokens added per second
        self.last_check = time.time()
        self.lock = Lock()

    def allow(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_check
            self.tokens += elapsed * self.refill_rate
            self.tokens = min(self.tokens, self.capacity)
            self.last_check = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

rate_limiter = RateLimiter()

def enqueue_message(target_id, ip, port, message):
    from peer_manager import blacklist, rtt_tracker 
    # 检查速率限制
    #Check if the peer sends message to the receiver too frequently using the function `is_rate_limited`. If yes, drop the message.
    if is_rate_limited(target_id):
        logger.debug(f"节点发送到 {target_id} 的消息被限制")
        return False
    
    # 检查黑名单
    #Check if the receiver exists in the `blacklist`. If yes, drop the message.
    if target_id in blacklist:
        logger.debug(f"节点尝试发送消息到黑名单中的节点 {target_id}")
        return False
    
    # 获取消息优先级
    #Classify the priority of the sending messages based on the message type using the function `classify_priority`.
    priority = classify_priority(message)
    
    # 初始化目标节点的队列(如果不存在)
    if target_id not in queues:
        queues[target_id] = defaultdict(deque)
    
    #Add the message to the queue (`queues`) if the length of the queue is within the limit `QUEUE_LIMIT`, or otherwise, drop the message.
    # 检查队列长度限制
    if sum(len(q) for q in queues[target_id].values()) >= QUEUE_LIMIT:
        logger.warning(f"发往节点 {target_id} 的队列已满")
        return False
    
    # 将消息加入队列
    with lock:
        queues[target_id][priority].append((message, ip, port, time.time()))
        logger.debug(f"消息 {message.get('type')} 已加入发送队列，目标: {target_id}, 优先级: {priority}")
    return True


def is_rate_limited(peer_id):
    # TODO:Check how many messages were sent from the peer to a target peer during the `TIME_WINDOW` that ends now.
  
    # TODO: If the sending frequency exceeds the sending rate limit `RATE_LIMIT`, return `TRUE`; otherwise, record the current sending time into `peer_send_timestamps`.
    """检查消息发送频率是否超过限制"""
    # 确保使用字符串类型的键
    str_peer_id = str(peer_id)
    
    current_time = time.time()
    # 初始化时间戳列表(如果不存在)
    if str_peer_id not in peer_send_timestamps:
        peer_send_timestamps[str_peer_id] = []
    
    # 移除过期的时间戳
    timestamps = peer_send_timestamps[str_peer_id]
    while timestamps and TIME_WINDOW < current_time - timestamps[0]:
        timestamps.pop(0)
    
    # 检查发送频率
    if len(timestamps) >= RATE_LIMIT:
        logger.debug(f"节点 {str_peer_id} 的消息发送频率已达上限，当前窗口内消息数: {len(timestamps)}")
        return True
    
    # 记录当前发送时间
    timestamps.append(current_time)
    return False

def classify_priority(message):
    # TODO: Classify the priority of a message based on the message type.
    """根据消息类型分类优先级"""
    msg_type = message.get("type", "")
    
    if msg_type in PRIORITY_HIGH:
        return 1  # 高优先级
    elif msg_type in PRIORITY_MEDIUM:
        return 2  # 中优先级
    return 3  # 低优先级
    

def send_from_queue(self_id):

    """从队列中发送消息"""
    def worker():
        from peer_discovery import known_peers
        # Read the message in the queue. 
        # Each time, read one message with the highest priority of a target peer. 
        # After sending the message, read the message of the next target peer. 
        # This ensures the fairness of sending messages to different target peers.
        # 记录上次处理的节点索引，确保公平处理
        last_peer_index = 0
        
        while True:
            try:
                # 获取当前已知节点列表
                peers = list(queues.keys())
                if not peers:
                    time.sleep(0.1)
                    continue
                
                # 轮询处理每个节点的消息
                if last_peer_index >= len(peers):
                    last_peer_index = 0
                
                target_id = peers[last_peer_index]
                last_peer_index = (last_peer_index + 1) % len(peers)
                
                # 获取当前节点队列中优先级最高的消息
                message = None
                with lock:
                    for priority in sorted(queues[target_id].keys()):
                        if queues[target_id][priority]:
                            message, ip, port, enqueue_time = queues[target_id][priority].popleft()
                            break
                
                if not message:
                    continue
                
                # 检查消息是否超时
                if time.time() - enqueue_time > 30:  # 30秒超时
                    logger.warning(f"消息发送超时，丢弃: {message.get('type')} 到 {target_id}")
                    continue
                # Send the message using the function `relay_or_direct_send`, which will decide whether to send the message to target peer directly or through a relaying peer.
                # 发送消息
                success = relay_or_direct_send(self_id,target_id,message)
                
                #Retry a message if it is sent unsuccessfully and drop the message if the retry times exceed the limit `MAX_RETRIES`
                if not success:
                    # 记录重试次数
                    retries[target_id] = retries.get(target_id, 0) + 1
                    
                    if retries[target_id] <= MAX_RETRIES:
                        # 重新入队，但降低优先级
                        priority = classify_priority(message) + 1 #数字越小优先级越小
                        with lock:
                            queues[target_id][priority].append((message, ip, port, time.time()))
                        logger.debug(f"重试发送消息到 {target_id}，尝试次数: {retries[target_id]}")
                    else:
                        logger.warning(f"发送到 {target_id} 的消息已达最大重试次数，放弃发送")
                        retries[target_id] = 0
                else:
                    retries[target_id] = 0
            
            except Exception as e:
                logger.error(f"发送消息时出错: {e}")
            
            finally:
                time.sleep(0.01)  # 避免CPU过载
    
    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=worker, daemon=True).start()

def relay_or_direct_send(self_id, dst_id, message):
    from peer_discovery import known_peers, peer_flags, peer_config
    """检查目标节点是否为NAT节点,决定是直接发送消息还是通过中继节点"""
    # Check if the target peer is NATed. 
    is_nated = False
    if dst_id in peer_flags and peer_flags[dst_id].get("nat",False):
        is_nated = True
        logger.info(f"目标节点 {dst_id} 根据peer_flags判断为NAT状态，需要使用中继")
    else:
        logger.info(f"目标节点 {dst_id} 根据peer_flags判断为非NAT状态或状态未知 ({peer_flags.get(dst_id, {}).get('nat')})，尝试直接发送")
        
    # If the target peer is NATed, use the function `get_relay_peer` to find the best relaying peer. 
    # Define the JSON format of a `RELAY` message, which should include `{message type, sender's ID, target peer's ID, `payload`}`. 
    # `payload` is the sending message. 
    # Send the `RELAY` message to the best relaying peer using the function `send_message`.
    if is_nated:
        # 找到最佳中继节点
        logger.info(f"为NAT节点 {dst_id} 寻找中继节点...")
        relay_peer = get_relay_peer(self_id, dst_id) # (peer_id, ip, port) or None
        
        if relay_peer:
            # 创建中继消息
            relay_message = {
                "type": "RELAY",
                "sender_id": self_id,
                "target_id": dst_id,
                "payload": message,
            }
            
            # 发送中继消息
            logger.info(f"通过中继节点 {relay_peer[0]} ({relay_peer[1]}:{relay_peer[2]}) 发送消息到NAT节点 {dst_id}")
            return send_message(relay_peer[1], relay_peer[2], relay_message)
        else:
            logger.warning(f"找不到节点 {dst_id} 的中继节点，无法发送消息")
            return False
    
    # If the target peer is non-NATed, send the message to the target peer using the function `send_message`.
    else:
        # 直接发送消息
        if dst_id in known_peers:
            peer_ip, peer_port = known_peers[dst_id]
            logger.info(f"直接发送消息到节点 {dst_id} ({peer_ip}:{peer_port})")
            return send_message(peer_ip, peer_port, message)
        else:
            logger.warning(f"未知节点 {dst_id}，无法发送消息")
            return False

def get_relay_peer(self_id, dst_id):
    from peer_discovery import known_peers,peer_flags
    from peer_manager import rtt_tracker
    from peer_discovery import known_peers, reachable_by
    
    """为NAT节点找到最佳中继节点"""
    # TODO: Find the set of relay candidates reachable from the target peer 
    # in `reachable_by` of `peer_discovery.py`.
    candidate_relays_info = [] # Store (peer_id, ip, port)
    
    # 尝试从reachable_by中查找已知可以作为目标节点中继的节点
    if dst_id in reachable_by and reachable_by[dst_id]:
        for relay_id in reachable_by[dst_id]:
            if relay_id in known_peers:
                ip, port = known_peers[relay_id]
                candidate_relays_info.append((relay_id, ip, port))
                logger.debug(f"[{self_id}] get_relay_peer: 从reachable_by中找到候选中继 {relay_id}")
    
    if not candidate_relays_info:
        logger.warning(f"[{self_id}] get_relay_peer: 节点 {dst_id}：找不到任何非NAT的中继候选节点。")
        return None
    # TODO: Read the transmission latency between the sender and other peers in `rtt_tracker` in `peer_manager.py`.
    # 选择最佳中继 (例如, RTT最低的)
    # 如果有多个候选，选择RTT最小的；如果RTT不可用，则随机选择一个
    best_relay_candidate = None
    min_rtt_to_relay = float('inf')

    # 基于RTT选择
    relays_with_rtt = []
    for relay_id, relay_ip, relay_port in candidate_relays_info:
        rtt = rtt_tracker.get(relay_id, float('inf'))
        relays_with_rtt.append(((relay_id, relay_ip, relay_port), rtt))
    
    if relays_with_rtt:
        # 按RTT排序并选择第一个
        relays_with_rtt.sort(key=lambda x: x[1])
        best_relay_candidate = relays_with_rtt[0][0]
        min_rtt_to_relay = relays_with_rtt[0][1]
        logger.info(f"[{self_id}] get_relay_peer: 为NAT目标 {dst_id} 基于RTT ({min_rtt_to_relay:.4f}ms) 选择中继节点 {best_relay_candidate[0]}")
    elif candidate_relays_info: # 如果没有RTT信息，但有候选者，则随机选择
        best_relay_candidate = random.choice(candidate_relays_info)
        logger.info(f"[{self_id}] get_relay_peer: 为NAT目标 {dst_id} (无RTT信息) 随机选择中继节点 {best_relay_candidate[0]}")
    
    if best_relay_candidate:
        return best_relay_candidate # (peer_id, ip, port)
    else:
        logger.warning(f"[{self_id}] get_relay_peer: 节点 {dst_id}：尽管有候选，但未能选择一个有效的中继节点。")
        return None

def send_message(ip, port, message):
    
    # Wrap the function `send_message` with the dynamic network condition 
    # in the function `apply_network_condition` of `link_simulator.py`.
    """发送消息到目标节点"""
    from peer_discovery import known_peers, peer_config
    # Send the message to the target peer. 
    try:
        # 从消息中获取发送者ID（如果是字典类型）
        sender_id = "UNKNOWN"
        if isinstance(message, dict) and "sender_id" in message:
            sender_id = message["sender_id"]
        elif isinstance(message, dict) and "peer_id" in message:
            sender_id = message["peer_id"]
        else:
            # 尝试从配置中获取当前节点ID
            sender_id = peer_config.get("self_id", "UNKNOWN")
        
        # 记录发送的消息
        from dashboard import log_sent_message
        
        # 尝试找出接收者ID
        receiver_id = "UNKNOWN"
        for peer_id, (peer_ip, peer_port) in known_peers.items():
            if peer_ip == ip and peer_port == port:
                receiver_id = peer_id
                break
        
        # 获取消息类型
        if isinstance(message, dict):
            msg_type = message.get('type', 'UNKNOWN')
        elif isinstance(message, str):
            try:
                import json
                msg_data = json.loads(message.strip())
                msg_type = msg_data.get('type', 'UNKNOWN')
            except:
                msg_type = 'UNKNOWN'
        else:
            msg_type = 'UNKNOWN'
            
        log_sent_message(sender_id, receiver_id, msg_type, message)
            
        logger.info(f"准备发送消息: 类型={msg_type}, 目标={ip}:{port}")   
            
        
        # 创建并配置套接字
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        
        # 连接目标节点
        logger.info(f"尝试连接到: {ip}:{port}")
        client_socket.connect((ip, int(port)))
        
        # 确保发送的是字节流
        if isinstance(message, dict):
            import json
            message_bytes = (json.dumps(message) + "\n").encode()
        elif isinstance(message, str):
            message_bytes = message.encode() if not message.endswith('\n') else message.encode()
        else:
            message_bytes = str(message).encode()
            
        # 发送数据
        client_socket.sendall(message_bytes)
        
        logger.info(f"消息发送成功: 类型={msg_type}, 目标={ip}:{port}, 大小={len(message_bytes)}字节")
        
        # 关闭连接
        client_socket.close()
        return True
        
    except ConnectionRefusedError:
        logger.error(f"连接被拒绝: {ip}:{port} - 目标节点可能未启动或端口未开放")
        return False
    except socket.timeout:
        logger.error(f"连接超时: {ip}:{port}")
        return False
    except Exception as e:
        logger.error(f"发送消息到 {ip}:{port} 失败: {str(e)}")
        return False


def apply_network_conditions(send_func):
    def wrapper(ip, port, message):
        # 检查发送容量限制
        # Use the function `rate_limiter.allow` to check if the peer's sending rate is out of limit. 
        # If yes, drop the message and update the drop states (`drop_stats`).
        if not rate_limiter.allow():
            msg_type = message.get("type", "OTHER") if isinstance(message, dict) else "STRING"
            drop_stats[msg_type] = drop_stats.get(msg_type, 0) + 1
            logger.info(f"消息因容量限制而丢弃: 类型={msg_type}, 目标={ip}:{port}")
            return False
        
        # 模拟随机丢包
        # Generate a random number. If it is smaller than `DROP_PROB`, 
        # drop the message to simulate the random message drop in the channel. 
        # Update the drop states (`drop_stats`).
        if random.random() < DROP_PROB:
            msg_type = message.get("type", "OTHER")
            drop_stats[msg_type] = drop_stats.get(msg_type, 0) + 1
            logger.info(f"消息因随机丢包而丢弃: 类型={msg_type}, 目标={ip}:{port}")
            return False
            
        # 模拟网络延迟
        # Add a random latency before sending the message to simulate message transmission delay.
        latency = random.uniform(LATENCY_MS[0], LATENCY_MS[1]) / 1000.0
        time.sleep(latency)
        
        # 执行实际发送
        # Send the message using the function `send_func`.
        return send_func(ip, port, message)
    
    return wrapper

# 应用网络条件
send_message = apply_network_conditions(send_message)

def start_dynamic_capacity_adjustment():
    def adjust_loop():
        # Peridically change the peer's sending capacity in `rate_limiter` within the range [2, 10].
        while True:
            try:
                # 随机调整容量(2-10)
                new_capacity = random.randint(2, 10)
                rate_limiter.capacity = new_capacity
                rate_limiter.refill_rate = new_capacity
                logger.info(f"节点发送容量已调整为: {new_capacity}")
                
                # 每30-60秒调整一次
                sleep_time = random.uniform(30, 60)
                time.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"调整容量时出错: {e}")
                time.sleep(30)
                
    threading.Thread(target=adjust_loop, daemon=True).start()


def gossip_message(self_id, message, fanout=3):
    """将消息传播给多个目标节点"""
    from peer_discovery import known_peers, peer_flags
    
    # Randomly select the number of target peer from `known_peers`, which is equal to `fanout`. 
    # If the gossip message is a transaction, skip the lightweight peers in the `know_peers`.
    # 过滤已知节点
    candidates = []
    for peer_id in known_peers:
        if peer_id == self_id:  # 不向自己发送
            continue
            
        # 检查节点状态
        from peer_manager import peer_status
        status = peer_status.get(peer_id, "unknown")
        
        # 如果节点状态是UNREACHABLE，则跳过该节点
        if status == "UNREACHABLE":
            continue
            
        # 如果是交易消息，排除轻量级节点
        if message.get("type") == "TX":
            if peer_id in peer_flags and not peer_flags[peer_id].get("light"):
                candidates.append(peer_id)
        else:
            candidates.append(peer_id)

    # 如果候选节点数量少于fanout，则全部发送
    if len(candidates) <= fanout:
        target_peers = candidates
    else:
        # 随机选择fanout个节点
        target_peers = random.sample(candidates, fanout)
    
    # Send the message to the selected target peer and put them in the outbox queue.
    # 发送消息到选定的节点
    success_count = 0
    for target_peer in target_peers:
        if target_peer in known_peers:
            peer_ip, peer_port = known_peers[target_peer]
            if enqueue_message(target_peer, peer_ip, peer_port, message):
                success_count += 1
    
    if target_peers:
        logger.info(f"节点 {self_id} 通过gossip发送了 {message.get('type')} 消息给 {success_count}/{len(target_peers)} 个节点")
    else:
        logger.warning(f"节点 {self_id} 没有找到可用的gossip目标节点")
    
    return success_count > 0

def get_outbox_status():
    # Return the message in the outbox queue.
    """获取outbox队列状态"""
    status = {}
    # 遍历每个节点
    for peer, priority_queues in queues.items():
        peer_status = {
            "total_messages": sum(len(q) for q in priority_queues.values()),
            "priority_breakdown": {
                priority: len(queue) for priority, queue in priority_queues.items()
            }
        }
        status[peer] = peer_status
    
    return status


def get_drop_stats():
    # Return the drop states (`drop_stats`).
    """获取丢弃的消息统计"""
    return drop_stats