"""
从GraphML分割结果生成Verilog文件的模块
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ElementTree
import typing


class GToV:
    """
    从GraphML分割结果生成Verilog文件
    """

    def __init__(self, graphml_file: str):
        self.graphml_file = graphml_file
        self.data = {}
        self.circuit_name = ""
        self.original_inputs = set()
        self.original_outputs = set()
        
        # 信号映射
        self.driven_by = {} # signal -> 'PI' or instance_id
        self.used_by = {}   # signal -> set of instance_ids
        self.instance_partition = {} # instance_id -> 'a' or 'b'
        self.instance_defs = {} # instance_id -> [type, name, connections_str]

    def _parse_connections(self, conn_str: str, inst_type: str) -> typing.List[tuple]:
        """
        解析连接字符串，返回 [(port_name, signal_name), ...]
        支持命名映射 .port(sig) 和位置映射 (sig1, sig2)
        """
        # 1. 尝试命名映射 .port(signal)
        connections = re.findall(r'\.(\w+)\s*\(([\w_]+)\)', conn_str)
        if connections:
            return connections
            
        # 2. 尝试位置映射 signal1, signal2
        # 移除括号和空白
        clean_str = conn_str.strip()
        if clean_str.startswith('(') and clean_str.endswith(')'):
            clean_str = clean_str[1:-1]
        
        signals = [s.strip() for s in clean_str.split(',') if s.strip()]
        if not signals:
            return []
            
        results = []
        
        # 2.1 检查是否为标准原语 (Verilog标准规定第一个端口为输出)
        # 注意：buf/not可能有多个输出，但这里简化处理，假设单输出
        primitives = ['and', 'nand', 'or', 'nor', 'xor', 'xnor', 'not', 'buf']
        if inst_type in primitives:
            # 第一个是输出，其余是输入
            results.append(('OUT', signals[0]))
            for i, sig in enumerate(signals[1:]):
                results.append((f'IN{i+1}', sig))
            return results
            
        # 2.2 检查是否在模块定义中 (从JSON获取端口顺序)
        if inst_type in self.data.get('modules', {}):
            mod_def = self.data['modules'][inst_type]
            ports = mod_def.get('ports', [])
            for i, sig in enumerate(signals):
                # 如果信号数多于定义端口数，生成虚拟端口名
                port_name = ports[i] if i < len(ports) else f'P{i}'
                results.append((port_name, sig))
            return results
            
        # 2.3 默认情况 (无法确定端口名)
        for i, sig in enumerate(signals):
            results.append((f'P{i}', sig))
            
        return results

    def _is_output_port(self, port_name: str, inst_type: str) -> bool:
        """判断端口是否为输出端口"""
        # 原语逻辑
        if port_name == 'OUT': return True
        if port_name.startswith('IN'): return False
        
        # 常见命名启发式规则
        if port_name in ['Y', 'Q', 'QN', 'Z', 'ZN', 'CO']: return True
        
        # 模块定义查找
        if inst_type in self.data.get('modules', {}):
            mod_def = self.data['modules'][inst_type]
            if port_name in mod_def.get('outputs', []):
                return True
            if port_name in mod_def.get('inputs', []):
                return False
                
        # DFF 特例 (如果JSON中没有定义)
        if inst_type.lower().startswith('dff') and port_name in ['Q', 'QN']:
            return True
            
        return False

    def load_data(self) -> bool:
        """加载GraphML数据并构建信号映射"""
        if not os.path.exists(self.graphml_file):
            print(f"错误: 找不到文件 {self.graphml_file}")
            return False
        
        try:
            tree = ElementTree.parse(self.graphml_file)
            root = tree.getroot()
            
            # 命名空间处理
            ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}
            
            # 获取电路信息
            graph_node = root.find('g:graph', ns)
            if graph_node is None:
                graph_node = root.find('graph')
                ns = {}
                
            d3_node = graph_node.find("g:data[@key='d3']", ns) if ns else graph_node.find("data[@key='d3']")
            if d3_node is None:
                print("错误: 找不到电路信息数据")
                return False
                
            circuit_info_str = d3_node.text
            self.data = json.loads(circuit_info_str)
            
            # 智能选择主模块
            # 1. 尝试使用文件名作为电路名
            filename_base = os.path.splitext(os.path.basename(self.graphml_file))[0]
            # 移除 _cut 后缀
            if filename_base.endswith('_cut'):
                filename_base = filename_base[:-4]
            
            if filename_base in self.data['modules']:
                self.circuit_name = filename_base
            else:
                # 2. 如果找不到同名模块，选择实例数最多的模块
                max_instances = -1
                best_module = ""
                for mod_name, mod_data in self.data['modules'].items():
                    inst_count = len(mod_data.get('instances', []))
                    if inst_count > max_instances:
                        max_instances = inst_count
                        best_module = mod_name
                self.circuit_name = best_module
            
            print(f"已选择主模块: {self.circuit_name}")
            module_data = self.data['modules'][self.circuit_name]
            
            self.original_inputs = set(module_data.get('inputs', []))
            self.original_outputs = set(module_data.get('outputs', []))
            
            # 1. 构建 instance_partition 映射
            nodes = graph_node.findall('g:node', ns) if ns else graph_node.findall('node')
            for node in nodes:
                node_id = node.get('id')
                partition_attr = node.find("g:data[@key='d0']", ns) if ns else node.find("data[@key='d0']")
                if partition_attr is not None:
                    self.instance_partition[node_id] = partition_attr.text

            # 2. 构建 instance_defs 和 信号映射
            # 预处理 PIs
            for pi in self.original_inputs:
                self.driven_by[pi] = 'PI'
                if pi not in self.used_by:
                    self.used_by[pi] = set()

            # 处理实例
            for inst in module_data['instances']:
                # inst: [type, name, connections_str]
                inst_type = inst[0]
                inst_name = inst[1]
                conn_str = inst[2]
                
                # 确保 instance_defs 使用与 instance_partition 相同的键
                # 在 FM_part.py 中，节点 ID 是 instance_name
                self.instance_defs[inst_name] = inst
                
                # 使用通用解析方法
                connections = self._parse_connections(conn_str, inst_type)
                
                for port, signal in connections:
                    if signal not in self.used_by:
                        self.used_by[signal] = set()
                    
                    # 使用通用方向判断方法
                    is_output = self._is_output_port(port, inst_type)
                    
                    if is_output:
                        self.driven_by[signal] = inst_name
                    else:
                        self.used_by[signal].add(inst_name)
            
            # 验证所有分区中的实例是否都在 instance_defs 中
            missing_instances = []
            for inst_id in self.instance_partition:
                if inst_id not in self.instance_defs:
                    missing_instances.append(inst_id)
            
            if missing_instances:
                print(f"警告: 以下实例在分区信息中存在但在模块定义中找不到: {missing_instances}")
                print(f"已加载的实例定义数量: {len(self.instance_defs)}")
                if len(self.instance_defs) > 0:
                    print(f"已加载的实例定义示例 (前5个): {list(self.instance_defs.keys())[:5]}")
                else:
                    print("错误: 没有加载到任何实例定义！请检查 JSON 数据中的 'instances' 字段。")
                    # 打印部分 JSON 数据以供调试
                    print(f"JSON 数据键: {self.data.keys()}")
                    if 'modules' in self.data:
                        print(f"模块列表: {list(self.data['modules'].keys())}")
                        if self.circuit_name in self.data['modules']:
                            mod_data = self.data['modules'][self.circuit_name]
                            print(f"模块 '{self.circuit_name}' 的键: {mod_data.keys()}")
                            if 'instances' in mod_data:
                                print(f"实例列表长度: {len(mod_data['instances'])}")
                                if len(mod_data['instances']) > 0:
                                    print(f"第一个实例数据: {mod_data['instances'][0]}")
                
                # 尝试修复：可能是因为 GraphML 中的 ID 与 JSON 中的 ID 不匹配
                pass

            return True
        except Exception as e:
            print(f"解析GraphML文件时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _generate_partition_module(self, partition_name: str) -> str:
        """生成单个分区的Verilog模块内容"""
        
        # 收集该分区的实例
        local_instances = [inst_id for inst_id, p in self.instance_partition.items() if p == partition_name]
        local_instances_set = set(local_instances)
        
        # 收集该分区涉及的所有信号
        involved_signals = set()
        for inst_id in local_instances:
            inst_def = self.instance_defs[inst_id]
            inst_type = inst_def[0]
            conn_str = inst_def[2]
            
            # 使用通用解析方法
            connections = self._parse_connections(conn_str, inst_type)
            for _, sig in connections:
                involved_signals.add(sig)
        
        assign_statements = []
        wire_declarations = set()
        module_ports = []
        
        # 用于收集单行声明的列表
        input_decls_list = []
        output_decls_list = []
        
        # 遍历所有涉及的信号，决定如何处理
        # 为了保持端口顺序稳定，排序
        sorted_signals = sorted(list(involved_signals))
        
        processed_signals = set()

        for sig in sorted_signals:
            if sig in processed_signals: continue
            processed_signals.add(sig)
            
            source = self.driven_by.get(sig)
            
            # 判断 Source 类型
            is_source_pi = (source == 'PI')
            is_source_local = (source in local_instances_set)
            is_source_remote = (source is not None and source not in local_instances_set and source != 'PI')
            
            # 判断 Destination 类型
            # 是否去往 Remote?
            goes_remote = False
            if sig in self.used_by:
                for user_inst in self.used_by[sig]:
                    if user_inst not in local_instances_set:
                        goes_remote = True
                        break
            
            is_po = (sig in self.original_outputs)
            
            # --- 生成逻辑 ---
            
            # 1. 输入处理
            if is_source_pi:
                # 原始输入，直接作为 input
                if sig not in module_ports:
                    module_ports.append(sig)
                    input_decls_list.append(sig)
                    # input 默认为 wire，不需要额外声明 wire，除非被 assign 赋值（这里没有）
            
            elif is_source_remote:
                # 来自另一个分区 -> input cut_sig
                cut_port_name = f"cut_{sig}"
                if cut_port_name not in module_ports:
                    module_ports.append(cut_port_name)
                    input_decls_list.append(cut_port_name)
                
                # 内部使用原始名称，需要 assign
                assign_statements.append(f"  assign {sig} = {cut_port_name};")
                wire_declarations.add(sig)
            
            # 2. 输出处理 (仅当源是本地时)
            if is_source_local:
                # 必须声明为 wire (因为它是实例的输出)
                wire_declarations.add(sig)
                
                if is_po:
                    # 原始输出 -> output sig
                    if sig not in module_ports:
                        module_ports.append(sig)
                        output_decls_list.append(sig)
                
                if goes_remote:
                    # 去往另一个分区 -> output cut_sig
                    cut_port_name = f"cut_{sig}"
                    if cut_port_name not in module_ports:
                        module_ports.append(cut_port_name)
                        output_decls_list.append(cut_port_name)
                    
                    assign_statements.append(f"  assign {cut_port_name} = {sig};")

        # 生成代码
        lines = [
            f"// Partition {partition_name} from {self.circuit_name}",
            f"// Contains {len(local_instances)} instances",
            "",
            f"module {self.circuit_name}_{partition_name} ({', '.join(module_ports)});",
        ]
        
        # 端口声明 (修正规则7：单行声明)
        if input_decls_list:
            lines.append(f"  input {', '.join(input_decls_list)};")
        if output_decls_list:
            lines.append(f"  output {', '.join(output_decls_list)};")
            
        lines.append("")
        
        # Wire 声明
        # 过滤掉已经是 input 端口的信号 (input 也是 wire)
        # 注意：如果 sig 是 input，它在 port_declarations 里已经声明了
        # 如果 sig 是 output，它在 port_declarations 里也声明了 (output 默认 wire)
        # 但是，如果 output sig 同时也是 wire sig，Verilog 允许 "output x; wire x;"
        # 为了安全和清晰，我们只声明那些没有出现在 input/output 列表中的，或者显式声明所有非 input
        
        # 简单起见，声明所有在 wire_declarations 中的信号
        # 但要排除 input 端口，因为 input 不能被重声明为 wire (虽然 input 也是 wire)
        # output 可以被重声明为 wire
        
        input_ports = set(input_decls_list)
        
        final_wires = [w for w in wire_declarations if w not in input_ports]
        # 还要排除 output 端口吗？通常 output x; wire x; 是合法的。
        # 让我们保留它，或者只声明那些不是 output 的。
        # 如果我们有 output cut_sig; assign cut_sig = sig; 那么 sig 需要是 wire。
        # 如果 sig 本身也是 output sig; 那么 sig 已经是 wire。
        # 所以，如果 sig 是 output 端口，我们不需要再声明 wire sig。
        
        output_ports = set(output_decls_list)
                    
        final_wires = [w for w in final_wires if w not in output_ports]
        
        if final_wires:
            lines.append(f"  wire {', '.join(sorted(list(set(final_wires))))};")
        lines.append("")
        
        if assign_statements:
            lines.extend(assign_statements)
            lines.append("")
            
        lines.append(f"// Instances assigned to partition {partition_name}")
        for inst_id in local_instances:
            inst = self.instance_defs[inst_id]
            # 格式化连接字符串，确保包含在括号内符合IEEE标准
            raw_conns = inst[2].strip()
            if raw_conns.endswith(';'):
                raw_conns = raw_conns[:-1].strip()
            
            if not (raw_conns.startswith('(') and raw_conns.endswith(')')):
                formatted_conns = f"({raw_conns})"
            else:
                formatted_conns = raw_conns
                
            lines.append(f"  {inst[0]} {inst[1]} {formatted_conns};")
            
        lines.append("")
        lines.append(f"endmodule  // {self.circuit_name}_{partition_name}")
        
        return "\n".join(lines)

    def generate_verilog(self) -> bool:
        """生成所有分区的Verilog文件"""
        if not self.load_data():
            return False
            
        output_dir = os.path.dirname(self.graphml_file)
        
        # 生成 A 区
        content_a = self._generate_partition_module('a')
        file_a = os.path.join(output_dir, f"{self.circuit_name}_a.v")
        with open(file_a, 'w') as f:
            f.write(content_a)
        print(f"已生成: {file_a}")
        
        # 生成 B 区
        content_b = self._generate_partition_module('b')
        file_b = os.path.join(output_dir, f"{self.circuit_name}_b.v")
        with open(file_b, 'w') as f:
            f.write(content_b)
        print(f"已生成: {file_b}")
        
        return True

def generate_verilog(circuit_name):
    """对外接口函数"""
    # 假设文件在 output 目录下
    # 尝试查找文件
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 更新为读取 _cut.graphml 文件
    graphml_path = os.path.join(base_dir, 'output', f'{circuit_name}_cut.graphml')
    
    if not os.path.exists(graphml_path):
        # 尝试旧命名格式作为后备
        old_path = os.path.join(base_dir, 'output', f'{circuit_name}.graphml')
        if os.path.exists(old_path):
            graphml_path = old_path
        else:
            # 尝试当前目录
            graphml_path = f'{circuit_name}_cut.graphml'
    
    converter = GToV(graphml_path)
    return converter.generate_verilog()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_verilog(sys.argv[1])
    else:
        print("用法: python G_to_v.py <circuit_name>")
