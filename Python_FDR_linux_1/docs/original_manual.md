# SER抗辐照分析工具使用说明书 (Legacy)

## 1. 项目简介
本项目是一套基于仿真的软错误率（Soft Error Rate, SER）分析工具。它通过控制 EDA 仿真工具（如 VCS 或 ModelSim），对数字电路进行故障注入（Fault Injection），并统计故障检测率（FDR, Fault Detection Rate）。

**核心功能：**
*   **Golden Run**：执行无故障仿真，获取标准输出。
*   **Fault Injection**：在指定时刻向指定寄存器注入翻转故障（Bit Flip）。
*   **FDR 计算**：对比故障仿真与 Golden 结果，分类统计故障影响（被掩盖、被检测、潜在故障）。

## 2. 环境配置

### 2.1 软件依赖
*   **操作系统**：Linux (推荐，因为依赖 `make` 和 EDA 工具) 或 Windows (需配置 Cygwin/MinGW)。
*   **Python 版本**：3.x
*   **Python 库**：
    *   `pprint` (内置)
    *   `json` (内置)
    *   `timeit` (内置)
    *   `timeout_decorator` (仅 `test.py` 需要，用于超时控制)
*   **外部工具**：
    *   `make`：用于构建仿真工程。
    *   **仿真器**：VCS (Synopsys) 或 ModelSim/Questasim (Siemens)，需在 `Makefile` 中配置。

## 3. 文件结构说明

| 文件路径 | 说明 |
| :--- | :--- |
| `src_legacy/simulator.py` | **核心主程序**。负责读取配置、生成 TCL 脚本、调用仿真器、解析结果并计算 FDR。 |
| `src_legacy/test.py` | **测试脚本**。包含一个带超时控制的函数示例，可能用于测试仿真器的挂起处理。 |
| `config.json` | **配置文件**。定义电路路径、时钟、仿真时间等关键参数。 |

## 4. 配置文件详解 (config.json)
运行前必须在项目根目录或指定位置创建 `config.json`。

```json
{
  "clk_name": "CK",             // 时钟信号名称
  "clk_period": 10,             // 时钟周期 (ns)
  "end_time": 1000,             // 仿真总时长 (ns)
  "circuit_info_file": "info.json", // 电路信息文件 (包含寄存器列表等)
  "golden_file": "golden.json", // Golden Run 结果输出文件
  "fault_file": "fault.json",   // 故障仿真结果输出文件
  "path": "../circuit/s382",    // 仿真工作目录 (包含 Makefile 和 Verilog)
  "tcl_file": "run.tcl"         // 生成的 TCL 脚本文件名
}
```

## 5. 核心模块解析

### 5.1 Config 类
*   **功能**：解析 `config.json`，将参数加载到内存。

### 5.2 CircuitInfo 类
*   **功能**：管理电路的拓扑和仿真结果。
*   **关键方法**：
    *   `get_circuit_info()`: 读取电路的寄存器列表 (`injection_reg`) 和输出端口 (`out_port`)。
    *   `cal_result()`: **核心算法**。对比 Golden 和 Fault 结果，计算 FDR。
        *   **Error (1)**: 输出端口值与 Golden 不一致（故障被检测）。
        *   **Correct (0)**: 输出一致，且内部状态也一致（故障被掩盖）。
        *   **Hide (-1)**: 输出一致，但内部状态不一致（潜在故障 Latent Fault）。

### 5.3 Simulator 类
*   **功能**：驱动外部仿真流程。
*   **关键方法**：
    *   `write_golden_tcl()`: 生成用于 Golden Run 的 TCL 脚本。
    *   `write_fault_tcl()`: 生成用于故障注入的 TCL 脚本。它会遍历所有注入寄存器，在每个时钟周期生成一个故障注入命令 (`force ... -deposit`)。
    *   `simulate()`: 调用 `os.system('make sim')` 执行仿真。

## 6. 运行指南

### 步骤 1: 准备仿真环境
确保 `path` 指定的目录下包含：
1.  电路源码 (`.v`)。
2.  `Makefile`：必须包含 `com` (编译), `sim` (仿真), `clean` (清理) 三个目标。
3.  `info.json`：描述电路结构的辅助文件。

### 步骤 2: 执行分析
在终端中运行：
```bash
python src_legacy/simulator.py
```

### 步骤 3: 查看结果
程序运行结束后，控制台会打印每个寄存器的 FDR 统计信息：
```python
{
 'DFF_0': {'FDR': 0.15, 'correct': 80, 'error': 15, 'hide': 5},
 ...
}
```
