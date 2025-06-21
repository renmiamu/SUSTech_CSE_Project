from flask import Flask, jsonify, render_template, request, url_for
from threading import Thread
from peer_manager import peer_status, rtt_tracker, get_peer_status, blacklist
from peer_discovery import known_peers,peer_flags
import json
import time
import threading
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(current_dir, 'static')
template_folder = os.path.join(current_dir, 'templates')

# 打印文件夹路径信息
print(f"静态文件夹路径: {static_folder}")
print(f"模板文件夹路径: {template_folder}")
print(f"静态文件存在: {os.path.exists(static_folder)}")
print(f"模板文件存在: {os.path.exists(template_folder)}")
if os.path.exists(static_folder):
    print(f"静态文件列表: {os.listdir(static_folder)}")
if os.path.exists(template_folder):
    print(f"模板文件列表: {os.listdir(template_folder)}")

# 初始化Flask应用程序，指定静态文件和模板目录
app = Flask(__name__, 
           static_folder=static_folder,
           template_folder=template_folder)

blockchain_data_ref = None
known_peers_ref = None

# 全局状态数据，由节点主线程更新
dashboard_data = {
    "peers": {},
    "transactions": [],
    "blocks": [],
    "orphan_blocks": [],
    "latency": {},
    "capacity": 0,
    "redundancy": {}
}


#--------------------------------------------#
def start_dashboard(self_id, port=None):
    global blockchain_data_ref, known_peers_ref, dashboard_data
    from block_handler import received_blocks
    dashboard_data["peer_id"] = self_id
    blockchain_data_ref = received_blocks
    known_peers_ref = known_peers
    
    # 使用节点ID作为环境变量，使其在模板中可访问
    os.environ['PEER_ID'] = str(self_id)
    
    # 如果未提供端口，则根据节点ID计算端口
    if port is None:
        port = 7000 + int(self_id) % 10000
    
    # 打印已知节点
    print(f"[{self_id}] Known peers before dashboard start: {known_peers}")
    print(f"[{self_id}] Peer flags before dashboard start: {peer_flags}")
    
    # 启动仪表盘
    print(f"[{self_id}] Starting dashboard on port {port}")
    
    # 在新线程中运行Flask应用
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # 打印节点状态
    ip = os.environ.get('NODE_IP', 'localhost')
    print(f"[{self_id}] Node is now running at {ip}:{self_id}")
    
    # 每30秒打印一次节点心跳
    def print_heartbeat():
        while True:
            print(f"[{self_id}] Still alive at {time.strftime('%H:%M:%S')}")
            time.sleep(30)
    
    threading.Thread(target=print_heartbeat, daemon=True).start()
    
    # 添加以下代码，定期更新仪表盘数据
    def update_data_loop():
        while True:
            update_dashboard_data(self_id)
            time.sleep(5)  # 每5秒更新一次
    
    # 启动更新线程
    threading.Thread(target=update_data_loop, daemon=True).start()

@app.route('/')
def home():
    # 渲染主页模板，传递节点ID
    return render_template('index.html', peer_id=os.environ.get('PEER_ID', 'Unknown'))

@app.route('/blocks')
def blocks():
    # display the blocks in the local blockchain.
    # 返回区块链数据
    return jsonify(dashboard_data["blocks"])

@app.route('/peers')
def peers():
    # display the information of known peers, 
    # including `{peer's ID, IP address, port, status, NATed or non-NATed, lightweight or full}`.
    peers_info = {}
    
    # 整合所有节点信息
    for peer_id, (ip, port) in known_peers.items():
        peer_id_str = str(peer_id)
        flag_info = peer_flags.get(peer_id_str, {})  # 确保使用字符串键
        status = peer_status.get(peer_id_str, "unknown")  # 确保使用字符串键
        
        # 处理NAT和light标志
        nat_status = flag_info.get("nat")
        light_status = flag_info.get("light")
        
        peers_info[peer_id_str] = {
            "peer_id": peer_id_str,
            "ip": ip,
            "port": port,
            "status": status,
            "nat": nat_status,
            "light": light_status
        }
    
    return jsonify(peers_info)

