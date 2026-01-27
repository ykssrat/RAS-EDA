import os
import pprint
import json
import timeit


class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.clk_name = ''
        self.clk_period = 0
        self.end_time = 0
        self.circuit_info_file = ''
        self.golden_file = ''
        self.fault_file = ''
        self.path = ''
        self.tcl_file = ''

        self.read_config()

    def read_config(self):
        with open(self.config_file) as c_file:
            js = json.load(c_file)
            self.clk_name = js['clk_name']
            self.clk_period = js['clk_period']
            self.end_time = js['end_time']
            self.circuit_info_file = js['circuit_info_file']
            self.golden_file = js['golden_file']
            self.fault_file = js['fault_file']
            self.path = js['path']
            self.tcl_file = js['tcl_file']

    def print_config(self):
        for attr, value in self.__dict__.items():
            print(f"{attr}: {value}")


class CircuitInfo:
    def __init__(self, config):
        self.path = config.path
        self.circuit_info_file = config.circuit_info_file
        self.golden_file = config.golden_file
        self.fault_file = config.fault_file
        self.injection_reg = []
        self.out_port = []
        self.reg = []
        self.golden_dic = {}
        self.fault_dic = {}
        self.fdr_log = {}
        self.fdr_result = {}

    @staticmethod
    def get_name_time(fault_cell):
        split_index = fault_cell.rfind('_')
        name = fault_cell[:split_index]
        time = fault_cell[split_index + 1:]
        return name, int(time)

    def get_circuit_info(self):
        os.chdir(self.path)
        with open(self.circuit_info_file) as info_file:
            js = json.load(info_file)
            for injection_reg in js["injection_reg"]:
                self.injection_reg.append(injection_reg)
            for reg in js["state_reg"]:
                self.reg.append(reg)
            for port in js["out_port"]:
                self.out_port.append(port)

    def get_golden(self):
        os.chdir(self.path)
        with open(self.golden_file) as golden_file:
            js = json.load(golden_file)
            self.golden_dic = js

    def get_fault(self):
        os.chdir(self.path)
        with open(self.fault_file) as fault_file:
            js = json.load(fault_file)
            self.fault_dic = js

    def cal_result(self):
        # self.print_circuit()
        # 初始化
        self.fdr_log = {}
        for k in self.golden_dic.keys():
            if k not in self.out_port:
                self.fdr_log[k] = []
        # 开始遍历fault_log
        for fault_cell, results in self.fault_dic.items():
            # 获得最终状态，用于判断是否有潜在故障
            golden = []
            for value in self.golden_dic.values():
                golden.append(value[-1])
            fault = []
            for value in results.values():
                fault.append(value[-1])
            reg_name, time = self.get_name_time(fault_cell)
            for output in self.out_port:
                # 先判断输出是否有故障
                if self.golden_dic[output] == results[output]:
                    # 如果输出无故障，判断是否有潜在故障
                    # 无潜在故障
                    if golden == fault:
                        self.fdr_log[reg_name].append(0)
                    # 存在潜在故障
                    else:
                        self.fdr_log[reg_name].append(-1)
                # 产生故障
                else:
                    self.fdr_log[reg_name].append(1)
        # pprint.pprint(self.fdr_log)
        self.fdr_result = {}
        for reg, values in self.fdr_log.items():
            total = len(values)
            error = 0
            correct = 0
            hide = 0
            for v in values:
                if v == 1:
                    error += 1
                elif v == 0:
                    correct += 1
                else:
                    hide += 1
            fdr = float(error) / float(total)
            self.fdr_result[reg] = {'error': error, 'correct': correct, 'hide': hide, 'FDR': fdr}
        pprint.pprint(self.fdr_result)
        self.save_report(self.fdr_result)

    def save_report(self, results):
        import csv
        import datetime
        import pandas as pd
        
        # 确保输出目录存在
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'ser_analysis')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        xlsx_filename = os.path.join(output_dir, f"fdr_report_{timestamp}.xlsx")
        
        # 准备数据
        data = []
        for reg, res in results.items():
            data.append({
                'Register': reg,
                'FDR': res['FDR'],
                'Error (Detected)': res['error'],
                'Correct (Masked)': res['correct'],
                'Hide (Latent)': res['hide']
            })
            
        # 创建 DataFrame
        df = pd.DataFrame(data)
        
        # 按 FDR 降序排序
        df = df.sort_values(by='FDR', ascending=False)
        
        # 保存为 Excel
        try:
            df.to_excel(xlsx_filename, index=False)
            print(f"Excel 报告已保存至: {xlsx_filename}")
        except Exception as e:
            print(f"保存 Excel 报告失败: {e}")
            # 降级保存为 CSV
            csv_filename = os.path.join(output_dir, f"fdr_report_{timestamp}.csv")
            df.to_csv(csv_filename, index=False)
            print(f"已降级保存为 CSV: {csv_filename}")

    def print_circuit(self):
        for attr, value in self.__dict__.items():
            print(f"{attr}: {value}")


