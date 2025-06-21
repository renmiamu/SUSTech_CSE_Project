import json
import os
import logging
import threading
import time
from peer_discovery import known_peers, peer_flags

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 配置文件路径
CONFIG_FILE_PATH = 'config.json'

def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return None

def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info("配置文件已保存")
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        return False

def generate_dynamic_config(self_id, known_nodes=None, flags=None):
    """生成动态配置，用于新节点"""
    if known_nodes is None:
        known_nodes = {}
    
    if flags is None:
        flags = {}
    
    # 基于当前已知节点生成配置
    config = {
        "peers": {},
        "dynamic_discovery": True
    }
    
    # 保留现有11个节点(5000-5010)作为引导节点
    for i in range(5000, 5011):
        peer_id = str(i)
        if peer_id in known_nodes:
            ip, port = known_nodes[peer_id]
            config["peers"][peer_id] = {
                "ip": ip,
                "port": int(port),
                "fanout": 1
            }
            
            # 添加标志
            if peer_id in peer_flags:
                if peer_flags[peer_id].get("nat", False):
                    config["peers"][peer_id]["nat"] = True
                if peer_flags[peer_id].get("light", False):
                    config["peers"][peer_id]["light"] = True
                if peer_flags[peer_id].get("mode", None) == "malicious":
                    config["peers"][peer_id]["mode"] = "malicious"
    
    # 添加当前节点
    if self_id in known_nodes:
        ip, port = known_nodes[self_id]
        config["peers"][self_id] = {
            "ip": ip,
            "port": int(port),
            "fanout": 1
        }
        
        # 添加节点标志
        if flags.get("nat", False):
            config["peers"][self_id]["nat"] = True
        if flags.get("light", False):
            config["peers"][self_id]["light"] = True
    
    return config

def create_node_config(node_id, ip, port, flags=None):
    """为新节点创建配置"""
    if flags is None:
        flags = {}
    
    # 加载当前配置
    config = load_config()
    if not config:
        config = {"peers": {}}
    
    # 添加新节点配置
    config["peers"][str(node_id)] = {
        "ip": ip,
        "port": int(port),
        "fanout": 1
    }
    
    # 添加标志
    if flags.get("nat", False):
        config["peers"][str(node_id)]["nat"] = True
    if flags.get("light", False):
        config["peers"][str(node_id)]["light"] = True
    
    # 保存配置
    return save_config(config)

def remove_node_config(node_id):
    """从配置中移除节点"""
    # 加载当前配置
    config = load_config()
    if not config:
        return False
    
    # 移除节点配置
    if str(node_id) in config["peers"]:
        del config["peers"][str(node_id)]
        
        # 保存配置
        return save_config(config)
    
    return False

def synchronize_config_with_network():
    """将配置与当前网络状态同步"""
    # 加载当前配置
    config = load_config()
    if not config:
        config = {"peers": {}}
    
    # 更新配置以包含所有已知节点
    updated = False
    for peer_id, (ip, port) in known_peers.items():
        if peer_id not in config["peers"]:
            config["peers"][peer_id] = {
                "ip": ip,
                "port": int(port),
                "fanout": 1
            }
            updated = True
            
            # 添加标志
            if peer_id in peer_flags:
                flags = peer_flags[peer_id]
                if flags.get("nat", False):
                    config["peers"][peer_id]["nat"] = True
                if flags.get("light", False):
                    config["peers"][peer_id]["light"] = True
    
    # 移除不在网络中的节点
    peers_to_remove = []
    for peer_id in config["peers"]:
        if peer_id not in known_peers:
            peers_to_remove.append(peer_id)
    
    for peer_id in peers_to_remove:
        del config["peers"][peer_id]
        updated = True
    
    # 如果有更新，保存配置
    if updated:
        return save_config(config)
    
    return True

def start_config_manager():
    """启动配置管理器"""
    def loop():
        while True:
            try:
                # 定期同步配置与网络状态
                synchronize_config_with_network()
                time.sleep(60)  # 每分钟同步一次
            except Exception as e:
                logger.error(f"配置管理器出错: {e}")
                time.sleep(30)
    
    threading.Thread(target=loop, daemon=True).start()
    logger.info("配置管理器已启动") 