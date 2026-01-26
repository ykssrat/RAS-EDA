# Python_FDR 项目使用说明与功能总结

## 项目概述

Python_FDR 是一个基于 Verilog 的数字电路设计与仿真项目，集成了硬件描述、C语言扩展功能和Python自动化控制的混合编程环境。该项目主要用于数字集成电路的功能验证和故障仿真。
vcs+verdi是目前市面上仿真最快的方式
## 资源需求
虚拟机：推荐使用vmware
仿真器：VCS2016
下载教程：https://blog.csdn.net/qiumingT/article/details/131700570

资源：通过网盘分享的文件：Synopsys
链接: https://pan.baidu.com/s/1pKsduApIso07RM5m3rbUpQ 提取码: dp5s
终端使用pip install -r py/requirements.txt可以一键快速安装依赖库
## 目录结构

```
Python_FDR/
├── circuit/                 # 数字电路设计文件目录
│   ├── Division.v           # 除法器模块
│   ├── Division_tb.v        # 除法器测试平台
│   ├── s27.v                # s27 基准电路
│   ├── s27_0.v              # s27 变体电路
│   ├── s27_tb.v             # s27 测试平台
│   ├── s382.v               # s382 基准电路
│   ├── s382_tb.v            # s382 测试平台
│   ├── stdcells.v           # 标准单元库定义
│   ├── tb.v                 # 通用测试平台
│   ├── test.v               # 测试文件
│   └── verilog_file.f       # Verilog 文件列表
├── clibrary/                # C语言库文件目录
│   ├── acc_user.h           # VPI访问用户头文件
│   ├── cJSON.c              # JSON解析C库实现
│   ├── cJSON.h              # JSON解析头文件
│   ├── function.c           # 功能函数实现
│   ├── main.c               # 主程序入口
│   ├── user.h               # 用户相关头文件
│   ├── vcs_acc_user.h       # VCS访问用户头文件
│   └── veriuser.h           # Verilog用户头文件
├── py/                      # Python脚本目录
│   ├── simulator.py         # 仿真控制脚本
│   └── test.py              # 测试脚本
├── Makefile                 # 构建配置文件
├── config/
│   └── config.json          # 配置文件
└── run.tcl                  # 运行脚本
```

## 核心组件说明

### 1. 电路设计文件 (circuit/)
- 包含标准基准电路s27和s382及其测试平台
- 提供除法器等算术逻辑单元的设计与验证
- `stdcells.v` 定义了标准单元库
- `verilog_file.f` 列出了所有需要编译的Verilog文件

### 2. C语言库 (clibrary/)
- 使用VPI(Verilog Procedural Interface)实现C语言与Verilog的交互
- `cJSON` 库用于JSON数据解析
- `main.c` 作为主程序入口点
- 提供用户自定义功能的接口支持

### 3. Python脚本 (py/)
- `simulator.py`: 仿真流程控制脚本
- `test.py`: 自动化测试脚本
- 实现高级自动化和数据分析功能

## 构建与运行流程

### 编译流程
```bash
make com
```
该命令会调用VCS编译器，根据Makefile中的配置编译所有Verilog文件和C语言源码。

### 仿真执行
```bash
make sim
```
运行仿真，执行run.tcl中定义的测试序列。

### 图形化波形查看
```bash
make wave
```
启动DVE图形界面查看仿真波形。

## 配置文件说明 (config.json)

```json
{
    "clk_name": "CK",              # 时钟信号名称
    "clk_period": 10,             # 时钟周期（ns）
    "end_time": 132,              # 仿真结束时间（ns）
    "circuit_info_file": "./output/circuit_info.json",  # 电路信息输出文件
    "golden_file": "./output/golden.json",              # 黄金参考输出文件
    "fault_file": "./output/fault.json",                # 故障信息输出文件
    "path": "/home/host/Documents/Python_FDR/",         # 项目路径
    "tcl_file": "./run.tcl"                            # TCL脚本路径
}
```

## TCL测试脚本分析 (run.tcl)

- 实现了系统级故障注入测试流程
- 对s27电路中的每个DFF触发器的Q输出进行故障模拟
- 每个故障测试包括：
  1. 重启仿真
  2. 调用`$runfault`函数注入特定故障
  3. 运行指定时间
  4. 将Q输出强制置为未知状态(x)
  5. 运行至绝对时间132ns
- 总共对3个DFF的12个输出状态进行故障覆盖率测试

## 使用建议

1. 修改设计后，应更新`verilog_file.f`中的文件列表
2. 调整仿真参数时，同步修改`config.json`和`run.tcl`
3. 新增测试用例时，可参考现有的TCL脚本格式
4. 输出数据将保存在`output/`目录下，便于后续分析