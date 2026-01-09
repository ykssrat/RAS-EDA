import os
import pprint
import json
import timeit
import subprocess
import typing


def ensure_path(path: typing.Optional[os.PathLike[str] | str]) -> str:
    """Return a usable path. If missing, fall back to the project root (dir above 'py')."""
    if path:
        normalized = os.fspath(path)
        if os.path.isdir(normalized):
            return normalized
    # fallback to project root (directory above the workspace 'py' folder)
    root_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.fspath(__file__))))
    print(f"Warning: 配置的路径 '{path}' 不存在，回退到 '{root_dir}'")
    return root_dir


class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.circuit_name = 'circuit'
        self.clk_name = ''
        self.clk_period = 0
        self.end_time = 0
        self.circuit_info_file = ''
        self.golden_file = ''
        self.fault_file = ''
        self.path = ''
        self.tcl_file = ''
        self.tb_module = ''
        self.verbose = False

        self.read_config()

    def read_config(self):
        base_dir = os.path.dirname(os.path.abspath(self.config_file))
        with open(self.config_file) as c_file:
            js = json.load(c_file)
            self.circuit_name = js.get('circuit_name', self.circuit_name)
            self.clk_name = js['clk_name']
            self.clk_period = js['clk_period']
            self.end_time = js['end_time']
            self.circuit_info_file = self._resolve_path(base_dir, js['circuit_info_file'])
            self.golden_file = self._resolve_path(base_dir, js['golden_file'])
            self.fault_file = self._resolve_path(base_dir, js['fault_file'])
            self.path = self._resolve_path(base_dir, js['path'])
            self.tcl_file = self._resolve_path(base_dir, js['tcl_file'])
            self.tb_module = js.get('tb_module', '')
            self.verbose = js.get('verbose', False)

    @staticmethod
    def _resolve_path(base_dir, value):
        if not value:
            return value
        if os.path.isabs(value):
            return value
        return os.path.abspath(os.path.join(base_dir, value))

    def print_config(self):
        if self.verbose:
            for attr, value in self.__dict__.items():
                print(f"{attr}: {value}")
        else:
            print(f"config_file: {self.config_file}")
            print(f"circuit: {self.circuit_name}, clk: {self.clk_name}@{self.clk_period}, end: {self.end_time}")