@app.route('/transactions')
def transactions():
    """返回交易池数据"""
    try:
        # 获取交易数据
        from transaction import get_recent_transactions
        tx_data = get_recent_transactions()
        
        # 确保返回的是列表，不是其他类型
        if not isinstance(tx_data, list):
            logger.warning(f"交易数据格式不是列表: {type(tx_data)}")
            if isinstance(tx_data, dict):
                tx_data = [tx_data]  # 如果是单个交易，转为列表
            else:
                tx_data = []  # 如果是其他类型，返回空列表
        
        # 过滤确保所有项都是字典
        filtered_data = []
        for item in tx_data:
            if isinstance(item, dict):
                filtered_data.append(item)
            else:
                logger.warning(f"交易数据中包含非字典项: {item}")
        
        # 返回标准JSON格式
        return jsonify(filtered_data)
    except Exception as e:
        logger.exception(f"获取交易数据时出错: {e}")
        return jsonify({"error": f"获取交易数据时出错: {str(e)}"}), 500

@app.route('/latency')
def latency():
    # display the transmission latency between peers.
    # 返回延迟数据
    return jsonify(dashboard_data["latency"])

@app.route('/capacity')
def capacity():
    from outbox import rate_limiter
    # 返回节点容量
    return jsonify(rate_limiter.capacity)

@app.route('/orphans')
def orphan_blocks():
    # display the orphaned blocks.
    # 返回孤块数据
    return jsonify(dashboard_data["orphan_blocks"])

@app.route('/redundancy')
def redundancy_stats():
    """返回冗余消息统计信息"""
    try:
        # 局部导入
        from message_handler import get_redundancy_stats
        # 获取冗余消息统计
        redundancy_data = get_redundancy_stats()
        
        # 确保返回的是dict，不是其他类型
        if not isinstance(redundancy_data, dict):
            logger.warning(f"冗余消息数据格式不是dict: {type(redundancy_data)}")
            redundancy_data = {}
            
        # 过滤确保所有值都是数字
        filtered_data = {}
        for key, value in redundancy_data.items():
            try:
                # 确保键是字符串，值是数字
                filtered_data[str(key)] = int(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"冗余消息数据中包含无效值: {key}={value}, 错误: {e}")
                
        # 返回标准JSON格式
        return jsonify(filtered_data)
    except Exception as e:
        logger.exception(f"获取冗余消息统计时出错: {e}")
        return jsonify({"error": f"获取冗余消息统计时出错: {str(e)}"}), 500

#--------------------------------------------#

#------以下为额外添加内容-------
@app.route('/api/network/stats')
def get_network_stats():
    # 局部导入
    from outbox import get_outbox_status, get_drop_stats
    from message_handler import get_redundancy_stats
    # 获取网络统计信息
    redundancy = get_redundancy_stats()
    outbox_status = get_outbox_status()
    drop_stats = get_drop_stats()
    
    return jsonify({
        'message_redundancy': redundancy,
        'outbox_status': outbox_status,
        'drop_stats': drop_stats
    })

@app.route('/api/blockchain/status')
def get_blockchain_status():
    # 局部导入
    from block_handler import received_blocks
    # 获取区块链状态
    chain_length = len(received_blocks)
    latest_block = received_blocks[-1] if received_blocks else {}
    
    return jsonify({
        'chain_length': chain_length,
        'latest_block': latest_block
    })

@app.route('/api/blockchain/blocks')
def get_blockchain_blocks():
    # 局部导入
    from block_handler import received_blocks
    # 获取区块链上的所有区块
    return jsonify(received_blocks)

@app.route('/api/blacklist')
def get_blacklist():
    # 只获取当前节点的黑名单列表
    from peer_manager import blacklist
    return jsonify(list(blacklist))

@app.route('/api/peer_blacklists')
def get_peer_blacklists():
    # 为了兼容前端，返回简化的数据结构
    # 只包含当前节点的黑名单信息
    from peer_manager import blacklist
    my_id = os.environ.get('PEER_ID', 'Unknown')
    simplified_blacklists = {
        my_id: list(blacklist)
    }
    return jsonify(simplified_blacklists)