class Simulator:
    def __init__(self, config):
        self.path = config.path
        self.tcl_file = config.tcl_file
        self.clk_period = config.clk_period
        self.end_time = config.end_time
        self.vcs_command = config.vcs_command
        self.env_setup = config.env_setup

        self.golden_tcl_content = "call {$rungolden}\nrun"
        self.fault_tcl_content = "restart\n" + \
                                 "call {{$runfault(\"{0}\")}}\n" + \
                                 "run {1}\n" + \
                                 "run 0\n" + \
                                 "force {{{2}}} x -deposit\n" + \
                                 "run -absolute {3}\n"

    def init_makefile(self):
        pass

    def compile(self):
        os.chdir(self.path)
        os.system('make com')

    def simulate(self):
        os.chdir(self.path)
        os.system('make sim')

    def clean(self):
        os.chdir(self.path)
        os.system('make clean')

    def write_golden_tcl(self):
        os.chdir(self.path)
        with open(self.tcl_file, 'w') as tcl:
            tcl.write(self.golden_tcl_content)

    def set_fault_tcl(self, time, reg, fault_name):
        os.chdir(self.path)
        with open(self.tcl_file, 'a') as tcl:
            tcl.write(self.fault_tcl_content.format(fault_name, time, reg, self.end_time))

    def write_fault_tcl(self, injection_reg_list):
        with open(self.tcl_file, 'w') as tcl:
            pass
        for reg in injection_reg_list:
            for i in range(self.end_time):
                t = self.clk_period / 2 + i * self.clk_period
                if t >= self.end_time - self.clk_period:
                    break
                fault_name = reg + "_{0}".format(i)
                self.set_fault_tcl(t, reg, fault_name)
        with open(self.tcl_file, 'a') as tcl:
            tcl.write("\nfinish\n")


class LogMonitor:
    """非侵入性日志解析器：
    - 通过扫描 VCS 日志中已完成的 fault 名称来估算进度（不会修改仿真流程）
    - 提供给有真实仿真运行时的可选进度显示
    """
    def __init__(self, log_path):
        self.log_path = log_path

    def _read_log(self):
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except FileNotFoundError:
            return ''

    def estimate_progress_by_faults(self, fault_names):
        """根据 fault_names 列表在日志中出现的次数来估算完成比例。
        返回 (completed_count, total_count, fraction)
        """
        if not fault_names:
            return 0, 0, 0.0
        txt = self._read_log()
        completed = 0
        for fn in fault_names:
            if fn in txt:
                completed += 1
        total = len(fault_names)
        return completed, total, float(completed) / float(total)