class CircuitInfo:
    def __init__(self, config):
        self.config = config
        self.path = config.path
        self.circuit_info_file = config.circuit_info_file
        self.golden_file = config.golden_file
        self.fault_file = config.fault_file
        self.circuit_name = config.circuit_name
        self.injection_reg = []
        self.out_port = []
        self.reg = []
        self.golden_dic = {}
        self.fault_dic = {}
        self.fdr_log = {}
        self.fdr_result = {}

    @staticmethod
    def get_name_time(fault_cell):
        # 解析形如: <hier.signal[bit]>_<time>
        # 使用正则从末尾提取时间，保留包含下划线的层次名
        import re
        m = re.search(r"^(.*)_(\d+)$", fault_cell)
        if not m:
            # 回退：无法匹配时，尽量返回原串与0
            return fault_cell, 0
        name = m.group(1)
        time_str = m.group(2)
        try:
            return name, int(time_str)
        except ValueError:
            return name, 0

    def get_circuit_info(self):
        os.chdir(ensure_path(self.path))
        with open(self.circuit_info_file) as info_file:
            js = json.load(info_file)
            for injection_reg in js["injection_reg"]:
                self.injection_reg.append(injection_reg)
            for reg in js["state_reg"]:
                self.reg.append(reg)
            for port in js["out_port"]:
                self.out_port.append(port)

    def get_golden(self):
        os.chdir(ensure_path(self.path))
        with open(self.golden_file) as golden_file:
            js = json.load(golden_file)
            self.golden_dic = js

    def get_fault(self):
        os.chdir(ensure_path(self.path))
        with open(self.fault_file) as fault_file:
            js = json.load(fault_file)
            self.fault_dic = js

    def cal_result(self):
        # 初始化：使用注入目标作为键，避免 KeyError 并包含输出位注入的情况
        self.fdr_log = {}

        # 从 injection_reg 构建基名集合（去掉位选，如 signal[0] -> signal）
        injection_basenames = set()
        for inj in self.injection_reg:
            base = inj.split('[')[0]
            injection_basenames.add(base)

        # 防御：如果 injection_reg 为空，则基于 fault_dic 动态推断
        if not injection_basenames and self.fault_dic:
            for fault_cell in self.fault_dic.keys():
                reg_name, _ = self.get_name_time(fault_cell)
                base = reg_name.split('[')[0]
                injection_basenames.add(base)

        for base in injection_basenames:
            self.fdr_log[base] = []

        # 开始遍历 fault_log
        for fault_cell, results in self.fault_dic.items():
            # 收集各输出的最终采样值，用于判断是否有潜在故障
            golden_last = []
            fault_last = []
            reg_name, _time = self.get_name_time(fault_cell)
            base = reg_name.split('[')[0]

            for output in self.out_port:
                if output not in results or not results[output]:
                    continue
                g_seq = self.golden_dic.get(output, [])
                f_seq = results.get(output, [])
                if not g_seq or not f_seq:
                    continue
                # 对齐长度，截取到黄金长度，避免过长波形导致比较失真
                min_len = min(len(g_seq), len(f_seq))
                g_seq = g_seq[:min_len]
                f_seq = f_seq[:min_len]
                golden_last.append(g_seq[-1])
                fault_last.append(f_seq[-1])

            # 确保键存在
            if base not in self.fdr_log:
                self.fdr_log[base] = []

            # 没有有效输出数据，跳过该故障样本
            if not golden_last and not fault_last:
                continue

            # 根据输出序列是否一致来记录检测情况
            if golden_last == fault_last:
                # 序列一致，视为掩蔽或隐性
                self.fdr_log[base].append(0)
            else:
                # 序列不同，视为检测到错误
                self.fdr_log[base].append(1)
        # pprint.pprint(self.fdr_log)
        self.fdr_result = {}
        for reg, values in self.fdr_log.items():
            total = len(values)
            if total == 0:
                # 无有效样本，跳过
                continue
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
        if self.config.verbose:
            pprint.pprint(self.fdr_result)
        else:
            for reg, res in self.fdr_result.items():
                print(f"{reg}: FDR={res['FDR']:.3f}, err={res['error']}, ok={res['correct']}, hide={res['hide']}")
        if not self.fdr_result:
            print("No valid FDR data; skipping report generation.")
            return
        self.save_report(self.fdr_result)

    def save_report(self, results):
        if not results:
            print("No results to save; report generation skipped.")
            return
        import pandas as pd
        
        # 确保输出目录存在
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'ser_analysis')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 文件名使用电路名，便于区分不同电路配置；不再用时间戳
        xlsx_filename = os.path.join(output_dir, f"fdr_report_{self.circuit_name}.xlsx")

        # 如同名文件已存在，提示并退出
        if os.path.exists(xlsx_filename):
            print(f"保存 Excel 报告已存在！: {xlsx_filename}")
            return
        
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

    def print_circuit(self):
        for attr, value in self.__dict__.items():
            print(f"{attr}: {value}")