@app.route('/api/messages')
def get_messages():
    """获取消息记录，合并所有类型的消息并按时间排序"""
    # 合并所有类型的消息
    all_messages = []
    for msg_type in message_logs_by_type:
        all_messages.extend(message_logs_by_type[msg_type])
    
    # 按时间倒序排序
    all_messages.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return jsonify(all_messages)

@app.route('/api/capacity')
def get_capacity():
    from outbox import rate_limiter
    # 获取节点当前发送容量
    capacity = {
        'current': rate_limiter.capacity,
        'usage': rate_limiter.tokens / rate_limiter.capacity
    }
    return jsonify(capacity)

# 新增：强制发送区块消息到指定节点的API
@app.route('/api/send_block', methods=['POST'])
def send_block_to_peer():
    from flask import request
    from block_handler import received_blocks
    from outbox import enqueue_message
    from peer_discovery import known_peers

    try:
        data = request.json
        target_peer_id = data.get('target_peer_id')
        
        if not target_peer_id:
            return jsonify({"status": "error", "message": "缺少目标节点ID"}), 400
            
        if target_peer_id not in known_peers:
            return jsonify({"status": "error", "message": "目标节点未知"}), 404
            
        # 获取本地最新区块
        if not received_blocks:
            return jsonify({"status": "error", "message": "本地区块链为空"}), 400
            
        latest_block = received_blocks[-1]
        target_ip, target_port = known_peers[target_peer_id]
        
        # 直接发送区块
        result = enqueue_message(target_peer_id, target_ip, target_port, latest_block)
        
        if result:
            # 记录发送的消息
            my_id = os.environ.get('PEER_ID', 'Unknown')
            log_sent_message(my_id, target_peer_id, "BLOCK", latest_block)
            return jsonify({"status": "success", "message": f"成功发送区块 {latest_block['block_id']} 到节点 {target_peer_id}"})
        else:
            return jsonify({"status": "error", "message": "消息入队失败"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"发送失败: {str(e)}"}), 500

def update_dashboard_data(peer_id):
    """更新仪表盘数据"""
    global dashboard_data
    
    # 局部导入
    from outbox import rate_limiter, get_outbox_status, get_drop_stats
    from block_handler import received_blocks, orphan_blocks, header_store
    
    # 更新节点信息
    from peer_manager import get_peer_status
    dashboard_data["peers"] = get_peer_status()
    
    # 更新交易信息
    from transaction import get_recent_transactions
    dashboard_data["transactions"] = get_recent_transactions()
    
    # 更新区块信息
    # 使用header_store代替不存在的block_headers
    is_lightweight = False
    if is_lightweight:
        dashboard_data["blocks"] = header_store
    else:
        dashboard_data["blocks"] = [{
            "block_id": block["block_id"],
            "prev_block_id": block.get("previous_block_id", None),
            "height": block.get("height", 0),
            "timestamp": block["timestamp"],
            "tx_count": len(block.get("transactions", []))
        } for block in received_blocks]
    
    # 更新孤块信息
    dashboard_data["orphan_blocks"] = [{
        "block_id": block["block_id"],
        "prev_block_id": block.get("previous_block_id", None),
        "timestamp": block["timestamp"]
    } for block in orphan_blocks.values()]
    
    # 更新传输延迟信息
    from peer_manager import rtt_tracker
    latency_data = {}
    for peer, rtt in rtt_tracker.items():
        if rtt is not None:
            latency_data[peer] = rtt
    dashboard_data["latency"] = latency_data
    
    # 更新节点发送容量
    dashboard_data["capacity"] = rate_limiter.capacity
    
    # 更新冗余消息信息
    from message_handler import get_redundancy_stats
    dashboard_data["redundancy"] = get_redundancy_stats()
    
    # 不再需要收集其他节点的黑名单信息
    # 删除update_peer_blacklists()调用

# 移除不需要的update_peer_blacklists函数
# def update_peer_blacklists():
#     """从网络中收集各节点的黑名单信息"""
#     这个函数不再需要，注释掉或删除

# 简化blacklists变量
peer_blacklists = {}  # 保留变量以避免前端错误，但不再使用

