print("=== NODE.PY LOADED ===", flush=True)

import json
import threading
import argparse
import time
import traceback
import logging
from peer_discovery import start_peer_discovery, known_peers, peer_flags, peer_config
from block_handler import block_generation, request_block_sync
from socket_server import start_socket_server
from dashboard import start_dashboard
from peer_manager import start_peer_monitor, start_ping_loop
from outbox import send_from_queue
from outbox import start_dynamic_capacity_adjustment
from inv_message import broadcast_inventory
from transaction import transaction_generation

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    
    # Import the peer's configuration from command line
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--fanout", type=int, help="Override fanout for this peer")
    parser.add_argument("--mode", default="normal", help="Node mode: normal or malicious")
    parser.add_argument("--nat", action="store_true", help="Mark node as behind NAT")
    parser.add_argument("--light", action="store_true", help="Run as lightweight node")
    parser.add_argument("--dynamic", action="store_true", help="Enable dynamic node features")
    args = parser.parse_args()
    
    MALICIOUS_MODE = args.mode == 'malicious'
    DYNAMIC_MODE = args.dynamic or True  # 默认启用动态节点功能
    IS_NEW_NODE = False  # 初始设置为False，后续检查
    
    print(f"[{args.id}] Running in {'malicious' if MALICIOUS_MODE else 'normal'} mode", flush=True)
    if DYNAMIC_MODE:
        print(f"[{args.id}] Dynamic node features enabled", flush=True)

    self_id = args.id
    str_self_id = str(self_id)  # 确保使用字符串ID

    print(f"[{self_id}] Starting node...", flush=True)

    with open(args.config) as f:
        config = json.load(f)

    # 检查节点是否在配置中，如果不在则是新节点
    if self_id not in config["peers"]:
        IS_NEW_NODE = True
        print(f"[{self_id}] This is a new node joining the network", flush=True)
        # 将新节点添加到配置中
        try:
            # 获取IP和端口
            import socket
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            port = int(self_id)
            
            # 添加到配置
            config["peers"][self_id] = {
                "ip": ip,
                "port": port,
                "fanout": 1
            }
            
            # 设置NAT和轻量级标志
            if args.nat:
                config["peers"][self_id]["nat"] = True
            if args.light:
                config["peers"][self_id]["light"] = True
                
            # 保存配置文件，使其他新启动的节点能够发现这个节点
            with open(args.config, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"[{self_id}] Added self to config file", flush=True)
        except Exception as e:
            print(f"[{self_id}] Failed to add new node to config: {e}", flush=True)
    
    # 正常流程，获取节点信息
    self_info = config["peers"][self_id]

    # 为当前节点设置自己的flags（从配置文件中获取，如果未指定则明确为False）
    nat_flag = self_info.get("nat", False) or args.nat
    light_flag = self_info.get("light", False) or args.light
    
    peer_flags[str_self_id] = {
        "nat": nat_flag,
        "light": light_flag
    }

    # 更新known_peers字典
    for peer_id, peer_info in config["peers"].items():
        str_peer_id = str(peer_id)  # 确保使用字符串ID
        known_peers[str_peer_id] = (peer_info["ip"], peer_info["port"])
        peer_config = config["peers"]

    if args.fanout:
        peer_config[self_id]["fanout"] = args.fanout
        print(f"[{self_id}] Overriding fanout to {args.fanout}", flush=True)

    ip = self_info["ip"]
    port = self_info["port"]

    # Start socket and listen for incoming messages
    print(f"[{self_id}] Starting socket server on {ip}:{port}", flush=True)
    start_socket_server(self_id, ip, port)

    # Peer Discovery
    print(f"[{self_id}] Starting peer discovery", flush=True)
    start_peer_discovery(self_id, self_info)

    print(f"[{self_id}] Starting ping loop", flush=True)
    start_ping_loop(self_id, known_peers)

    print(f"[{self_id}] Starting peer monitor", flush=True)
    start_peer_monitor()

    # Block and Transaction Generation and Verification
    print(f"[{self_id}] Starting block sync thread", flush=True)
    # 如果是新节点，启动特殊的区块同步
    if IS_NEW_NODE:
        threading.Thread(target=request_block_sync, args=(self_id, True), daemon=True).start()
        
        # 新节点也需要同步交易池
        from peer_discovery import request_mempool_sync
        threading.Thread(target=request_mempool_sync, args=(self_id,), daemon=True).start()
    else:
        threading.Thread(target=request_block_sync, args=(self_id,), daemon=True).start()

    if not self_info.get('light', False):
        print(f"[{self_id}] Starting transaction and block generation", flush=True)
        transaction_generation(self_id)
        block_generation(self_id, MALICIOUS_MODE)

    print(f"[{self_id}] Starting broadcast inventory thread", flush=True)
    threading.Thread(target=broadcast_inventory, args=(self_id,), daemon=True).start()

    # Sending Message Processing
    print(f"[{self_id}] Starting outbound queue", flush=True)
    send_from_queue(self_id)

    print(f"[{self_id}] Starting dynamic capacity adjustment", flush=True)
    start_dynamic_capacity_adjustment()
    
    # 启动动态节点管理
    if DYNAMIC_MODE:
        try:
            from dynamic_node_manager import start_dynamic_node_manager
            print(f"[{self_id}] Starting dynamic node manager", flush=True)
            start_dynamic_node_manager()
        except ImportError:
            print(f"[{self_id}] Dynamic node manager not available", flush=True)
            
        try:
            from config_manager import start_config_manager
            print(f"[{self_id}] Starting config manager", flush=True)
            start_config_manager()
        except ImportError:
            print(f"[{self_id}] Config manager not available", flush=True)

    # Start dashboard
    time.sleep(2)
    print(f"[{self_id}] Known peers before dashboard start: {known_peers}", flush=True)
    print(f"[{self_id}] Peer flags before dashboard start: {peer_flags}", flush=True)
    print(f"[{self_id}] Starting dashboard on port {port + 2000}", flush=True)
    start_dashboard(self_id, port + 2000)

    print(f"[{self_id}] Node is now running at {ip}:{port}", flush=True)
    
    # 添加退出的处理
    def graceful_exit():
        try:
            from peer_discovery import send_goodbye_message
            print(f"[{self_id}] Preparing for graceful exit...", flush=True)
            send_goodbye_message(self_id)
            
            # 如果是新节点，尝试从配置文件中移除自己
            if IS_NEW_NODE:
                try:
                    # 读取配置
                    with open(args.config) as f:
                        exit_config = json.load(f)
                    
                    # 移除自己
                    if self_id in exit_config["peers"]:
                        del exit_config["peers"][self_id]
                        
                        # 写回配置
                        with open(args.config, 'w') as f:
                            json.dump(exit_config, f, indent=2)
                        
                        print(f"[{self_id}] Removed self from config file during exit", flush=True)
                except Exception as e:
                    print(f"[{self_id}] Error removing self from config: {e}", flush=True)
            
            print(f"[{self_id}] Goodbye message sent, exiting.", flush=True)
        except Exception as e:
            print(f"[{self_id}] Error during graceful exit: {e}", flush=True)
    
    # 注册退出处理函数
    import atexit
    atexit.register(graceful_exit)
    
    # 捕获SIGINT和SIGTERM信号
    import signal
    def signal_handler(sig, frame):
        print(f"[{self_id}] Received signal {sig}, initiating graceful shutdown...", flush=True)
        graceful_exit()
        import sys
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 主循环，保持节点运行
    while True:
        print(f"[{self_id}] Still alive at {time.strftime('%X')}", flush=True)
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] Exception in main(): {e}", flush=True)
        traceback.print_exc()