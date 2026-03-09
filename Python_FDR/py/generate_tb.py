import re
import os
import sys

def generate_tb(verilog_path):
    if not os.path.exists(verilog_path):
        print(f"Error: {verilog_path} not found.")
        return

    with open(verilog_path, 'r') as f:
        content = f.read()

    # 简单正则匹配模块名和端口
    module_match = re.search(r'module\s+(\w+)', content)
    if not module_match:
        print("Could not find module name.")
        return
    
    module_name = module_match.group(1)
    
    # 提取输入输出端口
    inputs = re.findall(r'input\s+([^;]+);', content)
    outputs = re.findall(r'output\s+([^;]+);', content)
    
    # 清理端口列表（处理逗号分隔或换行）
    input_ports = []
    for i in inputs:
        input_ports.extend([p.strip() for p in i.split(',')])
    
    output_ports = []
    for o in outputs:
        output_ports.extend([p.strip() for p in o.split(',')])

    # 尝试识别时钟和复位键
    clk_port = ""
    rst_port = ""
    for p in input_ports:
        lp = p.lower()
        if 'clk' in lp or 'clock' in lp:
            clk_port = p
        elif 'reset' in lp or 'rst' in lp:
            rst_port = p
    
    # 如果没找到，默认取第一个
    if not clk_port: clk_port = input_ports[0]
    if not rst_port and len(input_ports) > 1: rst_port = input_ports[1]

    tb_name = f"{module_name}_tb"
    tb_content = f"""`timescale 1ns/1ps

module {tb_name};
    // Inputs
"""
    for p in input_ports:
        tb_content += f"    reg {p};\n"
    
    tb_content += "\n    // Outputs\n"
    for p in output_ports:
        tb_content += f"    wire {p};\n"

    tb_content += f"\n    // Instantiate the Unit Under Test (UUT)\n"
    tb_content += f"    {module_name} uut (\n"
    
    mappings = []
    for p in input_ports + output_ports:
        mappings.append(f"        .{p}({p})")
    tb_content += ",\n".join(mappings)
    tb_content += "\n    );\n\n"

    # 时钟逻辑
    tb_content += f"    initial begin\n        {clk_port} = 0;\n        forever #5 {clk_port} = ~{clk_port};\n    end\n\n"

    # 测试激励逻辑
    tb_content += f"    initial begin\n        // Initialize Inputs\n"
    for p in input_ports:
        tb_content += f"        {p} = 0;\n"
    
    if rst_port:
        tb_content += f"\n        // Reset\n        {rst_port} = 1;\n        #20 {rst_port} = 0;\n"
    
    tb_content += f"""
        // Basic Random Stimulus
        repeat (100) begin
            #10;
"""
    for p in input_ports:
        if p != clk_port and p != rst_port:
            tb_content += f"            {p} = $random;\n"
    
    tb_content += """        end
        
        #100 $finish;
    end

endmodule
"""
    
    output_path = os.path.join(os.path.dirname(verilog_path), f"{module_name}_tb.v")
    with open(output_path, 'w') as f:
        f.write(tb_content)
    
    print(f"[SUCCESS] Testbench generated: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_tb.py <verilog_file>")
    else:
        generate_tb(sys.argv[1])
