import sys
import time
import timeit
import threading
import json
import os
import re
import pprint
from tqdm import tqdm

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
        self.vcs_command = 'vcs'
        self.env_setup = ''

        self.read_config()

    def read_config(self):
        with open(self.config_file) as c_file:
            js = json.load(c_file)
            self.clk_name = js['clk_name']
            self.clk_period = js['clk_period']
            self.end_time = js['end_time']
            
            # 统一处理路径：确保不论从哪里启动，都能找到正确的文件
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            def fix_path(p):
                if not p: return ''
                if os.path.isabs(p): return p
                # 如果是 ./ 开头的相对路径，相对于项目根目录
                return os.path.normpath(os.path.join(base_dir, p.lstrip('./')))

            self.circuit_info_file = fix_path(js['circuit_info_file'])
            self.golden_file = fix_path(js['golden_file'])
            self.fault_file = fix_path(js['fault_file'])
            self.path = fix_path(js.get('path', '.'))
            self.tcl_file = fix_path(js['tcl_file'])
            
            self.vcs_command = js.get('vcs_command', self.vcs_command)
            self.env_setup = js.get('env_setup', self.env_setup)

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
        if not os.path.exists(self.golden_file):
            print(f"警告: {self.golden_file} 不存在，已初始化为空字典。")
            self.golden_dic = {}
            return
        with open(self.golden_file) as golden_file:
            js = json.load(golden_file)
            self.golden_dic = js

    def get_fault(self):
        os.chdir(self.path)
        if not os.path.exists(self.fault_file):
            print(f"警告: {self.fault_file} 不存在，已初始化为空字典。")
            self.fault_dic = {}
            return
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
        self.fdr_result = {}
        for reg, values in self.fdr_log.items():
            total = len(values)
            if total == 0:
                print(f"[WARN] 寄存器 {reg} 没有收集到任何故障仿真数据，跳过 FDR 计算。")
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
        
        if not self.fdr_result:
            print("[ERROR] 所有寄存器均无仿真数据。请检查：")
            print("  1. VCS 仿真是否正常结束？(查看 output/vcs_run.log)")
            print("  2. PLI 插件是否正确加载并写入了数据？")
            return
            
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
        # 可选的额外 flags（可用于启用 -debug_access+all 等），以及专用的 debug flags（仅在需要时使用）
        self.vcs_extra_flags = getattr(config, 'vcs_extra_flags', '')
        self.vcs_debug_flags = getattr(config, 'vcs_debug_flags', '')

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
        # 将 make 输出重定向到 output/vcs_run.log，便于后续分析
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, 'vcs_run.log')
        extra = self.vcs_extra_flags or ''
        if extra:
            cmd = f"make com VCS_EXTRA_FLAGS='{extra}' > {log_path} 2>&1"
        else:
            cmd = f"make com > {log_path} 2>&1"
        print(f"[SIM] 编译命令：{cmd}")
        rc = os.system(cmd)
        return rc == 0

    def rebuild_with_debug(self, extra_flags=None):
        """Recompile with debug-capable flags so that `force` works.
        This does NOT change config; it runs a one-off make with VCS_EXTRA_FLAGS.
        """
        debug_flags = extra_flags or self.vcs_debug_flags or '-debug_access+all'
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, 'vcs_run.log')
        cmd = f"make com VCS_EXTRA_FLAGS='{debug_flags}' >> {log_path} 2>&1"
        print(f"[SIM] 以 debug 标志重编译：{debug_flags}")
        rc = os.system(cmd)
        if rc == 0:
            print('[SIM] debug 重编译成功')
        else:
            print(f'[SIM] debug 重编译失败，查看日志: {log_path}')
        return rc == 0

    def simulate(self):
        os.chdir(self.path)
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, 'vcs_run.log')
        
        # 核心修复：强制使用配置中指定的 TCL 文件 (例如 Division_run.ucli)，而不是静态的 run.tcl
        tcl_filename = os.path.basename(self.tcl_file)
        cmd = f"./sim -ucli -i {tcl_filename} -ucli2Proc >> {log_path} 2>&1"
        print(f"[SIM] 仿真命令：{cmd}")
        rc = os.system(cmd)
        return rc == 0

    def clean(self):
        os.chdir(self.path)
        # 保护用户生成的分析产物（vcs_run.log 与 ser_analysis），以防 Makefile 的 clean 非预期删除
        root_output = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        vcs_log = os.path.join(root_output, 'vcs_run.log')
        sa_dir = os.path.join(root_output, 'ser_analysis')
        tmp_backup = None
        try:
            if os.path.exists(vcs_log):
                tmp_backup = vcs_log + '.bak'
                os.replace(vcs_log, tmp_backup)
            if os.path.exists(sa_dir):
                tmp_sa_bak = sa_dir + '_bak'
                if os.path.exists(tmp_sa_bak):
                    # 保持单次备份
                    pass
                else:
                    os.replace(sa_dir, tmp_sa_bak)
        except Exception:
            # 如果备份失败，继续执行 clean（不要阻塞）
            tmp_backup = None
        # 调用 make clean（Makefile 已修改为不删除 output/*）
        os.system('make clean')
        # 尝试还原备份
        try:
            if tmp_backup and os.path.exists(tmp_backup):
                os.replace(tmp_backup, vcs_log)
            if os.path.exists(sa_dir + '_bak') and not os.path.exists(sa_dir):
                os.replace(sa_dir + '_bak', sa_dir)
        except Exception:
            pass

    def write_golden_tcl(self):
        os.chdir(self.path)
        with open(self.tcl_file, 'w') as tcl:
            tcl.write(self.golden_tcl_content)

    def set_fault_tcl(self, time, reg, fault_name):
        os.chdir(self.path)
        with open(self.tcl_file, 'a') as tcl:
            tcl.write(self.fault_tcl_content.format(fault_name, time, reg, self.end_time))

    def write_fault_tcl(self, injection_reg_list):
        # 必须先写入 call {$runfault(...)} 才能激活 PLI 的故障记录逻辑
        with open(self.tcl_file, 'w') as tcl:
            # 修正属性访问：从传入的 config 路径获取文件名
            config_base = os.path.basename(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.json"))
            tcl.write(f"call {{$runfault(\"{config_base}\")}}\n")
        
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
    - 通过扫描 VCS 日志中已完成的 fault 名称来估算进度
    """
    def __init__(self, log_path, total_expected):
        self.log_path = log_path
        self.total_expected = total_expected
        self.pbar = None
        self.stop_event = threading.Event()

    def _get_completed_count(self):
        if not os.path.exists(self.log_path):
            return 0
        try:
            # 使用 shell 命令快速计数日志中的 "ucli%" 出现次数，这代表了一个命令周期的结束
            # 或者统计 "V C S   S i m u l a t i o n   R e p o r t" 出现的次数
            import subprocess
            cmd = f"grep -c 'V C S   S i m u l a t i o n   R e p o r t' {self.log_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
            return count
        except Exception:
            return 0

    def start_monitoring(self):
        self.pbar = tqdm(total=self.total_expected, desc="仿真进度", unit="fault")
        def update_loop():
            last_count = 0
            while not self.stop_event.is_set():
                curr_count = self._get_completed_count()
                if curr_count > last_count:
                    self.pbar.update(curr_count - last_count)
                    last_count = curr_count
                time.sleep(1)
        
        self.thread = threading.Thread(target=update_loop, daemon=True)
        self.thread.start()

    def stop_monitoring(self):
        self.stop_event.set()
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2)
        if self.pbar:
            # 确保最后进度条填满（如果是由于 finish 正常结束）
            self.pbar.n = self.total_expected
            self.pbar.refresh()
            self.pbar.close()

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
    # 保持向后兼容的默认行为不变；新增可选开关：--regress, --progress, --rebuild-debug
    args = sys.argv[1:]
    do_regress = '--regress' in args
    show_progress = '--progress' in args
    rebuild_debug = ('--rebuild-debug' in args) or ('--with-debug' in args)
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
        print(f"[ERROR] 编译失败，详细日志请查阅: {log_path}")
        return

    print("[INFO] 开始黄金 (Golden) 仿真以提取电路信号...")
    if not sim.simulate():
        print(f"[ERROR] 黄金仿真失败，详细日志请查阅: {log_path}")
        return

    # 黄金仿真结束后，读取并打印发现的信号
    circuit.get_circuit_info()
    circuit.get_golden()
    print(f"[INFO] 黄金仿真提取完成。探测到 {len(circuit.injection_reg)} 个可注入位，{len(circuit.out_port)} 个输出端口。")

    # fault
    print(f"[INFO] 正在生成故障注入指令，目标寄存器数量: {len(circuit.injection_reg)}")
    sim.write_fault_tcl(circuit.injection_reg)
    # 计算总故障点数量：每个寄存器 * 每个时序点
    total_faults = 0
    for reg in circuit.injection_reg:
        for i in range(config.end_time):
            t = config.clk_period / 2 + i * config.clk_period
            if t >= config.end_time - config.clk_period:
                break
            total_faults += 1
    
    # 启用进度监控线程
    monitor = LogMonitor(log_path, total_faults)
    monitor.start_monitoring()

    # 强制同步文件到磁盘
    import time
    time.sleep(1) 
    
    print(f"[INFO] 开始故障注入仿真 (预计运行 {total_faults} 个故障周期)...")
    if not sim.simulate():
        monitor.stop_monitoring()
        print(f"[ERROR] 故障仿真失败，详细日志请查阅: {log_path}")
        return
    
    # 停止监控
    monitor.stop_monitoring()
    
    # 检查 fault 仿真后是否出现 force/debug 相关错误（并给出修复建议）
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as _lf:
            _log_txt = _lf.read()
    except Exception:
        _log_txt = ''
    if any(p in _log_txt for p in ['Unable to force object', 'FORCE-NODBG', 'not compiled with the required debug capability']):
        print('\n[SIM][ERROR] 在 fault 注入阶段检测到 force/DEBUG 错误 — 这会阻止故障注入生效。')
        print('建议：在 config/config.json 中设置 vcs_debug_flags 并重新编译。')
        return

    print("[INFO] 仿真全部完成，正在分析结果...")
    circuit.get_fault()
    circuit.cal_result()
    # 成功完成仿真与结果计算后显式退出（返回码 0）——避免回到交互菜单
    sys.exit(0)


if __name__ == '__main__':
    start = timeit.default_timer()
    main()
    stop = timeit.default_timer()
    print('Time: ', stop - start)