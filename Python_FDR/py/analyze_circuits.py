#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verilog电路分析工具
分析电路规模、寄存器数量、input/output数目
"""

import re
import os
import json
import pandas as pd


class VerilogAnalyzer:
    """Verilog文件分析器"""
    
    def __init__(self, verilog_content):
        self.content = verilog_content
        self.lines = verilog_content.split('\n')
        
    def get_module_name(self):
        """获取模块名称"""
        for line in self.lines:
            match = re.match(r'\s*module\s+(\w+)', line)
            if match:
                return match.group(1)
        return 'unknown'
    
    def count_inputs(self):
        """统计input端口数量"""
        count = 0
        in_port_decl = False
        
        for line in self.lines:
            # 移除注释
            line = self._remove_comments(line)
            
            # 查找input声明
            if re.search(r'\binput\b', line):
                # 处理多个端口在一行的情况
                # 统计逗号数量 + 1 = 端口数
                input_part = re.findall(r'input\s+(?:\w+\s+)*\[?[^\]]*\]?\s*([^;]*)', line)
                if input_part:
                    # 计算这行中的端口数
                    ports_in_line = input_part[0].count(',') + 1 if input_part[0].strip() else 0
                    count += ports_in_line if ports_in_line > 0 else 1
        
        return count
    
    def count_outputs(self):
        """统计output端口数量"""
        count = 0
        
        for line in self.lines:
            # 移除注释
            line = self._remove_comments(line)
            
            # 查找output声明
            if re.search(r'\boutput\b', line):
                output_part = re.findall(r'output\s+(?:\w+\s+)*\[?[^\]]*\]?\s*([^;]*)', line)
                if output_part:
                    ports_in_line = output_part[0].count(',') + 1 if output_part[0].strip() else 0
                    count += ports_in_line if ports_in_line > 0 else 1
        
        return count
    
    def count_registers(self):
        """统计寄存器(reg)数量"""
        count = 0
        
        for line in self.lines:
            # 移除注释
            line = self._remove_comments(line)
            
            # 查找reg声明
            if re.search(r'\breg\b', line):
                # 统计此行的reg声明数
                reg_part = re.findall(r'reg\s+(?:\[?[^\]]*\]?\s+)*([^;]*)', line)
                if reg_part:
                    # 计算逗号数+1
                    regs_in_line = reg_part[0].count(',') + 1 if reg_part[0].strip() else 0
                    count += regs_in_line if regs_in_line > 0 else 1
        
        return count
    
    def _remove_comments(self, line):
        """移除Verilog注释"""
        # 移除//注释
        line = re.sub(r'//.*', '', line)
        return line
    
    def analyze(self):
        """执行完整分析"""
        return {
            'module_name': self.get_module_name(),
            'inputs': self.count_inputs(),
            'outputs': self.count_outputs(),
            'registers': self.count_registers()
        }


def analyze_circuit_files(circuit_dir, config_file=None):
    """
    分析电路目录下的所有Verilog文件
    
    Args:
        circuit_dir: 电路文件目录
        config_file: 配置文件路径
    
    Returns:
        DataFrame: 分析结果
    """
    
    if not os.path.exists(circuit_dir):
        raise FileNotFoundError(f"电路目录不存在: {circuit_dir}")
    
    # 获取所有.v文件
    verilog_files = sorted([f for f in os.listdir(circuit_dir) if f.endswith('.v')])
    
    # 过滤掉测试文件和标准库
    exclude_patterns = ['_tb.v', 'tb.v', 'test.v', 'stdcells.v']
    verilog_files = [f for f in verilog_files if not any(pattern in f for pattern in exclude_patterns)]
    
    results = []
    
    for verilog_file in verilog_files:
        file_path = os.path.join(circuit_dir, verilog_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            analyzer = VerilogAnalyzer(content)
            analysis = analyzer.analyze()
            analysis['file_name'] = verilog_file
            results.append(analysis)
            
            print(f"✓ {verilog_file}: 输入={analysis['inputs']}, 输出={analysis['outputs']}, 寄存器={analysis['registers']}")
        
        except Exception as e:
            print(f"✗ {verilog_file}: 分析失败 - {str(e)}")
            results.append({
                'file_name': verilog_file,
                'module_name': 'ERROR',
                'inputs': 0,
                'outputs': 0,
                'registers': 0
            })
    
    # 创建DataFrame
    df = pd.DataFrame(results)
    df = df[['file_name', 'module_name', 'inputs', 'outputs', 'registers']]
    
    return df


def load_config(config_file):
    """加载配置文件"""
    if not os.path.exists(config_file):
        return {}
    
    with open(config_file, 'r') as f:
        return json.load(f)


def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # 配置文件路径
    config_file = os.path.join(project_root, 'config', 'config.json')
    config = load_config(config_file)
    
    # 电路文件目录
    circuit_dir = os.path.join(project_root, 'circuit')
    
    # 输出目录
    output_dir = os.path.join(project_root, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # 分析电路
    print("开始分析电路文件...")
    df = analyze_circuit_files(circuit_dir, config_file)
    
    # 保存为Excel
    excel_file = os.path.join(output_dir, 'circuit_analysis.xlsx')
    df.to_excel(excel_file, index=False, sheet_name='电路分析')
    
    print(f"\n分析完成！结果已保存到: {excel_file}")
    print(f"\n总计: {len(df)} 个电路文件")
    print("\n统计摘要:")
    print(df.describe())
    
    return df


if __name__ == '__main__':
    main()
