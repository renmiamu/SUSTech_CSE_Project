import subprocess
import json
import os
import time
import logging
import threading
from utils import generate_message_id

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def update_global_config(peer_id, ip, port, flags=None):
    """更新全局配置文件，添加新节点"""
    if flags is None:
        flags = {}
    
    try:
        # 读取当前配置
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # 添加新节点配置
        config["peers"][str(peer_id)] = {
            "ip": ip,
            "port": port,
            "fanout": 1
        }
        
        # 添加标志
        if flags.get("nat", False):
            config["peers"][str(peer_id)]["nat"] = True
        if flags.get("light", False):
            config["peers"][str(peer_id)]["light"] = True
        
        # 写回配置文件
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"全局配置已更新，添加节点 {peer_id}")
    except Exception as e:
        logger.error(f"更新全局配置失败: {e}")

def remove_from_global_config(peer_id):
    """从全局配置文件中移除节点"""
    try:
        # 读取当前配置
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # 移除节点配置
        if str(peer_id) in config["peers"]:
            del config["peers"][str(peer_id)]
        
        # 写回配置文件
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"全局配置已更新，移除节点 {peer_id}")
    except Exception as e:
        logger.error(f"从全局配置移除节点失败: {e}")

def update_dynamic_config():
    """更新动态配置，确保所有节点的配置一致"""
    from peer_discovery import known_peers, peer_flags
    
    try:
        # 读取当前配置
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # 确保配置中包含所有已知节点
        for peer_id, (ip, port) in known_peers.items():
            if peer_id not in config["peers"]:
                config["peers"][peer_id] = {
                    "ip": ip,
                    "port": int(port),
                    "fanout": 1
                }
                
                # 添加标志
                if peer_id in peer_flags:
                    flags = peer_flags[peer_id]
                    if flags.get("nat", False):
                        config["peers"][peer_id]["nat"] = True
                    if flags.get("light", False):
                        config["peers"][peer_id]["light"] = True
        
        # 写回配置文件
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info("动态配置已更新")
    except Exception as e:
        logger.error(f"更新动态配置失败: {e}")

def start_dynamic_node_manager():
    """启动动态节点管理服务"""
    def loop():
        while True:
            try:
                # 定期检查配置是否需要更新
                update_dynamic_config()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"动态节点管理服务出错: {e}")
                time.sleep(30)
    
    threading.Thread(target=loop, daemon=True).start()
    logger.info("动态节点管理服务已启动") 