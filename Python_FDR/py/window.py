"""
交互式主程序，用于调用FM_part和j_to_v模块
根据规则文件重构版本
"""


import sys
import os
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from FM_part import CircuitPartitioner, process_circuit
from G_to_v import GToV, generate_verilog
import time


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
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        base = os.path.splitext(circuit_name)[0]
        circuit_info_path = os.path.join(output_dir, f"{base}_circuit_info.json")
        with open(circuit_info_path, 'w') as f:
            json.dump(partitions['circuit_info'], f, indent=4)

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

    import importlib.util
    import sys
    circuit_dir = os.path.join(os.path.dirname(__file__), '..', 'circuit')
    simulator_path = os.path.join(os.path.dirname(__file__), 'simulator.py')

    while True:
        print("" + "="*50)
        print("欢迎使用Python_FDR电路分割和Verilog生成工具")
        print("="*50)
        print("请选择操作:")
        print("1. 电路分割 (将Verilog文件分割为两个子电路)")
        print("2. 生成Verilog (从分割结果GraphML文件生成可综合的Verilog文件)")
        print("3. 运行仿真 (选择电路后调用simulator)")
        print("4. 退出程序")

        choice = input("请输入选项 (1/2/3/4): ").strip()

        if choice == '4':
            print("程序已退出。")
            break

        if choice not in ['1', '2', '3']:
            print("无效选项，请重新输入!")
            continue

        if choice in ['1', '2']:
            # 获取电路名称
            circuit_name = input("请输入电路名称 (例如: s27, s382): ").strip()
            if not circuit_name:
                print("电路名称不能为空!")
                continue
            if choice == '1':
                # 执行电路分割
                success = partition_circuit(circuit_name)
                if success:
                    print(f"电路 {circuit_name} 分割完成!")
            elif choice == '2':
                # 从GraphML生成Verilog
                success = generate_verilog_from_graphml(circuit_name)
                if success:
                    print(f"电路 {circuit_name} 的Verilog文件生成完成!")
        elif choice == '3':
            # 读取circuit目录下所有电路文件（.v结尾）
            circuits = [f for f in os.listdir(circuit_dir) if f.endswith('.v')]
            if not circuits:
                print("未找到任何电路文件！")
                continue
            print("可用电路列表：")
            for idx, fname in enumerate(circuits):
                print(f"{idx+1}. {fname}")
            while True:
                sel = input(f"请选择电路 (1-{len(circuits)}): ").strip()
                if not sel.isdigit() or not (1 <= int(sel) <= len(circuits)):
                    print("无效选择，请重新输入！")
                    continue
                break
            selected_circuit = circuits[int(sel)-1]
            # 检查分割/仿真相关文件是否存在
            base = os.path.splitext(selected_circuit)[0]
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
            circuit_info_file = os.path.join(output_dir, f"{base}_circuit_info.json")
            golden_file = os.path.join(output_dir, f"{base}_golden.json")
            fault_file = os.path.join(output_dir, f"{base}_fault.json")
            missing = []
            for f in [circuit_info_file, golden_file, fault_file]:
                if not os.path.exists(f):
                    missing.append(os.path.basename(f))
            if missing:
                print("警告：以下仿真/分割相关文件不存在：")
                for f in missing:
                    print(f"  - {f}")
                if any('circuit_info' in f for f in missing):
                    print("circuit_info.json 不存在，请先进行电路分割（选项1）生成。")
                print("你可以先进行电路分割（选项1），也可以直接仿真原始电路。")
                goon = input("是否继续仿真？(y/n): ").strip().lower()
                if goon != 'y':
                    print("已取消仿真。"); continue
            # 调用simulator.py的main函数
            print(f"即将对电路 {selected_circuit} 进行仿真...")
            # 动态加载simulator.py模块
            spec = importlib.util.spec_from_file_location("simulator", simulator_path)
            simulator = importlib.util.module_from_spec(spec)
            sys.modules["simulator"] = simulator
            spec.loader.exec_module(simulator)
            # 修改config.json中的circuit_info_file/golden_file/fault_file/path/tcl_file为对应电路
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            config_data['circuit_info_file'] = f"./output/{base}_circuit_info.json"
            config_data['golden_file'] = f"./output/{base}_golden.json"
            config_data['fault_file'] = f"./output/{base}_fault.json"
            config_data['path'] = '.'
            config_data['tcl_file'] = f"./{base}_run.ucli"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            simulator.main()
            print("仿真流程结束。")


if __name__ == "__main__":
    main()
