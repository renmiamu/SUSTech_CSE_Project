import time
import hashlib
import json
import threading
import random
import logging
from transaction import get_recent_transactions, clear_pool
from peer_discovery import known_peers, peer_config, peer_flags
from utils import generate_message_id

from outbox import enqueue_message, gossip_message
from peer_manager import record_offense

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

received_blocks = [] # The local blockchain. The blocks are added linearly at the end of the set.
header_store = [] # The header of blocks in the local blockchain. Used by lightweight peers.
orphan_blocks = {} # The block whose previous block is not in the local blockchain. Waiting for the previous block.

#sync change(new peer join in)
def request_block_sync(self_id, is_new_node=False):
    """请求区块同步，新节点有特殊处理"""
    # 创建消息
    if is_new_node:
        # 新节点的初始同步 - 分批请求区块
        current_height = get_latest_block_height()
        
        msg = {
            "type": "GET_BLOCK_HEADERS",
            "sender_id": self_id,
            "start_height": 0,
            "end_height": 99,  # 每次请求100个区块头
            "is_new_node": True,
            "message_id": generate_message_id()
        }
        
        logger.info(f"新节点 {self_id} 开始初始区块同步，请求高度范围[0-99]")
    else:
        # 常规同步
        msg = {
            "type": "GET_BLOCK_HEADERS",
            "sender_id": self_id,
            "message_id": generate_message_id()
        }
    
    # 发送消息到所有已知节点
    for peer_id, (ip, port) in known_peers.items():
        if peer_id != self_id:
            enqueue_message(peer_id, ip, port, msg)

def block_generation(self_id, MALICIOUS_MODE, interval=20):
    from inv_message import create_inv
    import threading
    
    # 添加一个锁用于同步区块生成
    genesis_lock = threading.Lock()
    waiting_for_sync = True
    sync_timeout = 30  # 等待同步的超时时间（秒）
    
    def mine():
        nonlocal waiting_for_sync
        
        # 等待区块同步完成或超时
        sync_start_time = time.time()
        
        while True:
            # 如果已经有区块或者等待超时，开始挖矿
            with genesis_lock:
                if len(received_blocks) > 0:
                    # 已经有区块了，不需要等待
                    waiting_for_sync = False
                elif time.time() - sync_start_time > sync_timeout:
                    # 超时了，假设没有其他节点可以同步，可以生成创世区块
                    logger.info(f"[{self_id}] 区块同步等待超时，准备生成创世区块")
                    waiting_for_sync = False
            
            # 如果不再等待同步，开始正常的区块生成循环
            if not waiting_for_sync:
                break
                
            # 继续等待
            time.sleep(2)
        
        # 开始正常的区块生成循环
        while True:
            time.sleep(interval)
    # TODO: Create a new block periodically using the function `create_dummy_block`.
            #new_block = create_dummy_block(self_id, MALICIOUS_MODE)
    # TODO: Create an `INV` message for the new block using the function `create_inv` in `inv_message.py`.
            # block_ids=[]
            # for block in received_blocks:
            #     block_ids.append(block["block_id"])
            #inv_msg=create_inv(self_id, [new_block["block_id"]])
    # TODO: Broadcast the `INV` message to known peers using the function `gossip` in `outbox.py`.
            #gossip_message(self_id, inv_msg)
            
            with genesis_lock:
                # 创建新区块
                try:
                    new_block = create_dummy_block(self_id, MALICIOUS_MODE)
                    # 创建INV消息
                    inv_msg = create_inv(self_id, [new_block["block_id"]])
                    # 广播INV消息
                    gossip_message(self_id, inv_msg)
                    logger.info(f"[{self_id}] 成功生成并广播新区块: {new_block['block_id']}, 高度: {new_block['height']}")
                except Exception as e:
                    logger.error(f"[{self_id}] 区块生成失败: {e}")
    
    threading.Thread(target=mine, daemon=True).start()
    
    # 提供一个更新同步状态的函数，在接收到区块时调用
    def update_sync_status():
        nonlocal waiting_for_sync
        with genesis_lock:
            if len(received_blocks) > 0:
                waiting_for_sync = False
    
    # 将更新函数添加到全局变量，以便其他函数可以调用
    global update_block_sync_status
    update_block_sync_status = update_sync_status

