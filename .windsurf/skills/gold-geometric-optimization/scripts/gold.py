import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import argparse

# 解决中文乱码
plt.rc("font", family="DengXian")
plt.rcParams["axes.unicode_minus"] = False


def compute_s_limit(x, y, z, golden_ratio=0.618, num_points=None):
    """根据黄金分割几何优选算法计算分割面分值 S_limit。
    得分 S_i = x_i * y_i * z_i，降序排列后按样本量 n 确定 k 与 S_limit。
    
    Args:
        x, y, z: 数据数组
        golden_ratio: 黄金系数（0~1），默认0.618
        num_points: 如果指定，直接使用该数量作为选取点数；否则使用 (1-golden_ratio) 倍总数
    """
    S = x * y * z
    n = len(S)
    order = np.argsort(S)[::-1]
    S_sorted = S[order]

    # 确定要选取的点数 k
    if num_points is not None:
        k = min(int(num_points), n)
    else:
        # 选取前 (1-golden_ratio) 倍总数个点
        k = int(round(n * (1 - golden_ratio)))
    
    # 确保 k 在有效范围内
    k = max(1, min(k, n - 1))

    if n == 1:
        S_limit = float(S_sorted[0] * golden_ratio)
    elif n in (2, 3):
        if k >= n:
            k = n - 1
        S_limit = float((S_sorted[0] - S_sorted[1]) * golden_ratio + S_sorted[1])
    elif n in (4, 5):
        if k >= n:
            k = n - 1
        S_limit = float((S_sorted[k - 1] - S_sorted[k]) * golden_ratio + S_sorted[k])
    else:
        if k >= n:
            k = n - 1
        S_limit = float((S_sorted[k - 1] - S_sorted[k]) * golden_ratio + S_sorted[k])

    return S_limit


def load_config(csv_file_path=None, global_config_file="gold.config.json"):
    """加载配置文件，按照以下优先级查找：
    1. CSV文件所在目录下的gold.config.json（如果有CSV文件路径传入）
    2. 当前工作目录下的gold.config.json
    3. 用户目录下的.CCQ.config/gold.config.json
    4. 如果都不存在或格式错误，采用默认设置
    """
    # 1. 首先尝试在CSV文件所在目录查找配置文件
    if csv_file_path:
        csv_dir_config = Path(csv_file_path).parent / "gold.config.json"
        if csv_dir_config.exists():
            try:
                with open(csv_dir_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"使用CSV文件所在目录的配置文件：{csv_dir_config}")
                return config
            except Exception as e:
                print(f"警告：无法读取CSV文件所在目录的配置文件 {csv_dir_config}，错误：{str(e)}")
    
    # 2. 尝试在当前工作目录查找配置文件
    current_dir_config = Path(global_config_file)
    if current_dir_config.exists():
        try:
            with open(current_dir_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"使用当前工作目录的配置文件：{current_dir_config}")
            return config
        except Exception as e:
            print(f"警告：无法读取当前工作目录的配置文件 {current_dir_config}，错误：{str(e)}")
    
    # 3. 尝试在用户目录下的.CCQ.config文件夹中查找配置文件
    user_ccq_config = Path.home() / ".CCQ.config" / "gold.config.json"
    if user_ccq_config.exists():
        try:
            with open(user_ccq_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"使用用户目录下.CCQ.config文件夹的配置文件：{user_ccq_config}")
            return config
        except Exception as e:
            print(f"警告：无法读取用户目录下.CCQ.config文件夹的配置文件 {user_ccq_config}，错误：{str(e)}")
    
    # 4. 如果以上都失败，返回默认配置
    print("未找到配置文件，使用默认配置设置")
    return get_default_config()


def get_default_config():
    """获取默认配置"""
    return {
        "axis_ranges": {
            "x": {"min": "auto", "max": "auto", "min_factor": 0, "max_factor": 1.2},
            "y": {"min": "auto", "max": "auto", "min_factor": 0, "max_factor": 1.2},
            "z": {"min": "auto", "max": "auto", "min_factor": 0, "max_factor": 1.6}
        },
        "surface_ranges": {
            "x": {"min_factor": 0.0, "max_factor": 1.0},
            "y": {"min_factor": 0.0, "max_factor": 1.0},
            "z": {"min_factor": 0.0, "max_factor": 1.0}
        }
    }


