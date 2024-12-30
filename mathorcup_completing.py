#20241219 cug 086232 赖恒远
import gurobipy as gp
from gurobipy import Model, GRB
import tkinter as tk
from tkinter import messagebox
import numpy as np
import pandas as pd
import openpyxl
import math as m
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


#前置：数据整理分析导入
file_path = "F:\\mathematical_modeling\\作业\\结课作业\\C\\附件\\附件1：仓库数据.xlsx"
datas_racks = pd.read_excel(file_path, sheet_name='货架')
datas_compartments = pd.read_excel(file_path, sheet_name='货格')
datas_review_stations = pd.read_excel(file_path, sheet_name='复核台')
datas_tasks = pd.read_excel(file_path, sheet_name='任务单')

# 打印列名以检查实际列名
print(datas_compartments.columns)

# 将每一行的货架属性存储在一个字典中
Storage_Racks_dict = {}
for i in range(len(datas_racks)):
    name = datas_racks.loc[i, '货架名称']
    attributes = {
        'x': datas_racks.loc[i, '坐标x毫米'],
        'y': datas_racks.loc[i, '坐标y毫米'],
        'length': datas_racks.loc[i, '货架长毫米'],
        'width': datas_racks.loc[i, '货架宽毫米'],
        'compartment': datas_racks.loc[i, '包含货格'].split('|')
    }
    Storage_Racks_dict[name] = attributes

# 将每一行的货格属性存储在一个字典中
Compartments_dict = {}
for i in range(len(datas_compartments)):
    name = datas_compartments.loc[i, '货格名称']
    attributes = {
        'x': datas_compartments.loc[i, '坐标x毫米'],
        'y': datas_compartments.loc[i, '坐标y毫米'],
        'length': datas_compartments.loc[i, '货格长毫米'],
        'width': datas_compartments.loc[i, '货格宽毫米'],
        'rack': datas_compartments.loc[i, '所属货架']
    }
    Compartments_dict[name] = attributes
    
Review_Stations_dict = {}
for i in range(len(datas_review_stations)):
    name = datas_review_stations.loc[i, '复核台名称']
    attributes = {
        'x': datas_review_stations.loc[i, '坐标x毫米'],
        'y': datas_review_stations.loc[i, '坐标y毫米'],
        'length': datas_review_stations.loc[i, '复核台长毫米'],
        'width': datas_review_stations.loc[i, '复核台宽毫米']
    }
    Review_Stations_dict[name] = attributes

# 将每一行的任务单属性存储在一个字典中
Tasks_dict = {}
for i in range(len(datas_tasks)):
    task_id = datas_tasks.loc[i, '任务单号']
    attributes = {
        'order_id': datas_tasks.loc[i, '订单号'],
        'compartment': datas_tasks.loc[i, '商品货格'],
        'quantity': datas_tasks.loc[i, '商品件数']
    }
    if task_id in Tasks_dict:
        Tasks_dict[task_id]['compartment'].append(attributes['compartment'])
    else:
        Tasks_dict[task_id] = {
            'order_id': attributes['order_id'],
            'compartment': [attributes['compartment']],
            'quantity': attributes['quantity']
        }
    
    

#1.1 复核台距离算法设计：
def extract_middle_two_digits(s):
    # 提取字符串中的所有数字
    digits = ''.join([char for char in s if char.isdigit()])
    # 确保数字长度足够
    if len(digits) >= 4:
        # 提取中间两位数字
        middle_two_digits = digits[1:3]
        return int(middle_two_digits)
    else:
        return None
def shelf_ordinate_range(y):
        """
        根据货格的纵坐标，得到所在货架的纵坐标范围
        """
        if 3000 <= y <= 14200:
            return 3000, 14200
        elif 17000 <= y <= 28200:
            return 17000, 28200
        elif 31000 <= y <= 42200:
            return 31000, 42200
        elif 45000 <= y <= 56200:
            return 45000, 56200
        else:
            return None, None

def is_pass_obstacle(x1, y1, x2, y2, pattern):
        """
        判断是否需要绕过障碍物
        """
        y_min, y_max = shelf_ordinate_range(y2)
        if y_min is None:
            return False  # 不在货架范围内，不需要绕过

        if pattern == 'pp':
            if abs(x1 - x2) > 1500 and y_min < y1 < y_max:
                return True
            else:
                return False
        elif pattern == 'pd':
            if x1 == 1000 and x2 > 3000 and y_min < y1 < y_max:
                return True
            else:
                return False
        else:
            return False


