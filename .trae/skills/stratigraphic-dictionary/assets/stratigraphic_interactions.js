// stratigraphic_interactions.js

// 全局变量
let rawData = null;
let stratigraphyData = null;
let initialStratigraphyOrder = []; // 保存整合后的地层顺序（包括新旧）
let referenceOrder = []; // 保存地层分层文件中的标准顺序
let svg = null;
let g = null;
let xScale = null;
let yScale = null;
let isExpandedMode = false;  // 是否处于展开模式

// 颜色生成器
// 检测数据是否异常的函数
function isDataAbnormal(d) {
    const topPos = parseFloat(d['顶界所处位置（0~1）']);
    const bottomPos = parseFloat(d['底界所处位置（0~1）']);
    
    // 检查是否为有效数字
    if (isNaN(topPos) || isNaN(bottomPos)) {
        return true;
    }
    
    // 检查是否超出范围 [0, 1]
    if (topPos < 0 || topPos > 1 || bottomPos < 0 || bottomPos > 1) {
        return true;
    }
    
    // 检查顶界是否大于底界（正常情况应该是顶界 < 底界）
    if (topPos > bottomPos) {
        return true;
    }
    
    return false;
}

// 根据数据是否异常返回颜色
function getColorForData(d) {
    if (isDataAbnormal(d)) {
        return '#000000'; // 黑色背景
    } else {
        // 使用原始的颜色比例尺，保持与图例一致
        return colorScale(d['地层名称']);
    }
}

// 获取文本颜色（根据背景决定）
function getTextFill(d) {
    if (isDataAbnormal(d)) {
        return '#ffffff'; // 白色文字
    } else {
        return '#000000'; // 黑色文字
    }
}

const colorScale = d3.scaleOrdinal(d3.schemeSet3);

// 添加展开功能相关函数
function toggleExpandMode() {
    isExpandedMode = !isExpandedMode;
    
    // 更新按钮文本
    document.getElementById('expandBtn').textContent = isExpandedMode ? '收起地层' : '展开地层';
    
    // 重新渲染可视化
    if (rawData && stratigraphyData) {
        renderVisualization();
    }
    
    document.getElementById('status-text').textContent = isExpandedMode ? '已进入展开模式' : '已退出展开模式';
}

// 显示编辑弹窗
function showEditModal(d) {
    const modal = document.getElementById('editModal');
    const formationNameInput = document.getElementById('editFormationName');
    const stratigraphySelect = document.getElementById('editStratigraphy');
    const topPositionInput = document.getElementById('editTopPosition');
    const bottomPositionInput = document.getElementById('editBottomPosition');
    
    // 设置当前值
    formationNameInput.value = d['地层名称'];
    topPositionInput.value = parseFloat(d['顶界所处位置（0~1）']).toFixed(2);
    bottomPositionInput.value = parseFloat(d['底界所处位置（0~1）']).toFixed(2);
    
    // 填充所属层位下拉选项
    stratigraphySelect.innerHTML = '';
    if (stratigraphyData) {
        stratigraphyData.forEach(strat => {
            const option = document.createElement('option');
            option.value = strat['地层信息'];
            option.textContent = strat['地层信息'];
            option.selected = strat['地层信息'] === d['所属层位'];
            stratigraphySelect.appendChild(option);
        });
    }
    
    // 显示弹窗
    modal.style.display = 'block';
    
    // 存储当前编辑的数据对象
    window.currentEditData = d;
}

// 隐藏编辑弹窗
function hideEditModal() {
    document.getElementById('editModal').style.display = 'none';
    window.currentEditData = null;
}

// 保存编辑结果
function saveEdit() {
    if (!window.currentEditData) return;
    
    const stratigraphySelect = document.getElementById('editStratigraphy');
    const topPositionInput = document.getElementById('editTopPosition');
    const bottomPositionInput = document.getElementById('editBottomPosition');
    
    // 获取新值
    const newStratigraphy = stratigraphySelect.value;
    const newTopPosition = parseFloat(topPositionInput.value);
    const newBottomPosition = parseFloat(bottomPositionInput.value);
    
    // 验证输入值
    if (isNaN(newTopPosition) || isNaN(newBottomPosition) || 
        newTopPosition < 0 || newTopPosition > 1 || 
        newBottomPosition < 0 || newBottomPosition > 1 ||
        newTopPosition > newBottomPosition) {
        alert('请输入有效的数值！顶界应小于等于底界，且数值应在0-1之间。');
        return;
    }
    
    // 更新原始数据
    const index = rawData.findIndex(item => 
        item['地层名称'] === window.currentEditData['地层名称'] &&
        item['顶界所处位置（0~1）'] === window.currentEditData['顶界所处位置（0~1）'] &&
        item['底界所处位置（0~1）'] === window.currentEditData['底界所处位置（0~1）'] &&
        item['所属层位'] === window.currentEditData['所属层位']
    );
    
    if (index !== -1) {
        rawData[index]['所属层位'] = newStratigraphy;
        rawData[index]['顶界所处位置（0~1）'] = newTopPosition;
        rawData[index]['底界所处位置（0~1）'] = newBottomPosition;
        
        // 重新渲染可视化
        renderVisualization();
    }
    
    // 隐藏弹窗
    hideEditModal();
}

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // 绑定事件监听器
    document.getElementById('loadDataBtn').addEventListener('click', loadData);
    document.getElementById('exportBtn').addEventListener('click', exportData);
    document.getElementById('expandBtn').addEventListener('click', toggleExpandMode);
    document.getElementById('addSmallLayerBtn').addEventListener('click', showAddSmallLayerModal);
    document.getElementById('csvFileInput').addEventListener('change', handleFileSelect);
    
    // 绑定编辑弹窗相关事件
    document.querySelector('.close').addEventListener('click', hideEditModal);
    document.getElementById('cancelEditBtn').addEventListener('click', hideEditModal);
    document.getElementById('saveEditBtn').addEventListener('click', saveEdit);
    
    // 绑定添加小层弹窗相关事件
    document.getElementById('closeAddModal').addEventListener('click', hideAddSmallLayerModal);
    document.getElementById('cancelAddBtn').addEventListener('click', hideAddSmallLayerModal);
    document.getElementById('saveAddBtn').addEventListener('click', saveNewSmallLayer);
    
    // 点击弹窗外部关闭
    window.addEventListener('click', function(event) {
        const editModal = document.getElementById('editModal');
        const addModal = document.getElementById('addSmallLayerModal');
        
        if (event.target === editModal) {
            hideEditModal();
        }
        if (event.target === addModal) {
            hideAddSmallLayerModal();
        }
    });
    
    // 初始化SVG
    initSvg();
    
    // 检查是否有预加载数据
    checkPreloadedData();
}

function initSvg() {
    svg = d3.select("#stratigraphic-svg");
    g = svg.append("g").attr("class", "canvas");
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        document.getElementById('status-text').textContent = `已选择文件: ${files[0].name}`;
    }
}

// 检查是否有预加载数据
function checkPreloadedData() {
    fetch('/api/upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.preloaded) {
            console.log('检测到预加载数据:', data);
            
            // 更新UI显示
            document.getElementById('status-text').textContent = `已加载预加载数据: ${data.filename} (${data.record_count} 条记录)`;
            
            // 处理数据
            rawData = data.data;
            stratigraphyData = data.stratigraphy;
            referenceOrder = data.reference_order || [];
            
            // 保存整合后的地层顺序
            initialStratigraphyOrder = stratigraphyData.map(item => item['地层信息']);
            
            // 自动加载数据可视化
            setTimeout(() => {
                console.log('准备渲染可视化，数据状态:', {
                    rawData: rawData ? rawData.length + ' 条' : 'null',
                    stratigraphyData: stratigraphyData ? stratigraphyData.length + ' 条' : 'null',
                    initialStratigraphyOrder: initialStratigraphyOrder ? initialStratigraphyOrder.length + ' 个' : 'null'
                });
                renderVisualization();
            }, 500);
            
            // 显示成功消息
            showNotification('✅ 已自动加载预加载数据！', 'success');
        } else {
            console.log('没有预加载数据，等待用户上传文件');
            document.getElementById('status-text').textContent = '请选择CSV文件或使用命令行预加载数据';
        }
    })
    .catch(error => {
        console.log('检查预加载数据失败:', error);
        document.getElementById('status-text').textContent = '请选择CSV文件开始分析';
    });
}

// 显示通知消息
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 1000;
        font-size: 14px;
        max-width: 300px;
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

