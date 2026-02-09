#!/usr/bin/env python3
"""
地层字典完整工作流管理器

整合地层提取、可视化编辑和JSON转换的完整工作流。
工作流步骤：
1. 从钻井数据中提取地层信息（stratigraphic_analysis.py）
2. 启动可视化编辑器进行地层编辑
3. 将编辑后的CSV转换为JSON字典（csv_to_json_converter.py）
"""

import argparse
import subprocess
import sys
import os
import glob
import json
import time
import signal
from pathlib import Path


def get_skill_root():
    """获取技能根目录"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 如果脚本在 .windsurf/skills/stratigraphic-dictionary/scripts/ 中
    if '.windsurf' in script_dir:
        skill_root = script_dir
        while not skill_root.endswith('stratigraphic-dictionary') and skill_root != '/':
            skill_root = os.path.dirname(skill_root)
        return skill_root if skill_root != '/' else None
    # 否则假设在项目的scripts目录中
    return os.path.dirname(script_dir)


def get_project_root():
    """获取项目根目录（当前工作目录）"""
    return os.getcwd()


def run_stratigraphic_analysis(data_file, stratigraphy_file, config_file=None, output_file='stratigraphic_depth_statistics.csv'):
    """
    步骤1：运行地层分析，从钻井数据中提取地层信息
    
    :param data_file: 钻井数据文件路径（如 CCQ_merged.csv）
    :param stratigraphy_file: 地层分层参考文件路径
    :param config_file: 可选的现有JSON配置文件路径
    :param output_file: 输出CSV文件路径
    :return: 生成的CSV文件路径
    """
    print("=" * 60)
    print("步骤 1/3: 提取地层数据")
    print("=" * 60)
    
    project_root = get_project_root()
    
    # 构建命令
    cmd = [
        sys.executable, 'stratigraphic_analysis.py',
        '-d', data_file,
        '-s', stratigraphy_file,
        '-o', output_file
    ]
    
    if config_file:
        cmd.extend(['-c', config_file])
    
    print(f"执行命令: {' '.join(cmd)}")
    print(f"工作目录: {project_root}")
    
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=False, text=True, check=True)
        print(f"\n地层数据提取完成: {output_file}")
        return os.path.join(project_root, output_file)
    except subprocess.CalledProcessError as e:
        print(f"错误：地层数据提取失败")
        print(f"返回码: {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"错误: 找不到 stratigraphic_analysis.py")
        print(f"请确保该文件位于项目根目录: {project_root}")
        sys.exit(1)


def start_visual_editor(data_file, stratigraphy_file, host='127.0.0.1', port=5000):
    """
    步骤2：启动可视化编辑器
    
    :param data_file: 预加载的地层数据文件路径
    :param stratigraphy_file: 地层分层参考文件路径
    :param host: 服务器地址
    :param port: 服务器端口
    :return: 服务器进程对象
    """
    print("\n" + "=" * 60)
    print("步骤 2/3: 启动可视化编辑器")
    print("=" * 60)
    
    skill_root = get_skill_root()
    project_root = get_project_root()
    
    if not skill_root:
        print("错误: 无法确定技能根目录")
        sys.exit(1)
    
    # 使用技能目录中的start_server.py
    server_script = os.path.join(skill_root, 'scripts', 'start_server.py')
    
    if not os.path.exists(server_script):
        print(f"错误: 找不到服务器脚本 {server_script}")
        sys.exit(1)
    
    # 构建命令 - 数据文件使用绝对路径
    data_file_abs = os.path.abspath(data_file)
    stratigraphy_file_abs = os.path.abspath(stratigraphy_file)
    
    cmd = [
        sys.executable, server_script,
        '-d', data_file_abs,
        '-m', stratigraphy_file_abs,
        '--host', host,
        '--port', str(port)
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print(f"工作目录: {project_root}")
    print(f"\n服务器启动中...")
    print(f"请在浏览器中访问: http://{host}:{port}")
    print(f"\n请在可视化编辑器中完成地层编辑，然后点击'导出数据'按钮")
    print(f"导出的文件将保存在: {os.path.join(project_root, 'uploads')}")
    print("\n完成编辑后，按 Ctrl+C 结束服务器并继续...")
    print("-" * 60)
    
    try:
        # 启动服务器进程
        process = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 实时输出服务器日志
        try:
            for line in process.stdout:
                print(line, end='')
        except KeyboardInterrupt:
            print("\n\n检测到中断信号，正在关闭服务器...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print("服务器已关闭")
        
        return process
    except Exception as e:
        print(f"错误: 启动服务器失败 - {e}")
        sys.exit(1)


def convert_csv_to_json(csv_file=None, config_file=None, output_name='stratigraphic_dictionary.json'):
    """
    步骤3：将CSV转换为JSON字典
    
    :param csv_file: CSV文件路径（如未指定，自动查找uploads目录中最新的_verification.csv）
    :param config_file: 可选的现有JSON配置文件路径
    :param output_name: 输出JSON文件名
    :return: 生成的JSON文件路径
    """
    print("\n" + "=" * 60)
    print("步骤 3/3: 转换为JSON字典")
    print("=" * 60)
    
    project_root = get_project_root()
    uploads_dir = os.path.join(project_root, 'uploads')
    
    # 如果未指定CSV文件，自动查找uploads目录中最新的_verification.csv
    if not csv_file:
        if not os.path.exists(uploads_dir):
            print(f"错误: uploads目录不存在: {uploads_dir}")
            print("请先在可视化编辑器中导出数据")
            sys.exit(1)
        
        # 查找所有_verification.csv文件
        verification_files = glob.glob(os.path.join(uploads_dir, '*_verification.csv'))
        
        if not verification_files:
            print(f"错误: 在 {uploads_dir} 中找不到 *_verification.csv 文件")
            print("请先在可视化编辑器中导出数据")
            sys.exit(1)
        
        # 按修改时间排序，取最新的
        verification_files.sort(key=os.path.getmtime, reverse=True)
        csv_file = verification_files[0]
        print(f"自动选择最新的导出文件: {os.path.basename(csv_file)}")
    
    if not os.path.exists(csv_file):
        print(f"错误: CSV文件不存在: {csv_file}")
        sys.exit(1)
    
    output_file = os.path.join(project_root, output_name)
    
    # 构建命令
    cmd = [
        sys.executable, 'csv_to_json_converter.py',
        '-d', csv_file,
        '-u'  # 默认以字典为准，只添加新项
    ]
    
    if config_file:
        cmd.extend(['-c', config_file])
    
    print(f"执行命令: {' '.join(cmd)}")
    print(f"输出文件: {output_file}")
    
    try:
        # 执行转换
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 从输出中提取JSON - 找到最外层的花括号包裹的内容
        output = result.stdout
        json_start = output.find('{')
        json_end = output.rfind('}')
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = output[json_start:json_end + 1]
            data = json.loads(json_str)
            # 保存到根目录
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\nJSON字典已保存: {output_file}")
            print(f"共 {len(data)} 条地层记录")
            return output_file
        else:
            print("警告: 无法从输出中解析JSON数据")
            print("原始输出:")
            print(result.stdout)
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"错误：CSV转换失败")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"错误: 找不到 csv_to_json_converter.py")
        print(f"请确保该文件位于项目根目录: {project_root}")
        sys.exit(1)


def run_full_workflow(args):
    """运行完整工作流"""
    print("\n" + "=" * 70)
    print("地层分层字典完整工作流")
    print("=" * 70)
    print("\n此工作流将:")
    print("1. 从钻井数据中提取地层信息")
    print("2. 启动可视化编辑器进行地层编辑")
    print("3. 将编辑后的数据转换为JSON字典")
    print()
    
    # 步骤1：提取地层数据
    analysis_output = run_stratigraphic_analysis(
        args.data_file,
        args.stratigraphy_file,
        args.config_file,
        args.analysis_output
    )
    
    # 步骤2：启动可视化编辑器（阻塞直到用户中断）
    start_visual_editor(
        analysis_output,
        args.stratigraphy_file,
        args.host,
        args.port
    )
    
    # 步骤3：转换为JSON
    json_output = convert_csv_to_json(
        csv_file=None,  # 自动查找最新的导出文件
        config_file=args.config_file,
        output_name=args.json_output
    )
    
    print("\n" + "=" * 70)
    print("工作流完成！")
    print("=" * 70)
    print(f"生成的文件:")
    print(f"  - 地层统计数据: {args.analysis_output}")
    print(f"  - 编辑后的CSV: uploads/*_verification.csv")
    print(f"  - JSON字典: {args.json_output}")
    print()


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='地层分层字典完整工作流',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 完整工作流（推荐）
  python workflow_manager.py -d "CCQ_merged.csv" -m "地层分层.csv"
  
  # 使用现有配置更新字典
  python workflow_manager.py -d "CCQ_merged.csv" -m "地层分层.csv" -c "stratigraphic_dictionary.json"
  
  # 指定输出文件名
  python workflow_manager.py -d "CCQ_merged.csv" -m "地层分层.csv" --json-output "my_dict.json"

工作流步骤:
  1. 从钻井数据中提取地层深度统计信息
  2. 启动可视化编辑器，用户可以拖拽调整地层边界
  3. 导出编辑后的数据，自动转换为JSON字典
        """
    )
    
    # 子命令模式
    subparsers = parser.add_subparsers(dest='command', help='可用子命令')
    
    # extract 子命令 - 仅提取地层数据
    extract_parser = subparsers.add_parser('extract', help='仅执行地层数据提取')
    extract_parser.add_argument('-d', '--data-file', type=str, required=True, help='钻井数据文件路径')
    extract_parser.add_argument('-s', '--stratigraphy-file', type=str, required=True, help='地层分层参考文件路径')
    extract_parser.add_argument('-c', '--config-file', type=str, help='现有JSON配置文件路径')
    extract_parser.add_argument('-o', '--output', type=str, default='stratigraphic_depth_statistics.csv', help='输出CSV文件名')
    
    # convert 子命令 - 仅转换CSV到JSON
    convert_parser = subparsers.add_parser('convert', help='仅执行CSV到JSON转换')
    convert_parser.add_argument('-f', '--csv-file', type=str,
                                help='CSV文件路径（如不指定，自动查找uploads目录中最新的导出文件）')
    convert_parser.add_argument('-c', '--config-file', type=str, help='现有JSON配置文件路径')
    convert_parser.add_argument('-o', '--output', type=str, default='stratigraphic_dictionary.json', help='输出JSON文件名')
    
    # 完整工作流参数（只在不使用子命令时使用）
    parser.add_argument('-d', '--data-file', type=str, help='钻井数据文件路径 (如: CCQ_merged.csv)')
    parser.add_argument('-m', '--stratigraphy-file', type=str, help='地层分层参考文件路径 (如: 地层分层.csv)')
    parser.add_argument('-c', '--config-file', type=str, help='可选的现有JSON配置文件路径')
    parser.add_argument('--analysis-output', type=str, default='stratigraphic_depth_statistics.csv',
                        help='地层分析输出文件名 (默认: stratigraphic_depth_statistics.csv)')
    parser.add_argument('--json-output', type=str, default='stratigraphic_dictionary.json',
                        help='JSON字典输出文件名 (默认: stratigraphic_dictionary.json)')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='可视化编辑器服务器地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                        help='可视化编辑器服务器端口 (默认: 5000)')
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    # 检查是否为子命令模式
    if args.command == 'extract':
        # 仅执行提取
        run_stratigraphic_analysis(
            args.data_file,
            args.stratigraphy_file,
            args.config_file,
            args.output
        )
    elif args.command == 'convert':
        # 仅执行转换
        convert_csv_to_json(
            args.csv_file,
            args.config_file,
            args.output
        )
    else:
        # 完整工作流 - 验证必需参数
        if not args.data_file or not args.stratigraphy_file:
            print("错误: 完整工作流需要提供 -d 和 -m 参数")
            print("用法: python workflow_manager.py -d <数据文件> -m <地层分层文件>")
            sys.exit(1)
        # 完整工作流
        run_full_workflow(args)