def caculate_distance(start_location, end_location):
    """
    计算start_location到end_location的距离，考虑绕过货架的情况
    """
    bias = 750  # 偏移量，单位：毫米

    # 判断起点和终点是货格还是复核台
    if start_location in Compartments_dict:
        st_x = Compartments_dict[start_location]['x']
        st_y = Compartments_dict[start_location]['y']
        st_loc = 'pavilion'  # 货格
        st_side = 'left' if extract_middle_two_digits(start_location) % 2 != 0 else 'right'
    else:
        st_x = Review_Stations_dict[start_location]['x']
        st_y = Review_Stations_dict[start_location]['y']
        st_loc = 'desk'  # 复核台
        st_side = None  # 复核台无左右侧

    if end_location in Compartments_dict:
        en_x = Compartments_dict[end_location]['x']
        en_y = Compartments_dict[end_location]['y']
        en_loc = 'pavilion'
        en_side = 'left' if extract_middle_two_digits(end_location) % 2 != 0 else 'right'
    else:
        en_x = Review_Stations_dict[end_location]['x']
        en_y = Review_Stations_dict[end_location]['y']
        en_loc = 'desk'
        en_side = None

    def shelf_ordinate_range(y):
        """
        根据货格的纵坐标，得到所在货架的纵坐标范围
        """
        if 3000 <= y <= 14200:
            return 3000, 14200
        elif 17000 <= y <= 28200:
            return 17000, 28200
        elif 31000 <= y <= 42200:
            return 31000, 42200
        elif 45000 <= y <= 56200:
            return 45000, 56200
        else:
            return None, None

    def is_pass_obstacle(x1, y1, x2, y2, pattern):
        """
        判断是否需要绕过障碍物
        """
        y_min, y_max = shelf_ordinate_range(y2)
        if y_min is None:
            return False  # 不在货架范围内，不需要绕过

        if pattern == 'pp':
            if abs(x1 - x2) > 1500 and y_min < y1 < y_max:
                return True
            else:
                return False
        elif pattern == 'pd':
            if x1 == 1000 and x2 > 3000 and y_min < y1 < y_max:
                return True
            else:
                return False
        else:
            return False
    

    # 根据类型选择计算方式
    if st_loc == 'pavilion' and en_loc == 'pavilion':
        # 货格与货格
        is_obstacle = is_pass_obstacle(st_x, st_y, en_x, en_y, 'pp')
        st_x_shifted = st_x - bias if st_side == 'left' else st_x + bias
        en_x_shifted = en_x - bias if en_side == 'left' else en_x + bias

        if is_obstacle:
            y_min, y_max = shelf_ordinate_range(en_y)
            if y_min is None:
                distance = abs(st_x_shifted - en_x_shifted) + abs(st_y - en_y) + 2 * bias
            else:
                distance_top = abs(st_x_shifted - en_x_shifted) + abs(st_y - y_max) + abs(en_y - y_max) + 4 * bias
                distance_bottom = abs(st_x_shifted - en_x_shifted) + abs(st_y - y_min) + abs(en_y - y_min) + 4 * bias
                distance = min(distance_top, distance_bottom)
        else:
            distance = abs(st_x_shifted - en_x_shifted) + abs(st_y - en_y) + 2 * bias

    elif st_loc == 'pavilion' and en_loc == 'desk':
        # 货格与复核台
        is_obstacle = is_pass_obstacle(en_x, en_y, st_x, st_y, 'pd')
        st_x_shifted = st_x - bias if st_side == 'left' else st_x + bias

        if is_obstacle:
            en_x_shifted = en_x + bias  # 复核台在左侧，偏移
            y_min, y_max = shelf_ordinate_range(st_y)
            if y_min is None:
                distance = abs(st_x_shifted - en_x_shifted) + abs(st_y - en_y) + bias
            else:
                distance_top = abs(st_x_shifted - en_x_shifted) + abs(st_y - y_max) + abs(en_y - y_max) + 4 * bias
                distance_bottom = abs(st_x_shifted - en_x_shifted) + abs(st_y - y_min) + abs(en_y - y_min) + 4 * bias
                distance = min(distance_top, distance_bottom)
        else:
            en_x_shifted = en_x  # 复核台不偏移
            distance = abs(st_x_shifted - en_x_shifted) + abs(st_y - en_y) + bias

    elif st_loc == 'desk' and en_loc == 'pavilion':
        # 复核台与货格
        # 与货格与复核台相同
        distance = caculate_distance(end_location, start_location)

    else:
        # 复核台与复核台
        distance = abs(st_x - en_x) + abs(st_y - en_y)
        

    distance = max(distance, 0)  # 确保距离非负

    return distance