async function loadData() {
    const fileInput = document.getElementById('csvFileInput');
    if (fileInput.files.length === 0) {
        alert('请先选择一个CSV文件');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    try {
        document.getElementById('status-text').textContent = '正在上传和处理数据...';
        console.log('开始上传文件:', fileInput.files[0].name);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        console.log('服务器响应状态:', response.status);
        
        const result = await response.json();
        console.log('服务器响应数据:', result);
        
        if (result.success) {
            rawData = result.data;
            stratigraphyData = result.stratigraphy;
            referenceOrder = result.reference_order || []; // 获取参考顺序

            // 保存初始地层顺序
            initialStratigraphyOrder = stratigraphyData.map(d => d['地层信息']);

            // 渲染可视化
            renderVisualization();
            
            document.getElementById('status-text').textContent = `成功加载数据: ${result.record_count} 条记录`;
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('数据加载错误:', error);
        document.getElementById('status-text').textContent = `数据加载失败: ${error.message}`;
        alert(`数据加载失败: ${error.message}`);
    }
}

function renderVisualization() {
    console.log('renderVisualization 被调用，数据检查:', {
        rawData: rawData ? rawData.length + ' 条记录' : 'null',
        stratigraphyData: stratigraphyData ? stratigraphyData.length + ' 条记录' : 'null',
        isExpandedMode: isExpandedMode
    });
    
    if (!rawData || !stratigraphyData) {
        console.log('数据不完整，退出渲染');
        return;
    }
    
    console.log('开始渲染地层可视化...');
    
    // 清除之前的图形
    g.selectAll("*").remove();
    
    // 设置尺寸
    const container = document.getElementById('visualization-container');
    const width = container.clientWidth - 40; // 减去padding
    let height = 600;
    const margin = { top: 40, right: 150, bottom: 60, left: 150 };
    
    // 根据展开模式调整高度和Y轴比例尺
    let yDomain = [];
    let yScaleRange;
    
    if (isExpandedMode) {
        // 展开模式：为每个地层单独分配空间，但Y轴标签只显示所属层位
        const expandedStratigraphy = [];
        
        // 按所属层位分组数据，但按照初始顺序遍历
        const groupedData = d3.group(rawData, d => d['所属层位']);
        
        let rowIndex = 0;
        // 按照初始地层顺序遍历，确保顺序不变
        for (const stratName of initialStratigraphyOrder) {
            const subData = groupedData.get(stratName) || [];
            if (subData.length > 0) {
                // 对于每个层位，如果有多个不同的地层，则为每个地层分配一行
                const uniqueFormations = [...new Set(subData.map(d => d['地层名称']))];

                if (uniqueFormations.length > 1) {
                    // 有多个地层，展开显示 - 每个子地层占用一行
                    uniqueFormations.forEach(formationName => {
                        expandedStratigraphy.push(rowIndex); // 直接使用数字索引，不需要特殊前缀
                        rowIndex++;
                    });
                } else {
                    // 只有一个地层，正常显示
                    expandedStratigraphy.push(rowIndex);
                    rowIndex++;
                }
            } else {
                // 没有数据的地层也要占一行 - 只在domain中添加索引，不进行渲染
                expandedStratigraphy.push(rowIndex);
                rowIndex++;
            }
        }
        
        // 也要处理不在初始顺序中的层位（如果有的话）
        for (const [stratName, subData] of groupedData) {
            // 使用 referenceOrder 来判断是否为新层位
            // 如果 referenceOrder 为空，说明没有加载地层分层文件，则所有层位都视为普通层位
            // 如果 stratName 不在 referenceOrder 中，且 referenceOrder 不为空，则视为新层位
            // 但这里我们是在处理"不在 initialStratigraphyOrder"中的层位，这通常是异常情况
            // 因为 initialStratigraphyOrder 应该包含了所有层位。
            // 现在的逻辑应该是：遍历 initialStratigraphyOrder，对于每个 stratName，
            // 检查它是否在 referenceOrder 中。

            // 此处的循环是处理那些可能在 groupedData 中存在但不在 initialStratigraphyOrder 中的数据
            // 理论上不应该发生，除非后端逻辑有误。
            // 我们重点修改上面主循环的逻辑。
            if (!initialStratigraphyOrder.includes(stratName)) {
                 // ... 保持原有逻辑作为兜底 ...

                const uniqueFormations = [...new Set(subData.map(d => d['地层名称']))];
                
                if (uniqueFormations.length > 1) {
                    // 有多个地层，展开显示
                    uniqueFormations.forEach(() => {
                        expandedStratigraphy.push(rowIndex);
                        rowIndex++;
                    });
                } else {
                    // 只有一个地层，正常显示
                    expandedStratigraphy.push(rowIndex);
                    rowIndex++;
                }
            }
        }
        
        yDomain = expandedStratigraphy;
        height = Math.max(600, expandedStratigraphy.length * 60); // 每行60像素
    } else {
        // 正常模式：每个层位占一行，使用初始地层顺序
        yDomain = initialStratigraphyOrder;
        height = 600;
    }
    
    // 更新SVG尺寸
    svg.attr("height", height + margin.top + margin.bottom);
    
    // 创建比例尺
    xScale = d3.scaleLinear()
        .domain([0, 1])
        .range([margin.left, width - margin.right]);
    
    yScale = d3.scaleBand()
        .domain(yDomain)
        .range([margin.top, height - margin.bottom])
        .padding(0.1);
    
    // 添加X轴
    g.append("g")
        .attr("class", "axis")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(xScale).ticks(10));
    
    g.append("text")
        .attr("class", "axis-label")
        .attr("x", width / 2)
        .attr("y", height - 10)
        .attr("text-anchor", "middle")
        .text("地层位置 (0-1，数值越小表示越靠近顶部)");
    
    // 添加Y轴
    g.append("g")
        .attr("class", "axis")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(yScale).tickFormat(function(d) {
            // 无论是展开模式还是普通模式，都隐藏Y轴刻度标签，因为我们手动添加标签以控制显示逻辑
            return "";
        }));
    
    g.append("text")
        .attr("class", "axis-label")
        .attr("transform", "rotate(-90)")
        .attr("x", -(height / 2))
        .attr("y", 15)
        .attr("text-anchor", "middle")
        .text("地层单位");
    
    // 添加网格线
    g.append("g")
        .attr("class", "grid")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(xScale)
            .tickSize(-height + margin.top + margin.bottom)
            .tickFormat("")
        );
    
    // 按所属层位分组数据
    const groupedData = d3.group(rawData, d => d['所属层位']);
    
    if (isExpandedMode) {
        // 展开模式渲染，按照初始地层顺序
        let rowIndex = 0;
        let lastStratName = null;
        
        let firstNewLayerExpanded = true;
        // 按照初始地层顺序遍历
        for (const stratName of initialStratigraphyOrder) {
            const subData = groupedData.get(stratName) || [];

            // 判断是否为新层位: 不在参考顺序中，且参考顺序不为空
            const isNewLayer = referenceOrder.length > 0 && !referenceOrder.includes(stratName);

            // 如果是新层位且是第一个，绘制红色分隔线
            if (isNewLayer && firstNewLayerExpanded) {
                 const yPos = yScale(rowIndex); // 当前行的Y位置

                 // 绘制背景大矩形 (覆盖红线以下所有区域)
                 const bottomY = yScale.range()[1];
                 g.append("rect")
                    .attr("x", margin.left)
                    .attr("y", yPos - 5)
                    .attr("width", width - margin.left - margin.right)
                    .attr("height", bottomY - (yPos - 5))
                    .attr("fill", "#E0E0E0") // 浅灰色背景
                    .attr("opacity", 0.5);   // 半透明

                 g.append("line")
                    .attr("x1", margin.left)
                    .attr("x2", width - margin.right)
                    .attr("y1", yPos - 5) // 稍微向上一点
                    .attr("y2", yPos - 5)
                    .attr("stroke", "red")
                    .attr("stroke-width", 2);
                firstNewLayerExpanded = false;
            }

            if (subData.length > 0) {
                const uniqueFormations = [...new Set(subData.map(d => d['地层名称']))];

                if (uniqueFormations.length > 1) {
                    // 有多个地层，展开显示，每个地层占一行
                    uniqueFormations.forEach((formationName, formationIdx) => {
                        const filteredData = subData.filter(d => d['地层名称'] === formationName);
                        // 在展开模式下，每个地层有自己的y位置，但标签仍然是大层名
                        const yPos = yScale(rowIndex);
                        const bandHeight = yScale.bandwidth();
                        const effectiveHeight = bandHeight * 0.8; // 使用部分高度
                        const rectY = yPos + (bandHeight - effectiveHeight) / 2;

                        // 绘制背景条带
                        g.append("rect")
                            .attr("class", "layer-band")
                            .attr("x", margin.left)
                            .attr("y", yPos)
                            .attr("width", width - margin.left - margin.right)
                            .attr("height", bandHeight)
                            .attr("fill", isNewLayer ? "#D3D3D3" : "#f8f9fa"); // 新层位灰色背景

                        
                        // 只在第一个子地层位置显示大层标签
                        if (formationIdx === 0) {
                            g.append("text")
                                .attr("class", "layer-text")
                                .attr("x", margin.left - 10)
                                .attr("y", yPos + bandHeight / 2)
                                .attr("text-anchor", "end")
                                .text(stratName);  // 只显示所属层位名称
                            
                            // 绘制粗虚线分隔符（除了第一个大层）
                            if (lastStratName !== null) {
                                g.append("line")
                                    .attr("x1", margin.left)
                                    .attr("x2", width - margin.right)
                                    .attr("y1", yPos - 5)
                                    .attr("y2", yPos - 5)
                                    .attr("stroke", "#333")
                                    .attr("stroke-width", 2)
                                    .attr("stroke-dasharray", "8,4");
                            }
                            
                            lastStratName = stratName;
                        }
                        
                        // 绘制该地层的数据
                        filteredData.forEach((d, idx) => {
                            const topPos = parseFloat(d['顶界所处位置（0~1）']);
                            const bottomPos = parseFloat(d['底界所处位置（0~1）']);
                            
                            // 验证数据有效性
                            if (isNaN(topPos) || isNaN(bottomPos) || 
                                topPos < 0 || topPos > 1 || 
                                bottomPos < 0 || bottomPos > 1) {
                                return; // 跳过无效数据
                            }
                            
                            // 计算矩形的位置和尺寸
                            const leftPos = Math.min(topPos, bottomPos);
                            const widthValue = Math.abs(bottomPos - topPos);
                            const rectWidth = widthValue * (width - margin.left - margin.right);
                            const rectX = xScale(leftPos);
                            
                            // 确保最小宽度
                            const minWidth = 10; // 像素
                            let finalWidth = Math.max(rectWidth, minWidth);
                            let finalX = rectX;
                            if (rectWidth < minWidth) {
                                const centerPos = (topPos + bottomPos) / 2;
                                finalX = xScale(centerPos) - minWidth / 2;
                            }
                            
                            // 获取颜色
                            const color = getColorForData(d);
                            
                            // 创建容器组
                            const group = g.append("g")
                                .attr("class", "formation-group")
                                .attr("data-formation", d['地层名称'])
                                .attr("data-original-strat", d['所属层位'])
                                .datum(d);
                            
                            // 绘制地层矩形
                            const rect = group.append("rect")
                                .attr("class", "formation-rect")
                                .attr("x", finalX)
                                .attr("y", rectY)
                                .attr("width", finalWidth)
                                .attr("height", effectiveHeight)
                                .attr("fill", isNewLayer ? color : color)
                                .attr("opacity", isDataAbnormal(d) ? 1.0 : (isNewLayer ? 0.2 : 0.8))
                                .attr("stroke", isNewLayer ? "black" : "none")
                                .attr("stroke-width", isNewLayer ? 2 : 0)
                                .attr("data-top", topPos)
                                .attr("data-bottom", bottomPos)
                                .attr("data-strat", stratName);
                            
                            // 添加地层名称文本
                            group.append("text")
                                .attr("class", "formation-text")
                                .attr("x", finalX + finalWidth / 2)
                                .attr("y", rectY + effectiveHeight / 2)
                                .attr("fill", getTextFill(d)) // 根据数据是否异常设置文本颜色
                                .text(`${d['地层名称']} (${topPos.toFixed(2)}, ${bottomPos.toFixed(2)})`);
                            
                            // 添加双击事件来编辑地层信息
                            group.on("dblclick", function(event, d) {
                                showEditModal(d);
                            });
                            
                            // 添加拖拽手柄（仅用于调整顶界/底界，不用于更改归属）
                            const leftHandle = group.append("rect")
                                .attr("class", "drag-handle")
                                .attr("x", finalX - 4)
                                .attr("y", rectY)
                                .attr("width", 8)
                                .attr("height", effectiveHeight)
                                .attr("cursor", "ew-resize")
                                .attr("data-side", "left");
                            
                            // 添加拖拽手柄（右边）
                            const rightHandle = group.append("rect")
                                .attr("class", "drag-handle")
                                .attr("x", finalX + finalWidth - 4)
                                .attr("y", rectY)
                                .attr("width", 8)
                                .attr("height", effectiveHeight)
                                .attr("cursor", "ew-resize")
                                .attr("data-side", "right");
                            
                            // 添加拖拽功能（仅调整顶界/底界）
                            const dragBehavior = d3.drag()
                                .on("start", dragStarted)
                                .on("drag", dragged)
                                .on("end", dragEnded);
                            
                            group.call(dragBehavior);
                            
                            // 为手柄也添加拖拽功能
                            leftHandle.call(dragBehavior);
                            rightHandle.call(dragBehavior);
                        });
                        
                        rowIndex++;
                    });
                } else {
                    // 只有一个地层，正常显示
                    const yPos = yScale(rowIndex);
                    const bandHeight = yScale.bandwidth();
                    const effectiveHeight = bandHeight * 0.8; // 使用部分高度
                    const rectY = yPos + (bandHeight - effectiveHeight) / 2;
                    
                    // 绘制背景条带
                    g.append("rect")
                        .attr("class", "layer-band")
                        .attr("x", margin.left)
                        .attr("y", yPos)
                        .attr("width", width - margin.left - margin.right)
                        .attr("height", bandHeight);
                    
                    // 添加Y轴标签 - 只有当这个层位尚未显示标签时才显示
                    if (stratName !== lastStratName) {
                        g.append("text")
                            .attr("class", "layer-text")
                            .attr("x", margin.left - 10)
                            .attr("y", yPos + bandHeight / 2)
                            .attr("text-anchor", "end")
                            .text(stratName);  // 只显示所属层位名称
                    }
                    
                    // 绘制粗虚线分隔符（除了第一个大层）
                    if (lastStratName !== null && stratName !== lastStratName) {
                        g.append("line")
                            .attr("x1", margin.left)
                            .attr("x2", width - margin.right)
                            .attr("y1", yPos - 5)
                            .attr("y2", yPos - 5)
                            .attr("stroke", "#333")
                            .attr("stroke-width", 2)
                            .attr("stroke-dasharray", "8,4");
                    }
                    
                    lastStratName = stratName;
                    
                    // 绘制数据
                    subData.forEach((d, idx) => {
                        const topPos = parseFloat(d['顶界所处位置（0~1）']);
                        const bottomPos = parseFloat(d['底界所处位置（0~1）']);
                        
                        // 验证数据有效性
                        if (isNaN(topPos) || isNaN(bottomPos) || 
                            topPos < 0 || topPos > 1 || 
                            bottomPos < 0 || bottomPos > 1) {
                            return; // 跳过无效数据
                        }
                        
                        // 计算矩形的位置和尺寸
                        const leftPos = Math.min(topPos, bottomPos);
                        const widthValue = Math.abs(bottomPos - topPos);
                        const rectWidth = widthValue * (width - margin.left - margin.right);
                        const rectX = xScale(leftPos);
                        
                        // 确保最小宽度
                        const minWidth = 10; // 像素
                        let finalWidth = Math.max(rectWidth, minWidth);
                        let finalX = rectX;
                        if (rectWidth < minWidth) {
                            const centerPos = (topPos + bottomPos) / 2;
                            finalX = xScale(centerPos) - minWidth / 2;
                        }
                        
                        // 获取颜色
                        const color = getColorForData(d);
                        
                        // 创建容器组
                        const group = g.append("g")
                            .attr("class", "formation-group")
                            .attr("data-formation", d['地层名称'])
                            .attr("data-original-strat", d['所属层位'])
                            .datum(d);
                        
                        // 绘制地层矩形
                        const rect = group.append("rect")
                            .attr("class", "formation-rect")
                            .attr("x", finalX)
                            .attr("y", rectY)
                            .attr("width", finalWidth)
                            .attr("height", effectiveHeight)
                            .attr("fill", isNewLayer ? color : color)
                            .attr("opacity", isDataAbnormal(d) ? 1.0 : (isNewLayer ? 0.2 : 0.8))
                            .attr("stroke", isNewLayer ? "black" : "none")
                            .attr("stroke-width", isNewLayer ? 2 : 0)
                            .attr("data-top", topPos)
                            .attr("data-bottom", bottomPos)
                            .attr("data-strat", stratName);
                        
                        // 添加地层名称文本
                        group.append("text")
                            .attr("class", "formation-text")
                            .attr("x", finalX + finalWidth / 2)
                            .attr("y", rectY + effectiveHeight / 2)
                            .attr("fill", getTextFill(d)) // 根据数据是否异常设置文本颜色
                            .text(`${d['地层名称']} (${topPos.toFixed(2)}, ${bottomPos.toFixed(2)})`);
                        
                        // 添加双击事件来编辑地层信息
                        group.on("dblclick", function(event, d) {
                            showEditModal(d);
                        });
                        
                        // 添加拖拽手柄（左边）
                        const leftHandle = group.append("rect")
                            .attr("class", "drag-handle")
                            .attr("x", finalX - 4)
                            .attr("y", rectY)
                            .attr("width", 8)
                            .attr("height", effectiveHeight)
                            .attr("cursor", "ew-resize")
                            .attr("data-side", "left");
                        
                        // 添加拖拽手柄（右边）
                        const rightHandle = group.append("rect")
                            .attr("class", "drag-handle")
                            .attr("x", finalX + finalWidth - 4)
                            .attr("y", rectY)
                            .attr("width", 8)
                            .attr("height", effectiveHeight)
                            .attr("cursor", "ew-resize")
                            .attr("data-side", "right");
                        
                        // 添加拖拽功能（仅调整顶界/底界）
                        const dragBehavior = d3.drag()
                            .on("start", dragStarted)
                            .on("drag", dragged)
                            .on("end", dragEnded);
                        
                        group.call(dragBehavior);
                        
                        // 为手柄也添加拖拽功能
                        leftHandle.call(dragBehavior);
                        rightHandle.call(dragBehavior);
                    });
                    
                    rowIndex++;
                }
            } else {
                // 处理没有数据的地层 - 显示空行
                const yPos = yScale(rowIndex);
                const bandHeight = yScale.bandwidth();
                
                // 绘制背景条带
                g.append("rect")
                    .attr("class", "layer-band")
                    .attr("x", margin.left)
                    .attr("y", yPos)
                    .attr("width", width - margin.left - margin.right)
                    .attr("height", bandHeight)
                    .attr("fill", isNewLayer ? "#D3D3D3" : "#f8f9fa"); // 新层位灰色背景
                
                // 添加Y轴标签
                g.append("text")
                    .attr("class", "layer-text")
                    .attr("x", margin.left - 10)
                    .attr("y", yPos + bandHeight / 2)
                    .attr("text-anchor", "end")
                    .text(stratName);
                
                // 绘制粗虚线分隔符（除了第一个大层）
                if (lastStratName !== null) {
                    g.append("line")
                        .attr("x1", margin.left)
                        .attr("x2", width - margin.right)
                        .attr("y1", yPos - 5)
                        .attr("y2", yPos - 5)
                        .attr("stroke", "#333")
                        .attr("stroke-width", 2)
                        .attr("stroke-dasharray", "8,4");
                }
                
                lastStratName = stratName;
                rowIndex++;
            }
        }
        
        // 也要处理不在初始顺序中的层位（如果有的话）
        let firstNewLayerExpandedFallback = true;
        for (const [stratName, subData] of groupedData) {
            if (!initialStratigraphyOrder.includes(stratName)) {
                // 绘制红色分隔线（仅在第一个新层位上方绘制）
                if (firstNewLayerExpandedFallback) {
                    const yPos = yScale(rowIndex);

                    // 绘制背景大矩形
                    const bottomY = yScale.range()[1];
                    g.append("rect")
                        .attr("x", margin.left)
                        .attr("y", yPos - 2)
                        .attr("width", width - margin.left - margin.right)
                        .attr("height", bottomY - (yPos - 2))
                        .attr("fill", "#E0E0E0")
                        .attr("opacity", 0.5);

                    g.append("line")
                        .attr("x1", margin.left)
                        .attr("x2", width - margin.right)
                        .attr("y1", yPos - 2)
                        .attr("y2", yPos - 2)
                        .attr("stroke", "red")
                        .attr("stroke-width", 2);
                    firstNewLayerExpandedFallback = false;
                }

                const uniqueFormations = [...new Set(subData.map(d => d['地层名称']))];

                if (uniqueFormations.length > 1) {
                    // 有多个地层，展开显示
                    uniqueFormations.forEach((formationName, formationIdx) => {
                        const filteredData = subData.filter(d => d['地层名称'] === formationName);
                        // 在展开模式下，每个地层有自己的y位置，但标签仍然是大层名
                        const yPos = yScale(rowIndex);
                        const bandHeight = yScale.bandwidth();
                        const effectiveHeight = bandHeight * 0.8; // 使用部分高度
                        const rectY = yPos + (bandHeight - effectiveHeight) / 2;

                        // 绘制背景条带
                        g.append("rect")
                            .attr("class", "layer-band")
                            .attr("x", margin.left)
                            .attr("y", yPos)
                            .attr("width", width - margin.left - margin.right)
                            .attr("height", bandHeight)
                            .attr("fill", "#D3D3D3"); // 新层位灰色背景

                        // 只在第一个子地层位置显示大层标签
                        if (formationIdx === 0) {
                            g.append("text")
                                .attr("class", "layer-text")
                                .attr("x", margin.left - 10)
                                .attr("y", yPos + bandHeight / 2)
                                .attr("text-anchor", "end")
                                .text(stratName);  // 只显示所属层位名称

                            // 绘制粗虚线分隔符（除了第一个大层）
                            if (lastStratName !== null) {
                                g.append("line")
                                    .attr("x1", margin.left)
                                    .attr("x2", width - margin.right)
                                    .attr("y1", yPos - 5)
                                    .attr("y2", yPos - 5)
                                    .attr("stroke", "#333")
                                    .attr("stroke-width", 2)
                                    .attr("stroke-dasharray", "8,4");
                            }

                            lastStratName = stratName;
                        }

                        // 绘制该地层的数据
                        filteredData.forEach((d, idx) => {
                            const topPos = parseFloat(d['顶界所处位置（0~1）']);
                            const bottomPos = parseFloat(d['底界所处位置（0~1）']);

                            // 验证数据有效性
                            if (isNaN(topPos) || isNaN(bottomPos) ||
                                topPos < 0 || topPos > 1 ||
                                bottomPos < 0 || bottomPos > 1) {
                                return; // 跳过无效数据
                            }

                            // 计算矩形的位置和尺寸
                            const leftPos = Math.min(topPos, bottomPos);
                            const widthValue = Math.abs(bottomPos - topPos);
                            const rectWidth = widthValue * (width - margin.left - margin.right);
                            const rectX = xScale(leftPos);

                            // 确保最小宽度
                            const minWidth = 10; // 像素
                            let finalWidth = Math.max(rectWidth, minWidth);
                            let finalX = rectX;
                            if (rectWidth < minWidth) {
                                const centerPos = (topPos + bottomPos) / 2;
                                finalX = xScale(centerPos) - minWidth / 2;
                            }

                            // 获取颜色
                            const color = getColorForData(d);

                            // 创建容器组
                            const group = g.append("g")
                                .attr("class", "formation-group")
                                .attr("data-formation", d['地层名称'])
                                .attr("data-original-strat", d['所属层位'])
                                .datum(d);

                            // 绘制地层矩形
                            const rect = group.append("rect")
                                .attr("class", "formation-rect")
                                .attr("x", finalX)
                                .attr("y", rectY)
                                .attr("width", finalWidth)
                                .attr("height", effectiveHeight)
                                .attr("fill", isNewLayer ? color : color)
                                .attr("opacity", isDataAbnormal(d) ? 1.0 : (isNewLayer ? 0.2 : 0.8))
                                .attr("stroke", isNewLayer ? "black" : "none")
                                .attr("stroke-width", isNewLayer ? 2 : 0)
                                .attr("data-top", topPos)
                                .attr("data-bottom", bottomPos)
                                .attr("data-strat", stratName);
                            
                            // 添加地层名称文本
                            group.append("text")
                                .attr("class", "formation-text")
                                .attr("x", finalX + finalWidth / 2)
                                .attr("y", rectY + effectiveHeight / 2)
                                .attr("fill", getTextFill(d)) // 根据数据是否异常设置文本颜色
                                .text(`${d['地层名称']} (${topPos.toFixed(2)}, ${bottomPos.toFixed(2)})`);
                            
                            // 添加双击事件来编辑地层信息
                            group.on("dblclick", function(event, d) {
                                showEditModal(d);
                            });
                            
                            // 添加拖拽手柄（仅用于调整顶界/底界，不用于更改归属）
                            const leftHandle = group.append("rect")
                                .attr("class", "drag-handle")
                                .attr("x", finalX - 4)
                                .attr("y", rectY)
                                .attr("width", 8)
                                .attr("height", effectiveHeight)
                                .attr("cursor", "ew-resize")
                                .attr("data-side", "left");
                            
                            // 添加拖拽手柄（右边）
                            const rightHandle = group.append("rect")
                                .attr("class", "drag-handle")
                                .attr("x", finalX + finalWidth - 4)
                                .attr("y", rectY)
                                .attr("width", 8)
                                .attr("height", effectiveHeight)
                                .attr("cursor", "ew-resize")
                                .attr("data-side", "right");
                            
                            // 添加拖拽功能（仅调整顶界/底界）
                            const dragBehavior = d3.drag()
                                .on("start", dragStarted)
                                .on("drag", dragged)
                                .on("end", dragEnded);
                            
                            group.call(dragBehavior);
                            
                            // 为手柄也添加拖拽功能
                            leftHandle.call(dragBehavior);
                            rightHandle.call(dragBehavior);
                        });
                        
                        rowIndex++;
                    });
                } else {
                    // 只有一个地层，正常显示
                    const yPos = yScale(rowIndex);
                    const bandHeight = yScale.bandwidth();
                    const effectiveHeight = bandHeight * 0.8; // 使用部分高度
                    const rectY = yPos + (bandHeight - effectiveHeight) / 2;
                    
                    // 绘制背景条带
                    g.append("rect")
                        .attr("class", "layer-band")
                        .attr("x", margin.left)
                        .attr("y", yPos)
                        .attr("width", width - margin.left - margin.right)
                        .attr("height", bandHeight);
                    
                    // 添加Y轴标签 - 只有当这个层位尚未显示标签时才显示
                    if (stratName !== lastStratName) {
                        g.append("text")
                            .attr("class", "layer-text")
                            .attr("x", margin.left - 10)
                            .attr("y", yPos + bandHeight / 2)
                            .attr("text-anchor", "end")
                            .text(stratName);  // 只显示所属层位名称
                    }
                    
                    // 绘制粗虚线分隔符（除了第一个大层）
                    if (lastStratName !== null && stratName !== lastStratName) {
                        g.append("line")
                            .attr("x1", margin.left)
                            .attr("x2", width - margin.right)
                            .attr("y1", yPos - 5)
                            .attr("y2", yPos - 5)
                            .attr("stroke", "#333")
                            .attr("stroke-width", 2)
                            .attr("stroke-dasharray", "8,4");
                    }
                    
                    lastStratName = stratName;
                    
                    // 绘制数据
                    subData.forEach((d, idx) => {
                        const topPos = parseFloat(d['顶界所处位置（0~1）']);
                        const bottomPos = parseFloat(d['底界所处位置（0~1）']);
                        
                        // 验证数据有效性
                        if (isNaN(topPos) || isNaN(bottomPos) || 
                            topPos < 0 || topPos > 1 || 
                            bottomPos < 0 || bottomPos > 1) {
                            return; // 跳过无效数据
                        }
                        
                        // 计算矩形的位置和尺寸
                        const leftPos = Math.min(topPos, bottomPos);
                        const widthValue = Math.abs(bottomPos - topPos);
                        const rectWidth = widthValue * (width - margin.left - margin.right);
                        const rectX = xScale(leftPos);
                        
                        // 确保最小宽度
                        const minWidth = 10; // 像素
                        let finalWidth = Math.max(rectWidth, minWidth);
                        let finalX = rectX;
                        if (rectWidth < minWidth) {
                            const centerPos = (topPos + bottomPos) / 2;
                            finalX = xScale(centerPos) - minWidth / 2;
                        }
                        
                        // 获取颜色
                        const color = getColorForData(d);
                        
                        // 创建容器组
                        const group = g.append("g")
                            .attr("class", "formation-group")
                            .attr("data-formation", d['地层名称'])
                            .attr("data-original-strat", d['所属层位'])
                            .datum(d);
                        
                        // 绘制地层矩形
                        const rect = group.append("rect")
                            .attr("class", "formation-rect")
                            .attr("x", finalX)
                            .attr("y", rectY)
                            .attr("width", finalWidth)
                            .attr("height", effectiveHeight)
                            .attr("fill", isNewLayer ? color : color)
                            .attr("opacity", isDataAbnormal(d) ? 1.0 : (isNewLayer ? 0.2 : 0.8))
                            .attr("stroke", isNewLayer ? "black" : "none")
                            .attr("stroke-width", isNewLayer ? 2 : 0)
                            .attr("data-top", topPos)
                            .attr("data-bottom", bottomPos)
                            .attr("data-strat", stratName);
                        
                        // 添加地层名称文本
                        group.append("text")
                            .attr("class", "formation-text")
                            .attr("x", finalX + finalWidth / 2)
                            .attr("y", rectY + effectiveHeight / 2)
                            .attr("fill", getTextFill(d)) // 根据数据是否异常设置文本颜色
                            .text(`${d['地层名称']} (${topPos.toFixed(2)}, ${bottomPos.toFixed(2)})`);
                        
                        // 添加双击事件来编辑地层信息
                        group.on("dblclick", function(event, d) {
                            showEditModal(d);
                        });
                        
                        // 添加拖拽手柄（左边）
                        const leftHandle = group.append("rect")
                            .attr("class", "drag-handle")
                            .attr("x", finalX - 4)
                            .attr("y", rectY)
                            .attr("width", 8)
                            .attr("height", effectiveHeight)
                            .attr("cursor", "ew-resize")
                            .attr("data-side", "left");
                        
                        // 添加拖拽手柄（右边）
                        const rightHandle = group.append("rect")
                            .attr("class", "drag-handle")
                            .attr("x", finalX + finalWidth - 4)
                            .attr("y", rectY)
                            .attr("width", 8)
                            .attr("height", effectiveHeight)
                            .attr("cursor", "ew-resize")
                            .attr("data-side", "right");
                        
                        // 添加拖拽功能（仅调整顶界/底界）
                        const dragBehavior = d3.drag()
                            .on("start", dragStarted)
                            .on("drag", dragged)
                            .on("end", dragEnded);
                        
                        group.call(dragBehavior);
                        
                        // 为手柄也添加拖拽功能
                        leftHandle.call(dragBehavior);
                        rightHandle.call(dragBehavior);
                    });
                    
                    rowIndex++;
                }
            }
        }
    } else {
        // 正常模式渲染，按照初始地层顺序
        let rowIndex = 0;
        let lastStratName = null;
        let firstNewLayerNormal = true;

        // 按照初始地层顺序遍历
        for (const stratName of initialStratigraphyOrder) {
            const subData = groupedData.get(stratName) || [];
            // if (subData.length > 0) { // 移除此判断以显示所有地层
            const yPos = yScale(stratName); // 使用层位名称作为y轴域的键
            const bandHeight = yScale.bandwidth();
            const effectiveHeight = bandHeight * 0.8; // 使用部分高度
            const rectY = yPos + (bandHeight - effectiveHeight) / 2;

            // 判断是否为新层位: 不在参考顺序中，且参考顺序不为空
            const isNewLayer = referenceOrder.length > 0 && !referenceOrder.includes(stratName);

            // 如果是新层位且是第一个，绘制红色分隔线
            if (isNewLayer && firstNewLayerNormal) {
                // 绘制背景大矩形
                const bottomY = yScale.range()[1];
                g.append("rect")
                    .attr("x", margin.left)
                    .attr("y", yPos - 5)
                    .attr("width", width - margin.left - margin.right)
                    .attr("height", bottomY - (yPos - 5))
                    .attr("fill", "#E0E0E0")
                    .attr("opacity", 0.5);

                g.append("line")
                    .attr("x1", margin.left)
                    .attr("x2", width - margin.right)
                    .attr("y1", yPos - 5) // 稍微向上一点
                    .attr("y2", yPos - 5)
                    .attr("stroke", "red")
                    .attr("stroke-width", 2);
                firstNewLayerNormal = false;
            }

            // 绘制背景条带
            g.append("rect")
                .attr("class", "layer-band")
                .attr("x", margin.left)
                .attr("y", yPos)
                .attr("width", width - margin.left - margin.right)
                .attr("height", bandHeight)
                .attr("fill", isNewLayer ? "#D3D3D3" : "#f8f9fa"); // 新层位灰色背景
                
                // 添加Y轴标签
                g.append("text")
                    .attr("class", "layer-text")
                    .attr("x", margin.left - 10)
                    .attr("y", yPos + bandHeight / 2)
                    .attr("text-anchor", "end")
                    .text(stratName);  // 只显示所属层位名称
                
                // 绘制数据
                subData.forEach((d, idx) => {
                    const topPos = parseFloat(d['顶界所处位置（0~1）']);
                    const bottomPos = parseFloat(d['底界所处位置（0~1）']);
                    
                    // 验证数据有效性
                    if (isNaN(topPos) || isNaN(bottomPos) || 
                        topPos < 0 || topPos > 1 || 
                        bottomPos < 0 || bottomPos > 1) {
                        return; // 跳过无效数据
                    }
                    
                    // 计算矩形的位置和尺寸
                    const leftPos = Math.min(topPos, bottomPos);
                    const widthValue = Math.abs(bottomPos - topPos);
                    const rectWidth = widthValue * (width - margin.left - margin.right);
                    const rectX = xScale(leftPos);
                    
                    // 确保最小宽度
                    const minWidth = 10; // 像素
                    let finalWidth = Math.max(rectWidth, minWidth);
                    let finalX = rectX;
                    if (rectWidth < minWidth) {
                        const centerPos = (topPos + bottomPos) / 2;
                        finalX = xScale(centerPos) - minWidth / 2;
                    }
                    
                    // 获取颜色
                    const color = getColorForData(d);
                    
                    // 创建容器组
                    const group = g.append("g")
                        .attr("class", "formation-group")
                        .attr("data-formation", d['地层名称'])
                        .attr("data-original-strat", d['所属层位'])
                        .datum(d);
                    
                    // 绘制地层矩形
                    const rect = group.append("rect")
                        .attr("class", "formation-rect")
                        .attr("x", finalX)
                        .attr("y", rectY)
                        .attr("width", finalWidth)
                        .attr("height", effectiveHeight)
                        .attr("fill", isNewLayer ? color : color)
                        .attr("opacity", isDataAbnormal(d) ? 1.0 : (isNewLayer ? 0.2 : 0.8))
                        .attr("stroke", isNewLayer ? "black" : "none")
                        .attr("stroke-width", isNewLayer ? 2 : 0)
                        .attr("data-top", topPos)
                        .attr("data-bottom", bottomPos)
                        .attr("data-strat", stratName);
                    
                    // 添加地层名称文本
                    group.append("text")
                        .attr("class", "formation-text")
                        .attr("x", finalX + finalWidth / 2)
                        .attr("y", rectY + effectiveHeight / 2)
                        .attr("fill", getTextFill(d)) // 根据数据是否异常设置文本颜色
                        .text(`${d['地层名称']} (${topPos.toFixed(2)}, ${bottomPos.toFixed(2)})`);
                    
                    // 添加双击事件来编辑地层信息
                    group.on("dblclick", function(event, d) {
                        showEditModal(d);
                    });
                    
                    // 添加拖拽手柄（左边）
                    const leftHandle = group.append("rect")
                        .attr("class", "drag-handle")
                        .attr("x", finalX - 4)
                        .attr("y", rectY)
                        .attr("width", 8)
                        .attr("height", effectiveHeight)
                        .attr("cursor", "ew-resize")
                        .attr("data-side", "left");
                    
                    // 添加拖拽手柄（右边）
                    const rightHandle = group.append("rect")
                        .attr("class", "drag-handle")
                        .attr("x", finalX + finalWidth - 4)
                        .attr("y", rectY)
                        .attr("width", 8)
                        .attr("height", effectiveHeight)
                        .attr("cursor", "ew-resize")
                        .attr("data-side", "right");
                    
                    // 添加拖拽功能（仅调整顶界/底界）
                    const dragBehavior = d3.drag()
                        .on("start", dragStarted)
                        .on("drag", dragged)
                        .on("end", dragEnded);
                    
                    group.call(dragBehavior);
                    
                    // 为手柄也添加拖拽功能
                    leftHandle.call(dragBehavior);
                    rightHandle.call(dragBehavior);
                });

                rowIndex++;
        }

        // 也要处理不在初始顺序中的层位（如果有的话）
        // 注意：由于我们在后端已经将所有出现的层位整合进了 initialStratigraphyOrder（通过 final_strat_list），
        // 所以理论上这里不需要再遍历 groupedData 中不在 initialStratigraphyOrder 的项了。
        // 但为了保险起见，或者如果后端逻辑有变，保留此循环，并添加相同的逻辑。

        for (const [stratName, subData] of groupedData) {
            if (!initialStratigraphyOrder.includes(stratName)) {
                const yPos = yScale(stratName); // 使用层位名称作为y轴域的键
                const bandHeight = yScale.bandwidth();
                const effectiveHeight = bandHeight * 0.8; // 使用部分高度
                const rectY = yPos + (bandHeight - effectiveHeight) / 2;

                 // 这些肯定都是新层位（不在初始顺序中，肯定也不在参考顺序中）
                 const isNewLayer = true;

                // 绘制红色分隔线（仅在第一个新层位上方绘制）
                if (firstNewLayerNormal) {
                    // 绘制背景大矩形
                    const bottomY = yScale.range()[1];
                    g.append("rect")
                        .attr("x", margin.left)
                        .attr("y", yPos - 5)
                        .attr("width", width - margin.left - margin.right)
                        .attr("height", bottomY - (yPos - 5))
                        .attr("fill", "#E0E0E0")
                        .attr("opacity", 0.5);

                    g.append("line")
                        .attr("x1", margin.left)
                        .attr("x2", width - margin.right)
                        .attr("y1", yPos - 5)
                        .attr("y2", yPos - 5)
                        .attr("stroke", "red")
                        .attr("stroke-width", 2);
                    firstNewLayerNormal = false;
                }

                // 绘制背景条带
                g.append("rect")
                    .attr("class", "layer-band")
                    .attr("x", margin.left)
                    .attr("y", yPos)
                    .attr("width", width - margin.left - margin.right)
                    .attr("height", bandHeight)
                    .attr("fill", "#D3D3D3"); // 新层位灰色背景

                // 添加Y轴标签
                g.append("text")
                    .attr("class", "layer-text")
                    .attr("x", margin.left - 10)
                    .attr("y", yPos + bandHeight / 2)
                    .attr("text-anchor", "end")
                    .text(stratName);  // 只显示所属层位名称

                // 绘制数据
                subData.forEach((d, idx) => {
                    const topPos = parseFloat(d['顶界所处位置（0~1）']);
                    const bottomPos = parseFloat(d['底界所处位置（0~1）']);

                    // 验证数据有效性
                    if (isNaN(topPos) || isNaN(bottomPos) ||
                        topPos < 0 || topPos > 1 ||
                        bottomPos < 0 || bottomPos > 1) {
                        return; // 跳过无效数据
                    }

                    // 计算矩形的位置和尺寸
                    const leftPos = Math.min(topPos, bottomPos);
                    const widthValue = Math.abs(bottomPos - topPos);
                    const rectWidth = widthValue * (width - margin.left - margin.right);
                    const rectX = xScale(leftPos);

                    // 确保最小宽度
                    const minWidth = 10; // 像素
                    let finalWidth = Math.max(rectWidth, minWidth);
                    let finalX = rectX;
                    if (rectWidth < minWidth) {
                        const centerPos = (topPos + bottomPos) / 2;
                        finalX = xScale(centerPos) - minWidth / 2;
                    }

                    // 获取颜色
                    const color = getColorForData(d);

                    // 创建容器组
                    const group = g.append("g")
                        .attr("class", "formation-group")
                        .attr("data-formation", d['地层名称'])
                        .attr("data-original-strat", d['所属层位'])
                        .datum(d);

                    // 绘制地层矩形
                    const rect = group.append("rect")
                        .attr("class", "formation-rect")
                        .attr("x", finalX)
                        .attr("y", rectY)
                        .attr("width", finalWidth)
                        .attr("height", effectiveHeight)
                        .attr("fill", isNewLayer ? color : color)
                        .attr("opacity", isDataAbnormal(d) ? 1.0 : (isNewLayer ? 0.2 : 0.8))
                        .attr("stroke", isNewLayer ? "black" : "none")
                        .attr("stroke-width", isNewLayer ? 2 : 0)
                        .attr("data-top", topPos)
                        .attr("data-bottom", bottomPos)
                        .attr("data-strat", stratName);
                    
                    // 添加地层名称文本
                    group.append("text")
                        .attr("class", "formation-text")
                        .attr("x", finalX + finalWidth / 2)
                        .attr("y", rectY + effectiveHeight / 2)
                        .attr("fill", getTextFill(d)) // 根据数据是否异常设置文本颜色
                        .text(`${d['地层名称']} (${topPos.toFixed(2)}, ${bottomPos.toFixed(2)})`);
                    
                    // 添加双击事件来编辑地层信息
                    group.on("dblclick", function(event, d) {
                        showEditModal(d);
                    });
                    
                    // 添加拖拽手柄（左边）
                    const leftHandle = group.append("rect")
                        .attr("class", "drag-handle")
                        .attr("x", finalX - 4)
                        .attr("y", rectY)
                        .attr("width", 8)
                        .attr("height", effectiveHeight)
                        .attr("cursor", "ew-resize")
                        .attr("data-side", "left");
                    
                    // 添加拖拽手柄（右边）
                    const rightHandle = group.append("rect")
                        .attr("class", "drag-handle")
                        .attr("x", finalX + finalWidth - 4)
                        .attr("y", rectY)
                        .attr("width", 8)
                        .attr("height", effectiveHeight)
                        .attr("cursor", "ew-resize")
                        .attr("data-side", "right");
                    
                    // 添加拖拽功能（仅调整顶界/底界）
                    const dragBehavior = d3.drag()
                        .on("start", dragStarted)
                        .on("drag", dragged)
                        .on("end", dragEnded);
                    
                    group.call(dragBehavior);
                    
                    // 为手柄也添加拖拽功能
                    leftHandle.call(dragBehavior);
                    rightHandle.call(dragBehavior);
                });
                
                rowIndex++;
            }
        }
    }
    
    // 添加图例
    addLegend();
}

