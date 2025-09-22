import streamlit as st
import graphviz
from itertools import cycle
import copy
import json
from collections import defaultdict
import pandas as pd
import altair as alt

# ===============================================================
#  頁面設定 (必須是第一個執行的 Streamlit 指令)
# ===============================================================
st.set_page_config(layout="wide")
st.title("Mukai Power Model and Battery Life Calculation V1.3")

# JavaScript 元件的 import
import streamlit.components.v1 as components

# ===============================================================
#  CSS 樣式 (保持您自訂的主題)
# ===============================================================

if 'theme' not in st.session_state:
    st.session_state.theme = "Dark" # 預設為 Dark

st.markdown("""
<style>
/* Custom styling for ratio inputs in Use Case Management */
div[data-testid="stVerticalBlock"] .stNumberInput {
    max-width: 120px;
}
</style>
""", unsafe_allow_html=True)

if st.session_state.theme == "Dark":
    st.markdown("""
        <style>
        /* ... (Dark Theme CSS 保持不變) ... */
        .stApp, [data-testid="stSidebar"] { background-color: #0e1117; }
        h1, h2, h3, h4, h5, h6, .st-emotion-cache-16txtl3, p, .st-emotion-cache-1y4p8pa { color: #fafafa !important; }
        [data-testid="stExpander"] summary { color: #fafafa !important; }
        div[data-testid="stExpander"] div[role="region"] { background-color: #1c1f2b; }
        [data-testid="stBlockContainer"], [data-testid="stDataFrame"], .stChart { background-color: #0e1117 !important; }
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div { background-color: #1c1f2b !important; border-color: #AAAAAA !important; }
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div { color: #fafafa !important; }
        div[data-baseweb="popover"] ul[role="listbox"] { background-color: #1c1f2b !important; }
        li[role="option"] { color: #fafafa !important; }
        </style>
    """, unsafe_allow_html=True)
else: # Light Theme
    st.markdown("""
        <style>
        /* ... (Light Theme CSS 保持不變) ... */
        .stApp { background-color: #FFFFFF; }
        [data-testid="stSidebar"] { background-color: #F0F2F6; }
        [data-testid="stBlockContainer"], [data-testid="stDataFrame"], .stChart { background-color: #FFFFFF !important; border-color: #F0F2F6 !important; }
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div { background-color: #FFFFFF !important; border-color: #AAAAAA !important; }
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div { color: #0e1117 !important; }
        div[data-baseweb="popover"] ul[role="listbox"] { background-color: #FFFFFF !important; }
        li[role="option"] { color: #0e1117 !important; }
        h1, h2, h3, h4, h5, h6, .st-emotion-cache-16txtl3, p, .st-emotion-cache-1y4p8pa { color: #0e1117 !important; }
        [data-testid="stExpander"] summary { color: #0e1117 !important; }
        div[data-testid="stExpander"] div[role="region"] { background-color: #F0F2F6; }
        </style>
    """, unsafe_allow_html=True)

# ---
# 核心數據結構 (Core Data Structure)
# ---
DEFAULT_COLORS = cycle(["#4CAF50", "#FF5722", "#607D8B", "#E91E63", "#9C27B0", "#03A9F4"])

