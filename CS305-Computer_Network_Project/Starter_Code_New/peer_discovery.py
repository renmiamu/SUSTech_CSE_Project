import json, time, threading
from utils import generate_message_id


known_peers = {}        # { peer_id: (ip, port) }
peer_flags = {}         # { peer_id: { 'nat': True/False, 'light': True/False } }
reachable_by = {}       # { peer_id: { set of peer_ids who can reach this peer }}
peer_config={}

def start_peer_discovery(self_id, self_info):
    from outbox import enqueue_message
    
    # 更新peer_config
    global peer_config
    peer_config = {
        "self_id": self_id,
        "ip": self_info["ip"],
        "port": self_info["port"],
        "nat": self_info.get("nat", False),
        "light": self_info.get("light", False)
    }
    
    def loop():
        # TODO: Define the JSON format of a `hello` message, which should include: `{message type, sender's ID, IP address, port, flags, and message ID}`. 
        # A `sender's ID` can be `peer_port`. 
        # The `flags` should indicate whether the peer is `NATed or non-NATed`, and `full or lightweight`. 
        # The `message ID` can be a random number.

        # TODO: Send a `hello` message to all known peers and put the messages into the outbox queue.
        
        
        # 创建HELLO消息
        msg = {
            "type": "HELLO",
            "sender_id": self_id,
            "ip": self_info["ip"],
            "port": self_info["port"],
            "flags": {
                "nat": self_info.get("nat", False),
                "light": self_info.get("light", False),
                "new_node": True  # 标记为新节点，第一次发送时使用
            },
            "message_id": generate_message_id()
        }

        # 首先向所有已知节点发送HELLO消息，表明自己是新节点
        for peer_id, (peer_ip, peer_port) in known_peers.items():
            if peer_id != self_id:  # 不发送给自己
                enqueue_message(peer_id, peer_ip, peer_port, msg)
                
        # 等待初始响应
        time.sleep(5)
        
        # 之后定期发送HELLO消息，但不再标记为新节点
        while True:
            msg["flags"]["new_node"] = False  # 不再是新节点
            for peer_id, (peer_ip, peer_port) in known_peers.items():
                if peer_id != self_id:  # 不发送给自己
                    enqueue_message(peer_id, peer_ip, peer_port, msg)
                
            # 每30秒发送一次HELLO消息
            time.sleep(30)

    threading.Thread(target=loop, daemon=True).start()

def handle_hello_message(msg, self_id):
    # TODO: Read information in the received `hello` message.
     
    # TODO: If the sender is unknown, add it to the list of known peers (`known_peer`) and record their flags (`peer_flags`).
     
    # TODO: Update the set of reachable peers (`reachable_by`).

    new_peers = []

    sender_id = msg.get("sender_id")
    sender_ip = msg.get("ip")
    sender_port = msg.get("port")
    sender_flags = msg.get("flags", {})

    # 不处理自己的HELLO
    if sender_id == self_id:
        return []

    new_peers = []

    # 检查是否是新节点
    is_new_node = sender_flags.get("new_node", False)

    # 添加到已知节点表
    if sender_id not in known_peers:
        known_peers[sender_id] = (sender_ip, sender_port)
        new_peers.append(sender_id)
        
        # 如果是新节点，向其他所有节点广播NEW_PEER消息
        if is_new_node:
            broadcast_new_peer(sender_id, sender_ip, sender_port, sender_flags, self_id)
    
    # 无论节点是否已知，都更新flags信息
    peer_flags[sender_id] = {
        "nat": sender_flags.get("nat", False),
        "light": sender_flags.get("light", False)
    }

    # 可达性更新
    if sender_id not in reachable_by:
        reachable_by[sender_id] = set()

    reachable_by[sender_id].add(self_id)

    return new_peers

def broadcast_new_peer(new_peer_id, new_peer_ip, new_peer_port, new_peer_flags, self_id):
    """向所有已知节点广播新节点信息"""
    from outbox import enqueue_message
    
    msg = {
        "type": "NEW_PEER",
        "new_peer_id": new_peer_id,
        "new_peer_ip": new_peer_ip,
        "new_peer_port": new_peer_port,
        "new_peer_flags": new_peer_flags,
        "sender_id": self_id,
        "message_id": generate_message_id()
    }
    
    for peer_id, (peer_ip, peer_port) in known_peers.items():
        if peer_id != new_peer_id and peer_id != self_id:  # 不发送给新节点自己和自己
            enqueue_message(peer_id, peer_ip, peer_port, msg)