#create a dummy block
def create_dummy_block(peer_id, MALICIOUS_MODE):
    # TODO: Define the JSON format of a `block`, which should include `{message type, peer's ID, timestamp, block ID, previous block's ID, and transactions}`. 
    # The `block ID` is the hash value of block structure except for the item `block ID`. 
    # `previous block` is the last block in the blockchain, to which the new block will be linked. 
    # If the block generator is malicious, it can generate random block ID.
    """创建一个新区块"""
    # 获取最新区块高度
    latest_height = get_latest_block_height()
    
    # 创建区块
    block = {
        "type": "BLOCK",
        "peer_id": peer_id,
        "timestamp": time.time(),
        "block_id": "",  
        "previous_block_id": received_blocks[-1]["block_id"] if received_blocks else None,
        "height": latest_height + 1,  # 设置区块高度
        "transactions": [],
        "message_id": generate_message_id()  # 添加message_id字段
    }
    # TODO: Read the transactions in the local `tx_pool` using the function `get_recent_transactions` in `transaction.py`.
    transactions = get_recent_transactions()
    block["transactions"] = transactions
    # TODO: Create a new block with the transactions and generate the block ID using the function `compute_block_hash`.
    if MALICIOUS_MODE:
        #generate a random block ID
        block["block_id"] = hashlib.sha256(str(random.random()).encode()).hexdigest()
    else:
        block["block_id"] = compute_block_hash(block)
    # TODO: Clear the local transaction pool and add the new block into the local blockchain (`receive_block`).
    clear_pool()
    received_blocks.append(block)
    
    # 添加区块头到header_store
    header_store.append({
        "block_id": block["block_id"],
        "previous_block_id": block["previous_block_id"],
        "height": block["height"]
    })
    return block

def compute_block_hash(block):
    # TODO: Compute the hash of a block except for the term `block ID`.
    block_data=block.copy()
    block_data.pop("block_id", None)
    block_data_str = json.dumps(block_data, sort_keys=True).encode()
    return hashlib.sha256(block_data_str).hexdigest()


def handle_block(msg, self_id):
    # 注意：区块哈希验证已经在message_handler.py中完成，这里不再重复验证
    # computed_hash = compute_block_hash(msg)
    # if computed_hash != msg["block_id"]:
    #     sender_id = msg.get("peer_id") or msg.get("sender_id") 
    #     if sender_id:
    #         print(f"检测到恶意节点 {sender_id}，区块ID验证失败")
    #         record_offense(sender_id)
    #     return
    
    # 检查当前节点是否为轻量级节点
    is_lightweight = False
    if self_id in peer_flags and peer_flags[self_id].get("light", False):
        is_lightweight = True
    
    # TODO: Check if the block exists in the local blockchain. If yes, drop the block.
    """处理接收到的区块"""
    # 检查区块是否已存在
    block_exists = False
    for block in received_blocks:
        if block["block_id"] == msg["block_id"]:
            logger.info(f"区块 {msg['block_id']} 已存在于本地区块链中，忽略")
            return
    
    # 检查是否是创世区块（previous_block_id为None）
    previous_block_id = msg.get("previous_block_id")
    if previous_block_id is None:
        # 如果已经有创世区块了，忽略这个新的创世区块
        for block in received_blocks:
            if block.get("previous_block_id") is None:
                logger.warning(f"忽略重复的创世区块: {msg['block_id']}，本地已有创世区块: {block['block_id']}")
                return
    
    # 轻量级节点只存储区块头，不存储完整区块
    if is_lightweight:
        # 创建区块头
        header = {
            "block_id": msg["block_id"],
            "previous_block_id": previous_block_id,
            "height": msg.get("height", 0)  # 确保有高度信息
        }
        
        # 计算高度（如果消息中没有）
        if "height" not in msg:
            if previous_block_id is None:
                header["height"] = 0  # 创世区块高度为0
            else:
                for h in header_store:
                    if h.get("block_id") == previous_block_id:
                        header["height"] = h.get("height", 0) + 1
                        break
        
        # 检查区块头是否已存在
        for h in header_store:
            if h.get("block_id") == msg["block_id"]:
                logger.info("区块头已存在于本地存储中，忽略")
                return
                
        # 添加到区块头存储
        header_store.append(header)
        logger.info(f"轻量级节点: 区块头 {msg['block_id']} 已添加到存储中，高度: {header['height']}")
        
        # 尝试调用更新同步状态函数
        try:
            if 'update_block_sync_status' in globals():
                update_block_sync_status()
                logger.info("区块同步状态已更新")
        except Exception as e:
            logger.error(f"更新区块同步状态失败: {e}")
            
        return  # 轻量级节点处理完区块头后直接返回
            
    # 检查区块的前置区块是否存在
    is_previous_block_exist = False
    
    for block in received_blocks:
        if block["block_id"] == previous_block_id:
            is_previous_block_exist = True
            break
            
    # 如果前置区块存在或者是创世区块，则添加到区块链
    if previous_block_id is None or is_previous_block_exist:
        # 确保区块有高度信息
        if "height" not in msg:
            # 如果区块没有高度，则根据前置区块计算高度
            if previous_block_id is None:
                msg["height"] = 0  # 创世区块高度为0
            else:
                for block in received_blocks:
                    if block["block_id"] == previous_block_id:
                        msg["height"] = block["height"] + 1
                        break
        
        received_blocks.append(msg)
        header_store.append({
            "block_id": msg["block_id"],
            "previous_block_id": msg["previous_block_id"],
            "height": msg.get("height", 0)
        })
        logger.info(f"区块 {msg['block_id']} 已添加到本地区块链中，高度: {msg.get('height')}")
        
        # 尝试调用更新同步状态函数
        try:
            if 'update_block_sync_status' in globals():
                update_block_sync_status()
                logger.info("区块同步状态已更新")
        except Exception as e:
            logger.error(f"更新区块同步状态失败: {e}")

    else:
        # 如果前置区块不存在，则添加到孤块列表
        orphan_blocks[msg["block_id"]] = msg
        logger.info(f"区块 {msg['block_id']} 的前置区块 {previous_block_id} 不存在，暂存为孤块")
        return
        
    # TODO: Check if the block is the previous block of blocks in `orphan_blocks`. If yes, add the orphaned blocks to the local blockchain.
    orphaned_to_add = []
    for orphan_id, orphan_block in orphan_blocks.items():
        if orphan_block["previous_block_id"] == msg["block_id"]:
            # 计算孤块高度
            orphan_block["height"] = msg.get("height", 0) + 1
            
            received_blocks.append(orphan_block)
            header_store.append({
                "block_id": orphan_block["block_id"],
                "previous_block_id": orphan_block["previous_block_id"],
                "height": orphan_block["height"]
            })
            orphaned_to_add.append(orphan_id)
            logger.info(f"孤块 {orphan_id} 现在可以添加到区块链中，高度: {orphan_block['height']}")
            
    # 从孤块列表中移除已添加的孤块
    for orphan_id in orphaned_to_add:
        del orphan_blocks[orphan_id]