def run_python_regression(circuit_name='s27'):
    """在 Python 端使用已有的 JSON 做快速回归：
    - 不调用 VCS/Make
    - 加载已有的 golden/fault/circuit_info（优先使用带电路名的文件）
    - 调用 cal_result() 并验证结果非退化（不是全部 FDR==0）
    返回 True/False（通过/失败）
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(project_root, 'config', 'config.json')
    cfg = Config(cfg_path)

    # 优先寻找 per-circuit 输出（window.py 生成的命名规则）
    candidate_golden = os.path.join(project_root, 'output', f"{circuit_name}_golden.json")
    candidate_fault = os.path.join(project_root, 'output', f"{circuit_name}_fault.json")
    candidate_info = os.path.join(project_root, 'output', f"{circuit_name}_circuit_info.json")

    if os.path.exists(candidate_golden) and os.path.exists(candidate_fault):
        cfg.golden_file = os.path.relpath(candidate_golden, cfg.path) if os.path.isabs(cfg.path) else os.path.relpath(candidate_golden, os.getcwd())
        cfg.fault_file = os.path.relpath(candidate_fault, cfg.path) if os.path.isabs(cfg.path) else os.path.relpath(candidate_fault, os.getcwd())
    else:
        print(f"[REGRESS] 未找到专用的 {circuit_name} golden/fault 文件，使用配置中的默认文件：{cfg.golden_file}, {cfg.fault_file}")

    if os.path.exists(candidate_info):
        cfg.circuit_info_file = os.path.relpath(candidate_info, cfg.path) if os.path.isabs(cfg.path) else os.path.relpath(candidate_info, os.getcwd())

    circ = CircuitInfo(cfg)
    circ.get_circuit_info()
    circ.get_golden()
    circ.get_fault()
    circ.cal_result()

    # 判断是否退化（所有寄存器的 error == 0）
    all_zero = True
    for reg, stats in circ.fdr_result.items():
        if stats.get('error', 0) > 0 or stats.get('FDR', 0.0) > 0.0:
            all_zero = False
            break

    if all_zero:
        print(f"[REGRESS][FAIL] {circuit_name} 回归失败：所有寄存器 FDR == 0（可能仿真/日志处理被篡改）")
        return False
    else:
        print(f"[REGRESS][PASS] {circuit_name} 回归通过 — 存在非零 FDR（快速验证通过）")
        return True


def main():
    # 保持向后兼容的默认行为不变；新增两个可选开关：--regress 和 --progress
    args = sys.argv[1:]
    do_regress = '--regress' in args
    show_progress = '--progress' in args
    regress_circuit = None
    for a_i, a in enumerate(args):
        if a == '--regress' and a_i + 1 < len(args):
            regress_circuit = args[a_i + 1]

    if do_regress:
        circuit_name = regress_circuit or 's27'
        ok = run_python_regression(circuit_name)
        sys.exit(0 if ok else 2)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'config.json')
    config = Config(config_path)
    circuit = CircuitInfo(config)
    config.print_config()
    sim = Simulator(config)

    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'vcs_run.log')
    print(f"[INFO] VCS/Make 所有输出将记录到: {log_path}")

    # golden
    sim.write_golden_tcl()
    sim.clean()
    if not sim.compile():
        print(f"[ERROR] 详细日志请查阅: {log_path}")
        return

    # 如果用户请求进度显示，则在真实仿真时监控日志（非侵入）
    if show_progress:
        monitor = LogMonitor(log_path)
        print('[INFO] 进度监控已开启（通过解析 VCS 日志） — 仅用于显示，不改动仿真流程')

    if not sim.simulate():
        print(f"[ERROR] 详细日志请查阅: {log_path}")
        return

    # 在仿真运行期间（或之后）可以查询进度（若启用）——这里只做一次示例查询
    if show_progress:
        # 尝试从 fault 文件或 circuit info 中收集 fault name 列表用于估算
        try:
            with open(os.path.join(os.path.dirname(script_dir), config.fault_file)) as f:
                fault_js = json.load(f)
                fault_names = list(fault_js.keys())
        except Exception:
            fault_names = []
        c, t, frac = monitor.estimate_progress_by_faults(fault_names)
        print(f"[PROGRESS] 已检测到 {c}/{t} 个故障记录在日志中（估算完成: {frac:.0%}）")

    circuit.get_circuit_info()
    circuit.get_golden()
    # circuit.print_circuit()

    # fault
    sim.write_fault_tcl(circuit.injection_reg)
    if not sim.simulate():
        print(f"[ERROR] 详细日志请查阅: {log_path}")
        return
    circuit.get_fault()
    circuit.cal_result()
    pass
    config = Config('../config.json')
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
    # circuit.print_circuit()

    # fault
    sim.write_fault_tcl(circuit.injection_reg)
    sim.simulate()
    circuit.get_fault()
    circuit.cal_result()
    pass


if __name__ == '__main__':
    start = timeit.default_timer()
    main()
    stop = timeit.default_timer()
    print('Time: ', stop - start)