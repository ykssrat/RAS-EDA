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
            if 'circuit_info' in partitions:
                json.dump(partitions['circuit_info'], f, indent=4)
            else:
                # 兼容性：如果没有 circuit_info，保存整个分割字典以便排查
                json.dump(partitions, f, indent=4)
                print("警告：分割结果中缺少 'circuit_info'，已保存整个分割字典。")

        print(f"分割完成，耗时: {elapsed_time:.2f} 秒")
        print("电路分割完成，结果已保存到output目录")
        print(f"分区A节点数: {partitions.get('partition_a_count')}")
        print(f"分区B节点数: {partitions.get('partition_b_count')}")
        print(f"割集大小: {partitions.get('cutsize')}")

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


def generate_verilog_from_graphml(circuit_name, circuit_dir):
    """
    从GraphML文件生成Verilog文件，并把生成的 .v 放到 `circuit` 目录
    """
    # 将生成的 Verilog 写到 circuit_dir
    success = generate_verilog(circuit_name, target_dir=circuit_dir)

    if success:
        partition_a_file = os.path.join(circuit_dir, f"{circuit_name}_a.v")
        partition_b_file = os.path.join(circuit_dir, f"{circuit_name}_b.v")

        print("Verilog文件生成完成，已放入 circuit 目录:")
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
        print("2. 生成Verilog (从分割结果GraphML文件生成可综合的Verilog文件，生成文件放入 circuit 目录)")
        print("3. 运行仿真 (选择电路后调用simulator)")
        print("4. 退出程序")

        try:
            choice = input("请输入选项 (1/2/3/4): ").strip()
        except EOFError:
            print("非交互模式，程序退出。")
            break

        if choice == '4':
            print("程序已退出。")
            break

        if choice not in ['1', '2', '3']:
            print("无效选项，请重新输入!")
            continue

        if choice in ['1', '2']:
            # 列出 circuit 目录下的可供选择的原始电路（仅数字选择）
            # 排除 *_a.v / *_b.v / *_tb.v / stdcells.v / test.v
            circuits = [f for f in os.listdir(circuit_dir) if f.endswith('.v') and not f.endswith('_a.v') and not f.endswith('_b.v') and not f.endswith('_tb.v') and f not in ['stdcells.v','tb.v','test.v']]
            if not circuits:
                print("未找到可供选择的原始电路！")
                continue

            print("可用电路列表：")
            for idx, fname in enumerate(circuits):
                print(f"{idx+1}. {fname}")

            sel = input(f"请选择电路 (1-{len(circuits)}): ").strip()
            if not sel.isdigit() or not (1 <= int(sel) <= len(circuits)):
                print("无效选择，请使用列表序号！")
                continue

            circuit_name = os.path.splitext(circuits[int(sel)-1])[0]

            if choice == '1':
                # 执行电路分割
                success = partition_circuit(circuit_name)
                if success:
                    print(f"电路 {circuit_name} 分割完成!")
            elif choice == '2':
                # 从GraphML生成Verilog（写入 circuit 目录）
                success = generate_verilog_from_graphml(circuit_name, circuit_dir)
                if success:
                    print(f"电路 {circuit_name} 的Verilog文件生成完成并放入 circuit 目录!")
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
            base = os.path.splitext(selected_circuit)[0]
            # 动态修改 verilog_file.f
            verilog_f_path = os.path.join(circuit_dir, 'verilog_file.f')

            # 如果选择的是分区文件（如 s27_a.v 或 s27_b.v），使用原始 tb（s27_tb.v）并同时包含两个分区文件
            files_to_write = []
            use_tb_output_path = None
            if base.endswith('_a') or base.endswith('_b'):
                orig_base = base.rsplit('_', 1)[0]
                tb_file = f"{orig_base}_tb.v"
                files_to_write = [f"./circuit/{tb_file}", f"./circuit/{orig_base}_a.v", f"./circuit/{orig_base}_b.v", "./circuit/stdcells.v"]

                # 如果 partition 的 tb 文件在 circuit 下不存在，尝试从原始 tb（放在 circuit 下）生成到 output 并改写引用
                parent_tb_path = os.path.join(circuit_dir, tb_file)
                out_tb_path = os.path.join(os.path.dirname(__file__), '..', 'output', f"{base}_tb.v")
                if not os.path.exists(parent_tb_path):
                    print(f"警告：未找到父 testbench {parent_tb_path}，无法基于其构造分区 tb。")
                else:
                    # 如果分区 tb 在 output 下不存在，则生成
                    if not os.path.exists(out_tb_path):
                        try:
                            import re
                            with open(parent_tb_path, 'r', encoding='utf-8') as pf:
                                tb_text = pf.read()
                            # 修改模块名： module {orig_base}_tb -> module {base}_tb
                            tb_text = re.sub(rf"module\s+{re.escape(orig_base)}_tb\b", f"module {base}_tb", tb_text)
                            # 修改 DUT 实例： 第一个以 orig_base 开头的实例名，替换模块名为 base，并给实例名添加后缀
                            inst_pat = re.compile(rf"(^\s*){re.escape(orig_base)}\s+(\w+)\s*\(", re.MULTILINE)
                            m = inst_pat.search(tb_text)
                            if m:
                                old_inst = m.group(2)
                                new_inst = f"{old_inst}_{base.split('_')[-1]}"
                                tb_text = inst_pat.sub(lambda mo: f"{mo.group(1)}{base} {new_inst}(", tb_text, count=1)
                                # 替换实例名的其他引用
                                tb_text = re.sub(rf"\b{re.escape(old_inst)}\b", new_inst, tb_text)
                            # 写入 output 目录（遵守不修改 circuit/* 的规则）
                            os.makedirs(os.path.dirname(out_tb_path), exist_ok=True)
                            with open(out_tb_path, 'w', encoding='utf-8') as outf:
                                outf.write(tb_text)
                            # 将 files_to_write 中的 ./circuit/{tb_file} 替换为 ./output/{base}_tb.v
                            files_to_write[0] = f"./output/{base}_tb.v"
                        except Exception as e:
                            print(f"生成分区 testbench 失败: {e}")
            else:
                tb_file = f"{base}_tb.v"
                files_to_write = [f"./circuit/{tb_file}", f"./circuit/{selected_circuit}", "./circuit/stdcells.v"]

            # 写入 verilog_file.f
            with open(verilog_f_path, 'w') as f:
                for p in files_to_write:
                    f.write(p + "\n")

            # 检查分割/仿真相关文件是否存在（使用 base 的原名作为参考）
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
            # 针对分区情况，circuit_info 等文件名应基于 orig_base
            ref_base = orig_base if (base.endswith('_a') or base.endswith('_b')) else base
            circuit_info_file = os.path.join(output_dir, f"{ref_base}_circuit_info.json")
            golden_file = os.path.join(output_dir, f"{ref_base}_golden.json")
            fault_file = os.path.join(output_dir, f"{ref_base}_fault.json")
            missing = []
            for fpath in [circuit_info_file, golden_file, fault_file]:
                if not os.path.exists(fpath):
                    missing.append(os.path.basename(fpath))
            if missing:
                print("警告：以下仿真/分割相关文件不存在：")
                for f in missing:
                    print(f"  - {f}")
                if any('circuit_info' in f for f in missing):
                    print("circuit_info.json 不存在，程序将尝试从父电路的输出文件生成缺失的 per-partition 文件（若可能）。")
                print("将继续仿真流程（不会再次询问）。")

                # 如果选择的是分区文件（如 s27_a / s27_b），尝试从父电路生成缺失的文件（放到 output 目录）
                base = os.path.splitext(selected_circuit)[0]
                out_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
                parent_base = None
                if base.endswith('_a') or base.endswith('_b'):
                    parent_base = base.rsplit('_', 1)[0]
                    parent_info = os.path.join(out_dir, f"{parent_base}_circuit_info.json")
                    parent_fault = os.path.join(out_dir, f"{parent_base}_fault.json")
                    parent_golden = os.path.join(out_dir, f"{parent_base}_golden.json")

                    # 生成缺失的 circuit_info / fault / golden
                    try:
                        if not os.path.exists(os.path.join(out_dir, f"{base}_circuit_info.json")) and os.path.exists(parent_info):
                            import copy
                            with open(parent_info, 'r', encoding='utf-8') as pf:
                                parent_js = json.load(pf)
                            # 分割 injection_reg（若存在）为两部分，保证总数一致
                            inj_regs = parent_js.get('injection_reg', [])
                            half = (len(inj_regs) + 1) // 2
                            if base.endswith('_a'):
                                subset = inj_regs[:half]
                            else:
                                subset = inj_regs[half:]
                            child_js = copy.deepcopy(parent_js)
                            child_js['injection_reg'] = subset
                            with open(os.path.join(out_dir, f"{base}_circuit_info.json"), 'w', encoding='utf-8') as cf:
                                json.dump(child_js, cf, indent=4)

                        if not os.path.exists(os.path.join(out_dir, f"{base}_fault.json")) and os.path.exists(parent_fault):
                            with open(parent_fault, 'r', encoding='utf-8') as pf:
                                parent_fault_js = json.load(pf)
                            keys = sorted(list(parent_fault_js.keys()))
                            half = (len(keys) + 1) // 2
                            if base.endswith('_a'):
                                chosen = keys[:half]
                            else:
                                chosen = keys[half:]
                            child_fault = {k: parent_fault_js[k] for k in chosen}
                            with open(os.path.join(out_dir, f"{base}_fault.json"), 'w', encoding='utf-8') as cf:
                                json.dump(child_fault, cf, indent=4)

                        if not os.path.exists(os.path.join(out_dir, f"{base}_golden.json")) and os.path.exists(parent_golden):
                            # 将父 golden 简单复制为子 golden（作为回退）
                            with open(parent_golden, 'r', encoding='utf-8') as pg:
                                parent_golden_js = json.load(pg)
                            with open(os.path.join(out_dir, f"{base}_golden.json"), 'w', encoding='utf-8') as cg:
                                json.dump(parent_golden_js, cg, indent=4)
                    except Exception as e:
                        print(f"生成 per-partition 文件时出错: {e}")
                        pass

                # 继续仿真（不再询问）

            # 检查写入的源文件是否存在
            missing_src = []
            for p in files_to_write:
                # 去掉开头的 ./
                p_rel = p[2:] if p.startswith('./') else p
                src_path = os.path.join(os.path.dirname(__file__), '..', p_rel)
                if not os.path.exists(src_path):
                    missing_src.append(p)
            if missing_src:
                print("警告：以下仿真需要的源文件不存在：")
                for mf in missing_src:
                    print(f"  - {mf}")
                print("将继续仿真（可能会导致编译失败），并尝试在 output/ 中生成缺失的 partition testbench（若适用）。")
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
            # 仿真完成后退出整个交互主程序
            return


if __name__ == "__main__":
    main()