tasks_to_compartments = {task_id: attributes['compartment'] for task_id, attributes in Tasks_dict.items()}
tasks_matrix = [attributes['compartment'] for attributes in Tasks_dict.values()]
#问题2 计算时间
options = {
    "WLSACCESSID":"b98c512f-95a5-49f5-a7d2-95b2037a9355",
    "WLSSECRET":"79244a5e-1c1f-4c58-97ac-5e5cbed3fdd6",
    "LICENSEID":2600508,
}

#数据准备：
def check_data(task_id, compartments, pick_nodes):
    """数据验证函数"""
    print(f"\n==== 检查任务单 {task_id} 的数据 ====")
    print(f"原始货格列表: {compartments}")
    print(f"去重后货格数量: {len(pick_nodes)}")
    
    # 检查货格是否存在
    for comp in pick_nodes:
        if comp not in Compartments_dict:
            print(f"警告: 货格 {comp} 不在货格字典中")
            return False
    return True

def solving_problem():
    last_end_point = 'FH10'  # 初始起点
    all_routes = {}  # 存储所有任务的路径
    total_time = 0   # 总时间，单位：秒

    for task_id, compartments in tasks_to_compartments.items():
        print(f"\n============ 处理任务单 {task_id} ============")
        print(f"起始位置: {last_end_point}")
        
        # 构建节点列表
        start_node = last_end_point  # 使用上一个任务的终点作为起点
        pick_nodes = list(set(compartments))
        review_stations = list(Review_Stations_dict.keys())
        
        print(f"拣货点数量: {len(pick_nodes)}")
        print(f"复核台数量: {len(review_stations)}")

        # 构建节点列表
        nodes = [start_node] + pick_nodes + review_stations
        nodes = list(set(nodes))
        
        # 创建模型
        model = gp.Model(f"Picking_Route_{task_id}")
        model.setParam('TimeLimit', 300)
        model.setParam('MIPGap', 0.2)
        model.setParam('OutputFlag', 1)

        try:
            # 创建决策变量
            x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name='x')
            u = model.addVars(nodes, lb=0, ub=len(nodes)-1, vtype=GRB.INTEGER, name='u')

            # 目标函数
            obj = gp.quicksum(caculate_distance(i, j) * x[i,j] 
                            for i in nodes for j in nodes if i != j)
            model.setObjective(obj, GRB.MINIMIZE)

            # 1. 起点约束
            model.addConstr(gp.quicksum(x[start_node,j] 
                          for j in nodes if j != start_node) == 1, 'start_out')
            model.addConstr(gp.quicksum(x[j,start_node] 
                          for j in nodes if j != start_node) == 0, 'no_return_start')

            # 2. 拣货点流量约束
            for i in pick_nodes:
                model.addConstr(gp.quicksum(x[j,i] 
                              for j in nodes if j != i) == 1, f'in_flow_{i}')
                model.addConstr(gp.quicksum(x[i,j] 
                              for j in nodes if j != i) == 1, f'out_flow_{i}')

            # 3. 复核台约束
            # 确保一个复核台作为终点
            model.addConstr(gp.quicksum(x[i,j] 
                          for i in nodes 
                          for j in review_stations if j != start_node) == 1, 'review_end')
            
            # 复核台只能作为终点
            for j in review_stations:
                if j != start_node:  # 排除起点是复核台的情况
                    model.addConstr(gp.quicksum(x[j,k] 
                                  for k in nodes if k != j) == 0, f'no_out_review_{j}')

            # 4. MTZ约束
            model.addConstr(u[start_node] == 0, "start_order")
            
            for i in nodes:
                if i != start_node and i not in review_stations:
                    for j in nodes:
                        if j != start_node and i != j:
                            model.addConstr(
                                u[i] - u[j] + len(nodes) * x[i,j] <= len(nodes) - 1,
                                f'mtz_{i}_{j}'
                            )

            # 求解模型
            model.optimize()

            # 处理结果
            if model.status == GRB.OPTIMAL:
                print(f'\n任务单 {task_id} 的最优总距离：{model.objVal}')
                
                route = []
                current = start_node
                total_distance = 0
                visited = {current}
                
                # 初始化任务时间
                task_time = 0  # 单位：秒
                walking_speed = 1500  # 毫米/秒

                print("\n详细路径:")
                while True:
                    next_node = None
                    for j in nodes:
                        if j != current and x[current,j].X > 0.5:
                            distance = caculate_distance(current, j)
                            distance = max(distance, 0)  # 确保距离非负
                            total_distance += distance
                            route.append((current, j, distance))
                            print(f"{current} -> {j} (距离: {distance:.2f}毫米)")
                            next_node = j
                            visited.add(j)
                            
                            # 计算行走时间
                            walking_time = distance / walking_speed
                            task_time += walking_time

                            # 如果是拣货点，计算下架时间
                            if j in pick_nodes:
                                quantity = get_compartment_quantity(task_id, j)
                                if quantity < 3:
                                    picking_time = quantity * 5
                                else:
                                    picking_time = quantity * 4
                                task_time += picking_time  # 增加下架时间
                            
                            break
                        
                    if next_node is None or next_node in review_stations:
                        last_end_point = next_node  # 更新下一个任务的起点
                        break
                    current = next_node
                
                # 增加复核和打包时间
                task_time += 30  # 30秒

                # 总时间累加
                total_time += task_time

                print('\n路径统计信息:')
                print(f'总距离: {total_distance:.2f}毫米')
                print(f'路径长度: {len(route)}步')
                print(f'已访问拣货点: {len(visited.intersection(set(pick_nodes)))}/{len(pick_nodes)}')
                print(f'任务耗时: {task_time:.2f}秒')
                print(f'终止于: {current}')
                
                all_routes[task_id] = {
                    'route': route,
                    'total_distance': total_distance,
                    'task_time': task_time,   # 记录任务时间
                    'start_point': start_node,
                    'end_point': current
                }
                
            else:
                print(f'\n任务单 {task_id} 未找到最优解')
                print(f'优化状态: {model.status}')
                if model.status == GRB.INFEASIBLE:
                    model.computeIIS()
                    print("\n约束冲突：")
                    for c in model.getConstrs():
                        if c.IISConstr:
                            print(f'- {c.ConstrName}')

        except gp.GurobiError as e:
            print(f"Gurobi错误: {str(e)}")
            continue
        except Exception as e:
            print(f"其他错误: {str(e)}")
            continue
        
    
    # 输出总体统计
    print("\n============ 总体统计 ============")
    total_distance = sum(route['total_distance'] for route in all_routes.values())
    total_tasks = len(all_routes)
    print(f"总任务数: {total_tasks}")
    print(f"总行走距离: {total_distance:.2f}毫米")
    print(f"总耗时: {total_time:.2f}秒")
    
    return all_routes
