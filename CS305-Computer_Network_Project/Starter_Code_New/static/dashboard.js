// 仪表盘数据刷新周期(毫秒)
const REFRESH_INTERVAL = 5000;

// 数据处理中间层，统一处理API返回的各种格式
const DataAdapter = {
    // 处理API响应，确保始终返回有效的JSON对象
    processResponse: function(response) {
        return response.text().then(text => {
            console.log('原始响应数据:', text);
            try {
                if (!text || text.trim() === '') {
                    console.warn('响应为空');
                    return null;
                }
                
                // 尝试作为JSON解析
                const json = JSON.parse(text);
                return json;
            } catch (e) {
                console.error('解析响应数据失败:', e);
                console.log('无法解析的原始数据:', text);
                
                // 针对一些常见的API错误，返回有意义的默认值
                if (text.includes('Error') || text.includes('error')) {
                    return { error: text };
                }
                
                return {}; // 返回空对象而不是文本，便于后续处理
            }
        });
    },
    
    // 处理冗余消息数据
    processRedundancyData: function(data) {
        if (!data) return {};
        
        if (typeof data === 'string') {
            try {
                data = JSON.parse(data);
            } catch (e) {
                console.error('解析冗余消息数据失败:', e);
                return {};
            }
        }
        
        if (typeof data !== 'object') {
            console.error('冗余消息数据不是对象格式:', data);
            return {};
        }
        
        // 过滤掉非数字值
        const cleanData = {};
        for (const [key, value] of Object.entries(data)) {
            if (typeof value === 'number') {
                cleanData[key] = value;
            } else {
                console.warn(`冗余消息中存在非数字值: key=${key}, value=${value}`);
            }
        }
        
        return cleanData;
    },
    
    // 处理交易数据
    processTransactionData: function(data) {
        if (!data) return [];
        
        if (typeof data === 'string') {
            try {
                data = JSON.parse(data);
            } catch (e) {
                console.error('解析交易数据失败:', e);
                return [];
            }
        }
        
        // 处理各种可能的数据格式
        if (Array.isArray(data)) {
            return data.filter(item => item && typeof item === 'object');
        } else if (data && typeof data === 'object') {
            // 如果是对象，尝试提取有用的数据
            if (data.error) {
                console.error('交易数据包含错误:', data.error);
                return [];
            }
            
            // 如果是对象但非数组，尝试转为数组
            if (Object.keys(data).length > 0) {
                const values = Object.values(data);
                if (values.length > 0 && typeof values[0] === 'object') {
                    return values;
                }
            }
        }
        
        console.warn('无法处理的交易数据格式:', data);
        return [];
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 测试JS是否成功加载
    const jsTestElement = document.getElementById('js-test');
    if (jsTestElement) {
        jsTestElement.textContent = "JS已成功加载";
        jsTestElement.style.backgroundColor = "#d4edda";
        jsTestElement.style.color = "#155724";
        jsTestElement.style.padding = "3px 8px";
        jsTestElement.style.borderRadius = "4px";
        console.log('dashboard.js 已成功加载并执行');
    }

    // 获取并显示节点ID
    const peerId = document.getElementById('peer-id').textContent;
    console.log(`Dashboard initialized for peer: ${peerId}`);
    
    // 初始化切换显示的内容区域
    initTabPanels();
    
    // 初始化发送区块模态框
    initSendBlockModal();
    
    // 调试UI元素
    debugUIElements();
    
    // 测试API
    testAPIs();
    
    // 首次加载数据
    refreshAllData();
    
    // 设置定时刷新
    setInterval(refreshAllData, REFRESH_INTERVAL);
});

// 调试UI元素，确保标签页正确设置
function debugUIElements() {
    // 检查网络监控面板标签页
    const networkTabs = document.querySelectorAll('#network-monitor-section .tab');
    console.log(`找到 ${networkTabs.length} 个网络监控标签页`);
    
    // 检查冗余消息标签页
    const redundancyTab = document.querySelector('.tab[data-target="redundancy-panel"]');
    if (redundancyTab) {
        console.log('找到冗余消息标签页');
        
        // 检查冗余消息面板
        const redundancyPanel = document.getElementById('redundancy-panel');
        if (redundancyPanel) {
            console.log('找到冗余消息面板');
        } else {
            console.error('未找到冗余消息面板');
        }
        
        // 检查冗余消息表格
        const redundancyTable = document.getElementById('redundancy-table');
        if (redundancyTable) {
            console.log('找到冗余消息表格');
        } else {
            console.error('未找到冗余消息表格');
        }
    } else {
        console.error('未找到冗余消息标签页');
    }
}

