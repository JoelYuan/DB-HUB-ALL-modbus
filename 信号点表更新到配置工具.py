#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置更新工具
用于从CSV或XLSX文件更新config.yaml中的设备配置
"""

import yaml
import pandas as pd
import argparse
import os

def read_config(config_path):
    """读取配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def write_config(config_path, config_data):
    """写入配置文件"""# 写入配置文件 - 确保格式与原始配置一致
    with open(config_path, 'w', encoding='utf-8') as f:
        # 先写入全局配置部分
        f.write("global:\n")
        for key, value in config_data['global'].items():
            f.write(f"  {key}: {value}\n")
        
        f.write("\ndevices:\n")
        
        # 遍历设备列表
        for device in config_data['devices']:
            f.write("  - name: {}\n".format(device['name']))
            f.write("    type: {}\n".format(device['type']))
            
            # 根据设备类型写入不同的配置项
            if device['type'] == 'rtu':
                f.write("    port: {}\n".format(device['port']))
                f.write("    baud: {}\n".format(device['baud']))
                f.write("    slave: {}\n".format(device['slave']))
            elif device['type'] == 'tcp':
                f.write("    address: {}\n".format(device['address']))
                f.write("    unit: {}\n".format(device['unit']))
            
            # 写入read操作
            if 'read' in device:
                f.write("    read:\n")
                for op in device['read']:
                    f.write("      - fc: {}\n".format(op['fc']))
                    f.write("        addr: {}\n".format(op['addr']))
                    f.write("        tag: {}\n".format(op['tag']))
                    f.write("        period_ms: {}\n".format(op['period_ms']))
            
            # 写入write操作
            if 'write' in device:
                f.write("    write:\n")
                for op in device['write']:
                    f.write("      - fc: {}\n".format(op['fc']))
                    f.write("        addr: {}\n".format(op['addr']))
                    f.write("        tag: {}\n".format(op['tag']))
            
            f.write("\n")

def read_signal_points(file_path):
    """读取信号点表文件"""
    # 根据文件扩展名选择读取方式
    _, ext = os.path.splitext(file_path)
    
    if ext.lower() == '.csv':
        df = pd.read_csv(file_path, encoding='utf-8')
    elif ext.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")
    
    # 处理空值
    df = df.fillna('')
    
    return df

def parse_modbus_address(register_address, operation_type):
    """
    解析Modbus寄存器地址并确定功能码
    - 0XXXX区 DO线圈 ：FC1(读) + FC5(写)
    - 1XXXX区 DI离散输入 ：FC2(读)
    - 4XXXX区 AO保持寄存器 ：FC3(读) + FC6(写) + FC16(批量写)
    - 3XXXX区 AI输入寄存器 ：FC4(读)
    """
    # 确保是字符串格式
    reg_str = str(register_address).zfill(5)
    reg_prefix = reg_str[0]
    reg_offset = int(reg_str[1:])
    
    # 根据寄存器地址和操作类型确定功能码
    if reg_prefix == '0':
        # Coils (DO) 0XXXX区
        if operation_type == 'read':
            fc = 1
        else:  # write
            fc = 5
    elif reg_prefix == '1':
        # Discrete Inputs (DI) 1XXXX区
        if operation_type == 'read':
            fc = 2
        else:
            raise ValueError(f"离散输入(DI)不支持写操作: {register_address}")
    elif reg_prefix == '3':
        # Input Registers (AI) 3XXXX区
        if operation_type == 'read':
            fc = 4
        else:
            raise ValueError(f"输入寄存器(AI)不支持写操作: {register_address}")
    elif reg_prefix == '4':
        # Holding Registers (AO) 4XXXX区
        if operation_type == 'read':
            fc = 3
        else:  # write
            fc = 6
    else:
        raise ValueError(f"不支持的寄存器地址格式: {register_address}")
    
    return fc, reg_offset

def update_config_from_dataframe(config_data, df):
    """从DataFrame更新配置数据"""
    # 按设备名称分组处理
    device_groups = df.groupby('设备名称')
    
    # 清空现有的设备列表
    config_data['devices'] = []
    
    for device_name, device_df in device_groups:
        # 创建设备基础配置
        device_config = {
            'name': device_name
        }
        
        # 获取设备类型
        device_type = device_df['设备类型'].iloc[0]
        device_config['type'] = device_type
        
        if device_type == 'rtu':
            # RTU设备配置
            device_config['port'] = device_df['COM端口'].iloc[0]
            baud_value = device_df['波特率'].iloc[0]
            device_config['baud'] = int(baud_value) if baud_value != '' else 9600
            slave_value = device_df['从站地址'].iloc[0]
            device_config['slave'] = int(slave_value) if slave_value != '' else 1
        elif device_type == 'tcp':
            # TCP设备配置
            ip_address = device_df['IP地址'].iloc[0]
            port_value = device_df['端口'].iloc[0]
            port = int(port_value) if port_value != '' else 502
            device_config['address'] = f"{ip_address}:{port}"
            # 处理TCP设备的从站地址（unit）
            unit_value = device_df['从站地址'].iloc[0]
            if unit_value != '' and pd.notna(unit_value):
                device_config['unit'] = int(unit_value)
            else:
                device_config['unit'] = 1
        
        # 处理读操作
        read_ops = []
        write_ops = []
        
        for index, row in device_df.iterrows():
            try:
                # 获取寄存器地址和操作类型
                register_address = row['寄存器地址']
                operation_type = row['操作类型']
                
                # 解析Modbus地址获取功能码和实际偏移地址
                fc, addr = parse_modbus_address(register_address, operation_type)
            except Exception as e:
                raise ValueError(f"处理行 {index} 错误: {e}") from e
            
            # 创建操作配置
            op_config = {
                'fc': fc,
                'addr': addr,
                'tag': row['数据标签名']
            }
            
            if operation_type == 'read':
                # 处理读取周期
                period_value = row['读取周期']
                if period_value != '' and pd.notna(period_value):
                    op_config['period_ms'] = int(period_value)
                else:
                    op_config['period_ms'] = 500  # 默认读取周期
                read_ops.append(op_config)
            elif operation_type == 'write':
                write_ops.append(op_config)
        
        # 添加读写操作配置
        if read_ops:
            device_config['read'] = read_ops
        if write_ops:
            device_config['write'] = write_ops
        
        # 添加设备到配置
        config_data['devices'].append(device_config)
    
    return config_data

def main():
    """主函数"""
    # 固定配置文件路径
    config_path = 'config.yaml'
    
    # 自动检测信号点表文件，优先使用CSV格式
    signal_files = ['信号点表.csv', '信号点表.xlsx']
    input_file = None
    
    for file in signal_files:
        if os.path.exists(file):
            input_file = file
            break
    
    if not input_file:
        print("错误: 未找到信号点表文件（信号点表.csv 或 信号点表.xlsx）")
        return 1
    
    try:
        # 读取配置文件
        print(f"读取配置文件: {config_path}")
        config_data = read_config(config_path)
        
        # 读取信号点表
        print(f"读取信号点表: {input_file}")
        df = read_signal_points(input_file)
        
        # 更新配置
        print("更新配置...")
        updated_config = update_config_from_dataframe(config_data, df)
        
        # 写入配置文件（覆盖）
        write_config(config_path, updated_config)
        print(f"配置已更新并保存到: {config_path}")
        
    except Exception as e:
        print(f"错误: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())