def get_actual_path_points(start_location, end_location):
    """获取考虑避让的实际路径点"""
    points = []
    bias = 750

    try:
        # 获取起点信息
        if start_location in Compartments_dict:
            st_x = Compartments_dict[start_location]['x']
            st_y = Compartments_dict[start_location]['y']
            st_rack = Compartments_dict[start_location]['rack']
            st_side = 'left' if extract_middle_two_digits(start_location) % 2 != 0 else 'right'
            st_x_shifted = st_x - bias if st_side == 'left' else st_x + bias
        else:
            st_x = Review_Stations_dict[start_location]['x']
            st_y = Review_Stations_dict[start_location]['y']
            st_x_shifted = st_x
            st_rack = None

        # 获取终点信息
        if end_location in Compartments_dict:
            en_x = Compartments_dict[end_location]['x']
            en_y = Compartments_dict[end_location]['y']
            en_rack = Compartments_dict[end_location]['rack']
            en_side = 'left' if extract_middle_two_digits(end_location) % 2 != 0 else 'right'
            en_x_shifted = en_x - bias if en_side == 'left' else en_x + bias
        else:
            en_x = Review_Stations_dict[end_location]['x']
            en_y = Review_Stations_dict[end_location]['y']
            en_x_shifted = en_x
            en_rack = None

        # 判断是否需要避让
        if st_rack and en_rack and st_rack != en_rack:
            # 不同货架间移动需要避让
            st_y_min, st_y_max = shelf_ordinate_range(st_y)
            en_y_min, en_y_max = shelf_ordinate_range(en_y)
            
            # 选择最优避让路径
            paths = []
            # 下方路径
            if st_y_min and en_y_min:
                bottom_path = [
                    (st_x_shifted, st_y),
                    (st_x_shifted, st_y_min - bias),
                    (en_x_shifted, st_y_min - bias),
                    (en_x_shifted, en_y)
                ]
                paths.append((sum(abs(p2[0]-p1[0]) + abs(p2[1]-p1[1]) 
                            for p1, p2 in zip(bottom_path[:-1], bottom_path[1:])), bottom_path))
            
            # 上方路径
            if st_y_max and en_y_max:
                top_path = [
                    (st_x_shifted, st_y),
                    (st_x_shifted, st_y_max + bias),
                    (en_x_shifted, en_y_max + bias),
                    (en_x_shifted, en_y)
                ]
                paths.append((sum(abs(p2[0]-p1[0]) + abs(p2[1]-p1[1]) 
                            for p1, p2 in zip(top_path[:-1], top_path[1:])), top_path))
            
            # 选择最短路径
            if paths:
                points.extend(min(paths, key=lambda x: x[0])[1])
            else:
                points.extend([(st_x_shifted, st_y), (en_x_shifted, en_y)])
        
        else:
            # 同一货架内或其他情况
            points.extend([(st_x_shifted, st_y), (en_x_shifted, en_y)])

        return points

    except Exception as e:
        print(f"路径点计算错误: {str(e)}")
        return [(st_x, st_y), (en_x, en_y)]

