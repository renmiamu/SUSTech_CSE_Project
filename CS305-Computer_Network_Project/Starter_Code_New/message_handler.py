import json
import threading
import time
import hashlib
import random
from collections import defaultdict
from peer_discovery import handle_hello_message, known_peers, peer_config
from inv_message import create_inv, get_inventory
from peer_manager import update_peer_heartbeat, record_offense, create_pong, handle_pong
from transaction import add_transaction
from outbox import enqueue_message, gossip_message
from utils import generate_message_id
import logging
import dashboard  # 导入dashboard模块以使用消息记录功能

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# === Global State ===
SEEN_EXPIRY_SECONDS = 600  # 10 minutes
seen_message_ids = {}
seen_txs = set()
redundant_blocks = 0
redundant_txs = 0
message_redundancy = {}
peer_inbound_timestamps = defaultdict(list)
drop_stats = defaultdict(int)  # 记录每种消息类型的丢弃次数


# === Inbound Rate Limiting ===
INBOUND_RATE_LIMIT = 10
INBOUND_TIME_WINDOW = 10  # seconds

def is_inbound_limited(peer_id):
    # Record the timestamp when receiving message from a sender.
    """检查发送者是否超过入站速率限制"""
    current_time = time.time()
    
    # 确保键是字符串类型
    str_peer_id = str(peer_id)
    
    # 记录当前时间戳
    peer_inbound_timestamps[str_peer_id].append(current_time)
    
    # 删除过期的时间戳
    peer_inbound_timestamps[str_peer_id] = [ts for ts in peer_inbound_timestamps[str_peer_id] 
                                      if current_time - ts <= INBOUND_TIME_WINDOW]
    # Check if the number of messages sent by the sender exceeds `INBOUND_RATE_LIMIT` 
    # during the `INBOUND_TIME_WINDOW`. If yes, return `TRUE`. If not, return `FALSE`.
     # 检查剩余的时间戳数量是否超过入站速率限制
    return len(peer_inbound_timestamps[str_peer_id]) > INBOUND_RATE_LIMIT

# ===  Redundancy Tracking ===

def get_redundancy_stats():
    # Return the times of receiving duplicated messages (`message_redundancy`).
    """返回重复消息次数的统计信息"""
    return message_redundancy

def get_drop_stats():
    """获取消息丢弃统计"""
    return dict(drop_stats)