# 消息记录，按类型分类记录发送和接收的消息
message_logs_by_type = {
    "block": [],  # 区块相关消息
    "tx": [],     # 交易相关消息
    "ping": [],   # PING/PONG消息
    "other": []   # 其他类型消息
}
MAX_MESSAGES_PER_TYPE = 100  # 每种类型最多保存的消息记录数量

# 用于记录发送消息的函数，在outbox.py中调用
def log_sent_message(sender_id, receiver_id, msg_type, content):
    """记录发送的消息"""
    message = {
        "type": "SENT",
        "timestamp": time.time(),
        "sender": str(sender_id),
        "receiver": str(receiver_id),
        "msg_type": msg_type,
        "content": str(content)[:200]  # 截断过长的内容
    }
    
    # 根据消息类型分类存储
    msg_type_upper = msg_type.upper() if msg_type else ""
    if msg_type_upper.find("BLOCK") >= 0 or msg_type_upper in ["INV", "GETBLOCK"]:
        message_logs_by_type["block"].append(message)
        # 限制该类型消息数量
        if len(message_logs_by_type["block"]) > MAX_MESSAGES_PER_TYPE:
            message_logs_by_type["block"] = message_logs_by_type["block"][-MAX_MESSAGES_PER_TYPE:]
    elif msg_type_upper.find("TX") >= 0 or msg_type_upper == "TRANSACTION":
        message_logs_by_type["tx"].append(message)
        if len(message_logs_by_type["tx"]) > MAX_MESSAGES_PER_TYPE:
            message_logs_by_type["tx"] = message_logs_by_type["tx"][-MAX_MESSAGES_PER_TYPE:]
    elif msg_type_upper in ["PING", "PONG"]:
        message_logs_by_type["ping"].append(message)
        if len(message_logs_by_type["ping"]) > MAX_MESSAGES_PER_TYPE:
            message_logs_by_type["ping"] = message_logs_by_type["ping"][-MAX_MESSAGES_PER_TYPE:]
    else:
        message_logs_by_type["other"].append(message)
        if len(message_logs_by_type["other"]) > MAX_MESSAGES_PER_TYPE:
            message_logs_by_type["other"] = message_logs_by_type["other"][-MAX_MESSAGES_PER_TYPE:]

# 用于记录接收消息的函数，在message_handler.py中调用
def log_received_message(sender_id, receiver_id, msg_type, content):
    """记录接收的消息"""
    message = {
        "type": "RECEIVED",
        "timestamp": time.time(),
        "sender": str(sender_id),
        "receiver": str(receiver_id),
        "msg_type": msg_type,
        "content": str(content)[:200]  # 截断过长的内容
    }
    
    # 根据消息类型分类存储
    msg_type_upper = msg_type.upper() if msg_type else ""
    if msg_type_upper.find("BLOCK") >= 0 or msg_type_upper in ["INV", "GETBLOCK"]:
        message_logs_by_type["block"].append(message)
        # 限制该类型消息数量
        if len(message_logs_by_type["block"]) > MAX_MESSAGES_PER_TYPE:
            message_logs_by_type["block"] = message_logs_by_type["block"][-MAX_MESSAGES_PER_TYPE:]
    elif msg_type_upper.find("TX") >= 0 or msg_type_upper == "TRANSACTION":
        message_logs_by_type["tx"].append(message)
        if len(message_logs_by_type["tx"]) > MAX_MESSAGES_PER_TYPE:
            message_logs_by_type["tx"] = message_logs_by_type["tx"][-MAX_MESSAGES_PER_TYPE:]
    elif msg_type_upper in ["PING", "PONG"]:
        message_logs_by_type["ping"].append(message)
        if len(message_logs_by_type["ping"]) > MAX_MESSAGES_PER_TYPE:
            message_logs_by_type["ping"] = message_logs_by_type["ping"][-MAX_MESSAGES_PER_TYPE:]
    else:
        message_logs_by_type["other"].append(message)
        if len(message_logs_by_type["other"]) > MAX_MESSAGES_PER_TYPE:
            message_logs_by_type["other"] = message_logs_by_type["other"][-MAX_MESSAGES_PER_TYPE:]

# 节点事件通知函数
def notify_node_joined(node_id, ip, port, flags):
    """通知前端有新节点加入"""
    event = {
        "type": "node_joined",
        "node_id": node_id,
        "ip": ip,
        "port": port,
        "flags": flags,
        "timestamp": time.time()
    }
    broadcast_event(event)