def get_compartment_quantity(task_id, compartment):
    """
    获取指定任务中指定货格的商品数量
    """
    quantities = []
    for idx, row in datas_tasks[datas_tasks['任务单号'] == task_id].iterrows():
        if row['商品货格'] == compartment:
            quantities.append(row['商品件数'])
    return sum(quantities)
def is_bottom_shelf(y):
    """判断是否为最底层货架"""
    return 3000 <= y <= 14200
def is_edge_shelf(y):
    """判断是否为边缘货架"""
    shelf_ranges = [
        (3000, 14200),   # 第一排货架
        (17000, 28200),  # 第二排货架
        (31000, 42200),  # 第三排货架
        (45000, 56200)   # 第四排货架
    ]
    
    for y_min, y_max in shelf_ranges:
        if abs(y - y_min) < 1000 or abs(y - y_max) < 1000:
            return True
    return False

def is_path_cross_shelf(x1, y1, x2, y2):
    """检查路径是否穿过货架"""
    # 检查所有货架
    for rack_info in Storage_Racks_dict.values():
        rack_x = rack_info['x']
        rack_y = rack_info['y']
        rack_width = rack_info['width']
        rack_length = rack_info['length']
        
        # 货架区域
        shelf_x_min = rack_x
        shelf_x_max = rack_x + rack_width
        shelf_y_min = rack_y
        shelf_y_max = rack_y + rack_length
        
        # 检查线段是否与货架相交
        if (min(x1, x2) <= shelf_x_max and max(x1, x2) >= shelf_x_min and
            min(y1, y2) <= shelf_y_max and max(y1, y2) >= shelf_y_min):
            return True
    return False