// 添加一个更强大的API诊断工具
function checkAPIStatus() {
    console.group('API诊断');
    console.log('开始诊断API状态...');
    
    // 检查各API状态的函数
    function checkAPI(url, name) {
        console.log(`测试${name} API (${url})...`);
        return fetch(url)
            .then(response => {
                if (!response.ok) {
                    console.error(`${name} API返回错误状态码: ${response.status}`);
                    return { status: 'error', code: response.status };
                }
                return response.text().then(text => {
                    try {
                        let data = text;
                        try {
                            // 尝试解析为JSON
                            data = JSON.parse(text);
                        } catch (e) {
                            console.warn(`${name} API返回的不是有效JSON: ${text.substring(0, 100)}...`);
                        }
                        
                        console.log(`${name} API正常，返回数据:`, data);
                        return { status: 'ok', data };
                    } catch (e) {
                        console.error(`处理${name} API响应时出错:`, e);
                        return { status: 'error', error: e.message };
                    }
                });
            })
            .catch(error => {
                console.error(`${name} API请求失败:`, error);
                return { status: 'error', error: error.message };
            });
    }
    
    // 创建诊断任务数组
    const tasks = [
        checkAPI('/redundancy', '冗余消息'),
        checkAPI('/transactions', '交易信息'),
        checkAPI('/blocks', '区块信息'),
        checkAPI('/peers', '节点信息')
    ];
    
    // 执行所有诊断任务
    Promise.all(tasks)
        .then(results => {
            console.log('API诊断完成:');
            const statusTable = {
                '/redundancy': results[0].status,
                '/transactions': results[1].status,
                '/blocks': results[2].status,
                '/peers': results[3].status
            };
            console.table(statusTable);
            console.groupEnd();
        })
        .catch(error => {
            console.error('API诊断出错:', error);
            console.groupEnd();
        });
}

// 修改testAPIs函数以使用新的API诊断工具
function testAPIs() {
    console.log("开始测试API...");
    checkAPIStatus();
}

// 添加手动强制更新方法
window.forceRefresh = function() {
    console.log("手动强制刷新所有数据...");
    refreshAllData();
    return "刷新命令已发送，检查控制台查看详情";
};

// 添加修复工具，可以在控制台中调用
window.fixUI = function() {
    console.log("修复UI元素...");
    
    // 确保所有面板存在
    const panels = ['transactions-panel', 'orphan-blocks-panel', 'network-stats-panel', 'redundancy-panel'];
    panels.forEach(panelId => {
        const panel = document.getElementById(panelId);
        if (!panel) {
            console.error(`找不到面板: #${panelId}`);
        } else {
            console.log(`面板 #${panelId} 已找到`);
            // 确保表格存在
            if (panelId === 'transactions-panel') {
                const table = panel.querySelector('#transactions-table');
                if (!table) {
                    console.error(`找不到交易表格 #transactions-table`);
                }
            } else if (panelId === 'redundancy-panel') {
                const table = panel.querySelector('#redundancy-table');
                if (!table) {
                    console.error(`找不到冗余消息表格 #redundancy-table`);
                }
            }
        }
    });
    
    // 重新刷新数据
    refreshAllData();
    return "UI修复完成，检查控制台查看详情";
};

// 初始化发送区块模态框
function initSendBlockModal() {
    const modal = document.getElementById('send-block-modal');
    const btn = document.getElementById('open-send-block-modal');
    const closeBtn = modal.querySelector('.close');
    const sendBtn = document.getElementById('send-block-btn');
    const resultDiv = document.getElementById('send-block-result');
    
    // 点击按钮打开模态框
    btn.onclick = function() {
        modal.style.display = "block";
        resultDiv.textContent = '';
        resultDiv.className = 'result-message';
    }
    
    // 点击 × 关闭模态框
    closeBtn.onclick = function() {
        modal.style.display = "none";
    }
    
    // 点击模态框外部关闭
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
    
    // 发送区块按钮点击事件
    sendBtn.onclick = function() {
        const targetPeerId = document.getElementById('target-peer-id').value.trim();
        
        if (!targetPeerId) {
            resultDiv.textContent = '请输入目标节点ID';
            resultDiv.className = 'result-message error';
            return;
        }
        
        // 显示加载状态
        resultDiv.textContent = '发送中...';
        resultDiv.className = 'result-message loading';
        
        // 调用API发送区块
        fetch('/api/send_block', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ target_peer_id: targetPeerId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                resultDiv.textContent = data.message;
                resultDiv.className = 'result-message success';
                // 5秒后自动关闭
                setTimeout(() => {
                    modal.style.display = "none";
                    // 刷新消息列表
                    fetchMessages();
                }, 3000);
            } else {
                resultDiv.textContent = data.message;
                resultDiv.className = 'result-message error';
            }
        })
        .catch(error => {
            resultDiv.textContent = `发送失败: ${error.message}`;
            resultDiv.className = 'result-message error';
            console.error('发送区块失败:', error);
        });
    }
}