def initialize_data():
    """初始化所有 session_state 數據"""
    if 'initialized' in st.session_state:
        # (防呆檢查... 保持不變)
        if 'component_group_notes' not in st.session_state:
            all_comp_groups = set(n['group'] for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component')
            st.session_state.component_group_notes = {group: "" for group in all_comp_groups}
        for ps_id, modes in st.session_state.power_source_modes.items():
            for mode_name, params in modes.items():
                if 'note' not in params:
                    st.session_state.power_source_modes[ps_id][mode_name]['note'] = ""
        return

    # --- 1. 節點定義 (【已修改】quiescent_current_mA -> quiescent_current_uA) ---
    st.session_state.power_tree_data = {
        "nodes": [
            # Power Sources
            {"id": "battery", "label": "Vsys", "type": "power_source", "output_voltage": 3.85, "efficiency": 1.0, "quiescent_current_uA": 0.0, "input_source_id": None},
            {"id": "vbb", "label": "VBB", "type": "power_source", "output_voltage": 3.9, "efficiency": 0.9, "quiescent_current_uA": 10.0, "input_source_id": "battery"}, # 0.01mA -> 10uA
            {"id": "pmic_buck", "label": "PMIC (BUCK_1V8)", "type": "power_source", "output_voltage": 1.8, "efficiency": 0.95, "quiescent_current_uA": 50.0, "input_source_id": "battery"}, # 0.05mA -> 50uA
            {"id": "pmic_ldo1", "label": "PMIC (LDO1)", "type": "power_source", "output_voltage": 3.3, "efficiency": 0.85, "quiescent_current_uA": 20.0, "input_source_id": "battery"}, # 0.02mA -> 20uA
            {"id": "pmic_ldo2", "label": "PMIC (LDO2)", "type": "power_source", "output_voltage": 3.6, "efficiency": 0.85, "quiescent_current_uA": 20.0, "input_source_id": "vbb"}, # 0.02mA -> 20uA
            {"id": "display_1v8", "label": "Display 1V8", "type": "power_source", "output_voltage": 1.8, "efficiency": 0.9, "quiescent_current_uA": 10.0, "input_source_id": "pmic_buck"}, # 0.01mA -> 10uA
            {"id": "ext_ldo_avdd", "label": "ext. LDO AVDD", "type": "power_source", "output_voltage": 3.0, "efficiency": 0.85, "quiescent_current_uA": 10.0, "input_source_id": "battery"},
            {"id": "ldo_mcu", "label": "LDO_MCU", "type": "power_source", "output_voltage": 0.9, "efficiency": 0.5, "quiescent_current_uA": 10.0, "input_source_id": "battery"},
            {"id": "dd_ovdd", "label": "Display Driver OVDD", "type": "power_source", "output_voltage": 4.5, "efficiency": 0.85, "quiescent_current_uA": 30.0, "input_source_id": "battery"},
            {"id": "dd_ovss", "label": "Display Driver OVSS", "type": "power_source", "output_voltage": 4.5, "efficiency": 0.85, "quiescent_current_uA": 30.0, "input_source_id": "battery"},
            {"id": "ls_mcu", "label": "LS MCU", "type": "power_source", "output_voltage": 1.2, "efficiency": 0.85, "quiescent_current_uA": 10.0, "input_source_id": "pmic_buck"},
            {"id": "lsw3_mcu", "label": "LSW3 MCU", "type": "power_source", "output_voltage": 1.8, "efficiency": 0.85, "quiescent_current_uA": 10.0, "input_source_id": "pmic_buck"},
            {"id": "drv2624", "label": "DRV2624", "type": "power_source", "output_voltage": 1.8, "efficiency": 0.85, "quiescent_current_uA": 10.0, "input_source_id": "pmic_buck", "note": "I2C Address: 0x5A and 0x58"},
            
            # Components (power_consumption 欄位只在初始化時使用一次)
            {"id": "mcu", "type": "component", "group": "SoC", "endpoint": "MCU Core", "power_consumption": 2.5, "input_source_id": "pmic_buck"},
            {"id": "ble", "type": "component", "group": "SoC", "endpoint": "BLE Radio", "power_consumption": 5.0, "input_source_id": "pmic_buck"},
            {"id": "soc_core", "type": "component", "group": "SoC", "endpoint": "core", "power_consumption": 1.0, "input_source_id": "ldo_mcu"},
            {"id": "display", "type": "component", "group": "Display Module", "endpoint": "AVDD", "power_consumption": 15.0, "input_source_id": "ext_ldo_avdd"},
            {"id": "node_8", "type": "component", "group": "Display Module", "endpoint": "IO_1V8", "power_consumption": 8.0, "input_source_id": "display_1v8"},
            {"id": "node_15", "type": "component", "group": "Display Module", "endpoint": "OVDD", "power_consumption": 5.0, "input_source_id": "dd_ovdd"},
            {"id": "node_16", "type": "component", "group": "Display Module", "endpoint": "OVSS", "power_consumption": 5.0, "input_source_id": "dd_ovss"},
            {"id": "hrm", "type": "component", "group": "AFE4510", "endpoint": "TX", "power_consumption": 10.0, "input_source_id": "pmic_ldo2"},
            {"id": "node_9", "type": "component", "group": "AFE4510", "endpoint": "RX/IO", "power_consumption": 7.0, "input_source_id": "pmic_ldo1"},
            {"id": "node_17", "type": "component", "group": "ALS", "endpoint": "ALS VDD", "power_consumption": 1.0, "input_source_id": "display_1v8"},
            {"id": "node_18", "type": "component", "group": "Temp Sensor TMP118A", "endpoint": "TEMP sensor 1V8", "power_consumption": 1.0, "input_source_id": "display_1v8"},
            {"id": "node_19", "type": "component", "group": "Barometer", "endpoint": "Baro 1V8", "power_consumption": 1.0, "input_source_id": "display_1v8"},
            {"id": "node_21", "type": "component", "group": "GNSS", "endpoint": "VDD", "power_consumption": 1.0, "input_source_id": "battery"},
            {"id": "node_22", "type": "component", "group": "GNSS", "endpoint": "IO", "power_consumption": 1.0, "input_source_id": "pmic_buck"},
            {"id": "node_23", "type": "component", "group": "Flash", "endpoint": "VDD", "power_consumption": 1.0, "input_source_id": "pmic_buck"},
            {"id": "node_24", "type": "component", "group": "IMU", "endpoint": "VDD", "power_consumption": 1.0, "input_source_id": "pmic_buck"},
            {"id": "node_25", "type": "component", "group": "Barometer", "endpoint": "VDD", "power_consumption": 1.0, "input_source_id": "pmic_buck"},
            {"id": "node_26", "type": "component", "group": "Temp Sensor TMP118B", "endpoint": "VDD", "power_consumption": 1.0, "input_source_id": "pmic_buck"},
        ]
    }
    st.session_state.max_id = 26 # 保持 26

    st.session_state.group_colors = {
        "SoC": "#FFC107", "Display Module": "#4CAF50", "AFE4510": "#F44336",
        "ALS": "#607D8B", "Temp Sensor TMP118A": "#E91E63", "Barometer": "#03A9F4",
        "GNSS": "#FF9800", "Flash": "#795548", "IMU": "#9E9E9E", "Temp Sensor TMP118B": "#00BCD4"
    }
    
    component_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component']
    power_source_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source']
    all_comp_groups = set(n['group'] for n in component_nodes)
    node_lookup = {(n['group'], n['endpoint']): n['id'] for n in component_nodes}
    
    # --- 2. 【已修改】quiescent_current_mA -> quiescent_current_uA ---
    st.session_state.power_source_modes = {}
    for ps in power_source_nodes:
        base_note = ps.get("note", "") 
        st.session_state.power_source_modes[ps['id']] = {
            "On": {
                "output_voltage": ps['output_voltage'], 
                "efficiency": ps['efficiency'], 
                "quiescent_current_uA": ps['quiescent_current_uA'], # <-- 已重命名
                "note": base_note
            },
            "Off": {
                "output_voltage": 0.0, 
                "efficiency": 0.0, 
                "quiescent_current_uA": ps['quiescent_current_uA'], # <-- 已重命名
                "note": "Device is off"
            }
        }

    # --- 3. 【已修改】建立 Operating Modes (儲存 "currents_uA") ---
    st.session_state.operating_modes = {}
    
    def get_default_current_uA(node): # <-- 已重命名
        source_id = node.get('input_source_id')
        if not source_id: return 0.0
        source_voltage = st.session_state.power_source_modes.get(source_id, {}).get("On", {}).get("output_voltage", 1.0)
        if source_voltage == 0: return 0.0
        # (mW / V) * 1000 = uA
        return (node.get('power_consumption', 0.0) / source_voltage) * 1000.0 # <-- 乘以 1000
    
    # --- 3A. 處理您貼上的表格資料 ---
    user_table_data = [
        # 您的表格數值 (1507, 1159 等) 現在被正確地當作 uA
        {"Group": "Display Module", "Mode Name": "Active - 60Hz", "Endpoint": "AVDD", "Current (uA)": 1507, "Mode Note": "100% OPR, White, 800nits, NBM"},
        {"Group": "Display Module", "Mode Name": "AOD - 15 Hz", "Endpoint": "AVDD", "Current (uA)": 1159, "Mode Note": "20% OPR, White, 50nits"},
        {"Group": "Display Module", "Mode Name": "Active - 60Hz", "Endpoint": "IO_1V8", "Current (uA)": 1281, "Mode Note": "100% OPR, White, 800nits, NBM"},
        {"Group": "Display Module", "Mode Name": "AOD - 15 Hz", "Endpoint": "IO_1V8", "Current (uA)": 861, "Mode Note": "20% OPR, White, 50nits"},
        {"Group": "Display Module", "Mode Name": "AOD - 15 Hz", "Endpoint": "OVSS", "Current (uA)": 1, "Mode Note": "50 nits, 15Hz"},
        {"Group": "Display Module", "Mode Name": "Idle mode", "Endpoint": "AVDD", "Current (uA)": 0, "Mode Note": "Display off"},
        {"Group": "Display Module", "Mode Name": "Idle mode", "Endpoint": "IO_1V8", "Current (uA)": 0.1, "Mode Note": "Display off"},
        {"Group": "Display Module", "Mode Name": "Idle mode", "Endpoint": "OVDD", "Current (uA)": 0, "Mode Note": "Display off"},
        {"Group": "Display Module", "Mode Name": "Idle mode", "Endpoint": "OVSS", "Current (uA)": 0, "Mode Note": "Display off"},
    ]

    new_op_modes = defaultdict(dict)
    for row in user_table_data:
        group = row["Group"]
        mode = row["Mode Name"]
        endpoint = row["Endpoint"]
        current = row["Current (uA)"] # <-- 讀取 uA
        note = row.get("Mode Note", "")
        
        node_id = node_lookup.get((group, endpoint))
        if not node_id: continue
        
        if mode not in new_op_modes[group]:
            all_node_ids_in_group = {n['id'] for n in component_nodes if n['group'] == group}
            new_op_modes[group][mode] = {"currents_uA": {nid: 0.0 for nid in all_node_ids_in_group}, "note": note} # <-- 已重命名
        
        new_op_modes[group][mode]["currents_uA"][node_id] = current # <-- 存入 uA
        if note:
            new_op_modes[group][mode]["note"] = note
    
    st.session_state.operating_modes = dict(new_op_modes)
    
    # --- 3B. 為所有「其他」群組建立 "Default" 模式 ---
    for group in all_comp_groups:
        if group in st.session_state.operating_modes:
            continue 
        
        group_nodes = [n for n in component_nodes if n['group'] == group]
        default_currents = {n['id']: get_default_current_uA(n) for n in group_nodes} # <-- 已重命名
        st.session_state.operating_modes[group] = {
            "Default": {
                "currents_uA": default_currents, # <-- 已重命名
                "note": "Default operating mode."
            }
        }

    st.session_state.component_group_notes = {group: "" for group in all_comp_groups}

    # --- 4. 建立 Use Cases (保持不變) ---
    default_comp_settings = {}
    for group in all_comp_groups:
        group_modes = st.session_state.operating_modes.get(group, {})
        if "Default" in group_modes:
            default_comp_settings[group] = {"Default": 100}
        elif group_modes:
            first_mode = list(group_modes.keys())[0]
            default_ratio_dict = {mode: 0 for mode in group_modes}
            default_ratio_dict[first_mode] = 100
            default_comp_settings[group] = default_ratio_dict
            
    default_ps_settings = {ps['id']: "On" for ps in power_source_nodes}
    default_use_case_settings = {"components": default_comp_settings, "power_sources": default_ps_settings}
    
    new_use_case_names = [
        "On-wrist stationary, BLE connected", "On-wrist stationary, BLE connected, Inductive button active",
        "On-wrist, BLE very fast advertising", "Off-wrist, BLE advertising", "On-wrist active, BLE connected",
        "Sync, BLE connected fast with payload", "Sync, BLE connected fast no payload", "Live data (steps + HR)",
        "Incoming text notifications", "Incoming call notifications", "Alarm", "Goal celebration",
        "Quick View - Turn on display", "Quick View - Turn on display - ECG", "Double Tap - Turn on display",
        "Button Press - Turn on display", "Single Tap - View stats", "Reminder to move - alert",
        "Reminder to move - celebration", "NFC Transit Pass Only", "NFC Payment Transaction (NFC incremental without Display)",
        "NFC Payment Transaction (Display + vibe without NFC)", "6-Axis Accel Exercise", "Inkling Incremental - logging data",
        "Inkling Incremental - BLE sync", "Vibe feedback incremental power on inductive button press",
        "Touch Timeout UI active", "On-wrist active, GPS", "Lead Imp sEDA", "Always On Display",
        "NLP cloud processing", "Display On", "SNORE DETECT", "VOICE/SOUND DETECT", "KEYWORD DETECT",
        "Touch LP Active Mode"
    ]

    st.session_state.use_cases = {}
    for name in new_use_case_names:
        st.session_state.use_cases[name] = copy.deepcopy(default_use_case_settings)
    
    st.session_state.active_use_case = new_use_case_names[0]
    
    # --- 5. User Profiles (保持不變) ---
    st.session_state.battery_capacity_mAh = 64.5
    empty_profile = {name: 0 for name in new_use_case_names}
    typical_profile = copy.deepcopy(empty_profile)
    typical_profile["On-wrist stationary, BLE connected"] = 10 
    typical_profile["On-wrist active, BLE connected"] = 6
    typical_profile["Always On Display"] = 8 
    st.session_state.user_profiles = {
        "Typical User": typical_profile,
        "Heavy User": copy.deepcopy(empty_profile),
        "Light User": copy.deepcopy(empty_profile)
    }
    st.session_state.active_user_profile = "Typical User"
    
    st.session_state.initialized = True

initialize_data()

# ---
# 核心功能函數 (Core Functions)
# ---

def get_node_by_id(node_id):
    return next((n for n in st.session_state.power_tree_data['nodes'] if n['id'] == node_id), None)

def apply_use_case(use_case_name_override=None):
    if use_case_name_override:
        active_uc_name = use_case_name_override
    else:
        active_uc_name = st.session_state.get('active_use_case', list(st.session_state.use_cases.keys())[0])
        if active_uc_name not in st.session_state.use_cases:
            active_uc_name = list(st.session_state.use_cases.keys())[0]
            st.session_state.active_use_case = active_uc_name

    active_uc = st.session_state.use_cases[active_uc_name]
    
    # --- 【已修改】 quiescent_current_uA ---
    ps_settings = active_uc.get("power_sources", {})
    for node in st.session_state.power_tree_data['nodes']:
        if node['type'] == 'power_source':
            ps_mode_name = ps_settings.get(node['id'], "On")
            if ps_mode_name not in st.session_state.power_source_modes.get(node['id'], {}):
                ps_mode_name = "On" 
            
            mode_params = st.session_state.power_source_modes[node['id']][ps_mode_name]
            node['output_voltage'] = mode_params['output_voltage']
            node['efficiency'] = mode_params['efficiency']
            node['quiescent_current_uA'] = mode_params['quiescent_current_uA'] # <-- 已重命名

    # --- 【已修改】 讀取 uA 並除以 1000 ---
    comp_settings = active_uc.get("components", {}) 
    for node in st.session_state.power_tree_data['nodes']:
        if node['type'] == 'component':
            group = node['group']
            group_ratios = comp_settings.get(group)
            
            if group_ratios:
                source_node = get_node_by_id(node.get('input_source_id'))
                current_voltage = 0.0
                if source_node:
                    current_voltage = source_node.get('output_voltage', 0.0)

                weighted_power = 0.0
                
                for mode_name, ratio in group_ratios.items():
                    if ratio > 0:
                        # 1. 讀取 uA
                        current_uA = st.session_state.operating_modes.get(group, {}).get(
                            mode_name, {}
                        ).get('currents_uA', {}).get(node['id'], 0.0) # <-- 讀取 currents_uA
                        
                        # 2. 轉換為 mA (uA / 1000) 來計算 mW
                        power_for_mode = current_voltage * (current_uA / 1000.0)
                        
                        weighted_power += power_for_mode * (ratio / 100.0)
                
                node['power_consumption'] = weighted_power
            else:
                node['power_consumption'] = 0.0

def calculate_power(use_case_name_override=None):
    apply_use_case(use_case_name_override)
    nodes = st.session_state.power_tree_data['nodes']
    
    memo = {}

    def recursive_power_calc(node_id, visited_nodes):
        if node_id in memo:
            return memo[node_id]
        if node_id in visited_nodes:
            st.error(f"檢測到循環依賴: {node_id}")
            return 0
        
        visited_nodes.add(node_id)
        node = get_node_by_id(node_id)
        if not node: return 0
        if node['type'] == 'component':
            source = get_node_by_id(node.get('input_source_id'))
            if source and source['output_voltage'] == 0:
                return 0.0
            return node.get('power_consumption', 0)
        
        total_downstream_power = sum(
            recursive_power_calc(downstream_node['id'], visited_nodes.copy())
            for downstream_node in nodes if downstream_node.get('input_source_id') == node_id
        )
        node['output_power_total'] = total_downstream_power
        
        efficiency = node.get('efficiency', 1.0)
        input_power_from_load = total_downstream_power / efficiency if efficiency > 0 else 0
        
        input_source = get_node_by_id(node.get('input_source_id'))
        input_voltage = input_source['output_voltage'] if input_source else node['output_voltage']
        
        # --- 【已修改】 讀取 uA 並除以 1000 ---
        quiescent_current_uA = node.get('quiescent_current_uA', 0.0)
        quiescent_power = input_voltage * (quiescent_current_uA / 1000.0) # <-- 除以 1000
        
        total_input_power = input_power_from_load + quiescent_power
        node['input_power'] = total_input_power
        
        memo[node_id] = total_input_power
        return total_input_power

    root_nodes = [n for n in nodes if n.get('input_source_id') is None]
    total_system_power_mW = sum(recursive_power_calc(root['id'], set()) for root in root_nodes)
    return total_system_power_mW


def get_vsys_referred_power_contributions(node_list):

    # 內部輔助函數 (保持不變)
    def trace_power_to_root(load_mW, start_node_id):
        current_node = get_node_by_id(start_node_id)
        power = load_mW
        while current_node and current_node.get('input_source_id') is not None:
            parent_node = get_node_by_id(current_node.get('input_source_id'))
            efficiency = current_node.get('efficiency', 1.0)
            power = power / efficiency if efficiency > 0 else 0
            current_node = parent_node
        return power

    contributions = []
    
    # --- 1. 計算所有「元件負載」的 Vsys 參考功耗 ---
    # (這部分已包含「工作功耗」+「效率損耗」)
    component_nodes = [n for n in node_list if n['type'] == 'component']
    for node in component_nodes:
        if node.get('power_consumption', 0) > 0:
            component_load_mW = node['power_consumption']
            vsys_referred_power = trace_power_to_root(component_load_mW, node.get('input_source_id'))
            
            label = node['group'] # 以 Group 為單位
            contributions.append({
                "source": label, 
                "power_mW": vsys_referred_power, 
                "type": "Component Load"
            })

    # --- 2. 計算所有「靜態電流 (Iq) 損耗」的 Vsys 參考功耗 ---
    power_source_nodes = [n for n in node_list if n['type'] == 'power_source']
    for node in power_source_nodes:
        
        quiescent_current_uA = node.get('quiescent_current_uA', 0.0)
        if quiescent_current_uA > 0:
            parent_node = get_node_by_id(node.get('input_source_id'))
            if parent_node:
                input_voltage = parent_node.get('output_voltage', 0.0)
                parent_id_to_trace_from = parent_node.get('id')
            else:
                input_voltage = node.get('output_voltage', 0.0) 
                parent_id_to_trace_from = None 

            iq_load_mW = input_voltage * (quiescent_current_uA / 1000.0) # 轉回 mW
            vsys_referred_iq_power = trace_power_to_root(iq_load_mW, parent_id_to_trace_from)

            if vsys_referred_iq_power > 0.0001:
                label = f"{node['label']} (Iq Loss)"
                contributions.append({
                    "source": label,
                    "power_mW": vsys_referred_iq_power,
                    "type": "Quiescent Loss"
                })



    if not contributions:
        return pd.DataFrame(columns=["source", "power_mW", "type"])
        
    df = pd.DataFrame(contributions)

    # --- 3. GroupBy (現在加總所有類型) ---
    # 我們需要加總 Component Load (依群組) 和 Quiescent Loss (依節點)
    df_components = df[df['type'] == 'Component Load']
    df_losses = df[df['type'] == 'Quiescent Loss'] # 只選 Iq Loss
    
    if not df_components.empty:
        df_components_grouped = df_components.groupby('source').agg(
            power_mW=('power_mW', 'sum'),
            type=('type', 'first')
        ).reset_index()
    else:
        df_components_grouped = pd.DataFrame(columns=['source', 'power_mW', 'type'])
    
    # 將加總後的 Component 和「所有獨立的 Iq 損耗項」重新組合
    final_df = pd.concat([df_components_grouped, df_losses], ignore_index=True)
    
    return final_df


# ===============================================================
#  側邊欄 UI (Sidebar UI)
# ===============================================================
with st.sidebar:
    components.html(
    """
    <script>
    window.addEventListener("beforeunload", function (e) {
        var confirmationMessage = "您有未儲存的修改，確定要離開嗎？";
        e.returnValue = confirmationMessage;
        return confirmationMessage;
    });
    </script>
    """,
    height=0,
    )
    
    st.header("Display Settings")
    theme_options = ["Light", "Dark"]
    current_theme_index = theme_options.index(st.session_state.theme)
    selected_theme = st.radio(
        "Select Page Theme",
        options=theme_options,
        index=current_theme_index,
        key="theme_selector",
        horizontal=True
    )
    if st.session_state.theme != selected_theme:
        st.session_state.theme = selected_theme
        st.rerun()

    st.markdown("---")
    st.header("設定檔管理")

    with st.expander("儲存目前設定", expanded=False):
        state_to_save = {
            'power_tree_data': st.session_state.power_tree_data,
            'max_id': st.session_state.max_id,
            'group_colors': st.session_state.group_colors,
            'operating_modes': st.session_state.operating_modes,
            'power_source_modes': st.session_state.power_source_modes,
            'use_cases': st.session_state.use_cases,
            'battery_capacity_mAh': st.session_state.battery_capacity_mAh,
            'user_profiles': st.session_state.user_profiles,
            'component_group_notes': st.session_state.component_group_notes
        }
        
        try:
            json_data = json.dumps(state_to_save, indent=4)
        except Exception as e:
            st.error(f"轉換 JSON 失敗: {e}")
            json_data = "{}"

        st.download_button(
           label="下載設定檔 (.json)",
           data=json_data,
           file_name='power_model_config.json',
           mime='application/json',
        )

    with st.expander("讀取設定檔", expanded=False):
        uploaded_file = st.file_uploader(
            "上傳您的 .json 設定檔",
            type=['json'],
            key="config_uploader"
        )
        
        if uploaded_file is not None:
            if st.button("確認載入此設定檔"):
                try:
                    file_content = uploaded_file.getvalue().decode("utf-8")
                    loaded_data = json.loads(file_content)
                    
                    required_keys = ['power_tree_data', 'user_profiles']
                    if not (all(key in loaded_data for key in required_keys) and ('device_modes' in loaded_data or 'use_cases' in loaded_data)):
                        st.error("錯誤：上傳的檔案格式不正確或缺少必要的鍵。")
                    else:
                        if 'device_modes' in loaded_data and 'use_cases' not in loaded_data:
                            loaded_data['use_cases'] = loaded_data.pop('device_modes')
                            
                        for key, value in loaded_data.items():
                            st.session_state[key] = value
                        
                        st.session_state.initialized = True 
                        st.success("設定已成功載入！頁面將自動刷新。")
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("錯誤：無法解析 JSON 檔案。請確認檔案內容是否為有效的 JSON 格式。")
                except Exception as e:
                    st.error(f"讀取檔案時發生錯誤: {e}")

# ===============================================================
#  主內容頁面 (Main Content)
# ===============================================================

tabs = st.tabs(["Power Tree", "Component Management", "Power Source Management", "Use Case Management", "Battery Life Estimation"])

calculate_power(st.session_state.active_use_case)

with tabs[0]:
    st.header("Power Consumption Analysis")
    
    st.subheader("Use Case Selection")
    
    use_case_list = list(st.session_state.use_cases.keys())
    active_use_case = st.session_state.get('active_use_case', use_case_list[0])
    try:
        current_index = use_case_list.index(active_use_case)
    except ValueError:
        current_index = 0

    selected_use_case = st.selectbox(
        "Select Use Case to Display", 
        options=use_case_list, 
        index=current_index, 
        key="use_case_selector", 
        label_visibility="collapsed"
    )
    
    if st.session_state.active_use_case != selected_use_case:
        st.session_state.active_use_case = selected_use_case
        st.rerun()
    
    power_placeholder = st.empty()
    current_placeholder = st.empty()
    
    # --- 【已修改】 預設改為收折 ---
    with st.expander("Show / Hide Power Tree Visualizer", expanded=False):
    # --- 【修改結束】 ---
        st.markdown("### Power Tree")
        graph_placeholder = st.empty()
    
    st.markdown("---")
    st.subheader("Vsys Power Consumption Distribution")

    df_contributions = get_vsys_referred_power_contributions(st.session_state.power_tree_data['nodes'])

    if not df_contributions.empty:
        total_calculated_power = df_contributions['power_mW'].sum()
        if total_calculated_power > 0:
            df_contributions['percentage'] = (df_contributions['power_mW'] / total_calculated_power)
        else:
            df_contributions['percentage'] = 0.0

        df_main = df_contributions[df_contributions['percentage'] >= 0.01].copy()
        other_power = df_contributions[df_contributions['percentage'] < 0.01]['power_mW'].sum()
        other_percentage = df_contributions[df_contributions['percentage'] < 0.01]['percentage'].sum()

        if other_power > 0:
            other_df = pd.DataFrame([{"source": "Others (<1%)", "power_mW": other_power, "type": "Others", "percentage": other_percentage}])
            df_chart = pd.concat([df_main, other_df], ignore_index=True)
        else:
            df_chart = df_main

        if st.session_state.theme == "Dark":
            pie_text_color = "white"
        else:
            pie_text_color = "black"

        base = alt.Chart(df_chart).encode(
           theta=alt.Theta("power_mW:Q", stack=True)
        ).properties(
           title="Breakdown of Total Vsys Power Draw",
           height=500
        )
        
        # --- 【已修改】 再次放大圓餅圖 ---
        pie = base.mark_arc(outerRadius=200, innerRadius=0).encode(
            color=alt.Color("source:N", title="Power Source"),
            order=alt.Order("percentage:Q", sort="descending"),
            tooltip=["source", alt.Tooltip("power_mW:Q", format=".2f"), alt.Tooltip("percentage:Q", format=".1%")]
        )
        text = base.mark_text(radius=220).encode(
            text=alt.Text("percentage:Q", format=".1%"),
            order=alt.Order("percentage:Q", sort="descending"),
            color=alt.value(pie_text_color)
        )
        # --- 【修改結束】 ---
        
        chart = pie + text
        st.altair_chart(chart, use_container_width=True)
        
        st.markdown("##### Contribution Data Table (Vsys-Referred)")
        st.dataframe(
            df_contributions.sort_values(by="power_mW", ascending=False).set_index("source"),
            column_config={
                "power_mW": st.column_config.NumberColumn("Power (mW)", format="%.3f"),
                "type": "Source Type",
                "percentage": st.column_config.ProgressColumn("Percentage", format="%.3f", min_value=0, max_value=1)
            },
            width='stretch'
        )
    else:
        st.info("No power consumption data to display for the pie chart.")
        

# --- 【tabs[1]】(【已修改】標籤為 uA，儲存 uA) ---
with tabs[1]:
    st.header("Component Management")
    all_groups = sorted(list(set(n['group'] for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component')))
    
    if not all_groups:
        st.info("請先新增元件。")
    else:
        selected_group = st.selectbox("Choose Component", options=all_groups, key="cm_group_selector")
        
        if 'component_group_notes' in st.session_state:
             st.session_state.component_group_notes[selected_group] = st.text_area(
                f"Note for {selected_group}", 
                value=st.session_state.component_group_notes.get(selected_group, ""), 
                key=f"base_note_comp_{selected_group}"
            )
        else:
            st.warning("`component_group_notes` 尚未初始化，請檢查 initialize_data 函數。")
            
        st.markdown("---")
        
        st.subheader(f"Component Current for {selected_group}")
        group_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component' and n['group'] == selected_group]
        
        if selected_group in st.session_state.operating_modes:
            num_modes = len(st.session_state.operating_modes[selected_group])
            
            for mode_name, mode_data in list(st.session_state.operating_modes[selected_group].items()):
                with st.expander(f"{mode_name}", expanded=False):
                    for node in group_nodes:
                        
                        source_id = node.get('input_source_id')
                        source_label = "N/A"
                        if source_id:
                            source_node = get_node_by_id(source_id)
                            if source_node:
                                source_label = source_node.get('label', source_id)
                        
                        widget_key = f"current_{selected_group}_{mode_name}_{node['id']}"

                        if widget_key in st.session_state:
                            current_val_for_widget = st.session_state[widget_key]
                        else:
                            current_val_for_widget = float(mode_data.get('currents_uA', {}).get(node['id'], 0.0))
                        
                        new_label_text = f"Current (uA) - {node['endpoint']} {source_label}"
                        
                        st.number_input(
                            new_label_text,
                            min_value=0.0,
                            value=current_val_for_widget,
                            key=widget_key,
                            format="%.3f"
                        )
                        
                        mode_data['currents_uA'][node['id']] = st.session_state[widget_key]

                    st.markdown("---")
                    mode_data['note'] = st.text_area("Mode Note", value=mode_data.get("note", ""), key=f"note_{selected_group}_{mode_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Rename Mode", value=mode_name, key=f"rename_{selected_group}_{mode_name}", label_visibility="collapsed")
                    with col2:
                        if st.button("Rename", key=f"rename_btn_{selected_group}_{mode_name}"):
                            if new_name and new_name != mode_name and new_name not in st.session_state.operating_modes[selected_group]:
                                st.session_state.operating_modes[selected_group][new_name] = st.session_state.operating_modes[selected_group].pop(mode_name)
                                for uc in st.session_state.use_cases.values():
                                    group_ratios = uc["components"].get(selected_group) 
                                    if group_ratios and mode_name in group_ratios:
                                        group_ratios[new_name] = group_ratios.pop(mode_name)
                                st.rerun()

                    is_default_only_mode = (mode_name == "Default" and num_modes == 1)
                    # (已更新) 擴展 Display Module 的基礎模式列表
                    display_base_modes = ["AOD mode", "NBM (no finger)", "NBM (1 finger)", "Idle mode", "Active - 60Hz", "AOD - 15 Hz"]
                    is_display_module_default = (selected_group == "Display Module" and mode_name in display_base_modes)

                    if not is_default_only_mode and mode_name != "Default" and not is_display_module_default:
                        with st.expander("🗑️ 刪除此模式"):
                            st.warning(f"此操作將永久刪除 '{mode_name}' 模式，無法復原。")
                            if st.button(f"確認永久刪除 '{mode_name}'", key=f"delete_confirm_{selected_group}_{mode_name}", type="primary"):
                                fallback_mode = "Default" if "Default" in st.session_state.operating_modes[selected_group] else list(st.session_state.operating_modes[selected_group].keys())[0]
                                for uc in st.session_state.use_cases.values():
                                    group_ratios = uc["components"].get(selected_group)
                                    if group_ratios and mode_name in group_ratios:
                                        deleted_ratio = group_ratios.pop(mode_name)
                                        group_ratios[fallback_mode] = group_ratios.get(fallback_mode, 0) + deleted_ratio
                                del st.session_state.operating_modes[selected_group][mode_name]
                                st.rerun()
                    elif (is_display_module_default or (mode_name == "Default" and not is_default_only_mode)) :
                            with st.expander("🗑️ 刪除此模式", expanded=False):
                                st.info(f"無法刪除基礎模式 ('{mode_name}')。")
        
        with st.expander("➕ Add New Mode", expanded=False):
            new_mode_name = st.text_input("New Mode Name", key=f"new_mode_{selected_group}")
            if st.button("Add Mode", key=f"add_mode_btn_{selected_group}", type="secondary"):
                if new_mode_name and new_mode_name not in st.session_state.operating_modes.get(selected_group, {}):
                    st.session_state.operating_modes.setdefault(selected_group, {})[new_mode_name] = {
                        "currents_uA": {n['id']: 0.0 for n in st.session_state.power_tree_data['nodes'] 
                                   if n['type'] == 'component' and n['group'] == selected_group},
                        "note": ""
                    }
                    st.rerun()
                elif not new_mode_name:
                    st.error("模式名稱不可為空。")
                else:
                    st.error(f"模式名稱 '{new_mode_name}' 已存在。")

    st.markdown("---")
    st.subheader("Component & Group Settings")

    with st.expander("➕ Add New Component"):
        with st.form(key="add_comp_form", clear_on_submit=True):
            new_group = st.text_input("元件群組名稱", "New Group")
            new_endpoint = st.text_input("電源端點名稱", "New Endpoint")
            power_sources_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source']
            power_source_options = {n['id']: n['label'] for n in power_sources_nodes}
            selected_ps_id = st.selectbox("連接到哪個電源？", options=power_source_options.keys(), format_func=lambda x: power_source_options.get(x, "N/A"))
            
            source_label_new = power_source_options.get(selected_ps_id, 'N/A')
            new_current = st.number_input(
                f"'Default' 模式電流 (uA) ({source_label_new})", 
                min_value=0.0, 
                value=1000.0, 
                format="%.3f"
            )

            submitted = st.form_submit_button("確認新增元件")
            
            if submitted:
                new_id = f"node_{st.session_state.max_id + 1}"
                new_node_data = {"id": new_id, "type": "component"}
                new_node_data.update({"group": new_group, "endpoint": new_endpoint, "power_consumption": 0.0, "input_source_id": selected_ps_id})
                
                if new_group not in st.session_state.operating_modes:
                    st.session_state.operating_modes[new_group] = {"Default": {"currents_uA": {}, "note": "Default operating mode."}}
                    if 'component_group_notes' not in st.session_state:
                         st.session_state.component_group_notes = {}
                    st.session_state.component_group_notes[new_group] = ""

                st.session_state.operating_modes[new_group]["Default"]["currents_uA"][new_id] = new_current
                
                if new_group not in st.session_state.group_colors:
                    st.session_state.group_colors[new_group] = next(DEFAULT_COLORS)
                for uc in st.session_state.use_cases.values():
                    if new_group not in uc["components"]:
                        uc["components"][new_group] = {"Default": 100}
                
                st.session_state.power_tree_data['nodes'].append(new_node_data)
                st.session_state.max_id += 1
                st.success(f"已新增元件: {new_group} - {new_endpoint}")
                st.rerun()

    # --- 【START：已簡化的「編輯元件」區塊】 ---
    with st.expander("✏️ Edit / Delete Component"):
        nodes_list = st.session_state.power_tree_data['nodes']
        def format_node_for_display_comp(node_id):
            node = get_node_by_id(node_id)
            if not node: return "N/A"
            return f"{node['group']} - {node['endpoint']}"
        
        component_nodes = sorted([n for n in nodes_list if n['type'] == 'component'], key=lambda x: (x['group'], x['endpoint']))
        component_node_ids = [n['id'] for n in component_nodes]
        
        if component_node_ids:
            selected_node_id = st.selectbox("選擇要編輯的元件", options=component_node_ids, format_func=format_node_for_display_comp, key="edit_comp_selector")
            node_to_edit = get_node_by_id(selected_node_id)
            
            if node_to_edit:
                original_group = node_to_edit['group']
                edited_group = st.text_input("群組名稱", original_group, key=f"edit_group_{selected_node_id}")
                edited_endpoint = st.text_input("端點名稱", node_to_edit['endpoint'], key=f"edit_endpoint_{selected_node_id}")
                
                power_sources = [n for n in nodes_list if n['type'] == 'power_source']
                ps_options = {n['id']: n['label'] for n in power_sources}
                current_source_id = node_to_edit.get('input_source_id')
                ps_ids = list(ps_options.keys())
                default_index = ps_ids.index(current_source_id) if current_source_id in ps_ids else 0
                selected_ps_id_edit = st.selectbox("連接到哪個電源？", options=ps_ids, format_func=ps_options.get, index=default_index, key=f"edit_comp_source_{selected_node_id}")
                
                # --- 【已移除】「'Default' 模式電流」的相關邏輯 ---

                if st.button("更新元件", key=f"update_comp_{selected_node_id}"):
                    node_to_edit['endpoint'] = edited_endpoint
                    node_to_edit['input_source_id'] = selected_ps_id_edit
                    
                    # --- 【已移除】更新 Default 電流的邏輯 ---

                    if original_group != edited_group:
                        if edited_group not in st.session_state.operating_modes:
                            st.session_state.operating_modes[edited_group] = {"Default": {"currents_uA": {}, "note": "Default operating mode."}}
                            st.session_state.group_colors[edited_group] = next(DEFAULT_COLORS)
                        
                        # 將所有模式的電流資料從舊群組轉移到新群組
                        for op_mode in st.session_state.operating_modes.get(original_group, {}).values():
                            current_val = op_mode["currents_uA"].pop(selected_node_id, None)
                            if current_val is not None:
                                # 找到新群組的對應模式 (假設名稱相同)
                                if op_mode_name in st.session_state.operating_modes.get(edited_group, {}):
                                    st.session_state.operating_modes[edited_group][op_mode_name]["currents_uA"][selected_node_id] = current_val
                                else:
                                    # 如果新群組沒有這個模式，加到 Default
                                    st.session_state.operating_modes[edited_group]["Default"]["currents_uA"][selected_node_id] = current_val

                        for dm in st.session_state.use_cases.values():
                            if original_group in dm["components"]:
                                dm["components"][edited_group] = dm["components"].pop(original_group)
                        node_to_edit['group'] = edited_group
                    
                    st.success("已更新元件")
                    st.rerun()
        else:
            st.info("沒有可編輯的元件。")
    # --- 【END：簡化結束】 ---

    with st.expander("🎨 Group Color Management"):
        all_groups_for_color = sorted(list(set(n['group'] for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component')))
        for group in all_groups_for_color:
            st.session_state.group_colors[group] = st.color_picker(
                f"'{group}' 群組顏色", st.session_state.group_colors.get(group, '#CCCCCC'), key=f"color_{group}"
            )
            
    with st.expander("🖨️ Clone Component Group"):
        
        all_groups_list = sorted(list(set(n['group'] for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component')))
        if not all_groups_list:
            st.info("No component groups to clone.")
        else:
            group_to_clone = st.selectbox(
                "Select group to clone", 
                options=all_groups_list, 
                key="clone_group_src"
            )
            
            new_group_name = st.text_input(
                "New group name", 
                value=f"{group_to_clone} (Copy)", 
                key="clone_group_name"
            )

            if st.button("Clone Group", key="clone_group_btn"):
                if not new_group_name:
                    st.error("New group name cannot be empty.")
                elif new_group_name == group_to_clone:
                    st.error("New group name cannot be the same as the original.")
                elif new_group_name in all_groups_list:
                    st.error(f"The group name '{new_group_name}' already exists.")
                else:
                    try:
                        nodes_to_clone = [n for n in st.session_state.power_tree_data['nodes'] if n.get('group') == group_to_clone]
                        new_nodes = []
                        node_id_map = {} 
                        
                        for node in nodes_to_clone:
                            new_node_id = f"node_{st.session_state.max_id + 1}"
                            st.session_state.max_id += 1
                            node_id_map[node['id']] = new_node_id
                            
                            new_node = copy.deepcopy(node)
                            new_node['id'] = new_node_id
                            new_node['group'] = new_group_name
                            new_nodes.append(new_node)
                        
                        st.session_state.power_tree_data['nodes'].extend(new_nodes)

                        modes_to_clone = copy.deepcopy(st.session_state.operating_modes.get(group_to_clone, {}))
                        new_op_modes = {}
                        
                        for mode_name, mode_data in modes_to_clone.items():
                            new_currents_dict = {}
                            old_currents_dict = mode_data.get("currents_uA", {})
                            
                            for old_node_id, current_val in old_currents_dict.items():
                                new_node_id = node_id_map.get(old_node_id)
                                if new_node_id:
                                    new_currents_dict[new_node_id] = current_val
                            
                            mode_data["currents_uA"] = new_currents_dict
                            new_op_modes[mode_name] = mode_data
                        
                        st.session_state.operating_modes[new_group_name] = new_op_modes

                        for uc in st.session_state.use_cases.values():
                            if new_group_name not in uc["components"]:
                                uc["components"][new_group_name] = {"Default": 100}

                        st.session_state.component_group_notes[new_group_name] = st.session_state.component_group_notes.get(group_to_clone, "")
                        st.session_state.group_colors[new_group_name] = next(DEFAULT_COLORS)

                        st.success(f"Successfully cloned '{group_to_clone}' to '{new_group_name}' with {len(new_nodes)} new nodes.")
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"An error occurred during cloning: {e}")

# --- 【tabs[2]】(【已修改】標籤為 uA) ---
with tabs[2]:
    st.header("Power Source Management")
    all_power_sources = sorted([n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source'], key=lambda x: x['label'])
    
    if not all_power_sources:
        st.info("Please Add The Power Source")
    else:
        ps_options = {ps['id']: ps['label'] for ps in all_power_sources}
        selected_ps_id = st.selectbox("Choose Power Source", options=ps_options.keys(), format_func=ps_options.get, key="psm_ps_selector")
        
        base_node = get_node_by_id(selected_ps_id)
        if base_node: 
            current_note = base_node.get("note", "")
            new_note = st.text_area(
                f"Note for {base_node['label']}", 
                value=current_note,
                key=f"base_note_ps_{selected_ps_id}"
            )
            base_node["note"] = new_note
            
        st.subheader(f"Edit Modes for {ps_options[selected_ps_id]}")
        
        for mode_name, params in list(st.session_state.power_source_modes.get(selected_ps_id, {}).items()):
            if 'note' not in params: params['note'] = ""
            if 'quiescent_current_uA' not in params: params['quiescent_current_uA'] = 0.0 # 相容舊檔
            
            with st.expander(f"{mode_name}", expanded=False):
                
                key_v = f"psm_v_{selected_ps_id}_{mode_name}"
                key_eff = f"psm_eff_{selected_ps_id}_{mode_name}"
                key_iq = f"psm_iq_{selected_ps_id}_{mode_name}"
                key_note = f"psm_note_{selected_ps_id}_{mode_name}"

                if is_off_mode := params.get('output_voltage') == 0 and params.get('efficiency') == 0:
                    st.text_input("Output Voltage (V)", value="0.0 (Off)", disabled=True, key=key_v)
                    st.text_input("Efficiency (%)", value="N/A", disabled=True, key=key_eff)
                    
                    current_iq = params['quiescent_current_uA'] # <-- 已修改
                    st.number_input("Quiescent Current (uA)", min_value=0.0, value=current_iq, key=key_iq, format="%.3f") # <-- 已修改
                    params['quiescent_current_uA'] = st.session_state[key_iq] # <-- 已修改

                else:
                    current_v = params['output_voltage']
                    st.number_input("Output Voltage (V)", value=current_v, key=key_v) 
                    
                    current_eff = params['efficiency'] * 100.0
                    st.number_input("Efficiency (%)", min_value=0.0, max_value=100.0, value=current_eff, key=key_eff)

                    current_iq = params['quiescent_current_uA'] # <-- 已修改
                    st.number_input("Quiescent Current (uA)", min_value=0.0, value=current_iq, key=key_iq, format="%.3f") # <-- 已修改

                    params['output_voltage'] = st.session_state[key_v]
                    params['efficiency'] = st.session_state[key_eff] / 100.0
                    params['quiescent_current_uA'] = st.session_state[key_iq] # <-- 已修改
                
                current_note_val = params.get("note", "")
                st.text_area("Note", value=current_note_val, key=key_note)
                params['note'] = st.session_state[key_note]
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Rename Mode", value=mode_name, key=f"rename_ps_{selected_ps_id}_{mode_name}", label_visibility="collapsed")
                with col2:
                    if st.button("Rename", key=f"rename_ps_btn_{selected_ps_id}_{mode_name}"):
                        if new_name and new_name != mode_name and new_name not in st.session_state.power_source_modes[selected_ps_id]:
                            st.session_state.power_source_modes[selected_ps_id][new_name] = st.session_state.power_source_modes[selected_ps_id].pop(mode_name)
                            for uc in st.session_state.use_cases.values():
                                if uc.get("power_sources", {}).get(selected_ps_id) == mode_name:
                                    uc["power_sources"][selected_ps_id] = new_name
                            
                            old_keys = [key_v, key_eff, key_iq, key_note]
                            for k in old_keys:
                                if k in st.session_state: del st.session_state[k]
                            st.rerun()

                if len(st.session_state.power_source_modes[selected_ps_id]) > 1 and mode_name not in ["On", "Off"]:
                    with st.expander(f"🗑️ 刪除模式 '{mode_name}'"):
                        st.warning(f"此操作將永久刪除 '{mode_name}' 模式，無法復原。")
                        if st.button(f"確認永久刪除 '{mode_name}'", key=f"del_psm_confirm_{selected_ps_id}_{mode_name}", type="primary"):
                            fallback_mode = "On" if "On" in st.session_state.power_source_modes[selected_ps_id] else list(st.session_state.power_source_modes[selected_ps_id].keys())[0]
                            for uc in st.session_state.use_cases.values():
                                if uc.get("power_sources", {}).get(selected_ps_id) == mode_name:
                                    uc["power_sources"][selected_ps_id] = fallback_mode
                            del st.session_state.power_source_modes[selected_ps_id][mode_name]
                            
                            old_keys = [key_v, key_eff, key_iq, key_note]
                            for k in old_keys:
                                if k in st.session_state: del st.session_state[k]
                            st.rerun()
                
        with st.expander("➕ Add New Mode", expanded=False):
            new_ps_mode_name = st.text_input("New Mode Name", key=f"new_ps_mode_{selected_ps_id}")
            if st.button("Add Mode", key=f"add_ps_mode_{selected_ps_id}", type="secondary"):
                if new_ps_mode_name and new_ps_mode_name not in st.session_state.power_source_modes.get(selected_ps_id, {}):
                    st.session_state.power_source_modes.setdefault(selected_ps_id, {})[new_ps_mode_name] = {
                        "output_voltage": 0.0, 
                        "efficiency": 0.9, 
                        "quiescent_current_uA": 0.0, # <-- 已修改
                        "note": ""
                    }
                    st.rerun()
                elif not new_ps_mode_name:
                    st.error("模式名稱不可為空。")
                else:
                    st.error(f"模式名稱 '{new_ps_mode_name}' 已存在。")

    st.markdown("---")
    st.subheader("Power Source Settings")

    with st.expander("➕ Add New Power Source"):
        with st.form(key="add_ps_form", clear_on_submit=True):
            new_label = st.text_input("新電源名稱", "New Power Source")
            ps_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source']
            ps_options = {n['id']: n['label'] for n in ps_nodes}
            ps_options_with_none = {"": "無 (設為根節點)", **ps_options}
            new_input_source_id = st.selectbox("連接到哪個上游電源？", options=ps_options_with_none.keys(), format_func=lambda x: ps_options_with_none.get(x, "N/A"))
            new_efficiency_percent = st.number_input("'On' 模式效率 (%)", 0.0, 100.0, 90.0, step=1.0)
            new_output_voltage = st.number_input("'On' 模式輸出電壓 (V)", min_value=0.0, value=1.8)
            new_quiescent_current = st.number_input("靜態電流 (uA)", min_value=0.0, value=10.0, format="%.3f") # <-- 已修改
            
            submitted = st.form_submit_button("確認新增電源")

            if submitted:
                new_id = f"node_{st.session_state.max_id + 1}"
                new_node_data = {"id": new_id, "type": "power_source"}
                new_node_data.update({
                    "label": new_label, "efficiency": new_efficiency_percent / 100.0, "output_voltage": new_output_voltage,
                    "quiescent_current_uA": new_quiescent_current, "input_source_id": new_input_source_id if new_input_source_id else None # <-- 已修改
                })
                base_note = new_node_data.get("note", "")
                st.session_state.power_source_modes[new_id] = {
                    "On": {"output_voltage": new_output_voltage, "efficiency": new_efficiency_percent / 100.0, "quiescent_current_uA": new_quiescent_current, "note": base_note}, # <-- 已修改
                    "Off": {"output_voltage": 0.0, "efficiency": 0.0, "quiescent_current_uA": new_quiescent_current, "note": "Device is off"} # <-- 已修改
                }
                for uc in st.session_state.use_cases.values():
                    if new_id not in uc["power_sources"]:
                        uc["power_sources"][new_id] = "On"
                
                st.session_state.power_tree_data['nodes'].append(new_node_data)
                st.session_state.max_id += 1
                st.success(f"已新增電源: {new_label}")
                st.rerun()

    with st.expander("✏️ Edit / Delete Power Source"):
        nodes_list = st.session_state.power_tree_data['nodes']
        def format_node_for_display_ps(node_id):
            node = get_node_by_id(node_id)
            if not node: return "N/A"
            return node['label']
        
        power_source_nodes = sorted([n for n in nodes_list if n['type'] == 'power_source'], key=lambda x: x['label'])
        power_source_node_ids = [n['id'] for n in power_source_nodes]
        
        if power_source_node_ids:
            selected_node_id = st.selectbox("選擇要編輯的電源", options=power_source_node_ids, format_func=format_node_for_display_ps, key="edit_ps_selector")
            node_to_edit = get_node_by_id(selected_node_id)
            
            if node_to_edit:
                key_edit_v = f"edit_volt_{selected_node_id}"
                key_edit_eff = f"edit_eff_{selected_node_id}"
                key_edit_iq = f"edit_iq_{selected_node_id}"

                edited_label = st.text_input("名稱", node_to_edit['label'], key=f"edit_label_{selected_node_id}")
                upstream_ps = [n for n in nodes_list if n['type'] == 'power_source' and n['id'] != selected_node_id]
                ups_options = {n['id']: n['label'] for n in upstream_ps}
                ups_options_with_none = {"": "無 (設為根節點)", **ups_options}
                current_ups_id = node_to_edit.get('input_source_id') or ""
                ups_ids = list(ups_options_with_none.keys())
                default_index = ups_ids.index(current_ups_id) if current_ups_id in ups_ids else 0
                selected_ups_id_edit = st.selectbox("連接到哪個上游電源？", options=ups_ids, format_func=ups_options_with_none.get, index=default_index, key=f"edit_ps_source_{selected_node_id}")

                on_mode_params = st.session_state.power_source_modes.get(selected_node_id, {}).get("On", {})
                
                if key_edit_eff not in st.session_state:
                    st.session_state[key_edit_eff] = float(on_mode_params.get('efficiency', 0)) * 100
                st.number_input("'On' 模式效率 (%)", 0.0, 100.0, step=1.0, key=key_edit_eff)
                
                if key_edit_v not in st.session_state:
                    st.session_state[key_edit_v] = float(on_mode_params.get('output_voltage', 0))
                st.number_input("'On' 模式輸出電壓 (V)", 0.0, key=key_edit_v)

                if key_edit_iq not in st.session_state:
                    st.session_state[key_edit_iq] = float(on_mode_params.get('quiescent_current_uA', 0)) # <-- 已修改
                st.number_input("靜態電流 (uA)", min_value=0.0, format="%.3f", key=key_edit_iq) # <-- 已修改

                if st.button("更新電源", key=f"update_ps_{selected_node_id}"):
                    node_to_edit['label'] = edited_label
                    node_to_edit['input_source_id'] = selected_ups_id_edit if selected_ups_id_edit else None
                    
                    edited_output_voltage = st.session_state[key_edit_v]
                    edited_efficiency_percent = st.session_state[key_edit_eff]
                    edited_quiescent_current = st.session_state[key_edit_iq] # <-- 已修改

                    existing_on_note = st.session_state.power_source_modes.get(selected_node_id, {}).get("On", {}).get("note", "")
                    st.session_state.power_source_modes[selected_node_id]["On"] = {
                        "output_voltage": edited_output_voltage,
                        "efficiency": edited_efficiency_percent / 100.0,
                        "quiescent_current_uA": edited_quiescent_current, # <-- 已修改
                        "note": existing_on_note
                    }
                    
                    if "Off" in st.session_state.power_source_modes[selected_node_id]:
                        st.session_state.power_source_modes[selected_node_id]["Off"]["quiescent_current_uA"] = edited_quiescent_current # <-- 已修改
                    
                    del st.session_state[key_edit_v]
                    del st.session_state[key_edit_eff]
                    del st.session_state[key_edit_iq]

                    st.success("已更新電源")
                    st.rerun()
        else:
            st.info("沒有可編輯的電源。")

# --- 【tabs[3]】(Use Case Management) (保持不變) ---
with tabs[3]:
    st.header("Use Case Management")
    
    st.subheader("Edit Use Cases")
    num_use_cases = len(st.session_state.use_cases)
    
    for uc_name, uc_settings in list(st.session_state.use_cases.items()):
        with st.expander(f"{uc_name}", expanded=False):
            
            st.markdown("#### Component Settings")
            all_comp_groups = sorted(list(st.session_state.operating_modes.keys()))
            
            for group in all_comp_groups:
                
                group_modes = list(st.session_state.operating_modes.get(group, {}).keys())
                if not group_modes:
                    st.warning(f"'{group}' 尚未在 ] 中定義任何 Component Mode。")
                    continue
                
                current_ratios = uc_settings.get("components", {}).get(group, {})
                
                with st.expander(f"**{group}**"):
                
                    for mode in group_modes:
                        if mode not in current_ratios: current_ratios[mode] = 0
                    for mode in list(current_ratios.keys()):
                        if mode not in group_modes: del current_ratios[mode]
                    
                    for mode_name in group_modes:
                        left_column, _ = st.columns([1, 3]) 
                        with left_column:
                            sub_col1, sub_col2, sub_col3 = st.columns([2, 1, 1])
                            with sub_col1:
                                st.markdown(f"<p style='padding-top: 8px; padding-left: 20px;'>{mode_name}</p>", unsafe_allow_html=True)
                            with sub_col2:
                                current_ratios[mode_name] = st.number_input(
                                    f"Ratio for {mode_name}", min_value=0, max_value=100, 
                                    value=current_ratios.get(mode_name, 0),
                                    step=1, key=f"uc_ratio_{uc_name}_{group}_{mode_name}", label_visibility="collapsed"
                                )
                            with sub_col3:
                                st.markdown("<p style='padding-top: 8px;'>%</p>", unsafe_allow_html=True)
                    
                    uc_settings["components"][group] = current_ratios

            st.markdown("---")
            st.markdown("#### Power Source Settings")
            all_ps_nodes = sorted([n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source'], key=lambda x: x['label'])
            for ps_node in all_ps_nodes:
                ps_modes = list(st.session_state.power_source_modes.get(ps_node['id'], {}).keys())
                current_ps_mode = uc_settings.get("power_sources", {}).get(ps_node['id'], "On")
                idx = ps_modes.index(current_ps_mode) if current_ps_mode in ps_modes else 0
                
                selected_ps_mode = st.selectbox(
                    f"{ps_node['label']}", options=ps_modes, index=idx, key=f"uc_ps_select_{uc_name}_{ps_node['id']}"
                )
                uc_settings["power_sources"][ps_node['id']] = selected_ps_mode
            
            
            st.markdown("---") 
            if st.button(f"Clone this Use Case", key=f"clone_uc_{uc_name}", type="secondary"):
                new_uc_name = f"{uc_name} (Copy)"
                counter = 2
                while new_uc_name in st.session_state.use_cases:
                    new_uc_name = f"{uc_name} (Copy {counter})"
                    counter += 1
                new_uc_settings = copy.deepcopy(uc_settings)
                st.session_state.use_cases[new_uc_name] = new_uc_settings
                for profile in st.session_state.user_profiles.values():
                    profile[new_uc_name] = 0
                st.success(f"Cloned '{uc_name}' to '{new_uc_name}'.")
                st.rerun()

            
            st.markdown("---")
            st.markdown("##### Rename this Use Case")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                new_uc_name_input = st.text_input(
                    "New use case name", 
                    value=uc_name, 
                    key=f"rename_uc_text_{uc_name}",
                    label_visibility="collapsed"
                )
            with col2:
                if st.button("Rename", key=f"rename_uc_btn_{uc_name}"):
                    if new_uc_name_input == uc_name:
                        st.toast("Name is the same.")
                    elif new_uc_name_input in st.session_state.use_cases:
                        st.error(f"Error: The name '{new_uc_name_input}' already exists.")
                    else:
                        st.session_state.use_cases[new_uc_name_input] = st.session_state.use_cases.pop(uc_name)
                        
                        for profile in st.session_state.user_profiles.values():
                            if uc_name in profile:
                                profile[new_uc_name_input] = profile.pop(uc_name)
                        
                        if st.session_state.active_use_case == uc_name:
                            st.session_state.active_use_case = new_uc_name_input
                        
                        st.success(f"Renamed '{uc_name}' to '{new_uc_name_input}'.")
                        st.rerun()

            if num_use_cases > 1:
                with st.expander(f"🗑️ Delete '{uc_name}'"):
                    st.warning(f"此操作將永久刪除 '{uc_name}' Use Case，無法復原。")
                    if st.button(f"確認永久刪除 '{uc_name}'", key=f"del_uc_confirm_{uc_name}", type="primary"):
                        mode_to_delete = uc_name
                        
                        if st.session_state.active_use_case == mode_to_delete:
                            del st.session_state.use_cases[mode_to_delete]
                            st.session_state.active_use_case = list(st.session_state.use_cases.keys())[0]
                        else:
                            del st.session_state.use_cases[mode_to_delete]

                        for profile in st.session_state.user_profiles.values():
                            if mode_to_delete in profile:
                                del profile[mode_to_delete]
                        st.rerun()

    with st.expander("➕ Add New Use Case", expanded=False):
        new_uc_name = st.text_input("New Use Case Name", key="new_uc_name")
        if st.button("Add Use Case", key="add_uc_btn", type="secondary"):
            if new_uc_name and new_uc_name not in st.session_state.use_cases:
                all_comp_groups = set(n['group'] for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component')
                all_ps_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source']
                
                st.session_state.use_cases[new_uc_name] = {
                    "components": {group: {"Default": 100} for group in all_comp_groups},
                    "power_sources": {ps['id']: "On" for ps in all_ps_nodes}
                }
                for profile in st.session_state.user_profiles.values():
                    profile[new_uc_name] = 0
                st.rerun()
            elif not new_uc_name:
                st.error("Use Case 名稱不可為空。")
            else:
                st.error(f"Use Case '{new_uc_name}' 已存在。")

# --- 【tabs[4]】(【已修改】顯示 uA) ---
with tabs[4]:
    st.header("Battery Life Estimation")

    st.number_input("Battery Capacity (mAh)", min_value=0.0, value=st.session_state.battery_capacity_mAh, key="battery_capacity_input")
    st.session_state.battery_capacity_mAh = st.session_state.battery_capacity_input

    st.markdown("---")
    st.subheader("Estimation Results per Profile")

    power_per_use_case = {uc: calculate_power(use_case_name_override=uc) for uc in st.session_state.use_cases}
    vsys_node = get_node_by_id("battery")
    vsys_voltage = vsys_node['output_voltage'] if vsys_node else 3.85

    for profile_name, profile_data in list(st.session_state.user_profiles.items()):
        
        total_energy_mWh = sum(power_per_use_case.get(uc_name, 0) * profile_data.get(uc_name, 0) for uc_name in profile_data)
        total_hours_in_profile = sum(profile_data.values())
        avg_power_mW = total_energy_mWh / 24 if total_hours_in_profile > 0 else 0
        avg_current_mA = avg_power_mW / vsys_voltage if vsys_voltage > 0 else 0
        
        if avg_current_mA > 0:
            battery_life_hours = st.session_state.battery_capacity_mAh / avg_current_mA
            battery_life_days = battery_life_hours / 24
            life_display_str = f"{battery_life_days:.2f} Days"
        else:
            battery_life_days = 0 
            life_display_str = "Infinite"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label=f"**{profile_name}**", value=life_display_str)
        with col2:
            st.metric(label="Avg. Power", value=f"{avg_power_mW:.2f} mW")
        with col3:
            # 【已修改】顯示 uA，並顯示到整數
            st.metric(label="Avg. Current", value=f"{avg_current_mA * 1000.0:.0f} uA")
            
        with st.expander(f"編輯 '{profile_name}' 設定檔", expanded=False):
            
            for uc_name in st.session_state.use_cases:
                if uc_name not in profile_data: profile_data[uc_name] = 0
            for uc_name in list(profile_data.keys()):
                if uc_name not in st.session_state.use_cases: del profile_data[uc_name]

            total_hours = 0
            for uc_name in st.session_state.use_cases:
                hours = st.slider(
                    f"Hours in '{uc_name}'", 0, 24, 
                    value=profile_data.get(uc_name, 0), 
                    key=f"profile_{profile_name}_{uc_name}"
                )
                profile_data[uc_name] = hours
                total_hours += hours
            
            st.metric("Total Hours per Day", f"{total_hours} / 24")
            if total_hours != 24:
                st.warning("為獲得準確的每日估算，設定檔的總時數應為 24 小時。")
            
            if len(st.session_state.user_profiles) > 1:
                with st.expander(f"🗑️ 刪除設定檔 '{profile_name}'"):
                    st.warning(f"此操作將永久刪除 '{profile_name}' 設定檔，無法復原。")
                    if st.button(f"確認永久刪除 '{profile_name}'", key=f"del_profile_confirm_{profile_name}", type="primary"):
                        del st.session_state.user_profiles[profile_name]
                        st.rerun()

    st.markdown("---")
    with st.expander("➕ Add New Profile"):
        profile_name = st.text_input("New Profile Name")
        if st.button("Add Profile", type="secondary"):
            if profile_name and profile_name not in st.session_state.user_profiles:
                st.session_state.user_profiles[profile_name] = {uc_name: 0 for uc_name in st.session_state.use_cases}
                st.rerun()
            elif not profile_name:
                st.error("設定檔名稱不可為空。")
            else:
                st.error(f"設定檔 '{profile_name}' 已存在。")


# ---
# 在所有狀態更新後，執行最終的計算與渲染
# ---
total_power = calculate_power(st.session_state.active_use_case)

power_placeholder.write(f"<strong>Total System Power:</strong> {total_power:.2f} mW", unsafe_allow_html=True)
vsys_node = get_node_by_id("battery")
if vsys_node and vsys_node.get('output_voltage', 0) > 0:
    current_mA = total_power / vsys_node['output_voltage']
    # 【已修改】顯示 uA，並顯示到整數
    current_placeholder.write(f"<strong>Total Vsys Current:</strong> {current_mA * 1000.0:.0f} uA", unsafe_allow_html=True)

# 繪製 Power Tree
if st.session_state.theme == "Dark":
    graph_bgcolor = "black"
    edge_color = "white"
    font_color = "#CCCCCC"
    table_border_color = "white"
else: # Light theme
    graph_bgcolor = "white"
    edge_color = "black"
    font_color = "#555555"
    table_border_color = "black"

dot = graphviz.Digraph(comment='Power Tree')
dot.attr(rankdir='LR', splines='line', ranksep='0.5', nodesep='0.15', center='true', bgcolor=graph_bgcolor)
dot.attr('edge', color=edge_color, fontname='Arial', fontsize='10', fontcolor=font_color)

nodes = st.session_state.power_tree_data['nodes']
for node in [n for n in nodes if n['type'] == 'power_source']:
    pin_str = f"Pin: {node.get('input_power', 0):.2f}mW" if node.get('input_source_id') else "Pin: N/A"
    pout_str = f"Pout: {node.get('output_power_total', 0):.2f}mW"
    eff_str = f"eff: {node.get('efficiency', 1.0) * 100:.0f}%" if node.get('efficiency', 0) > 0 else "eff: N/A"
    # 【已修改】顯示 uA
    iq_str = f"Iq: {node.get('quiescent_current_uA', 0.0):.1f}uA"
    
    pin_pout_str = f'{pin_str} &nbsp;|&nbsp; {pout_str}'
    details_html = f"{pin_pout_str}<BR/>{eff_str}<BR/>{iq_str}"
    
    table = (f'<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5" COLOR="{table_border_color}">'
             f'<TR><TD BGCOLOR="#2196F3" ALIGN="CENTER"><B><FONT COLOR="white">{node["label"]}</FONT></B></TD></TR>'
             f'<TR><TD ALIGN="CENTER" BGCOLOR="#FFFFFF"><FONT COLOR="black">{details_html}</FONT></TD></TR>'
             f'</TABLE>')
    dot.node(node['id'], label=f'<{table}>', shape='none')

with dot.subgraph(name='cluster_components') as c:
    c.attr(rank='sink', style='invis')
    components = [n for n in nodes if n['type'] == 'component']
    components.sort(key=lambda x: x['group'])
    for node in components:
        group_color = st.session_state.group_colors.get(node['group'], "#CCCCCC")
        power_details = f"Power: {node.get('power_consumption', 0):.2f}mW"
        combined_details = f'{node["endpoint"]}<BR/>{power_details}'
        table = (f'<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5" COLOR="{table_border_color}">'
               f'<TR><TD BGCOLOR="{group_color}" ALIGN="CENTER"><B><FONT COLOR="white">{node["group"]}</FONT></B></TD></TR>'
               f'<TR><TD ALIGN="CENTER" BGCOLOR="#FFFFFF"><FONT COLOR="black">{combined_details}</FONT></TD></TR>'
               f'</TABLE>')
        c.node(node['id'], label=f'<{table}>', shape='none')

for node in nodes:
    if node.get('input_source_id'):
        source = get_node_by_id(node['input_source_id'])
        if source:
            voltage = source.get('output_voltage', 0)
            power = node.get('input_power', 0) if node['type'] == 'power_source' else node.get('power_consumption', 0)
            current_mA = power / voltage if voltage > 0 else 0
            # 【已修改】邊線顯示 uA
            edge_label = f"{voltage:.2f} V\n{current_mA * 1000.0:.1f} uA"
            dot.edge(node['input_source_id'], node['id'], label=edge_label, tailport='e', headport='w')

graph_placeholder.graphviz_chart(dot)
