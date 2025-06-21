#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动区块链节点仪表盘的脚本
"""

import sys
import os

# 添加Starter_Code_New目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
starter_code_dir = os.path.join(current_dir, 'Starter_Code_New')
sys.path.append(starter_code_dir)

# 创建模拟数据的存根模块
import types

# 导入日志处理模块
import Starter_Code_New.log_handler

# 创建必要的模块和变量以避免导入错误
sys.modules['peer_manager'] = types.ModuleType('peer_manager')
sys.modules['peer_manager'].peer_status = {}
sys.modules['peer_manager'].rtt_tracker = {}
sys.modules['peer_manager'].blacklist = set()
sys.modules['peer_manager'].get_peer_status = lambda: {}

sys.modules['transaction'] = types.ModuleType('transaction')
sys.modules['transaction'].get_recent_transactions = lambda: []

sys.modules['outbox'] = types.ModuleType('outbox')
sys.modules['outbox'].rate_limiter = types.SimpleNamespace(capacity=100, tokens=0)
sys.modules['outbox'].get_outbox_status = lambda: {}
sys.modules['outbox'].get_drop_stats = lambda: {}

sys.modules['message_handler'] = types.ModuleType('message_handler')
sys.modules['message_handler'].get_redundancy_stats = lambda: {}

sys.modules['peer_discovery'] = types.ModuleType('peer_discovery')
sys.modules['peer_discovery'].known_peers = {}
sys.modules['peer_discovery'].peer_flags = {}

sys.modules['block_handler'] = types.ModuleType('block_handler')
sys.modules['block_handler'].received_blocks = []
sys.modules['block_handler'].blockchain = []
sys.modules['block_handler'].block_headers = []
sys.modules['block_handler'].orphan_blocks = []
sys.modules['block_handler'].is_lightweight = False
sys.modules['block_handler'].header_store = []

# 现在导入仪表盘模块
from Starter_Code_New.dashboard import app

if __name__ == '__main__':
    # 默认使用7000端口，也可以通过命令行参数指定
    port = 7000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"端口号必须是整数，使用默认端口 {port}")
    
    print(f"启动仪表盘服务器: http://localhost:{port}/")
    print("请在浏览器中访问上述URL以查看仪表盘")
    print("日志页面地址: http://localhost:{}/logs".format(port))
    # 设置debug=True以便在代码修改后自动重启
    app.run(host='0.0.0.0', port=port, debug=True) 