// 初始化切换显示的内容区域
function initTabPanels() {
    // 找到所有标签页面板区域
    const tabContainers = document.querySelectorAll('.tab-container');
    
    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('.tab-header .tab');
        const panels = container.querySelectorAll('.tab-content .tab-panel');
        
        // 设置初始状态：第一个标签激活
        if(tabs.length > 0) tabs[0].classList.add('active');
        if(panels.length > 0) panels[0].classList.add('active');
        
        // 为每个标签添加点击事件
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                // 移除所有活动状态
                tabs.forEach(t => t.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));
                
                // 设置当前标签和面板为活动状态
                tab.classList.add('active');
                
                // 获取目标面板ID（如果有data-target属性）
                const targetId = tab.getAttribute('data-target');
                if (targetId) {
                    // 根据目标ID查找面板并激活
                    const targetPanel = container.querySelector(`#${targetId}`);
                    if (targetPanel) {
                        targetPanel.classList.add('active');
                        return;
                    }
                }
                
                // 如果没有data-target或找不到目标面板，则按索引激活
                if(panels[index]) panels[index].classList.add('active');
            });
        });
    });
    
    // 调试信息
    console.log('标签面板初始化完成');
}

// 刷新所有数据
function refreshAllData() {
    // 显示更新动画
    document.getElementById('last-updated').classList.add('updating');
    
    Promise.all([
        fetchPeers(),
        fetchBlocks(),
        fetchOrphanBlocks(),
        fetchTransactions(),
        fetchCapacity(),
        fetchRedundancy(),
        fetchBlacklist(),
        fetchNetworkStats(),
        fetchMessages()
    ]).then(() => {
        // 更新最后刷新时间
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        const lastUpdated = document.getElementById('last-updated');
        lastUpdated.textContent = timeString;
        
        // 移除更新动画
        setTimeout(() => {
            lastUpdated.classList.remove('updating');
        }, 300);
    }).catch(error => {
        console.error('数据刷新失败:', error);
    });
}

// 截断长ID
function truncateId(id, length = 16) {
    if (!id) return '未知';
    if (id.length <= length) return id;
    const prefix = id.substring(0, length/2);
    const suffix = id.substring(id.length - length/2);
    return `${prefix}...${suffix}`;
}

// 获取节点信息
function fetchPeers() {
    // 获取延迟数据和节点信息，然后合并显示
    return Promise.all([
        fetch('/peers').then(response => response.json()),
        fetch('/latency').then(response => response.json())
    ])
    .then(([peersData, latencyData]) => {
        const tableBody = document.getElementById('peers-table');
        tableBody.innerHTML = '';
        const section = document.getElementById('peers-section');
        
        if (Object.keys(peersData).length === 0) {
            section.classList.add('empty');
            tableBody.innerHTML = '<tr><td colspan="7" class="empty-state">没有已知节点</td></tr>';
            return;
        }
        
        section.classList.remove('empty');
        
        // 更新节点数量
        updateCounter('peers-section', Object.keys(peersData).length);
        
        // 按照连接状态和ID排序：ALIVE > UNKNOWN > UNREACHABLE
        const sortedPeers = Object.entries(peersData).sort((a, b) => {
            const statusA = a[1].status.toLowerCase();
            const statusB = b[1].status.toLowerCase();
            
            if (statusA === 'alive' && statusB !== 'alive') return -1;
            if (statusA !== 'alive' && statusB === 'alive') return 1;
            if (statusA === 'unknown' && statusB === 'unreachable') return -1;
            if (statusA === 'unreachable' && statusB === 'unknown') return 1;
            
            return a[0].localeCompare(b[0]); // 按ID排序
        });
        
        for (const [peerId, peerInfo] of sortedPeers) {
            const row = document.createElement('tr');
            
            // 处理状态显示
            let statusClass;
            if (peerInfo.status.toLowerCase() === 'alive') {
                statusClass = 'status-online';
            } else if (peerInfo.status.toLowerCase() === 'unreachable') {
                statusClass = 'status-offline';
            } else {
                statusClass = 'status-unknown';
            }
            
            // 处理NAT和轻量级状态
            let natDisplay = '否';
            let lightDisplay = '否';
            
            // 处理NAT状态
            if (peerInfo.nat === true) {
                natDisplay = '是';
            } else if (peerInfo.nat === 'unknown') {
                natDisplay = '未知';
            }
            
            // 处理轻量级状态
            if (peerInfo.light === true) {
                lightDisplay = '是';
            } else if (peerInfo.light === 'unknown') {
                lightDisplay = '未知';
            }
            
            // 获取延迟信息
            let latencyDisplay = '未知';
            if (latencyData[peerId]) {
                latencyDisplay = `${latencyData[peerId].toFixed(2)}`;
                
                // 高亮显示高延迟
                if (latencyData[peerId] > 500) {
                    row.classList.add('highlight-row');
                }
            }
            
            // 根据节点状态设置行样式
            if (peerInfo.status.toLowerCase() === 'alive') {
                row.classList.add('alive-row');
            } else if (peerInfo.status.toLowerCase() === 'unreachable') {
                row.classList.add('unreachable-row');
            }
            
            row.innerHTML = `
                <td><span class="truncate-id" title="${peerInfo.peer_id}">${peerInfo.peer_id}</span></td>
                <td>${peerInfo.ip}</td>
                <td>${peerInfo.port}</td>
                <td><span class="status ${statusClass}">${peerInfo.status}</span></td>
                <td>${natDisplay}</td>
                <td>${lightDisplay}</td>
                <td>${latencyDisplay}</td>
            `;
            tableBody.appendChild(row);
        }
    })
    .catch(error => console.error('获取节点信息失败:', error));
}