def create_getblock(sender_id, requested_ids):
    # TODO: Define the JSON format of a `GETBLOCK` message, which should include `{message type, sender's ID, requesting block IDs}`.
    msg = {
        "type": "GETBLOCK",
        "sender_id": sender_id,
        "requested_ids": requested_ids,
        "message_id": generate_message_id()
    }
    return msg


def get_block_by_id(block_id):
    # TODO: Return the block in the local blockchain based on the block ID.
    for block in received_blocks:
        if block["block_id"] == block_id:
            return block
    return None

def get_inventory():
    """获取本地区块链中的所有区块ID"""
    block_ids = []
    for block in received_blocks:
        block_ids.append(block["block_id"])
    return block_ids

def get_latest_block():
    """获取最新区块"""
    if not received_blocks:
        return None
        
    # 按高度排序，获取最高的区块
    sorted_blocks = sorted(received_blocks, key=lambda b: b.get("height", 0), reverse=True)
    return sorted_blocks[0] if sorted_blocks else None

def get_latest_block_height():
    """获取最新区块高度"""
    latest_block = get_latest_block()
    return latest_block.get("height", 0) if latest_block else 0

def get_blocks_since_height(height, limit=50):
    """获取指定高度之后的区块，最多返回limit个"""
    if not received_blocks:
        return []
        
    # 找出高于指定高度的所有区块
    higher_blocks = [b for b in received_blocks if b.get("height", 0) > height]
    
    # 按高度排序
    sorted_blocks = sorted(higher_blocks, key=lambda b: b.get("height", 0))
    
    # 返回指定数量的区块
    return sorted_blocks[:limit]

def get_headers_by_height_range(start_height, end_height):
    """获取指定高度范围内的区块头"""
    filtered_headers = []
    for header in header_store:
        header_height = header.get("height", 0)
        if start_height <= header_height <= end_height:
            filtered_headers.append(header)
    
    # 按高度排序
    filtered_headers.sort(key=lambda h: h.get("height", 0))
    return filtered_headers