def request_peer_list(self_id):
    """请求完整的节点列表"""
    from outbox import enqueue_message
    import random
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 选择几个已知节点作为种子节点
    seed_peers = list(known_peers.items())
    if len(seed_peers) > 3:
        seed_peers = random.sample(seed_peers, 3)  # 最多选择3个
    
    msg = {
        "type": "GET_PEERS",
        "sender_id": self_id,
        "message_id": generate_message_id()
    }
    
    # 向选定的节点发送请求
    for peer_id, (peer_ip, peer_port) in seed_peers:
        if peer_id != self_id:
            enqueue_message(peer_id, peer_ip, peer_port, msg)
            logger.info(f"向节点 {peer_id} 请求节点列表")

def handle_get_peers(msg, self_id):
    """处理GET_PEERS请求，返回已知节点列表"""
    import logging
    logger = logging.getLogger(__name__)
    
    sender_id = msg.get("sender_id")
    
    if sender_id not in known_peers:
        logger.warning(f"未知节点 {sender_id} 请求节点列表，忽略")
        return  # 未知节点，忽略请求
    
    sender_ip, sender_port = known_peers[sender_id]
    
    # 准备节点列表响应
    peers_data = {}
    for peer_id, (ip, port) in known_peers.items():
        if peer_id != sender_id and peer_id != self_id:
            peers_data[peer_id] = {
                "ip": ip,
                "port": port,
                "flags": peer_flags.get(peer_id, {})
            }
    
    response = {
        "type": "PEERS_LIST",
        "sender_id": self_id,
        "peers": peers_data,
        "message_id": generate_message_id()
    }
    
    # 发送响应
    from outbox import enqueue_message
    enqueue_message(sender_id, sender_ip, sender_port, response)
    logger.info(f"向节点 {sender_id} 发送节点列表，包含 {len(peers_data)} 个节点")

def handle_peers_list(msg, self_id):
    """处理PEERS_LIST响应，更新已知节点"""
    import logging
    logger = logging.getLogger(__name__)
    
    peers_data = msg.get("peers", {})
    
    new_peers = []
    
    for peer_id, info in peers_data.items():
        if peer_id != self_id and peer_id not in known_peers:
            ip = info.get("ip")
            port = info.get("port")
            flags = info.get("flags", {})
            
            # 添加到已知节点
            known_peers[peer_id] = (ip, port)
            peer_flags[peer_id] = flags
            new_peers.append(peer_id)
            logger.info(f"从节点列表响应中添加新节点: {peer_id}")
    
    return new_peers

def handle_new_peer(msg, self_id):
    """处理NEW_PEER消息，添加新节点"""
    import logging
    logger = logging.getLogger(__name__)
    
    new_peer_id = msg.get("new_peer_id")
    new_peer_ip = msg.get("new_peer_ip")
    new_peer_port = msg.get("new_peer_port")
    new_peer_flags = msg.get("new_peer_flags", {})
    
    # 检查是否是新节点
    if new_peer_id in known_peers:
        return []  # 已知节点，无需处理
    
    # 添加新节点
    known_peers[new_peer_id] = (new_peer_ip, new_peer_port)
    peer_flags[new_peer_id] = new_peer_flags
    
    logger.info(f"通过NEW_PEER消息添加新节点: {new_peer_id}")
    
    # 更新动态配置
    try:
        from dynamic_node_manager import update_dynamic_config
        update_dynamic_config()
    except ImportError:
        pass
    
    return [new_peer_id]

def handle_goodbye_message(msg):
    """处理节点退出消息，包括接收转移的交易"""
    import logging
    logger = logging.getLogger(__name__)
    
    sender_id = msg.get("sender_id")
    reason = msg.get("reason", "unknown")
    pending_transactions = msg.get("pending_transactions", [])
    has_more_transactions = msg.get("has_more_transactions", False)
    
    if sender_id in known_peers:
        logger.info(f"节点 {sender_id} 正在离开网络。原因: {reason}")
        
        # 处理附带的交易
        if pending_transactions:
            from transaction import TransactionMessage, add_transaction
            added_count = 0
            
            for tx_data in pending_transactions:
                try:
                    tx = TransactionMessage.from_dict(tx_data)
                    add_transaction(tx)
                    added_count += 1
                except Exception as e:
                    logger.error(f"处理离开节点的交易时出错: {e}")
                    
            logger.info(f"从离开的节点 {sender_id} 接收 {len(pending_transactions)} 条交易，成功添加 {added_count} 条")
            
            if has_more_transactions:
                logger.info(f"节点 {sender_id} 还有更多交易将通过MEMPOOL_TRANSFER消息发送")
        
        # 从已知节点中移除
        if sender_id in known_peers:
            del known_peers[sender_id]
        
        # 移除其他相关信息
        if sender_id in peer_flags:
            del peer_flags[sender_id]
        
        if sender_id in reachable_by:
            del reachable_by[sender_id]
        
        # 更新配置
        try:
            from dynamic_node_manager import update_dynamic_config
            update_dynamic_config()
        except ImportError:
            pass