class Simulator:
    def __init__(self, config):
        self.config = config
        self.path = config.path
        self.tcl_file = config.tcl_file
        self.clk_period = config.clk_period
        self.end_time = config.end_time
        self.golden_file = config.golden_file
        self.fault_file = config.fault_file
        self.circuit_info_file = config.circuit_info_file
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Golden run script now forces simulator to exit to avoid hanging at VSIM prompt
        self.golden_tcl_content = "call {$rungolden}\nrun\nquit -f"
        # Fault run: run to injection time, inject, then run remaining time
        self.fault_tcl_content = "restart\n" + \
                     "call {{$runfault(\"{0}\")}}\n" + \
                     "run {1}\n" + \
                     "force {{{2}}} x -deposit\n" + \
                     "run {3}\n"

    def init_makefile(self):
        pass

    def compile(self):
        if os.name == 'nt': # Windows
            bat_file = os.path.join(self.project_root, 'compile_pli.bat')
            cmd = f'cd /d "{self.project_root}" && "{bat_file}"'
            print(f"正在执行编译: {cmd}")
            ret = os.system(cmd)
            if ret != 0:
                print("Error: compile_pli.bat 执行失败。请检查 GCC 和 Questasim 路径配置。")
        else:
            print("Warning: Non-Windows environment detected. Please use Windows for Questasim simulation.")

    def simulate(self):
        if os.name == 'nt': # Windows
            tb_module = self.config.tb_module or f"{self.config.circuit_name}_tb"
            bat_file = os.path.join(self.project_root, 'run_modelsim.bat')
            cmd = f'cd /d "{self.project_root}" && "{bat_file}" {tb_module}'
            print(f"正在执行仿真: {cmd}")

            # 捕获输出，重复行只打印一次，降低终端噪声
            dedup_prefixes = [
                "# ** Note: (vsim-8009)",
                "# Loading work.",
                "# config.json size",
                "# [PLI] fault_call done.",
                "Top level modules:",
                "Running Simulation...",
                "Compiling Verilog...",
            ]
            # 过滤掉重复的 testbench 输出
            skip_prefixes = [
                "# {FM, TEST, CLR}",  # 过滤 testbench 每个周期的输出
            ]
            printed_once = set()
            fault_count = 0

            with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
                for raw in proc.stdout:
                    line = raw.decode(errors='ignore').rstrip('\r\n')
                    
                    # 跳过重复的 testbench 输出
                    if any(line.startswith(prefix) for prefix in skip_prefixes):
                        continue
                    
                    # 统计并显示故障注入进度
                    if line.startswith("# [PLI] fault_call start"):
                        fault_count += 1
                        print(f"\r[进度] 正在执行第 {fault_count} 个故障注入...", end='', flush=True)
                        continue
                    
                    # 去重打印其他信息
                    if any(line.startswith(prefix) for prefix in dedup_prefixes):
                        if line in printed_once:
                            continue
                        printed_once.add(line)
                    
                    # 显示错误和其他重要信息
                    if line and ("Error" in line or "error" in line or line.startswith("#")):
                        if fault_count > 0:
                            print()  # 换行后再打印
                        print(line)
                
                ret = proc.wait()
                if fault_count > 0:
                    print(f"\n✓ 故障注入仿真完成，共执行了 {fault_count} 次")

            if ret != 0:
                print("Error: run_modelsim.bat 执行失败。")
        else:
            print("Warning: Non-Windows environment detected. Please use Windows for Questasim simulation.")

    def clean(self):
        os.chdir(ensure_path(self.path))
        if os.name == 'nt': # Windows
            # Kill existing vsim processes to release file locks
            os.system("taskkill /F /IM vsim.exe /T >nul 2>&1")
            os.system("taskkill /F /IM vish.exe /T >nul 2>&1")

            if os.path.exists('work'):
                import shutil
                shutil.rmtree('work')
            if os.path.exists('transcript'):
                os.remove('transcript')
            if os.path.exists('vsim.wlf'):
                os.remove('vsim.wlf')
            
            # Clean up the DLL to ensure a fresh build
            dll_path = os.path.join(self.project_root, 'clibrary', 'pli.dll')
            if os.path.exists(dll_path):
                try:
                    os.remove(dll_path)
                except OSError:
                    print(f"Warning: Could not remove {dll_path}. It might be in use.")

            # Reset previous simulation outputs to avoid stale or duplicate data
            for stale_file in (self.golden_file, self.fault_file, self.circuit_info_file):
                if stale_file and os.path.exists(stale_file):
                    try:
                        os.remove(stale_file)
                        print(f"已清理旧输出: {stale_file}")
                    except OSError:
                        print(f"Warning: Could not remove {stale_file}. It might be in use.")
        else:
            print("Warning: Non-Windows environment detected. Clean operation skipped.")

    def write_golden_tcl(self):
        os.chdir(ensure_path(self.path))
        tcl_path = os.fspath(self.tcl_file)
        with open(tcl_path, 'w') as tcl:
            tcl.write(self.golden_tcl_content)

    def set_fault_tcl(self, time, reg, fault_name, remaining_time):
        os.chdir(ensure_path(self.path))
        tcl_path = os.fspath(self.tcl_file)
        with open(tcl_path, 'a') as tcl:
            tcl.write(self.fault_tcl_content.format(fault_name, time, reg, remaining_time))

    def write_fault_tcl(self, injection_reg_list):
        tcl_path = os.fspath(self.tcl_file)
        with open(tcl_path, 'w'):
            pass
        for reg in injection_reg_list:
            for i in range(self.end_time):
                t = self.clk_period / 2 + i * self.clk_period
                if t >= self.end_time - self.clk_period:
                    break
                remaining = self.end_time - t
                fault_name = reg + "_{0}".format(i)
                self.set_fault_tcl(t, reg, fault_name, remaining)
        with open(tcl_path, 'a') as tcl:
            tcl.write("\nquit -f\n")


def main():
    # Use absolute path for config.json based on script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.abspath(os.path.join(script_dir, '..', 'config.json'))
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