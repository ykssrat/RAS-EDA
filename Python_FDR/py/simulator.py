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
        self.vcs_command = 'vcs'
        self.env_setup = ''

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
            if not os.path.isabs(self.path):
                # 将相对路径转换为基于配置文件所在目录的绝对路径
                # config.json 在 config/ 文件夹下，所以其父目录是项目根目录
                base_dir = os.path.dirname(os.path.abspath(self.config_file))
                self.path = os.path.abspath(os.path.join(base_dir, '..', self.path))
            self.tcl_file = js['tcl_file']
            self.vcs_command = js.get('vcs_command', 'vcs')
            self.env_setup = js.get('env_setup', '')

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
        # 确保 output 目录存在
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, 'vcs_run.log')
        cmd = f'make com VCS_CMD={self.vcs_command} > {log_path} 2>&1'
        if self.env_setup:
            cmd = f'{self.env_setup} && {cmd}'
        full_cmd = f"bash -c '{cmd}'"
        print(f"Executing: {full_cmd}")
        result = os.system(full_cmd)
        if result != 0:
            print(f"Error: Compilation failed with exit code {result}. See log: {log_path}")
            return False
        return True

    def simulate(self):
        os.chdir(self.path)
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, 'vcs_run.log')
        cmd = f'make sim >> {log_path} 2>&1'
        if self.env_setup:
            cmd = f'{self.env_setup} && {cmd}'
        full_cmd = f"bash -c '{cmd}'"
        print(f"Executing: {full_cmd}")
        result = os.system(full_cmd)
        if result != 0:
            print(f"Error: Simulation failed with exit code {result}. See log: {log_path}")
            return False
        return True

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


def main():
    # 获取脚本所在目录，确保无论在哪启动都能找到配置文件
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
    if not sim.simulate():
        print(f"[ERROR] 详细日志请查阅: {log_path}")
        return
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


if __name__ == '__main__':
    start = timeit.default_timer()
    main()
    stop = timeit.default_timer()
    print('Time: ', stop - start)