def send_goodbye_message(self_id, reason="normal_shutdown"):
    """发送优雅退出通知，并转发未确认交易"""
    from outbox import enqueue_message
    from transaction import get_recent_transactions
    import logging
    import random
    import time
    
    logger = logging.getLogger(__name__)
    
    # 获取本地交易池中的交易
    pending_txs = get_recent_transactions()
    
    msg = {
        "type": "GOODBYE",
        "sender_id": self_id,
        "reason": reason,
        "pending_transactions": pending_txs if len(pending_txs) <= 100 else [],  # 限制大小
        "has_more_transactions": len(pending_txs) > 100,  # 指示是否有更多交易
        "message_id": generate_message_id(),
        "timestamp": time.time()
    }
    
    # 向所有已知节点广播退出消息
    for peer_id, (peer_ip, peer_port) in known_peers.items():
        if peer_id != self_id:
            enqueue_message(peer_id, peer_ip, peer_port, msg)
    
    # 如果交易太多，无法在GOODBYE消息中包含，则额外发送MEMPOOL_TRANSFER消息
    if len(pending_txs) > 100:
        # 将交易分批发送
        batch_size = 100
        active_peers = [peer_id for peer_id in known_peers.keys() 
                       if peer_id != self_id]
        
        if not active_peers:
            logger.warning("没有活跃节点可接收交易池转移")
            return
            
        # 随机选择一些活跃节点
        selected_peers = random.sample(active_peers, min(3, len(active_peers)))
        
        for i in range(0, len(pending_txs), batch_size):
            batch = pending_txs[i:i+batch_size]
            transfer_msg = {
                "type": "MEMPOOL_TRANSFER",
                "sender_id": self_id,
                "transactions": batch,
                "batch": i // batch_size + 1,
                "total_batches": (len(pending_txs) + batch_size - 1) // batch_size,
                "message_id": generate_message_id()
            }
            
            # 发送给选定的节点
            for peer_id in selected_peers:
                if peer_id in known_peers:
                    peer_ip, peer_port = known_peers[peer_id]
                    enqueue_message(peer_id, peer_ip, peer_port, transfer_msg)
                    
        logger.info(f"交易池转移：向 {len(selected_peers)} 个节点发送 {len(pending_txs)} 条交易")
    
    # 等待消息发送完成
    time.sleep(2)
    
    logger.info(f"[{self_id}] 正在优雅地退出网络")

def request_mempool_sync(self_id):
    """请求同步交易池中的交易"""
    from outbox import enqueue_message
    import logging
    import random
    
    logger = logging.getLogger(__name__)
    
    # 选择几个稳定节点作为同步源
    sync_sources = []
    for peer_id, (ip, port) in known_peers.items():
        if peer_id != self_id:
            sync_sources.append((peer_id, ip, port))
            if len(sync_sources) >= 3:
                break
    
    if not sync_sources:
        logger.warning("没有可用的节点来同步交易池")
        return
    
    # 随机选择一个节点
    if len(sync_sources) > 1:
        selected_source = random.choice(sync_sources)
    else:
        selected_source = sync_sources[0]
    
    msg = {
        "type": "GET_MEMPOOL",
        "sender_id": self_id,
        "message_id": generate_message_id()
    }
    
    # 发送请求
    peer_id, peer_ip, peer_port = selected_source
    enqueue_message(peer_id, peer_ip, peer_port, msg)
    logger.info(f"向节点 {peer_id} 请求交易池数据")

def get_headers_by_height_range(start_height, end_height, header_store):
    """获取指定高度范围内的区块头"""
    filtered_headers = []
    for header in header_store:
        header_height = header.get("height", 0)
        if start_height <= header_height <= end_height:
            filtered_headers.append(header)
    
    # 按高度排序
    filtered_headers.sort(key=lambda h: h.get("height", 0))
    return filtered_headers

