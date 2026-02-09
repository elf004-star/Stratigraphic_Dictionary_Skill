#!/usr/bin/env python3
"""
地层分层字典可视化编辑工具 - Flask服务器

此脚本启动地层分层字典的Web服务，支持数据预加载和可视化编辑。
脚本路径相对于技能根目录运行，确保跨平台兼容性。
"""

from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import os
import json
import webbrowser
import threading
import time
import argparse
from werkzeug.utils import secure_filename

# 确定技能根目录（脚本位于 scripts/ 子目录中）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
ASSETS_DIR = os.path.join(SKILL_ROOT, 'assets')

# uploads目录：优先使用当前工作目录下的uploads，便于用户访问
UPLOADS_DIR = os.path.join(os.getcwd(), 'uploads')

# 初始化Flask应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOADS_DIR
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """提供主页面"""
    return send_from_directory(ASSETS_DIR, 'stratigraphic_visualizer.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    return send_from_directory(ASSETS_DIR, filename)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        # 如果有预加载数据，直接返回
        if PRELOADED_DATA:
            file_strat_list = [item['所属层位'] for item in PRELOADED_DATA]
            
            # 整合地层顺序：使用预设顺序（如果存在），并补充文件中出现但不在预设顺序中的层位
            if STRATIGRAPHY_ORDER:
                final_strat_list = list(STRATIGRAPHY_ORDER)
                for strat in file_strat_list:
                    if strat not in final_strat_list:
                        final_strat_list.append(strat)
            else:
                final_strat_list = file_strat_list

            stratigraphy_data = [{'地层信息': name, '序号': i+1} for i, name in enumerate(final_strat_list)]

            return jsonify({
                'success': True,
                'data': PRELOADED_DATA,
                'stratigraphy': stratigraphy_data,
                'reference_order': STRATIGRAPHY_ORDER,
                'filename': PRELOADED_FILENAME,
                'record_count': len(PRELOADED_DATA),
                'preloaded': True
            })
        
        # 否则处理上传的文件
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 读取CSV文件
            df = pd.read_csv(filepath, encoding='utf-8-sig')
            
            # 验证必要的列是否存在
            required_columns = ['地层名称', '所属层位', '顶界所处位置（0~1）', '底界所处位置（0~1）']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return jsonify({'error': f'Missing required columns: {missing_columns}'}), 400
            
            # 将数据转换为字典格式返回
            data = df.to_dict('records')
            
            # 获取唯一层位信息用于构建层级结构
            file_strat_list = df['所属层位'].drop_duplicates().tolist()

            # 整合地层顺序：使用预设顺序（如果存在），并补充文件中出现但不在预设顺序中的层位
            if STRATIGRAPHY_ORDER:
                final_strat_list = list(STRATIGRAPHY_ORDER)
                for strat in file_strat_list:
                    if strat not in final_strat_list:
                        final_strat_list.append(strat)
            else:
                final_strat_list = file_strat_list

            stratigraphy_data = [{'地层信息': name, '序号': i+1} for i, name in enumerate(final_strat_list)]

            return jsonify({
                'success': True,
                'data': data,
                'stratigraphy': stratigraphy_data,
                'reference_order': STRATIGRAPHY_ORDER,
                'filename': filename,
                'record_count': len(data),
                'preloaded': False
            })
        else:
            return jsonify({'error': 'Invalid file type. Only CSV files are allowed.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_data():
    try:
        data = request.json.get('data', [])
        original_filename = request.json.get('original_filename', '')
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 将数据转换为DataFrame
        df = pd.DataFrame(data)
        
        # 确保列按指定顺序排列：地层名称，所属层位，顶界所处位置（0~1），底界所处位置（0~1）
        required_columns = ['地层名称', '所属层位', '顶界所处位置（0~1）', '底界所处位置（0~1）']
        
        # 检查DataFrame是否包含所需的所有列
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing required columns: {missing_columns}'}), 400
        
        # 只选择并重新排序所需的列
        df = df[required_columns]
        
        # 对数值列进行格式化，保留两位小数
        numeric_columns = ['顶界所处位置（0~1）', '底界所处位置（0~1）']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        # 生成导出文件名：原文件名加verification后缀
        if original_filename:
            # 移除原文件的扩展名
            name_without_ext = os.path.splitext(original_filename)[0]
            export_filename = f"{name_without_ext}_verification.csv"
        else:
            # 如果没有原文件名，使用默认名称
            export_filename = "export_verification.csv"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], export_filename)
        
        # 保存为CSV文件
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'success': True,
            'filename': export_filename,
            'download_url': f'/download/{export_filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# 全局变量存储预加载数据
PRELOADED_DATA = None
PRELOADED_FILENAME = None

# 地层分层参考数据（默认为空，通过命令行参数加载）
STRATIGRAPHY_ORDER = []

def resolve_path(filepath):
    """
    解析文件路径，支持相对路径和绝对路径
    
    规则：
    - 绝对路径直接使用
    - 相对路径基于当前工作目录解析
    """
    if not filepath:
        return None
    
    if os.path.isabs(filepath):
        return filepath
    
    # 相对路径：基于当前工作目录
    return os.path.join(os.getcwd(), filepath)


def load_stratigraphy_reference(filepath):
    """加载地层分层参考文件"""
    global STRATIGRAPHY_ORDER
    
    filepath = resolve_path(filepath)
    
    if not filepath or not os.path.exists(filepath):
        print(f"❌ 地层分层参考文件不存在: {filepath}")
        return False
    
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        
        # 验证必要的列是否存在
        required_column = '地层信息'
        if required_column not in df.columns:
            print(f"❌ 文件缺少必要列: {required_column}")
            return False
        
        STRATIGRAPHY_ORDER = df[required_column].tolist()
        print(f"✅ 已加载地层分层参考文件: {os.path.basename(filepath)} ({len(STRATIGRAPHY_ORDER)} 个地层)")
        return True
        
    except Exception as e:
        print(f"❌ 加载地层分层参考文件失败: {e}")
        return False

def preload_data(filepath):
    """预加载地层数据文件"""
    global PRELOADED_DATA, PRELOADED_FILENAME
    
    filepath = resolve_path(filepath)
    
    if not filepath or not os.path.exists(filepath):
        print(f"❌ 数据文件不存在: {filepath}")
        return False
    
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        
        # 验证必要的列是否存在
        required_columns = ['地层名称', '所属层位', '顶界所处位置（0~1）', '底界所处位置（0~1）']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ 文件缺少必要列: {missing_columns}")
            return False
        
        # 将数据转换为字典格式
        PRELOADED_DATA = df.to_dict('records')
        PRELOADED_FILENAME = os.path.basename(filepath)
        
        print(f"✅ 已预加载数据文件: {PRELOADED_FILENAME} ({len(PRELOADED_DATA)} 条记录)")
        return True
        
    except Exception as e:
        print(f"❌ 加载数据文件失败: {e}")
        return False

def reorder_stratigraphy_by_reference(stratigraphy_list, reference_order=STRATIGRAPHY_ORDER):
    """
    根据参考顺序重新排列地层列表
    """
    if not reference_order:
        return stratigraphy_list
    
    # 创建一个字典，用于快速查找参考顺序中的索引
    order_map = {item: idx for idx, item in enumerate(reference_order)}
    
    # 分离在参考顺序中存在的和不存在的地层
    in_reference = []
    not_in_reference = []
    
    for item in stratigraphy_list:
        if item in order_map:
            in_reference.append((order_map[item], item))
        else:
            not_in_reference.append(item)
    
    # 按照参考顺序对存在的地层排序
    in_reference.sort(key=lambda x: x[0])
    in_reference = [item[1] for item in in_reference]
    
    # 合并结果：参考顺序中的地层 + 不在参考顺序中的地层
    result = in_reference + not_in_reference
    
    return result

@app.route('/api/process', methods=['POST'])
def process_stratigraphy():
    """处理地层数据，返回层级结构"""
    try:
        data = request.json.get('data', [])
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 构建层级结构
        hierarchy = {}
        if '所属层位' in df.columns and '地层名称' in df.columns:
            hierarchy = df.groupby('所属层位')['地层名称'].apply(list).to_dict()
        
        # 获取所有唯一的地层名称及它们的颜色
        formations = df['地层名称'].drop_duplicates().tolist()
        
        # 获取唯一层位信息并根据参考顺序重新排列
        stratigraphy_list = df['所属层位'].drop_duplicates().tolist()
        ordered_stratigraphy_list = reorder_stratigraphy_by_reference(stratigraphy_list)
        
        return jsonify({
            'success': True,
            'hierarchy': hierarchy,
            'formations': formations,
            'stratigraphy_list': ordered_stratigraphy_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load_stratigraphy_order', methods=['GET'])
def load_stratigraphy_order():
    """获取预设的地层顺序"""
    try:
        return jsonify({
            'success': True,
            'stratigraphy_order': STRATIGRAPHY_ORDER
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload_stratigraphy_reference', methods=['POST'])
def upload_stratigraphy_reference():
    """上传地层分层参考文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 读取CSV文件
            df = pd.read_csv(filepath, encoding='utf-8-sig')
            
            # 验证必要的列是否存在
            required_column = '地层信息'
            if required_column not in df.columns:
                return jsonify({'error': f'Missing required column: {required_column}'}), 400
            
            # 更新全局地层顺序
            global STRATIGRAPHY_ORDER
            STRATIGRAPHY_ORDER = df[required_column].tolist()
            
            return jsonify({
                'success': True,
                'message': '地层分层参考文件上传成功',
                'stratigraphy_order': STRATIGRAPHY_ORDER,
                'record_count': len(STRATIGRAPHY_ORDER)
            })
        else:
            return jsonify({'error': 'Invalid file type. Only CSV files are allowed.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def open_browser():
    """延迟打开浏览器"""
    time.sleep(1.5)  # 等待服务器启动
    webbrowser.open('http://127.0.0.1:5000')

def start_server(host='127.0.0.1', port=5000, debug=False, stratigraphy_file=None, data_file=None):
    """启动地层分层字典服务器"""
    print(f"🚀 启动地层分层字典服务...")
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"📁 上传目录: {os.path.abspath(app.config['UPLOAD_FOLDER'])}")
    
    # 如果指定了地层分层参考文件，先加载
    if stratigraphy_file:
        print(f"📂 加载地层分层参考文件: {stratigraphy_file}")
        if not load_stratigraphy_reference(stratigraphy_file):
            print("⚠️  地层分层参考文件加载失败，服务将以无参考模式启动")
    
    # 如果指定了数据文件，预加载数据
    if data_file:
        print(f"📂 预加载数据文件: {data_file}")
        if not preload_data(data_file):
            print("⚠️  数据文件预加载失败，服务将以正常模式启动")
    
    # 在后台线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        app.run(debug=debug, host=host, port=port)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description='地层分层字典可视化编辑工具')
    parser.add_argument('--host', default='127.0.0.1', help='服务器地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('-m', '--stratigraphy', help='地层分层参考CSV文件路径 (包含地层信息列)')
    parser.add_argument('-d', '--data', help='预加载的地层数据CSV文件路径 (包含地层名称、所属层位等列)')
    
    args = parser.parse_args()
    
    # 启动服务器
    start_server(host=args.host, port=args.port, debug=args.debug, 
                stratigraphy_file=args.stratigraphy, data_file=args.data)

if __name__ == '__main__':
    main()
