import matplotlib.pyplot as plt
import numpy as np

def plot_experiment_results():
    # 数据准备
    experiment_num = [1, 2, 3, 4, 5]
    peer1_data = [56, 42, 35, 39, 33]
    peer2_data = [15, 21, 8, 15, 23]
    peer1_avg = 41
    peer2_avg = 16.4
    
    # 创建图表
    plt.figure(figsize=(10, 6))
    
    # 绘制折线图
    plt.plot(experiment_num, peer1_data, 'o-', label='Peer1', linewidth=2, markersize=8)
    plt.plot(experiment_num, peer2_data, 's--', label='Peer2', linewidth=2, markersize=8)
    
    # 添加数据标签
    for x, y1, y2 in zip(experiment_num, peer1_data, peer2_data):
        plt.text(x, y1+1, str(y1), ha='center')
        plt.text(x, y2+1, str(y2), ha='center')
    
    # 添加平均值水平线
    plt.axhline(y=peer1_avg, color='blue', linestyle=':', linewidth=1.5, 
                label=f'Peer1 Avg ({peer1_avg})')
    plt.axhline(y=peer2_avg, color='orange', linestyle=':', linewidth=1.5, 
                label=f'Peer2 Avg ({peer2_avg})')
    
    # 图表装饰
    plt.title('Experiment Results Comparison (fanout=10)', pad=20)
    plt.xlabel('Experiment Number')
    plt.ylabel('Value')
    plt.xticks(experiment_num)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # 添加底部信息
    plt.figtext(0.5, 0.01, 'Duration: 3min | Data from user-provided table', ha='center')
    
    plt.tight_layout()
    plt.savefig('experiment_comparison_with_avg.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    plot_experiment_results()