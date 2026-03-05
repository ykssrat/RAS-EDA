
import json
import os
import sys

# 将当前目录添加到路径以便导入项目模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from FM_part import VerilogParser, CircuitPartitioner

def generate_default_files(circuit_name):
    """
    为指定电路生成默认的 circuit_info, golden 和 fault JSON 文件。
    这些文件允许在不分割的情况下直接进行故障仿真。
    """
    verilog_filename = circuit_name if circuit_name.endswith('.v') else f"{circuit_name}.v"
    circuit_dir = os.path.join(os.path.dirname(__file__), '..', 'circuit')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    verilog_file = os.path.join(circuit_dir, verilog_filename)

    if not os.path.exists(verilog_file):
        print(f"错误: 找不到 Verilog 文件 {verilog_file}")
        return False

    print(f"解析电路 {verilog_filename} 以生成默认配置文件...")
    
    parser = VerilogParser(verilog_file)
    modules = parser.parse()
    if not modules:
        print("错误: 无法解析 Verilog 文件。")
        return False

    # 获取主模块（假设第一个模块是主模块）
    main_module_name = list(modules.keys())[0]
    module_data = modules[main_module_name]

    # 提取输入、输出和寄存器（DFF）
    inputs = module_data.get('inputs', [])
    outputs = module_data.get('outputs', [])
    
    # 查找 DFF 类型的实例作为状态寄存器
    state_regs = []
    for inst_type, inst_name, _ in module_data.get('instances', []):
        if 'DFF' in inst_type.upper():
            state_regs.append(inst_name)

    # 构造 circuit_info.json 内容
    circuit_info = {
        "injection_reg": state_regs,
        "state_reg": state_regs,
        "out_port": outputs,
        "modules": modules
    }

    # 保存 circuit_info.json
    info_path = os.path.join(output_dir, f"{circuit_name}_circuit_info.json")
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(circuit_info, f, indent=4)
    print(f"已生成: {info_path}")

    # 构造默认的 golden.json (空或者占位符，由仿真器填充)
    # simulator.py 的 get_golden 会读取这个文件，如果不存在会报错
    # 实际上，golden 应该是由仿真第一次运行产生的，但 simulator.py 期望它已经存在。
    # 这里我们生成一个空的占位对象。
    golden_path = os.path.join(output_dir, f"{circuit_name}_golden.json")
    if not os.path.exists(golden_path):
        with open(golden_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
        print(f"已生成占位文件: {golden_path}")

    # 构造默认的 fault.json (占位符)
    fault_path = os.path.join(output_dir, f"{circuit_name}_fault.json")
    if not os.path.exists(fault_path):
        with open(fault_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
        print(f"已生成占位文件: {fault_path}")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python gen_default_json.py <circuit_name>")
    else:
        generate_default_files(sys.argv[1])
