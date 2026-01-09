# FM 算法电路分割规则

本规则定义了 AI 在执行 FM (Fiduccia-Mattheyses) 算法进行电路分割及生成 Verilog 代码时必须遵循的规范。

## 1. 核心行为准则
*   **被动执行**：AI 不得主动运行代码或终端命令，仅提供代码修改建议或操作指引。
*   **禁止执行**：严禁使用 `run_in_terminal` 等工具直接运行分割脚本。
*   **备份命名**：修改文件时若需备份，统一使用 `_1`, `_2` 等数字后缀。

## 2. 信号流向与端口生成规则
在将原电路分割为 A、B 两个分区（Partition）时，遵循以下规则：

### 2.1 原电路端口 (PI/PO)
*   **输入 (PI)**：
    *   默认分配给 A 区。
    *   若 B 区实例也使用了该输入，则 B 区也需声明为 `input`。
*   **输出 (PO)**：
    *   归属于**驱动该信号的实例**所在的分区。

### 2.2 割线 (Cut Net) 处理
连接 A 区与 B 区的内部信号定义为割线，处理规则如下：
*   **方向判定**：
    *   **A $\to$ B**：源实例在 A 区 $\Rightarrow$ A 区声明 `output`，B 区声明 `input`。
    *   **B $\to$ A**：源实例在 B 区 $\Rightarrow$ B 区声明 `output`，A 区声明 `input`。
*   **命名规范**：
    *   端口名必须添加 `cut_` 前缀（例如 `cut_n10`）。
    *   内部信号保持原名，通过 `assign` 语句连接端口与内部信号。
    *   **示例**：`assign n10 = cut_n10;` （用于接收端）或 `assign cut_n10 = n10;` （用于发送端）。

### 2.3 端口列表完备性
生成的 Verilog 模块端口列表必须包含：
1.  本分区使用的原电路 PI。
2.  本分区产生的原电路 PO。
3.  所有进出本分区的 `cut_` 信号。

## 3. 代码格式规范
*   **声明格式**：生成的 Verilog 文件中，所有 `input` 声明必须合并在一行，所有 `output` 声明必须合并在一行。
*   **语法合规**：生成的代码必须严格符合 IEEE Verilog 标准（如模块实例化语法）。

## 4. 工具链与运行说明
项目包含三个核心 Python 脚本，位于 `py/` 目录下：

| 脚本 | 功能 | 独立运行命令 |
| :--- | :--- | :--- |
| `FM_part.py` | 执行 FM 算法，生成 `.graphml` 分割图 | `python py/FM_part.py <电路名>` |
| `G_to_v.py` | 解析 `.graphml`，生成 Verilog (`_a.v`, `_b.v`) | `python py/G_to_v.py <电路名>` |
| `window.py` | 交互式主程序，集成上述功能 | `python py/window.py` |

**示例流程 (s27 电路)**：
1.  运行 `python py/window.py`。
2.  输入 `s27` 进行分割 $\to$ 生成 `output/s27_cut.graphml`。
3.  再次输入 `s27` 生成 Verilog $\to$ 生成 `output/s27_a.v` 和 `output/s27_b.v`。