// 存储当前显示状态的对象
let currentDisplayState = {
    showingOnly: null // null 表示显示全部，否则为特定地层名称
};

function addLegend() {
    // 获取所有唯一的地层名称
    const uniqueFormations = [...new Set(rawData.map(d => d['地层名称']))];
    
    // 清空现有的图例内容
    const legendContainer = document.getElementById('legend-content');
    if (legendContainer) {
        legendContainer.innerHTML = '';
        
        // 为每个地层创建图例项
        uniqueFormations.forEach(formation => {
            // 检查该地层是否有任何异常数据
            const formationData = rawData.filter(d => d['地层名称'] === formation);
            const hasAbnormalData = formationData.some(d => isDataAbnormal(d));
            
            // 如果有任何一条数据异常，则使用黑色作为图例颜色
            const color = hasAbnormalData ? '#000000' : colorScale(formation);
            
            const legendItem = document.createElement('div');
            legendItem.className = 'legend-item';
            legendItem.setAttribute('data-formation', formation);
            
            legendItem.innerHTML = `
                <div class="legend-color" style="background-color: ${color}"></div>
                <div class="legend-label" title="${formation}">${formation}</div>
            `;
            
            // 添加点击事件 - 高亮显示
            legendItem.addEventListener('click', function() {
                highlightFormation(formation);
            });
            
            // 添加双击事件 - 切换显示状态
            legendItem.addEventListener('dblclick', function() {
                toggleFormationVisibility(formation);
            });
            
            legendContainer.appendChild(legendItem);
        });
    }
}