# === Main Message Dispatcher ===
def dispatch_message(msg, self_id, self_ip):
    """处理接收到的消息"""
    try:
        msg_type = msg.get("type")
        logger.debug(f"[{self_id}] 收到消息: {msg_type}, 内容: {msg}")
        
        # 消息合法性检查
        if not msg_type:
            logger.warning(f"收到无类型消息: {msg}")
            drop_stats["INVALID"] += 1
            return
        
        # 获取消息发送者
        sender_id = msg.get("sender_id")
        if not sender_id:
            sender_id = msg.get("peer_id")
            
        
        #  Check if the message has been seen in `seen_message_ids` to prevent replay attacks. 
        # If yes, drop the message and add one to `message_redundancy`. 
        # If not, add the message ID to `seen_message_ids`.
        # 检查消息ID，防止重放攻击
        msg_id = msg.get("message_id", str(hash(str(msg)))) #为消息生成一个唯一标识符（ID）
        current_time = time.time()
        if msg_id in seen_message_ids:
                if current_time - seen_message_ids[msg_id] < SEEN_EXPIRY_SECONDS:
                    logger.warning(f"收到来自节点 {sender_id} 的重复消息，类型为{msg_type}，丢弃")
                    message_redundancy[msg_id] = message_redundancy.get(msg_id, 0) + 1
                    drop_stats["DUPLICATE"] += 1
                    return
        # 记录消息ID和时间戳
        seen_message_ids[msg_id] = current_time
        
        # 检查入站速率限制
        if is_inbound_limited(sender_id):
            logger.warning(f"节点 {sender_id} 超过入站速率限制")
            drop_stats["RATE_LIMITED"] += 1
            return
        
        # Check if the sender exists in the `blacklist` of `peer_manager.py`. If yes, drop the message.
        # 检查节点是否在黑名单中
        from peer_manager import blacklist
        if str(sender_id) in blacklist:
            logger.warning(f"丢弃来自黑名单节点 {sender_id} 的消息")
            drop_stats["BLACKLISTED"] += 1
            return
        
        if msg_type == "RELAY":

            # Check if the peer is the target peer.
            # If yes, extract the payload and recall the function `dispatch_message` to process the payload.
            # If not, forward the message to target peer using the function `enqueue_message` in `outbox.py`.
            target_id = msg.get("target_id")
            payload = msg.get("payload", {})
            
            logger.info(f"收到RELAY消息，目标节点: {target_id}, 发送者: {sender_id}")
            # 记录接收到的消息
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            if target_id == self_id:
                logger.info(f"本节点是RELAY消息的目标节点，处理payload")
                if payload:
                    dispatch_message(payload, self_id, self_ip)
                else:
                    logger.warning(f"RELAY消息中没有payload")
            else:
                from outbox import enqueue_message
                # 检查目标是否在已知节点列表中
                if target_id in known_peers:
                    target_ip, target_port = known_peers[target_id]
                    logger.info(f"转发RELAY消息到目标节点 {target_id} ({target_ip}:{target_port})")
                    enqueue_message(target_id, target_ip, target_port, msg)
                else:
                    logger.warning(f"无法转发RELAY消息，目标节点 {target_id} 不在已知节点列表中")

        elif msg_type == "HELLO":
            #  Call the function `handle_hello_message` in `peer_discovery.py` to process the message.
            from peer_discovery import handle_hello_message
            # 记录接收到的消息
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            logger.info(f"收到HELLO消息：发送者={msg.get('sender_id')}, IP={msg.get('ip')}, 端口={msg.get('port')}")
            new_peers = handle_hello_message(msg, self_id)
            if new_peers:
                logger.info(f"通过HELLO消息发现新节点: {new_peers}")
            else:
                logger.info("没有发现新节点")

        elif msg_type == "BLOCK":
            block_id = msg.get("block_id")
            # Check the correctness of block ID. 
            # If incorrect, record the sender's offence using the function `record_offence` in `peer_manager.py`.
            from block_handler import handle_block,compute_block_hash
            
            # 首先获取发送节点的ID，使用peer_id
            block_sender_id = msg.get("peer_id") 
            # 记录消息
            from dashboard import log_received_message
            log_received_message(block_sender_id, self_id, msg_type, msg)
            
            # 验证区块ID是否正确
            computed_hash = compute_block_hash(msg)
            logger.warning(f"计算哈希={computed_hash}, 提供哈希={msg['block_id']}")
            if computed_hash != msg["block_id"]:
                logger.warning(f"来自节点 {block_sender_id} 的区块ID验证失败: 计算哈希={computed_hash}, 提供哈希={msg['block_id']}")
                # 将节点记录为恶意节点
                record_offense(block_sender_id)
                logger.warning(f"节点 {block_sender_id} 已记录违规行为，将被加入黑名单")
                return
            logger.warning(f"节点 {block_sender_id} 区块id验证通过")
            #  Call the function `handle_block` in `block_handler.py` to process the block.
            # 处理区块
            logger.info(f"接收到BLOCK消息，区块ID: {block_id}, 发送者: {block_sender_id}")
            
            
            
            handle_block(msg, self_id)
                 
            # Call the function `create_inv` to create an `INV` message for the block.
            # Broadcast the `INV` message to known peers using the function `gossip_message` in `outbox.py`.
            # 创建并广播INV消息
            from inv_message import create_inv
            inv_msg = create_inv(self_id, [block_id])
            from outbox import gossip_message
            gossip_message(self_id, inv_msg)
            
            #INV消息的工作流程
            #触发条件：当节点验证并接受一个新区块后
            #消息创建：通过 create_inv 函数创建INV消息
            #消息传播：通过 gossip_message 将INV消息传播给网络中的其他节点
            #接收处理：其他节点收到INV消息后，会检查自己是否已有这些数据
            #数据请求：如果没有，会发送GETDATA消息请求完整数据
            


        elif msg_type == "TX":
            tx_id = msg.get("id")
            logger.info(f"收到来自节点{msg['from']}的transaction消息")
            # Check the correctness of transaction ID. 
            # If incorrect, record the sender's offence using the function `record_offence` in `peer_manager.py`.
            # 验证交易ID正确性
            from transaction import compute_hash as compute_tx_hash
            # 记录消息
            from dashboard import log_received_message
            log_received_message(msg['from'], self_id, msg_type, msg)
            if compute_tx_hash(msg) != msg["id"]:
                record_offense(msg["from"])
                logger.warning(f"来自节点{msg['from']}的transaction消息id验证不通过,丢弃")
                return
            # Add the transaction to `tx_pool` using the function `add_transaction` in `transaction.py`.
            # 添加交易到交易池
            if tx_id not in seen_txs:
                seen_txs.add(tx_id)
                from transaction import add_transaction
                add_transaction(msg)                
            # Broadcast the transaction to known peers using the function `gossip_message` in `outbox.py`.
                # 广播交易
                from outbox import gossip_message
                gossip_message(self_id, msg)

        elif msg_type == "PING":
            # 记录消息
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            # Update the last ping time using the function `update_peer_heartbeat` in `peer_manager.py`.
            # 更新the last ping time
            from peer_manager import update_peer_heartbeat
            update_peer_heartbeat(sender_id)
            
            # Create a `pong` message using the function `create_pong` in `peer_manager.py`.
            from peer_manager import create_pong
            pong_msg = create_pong(self_id, msg.get("timestamp"))
            
            # Send the `pong` message to the sender using the function `enqueue_message` in `outbox.py`.
            #发送PONG消息
            from outbox import enqueue_message
            # 检查发送者是否在已知节点列表中
            if sender_id in known_peers:
                enqueue_message(sender_id, known_peers[sender_id][0], known_peers[sender_id][1], pong_msg)
            else:
                logger.warning(f"无法回复PING消息，发送者 {sender_id} 不在已知节点列表中")
            

        elif msg_type == "PONG":
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            # Update the last ping time using the function `update_peer_heartbeat` in `peer_manager.py`.
            from peer_manager import update_peer_heartbeat, handle_pong
            update_peer_heartbeat(sender_id)
            #  Call the function `handle_pong` in `peer_manager.py` to handle the message.
            handle_pong(msg)
            

        elif msg_type == "INV":
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            rsv_block_ids = msg.get("block_ids", [])
            # Read all blocks IDs in the local blockchain 
            # using the function `get_inventory` in `block_handler.py`.
            # 获取本地区块链中的所有区块ID
            from block_handler import get_inventory
            local_blocks = get_inventory()
            # Compare the local block IDs with those in the message.
            # 比较并找出缺失的区块
            missing_blocks = [block_id for block_id in rsv_block_ids if block_id not in local_blocks]
                    
                # If there are missing blocks, create a `GETBLOCK` message to request the missing blocks from the sender.
                # Send the `GETBLOCK` message to the sender using the function `enqueue_message` in `outbox.py`.
            if missing_blocks and sender_id in known_peers:
                # 创建GETBLOCK消息
                from block_handler import create_getblock
                getblock_msg = create_getblock(self_id, missing_blocks)
                
                # 获取发送者的IP和端口
                sender_ip, sender_port = known_peers[sender_id]
                
                # 先记录将要发送的GETBLOCK消息
                from dashboard import log_sent_message
                log_sent_message(self_id, sender_id, "GETBLOCK", getblock_msg)
                
                # 导入enqueue_message函数
                from outbox import enqueue_message
                
                # 发送GETBLOCK消息
                enqueue_message(sender_id, sender_ip, sender_port, getblock_msg)
                
                logger.info(f"向节点 {sender_id} 请求缺失的区块: {missing_blocks}")
            else:
                if not missing_blocks:
                    logger.info(f"收到节点 {sender_id} 的INV消息，但没有缺失的区块")
                elif sender_id not in known_peers:
                    logger.warning(f"收到节点 {sender_id} 的INV消息，但该节点不在已知节点列表中")

        elif msg_type == "GETBLOCK":
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
        # TODO: Extract the block IDs from the message.
            requested_block_ids = msg.get("requested_ids", [])
        # TODO: Get the blocks from the local blockchain according to the block IDs using the function `get_block_by_id` in `block_handler.py`.
            
            for block_id in requested_block_ids:
                from block_handler import get_block_by_id
                block = get_block_by_id(block_id)
                if not block:
                    # TODO: If the blocks are not in the local blockchain, create a `GETBLOCK` message to request the missing blocks from known peers.
                    from block_handler import create_getblock
                    getblock_msg = create_getblock(self_id, [block_id])
                    if sender_id in known_peers:
                        sender_ip, sender_port = known_peers[sender_id]
                        # TODO: Send the `GETBLOCK` message to known peers using the function `enqueue_message` in `outbox.py`.
                        from outbox import enqueue_message
                        enqueue_message(sender_id, sender_ip, sender_port, getblock_msg)
                        logger.info(f"向节点 {sender_id} 请求缺失的区块: {block_id}")
                        # TODO: Retry getting the blocks from the local blockchain. If the retry times exceed 3, drop the message.
                        retry_count = 0;
                        while True:
                            block = get_block_by_id(block_id)
                            if block:
                                break
                            retry_count += 1
                            if retry_count >= 3:
                                logger.warning(f"区块请求 {msg.get('message_id', '未知ID')} 重试次数已达上限 ({retry_count}/3)，放弃处理")
                                return
                # TODO: If the blocks exist in the local blockchain, 
                # send the blocks one by one to the requester using the function `enqueue_message` in `outbox.py`.
                # 如果区块存在，发送给请求者
                if sender_id in known_peers:
                    sender_ip, sender_port = known_peers[sender_id]
                    from outbox import enqueue_message
                    enqueue_message(sender_id, sender_ip, sender_port, block)
                    logger.info(f"发送区块 {block_id} 到节点 {sender_id}")
                    
                    # 在接收方调用log_received_message记录对方收到的消息
                    # 注意：这里模拟接收方记录接收到的消息，因此sender和receiver需要互换
                    from dashboard import log_received_message
                    log_received_message(self_id, sender_id, "BLOCK", block)
                else:
                    logger.warning(f"无法发送区块 {block_id}，节点 {sender_id} 不在已知节点列表中")   
                
        elif msg_type == "GET_BLOCK_HEADERS":
            
            # Read all block header in the local blockchain and store them in `headers`.
            # Create a `BLOCK_HEADERS` message, which should include `{message type, sender's ID, headers}`.
            from block_handler import header_store
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            
            # 获取请求的高度范围
            start_height = msg.get("start_height", 0)
            end_height = msg.get("end_height", float('inf'))  # 如果未指定，则假设为无限大
            is_new_node = msg.get("is_new_node", False)
            
            # 从区块头存储中筛选指定高度范围的区块头
            from block_handler import header_store, get_headers_by_height_range
            
            # 筛选出落在高度范围内的区块头
            filtered_headers = get_headers_by_height_range(start_height, end_height)
            
            # 记录日志
            logger.info(f"收到区块头请求: 高度范围[{start_height}-{end_height}], 发送{len(filtered_headers)}个区块头")
            
            # 创建响应消息
            headers_msg = {
                "type": "BLOCK_HEADERS",
                "sender_id": self_id,
                "headers": filtered_headers,
                "is_full_chain": is_new_node,  # 如果是新节点请求，标记为完整链数据
                "start_height": start_height,
                "end_height": min(end_height, max([h.get("height", 0) for h in filtered_headers]) if filtered_headers else end_height),
                "message_id": generate_message_id()
            }
            
            # Send the `BLOCK_HEADERS` message to the requester using the function `enqueue_message` in `outbox.py`.
            from outbox import enqueue_message
            if sender_id in known_peers:
                sender_ip, sender_port = known_peers[sender_id]
                enqueue_message(sender_id, sender_ip, sender_port, headers_msg)
                
            # 如果是新节点且请求的是初始区块头，考虑主动发送一些最新区块
            if is_new_node and start_height == 0:
                # 获取一些最新区块（例如最新的10个区块）
                from block_handler import get_blocks_since_height, get_latest_block_height
                latest_height = get_latest_block_height()
                start_height_for_blocks = max(0, latest_height - 10)
                recent_blocks = get_blocks_since_height(start_height_for_blocks)
                
                if recent_blocks:
                    # 创建批量区块响应
                    batch_response = {
                        "type": "BLOCK_BATCH",
                        "sender_id": self_id,
                        "blocks": recent_blocks,
                        "has_more": start_height_for_blocks > 0,  # 如果还有更早的区块，表示还有更多
                        "next_height": 0 if start_height_for_blocks <= 0 else start_height_for_blocks,  # 下一批从哪个高度开始
                        "message_id": generate_message_id()
                    }
                    
                    # 发送批量区块响应
                    if sender_id in known_peers:
                        sender_ip, sender_port = known_peers[sender_id]
                        enqueue_message(sender_id, sender_ip, sender_port, batch_response)
                        logger.info(f"向新节点 {sender_id} 主动发送最新 {len(recent_blocks)} 个区块")

        elif msg_type == "BLOCK_HEADERS":
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            
            received_headers = msg.get("headers", [])
            is_full_chain = msg.get("is_full_chain", False)
            start_height = msg.get("start_height", 0)
            end_height = msg.get("end_height", float('inf'))
            
            from peer_discovery import peer_flags
            from block_handler import header_store, received_blocks
            
            # 检查接收到的区块头是否为空
            if not received_headers:
                logger.warning(f"从节点 {sender_id} 接收到空的区块头列表")
                return
            
            # 构建本地区块链和收到的区块头的ID集合，用于快速查找
            local_block_ids = {block.get("block_id", "") for block in received_blocks}
            local_header_ids = {header.get("block_id", "") for header in header_store}
            received_header_ids = {header.get("block_id", "") for header in received_headers}
            
            # 完整链同步模式 - 用于新节点快速同步
            if is_full_chain:
                logger.info(f"从节点 {sender_id} 接收到完整链区块头，共 {len(received_headers)} 个，高度范围[{start_height}-{end_height}]")
                
                # 检查是否是轻量级节点
                is_lightweight = False
                if self_id in peer_flags and peer_flags[self_id].get("light", False):
                    is_lightweight = True
                    
                if is_lightweight:
                    # 轻量级节点直接更新区块头存储
                    # 首先删除收到范围内的旧区块头，然后添加新的
                    header_store = [h for h in header_store if h.get("height", 0) < start_height or h.get("height", 0) > end_height]
                    for header in received_headers:
                        header_store.append(header)
                    logger.info(f"轻量级节点更新区块头: 已添加 {len(received_headers)} 个")
                else:
                    # 完整节点需要请求缺失的完整区块
                    missing_blocks = []
                    for header in received_headers:
                        block_id = header.get("block_id", "")
                        if block_id and (block_id not in local_block_ids) and (block_id not in local_header_ids):
                            missing_blocks.append(block_id)
                    
                    if missing_blocks:
                        # 创建GETBLOCK消息请求缺失区块，但限制每次请求的数量
                        batch_size = 20  # 每批请求20个区块
                        for i in range(0, len(missing_blocks), batch_size):
                            batch = missing_blocks[i:i+batch_size]
                            from block_handler import create_getblock
                            getblock_msg = create_getblock(self_id, batch)
                            
                            if sender_id in known_peers:
                                sender_ip, sender_port = known_peers[sender_id]
                                from outbox import enqueue_message
                                enqueue_message(sender_id, sender_ip, sender_port, getblock_msg)
                                logger.info(f"向节点 {sender_id} 请求第 {i//batch_size + 1} 批缺失区块: {len(batch)} 个")
                        
                        # 如果还有下一批区块头需要同步，发送请求
                        if end_height < float('inf') and len(received_headers) > 0:
                            next_start = end_height + 1
                            next_end = next_start + 99  # 每次请求100个区块头
                            
                            # 创建下一批区块头请求
                            next_headers_request = {
                                "type": "GET_BLOCK_HEADERS",
                                "sender_id": self_id,
                                "start_height": next_start,
                                "end_height": next_end,
                                "is_new_node": True,
                                "message_id": generate_message_id()
                            }
                            
                            if sender_id in known_peers:
                                sender_ip, sender_port = known_peers[sender_id]
                                enqueue_message(sender_id, sender_ip, sender_port, next_headers_request)
                                logger.info(f"请求下一批区块头: {next_start}-{next_end}")
            else:
                # 原有的处理逻辑保持不变
                # 检查区块头链的连续性
                is_valid = True
                missing_blocks = []
                
                for header in received_headers:
                    block_id = header.get("block_id", "")
                    prev_block_id = header.get("prev_block_id", "")
                    
                    # 检查前一个区块是否存在
                    if prev_block_id and (prev_block_id not in local_block_ids) and (prev_block_id not in local_header_ids) and (prev_block_id not in received_header_ids):
                        is_valid = False
                        logger.warning(f"区块头链不连续: 区块 {block_id} 的前置区块 {prev_block_id} 不存在")
                        break
                        
                    # 记录本地不存在的区块
                    if (block_id not in local_block_ids) and (block_id not in local_header_ids):
                        missing_blocks.append(block_id)
                        
                # 处理有效的区块头链
                if is_valid:
                    # 检查当前节点是轻量级还是完整节点
                    is_lightweight = False
                    if self_id in peer_flags and peer_flags[self_id].get("light", False):
                        is_lightweight = True
                        
                    if is_lightweight:
                        # 轻量级节点只存储区块头
                        for header in received_headers:
                            block_id = header.get("block_id", "")
                            if block_id not in local_header_ids:
                                header_store.append(header)
                                logger.info(f"轻量级节点添加区块头: {block_id}")
                    else:
                        # 完整节点需要请求缺失的完整区块
                        if missing_blocks:
                            from block_handler import create_getblock
                            getblock_msg = create_getblock(self_id, missing_blocks)
                            
                            if sender_id in known_peers:
                                sender_ip, sender_port = known_peers[sender_id]
                                from outbox import enqueue_message
                                enqueue_message(sender_id, sender_ip, sender_port, getblock_msg)
                                logger.info(f"完整节点请求缺失的区块: {missing_blocks}")
                else:
                    logger.warning(f"丢弃来自节点 {sender_id} 的区块头消息，因为包含孤儿区块")
        elif msg_type == "BLOCK_BATCH":
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            
            batch_blocks = msg.get("blocks", [])
            has_more = msg.get("has_more", False)
            next_height = msg.get("next_height", 0)
            
            if not batch_blocks:
                logger.warning(f"从节点 {sender_id} 接收到空的区块批次")
                return
                
            # 处理收到的批量区块
            from block_handler import handle_block
            processed_count = 0
            
            for block in batch_blocks:
                try:
                    # 验证并处理每个区块
                    handle_block(block, self_id)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"处理批量区块时出错: {e}")
            
            logger.info(f"成功处理 {processed_count}/{len(batch_blocks)} 个批量区块")
            
            # 尝试更新区块同步状态
            try:
                from block_handler import update_block_sync_status
                if 'update_block_sync_status' in globals():
                    update_block_sync_status()
                    logger.info("批量区块处理后，更新了区块同步状态")
            except Exception as e:
                logger.error(f"更新区块同步状态失败: {e}")
            
            # 如果还有更多区块需要同步，继续请求
            if has_more and next_height > 0:
                # 创建新的GET_LATEST_BLOCK请求，标记为新节点请求
                latest_block_request = {
                    "type": "GET_LATEST_BLOCK",
                    "sender_id": self_id,
                    "current_height": next_height,
                    "is_new_node": True,
                    "message_id": generate_message_id()
                }
                
                # 发送请求获取下一批区块
                from outbox import enqueue_message
                if sender_id in known_peers:
                    sender_ip, sender_port = known_peers[sender_id]
                    enqueue_message(sender_id, sender_ip, sender_port, latest_block_request)
                    logger.info(f"请求下一批区块，从高度 {next_height} 开始")
                    
        elif msg_type == "GET_MEMPOOL":
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            
            # 获取本地交易池中的交易
            from transaction import get_recent_transactions
            mempool_txs = get_recent_transactions()
            
            # 创建响应消息
            response = {
                "type": "MEMPOOL_DATA",
                "sender_id": self_id,
                "transactions": mempool_txs,
                "message_id": generate_message_id()
            }
            
            # 发送响应
            from outbox import enqueue_message
            if sender_id in known_peers:
                sender_ip, sender_port = known_peers[sender_id]
                enqueue_message(sender_id, sender_ip, sender_port, response)
                logger.info(f"向节点 {sender_id} 发送交易池数据，共 {len(mempool_txs)} 条交易")

        elif msg_type == "MEMPOOL_DATA":
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            
            # 处理接收到的交易池数据
            transactions = msg.get("transactions", [])
            
            if not transactions:
                logger.info(f"从节点 {sender_id} 接收到空的交易池数据")
                return
            
            # 添加交易到本地交易池
            from transaction import TransactionMessage, add_transaction
            added_count = 0
            
            for tx_data in transactions:
                try:
                    # 从字典创建交易对象
                    tx = TransactionMessage.from_dict(tx_data)
                    # 添加到交易池
                    add_transaction(tx)
                    added_count += 1
                except Exception as e:
                    logger.error(f"处理交易时出错: {e}")
            
            logger.info(f"从节点 {sender_id} 同步交易池数据，接收 {len(transactions)} 条交易，成功添加 {added_count} 条")
            
        elif msg_type == "MEMPOOL_TRANSFER":
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            
            # 处理交易池转移
            transactions = msg.get("transactions", [])
            batch = msg.get("batch", 1)
            total_batches = msg.get("total_batches", 1)
            
            if not transactions:
                logger.info(f"从节点 {sender_id} 接收到空的交易池转移批次 {batch}/{total_batches}")
                return
            
            # 添加交易到本地交易池
            from transaction import TransactionMessage, add_transaction
            added_count = 0
            
            for tx_data in transactions:
                try:
                    # 从字典创建交易对象
                    tx = TransactionMessage.from_dict(tx_data)
                    # 添加到交易池
                    add_transaction(tx)
                    added_count += 1
                except Exception as e:
                    logger.error(f"处理交易时出错: {e}")
            
            logger.info(f"接收节点 {sender_id} 的交易池转移 (批次 {batch}/{total_batches})：" 
                       f"接收 {len(transactions)} 条交易，成功添加 {added_count} 条")
                       
        elif msg_type == "NEW_PEER":
            # 处理新节点通知消息
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            
            # 调用peer_discovery中的处理函数
            from peer_discovery import handle_new_peer
            new_peers = handle_new_peer(msg, self_id)
            
            # 通知仪表盘有新节点加入
            if new_peers:
                from dashboard import notify_nodes_discovered
                notify_nodes_discovered(new_peers)
                logger.info(f"通过NEW_PEER消息发现新节点: {new_peers}")
                
                # 更新动态配置
                try:
                    from dynamic_node_manager import update_dynamic_config
                    update_dynamic_config()
                except ImportError:
                    pass
            
        elif msg_type == "GOODBYE":
            # 处理节点退出消息
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            
            # 调用peer_discovery中的处理函数
            from peer_discovery import handle_goodbye_message
            handle_goodbye_message(msg)
            
            # 通知仪表盘有节点离开
            from dashboard import notify_node_left
            notify_node_left(sender_id, msg.get("reason", "unknown"))
            
        elif msg_type == "GET_LATEST_BLOCK":
            from dashboard import log_received_message
            log_received_message(sender_id, self_id, msg_type, msg)
            
            # 检查是否是新节点请求
            is_new_node = msg.get("is_new_node", False)
            
            # 获取发送者当前区块高度
            sender_height = msg.get("current_height", 0)
            
            # 获取本地最新区块
            from block_handler import get_latest_block, get_blocks_since_height
            latest_block = get_latest_block()
            
            if not latest_block:
                logger.warning(f"本地没有区块可发送给节点 {sender_id}")
                return
                
            # 如果是新节点且其区块高度远低于当前节点，提供分批同步
            if is_new_node and sender_height < latest_block.get("height", 0) - 50:
                # 获取新节点所需的区块批次
                # 为避免一次发送过多数据，限制每次最多发送50个区块
                missing_blocks = get_blocks_since_height(sender_height, limit=50)
                
                # 创建批量区块响应
                batch_response = {
                    "type": "BLOCK_BATCH",
                    "sender_id": self_id,
                    "blocks": missing_blocks,
                    "has_more": sender_height + len(missing_blocks) < latest_block.get("height", 0),
                    "next_height": sender_height + len(missing_blocks),
                    "message_id": generate_message_id()
                }
                
                # 发送批量区块响应
                from outbox import enqueue_message
                if sender_id in known_peers:
                    sender_ip, sender_port = known_peers[sender_id]
                    enqueue_message(sender_id, sender_ip, sender_port, batch_response)
                    logger.info(f"向新节点 {sender_id} 发送批量区块: {sender_height} -> {sender_height + len(missing_blocks)}")
            else:
                # 正常处理，仅发送最新区块
                from outbox import enqueue_message
                if sender_id in known_peers:
                    sender_ip, sender_port = known_peers[sender_id]
                    enqueue_message(sender_id, sender_ip, sender_port, latest_block)
                    logger.info(f"向节点 {sender_id} 发送最新区块: {latest_block.get('block_id')}")
        else:
            logger.warning(f"[{self_id}] 未知消息类型: {msg_type}")
    
    except Exception as e:
        logger.error(f"处理消息时发生异常: {e}", exc_info=True)