def get_actual_path_points(start_location, end_location):
    """获取考虑避让的实际路径点"""
    points = []
    bias = 750
    edge_bias = 1500
    review_station_offset = 2000

    try:
        # 获取起点信息
        if start_location in Compartments_dict:
            st_x = Compartments_dict[start_location]['x']
            st_y = Compartments_dict[start_location]['y']
            st_side = 'left' if extract_middle_two_digits(start_location) % 2 != 0 else 'right'
            st_x_shifted = st_x - bias if st_side == 'left' else st_x + bias
            st_is_edge = is_edge_shelf(st_y)
            st_is_bottom = is_bottom_shelf(st_y)
            st_type = 'compartment'
        else:
            st_x = Review_Stations_dict[start_location]['x']
            st_y = Review_Stations_dict[start_location]['y']
            st_x_shifted = st_x
            st_is_edge = False
            st_is_bottom = False
            st_type = 'review'

        # 获取终点信息
        if end_location in Compartments_dict:
            en_x = Compartments_dict[end_location]['x']
            en_y = Compartments_dict[end_location]['y']
            en_side = 'left' if extract_middle_two_digits(end_location) % 2 != 0 else 'right'
            en_x_shifted = en_x - bias if en_side == 'left' else en_x + bias
            en_is_edge = is_edge_shelf(en_y)
            en_is_bottom = is_bottom_shelf(en_y)
            en_type = 'compartment'
        else:
            en_x = Review_Stations_dict[end_location]['x']
            en_y = Review_Stations_dict[end_location]['y']
            en_x_shifted = en_x
            en_is_edge = False
            en_is_bottom = False
            en_type = 'review'

        # 处理复核台到货格的路径
        if st_type == 'review' and en_type == 'compartment':
            y_min, y_max = shelf_ordinate_range(en_y)
            if y_min is not None:
                if en_is_bottom:
                    # 最底层货架特殊处理
                    points.extend([
                        (st_x_shifted, st_y),
                        (st_x_shifted, y_min - edge_bias),
                        (en_x_shifted, y_min - edge_bias),
                        (en_x_shifted, en_y)
                    ])
                else:
                    # 其他情况
                    if st_x < en_x:  # 复核台在左侧
                        mid_x = st_x + review_station_offset
                        points.extend([
                            (st_x_shifted, st_y),
                            (mid_x, st_y),
                            (mid_x, y_min - edge_bias),
                            (en_x_shifted, y_min - edge_bias),
                            (en_x_shifted, en_y)
                        ])
                    else:  # 复核台在右侧
                        mid_x = st_x - review_station_offset
                        points.extend([
                            (st_x_shifted, st_y),
                            (mid_x, st_y),
                            (mid_x, y_max + edge_bias),
                            (en_x_shifted, y_max + edge_bias),
                            (en_x_shifted, en_y)
                        ])

        # 处理货格到复核台的路径
        elif st_type == 'compartment' and en_type == 'review':
            y_min, y_max = shelf_ordinate_range(st_y)
            if y_min is not None:
                if st_is_bottom:
                    # 从底层货格到复核台
                    if en_y < y_min:  # 复核台在货架下方
                        points.extend([
                            (st_x_shifted, st_y),
                            (st_x_shifted, y_min - edge_bias),
                            (en_x_shifted, y_min - edge_bias),
                            (en_x_shifted, en_y)
                        ])
                    else:  # 复核台在货架上方
                        points.extend([
                            (st_x_shifted, st_y),
                            (st_x_shifted, y_max + edge_bias),
                            (en_x_shifted, y_max + edge_bias),
                            (en_x_shifted, en_y)
                        ])
                else:
                    # 从其他层货格到复核台
                    if st_x < en_x:  # 货格在复核台左侧
                        points.extend([
                            (st_x_shifted, st_y),
                            (st_x_shifted, y_min - edge_bias),
                            (en_x_shifted, y_min - edge_bias),
                            (en_x_shifted, en_y)
                        ])
                    else:  # 货格在复核台右侧
                        points.extend([
                            (st_x_shifted, st_y),
                            (st_x_shifted, y_max + edge_bias),
                            (en_x_shifted, y_max + edge_bias),
                            (en_x_shifted, en_y)
                        ])
            else:
                points.extend([(st_x_shifted, st_y), (en_x_shifted, en_y)])
        
        # 处理货格之间的路径
        elif st_type == 'compartment' and en_type == 'compartment':
            y_min, y_max = shelf_ordinate_range(st_y)
            if not y_min:
                y_min, y_max = shelf_ordinate_range(en_y)

            if y_min:
                if st_is_bottom or en_is_bottom:
                    # 最底层货架特殊处理
                    points.extend([
                        (st_x_shifted, st_y),
                        (st_x_shifted, y_min - edge_bias),
                        (en_x_shifted, y_min - edge_bias),
                        (en_x_shifted, en_y)
                    ])
                else:
                    # 计算上下两种路径
                    path_bottom = [
                        (st_x_shifted, st_y),
                        (st_x_shifted, y_min - edge_bias),
                        (en_x_shifted, y_min - edge_bias),
                        (en_x_shifted, en_y)
                    ]
                    path_top = [
                        (st_x_shifted, st_y),
                        (st_x_shifted, y_max + edge_bias),
                        (en_x_shifted, y_max + edge_bias),
                        (en_x_shifted, en_y)
                    ]
                    
                    # 选择最短路径
                    len_bottom = sum(abs(p2[0]-p1[0]) + abs(p2[1]-p1[1]) 
                                   for p1, p2 in zip(path_bottom[:-1], path_bottom[1:]))
                    len_top = sum(abs(p2[0]-p1[0]) + abs(p2[1]-p1[1]) 
                                for p1, p2 in zip(path_top[:-1], path_top[1:]))
                    points.extend(path_bottom if len_bottom <= len_top else path_top)
            else:
                points.extend([(st_x_shifted, st_y), (en_x_shifted, en_y)])
        
        # 处理复核台之间的路径
        else:
            points.extend([(st_x_shifted, st_y), (en_x_shifted, en_y)])

        return points

    except Exception as e:
        print(f"路径点计算错误: {str(e)}")
        return [(st_x, st_y), (en_x, en_y)]