// 切换地层显示状态（双击图例时调用）
function toggleFormationVisibility(formationName) {
    // 如果当前正在显示特定地层，且双击的是同一个地层，则恢复显示所有地层
    if (currentDisplayState.showingOnly === formationName) {
        // 恢复显示所有地层
        showAllFormations();
        currentDisplayState.showingOnly = null;
        
        // 更新图例样式
        document.querySelectorAll('.legend-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // 更新状态栏
        document.getElementById('status-text').textContent = '已恢复显示所有地层';
    } else {
        // 只显示选中的地层
        hideOtherFormations(formationName);
        currentDisplayState.showingOnly = formationName;
        
        // 更新图例样式，只选中当前激活的图例
        document.querySelectorAll('.legend-item').forEach(item => {
            item.classList.remove('selected');
        });
        const selectedLegendItem = document.querySelector(`.legend-item[data-formation="${formationName}"]`);
        if (selectedLegendItem) {
            selectedLegendItem.classList.add('selected');
        }
        
        // 更新状态栏
        document.getElementById('status-text').textContent = `仅显示地层: ${formationName}`;
    }
}

// 显示所有地层
function showAllFormations() {
    d3.selectAll(".formation-rect, .formation-text, .drag-handle")
        .transition()
        .duration(300)
        .style("opacity", function(d) {
            // 恢复原始透明度，异常数据保持黑色，正常数据保持原有颜色
            return isDataAbnormal(d) ? 1.0 : 0.7;
        })
        .style("visibility", "visible");
}

// 隐藏其他地层，只显示指定地层
function hideOtherFormations(formationName) {
    d3.selectAll(".formation-rect, .formation-text, .drag-handle")
        .transition()
        .duration(300)
        .style("opacity", function(d) {
            return d['地层名称'] === formationName ? 1.0 : 0.1;
        })
        .style("visibility", function(d) {
            return d['地层名称'] === formationName ? "visible" : "hidden";
        });
}

// 高亮显示指定地层
function highlightFormation(formationName) {
    // 如果当前处于只显示某个地层的状态，先恢复显示所有地层
    if (currentDisplayState.showingOnly !== null) {
        showAllFormations();
        currentDisplayState.showingOnly = null;
        
        // 更新图例样式
        document.querySelectorAll('.legend-item').forEach(item => {
            item.classList.remove('selected');
        });
    }
    
    // 为当前选中的图例项添加选中样式
    const selectedLegendItem = document.querySelector(`.legend-item[data-formation="${formationName}"]`);
    if (selectedLegendItem) {
        selectedLegendItem.classList.add('selected');
    }
    
    // 重置所有地层的样式
    d3.selectAll(".formation-rect")
        .transition()
        .duration(300)
        .attr("opacity", function(d) {
            // 异常数据保持黑色显示，正常数据使用较低透明度
            return isDataAbnormal(d) ? 1.0 : 0.4;
        })
        .attr("stroke", null)
        .attr("stroke-width", null)
        .attr("stroke-dasharray", null);
    
    // 同时重置拖拽手柄的样式
    d3.selectAll(".drag-handle")
        .transition()
        .duration(300)
        .attr("opacity", 0.7);
    
    // 高亮选中的地层，添加动画效果
    d3.selectAll(".formation-rect")
        .filter(function(d) {
            return d['地层名称'] === formationName;
        })
        .transition()
        .duration(300)
        .attr("opacity", 1.0) // 完全不透明
        .attr("stroke", "#ff6b35")
        .attr("stroke-width", 3)
        .attr("stroke-dasharray", "5,5"); // 添加虚线边框
    
    // 高亮选中的地层的拖拽手柄
    d3.selectAll(".drag-handle")
        .filter(function(d) {
            return d['地层名称'] === formationName;
        })
        .transition()
        .duration(300)
        .attr("opacity", 1.0);
    
    // 同时高亮相关的文本
    d3.selectAll(".formation-text")
        .filter(function(d) {
            return d['地层名称'] === formationName;
        })
        .transition()
        .duration(300)
        .attr("font-weight", "bold")
        .attr("font-size", "13px")
        .attr("fill", function(d) {
            // 为高亮的地层使用适当的文本颜色
            return isDataAbnormal(d) ? '#ffffff' : '#000000';
        });
    
    // 重置其他文本样式
    d3.selectAll(".formation-text")
        .filter(function(d) {
            return d['地层名称'] !== formationName;
        })
        .transition()
        .duration(300)
        .attr("font-weight", "normal")
        .attr("font-size", "11px");
    
    // 更新状态栏
    document.getElementById('status-text').textContent = `已选中地层: ${formationName}`;
}

function dragStarted(event, d) {
    d3.select(this).raise().attr("stroke", "#000").attr("stroke-width", 2);
}

function dragged(event, d) {
    // 获取当前元素
    const element = d3.select(this);
    const parentGroup = element.node().parentNode;
    const groupSelection = d3.select(parentGroup);
    
    // 获取原始数据
    const originalData = groupSelection.datum();
    
    // 判断是拖拽整个矩形还是手柄
    const isHandle = element.classed("drag-handle");
    const side = element.attr("data-side");
    
    if (isHandle && side) {
        // 调整边界的手柄
        adjustBoundary(groupSelection, side, event.x);
    } else {
        // 整体拖拽移动位置
        moveFormation(groupSelection, event.x);
    }
}

function adjustBoundary(group, side, mouseX) {
    const rect = group.select(".formation-rect");
    const text = group.select(".formation-text");
    const leftHandle = group.select(".drag-handle[data-side='left']");
    const rightHandle = group.select(".drag-handle[data-side='right']");
    
    // 将鼠标位置转换为数据值
    const newValue = xScale.invert(mouseX);
    
    // 获取当前的地层数据
    const formationData = group.datum();
    let topPos = parseFloat(formationData['顶界所处位置（0~1）']);
    let bottomPos = parseFloat(formationData['底界所处位置（0~1）']);
    
    // 更新相应的边界
    if (side === 'left') {
        topPos = Math.max(0, Math.min(1, newValue)); // 限制在0-1范围内
    } else if (side === 'right') {
        bottomPos = Math.max(0, Math.min(1, newValue)); // 限制在0-1范围内
    }
    
    // 确保top <= bottom (或根据业务逻辑决定是否需要交换)
    if (topPos > bottomPos) {
        [topPos, bottomPos] = [bottomPos, topPos]; // 交换值
    }
    
    // 更新数据
    formationData['顶界所处位置（0~1）'] = topPos;
    formationData['底界所处位置（0~1）'] = bottomPos;
    
    // 重新计算位置和宽度
    const leftPos = Math.min(topPos, bottomPos);
    const widthValue = Math.abs(bottomPos - topPos);
    const newWidth = widthValue * (xScale.range()[1] - xScale.range()[0]);
    const newX = xScale(leftPos);
    
    // 更新图形元素
    rect
        .attr("x", newX)
        .attr("width", newWidth);
    
    text
        .attr("x", newX + newWidth / 2);
    
    leftHandle
        .attr("x", newX - 4);
    
    rightHandle
        .attr("x", newX + newWidth - 4);
    
    // 更新文本内容
    text.text(`${formationData['地层名称']} (${topPos.toFixed(2)}, ${bottomPos.toFixed(2)})`);
    
    // 更新数据存储
    rect.attr("data-top", topPos);
    rect.attr("data-bottom", bottomPos);
    
    // 更新原始数据数组
    updateRawDataFromGroup(group, formationData);
}

function moveFormation(group, mouseX) {
    // 获取当前元素
    const rect = group.select(".formation-rect");
    const text = group.select(".formation-text");
    const leftHandle = group.select(".drag-handle[data-side='left']");
    const rightHandle = group.select(".drag-handle[data-side='right']");
    
    // 获取当前的地层数据
    const formationData = group.datum();
    const topPos = parseFloat(formationData['顶界所处位置（0~1）']);
    const bottomPos = parseFloat(formationData['底界所处位置（0~1）']);
    
    // 计算当前宽度
    const widthValue = Math.abs(bottomPos - topPos);
    const currentWidth = widthValue * (xScale.range()[1] - xScale.range()[0]);
    
    // 计算新的起始位置（保持宽度不变）
    const newX = Math.max(
        xScale(0), 
        Math.min(
            mouseX - currentWidth / 2, 
            xScale(1) - currentWidth
        )
    );
    
    // 将新的X位置转换回数据值
    const newStartPos = xScale.invert(newX);
    const newEndPos = newStartPos + widthValue;
    
    // 更新数据（保持原始宽度，只改变位置）
    formationData['顶界所处位置（0~1）'] = Math.max(0, Math.min(1, newStartPos));
    formationData['底界所处位置（0~1）'] = Math.max(0, Math.min(1, newEndPos));
    
    // 更新图形元素
    rect
        .attr("x", newX);
    
    text
        .attr("x", newX + currentWidth / 2);
    
    leftHandle
        .attr("x", newX - 4);
    
    rightHandle
        .attr("x", newX + currentWidth - 4);
    
    // 更新文本内容
    text.text(`${formationData['地层名称']} (${formationData['顶界所处位置（0~1）'].toFixed(2)}, ${formationData['底界所处位置（0~1）'].toFixed(2)})`);
    
    // 更新数据存储
    rect.attr("data-top", formationData['顶界所处位置（0~1）']);
    rect.attr("data-bottom", formationData['底界所处位置（0~1）']);
    
    // 更新原始数据数组
    updateRawDataFromGroup(group, formationData);
}

function dragEnded(event, d) {
    d3.select(this).attr("stroke", null).attr("stroke-width", null);
}

async function exportData() {
    if (!rawData) {
        alert('没有数据可供导出');
        return;
    }
    
    try {
        document.getElementById('status-text').textContent = '正在处理导出数据...';
        console.log('开始导出数据，记录数:', rawData.length);
        
        // 发送数据到后端进行处理
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data: rawData })
        });
        
        console.log('导出响应状态:', response.status);
        
        const result = await response.json();
        console.log('导出响应数据:', result);
        
        if (result.success) {
            // 创建下载链接
            const downloadUrl = result.download_url;
            window.open(downloadUrl, '_blank');
            
            document.getElementById('status-text').textContent = '数据导出成功，请检查下载文件';
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('数据导出错误:', error);
        document.getElementById('status-text').textContent = `数据导出失败: ${error.message}`;
        alert(`数据导出失败: ${error.message}`);
    }
}

