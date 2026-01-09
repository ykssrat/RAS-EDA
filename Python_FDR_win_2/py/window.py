"""
交互式主程序，用于调用FM_part和j_to_v模块
根据规则文件重构版本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from FM_part import process_circuit
from G_to_v import generate_verilog
from simulator import Config, CircuitInfo, Simulator
import time


def run_fdr_analysis():
    """
    调用simulator模块执行FDR分析
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.abspath(os.path.join(script_dir, '..', 'config.json'))

    if not os.path.exists(config_path):
        print(f"错误：找不到配置文件 {config_path}")
        return

    config = Config(config_path)
    circuit = CircuitInfo(config)
    config.print_config()
    sim = Simulator(config)

    # golden
    sim.write_golden_tcl()
    sim.clean()
    sim.compile()
    sim.simulate()
    circuit.get_circuit_info()
    circuit.get_golden()

    # fault
    sim.write_fault_tcl(circuit.injection_reg)
    sim.simulate()
    circuit.get_fault()
    circuit.cal_result()

    print("FDR分析完成")


def partition_circuit(circuit_name):
    """
    对电路进行分割
    """
    # 自动添加.v扩展名（如果没有的话）
    verilog_filename = circuit_name if circuit_name.endswith('.v') else f"{circuit_name}.v"

    # 检查文件是否存在
    verilog_file = os.path.join(os.path.dirname(__file__), '..', 'circuit', verilog_filename)
    if not os.path.exists(verilog_file):
        print(f"错误：找不到文件 {verilog_file}")
        print("请确保文件存在于circuit目录下")
        return False

    print(f"开始处理电路: {verilog_filename}")

    start_time = time.time()
    partitions = process_circuit(circuit_name)
    elapsed_time = time.time() - start_time

    if partitions:
        print(f"分割完成，耗时: {elapsed_time:.2f} 秒")
        print("电路分割完成，结果已保存到output目录")
        print(f"分区A节点数: {partitions['partition_a_count']}")
        print(f"分区B节点数: {partitions['partition_b_count']}")
        print(f"割集大小: {partitions['cutsize']}")

        # 检查分区端口是否符合规则
        if 'circuit_info' in partitions and 'partition_ports' in partitions['circuit_info']:
            partition_a_ports = partitions['circuit_info']['partition_ports']['partition_a']
            partition_b_ports = partitions['circuit_info']['partition_ports']['partition_b']

            # 检查A区是否包含所有输入端口
            original_inputs = ["CK", "G0", "G1", "G2", "G3"]
            all_inputs_in_a = all(inp in partition_a_ports['inputs'] for inp in original_inputs)
            print(f"A区包含所有输入端口: {all_inputs_in_a}")

            # 检查B区是否包含输出端口
            original_outputs = ["G17"]
            all_outputs_in_b = all(out in partition_b_ports['outputs'] for out in original_outputs)
            print(f"B区包含所有输出端口: {all_outputs_in_b}")

        return True
    else:
        print("电路分割失败")
        return False


def generate_verilog_from_graphml(circuit_name):
    """
    从GraphML文件生成Verilog文件
    """
    success = generate_verilog(circuit_name)

    if success:
        # 显示生成的文件信息
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        partition_a_file = os.path.join(output_dir, f"{circuit_name}_a.v")
        partition_b_file = os.path.join(output_dir, f"{circuit_name}_b.v")

        print("Verilog文件生成完成:")
        print(f"  - {partition_a_file}")
        print(f"  - {partition_b_file}")
        return True
    else:
        return False


def main():
    """
    主函数
    """
    while True:
        print("" + "="*50)
        print("欢迎使用Python_FDR工具")
        print("="*50)
        print("请选择操作:")
        print("1. FDR分析")
        print("2. 电路分割 (将Verilog文件分割为两个子电路)")
        print("3. 生成Verilog (从分割结果GraphML文件生成可综合的Verilog文件)")
        print("4. 退出程序")

        choice = input("请输入选项 (1/2/3/4): ").strip()

        if choice == '4':
            print("程序已退出。")
            break

        if choice not in ['1', '2', '3']:
            print("无效选项，请重新输入!")
            continue

        if choice == '1':
            run_fdr_analysis()

        else:
            # 获取电路名称（分割和生成Verilog共用）
            circuit_name = input("请输入电路名称 (例如: s27, s382): ").strip()

            if not circuit_name:
                print("电路名称不能为空!")
                continue

            if choice == '2':
                success = partition_circuit(circuit_name)
                if success:
                    print(f"电路 {circuit_name} 分割完成!")

            elif choice == '3':
                success = generate_verilog_from_graphml(circuit_name)
                if success:
                    print(f"电路 {circuit_name} 的Verilog文件生成完成!")


if __name__ == "__main__":
    main()