def visualize_warehouse_and_route(all_routes, task_id):
    """可视化仓库布局和拣货路径"""
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(15, 10))

    # 绘制货架
    for rack_name, rack_info in Storage_Racks_dict.items():
        x = rack_info['x']
        y = rack_info['y']
        length = rack_info['length']
        width = rack_info['width']
        rect = Rectangle((x, y), width, length, linewidth=1, 
                        edgecolor='black', facecolor='gray', alpha=0.5)
        ax.add_patch(rect)
        ax.text(x + width/2, y + length/2, rack_name, 
                ha='center', va='center', fontsize=6)

    # 绘制货格
    for compartment_name, compartment_info in Compartments_dict.items():
        x = compartment_info['x']
        y = compartment_info['y']
        ax.plot(x, y, 'bo', markersize=2)

    # 绘制复核台
    for station_name, station_info in Review_Stations_dict.items():
        x = station_info['x']
        y = station_info['y']
        length = station_info['length']
        width = station_info['width']
        rect = Rectangle((x, y), width, length, linewidth=1, 
                        edgecolor='red', facecolor='yellow', alpha=0.7)
        ax.add_patch(rect)
        ax.text(x + width/2, y + length/2, station_name, 
                ha='center', va='center', fontsize=6)

    # 绘制拣货路径
    if task_id in all_routes:
        route = all_routes[task_id]['route']
        for i, (start, end, distance) in enumerate(route):
            path_points = get_actual_path_points(start, end)
            if path_points:
                x_coords = [p[0] for p in path_points]
                y_coords = [p[1] for p in path_points]
                
                # 绘制路径线段
                ax.plot(x_coords, y_coords, 'r-', linewidth=1.5, alpha=0.7)
                
                # 标记起点和路径点
                ax.plot(x_coords[0], y_coords[0], 'bo', markersize=4)
                ax.plot(x_coords[-1], y_coords[-1], 'ro', markersize=4)
                
                # 添加路径序号
                ax.text(x_coords[0], y_coords[0], f'{i+1}', fontsize=8)

    ax.set_xlabel('X 坐标 (毫米)')
    ax.set_ylabel('Y 坐标 (毫米)')
    ax.set_title(f'仓库布局与拣货路径 - 任务单 {task_id}')
    ax.grid(True)
    ax.set_aspect('equal')
    
    # 设置坐标轴范围
    margin = 2000
    ax.set_xlim(min(x['x'] for x in Review_Stations_dict.values()) - margin,
                max(x['x'] + x['width'] for x in Storage_Racks_dict.values()) + margin)
    ax.set_ylim(min(y['y'] for y in Review_Stations_dict.values()) - margin,
                max(y['y'] + y['length'] for y in Storage_Racks_dict.values()) + margin)

    plt.show()

if __name__ == "__main__":
    print("开始求解问题...")  # 调试信息
    all_routes = solving_problem()
    task_id_to_visualize = 'T0003'
    task_id = 'T0040'
    print(f"路径数据: {all_routes.keys()}")  # 打印所有任务ID
    print(all_routes[task_id_to_visualize]['route'])
    visualize_warehouse_and_route(all_routes, task_id)
