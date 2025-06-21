import matplotlib.pyplot as plt
import numpy as np

def plot_avg_comparison():
    # 数据准备
    peers = ['Peer0', 'Peer1', 'Peer2', 'Peer3', 'Peer4']
    fanout1_avg = [44, 39.25, 9.25, 10.75, 29]  # 图1数据
    fanout10_avg = [41, 43.25, 16.5, 15, 34.75]  # 图2数据
    
    # 创建图表
    plt.figure(figsize=(10, 6))
    
    # 设置柱形图位置
    x = np.arange(len(peers))
    width = 0.35
    
    # 绘制柱形图
    bars1 = plt.bar(x - width/2, fanout1_avg, width, label='fanout=1', color='#1f77b4')
    bars2 = plt.bar(x + width/2, fanout10_avg, width, label='fanout=10', color='#ff7f0e')
    
    # 添加数据标签
    for bar in bars1 + bars2:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    # 图表装饰
    plt.title('Redundancy Messages AVG Comparison (fanout 1 vs 10)', pad=20)
    plt.xlabel('Peer ID')
    plt.ylabel('Average Redundancy Count')
    plt.xticks(x, peers)
    plt.legend()
    
    # 添加网格线
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 添加底部文字
    plt.figtext(0.5, 0.01, 'total peers:5 | Data from user-provided images', ha='center')
    
    plt.tight_layout()
    plt.savefig('fanout_avg_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    plot_avg_comparison()