function convertToCSV(data) {
    if (data.length === 0) return '';
    
    // 获取所有键名作为表头
    const headers = Object.keys(data[0]);
    
    // 创建CSV内容
    const csvRows = [];
    csvRows.push(headers.join(','));
    
    // 添加数据行
    for (const row of data) {
        const values = headers.map(header => {
            const value = row[header];
            // 处理包含逗号或引号的值
            return `"${String(value).replace(/"/g, '""')}"`;
        });
        csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
}

// 显示添加小层弹窗
function showAddSmallLayerModal() {
    const modal = document.getElementById('addSmallLayerModal');
    const stratigraphySelect = document.getElementById('addStratigraphy');
    
    // 清空表单
    document.getElementById('addFormationName').value = '';
    document.getElementById('addTopPosition').value = '0.00';
    document.getElementById('addBottomPosition').value = '0.10';
    
    // 填充所属层位下拉选项
    stratigraphySelect.innerHTML = '';
    if (stratigraphyData) {
        stratigraphyData.forEach(strat => {
            const option = document.createElement('option');
            option.value = strat['地层信息'];
            option.textContent = strat['地层信息'];
            stratigraphySelect.appendChild(option);
        });
    }
    
    // 如果没有地层数据，创建一个默认选项
    if (!stratigraphyData || stratigraphyData.length === 0) {
        const option = document.createElement('option');
        option.value = '未分类';
        option.textContent = '未分类';
        stratigraphySelect.appendChild(option);
    }
    
    // 显示弹窗
    modal.style.display = 'block';
}

// 隐藏添加小层弹窗
function hideAddSmallLayerModal() {
    document.getElementById('addSmallLayerModal').style.display = 'none';
}

// 保存新增的小层数据
function saveNewSmallLayer() {
    const formationNameInput = document.getElementById('addFormationName');
    const stratigraphySelect = document.getElementById('addStratigraphy');
    const topPositionInput = document.getElementById('addTopPosition');
    const bottomPositionInput = document.getElementById('addBottomPosition');
    
    // 获取输入值
    const formationName = formationNameInput.value.trim();
    const stratigraphy = stratigraphySelect.value;
    const topPosition = parseFloat(topPositionInput.value);
    const bottomPosition = parseFloat(bottomPositionInput.value);
    
    // 验证输入值
    if (!formationName) {
        alert('请输入地层名称！');
        return;
    }
    
    if (isNaN(topPosition) || isNaN(bottomPosition) || 
        topPosition < 0 || topPosition > 1 || 
        bottomPosition < 0 || bottomPosition > 1 ||
        topPosition >= bottomPosition) {
        alert('请输入有效的数值！顶界应小于底界，且数值应在0-1之间。');
        return;
    }
    
    // 检查地层名称是否已存在
    if (rawData && rawData.some(item => item['地层名称'] === formationName)) {
        alert('该地层名称已存在，请使用其他名称！');
        return;
    }
    
    // 创建新的地层数据对象
    const newFormationData = {
        '地层名称': formationName,
        '所属层位': stratigraphy,
        '顶界所处位置（0~1）': topPosition,
        '底界所处位置（0~1）': bottomPosition
    };
    
    // 添加到原始数据数组
    if (!rawData) {
        rawData = [];
    }
    rawData.push(newFormationData);
    
    // 检查并更新stratigraphyData（如果需要）
    if (stratigraphyData && !stratigraphyData.some(item => item['地层信息'] === stratigraphy)) {
        const newIndex = stratigraphyData.length + 1;
        stratigraphyData.push({
            '地层信息': stratigraphy,
            '序号': newIndex
        });
        // 更新初始地层顺序
        initialStratigraphyOrder.push(stratigraphy);
    }
    
    // 重新渲染可视化
    renderVisualization();
    
    // 隐藏弹窗
    hideAddSmallLayerModal();
    
    // 更新状态信息
    document.getElementById('status-text').textContent = `成功添加新的小层: ${formationName}`;
}

// 更新原始数据数组
function updateRawDataFromGroup(group, formationData) {
    if (!rawData) return;
    
    // 获取原始数据的索引
    const originalTop = group.select('.formation-rect').attr('data-top-org') || formationData['顶界所处位置（0~1）'];
    const originalBottom = group.select('.formation-rect').attr('data-bottom-org') || formationData['底界所处位置（0~1）'];
    const originalStrat = group.attr('data-original-strat') || formationData['所属层位'];
    
    // 在原始数据中查找对应的记录
    const dataIndex = rawData.findIndex(item => 
        item['地层名称'] === formationData['地层名称'] && 
        parseFloat(item['顶界所处位置（0~1）']) === parseFloat(originalTop) &&
        parseFloat(item['底界所处位置（0~1）']) === parseFloat(originalBottom) &&
        item['所属层位'] === originalStrat
    );
    
    if (dataIndex !== -1) {
        rawData[dataIndex]['顶界所处位置（0~1）'] = parseFloat(formationData['顶界所处位置（0~1）']);
        rawData[dataIndex]['底界所处位置（0~1）'] = parseFloat(formationData['底界所处位置（0~1）']);
        
        // 数据更新后，重新计算并更新颜色
        const updatedData = rawData[dataIndex];
        const newColor = getColorForData(updatedData);
        const newTextFill = getTextFill(updatedData);
        
        // 更新矩形颜色
        group.select('.formation-rect')
            .attr('fill', newColor);
        
        // 更新文本颜色
        group.select('.formation-text')
            .attr('fill', newTextFill);
    }
}