def check_header(header):
    """检查表头是否符合要求：序号、标签+其它（三项）"""
    if len(header) != 5:
        return False, f"表头列数应为5列，实际为{len(header)}列"
    
    if header[0] != "序号":
        return False, f"第一列应为'序号'，实际为'{header[0]}'"
    
    if header[1] != "标签":
        return False, f"第二列应为'标签'，实际为'{header[1]}'"
    
    # 检查是否有3列其它数据（X、Y、Z）
    if len(header) < 5:
        return False, "表头应包含序号、标签和至少3列数据"
    
    return True, "表头检查通过"


def plot_3d_scatter(csv_file, view_mode=False, golden_ratio=0.618, num_points=None, show_colormap_label=False, config_file="gold.config.json"):
    """绘制3D散点图
    
    Args:
        csv_file: CSV文件路径
        view_mode: 如果为True，在窗口中显示图片；如果为False，保存图片
        golden_ratio: 黄金系数（0~1），默认0.618
        num_points: 如果指定，直接使用该数量作为选取点数；否则使用 (1-golden_ratio) 倍总数
        show_colormap_label: 如果为True，显示色谱系标签（颜色条）
        config_file: 配置文件路径，默认为 "gold.config.json"，当未通过命令行指定时使用
    """
    try:
        # 加载配置 - 优先使用命令行参数指定的配置文件，否则按默认优先级查找
        if config_file == "gold.config.json":
            # 如果是默认值，使用多级查找逻辑
            config = load_config(csv_file_path=csv_file)
        else:
            # 如果用户通过命令行明确指定了配置文件，直接使用该配置文件
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    print(f"使用指定的配置文件：{config_path}")
                except Exception as e:
                    print(f"警告：无法读取指定的配置文件 {config_file}，使用默认配置。错误：{str(e)}")
                    config = load_config(csv_file_path=csv_file)
            else:
                print(f"警告：指定的配置文件不存在 {config_file}，使用默认配置")
                config = load_config(csv_file_path=csv_file)
        
        # 读取CSV文件
        data = pd.read_csv(csv_file, encoding="utf-8")
        
        # 检查表头
        header = list(data.columns)
        is_valid, message = check_header(header)
        
        if not is_valid:
            print(f"错误：{csv_file} - {message}")
            return False, None, None, None, None
        
        # 提取数据
        # 第三列为x（索引2），第四列为y（索引3），第五列为z（索引4）
        x = data.iloc[:, 2].values  # X列
        y = data.iloc[:, 3].values  # Y列
        z = data.iloc[:, 4].values  # Z列
        labels = data.iloc[:, 1].values  # 标签列
        
        # 获取坐标轴标题（表头）
        x_label = header[2]  # X
        y_label = header[3]  # Y
        z_label = header[4]  # Z
        
        # 检查并过滤掉包含NaN或空值的数据行
        # 将空字符串转换为NaN，然后删除包含NaN的行
        df_for_filter = pd.DataFrame({'x': x, 'y': y, 'z': z, 'labels': labels})
        df_for_filter = df_for_filter.replace('', np.nan)  # 将空字符串替换为NaN
        df_for_filter = df_for_filter.dropna()  # 删除包含NaN的行
        
        # 重新赋值过滤后的数据
        x = df_for_filter['x'].values.astype(float)
        y = df_for_filter['y'].values.astype(float)
        z = df_for_filter['z'].values.astype(float)
        labels = df_for_filter['labels'].values
        
        # 检查是否有足够的数据点进行处理
        if len(x) == 0:
            print(f"错误：{csv_file} - 过滤空值后没有可用数据")
            return False, None, None, None, None
        elif len(x) < 2:
            print(f"警告：{csv_file} - 过滤空值后只剩{len(x)}个数据点，不足以进行有效的3D绘图")
            return False, None, None, None, None
        
        # 创建3D图形
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(projection="3d")

        # 分割面 x·y·z = S_limit（双曲面）
        S_limit = compute_s_limit(x, y, z, golden_ratio=golden_ratio, num_points=num_points)
        S = x * y * z
        mask_above = S >= S_limit  # 分割面之上 = 选取点
        mask_below = ~mask_above
        
        # 获取选取点和未选取点的Z值及标签
        selected_z_values = z[mask_above]
        selected_labels = labels[mask_above]
        unselected_z_values = z[mask_below]
        unselected_labels = labels[mask_below]
        
        # 按Z值降序排序选取点
        if len(selected_labels) > 0:
            selected_order = np.argsort(selected_z_values)[::-1]  # 降序
            selected_labels = selected_labels[selected_order]
            selected_z_values = selected_z_values[selected_order]  # 同步排序Z值
        else:
            selected_labels = []
            selected_z_values = np.array([])

        # 按Z值降序排序未选取点
        if len(unselected_labels) > 0:
            unselected_order = np.argsort(unselected_z_values)[::-1]  # 降序
            unselected_labels = unselected_labels[unselected_order]
            unselected_z_values = unselected_z_values[unselected_order]  # 同步排序Z值
        else:
            unselected_labels = []
            unselected_z_values = np.array([])

        # 使用配置设置轴范围
        axis_config = config.get("axis_ranges", {})
        
        # X轴范围
        x_min_config = axis_config.get("x", {}).get("min", "auto")
        x_max_config = axis_config.get("x", {}).get("max", "auto")
        x_min_factor = axis_config.get("x", {}).get("min_factor", 0)
        x_max_factor = axis_config.get("x", {}).get("max_factor", 1.2)
        
        if x_min_config == "auto":
            if x.min() == 0:
                x_min = 0  # 如果实际最小值为0，则轴最小值也为0
            else:
                x_min = x.min() * x_min_factor  # 使用配置的最小倍数
        else:
            x_min = float(x_min_config)
        
        if x_max_config == "auto":
            x_max = x.max() * x_max_factor  # 使用配置的最大倍数
        else:
            x_max = float(x_max_config)
        
        # Y轴范围
        y_min_config = axis_config.get("y", {}).get("min", "auto")
        y_max_config = axis_config.get("y", {}).get("max", "auto")
        y_min_factor = axis_config.get("y", {}).get("min_factor", 0)
        y_max_factor = axis_config.get("y", {}).get("max_factor", 1.2)
        
        if y_min_config == "auto":
            if y.min() == 0:
                y_min = 0  # 如果实际最小值为0，则轴最小值也为0
            else:
                y_min = y.min() * y_min_factor  # 使用配置的最小倍数
        else:
            y_min = float(y_min_config)
        
        if y_max_config == "auto":
            y_max = y.max() * y_max_factor  # 使用配置的最大倍数
        else:
            y_max = float(y_max_config)
        
        # Z轴范围
        z_min_config = axis_config.get("z", {}).get("min", "auto")
        z_max_config = axis_config.get("z", {}).get("max", "auto")
        z_min_factor = axis_config.get("z", {}).get("min_factor", 0)
        z_max_factor = axis_config.get("z", {}).get("max_factor", 1.6)
        
        if z_min_config == "auto":
            if z.min() == 0:
                z_min = 0  # 如果实际最小值为0，则轴最小值也为0
            else:
                z_min = z.min() * z_min_factor  # 使用配置的最小倍数
        else:
            z_min = float(z_min_config)
        
        if z_max_config == "auto":
            z_max = z.max() * z_max_factor  # 使用配置的最大倍数
        else:
            z_max = float(z_max_config)

        # 使用配置设置分割面范围
        surface_config = config.get("surface_ranges", {})
        
        # 获取分割面X范围因子
        x_surf_min_factor = surface_config.get("x", {}).get("min_factor", 0.0)
        x_surf_max_factor = surface_config.get("x", {}).get("max_factor", 1.0)
        # 计算分割面X的实际范围
        x_surf_min = x_min + (x_max - x_min) * x_surf_min_factor
        x_surf_max = x_min + (x_max - x_min) * x_surf_max_factor
        
        # 获取分割面Y范围因子
        y_surf_min_factor = surface_config.get("y", {}).get("min_factor", 0.0)
        y_surf_max_factor = surface_config.get("y", {}).get("max_factor", 1.0)
        # 计算分割面Y的实际范围
        y_surf_min = y_min + (y_max - y_min) * y_surf_min_factor
        y_surf_max = y_min + (y_max - y_min) * y_surf_max_factor
        
        # 获取分割面Z范围因子
        z_surf_min_factor = surface_config.get("z", {}).get("min_factor", 0.0)
        z_surf_max_factor = surface_config.get("z", {}).get("max_factor", 1.0)
        # 计算分割面Z的实际范围
        z_surf_min = z_min + (z_max - z_min) * z_surf_min_factor
        z_surf_max = z_min + (z_max - z_min) * z_surf_max_factor

        # 计算网格用于绘制分割面，使用配置的分割面范围
        # 为避免分割面超出配置的轴范围，直接使用配置的范围进行网格生成
        xs = np.linspace(x_surf_min, x_surf_max, 60)
        ys = np.linspace(y_surf_min, y_surf_max, 60)
        xx, yy = np.meshgrid(xs, ys)
        eps = 1e-10
        with np.errstate(divide="ignore", invalid="ignore"):
            zz = np.where(
                np.abs(xx * yy) > eps, S_limit / (xx * yy), np.nan
            )
        # 只保留Z值在配置范围内的分割面部分
        zz_mask = (zz >= z_surf_min) & (zz <= z_surf_max)
        zz = np.where(zz_mask, zz, np.nan)
        
        ax.plot_surface(
            xx, yy, zz,
            alpha=0.35,
            rstride=1,
            cstride=1,
            cmap=plt.cm.coolwarm,
        )

        # 根据Z值设置颜色映射（仅用于分割面之上的点）
        # 创建从深红色到紫色的颜色映射（Z值大→深红色，Z值小→紫色）
        colors_list = ['#4B0082', '#8A2BE2', '#9370DB', '#DA70D6', '#FF1493', '#DC143C', '#A52A2A', '#8B0000']
        colormap = LinearSegmentedColormap.from_list('purple_to_red', colors_list, N=256)
        normalize = plt.Normalize(vmin=z.min(), vmax=z.max())
        colors = colormap(normalize(z))
        
        # 计算数据范围，用于标签偏移
        x_range = x.max() - x.min() if x.max() != x.min() else 1
        y_range = y.max() - y.min() if y.max() != y.min() else 1
        z_range = z.max() - z.min() if z.max() != z.min() else 1
        base_offset_ratio = 0.08  # 基础偏移比例
        
        s_base = 100
        s_below = s_base * 2 / 3  # 未选取点大小为原来的 2/3
        # 绘制散点：分割面之下先画（透明、黑色细边框、无标签），之上后画（彩色、黑色粗边框）
        if np.any(mask_below):
            ax.scatter(
                x[mask_below], y[mask_below], z[mask_below],
                s=s_below, facecolors='none', edgecolors="black", linewidth=1.0
            )
        if np.any(mask_above):
            ax.scatter(
                x[mask_above], y[mask_above], z[mask_above],
                s=s_base, c=z[mask_above], cmap=colormap, alpha=0.6,
                edgecolors="black", linewidth=2.5
            )

        # 仅对分割面之上的点计算标签位置并绘制连接线、标签
        label_data = []  # [(i, (lx, ly, lz)), ...]
        above_idx = np.where(mask_above)[0]
        min_distance_ratio = 0.03

        for i in above_idx:
            offset_directions = [
                (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
                (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1),
                (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
            ]
            best_pos = None
            best_distance = 0.0

            for scale in [1.0, 1.5, 2.0, 2.5, 3.0]:
                for dir_x, dir_y, dir_z in offset_directions:
                    x_offset = dir_x * x_range * base_offset_ratio * scale
                    y_offset = dir_y * y_range * base_offset_ratio * scale
                    z_offset = dir_z * z_range * base_offset_ratio * scale
                    cx = x[i] + x_offset
                    cy = y[i] + y_offset
                    cz = z[i] + z_offset

                    min_dist = float("inf")
                    for _, (lx, ly, lz) in label_data:
                        d = np.sqrt((cx - lx) ** 2 + (cy - ly) ** 2 + (cz - lz) ** 2)
                        min_dist = min(min_dist, d)
                    norm = np.sqrt(x_range ** 2 + y_range ** 2 + z_range ** 2)
                    normalized_dist = min_dist / norm if norm > 0 else 0

                    if normalized_dist >= min_distance_ratio and normalized_dist > best_distance:
                        best_pos = (cx, cy, cz)
                        best_distance = normalized_dist
                        if normalized_dist >= min_distance_ratio * 2:
                            break
                if best_pos is not None and best_distance >= min_distance_ratio * 2:
                    break

            if best_pos is None:
                best_pos = (
                    x[i] + x_range * base_offset_ratio,
                    y[i] + y_range * base_offset_ratio,
                    z[i] + z_range * base_offset_ratio,
                )
            label_data.append((i, best_pos))

        for i, (lx, ly, lz) in label_data:
            color = colors[i]
            dark_color = tuple(max(0, c * 0.4) for c in color[:3])
            ax.plot([x[i], lx], [y[i], ly], [z[i], lz], "gray", linewidth=0.8, alpha=0.6, linestyle="--")
            ax.text(lx, ly, lz, labels[i], fontsize=14, color=dark_color, weight="bold")
        
        # 设置坐标轴标签（加粗，字体更大）
        ax.set_xlabel(x_label, fontdict={"size": 16, "color": "black", "weight": "bold"})
        ax.set_ylabel(y_label, fontdict={"size": 16, "color": "black", "weight": "bold"})
        # 如果启用色谱标签，不显示Z轴标题
        if not show_colormap_label:
            ax.set_zlabel(z_label, fontdict={"size": 16, "color": "black", "weight": "bold"})
        
        # 设置坐标轴范围
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_zlim(z_min, z_max)
        
        # 设置坐标轴刻度标签字体大小
        ax.tick_params(axis='x', labelsize=11)
        ax.tick_params(axis='y', labelsize=11)
        ax.tick_params(axis='z', labelsize=11)
        
        # 如果启用色谱系标签，添加颜色条
        if show_colormap_label:
            # 创建颜色条，只显示选取点的颜色映射
            if np.any(mask_above):
                sm = plt.cm.ScalarMappable(cmap=colormap, norm=normalize)
                sm.set_array([])
                cbar = fig.colorbar(sm, ax=ax, pad=0.1, shrink=0.8)
                cbar.set_label(z_label, fontsize=14, weight='bold')
                cbar.ax.tick_params(labelsize=11)
        
        # 调整布局，确保Z轴标签完整显示（增加右边距）
        # 先调整subplot的位置，为Z轴标签留出更多空间
        if show_colormap_label:
            fig.subplots_adjust(left=0.05, bottom=0.05, right=0.75, top=0.95)
        else:
            fig.subplots_adjust(left=0.05, bottom=0.05, right=0.80, top=0.95)
        
        csv_path = Path(csv_file)
        folder = str(csv_path.resolve().parent)
        fname = csv_path.name

        # 创建带Z值的标签列表
        selected_with_z = [f"{label}({z_val:.2f})" for label, z_val in zip(selected_labels, selected_z_values)]
        unselected_with_z = [f"{label}({z_val:.2f})" for label, z_val in zip(unselected_labels, unselected_z_values)]

        if view_mode:
            plt.show()
            print(f"显示：{csv_file}")
            plt.close()
            return True, folder, fname, selected_with_z, unselected_with_z
        else:
            pic_name = csv_path.stem + "pic" + ".png"
            pic_path = csv_path.parent / pic_name
            plt.savefig(pic_path, dpi=300, bbox_inches="tight", pad_inches=0.4, facecolor="white")
            print(f"成功：{csv_file} -> {pic_path}")
            plt.close()
            return True, folder, fname, selected_with_z, unselected_with_z

    except Exception as e:
        print(f"错误：处理 {csv_file} 时发生异常：{str(e)}")
        return False, None, None, None, None


def find_csv_files(path, max_depth=3, current_depth=0):
    """递归查找CSV文件，最多3层"""
    csv_files = []
    
    if current_depth > max_depth:
        return csv_files
    
    path_obj = Path(path)
    
    if path_obj.is_file():
        if path_obj.suffix.lower() == '.csv':
            csv_files.append(str(path_obj))
    elif path_obj.is_dir():
        try:
            for item in path_obj.iterdir():
                if item.is_file() and item.suffix.lower() == '.csv':
                    csv_files.append(str(item))
                elif item.is_dir() and current_depth < max_depth:
                    csv_files.extend(find_csv_files(str(item), max_depth, current_depth + 1))
        except PermissionError:
            print(f"警告：无法访问目录 {path_obj}")
    
    return csv_files


def write_report(input_path, results, report_name="gold_report.md"):
    """生成选取报告：文件夹、文件名、选取点。"""
    path_obj = Path(input_path)
    report_dir = path_obj.resolve().parent if path_obj.is_file() else path_obj.resolve()
    report_path = report_dir / report_name
    
    # 构建Markdown格式的文件树
    lines = [
        "# 黄金分割几何优选 — 选取报告",
        "",
        f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    # 获取根目录名称
    root_path = Path(input_path)
    if root_path.is_file():
        root_name = root_path.parent.name
        base_path = root_path.parent
    else:
        # 如果输入的是当前目录（.），使用当前目录名
        if str(root_path) == '.':
            root_name = Path.cwd().name
            base_path = Path.cwd()
        else:
            root_name = root_path.name
            base_path = root_path
    
    lines.append(f"- {root_name}/")
    
    # 按文件夹组织结果 - 使用绝对路径作为键来避免重复
    folder_structure = {}
    for folder, fname, selected, unselected in results:
        abs_folder_path = Path(folder).resolve()
        try:
            rel_to_base_path = abs_folder_path.relative_to(base_path) if abs_folder_path != base_path else Path('.')
            rel_folder_str = str(rel_to_base_path)
        except ValueError:
            # 如果无法相对于base_path计算路径，则尝试相对于当前工作目录
            try:
                rel_to_base_path = abs_folder_path.relative_to(Path.cwd())
                rel_folder_str = str(rel_to_base_path)
            except ValueError:
                # 否则使用文件夹名
                rel_folder_str = abs_folder_path.name
        
        if rel_folder_str not in folder_structure:
            folder_structure[rel_folder_str] = []
        # 添加文件信息，确保同一文件夹下不会重复添加
        file_exists = False
        for existing_fname, existing_selected, existing_unselected in folder_structure[rel_folder_str]:
            if existing_fname == fname:
                file_exists = True
                break
        if not file_exists:
            folder_structure[rel_folder_str].append((fname, selected, unselected))
    
    # 收集所有唯一路径并排序
    all_paths = list(folder_structure.keys())
    all_paths.sort(key=lambda x: x.count(os.sep))  # 按层级深度排序
    
    # 记录已经输出过的路径，避免重复
    printed_paths = set()
    
    # 构建文件树
    for folder_path in all_paths:
        if folder_path == "." or folder_path == "":
            # 这是根目录，不需要额外的缩进
            pass
        else:
            # 输出路径中的每一级文件夹（如果还没有输出过）
            subfolders = folder_path.split(os.sep)
            for i, subfolder in enumerate(subfolders):
                current_path = os.sep.join(subfolders[:i+1])
                if current_path not in printed_paths:
                    indent_level = i + 1
                    folder_line = "  " * indent_level + f"- {subfolder}/"
                    lines.append(folder_line)
                    printed_paths.add(current_path)
        
        # 添加该文件夹下的文件
        for fname, selected, unselected in folder_structure[folder_path]:
            csv_name = Path(fname).stem
            png_name = csv_name + "pic.png"
            
            # 确定缩进级别
            if folder_path == "." or folder_path == "":
                indent_level = 1
            else:
                indent_level = len(folder_path.split(os.sep)) + 1
            
            # 添加CSV文件
            csv_indent = "  " * indent_level + f"- {fname}"
            lines.append(csv_indent)
            
            # 添加PNG文件
            png_indent = "  " * indent_level + f"- {png_name}"
            lines.append(png_indent)
            
            # 添加选取点
            if selected:
                selected_str = "、".join(str(s) for s in selected)
                # 构建文件路径前缀
                file_prefix = f"{folder_path.replace(os.sep, '/')}/" if folder_path not in [".", ""] else ""
                full_prefix = f"{file_prefix}{fname}选取点："
                selected_indent = "  " * indent_level + f"- {full_prefix}{selected_str}"
                lines.append(selected_indent)
            
            # 添加未选取点
            if unselected:
                unselected_str = "、".join(str(u) for u in unselected)
                # 构建文件路径前缀
                file_prefix = f"{folder_path.replace(os.sep, '/')}/" if folder_path not in [".", ""] else ""
                full_prefix = f"{file_prefix}{fname}未选取点："
                unselected_indent = "  " * indent_level + f"- {full_prefix}{unselected_str}"
                lines.append(unselected_indent)
    
    # 添加gold_report.md文件
    lines.append("  - gold_report.md")
    
    text = "\n".join(lines)
    report_path.write_text(text, encoding="utf-8")
    print(f"报告已生成：{report_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='绘制3D散点图')
    parser.add_argument('path', help='CSV文件或文件夹路径')
    parser.add_argument('-v', '--view', action='store_true', 
                       help='在matplotlib窗口中显示图片，而不是保存')
    parser.add_argument('-x', '--golden-ratio', type=float, default=0.618,
                       help='黄金系数（0~1），默认0.618')
    parser.add_argument('-g', '--num-points', type=int, default=None,
                       help='直接指定要选取的数据点个数')
    parser.add_argument('-l', '--colormap-label', action='store_true',
                       help='启用或显示色谱系标签（颜色条）')
    parser.add_argument('-c', '--config-file', type=str, default="gold.config.json",
                       help='配置文件路径，默认为 "gold.config.json"')
    
    args = parser.parse_args()
    
    input_path = args.path
    view_mode = args.view
    golden_ratio = args.golden_ratio
    num_points = args.num_points
    show_colormap_label = args.colormap_label
    config_file = args.config_file
    
    # 验证黄金系数范围
    if not 0 < golden_ratio < 1:
        print(f"错误：黄金系数必须在0~1之间，当前值为{golden_ratio}")
        sys.exit(1)
    
    # 如果同时指定了-g和-x，优先使用-g
    if num_points is not None and num_points <= 0:
        print(f"错误：选取点数必须大于0，当前值为{num_points}")
        sys.exit(1)
    
    if not os.path.exists(input_path):
        print(f"错误：路径不存在：{input_path}")
        sys.exit(1)
    
    # 查找所有CSV文件
    csv_files = find_csv_files(input_path)
    
    if not csv_files:
        print(f"未找到CSV文件：{input_path}")
        sys.exit(1)
    
    if view_mode:
        print(f"找到 {len(csv_files)} 个CSV文件，将在窗口中显示...")
    else:
        print(f"找到 {len(csv_files)} 个CSV文件，开始处理...")
    
    # 处理每个CSV文件，收集选取结果
    success_count = 0
    report_results = []
    for csv_file in csv_files:
        ok, folder, fname, selected_labels, unselected_labels = plot_3d_scatter(
            csv_file, 
            view_mode=view_mode,
            golden_ratio=golden_ratio,
            num_points=num_points,
            show_colormap_label=show_colormap_label,
            config_file=config_file
        )
        if ok:
            success_count += 1
            report_results.append((folder, fname, selected_labels, unselected_labels))

    if not view_mode:
        print(f"\n处理完成：成功 {success_count}/{len(csv_files)} 个文件")
        if report_results:
            write_report(input_path, report_results)


if __name__ == "__main__":
    main()
