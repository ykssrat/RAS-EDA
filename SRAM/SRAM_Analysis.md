# SRAM Radiation Analysis System

## 项目简介
本目录包含了针对 SRAM（静态随机存取存储器）电路的辐照效应分析相关设计与仿真文件。它是 **RAS-EDA** (Reliability & Radiation Analysis System for EDA) 项目的重要组成部分，专注于评估和增强存储器在辐射环境下的可靠性。

## 目录结构说明
本项目基于 Cadence Virtuoso 格式组织，主要包含以下关键模块：

### 核心位线单元 (Core Cells)
- **6T#2dSRAM**: 标准 6 管 SRAM 单元。
- **10T#2dSRAM / 12T#2dSRAM**: 增强型（加固版）多管 SRAM 单元设计，用于提高抗辐照能力。
- **SRAM_Cell**: 基础存储单元及其测试平台 (`SRAM_Cell_TB`, `SRAM_Cell_TB2`)。

### 辅助电路 (Peripheral Circuits)
- **译码器 (Decoders)**: 包含 `2_4_decoder` 和 `5_32_decoder`。
- **感测放大器 (Sense Amplifiers)**: `Sense`, `data_Sense`, `mac_Sense` 及其相应的测试平台。
- **预充与控制电路**: `Precharge`, `Inout_contrl`, `TG` (传输门)。
- **逻辑门与触发器**: `Inv` (反相器), `Nand`, `And`, `D_trigger` 等。

### 加固设计 (Hardening Designs)
- **Inv_Harden / Harden_Inv**: 经过加固处理的反相器设计。
- **6T#2dSRAM_Harden**: 针对辐照环境优化的标准单元加固。

## 仿真与分析服务
1. **电路提取**: 支持从 `schematic` 提取网表用于后续分析。
2. **可靠性评估**: 结合 Python 脚本（位于根目录 `py/`）进行瞬态辐射脉冲模拟及比特翻转（SEU）概率计算。
3. **性能对比**: 对比标准单元与加固单元在不同辐照强度下的稳定度。

## 使用指南
- 确保已正确配置 Cadence 环境并引用 `cds.lib`。
- 大部分模块包含 `spectre_state1` 仿真状态，可直接加载进行基准测试。
- 相关 Python 自动化分析流程请参考根目录下的 `docs/` 文件夹。
