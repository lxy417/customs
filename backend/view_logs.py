#!/usr/bin/env python3
"""
日志查看工具
"""
import os
import sys
import time
from pathlib import Path
import argparse

def tail_file(filepath, lines=50):
    """显示文件的最后几行"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.readlines()
            for line in content[-lines:]:
                print(line.rstrip())
    except FileNotFoundError:
        print(f"日志文件不存在: {filepath}")
    except Exception as e:
        print(f"读取日志文件失败: {e}")

def follow_file(filepath):
    """实时跟踪文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # 移动到文件末尾
            f.seek(0, 2)
            print(f"正在监控日志文件: {filepath}")
            print("按 Ctrl+C 退出")
            print("-" * 50)
            
            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n监控已停止")
    except FileNotFoundError:
        print(f"日志文件不存在: {filepath}")
    except Exception as e:
        print(f"监控日志文件失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='日志查看工具')
    parser.add_argument('--file', '-f', default='logs/app.log', help='日志文件路径')
    parser.add_argument('--lines', '-n', type=int, default=50, help='显示最后几行')
    parser.add_argument('--follow', '-F', action='store_true', help='实时跟踪日志')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有日志文件')
    
    args = parser.parse_args()
    
    log_dir = Path('logs')
    
    if args.list:
        print("可用的日志文件:")
        if log_dir.exists():
            for log_file in log_dir.glob('*.log'):
                size = log_file.stat().st_size
                print(f"  {log_file.name} ({size} bytes)")
        else:
            print("  日志目录不存在")
        return
    
    log_file = Path(args.file)
    
    if args.follow:
        follow_file(log_file)
    else:
        tail_file(log_file, args.lines)

if __name__ == '__main__':
    main()