"""
使用FM算法对大规模Verilog电路进行分割的模块 - 根据规则完全重构版本
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ElementTree
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any

import numpy as np


class VerilogParser:
    """解析Verilog文件，提取模块和连接信息。"""

    def __init__(self, verilog_file: str):
        # 初始化Verilog文件路径
        self.verilog_file = verilog_file
        # 使用字典存储模块信息，键为模块名，值为模块详细信息
        self.modules: Dict[str, Dict] = {}  # 存储模块信息
        # 使用集合存储所有wire信号名
        self.wires: Set[str] = set()  # 存储所有wire
        # 存储输入输出端口
        self.inputs: Set[str] = set()
        self.outputs: Set[str] = set()
        # 使用defaultdict存储连接关系，值为集合类型，确保每个连接只记录一次
        self.connections: Dict[str, Set[str]] = defaultdict(set)  # 存储连接关系

    def parse(self) -> Dict[str, Dict]:
        """解析Verilog，返回模块信息字典。"""
        try:
            # 尝试用UTF-8编码打开文件
            with open(self.verilog_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            with open(self.verilog_file, 'r', encoding='latin-1') as f:
                content = f.read()

        # 提取模块定义
        module_pattern = r'module\s+(\w+)\s*\((.*?)\)\s*;(.*?)(?=endmodule|$)'
        modules = re.findall(module_pattern, content, re.DOTALL)

        for module_name, ports_str, module_body in modules:
            # 提取端口列表
            ports = [p.strip() for p in ports_str.split(',') if p.strip()]

            # 提取输入端口
            input_pattern = r'input\s+([^;]+);'
            for input_match in re.finditer(input_pattern, module_body):
                input_str = input_match.group(1)
                self.inputs.update([i.strip() for i in input_str.split(',') if i.strip()])

            # 提取输出端口
            output_pattern = r'output\s+([^;]+);'
            for output_match in re.finditer(output_pattern, module_body):
                output_str = output_match.group(1)
                self.outputs.update([o.strip() for o in output_str.split(',') if o.strip()])

            # 提取wire声明
            wire_pattern = r'wire\s+([^;]+);'
            wires = []
            for wire_match in re.finditer(wire_pattern, module_body):
                wire_str = wire_match.group(1)
                wires.extend([w.strip() for w in wire_str.split(',') if w.strip()])

            # 提取实例
            instance_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\);'
            instances = []
            for instance_match in re.finditer(instance_pattern, module_body):
                instance_type = instance_match.group(1)
                instance_name = instance_match.group(2)
                connections = instance_match.group(3)
                instances.append((instance_type, instance_name, connections))

            # 存储模块信息
            self.modules[module_name] = {
                'ports': ports,
                'inputs': list(self.inputs),
                'outputs': list(self.outputs),
                'wires': wires,
                'instances': instances
            }

        return self.modules


class Graph:
    """电路图。"""

    def __init__(self):
        self.nodes: Dict[str, Dict] = {}  # 存储节点信息
        self.edges: Dict[Tuple[str, str], int] = {}  # 存储边及其权重
        self.edge_weights: Dict[Tuple[str, str], int] = {}  # 存储边权重
        self.node_neighbors_cache: Dict[str, Set[str]] = defaultdict(set)  # 邻居缓存

    def add_node(self, node_id: str, node_type: str = "default", **kwargs) -> None:
        """添加节点。"""
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                'type': node_type,
                **kwargs
            }
            # 初始化邻居缓存
            self.node_neighbors_cache[node_id] = set()

    def add_edge(self, node1: str, node2: str, weight: int = 1) -> None:
        """添加无向边。"""
        if node1 in self.nodes and node2 in self.nodes:
            self.edges[(node1, node2)] = weight
            self.edges[(node2, node1)] = weight  # 无向图
            self.edge_weights[(node1, node2)] = weight
            self.edge_weights[(node2, node1)] = weight  # 无向图

            # 更新邻居缓存
            self.node_neighbors_cache[node1].add(node2)
            self.node_neighbors_cache[node2].add(node1)

    def get_neighbors(self, node_id: str) -> Set[str]:
        """获取节点邻居。"""
        if node_id in self.node_neighbors_cache:
            return self.node_neighbors_cache[node_id]
        return set()

    def get_detailed_partition_info(self, partition_a: Set[str], partition_b: Set[str]) -> Dict[str, Any]:
        """获取详细的分割信息。"""
        cutsize = 0
        # 计算割集大小
        for node in partition_a:
            for neighbor in self.get_neighbors(node):
                if neighbor in partition_b:
                    cutsize += self.edge_weights.get((node, neighbor), 1)

        return {
            'partition_a_count': len(partition_a),
            'partition_b_count': len(partition_b),
            'cutsize': cutsize,
            'partition_a_nodes': list(partition_a),
            'partition_b_nodes': list(partition_b)
        }


class FMPartitioner:
    """FM分割算法（规则化版本）。"""

    def __init__(self, graph: Graph, parser: VerilogParser, balance_factor: float = 0.5):
        self.graph = graph
        self.parser = parser  # 添加parser属性
        self.balance_factor = balance_factor  # 分割平衡因子
        self.locked: Set[str] = set()  # 锁定的节点
        self.partition_a: Set[str] = set()  # 分区A
        self.partition_b: Set[str] = set()  # 分区B
        self.buckets: Dict[str, Dict[int, Set[str]]] = {  # 桶排序结构
            'A': defaultdict(set),  # A分区的增益桶
            'B': defaultdict(set)   # B分区的增益桶
        }
        self.max_gain_a: int = 0  # A分区的最大增益
        self.max_gain_b: int = 0  # B分区的最大增益
        self.move_history: List[Tuple[str, str, int]] = []  # 移动历史记录

    def initialize_partitions(self) -> None:
        """
        初始化分割 - 根据规则重构版本

        规则：A区在分割之前包含原电路的所有input
        """
        nodes = list(self.graph.nodes.keys())
        total_nodes = len(nodes)

        # 对于小规模电路，使用更平衡的初始分割
        if total_nodes <= 20:
            # 对于小电路，确保分区大小更接近
            target_size_a = total_nodes // 2
            target_size_b = total_nodes - target_size_a
        else:
            # 对于大电路，使用平衡因子
            target_size_a = int(total_nodes * self.balance_factor)
            target_size_b = total_nodes - target_size_a

        # 获取模块信息，找到与输入端口直接连接的实例
        modules = self.parser.parse()
        module_info = {}
        for module_name, module_data in modules.items():
            module_info[module_name] = {
                'ports': module_data['ports'],
                'inputs': module_data.get('inputs', []),
                'outputs': module_data.get('outputs', []),
                'instances': module_data['instances']
            }

        # 获取原始端口信息
        first_module = list(module_info.values())[0]
        original_inputs = first_module['inputs']
        original_outputs = first_module['outputs']
        
        # 如果解析不到输入输出（兼容旧代码或特殊情况），使用s27默认值作为后备
        if not original_inputs and not original_outputs:
             original_ports = first_module['ports']
             original_inputs = [p for p in original_ports if p in ["CK", "G0", "G1", "G2", "G3"]]
             original_outputs = [p for p in original_ports if p in ["G17"]]

        # 找到与输入端口直接连接的实例
        input_connected_instances = set()
        output_connected_instances = set()

        for module_name, module_data in modules.items():
            for instance_type, instance_name, connections in module_data['instances']:
                conn_list = [c.strip() for c in connections.split(',') if c.strip()]
                for conn in conn_list:
                    # 提取信号名
                    if '.' in conn:  # 形如 .port(signal) 的连接
                        signal = conn.split('(')[1].split(')')[0].strip()
                        if signal in original_inputs:
                            input_connected_instances.add(instance_name)
                        elif signal in original_outputs:
                            output_connected_instances.add(instance_name)

        # 随机打乱节点顺序，确保随机性
        np.random.shuffle(nodes)

        # 初始分配节点到两个分区
        self.partition_a = set()
        self.partition_b = set()

        # 首先将与输入端口直接连接的实例分配到A区
        for instance in input_connected_instances:
            if instance in nodes:
                self.partition_a.add(instance)
                nodes.remove(instance)

        # 然后将与输出端口直接连接的实例分配到B区
        for instance in output_connected_instances:
            if instance in nodes:
                self.partition_b.add(instance)
                nodes.remove(instance)

        # 使用更智能的初始分配策略
        # 交替分配节点，确保初始平衡
        for i, node in enumerate(nodes):
            if i % 2 == 0 and len(self.partition_a) < target_size_a:
                self.partition_a.add(node)
            elif len(self.partition_b) < target_size_b:
                self.partition_b.add(node)
            elif len(self.partition_a) < target_size_a:
                self.partition_a.add(node)
            else:
                self.partition_b.add(node)

        # 确保每个分区至少有2个节点（避免极不均衡地分割）
        if len(self.partition_a) < 2:
            # 从B区移动一个节点到A区
            node_to_move = next(iter(self.partition_b))
            self.partition_b.remove(node_to_move)
            self.partition_a.add(node_to_move)
        elif len(self.partition_b) < 2:
            # 从A区移动一个节点到B区
            node_to_move = next(iter(self.partition_a))
            self.partition_a.remove(node_to_move)
            self.partition_b.add(node_to_move)

        # 确保分区大小平衡
        while len(self.partition_a) < target_size_a and len(self.partition_b) > target_size_b:
            # 从B区移动一个连接最少的节点到A区
            min_connections = float('inf')
            min_node = None
            for node in self.partition_b:
                # 获取节点的连接数，使用graph.get_neighbors获取连接信息
                connections = len(self.graph.get_neighbors(node))
                if connections < min_connections:
                    min_connections = connections
                    min_node = node

            if min_node:
                self.partition_b.remove(min_node)
                self.partition_a.add(min_node)
            else:
                # 如果找不到合适的节点，随机移动
                node = next(iter(self.partition_b))
                self.partition_b.remove(node)
                self.partition_a.add(node)

        while len(self.partition_b) < target_size_b and len(self.partition_a) > target_size_a:
            # 从A区移动一个连接最少的节点到B区
            min_connections = float('inf')
            min_node = None
            for node in self.partition_a:
                # 获取节点的连接数，使用graph.get_neighbors获取连接信息
                connections = len(self.graph.get_neighbors(node))
                if connections < min_connections:
                    min_connections = connections
                    min_node = node

            if min_node:
                self.partition_a.remove(min_node)
                self.partition_b.add(min_node)
            else:
                # 如果找不到合适的节点，随机移动
                node = next(iter(self.partition_a))
                self.partition_a.remove(node)
                self.partition_b.add(node)

        # 初始化桶结构
        self._initialize_buckets()

    def _compute_gain(self, node: str, from_partition: Set[str], to_partition: Set[str]) -> int:
        """
        计算节点移动的增益
        """
        gain = 0
        # 对于连接到相同分区的邻居，增加增益
        for neighbor in self.graph.get_neighbors(node):
            if neighbor in from_partition:
                gain += self.graph.edge_weights.get((node, neighbor), 1)
            elif neighbor in to_partition:
                gain -= self.graph.edge_weights.get((node, neighbor), 1)
        return gain

    def _initialize_buckets(self) -> None:
        """
        初始化桶数据结构
        """
        # 清空桶
        self.buckets = {
            'A': defaultdict(set),
            'B': defaultdict(set)
        }

        # 重置最大增益
        self.max_gain_a = float('-inf')
        self.max_gain_b = float('-inf')

        # 计算每个节点的增益并放入相应桶中
        for node in self.partition_a:
            gain = self._compute_gain(node, self.partition_a, self.partition_b)
            self.buckets['A'][gain].add(node)
            if gain > self.max_gain_a:
                self.max_gain_a = gain

        for node in self.partition_b:
            gain = self._compute_gain(node, self.partition_b, self.partition_a)
            self.buckets['B'][gain].add(node)
            if gain > self.max_gain_b:
                self.max_gain_b = gain

    def _calculate_cutsize(self) -> int:
        """
        计算当前割集大小
        """
        cutsize = 0
        for node in self.partition_a:
            for neighbor in self.graph.get_neighbors(node):
                if neighbor in self.partition_b:
                    cutsize += self.graph.edge_weights.get((node, neighbor), 1)
        return cutsize

    def _select_best_move(self) -> Optional[Tuple[str, str, int]]:
        """选择当前最大奖励的移动。"""
        candidates: list[Tuple[str, str, int]] = []
        if self.buckets['A']:
            node = next(iter(self.buckets['A'][self.max_gain_a]))
            candidates.append(('A_to_B', node, self.max_gain_a))
        if self.buckets['B']:
            node = next(iter(self.buckets['B'][self.max_gain_b]))
            candidates.append(('B_to_A', node, self.max_gain_b))
        if not candidates:
            return None
        return max(candidates, key=lambda item: item[2])

    def _move_node(self, move_info: Tuple[str, str, int]) -> None:
        """
        移动节点
        """
        direction, node, gain = move_info

        if direction == 'A_to_B':
            if node in self.partition_a:  # 确保节点在正确的分区中
                self.partition_a.remove(node)
                self.partition_b.add(node)

                # 更新桶结构
                if node in self.buckets['A'][gain]:
                    self.buckets['A'][gain].remove(node)
                    if not self.buckets['A'][gain]:
                        del self.buckets['A'][gain]
                        if gain == self.max_gain_a and self.buckets['A']:
                            self.max_gain_a = max(self.buckets['A'].keys())

                # 只更新直接受影响的邻居节点
                for neighbor in self.graph.get_neighbors(node):
                    if neighbor in self.partition_a and neighbor not in self.locked:
                        # 更新邻居的增益
                        # 获取旧增益
                        old_gain = 0
                        for n in self.graph.get_neighbors(neighbor):
                            if n in self.partition_a:
                                old_gain += self.graph.edge_weights.get((neighbor, n), 1)
                            elif n in self.partition_b:
                                old_gain -= self.graph.edge_weights.get((neighbor, n), 1)

                        # 计算新增益
                        new_gain = old_gain + self.graph.edge_weights.get((neighbor, node), 1)

                        # 更新桶
                        if old_gain in self.buckets['A']:
                            self.buckets['A'][old_gain].discard(neighbor)
                            if not self.buckets['A'][old_gain]:
                                del self.buckets['A'][old_gain]
                                if old_gain == self.max_gain_a and self.buckets['A']:
                                    self.max_gain_a = max(self.buckets['A'].keys())

                        self.buckets['A'][new_gain].add(neighbor)
                        if new_gain > self.max_gain_a:
                            self.max_gain_a = new_gain

        elif direction == 'B_to_A':
            if node in self.partition_b:  # 确保节点在正确的分区中
                self.partition_b.remove(node)
                self.partition_a.add(node)

                # 更新桶结构
                if node in self.buckets['B'][gain]:
                    self.buckets['B'][gain].remove(node)
                    if not self.buckets['B'][gain]:
                        del self.buckets['B'][gain]
                        if gain == self.max_gain_b and self.buckets['B']:
                            self.max_gain_b = max(self.buckets['B'].keys())

                # 只更新直接受影响的邻居节点
                for neighbor in self.graph.get_neighbors(node):
                    if neighbor in self.partition_b and neighbor not in self.locked:
                        # 更新邻居的增益
                        # 获取旧增益
                        old_gain = 0
                        for n in self.graph.get_neighbors(neighbor):
                            if n in self.partition_b:
                                old_gain += self.graph.edge_weights.get((neighbor, n), 1)
                            elif n in self.partition_a:
                                old_gain -= self.graph.edge_weights.get((neighbor, n), 1)

                        # 计算新增益
                        new_gain = old_gain + self.graph.edge_weights.get((neighbor, node), 1)

                        # 更新桶
                        if old_gain in self.buckets['B']:
                            self.buckets['B'][old_gain].discard(neighbor)
                            if not self.buckets['B'][old_gain]:
                                del self.buckets['B'][old_gain]
                                if old_gain == self.max_gain_b and self.buckets['B']:
                                    self.max_gain_b = max(self.buckets['B'].keys())

                        self.buckets['B'][new_gain].add(neighbor)
                        if new_gain > self.max_gain_b:
                            self.max_gain_b = new_gain

    def partition(self, max_iterations: int = 3) -> Tuple[Set[str], Set[str]]:
        """
        执行分割算法
        """
        self.initialize_partitions()

        # 确保初始分区不为空
        if not self.partition_a or not self.partition_b:
            # 如果一个分区为空，则随机分配节点
            all_nodes = list(self.graph.nodes.keys())
            np.random.shuffle(all_nodes)
            mid_point = len(all_nodes) // 2
            self.partition_a = set(all_nodes[:mid_point])
            self.partition_b = set(all_nodes[mid_point:])

        best_cutsize = float('inf')
        best_partition = (self.partition_a.copy(), self.partition_b.copy())
        consecutive_no_improvement = 0  # 连续无改进次数
        max_no_improvement = 2  # 最大允许连续无改进次数，减少到2次

        for iteration in range(max_iterations):
            # 重置锁定集合
            self.locked = set()
            self.move_history = []  # 重置移动历史

            # 一次FM迭代 - 限制最大移动次数
            max_moves = min(len(self.graph.nodes) // 2, 50)  # 限制每次迭代的最大移动次数
            moves_count = 0

            while len(self.locked) < len(self.graph.nodes) and moves_count < max_moves:
                # 选择最佳移动
                move = self._select_best_move()
                if not move:
                    break

                # 执行移动
                self._move_node(move)
                self.move_history.append(move)
                self.locked.add(move[1])  # 锁定已移动的节点
                moves_count += 1

            # 计算当前割集大小
            cutsize = self._calculate_cutsize()

            if cutsize < best_cutsize:
                best_cutsize = cutsize
                best_partition = (self.partition_a.copy(), self.partition_b.copy())
                consecutive_no_improvement = 0
            else:
                consecutive_no_improvement += 1

            # 如果连续多次没有改进则提前终止
            if consecutive_no_improvement >= max_no_improvement:
                break

        # 设置最佳分割结果
        if best_partition:
            self.partition_a, self.partition_b = best_partition

        return self.partition_a, self.partition_b


class CircuitPartitioner:
    """
    电路分割主类 - 根据规则重构版本

    遵循规则：
    1. A区在分割之前包含原电路的所有input，在分割后一定为"partition_a":列表中的input
    2. 如果A区包含原电路的output，在分割后一定视作列表里的output
    3. "partition_a"列表中和X相接的端口一定视作列表里的output
    4. "partition_b"的列表：如果包含原电路的output，在分割后一定视作列表里的output
    5. "partition_b"列表中和X相接的端口一定视作列表里的input
    """

    def __init__(self, verilog_file: str):
        self.verilog_file = verilog_file
        self.parser = VerilogParser(verilog_file)
        self.graph = Graph()
        self.original_module_content = ""

    def build_graph(self) -> None:
        """
        根据Verilog模块构建图
        """
        modules = self.parser.parse()

        # 读取原始模块内容
        with open(self.verilog_file, 'r') as f:
            self.original_module_content = f.read()

        # 构建节点
        for module_name, module_data in modules.items():
            for instance_type, instance_name, connections in module_data['instances']:
                # 为每个实例创建节点
                self.graph.add_node(instance_name, instance_type)

        # 构建信号到实例的映射
        signal_to_instances = defaultdict(set)

        for module_name, module_data in modules.items():
            for instance_type, instance_name, connections in module_data['instances']:
                conn_list = [c.strip() for c in connections.split(',') if c.strip()]
                for conn in conn_list:
                    # 提取连接的信号名
                    if '.' in conn:  # 形如 .port(signal) 的连接
                        signal = conn.split('(')[1].split(')')[0].strip()
                        signal_to_instances[signal].add(instance_name)
                    else:  # 直接连接
                        signal_to_instances[conn].add(instance_name)

        # 基于信号连接构建边
        connection_count = 0
        for signal, instances in signal_to_instances.items():
            # 如果一个信号连接到多个实例，则在所有实例之间建立边
            if len(instances) > 1:
                instances_list = list(instances)
                for i in range(len(instances_list)):
                    for j in range(i+1, len(instances_list)):
                        self.graph.add_edge(instances_list[i], instances_list[j])
                        connection_count += 1

    def partition_circuit(self, balance_factor: float = 0.5) -> Dict[str, Any]:
        """
        对电路进行分割
        """
        # 构建图
        self.build_graph()

        # 应用FM算法
        partitioner = FMPartitioner(self.graph, self.parser, balance_factor)
        partition_a, partition_b = partitioner.partition()

        # 返回详细信息
        return self.graph.get_detailed_partition_info(partition_a, partition_b)

    def save_partitions(self, partitions: Dict[str, Any], output_dir: str) -> None:
        """
        保存分割结果到GraphML文件
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 保存分割结果到GraphML文件，使用基础名称 + _cut.graphml
        base_name = os.path.splitext(os.path.basename(self.verilog_file))[0]
        graphml_file = os.path.join(output_dir, f'{base_name}_cut.graphml')

        # 添加原始电路信息到分割结果中
        enhanced_partitions = self._add_circuit_info(partitions)
        
        # 创建GraphML结构
        root = ElementTree.Element("graphml")
        root.set("xmlns", "http://graphml.graphdrawing.org/xmlns")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", "http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd")

        # 定义键 (Keys)
        # 节点属性
        key_partition = ElementTree.SubElement(root, "key")
        key_partition.set("id", "d0")
        key_partition.set("for", "node")
        key_partition.set("attr.name", "partition")
        key_partition.set("attr.type", "string")

        key_type = ElementTree.SubElement(root, "key")
        key_type.set("id", "d1")
        key_type.set("for", "node")
        key_type.set("attr.name", "type")
        key_type.set("attr.type", "string")
        
        key_connections = ElementTree.SubElement(root, "key")
        key_connections.set("id", "d2")
        key_connections.set("for", "node")
        key_connections.set("attr.name", "connections")
        key_connections.set("attr.type", "string")

        # 图属性 (存储复杂的circuit_info)
        key_circuit_info = ElementTree.SubElement(root, "key")
        key_circuit_info.set("id", "d3")
        key_circuit_info.set("for", "graph")
        key_circuit_info.set("attr.name", "circuit_info")
        key_circuit_info.set("attr.type", "string")

        # 图元素
        graph_elem = ElementTree.SubElement(root, "graph")
        graph_elem.set("id", "G")
        graph_elem.set("edgedefault", "undirected")

        # 存储circuit_info
        data_circuit_info = ElementTree.SubElement(graph_elem, "data")
        data_circuit_info.set("key", "d3")
        data_circuit_info.text = json.dumps(enhanced_partitions['circuit_info'])

        # 添加节点
        partition_a = set(enhanced_partitions['partition_a_nodes'])
        partition_b = set(enhanced_partitions['partition_b_nodes'])
        
        # 获取所有实例信息以便添加到节点
        modules = enhanced_partitions['circuit_info']['modules']
        # 假设只有一个顶层模块或我们只关心实例
        all_instances = {}
        for m_name, m_data in modules.items():
            for inst_type, inst_name, inst_conns in m_data['instances']:
                all_instances[inst_name] = {'type': inst_type, 'connections': inst_conns}

        # 添加A区节点
        for node in partition_a:
            node_elem = ElementTree.SubElement(graph_elem, "node")
            node_elem.set("id", node)
            
            data_part = ElementTree.SubElement(node_elem, "data")
            data_part.set("key", "d0")
            data_part.text = "a"
            
            if node in all_instances:
                data_type = ElementTree.SubElement(node_elem, "data")
                data_type.set("key", "d1")
                data_type.text = all_instances[node]['type']
                
                data_conns = ElementTree.SubElement(node_elem, "data")
                data_conns.set("key", "d2")
                data_conns.text = all_instances[node]['connections']

        # 添加B区节点
        for node in partition_b:
            node_elem = ElementTree.SubElement(graph_elem, "node")
            node_elem.set("id", node)
            
            data_part = ElementTree.SubElement(node_elem, "data")
            data_part.set("key", "d0")
            data_part.text = "b"
            
            if node in all_instances:
                data_type = ElementTree.SubElement(node_elem, "data")
                data_type.set("key", "d1")
                data_type.text = all_instances[node]['type']
                
                data_conns = ElementTree.SubElement(node_elem, "data")
                data_conns.set("key", "d2")
                data_conns.text = all_instances[node]['connections']

        # 添加边
        # 使用self.graph.edges
        added_edges = set()
        for (u, v) in self.graph.edges:
            # 避免重复添加无向边
            if (u, v) not in added_edges and (v, u) not in added_edges:
                edge_elem = ElementTree.SubElement(graph_elem, "edge")
                edge_elem.set("source", u)
                edge_elem.set("target", v)
                added_edges.add((u, v))

        # 写入文件
        tree = ElementTree.ElementTree(root)
        # 缩进美化 (Python 3.9+)
        if hasattr(ElementTree, "indent"):
            ElementTree.indent(tree, space="  ", level=0)
            
        tree.write(graphml_file, encoding="utf-8", xml_declaration=True)

    def _add_circuit_info(self, partitions: Dict[str, Any]) -> Dict[str, Any]:
        """附加端口方向等电路信息。"""
        modules = self.parser.parse()
        partition_a = set(partitions['partition_a_nodes'])
        partition_b = set(partitions['partition_b_nodes'])

        # 预先定义，避免未赋值警告
        signal_to_instances: Dict[str, List[Tuple[str, bool, bool]]] = defaultdict(list)
        cut_signal_directions: Dict[str, Dict[str, bool]] = {}

        module_info = {}
        for module_name, module_data in modules.items():
            for instance_type, instance_name, connections in module_data['instances']:
                in_partition_a = instance_name in partition_a
                conn_list = [c.strip() for c in connections.split(',') if c.strip()]
                for conn in conn_list:
                    if '.' in conn:
                        port_signal = conn.split('(')
                        port = port_signal[0].replace('.', '').strip()
                        signal = port_signal[1].split(')')[0].strip()
                        port_mapping = self._get_port_mapping(instance_type)
                        if port_mapping and port in port_mapping["ports"]:
                            port_index = port_mapping["ports"].index(port)
                            is_output = port_mapping["directions"][port_index] == "output"
                        else:
                            is_output = port.upper() in ('Q', 'ZN', 'Y')
                        signal_to_instances[signal].append((instance_name, is_output, in_partition_a))
                    else:
                        signal_to_instances[conn].append((instance_name, False, in_partition_a))

            cut_signals = set()
            for signal, instances in signal_to_instances.items():
                partitions_connected = {'A' if in_a else 'B' for _, _, in_a in instances}
                if len(partitions_connected) > 1:
                    cut_signals.add(signal)

            cut_signal_directions = {}
            for signal in cut_signals:
                from_a = False
                from_b = False
                for instance_name, is_output, in_a in signal_to_instances.get(signal, []):
                    if is_output:
                        if in_a:
                            from_a = True
                            from_b = False
                        else:
                            from_a = False
                            from_b = True
                        break
                if not (from_a or from_b):
                    if signal not in module_data.get('inputs', []):
                        from_a = True
                cut_signal_directions[signal] = {
                    'from_partition_a': from_a,
                    'from_partition_b': from_b
                }

            real_cut_signals = [s for s in cut_signals if s not in module_data.get('inputs', [])]
            for sig in list(cut_signal_directions.keys()):
                if sig not in real_cut_signals:
                    del cut_signal_directions[sig]

            module_info[module_name] = {
                'ports': module_data['ports'],
                'inputs': module_data.get('inputs', []),
                'outputs': module_data.get('outputs', []),
                'wires': module_data['wires'],
                'instances': module_data['instances'],
                'cut_signals': real_cut_signals,
                'cut_signal_directions': cut_signal_directions
            }

        connections = {node: list(self.graph.get_neighbors(node)) for node in self.graph.nodes}

        enhanced_partitions = partitions.copy()
        enhanced_partitions['circuit_info'] = {
            'modules': module_info,
            'connections': connections,
            'original_file': self.verilog_file,
            'partition_ports': {
                'partition_a': self._get_partition_ports(partition_a, True, signal_to_instances, cut_signal_directions),
                'partition_b': self._get_partition_ports(partition_b, False, signal_to_instances, cut_signal_directions)
            }
        }

        return enhanced_partitions

    @staticmethod
    def _get_port_mapping(instance_type: str) -> Dict[str, Any]:
        """
        获取实例类型的端口映射
        """
        mappings = {
            "DFF_X1": {
                "ports": ["D", "CK", "Q", "QN"],
                "directions": ["input", "input", "output", "output"]
            },
            "OR2_X1": {
                "ports": ["A1", "A2", "ZN"],
                "directions": ["input", "input", "output"]
            },
            "NOR2_X1": {
                "ports": ["A1", "A2", "ZN"],
                "directions": ["input", "input", "output"]
            },
            "AND2_X1": {
                "ports": ["A1", "A2", "ZN"],
                "directions": ["input", "input", "output"]
            },
            "NAND2_X1": {
                "ports": ["A1", "A2", "ZN"],
                "directions": ["input", "input", "output"]
            },
            "INV_X1": {
                "ports": ["A", "ZN"],
                "directions": ["input", "output"]
            }
        }
        return mappings.get(instance_type, {})

    def _get_partition_ports(self, partition: Set[str], is_partition_a: bool, 
                           signal_to_instances: Dict, cut_signal_directions: Dict) -> Dict[str, List[str]]:
        """
        获取分区的端口信息，包括输入和输出

        规则说明 (基于信号流向):
        1. 原电路输入 (PI)：初始默认分配给 A 区；若 B 区实例也使用该输入，则 B 区也声明为 input。
        2. 原电路输出 (PO)：归属于驱动该信号的实例所在的分区。
        3. 割线方向 (动态决定)：
           - A -> B：若信号源实例在 A，则 A output, B input。
           - B -> A：若信号源实例在 B，则 B output, A input。
        """
        inputs = []
        outputs = []

        # 获取原始端口信息
        modules = self.parser.parse()
        first_module = list(modules.values())[0]
        original_inputs = first_module.get('inputs', [])
        original_outputs = first_module.get('outputs', [])
        
        # 后备逻辑
        if not original_inputs and not original_outputs:
            original_ports = first_module['ports']
            original_inputs = [p for p in original_ports if p in ["CK", "G0", "G1", "G2", "G3"]]
            original_outputs = [p for p in original_ports if p in ["G17"]]

        # 规则1: 处理原始输入 (PI)
        # 检查该分区的实例是否使用了某个PI
        for pi in original_inputs:
            used_in_partition = False
            # 检查连接到该PI的实例是否在当前分区
            # 注意：signal_to_instances 存储的是 (instance_name, is_output, in_partition_a)
            # 对于PI，它连接的实例通常是 input (is_output=False)
            for instance_name, _, _ in signal_to_instances.get(pi, []):
                if instance_name in partition:
                    used_in_partition = True
                    break
            
            # 特殊情况：如果PI没有连接到任何实例（未通过解析找到），或者默认分配
            # 规则1说 "初始默认分配给 A 区"
            if is_partition_a:
                inputs.append(pi)
            elif used_in_partition:
                # 如果是B区且使用了该PI
                inputs.append(pi)

        # 规则2: 处理原始输出 (PO)
        # 归属于驱动该信号的实例所在的分区
        for out in original_outputs:
            # 找到驱动该输出的实例
            driving_instance = None
            for instance_name, is_out, _ in signal_to_instances.get(out, []):
                if is_out:
                    driving_instance = instance_name
                    break
            
            if driving_instance:
                if driving_instance in partition:
                    outputs.append(out)
            else:
                # 如果找不到驱动实例，检查是否有任何连接实例在当前分区
                # (这通常不应该发生，除非是直接连接)
                connected = False
                for instance_name, _, _ in signal_to_instances.get(out, []):
                    if instance_name in partition:
                        connected = True
                        break
                if connected:
                    outputs.append(out)

        # 规则3: 处理割集信号
        # 遍历所有割集信号
        for signal, directions in cut_signal_directions.items():
            # directions['from_partition_a'] == True 意味着 A output, B input
            # directions['from_partition_b'] == True 意味着 B output, A input
            
            from_a = directions.get('from_partition_a', False)
            from_b = directions.get('from_partition_b', False)
            
            if is_partition_a:
                if from_a:
                    # A -> B，A是输出
                    outputs.append(signal)
                elif from_b:
                    # B -> A，A是输入
                    inputs.append(signal)
            else: # Partition B
                if from_a:
                    # A -> B，B是输入
                    inputs.append(signal)
                elif from_b:
                    # B -> A，B是输出
                    outputs.append(signal)

        # 去除重复端口
        inputs = list(set(inputs))
        outputs = list(set(outputs))

        return {
            'inputs': inputs,
            'outputs': outputs
        }


def process_circuit(ckt_name: str):
    """
    处理指定的电路

    :param circuit_name: 电路名称，例如 "s27"
    :return: 分割结果字典
    """
    # 自动添加.v扩展名（如果没有的话）
    verilog_filename = ckt_name if ckt_name.endswith('.v') else f"{ckt_name}.v"

    # 检查文件是否存在
    verilog_file = os.path.join(os.path.dirname(__file__), '..', 'circuit', verilog_filename)
    if not os.path.exists(verilog_file):
        print(f"错误：找不到文件 {verilog_file}")
        print("请确保文件存在于circuit目录下")
        return None

    partitioner = CircuitPartitioner(verilog_file)
    partitions = partitioner.partition_circuit()

    # 确保output目录存在
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    partitioner.save_partitions(partitions, output_dir)

    return partitions


if __name__ == "__main__":
    # 支持直接运行：优先使用命令行参数，否则提示输入电路名
    if len(sys.argv) > 1:
        ckt_arg = sys.argv[1]
    else:
        ckt_arg = input("请输入电路名称 (例如: s27, s382): ").strip()

    if ckt_arg:
        process_circuit(ckt_arg)
    else:
        print("未提供电路名称，程序退出。")