// 获取区块信息
function fetchBlocks() {
    return fetch('/blocks')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('blocks-table');
            tableBody.innerHTML = '';
            const section = document.getElementById('blocks-section');
            
            if (data.length === 0) {
                section.classList.add('empty');
                tableBody.innerHTML = '<tr><td colspan="5" class="empty-state">没有区块</td></tr>';
                return;
            }
            
            section.classList.remove('empty');
            
            // 更新区块数量
            updateCounter('blocks-section', data.length);
            
            data.forEach(block => {
                const row = document.createElement('tr');
                
                // 确保显示区块高度
                let height = '未知';
                if (block.height !== undefined && block.height !== null) {
                    height = block.height;
                } else if (data.indexOf(block) === 0) {
                    // 对于第一个区块，如果没有高度，可能是创世区块
                    height = 0;
                } else if (data.indexOf(block) > 0) {
                    // 对于其他区块，可以基于位置估计高度
                    height = data.indexOf(block);
                }
                
                row.innerHTML = `
                    <td><span class="blockchain-id" title="${block.block_id}">${truncateId(block.block_id)}</span></td>
                    <td><span class="blockchain-id" title="${block.prev_block_id}">${truncateId(block.prev_block_id || '创世区块')}</span></td>
                    <td>${height}</td>
                    <td>${formatTimestamp(block.timestamp)}</td>
                    <td>${block.tx_count || block.transactions?.length || '0'}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('获取区块信息失败:', error));
}

// 获取孤立区块信息
function fetchOrphanBlocks() {
    return fetch('/orphans')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('orphan-blocks-table');
            tableBody.innerHTML = '';
            const section = document.getElementById('orphan-blocks-section');
            
            if (data.length === 0) {
                section.classList.add('empty');
                tableBody.innerHTML = '<tr><td colspan="3" class="empty-state">没有孤立区块</td></tr>';
                return;
            }
            
            section.classList.remove('empty');
            
            // 更新孤块数量
            updateCounter('orphan-blocks-section', data.length);
            
            data.forEach(block => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><span class="blockchain-id" title="${block.block_id}">${truncateId(block.block_id)}</span></td>
                    <td><span class="blockchain-id" title="${block.prev_block_id}">${truncateId(block.prev_block_id || '未知')}</span></td>
                    <td>${formatTimestamp(block.timestamp)}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('获取孤立区块信息失败:', error));
}

// 获取交易信息
function fetchTransactions() {
    return fetch('/transactions')
        .then(response => DataAdapter.processResponse(response))
        .then(data => {
            const tableBody = document.getElementById('transactions-table');
            if (!tableBody) {
                console.error('找不到交易表格(#transactions-table)');
                return;
            }
            
            tableBody.innerHTML = '';
            
            // 取得正确的交易面板元素
            const panel = document.getElementById('transactions-panel');
            
            console.log("解析后交易数据:", data);
            
            try {
                // 通过DataAdapter处理交易数据
                data = DataAdapter.processTransactionData(data);
                
                if (data.length === 0) {
                    if (panel) {
                        panel.classList.add('empty');
                    }
                    tableBody.innerHTML = '<tr><td colspan="5" class="empty-state">没有交易</td></tr>';
                    return;
                }
                
                if (panel) {
                    panel.classList.remove('empty');
                }
                
                // 更新交易数量 - 使用相应的标签
                const networkMonitor = document.getElementById('network-monitor-section');
                if (networkMonitor) {
                    const tabElement = networkMonitor.querySelector('.tab[data-target="transactions-panel"]');
                    if (tabElement) {
                        let counter = tabElement.querySelector('.counter');
                        if (!counter) {
                            counter = document.createElement('span');
                            counter.className = 'counter';
                            tabElement.appendChild(counter);
                        }
                        counter.textContent = data.length;
                    }
                }
                
                data.forEach(tx => {
                    console.log("处理交易:", tx);
                    const row = document.createElement('tr');
                    
                    // 统一处理不同格式的交易数据
                    // 从screenshots看，交易数据的格式为 {amount, from, to, id, timestamp, type} 
                    const txId = tx.id || '';
                    const fromPeer = tx.from || tx.from_peer || '';
                    const toPeer = tx.to || tx.to_peer || '';
                    const amount = tx.amount || '未知';
                    const timestamp = tx.timestamp || '';
                    
                    row.innerHTML = `
                        <td><span class="blockchain-id" title="${txId}">${truncateId(txId || '未知')}</span></td>
                        <td><span class="blockchain-id" title="${fromPeer}">${truncateId(fromPeer || '未知', 10)}</span></td>
                        <td><span class="blockchain-id" title="${toPeer}">${truncateId(toPeer || '未知', 10)}</span></td>
                        <td>${amount}</td>
                        <td>${formatTimestamp(timestamp)}</td>
                    `;
                    tableBody.appendChild(row);
                });
            } catch (e) {
                console.error("处理交易数据出错:", e);
                tableBody.innerHTML = `<tr><td colspan="5" class="empty-state">处理交易数据出错: ${e.message}</td></tr>`;
            }
        })
        .catch(error => {
            console.error('获取交易信息失败:', error);
            const tableBody = document.getElementById('transactions-table');
            if (tableBody) {
                tableBody.innerHTML = `<tr><td colspan="5" class="empty-state">获取交易信息失败: ${error.message}</td></tr>`;
            }
        });
}

// 获取容量信息
function fetchCapacity() {
    return fetch('/capacity')
        .then(response => response.json())
        .then(data => {
            document.getElementById('capacity').textContent = data;
        })
        .catch(error => console.error('获取容量信息失败:', error));
}

// 获取冗余信息
function fetchRedundancy() {
    return fetch('/redundancy')
        .then(response => DataAdapter.processResponse(response))
        .then(data => {
            const tableBody = document.getElementById('redundancy-table');
            if (!tableBody) {
                console.error('找不到冗余消息表格(#redundancy-table)');
                return;
            }
            
            tableBody.innerHTML = '';
            
            // 修正：使用正确的选择器，从网络监控面板中查找对应的面板
            const panel = document.getElementById('redundancy-panel');
            
            console.log("冗余消息解析数据:", data); // 添加调试日志
            
            try {
                // 通过DataAdapter处理数据
                data = DataAdapter.processRedundancyData(data);
                
                // 检查是否有冗余消息
                if (Object.keys(data).length === 0) {
                    if (panel) {
                        panel.classList.add('empty');
                    }
                    tableBody.innerHTML = '<tr><td colspan="2" class="empty-state">没有冗余消息</td></tr>';
                    return;
                }
                
                if (panel) {
                    panel.classList.remove('empty');
                }
                
                // 更新消息数量 - 使用网络监控面板标题
                const networkMonitor = document.getElementById('network-monitor-section');
                if (networkMonitor) {
                    const tabElement = networkMonitor.querySelector('.tab[data-target="redundancy-panel"]');
                    if (tabElement) {
                        let counter = tabElement.querySelector('.counter');
                        if (!counter) {
                            counter = document.createElement('span');
                            counter.className = 'counter';
                            tabElement.appendChild(counter);
                        }
                        counter.textContent = Object.keys(data).length;
                    }
                }
                
                // 按重复次数排序
                const sortedMessages = Object.entries(data).sort((a, b) => b[1] - a[1]);
                
                sortedMessages.forEach(([msgId, count]) => {
                    const row = document.createElement('tr');
                    // 高亮显示高重复次数
                    if (count > 3) {
                        row.classList.add('highlight-row');
                    }
                    
                    row.innerHTML = `
                        <td><span class="blockchain-id" title="${msgId}">${truncateId(msgId, 20)}</span></td>
                        <td>${count}</td>
                    `;
                    tableBody.appendChild(row);
                });
                
                // 如果有冗余消息且数量大于5，自动显示冗余消息标签页
                if (sortedMessages.length > 5) {
                    // 获取冗余消息标签并激活
                    const redundancyTab = document.querySelector('.tab[data-target="redundancy-panel"]');
                    if (redundancyTab) {
                        const tabContainer = redundancyTab.closest('.tab-container');
                        if (tabContainer) {
                            const allTabs = tabContainer.querySelectorAll('.tab');
                            const allPanels = tabContainer.querySelectorAll('.tab-panel');
                            
                            // 移除所有活动状态
                            allTabs.forEach(t => t.classList.remove('active'));
                            allPanels.forEach(p => p.classList.remove('active'));
                            
                            // 激活冗余消息标签和面板
                            redundancyTab.classList.add('active');
                            const redundancyPanel = document.getElementById('redundancy-panel');
                            if (redundancyPanel) {
                                redundancyPanel.classList.add('active');
                            }
                        }
                    }
                }
            } catch (e) {
                console.error("处理冗余消息数据出错:", e);
                tableBody.innerHTML = `<tr><td colspan="2" class="empty-state">处理数据出错: ${e.message}</td></tr>`;
            }
        })
        .catch(error => {
            console.error('获取冗余信息失败:', error);
            const tableBody = document.getElementById('redundancy-table');
            if (tableBody) {
                tableBody.innerHTML = `<tr><td colspan="2" class="empty-state">获取冗余消息失败: ${error.message}</td></tr>`;
            }
        });
}

// 获取黑名单信息（合并）
function fetchBlacklist() {
    // 这里调用合并函数，不直接使用旧的fetchBlacklist功能
    return fetchCombinedBlacklist();
}

// 获取合并的黑名单信息
function fetchCombinedBlacklist() {
    // 同时获取黑名单和节点黑名单详情
    return Promise.all([
        fetch('/api/blacklist').then(response => response.json()),
        fetch('/api/peer_blacklists').then(response => response.json())
    ])
    .then(([blacklist, peerBlacklists]) => {
        const tableBody = document.getElementById('blacklist-combined-table');
        tableBody.innerHTML = '';
        const section = document.getElementById('blacklist-combined-section');
        
        // 构建黑名单节点统计
        const nodeStats = {};
        
        // 统计每个节点被拉黑的次数
        for (const [peerId, blacklistNodes] of Object.entries(peerBlacklists)) {
            blacklistNodes.forEach(nodeId => {
                if (!nodeStats[nodeId]) {
                    nodeStats[nodeId] = { count: 0, blacklistedBy: [] };
                }
                nodeStats[nodeId].count++;
                nodeStats[nodeId].blacklistedBy.push(peerId);
            });
        }
        
        // 如果本地黑名单和节点黑名单详情都为空
        if (blacklist.length === 0 && Object.keys(nodeStats).length === 0) {
            section.classList.add('empty');
            tableBody.innerHTML = '<tr><td colspan="2" class="empty-state">没有黑名单信息</td></tr>';
            return;
        }
        
        section.classList.remove('empty');
        
        // 添加本地黑名单中的节点（如果未在统计中）
        blacklist.forEach(nodeId => {
            if (!nodeStats[nodeId]) {
                nodeStats[nodeId] = { count: 1, blacklistedBy: ['本节点'] };
            } else if (!nodeStats[nodeId].blacklistedBy.includes('本节点')) {
                nodeStats[nodeId].count++;
                nodeStats[nodeId].blacklistedBy.push('本节点');
            }
        });
        
        // 更新黑名单节点数量
        updateCounter('blacklist-combined-section', Object.keys(nodeStats).length);
        
        // 按被拉黑次数排序
        const sortedNodes = Object.entries(nodeStats).sort((a, b) => b[1].count - a[1].count);
        
        sortedNodes.forEach(([nodeId, stats]) => {
            const row = document.createElement('tr');
            
            // 高亮显示被多个节点拉黑的节点
            if (stats.count > 2) {
                row.classList.add('highlight-row');
            }
            
            row.innerHTML = `
                <td>${nodeId}</td>
                <td>${stats.count} (${stats.blacklistedBy.join(', ')})</td>
            `;
            tableBody.appendChild(row);
        });
    })
    .catch(error => console.error('获取黑名单信息失败:', error));
}

// 获取节点黑名单详情 - 保留函数但不再使用
function fetchPeerBlacklists() {
    // 这个函数保留但不再调用，功能已被合并到fetchCombinedBlacklist
    return Promise.resolve();
}

// 获取网络统计信息
function fetchNetworkStats() {
    return fetch('/api/network/stats')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('network-stats-content');
            const section = document.getElementById('network-stats-section');
            
            if (!data || (Object.keys(data.outbox_status || {}).length === 0 && Object.keys(data.drop_stats || {}).length === 0)) {
                section.classList.add('empty');
                container.innerHTML = '<div class="empty-state">没有网络统计数据</div>';
                return;
            }
            
            section.classList.remove('empty');
            
            let html = '<dl>';
            
            // 显示发送队列状态
            html += '<dt>发送队列状态</dt>';
            if (Object.keys(data.outbox_status || {}).length === 0) {
                html += '<dd>无发送队列数据</dd>';
            } else {
                html += '<dd><ul>';
                for (const [peerId, queueInfo] of Object.entries(data.outbox_status)) {
                    html += `<li>节点 ${peerId}: ${queueInfo.total_messages} 条消息等待发送</li>`;
                }
                html += '</ul></dd>';
            }
            
            // 显示消息丢弃统计
            html += '<dt>消息丢弃统计</dt>';
            if (Object.keys(data.drop_stats || {}).length === 0) {
                html += '<dd>无消息丢弃数据</dd>';
            } else {
                html += '<dd><ul>';
                for (const [msgType, count] of Object.entries(data.drop_stats)) {
                    html += `<li>${msgType}: 丢弃 ${count} 次</li>`;
                }
                html += '</ul></dd>';
            }
            
            html += '</dl>';
            container.innerHTML = html;
        })
        .catch(error => console.error('获取网络统计信息失败:', error));
}

// 获取消息记录
function fetchMessages() {
    return fetch('/api/messages')
        .then(response => response.json())
        .then(data => {
            // 按消息类型归类
            const messagesByType = {
                block: [],
                tx: [],
                ping: [],
                other: []
            };
            
            // 清空所有消息表
            document.getElementById('all-messages-table').innerHTML = '';
            document.getElementById('block-messages-table').innerHTML = '';
            document.getElementById('tx-messages-table').innerHTML = '';
            document.getElementById('ping-messages-table').innerHTML = '';
            document.getElementById('other-messages-table').innerHTML = '';
            
            const section = document.getElementById('messages-section');
            
            if (data.length === 0) {
                section.classList.add('empty');
                document.getElementById('all-messages-table').innerHTML = '<tr><td colspan="5" class="empty-state">没有消息记录</td></tr>';
                document.getElementById('block-messages-table').innerHTML = '<tr><td colspan="5" class="empty-state">没有区块相关消息</td></tr>';
                document.getElementById('tx-messages-table').innerHTML = '<tr><td colspan="5" class="empty-state">没有交易相关消息</td></tr>';
                document.getElementById('ping-messages-table').innerHTML = '<tr><td colspan="5" class="empty-state">没有PING/PONG消息</td></tr>';
                document.getElementById('other-messages-table').innerHTML = '<tr><td colspan="5" class="empty-state">没有其他消息</td></tr>';
                return;
            }
            
            section.classList.remove('empty');
            
            // 按时间倒序排列
            data.sort((a, b) => b.timestamp - a.timestamp);
            
            // 分类消息
            data.forEach(message => {
                // 根据消息类型分类
                const msgType = (message.msg_type || '').toUpperCase();
                
                if (msgType.includes('BLOCK') || msgType === 'INV' || msgType === 'GETBLOCK') {
                    messagesByType.block.push(message);
                } else if (msgType.includes('TX') || msgType === 'TRANSACTION') {
                    messagesByType.tx.push(message);
                } else if (msgType === 'PING' || msgType === 'PONG') {
                    messagesByType.ping.push(message);
                } else {
                    messagesByType.other.push(message);
                }
            });
            
            // 限制各类型最多显示100条消息
            Object.keys(messagesByType).forEach(type => {
                if (messagesByType[type].length > 100) {
                    messagesByType[type] = messagesByType[type].slice(0, 100);
                }
            });
            
            // 创建"全部"分类，包含所有子分类的消息
            const allMessages = [
                ...messagesByType.block,
                ...messagesByType.tx,
                ...messagesByType.ping,
                ...messagesByType.other
            ];
            
            // 重新按时间倒序排列"全部"分类
            allMessages.sort((a, b) => b.timestamp - a.timestamp);
            
            // 更新消息数量计数器
            updateCounter('messages-section', allMessages.length);
            
            // 渲染各类消息表格
            renderMessagesTable('all-messages-table', allMessages);
            renderMessagesTable('block-messages-table', messagesByType.block);
            renderMessagesTable('tx-messages-table', messagesByType.tx);
            renderMessagesTable('ping-messages-table', messagesByType.ping);
            renderMessagesTable('other-messages-table', messagesByType.other);
        })
        .catch(error => console.error('获取消息记录失败:', error));
}

// 渲染消息表格
function renderMessagesTable(tableId, messages) {
    const tableBody = document.getElementById(tableId);
    
    if (messages.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="empty-state">没有${getMessageTypeName(tableId)}消息</td></tr>`;
        return;
    }
    
    messages.forEach(message => {
        const row = document.createElement('tr');
        
        // 根据消息类型设置样式
        if (message.type === 'SENT') {
            row.classList.add('sent-message');
        } else if (message.type === 'RECEIVED') {
            row.classList.add('received-message');
        }
        
        // 格式化消息内容显示
        let content = '';
        let fullContent = '';
        
        if (typeof message.content === 'object') {
            try {
                // 准备完整内容用于悬停显示
                fullContent = JSON.stringify(message.content, null, 2);
                
                // 尝试提取重要字段并美化显示
                const importantFields = ['type', 'message_id', 'block_id', 'prev_block_id', 'id', 'tx_id', 'target_id', 'sender_id'];
                const contentObj = message.content;
                
                let contentPreview = [];
                
                // 优先显示重要字段
                importantFields.forEach(field => {
                    if (contentObj[field]) {
                        let value = contentObj[field];
                        // 对于ID类型字段，使用截断函数
                        if (field.includes('id') && typeof value === 'string' && value.length > 12) {
                            value = truncateId(value, 12);
                        }
                        contentPreview.push(`${field}: ${value}`);
                    }
                });
                
                // 如果没有重要字段，尝试其他字段
                if (contentPreview.length === 0) {
                    const keys = Object.keys(contentObj).slice(0, 4);
                    keys.forEach(key => {
                        let value = contentObj[key];
                        if (typeof value === 'object') value = '[Object]';
                        contentPreview.push(`${key}: ${value}`);
                    });
                }
                
                content = contentPreview.join(', ');
            } catch (e) {
                content = '无法解析的对象';
                fullContent = String(message.content);
            }
        } else {
            content = message.content || '';
            fullContent = content;
        }
        
        row.innerHTML = `
            <td>${formatTimestamp(message.timestamp)}</td>
            <td>${message.msg_type || '未知'}</td>
            <td><span class="blockchain-id" title="${message.sender || '未知'}">${truncateId(message.sender || '未知', 8)}</span></td>
            <td><span class="blockchain-id" title="${message.receiver || '未知'}">${truncateId(message.receiver || '未知', 8)}</span></td>
            <td><span class="message-content" title="${fullContent}">${content}</span></td>
        `;
        tableBody.appendChild(row);
    });
}

// 获取消息类型名称
function getMessageTypeName(tableId) {
    switch(tableId) {
        case 'all-messages-table': return '';
        case 'block-messages-table': return '区块相关';
        case 'tx-messages-table': return '交易相关';
        case 'ping-messages-table': return 'PING/PONG';
        case 'other-messages-table': return '其他';
        default: return '';
    }
}

// 更新卡片标题中的计数器
function updateCounter(sectionId, count) {
    const section = document.getElementById(sectionId);
    if (!section) {
        console.warn(`未找到ID为${sectionId}的区域`);
        return;
    }
    
    // 特殊处理：冗余消息标签在网络监控面板下
    if (sectionId === 'redundancy-section') {
        const networkSection = document.getElementById('network-monitor-section');
        if (networkSection) {
            const tabContainer = networkSection.querySelector('.tab-container');
            if (tabContainer) {
                const redundancyTab = tabContainer.querySelector('.tab[data-target="redundancy-panel"]');
                if (redundancyTab) {
                    // 检查是否存在计数器
                    let counter = redundancyTab.querySelector('.counter');
                    if (!counter) {
                        counter = document.createElement('span');
                        counter.className = 'counter';
                        redundancyTab.appendChild(counter);
                    }
                    counter.textContent = count;
                    return;
                }
            }
        }
    }
    
    // 标准处理：直接在标题中添加计数器
    const title = section.querySelector('h2');
    if (!title) {
        console.warn(`未在${sectionId}中找到h2标题元素`);
        return;
    }
    
    // 查找或创建计数器元素
    let counter = title.querySelector('.counter');
    if (!counter) {
        counter = document.createElement('span');
        counter.className = 'counter';
        title.appendChild(counter);
    }
    
    counter.textContent = count;
}

// 格式化时间戳
function formatTimestamp(timestamp) {
    if (!timestamp) return '未知';
    
    try {
        const date = new Date(timestamp * 1000);
        return date.toLocaleString();
    } catch (e) {
        return timestamp;
    }
} 