def notify_node_left(node_id, reason):
    """通知前端有节点离开"""
    event = {
        "type": "node_left",
        "node_id": node_id,
        "reason": reason,
        "timestamp": time.time()
    }
    broadcast_event(event)
    
def notify_nodes_discovered(node_ids):
    """通知前端发现了新节点"""
    event = {
        "type": "nodes_discovered",
        "node_ids": node_ids,
        "timestamp": time.time()
    }
    broadcast_event(event)

# 广播事件到所有连接的客户端
def broadcast_event(event):
    """广播事件到所有WebSocket客户端"""
    import json
    
    event_json = json.dumps(event)
    # 在这里实现向WebSocket客户端发送事件的逻辑
    # 由于我们的dashboard是基于HTTP的，暂时不实现完整的WebSocket功能
    logger.info(f"广播事件: {event_json}")

@app.route('/api/nodes/list')
def list_nodes_api():
    """处理获取节点列表的请求，保留此API以便仪表盘显示节点状态"""
    from peer_discovery import known_peers, peer_flags
    from peer_manager import get_peer_status
    
    node_list = []
    for node_id, (ip, port) in known_peers.items():
        node_info = {
            "id": node_id,
            "ip": ip,
            "port": port,
            "flags": peer_flags.get(node_id, {}),
            "status": get_peer_status().get(node_id, {})
        }
        node_list.append(node_info)
        
    return jsonify({"nodes": node_list})

@app.route('/api/network/status')
def network_status_api():
    """处理获取网络状态的请求，保留此API以便仪表盘显示网络状态"""
    from peer_discovery import known_peers
    from block_handler import get_latest_block_height, get_inventory
    from peer_manager import get_peer_status
    
    status = {
        "node_count": len(known_peers),
        "active_nodes": sum(1 for node_id, info in get_peer_status().items() if info.get("status") == "ALIVE"),
        "block_height": get_latest_block_height(),
        "block_count": len(get_inventory())
    }
    
    return jsonify(status)

@app.route('/api/network/topology')
def network_topology_api():
    """处理获取网络拓扑的请求，保留此API以便可视化网络状态"""
    from peer_discovery import known_peers, reachable_by
    
    nodes = []
    for node_id, (ip, port) in known_peers.items():
        nodes.append({
            "id": node_id,
            "ip": ip,
            "port": port
        })
        
    links = []
    for node_id, reachable_nodes in reachable_by.items():
        for reachable_node in reachable_nodes:
            links.append({
                "source": node_id,
                "target": reachable_node
            })
            
    return jsonify({"nodes": nodes, "links": links})

@app.route('/api/transactions/create', methods=['POST'])
def create_transaction_api():
    """处理创建新交易的请求"""
    try:
        data = request.json
        from_peer = data.get("from")
        to_peer = data.get("to")
        amount = data.get("amount")
        
        if not from_peer or not to_peer or not amount:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400
            
        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"success": False, "error": "金额必须是数字"}), 400
            
        if amount <= 0:
            return jsonify({"success": False, "error": "金额必须大于0"}), 400
            
        # 创建交易
        from transaction import TransactionMessage, add_transaction
        tx = TransactionMessage(sender=from_peer, receiver=to_peer, amount=amount)
        
        # 添加到交易池
        add_transaction(tx)
        
        # 广播交易
        from outbox import gossip_message
        gossip_message(from_peer, tx.to_dict())
        
        return jsonify({
            "success": True, 
            "transaction": {
                "id": tx.id,
                "from": tx.sender,
                "to": tx.receiver,
                "amount": tx.amount,
                "timestamp": tx.timestamp
            }
        })
                
    except Exception as e:
        logger.error(f"创建交易出错: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/transactions/list')
def list_transactions_api():
    """获取交易池中的交易"""
    from transaction import get_recent_transactions
    
    transactions = get_recent_transactions()
    return jsonify({"transactions": transactions})

@app.route('/redundancy_total')
def redundancy_total():
    from message_handler import total_redundant_message
    return jsonify({"total_redundant_messages": total_redundant_message})