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
st.title("Mukai Power Model and Battery Life Calculation V1.2")

# JavaScript 元件的 import
import streamlit.components.v1 as components

# ===============================================================
#  CSS 樣式
# ===============================================================

if 'theme' not in st.session_state:
    st.session_state.theme = "Dark"

st.markdown("""
<style>
/* Custom styling for ratio inputs in Device Mode Management */
div[data-testid="stVerticalBlock"] .stNumberInput {
    max-width: 120px;
}
</style>
""", unsafe_allow_html=True)


if st.session_state.theme == "Dark":
    st.markdown("""
        <style>
        /* 深色主題：主頁面與側邊欄背景 */
        .stApp, [data-testid="stSidebar"] {
            background-color: #0e1117;
        }
        /* 深色主題：所有文字顏色 */
        h1, h2, h3, h4, h5, h6, .st-emotion-cache-16txtl3, p, .st-emotion-cache-1y4p8pa {
            color: #fafafa !important;
        }
        
        /* 設定 Expander 標頭與箭頭顏色 */
        [data-testid="stExpander"] summary {
            color: #fafafa !important;
        }
        /* 設定 Expander 內容區塊的背景色 */
        div[data-testid="stExpander"] div[role="region"] {
             background-color: #1c1f2b; 
        }
        </style>
    """, unsafe_allow_html=True)
else: # Light Theme
    st.markdown("""
        <style>
        /* 淺色主題：主頁面背景 */
        .stApp {
            background-color: #FFFFFF;
        }
        /* 淺色主題：側邊欄背景 (淺灰色) */
        [data-testid="stSidebar"] {
            background-color: #F0F2F6;
        }
        /* 淺色主題：所有文字顏色 */
        h1, h2, h3, h4, h5, h6, .st-emotion-cache-16txtl3, p, .st-emotion-cache-1y4p8pa {
            color: #0e1117 !important;
        }
        /* 設定 Expander 標頭與箭頭顏色為黑色 */
        [data-testid="stExpander"] summary {
            color: #0e1117 !important;
        }
        /* 設定 Expander 內容區塊的背景色，使其與側邊欄一致 */
        div[data-testid="stExpander"] div[role="region"] {
             background-color: #F0F2F6;
        }
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

    # --- 1. 節點定義 (保持不變) ---
    st.session_state.power_tree_data = {
        "nodes": [
            # Power Sources
            {"id": "battery", "label": "Vsys", "type": "power_source", "output_voltage": 3.85, "efficiency": 1.0, "quiescent_current_mA": 0.0, "input_source_id": None},
            {"id": "vbb", "label": "VBB", "type": "power_source", "output_voltage": 3.9, "efficiency": 0.9, "quiescent_current_mA": 0.01, "input_source_id": "battery"},
            {"id": "pmic_buck", "label": "PMIC (BUCK_1V8)", "type": "power_source", "output_voltage": 1.8, "efficiency": 0.95, "quiescent_current_mA": 0.05, "input_source_id": "battery"},
            {"id": "pmic_ldo1", "label": "PMIC (LDO1)", "type": "power_source", "output_voltage": 3.3, "efficiency": 0.85, "quiescent_current_mA": 0.02, "input_source_id": "battery"},
            {"id": "pmic_ldo2", "label": "PMIC (LDO2)", "type": "power_source", "output_voltage": 3.6, "efficiency": 0.85, "quiescent_current_mA": 0.02, "input_source_id": "vbb"},
            {"id": "display_1v8", "label": "Display 1V8", "type": "power_source", "output_voltage": 1.8, "efficiency": 0.9, "quiescent_current_mA": 0.01, "input_source_id": "pmic_buck"},
            {"id": "ext_ldo_avdd", "label": "ext. LDO AVDD", "type": "power_source", "output_voltage": 3.0, "efficiency": 0.85, "quiescent_current_mA": 0.01, "input_source_id": "battery"},
            {"id": "ldo_mcu", "label": "LDO_MCU", "type": "power_source", "output_voltage": 0.9, "efficiency": 0.5, "quiescent_current_mA": 0.01, "input_source_id": "battery"},
            {"id": "dd_ovdd", "label": "Display Driver OVDD", "type": "power_source", "output_voltage": 4.5, "efficiency": 0.85, "quiescent_current_mA": 0.03, "input_source_id": "battery"},
            {"id": "dd_ovss", "label": "Display Driver OVSS", "type": "power_source", "output_voltage": 4.5, "efficiency": 0.85, "quiescent_current_mA": 0.03, "input_source_id": "battery"},
            {"id": "ls_mcu", "label": "LS MCU", "type": "power_source", "output_voltage": 1.2, "efficiency": 0.85, "quiescent_current_mA": 0.01, "input_source_id": "pmic_buck"},
            {"id": "lsw3_mcu", "label": "LSW3 MCU", "type": "power_source", "output_voltage": 1.8, "efficiency": 0.85, "quiescent_current_mA": 0.01, "input_source_id": "pmic_buck"},
            {"id": "drv2624", "label": "DRV2624", "type": "power_source", "output_voltage": 1.8, "efficiency": 0.85, "quiescent_current_mA": 0.01, "input_source_id": "pmic_buck", "note": "I2C Address: 0x5A and 0x58"},
            
            # Components (power_consumption 欄位現在只在初始化時使用一次)
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
    st.session_state.max_id = 26 # <-- 已修正回 26

    st.session_state.group_colors = {
        "SoC": "#FFC107", "Display Module": "#4CAF50", "AFE4510": "#F44336",
        "ALS": "#607D8B", "Temp Sensor TMP118A": "#E91E63", "Barometer": "#03A9F4",
        "GNSS": "#FF9800", "Flash": "#795548", "IMU": "#9E9E9E", "Temp Sensor TMP118B": "#00BCD4"
    }
    
    component_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component']
    power_source_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source']
    all_comp_groups = set(n['group'] for n in component_nodes)
    
    # --- 2. 【已修改】先初始化 Power Source Modes (為了取得 "On" 電壓) ---
    st.session_state.power_source_modes = {}
    for ps in power_source_nodes:
        base_note = ps.get("note", "") 
        st.session_state.power_source_modes[ps['id']] = {
            "On": {
                "output_voltage": ps['output_voltage'], 
                "efficiency": ps['efficiency'], 
                "quiescent_current_mA": ps['quiescent_current_mA'],
                "note": base_note
            },
            "Off": {
                "output_voltage": 0.0, 
                "efficiency": 0.0, 
                "quiescent_current_mA": ps['quiescent_current_mA'],
                "note": "Device is off"
            }
        }

    # --- 3. 【已修改】建立 Operating Modes (儲存 "currents_mA") ---
    st.session_state.operating_modes = {}
    
    # 輔助函數：根據 "On" 電壓將預設功率轉換為電流
    def get_default_current(node):
        source_id = node.get('input_source_id')
        if not source_id: return 0.0
        
        # 從剛建立的 power_source_modes 讀取 "On" 電壓
        source_voltage = st.session_state.power_source_modes.get(source_id, {}).get("On", {}).get("output_voltage", 1.0)
        
        if source_voltage == 0: return 0.0
        return node.get('power_consumption', 0.0) / source_voltage

    for group in all_comp_groups:
        group_nodes = [n for n in component_nodes if n['group'] == group]
        
        if group == "Display Module":
            # 預設電流 (來自節點定義)
            default_currents = {n['id']: get_default_current(n) for n in group_nodes}
            # Idle 電流 (全 0)
            idle_currents = {n['id']: 0.0 for n in group_nodes}

            st.session_state.operating_modes[group] = {
                "AOD mode": {
                    "currents_mA": copy.deepcopy(default_currents), # 使用預設值
                    "note": "50nits, OPR 20%, 15Hz refresh rate, 15Hz touch scan rate"
                },
                "NBM (no finger)": {
                    "currents_mA": copy.deepcopy(default_currents), # 使用預設值
                    "note": "200nits, OPR 50%, 60Hz refresh rate, 60Hz touch scan rate, no finger"
                },
                "NBM (1 finger)": {
                    "currents_mA": copy.deepcopy(default_currents), # 使用預設值
                    "note": "200nits, OPR 50%, 60Hz refresh rate, 120Hz touch scan rate, 1 finger"
                },
                "Idle mode": {
                    "currents_mA": idle_currents, # 預設為 0.0
                    "note": "Display off, touch 20Hz"
                }
            }
        else:
            # 針對所有其他群組，轉換 "Default" 功率為電流
            default_currents = {n['id']: get_default_current(n) for n in group_nodes}
            st.session_state.operating_modes[group] = {
                "Default": {
                    "currents_mA": default_currents,
                    "note": "Default operating mode."
                }
            }

    st.session_state.component_group_notes = {group: "" for group in all_comp_groups}

    # --- 4. 建立 Device Modes (已更新為「非比例」) ---
    default_comp_settings_base = {
        group: "Default" 
        for group in all_comp_groups if group != "Display Module"
    }
    default_ps_settings = {ps['id']: "On" for ps in power_source_nodes}

    dm_idle_day = {
        "components": copy.deepcopy(default_comp_settings_base),
        "power_sources": copy.deepcopy(default_ps_settings)
    }
    dm_idle_day["components"]["Display Module"] = "Idle mode"

    dm_idle_night = {
        "components": copy.deepcopy(default_comp_settings_base),
        "power_sources": copy.deepcopy(default_ps_settings)
    }
    dm_idle_night["components"]["Display Module"] = "Idle mode"

    dm_exercise = {
        "components": copy.deepcopy(default_comp_settings_base),
        "power_sources": copy.deepcopy(default_ps_settings)
    }
    dm_exercise["components"]["Display Module"] = "NBM (1 finger)"

    dm_aod = {
        "components": copy.deepcopy(default_comp_settings_base),
        "power_sources": copy.deepcopy(default_ps_settings)
    }
    dm_aod["components"]["Display Module"] = "AOD mode"
    
    st.session_state.device_modes = {
        "Exercise Mode": dm_exercise,
        "Idle Day Mode": dm_idle_day,
        "Idle Night Mode": dm_idle_night,
        "AOD Mode": dm_aod
    }
    
    st.session_state.active_device_mode = "Exercise Mode"
    
    # --- 5. User Profiles (保持不變) ---
    st.session_state.battery_capacity_mAh = 64.5
    st.session_state.user_profiles = {
        "P75 - Typical User / SPEC 7 days": {
            "Idle Day Mode": 10,
            "Idle Night Mode": 8,
            "Exercise Mode": 4,
            "AOD Mode": 2
        },
        # ... (其他 profiles 保持不變) ...
         "Hibernation / SPEC 2.5days": {
            "Idle Day Mode": 6,
            "Idle Night Mode": 6,
            "Exercise Mode": 8,
            "AOD Mode": 4
        },
    }
    st.session_state.active_user_profile = "Typical User"
    
    st.session_state.initialized = True

initialize_data()

# ---
# 核心功能函數 (Core Functions)
# ---

def get_node_by_id(node_id):
    return next((n for n in st.session_state.power_tree_data['nodes'] if n['id'] == node_id), None)

def apply_device_mode(mode_name_override=None):
    if mode_name_override:
        active_dm_name = mode_name_override
    else:
        active_dm_name = st.session_state.get('active_device_mode', 'Exercise Mode')
        if active_dm_name not in st.session_state.device_modes:
            active_dm_name = list(st.session_state.device_modes.keys())[0]
            st.session_state.active_device_mode = active_dm_name

    active_dm = st.session_state.device_modes[active_dm_name]
    
    # --- 【步驟 1：設定所有電源的電壓】 ---
    ps_settings = active_dm.get("power_sources", {})
    for node in st.session_state.power_tree_data['nodes']:
        if node['type'] == 'power_source':
            ps_mode_name = ps_settings.get(node['id'], "On")
            if ps_mode_name not in st.session_state.power_source_modes.get(node['id'], {}):
                ps_mode_name = "On" 
            
            mode_params = st.session_state.power_source_modes[node['id']][ps_mode_name]
            node['output_voltage'] = mode_params['output_voltage']
            node['efficiency'] = mode_params['efficiency']
            node['quiescent_current_mA'] = mode_params['quiescent_current_mA']

    # --- 【步驟 2：計算所有元件的功率】 ---
    comp_settings = active_dm.get("components", {}) 
    for node in st.session_state.power_tree_data['nodes']:
        if node['type'] == 'component':
            group = node['group']
            
            # 1. 取得這個群組被選定的「單一模式」名稱 (例如 "Test Mode")
            selected_mode_name = comp_settings.get(group)
            
            if selected_mode_name:
                # 2. 取得該模式下，這個 node 應有的「電流 (mA)」
                current_mA = st.session_state.operating_modes.get(group, {}).get(
                    selected_mode_name, {}
                ).get('currents_mA', {}).get(node['id'], 0.0) # <-- 讀取 currents_mA
                
                # 3. 取得此 node 的電源
                source_node = get_node_by_id(node.get('input_source_id'))
                
                # 4. 取得該電源「當前」的電壓 (已在步驟 1 中設定)
                current_voltage = 0.0
                if source_node:
                    current_voltage = source_node.get('output_voltage', 0.0) # <-- 讀取 node 的即時電壓
                
                # 5. 計算 P = V * I
                power_mW = current_voltage * current_mA
                
                node['power_consumption'] = power_mW
            else:
                node['power_consumption'] = 0.0

def calculate_power(mode_name_override=None):
    apply_device_mode(mode_name_override)
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
                return 0.0 # Component receives 0V, consumes 0 power regardless of mode
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
        quiescent_power = input_voltage * node.get('quiescent_current_mA', 0.0)
        
        total_input_power = input_power_from_load + quiescent_power
        node['input_power'] = total_input_power
        
        memo[node_id] = total_input_power
        return total_input_power

    root_nodes = [n for n in nodes if n.get('input_source_id') is None]
    total_system_power_mW = sum(recursive_power_calc(root['id'], set()) for root in root_nodes)
    return total_system_power_mW


def get_vsys_referred_power_contributions(node_list):
    """
    (已更新：獨立列出 Component Groups, Iq Loss, 和 Efficiency Loss)
    計算每個元件群組、每個 Iq 損耗、每個效率損耗對 Vsys 的 "參考功耗"。
    """

    # 內部輔助函數
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

    # --- 2. 計算所有「電源損耗」 (Iq Loss + Efficiency Loss) ---
    power_source_nodes = [n for n in node_list if n['type'] == 'power_source']
    for node in power_source_nodes:
        
        # === A. 計算 靜態電流 (Iq) 損耗 (獨立列出) ===
        quiescent_current_mA = node.get('quiescent_current_mA', 0.0)
        if quiescent_current_mA > 0:
            parent_node = get_node_by_id(node.get('input_source_id'))
            if parent_node:
                input_voltage = parent_node.get('output_voltage', 0.0)
                parent_id_to_trace_from = parent_node.get('id')
            else:
                # This is a root node (like 'battery'), its Iq is its own load.
                input_voltage = node.get('output_voltage', 0.0) 
                parent_id_to_trace_from = None 

            iq_load_mW = input_voltage * quiescent_current_mA
            vsys_referred_iq_power = trace_power_to_root(iq_load_mW, parent_id_to_trace_from)

            if vsys_referred_iq_power > 0.0001: # 過濾掉極小值
                label = f"{node['label']} (Iq Loss)"
                contributions.append({
                    "source": label,
                    "power_mW": vsys_referred_iq_power,
                    "type": "Quiescent Loss"
                })

        # === B. 計算 效率 (Efficiency) 損耗 (獨立列出) ===
        efficiency = node.get('efficiency', 1.0)
        if 0 < efficiency < 1.0: # 找出所有有效率損耗的穩壓器
            output_power_mW = node.get('output_power_total', 0.0)
            if output_power_mW > 0:
                # 效率損耗 = 輸出功率 * ( (1 / 效率) - 1 )
                efficiency_loss_mW = output_power_mW * ((1.0 / efficiency) - 1.0)
                
                # 將損耗換算回 Vsys 參考值
                vsys_referred_eff_loss = trace_power_to_root(efficiency_loss_mW, node.get('input_source_id'))
                
                if vsys_referred_eff_loss > 0.0001:
                    label = f"{node['label']} (Efficiency Loss)"
                    contributions.append({
                        "source": label,
                        "power_mW": vsys_referred_eff_loss,
                        "type": "Efficiency Loss"
                    })

    if not contributions:
        return pd.DataFrame(columns=["source", "power_mW", "type"])
        
    df = pd.DataFrame(contributions)

    # --- 3. GroupBy (僅加總 Component Loads) ---
    df_components = df[df['type'] == 'Component Load']
    df_losses = df[df['type'] != 'Component Load'] # 選取所有非元件負載 (Iq + Efficiency)
    
    if not df_components.empty:
        df_components_grouped = df_components.groupby('source').agg(
            power_mW=('power_mW', 'sum'),
            type=('type', 'first')
        ).reset_index()
    else:
        df_components_grouped = pd.DataFrame(columns=['source', 'power_mW', 'type'])
    
    # 將加總後的 Component 和「所有獨立的損耗項」重新組合
    final_df = pd.concat([df_components_grouped, df_losses], ignore_index=True)
    
    return final_df


# ===============================================================
#  側邊欄 UI (Sidebar UI) - 【已簡化】
# ===============================================================

with st.sidebar:
    
    # --- JS 元件已移至此處 ---
    components.html(
    """
    <script>
    window.addEventListener("beforeunload", function (e) {
        var confirmationMessage = "您有未儲存的修改，確定要離開嗎？";
        e.returnValue = confirmationMessage; // 舊版瀏覽器
        return confirmationMessage;          // 新版瀏覽器
    });
    </script>
    """,
    height=0, # 隱藏元件
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

    # --- 【設定檔管理】(已正確縮排) ---
    st.markdown("---")
    st.header("設定檔管理")

    with st.expander("儲存目前設定", expanded=False):
        state_to_save = {
            'power_tree_data': st.session_state.power_tree_data,
            'max_id': st.session_state.max_id,
            'group_colors': st.session_state.group_colors,
            'operating_modes': st.session_state.operating_modes,
            'power_source_modes': st.session_state.power_source_modes,
            'device_modes': st.session_state.device_modes,
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
                    
                    required_keys = ['power_tree_data', 'device_modes', 'user_profiles']
                    if not all(key in loaded_data for key in required_keys):
                        st.error("錯誤：上傳的檔案格式不正確或缺少必要的鍵。")
                    else:
                        for key, value in loaded_data.items():
                            st.session_state[key] = value
                        
                        st.session_state.initialized = True 
                        st.success("設定已成功載入！頁面將自動刷新。")
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("錯誤：無法解析 JSON 檔案。請確認檔案內容是否為有效的 JSON 格式。")
                except Exception as e:
                    st.error(f"讀取檔案時發生錯誤: {e}")

# === 側邊欄結束 ===


# ===============================================================
#  主內容頁面 (Main Content)
# ===============================================================

tabs = st.tabs(["Power Tree", "Component Management", "Power Source Management", "Device Mode Management", "Battery Life Estimation"])

calculate_power(st.session_state.active_device_mode)

with tabs[0]:
    st.header("Power Consumption Analysis")
    
    st.subheader("Device Mode Selection")
    device_modes_list = list(st.session_state.device_modes.keys())
    active_device_mode = st.session_state.get('active_device_mode', 'Exercise Mode')
    try:
        current_index = device_modes_list.index(active_device_mode)
    except ValueError:
        current_index = 0 if not device_modes_list else device_modes_list.index(device_modes_list[0])

    selected_device_mode = st.radio(
        "Select Device Mode to Display", 
        options=device_modes_list, 
        index=current_index, 
        horizontal=True,
        label_visibility="collapsed"
    )
    if st.session_state.active_device_mode != selected_device_mode:
        st.session_state.active_device_mode = selected_device_mode
        st.rerun()
    
    power_placeholder = st.empty()
    current_placeholder = st.empty()
    
    with st.expander("Show / Hide Power Tree Visualizer", expanded=True):
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
            other_df = pd.DataFrame([{
                "source": "Others (<1%)", 
                "power_mW": other_power, 
                "type": "Others",
                "percentage": other_percentage
            }])
            df_chart = pd.concat([df_main, other_df], ignore_index=True)
        else:
            df_chart = df_main

        # --- 【START：修正圓餅圖文字顏色】 ---
        
        # 根據主題決定文字顏色
        if st.session_state.theme == "Dark":
            pie_text_color = "white"
        else:
            pie_text_color = "black"

        base = alt.Chart(df_chart).encode(
           theta=alt.Theta("power_mW:Q", stack=True)
        ).properties(
           title="Breakdown of Total Vsys Power Draw"
        )

        pie = base.mark_arc(outerRadius=160, innerRadius=0).encode(
            color=alt.Color("source:N", title="Power Source"),
            order=alt.Order("percentage:Q", sort="descending"),
            tooltip=["source", 
                     alt.Tooltip("power_mW:Q", format=".2f"), 
                     alt.Tooltip("percentage:Q", format=".1%")]
        )

        # 百分比文字
        text = base.mark_text(radius=180).encode(
            text=alt.Text("percentage:Q", format=".1%"),
            order=alt.Order("percentage:Q", sort="descending"),
            color=alt.value(pie_text_color)  # <-- 【已修改】 使用動態顏色
        )
        # --- 【END：修正】 ---

        chart = pie + text
        
        st.altair_chart(chart, use_container_width=True)
        
        st.markdown("##### Contribution Data Table (Vsys-Referred)")
        
        st.dataframe(
            df_contributions.sort_values(by="power_mW", ascending=False).set_index("source"),
            column_config={
                "power_mW": st.column_config.NumberColumn("Power (mW)", format="%.3f"),
                "type": "Source Type",
                "percentage": st.column_config.ProgressColumn(
                    "Percentage", 
                    format="%.3f", 
                    min_value=0,
                    max_value=1
                )
            },
            width='stretch'
        )
    else:
        st.info("No power consumption data to display for the pie chart.")
        
# --- 【tabs[1]】(已更新為電流輸入和群組 Note) ---
with tabs[1]:
    st.header("Component Mode Management")
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
                        
                        # --- 【START：邏輯簡化 - 只處理電流】 ---
                        source_id = node.get('input_source_id')
                        source_label = "N/A"
                        if source_id:
                            source_node = get_node_by_id(source_id)
                            if source_node:
                                source_label = source_node.get('label', source_id)
                        
                        widget_key = f"current_{selected_group}_{mode_name}_{node['id']}"

                        # 1. 讀取儲存的「電流 (mA)」
                        if widget_key in st.session_state:
                            current_val_for_widget = st.session_state[widget_key]
                        else:
                            current_val_for_widget = float(mode_data.get('currents_mA', {}).get(node['id'], 0.0))
                        
                        # 2. 建立標籤 (只顯示電源名稱)
                        new_label_text = f"Current (mA) - {node['endpoint']} {source_label}"
                        
                        st.number_input(
                            new_label_text,
                            min_value=0.0,
                            value=current_val_for_widget,
                            key=widget_key,
                            format="%.3f"
                        )
                        
                        # 3. 將「電流 (mA)」存回 session_state
                        mode_data['currents_mA'][node['id']] = st.session_state[widget_key]
                        # --- 【END：修正結束】 ---

                    st.markdown("---")
                    mode_data['note'] = st.text_area("Mode Note", value=mode_data.get("note", ""), key=f"note_{selected_group}_{mode_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Rename Mode", value=mode_name, key=f"rename_{selected_group}_{mode_name}", label_visibility="collapsed")
                    with col2:
                        if st.button("Rename", key=f"rename_btn_{selected_group}_{mode_name}"):
                            if new_name and new_name != mode_name and new_name not in st.session_state.operating_modes[selected_group]:
                                st.session_state.operating_modes[selected_group][new_name] = st.session_state.operating_modes[selected_group].pop(mode_name)
                                for dm in st.session_state.device_modes.values():
                                    if group in dm["components"] and dm["components"][group] == mode_name:
                                        dm["components"][group] = new_name
                                st.rerun()

                    is_default_only_mode = (mode_name == "Default" and num_modes == 1)
                    is_display_module_default = (selected_group == "Display Module" and mode_name in ["AOD mode", "NBM (no finger)", "NBM (1 finger)", "Idle mode"])
                    if not is_default_only_mode and mode_name != "Default" and not is_display_module_default:
                        with st.expander("🗑️ 刪除此模式"):
                            st.warning(f"此操作將永久刪除 '{mode_name}' 模式，無法復原。")
                            if st.button(f"確認永久刪除 '{mode_name}'", key=f"delete_confirm_{selected_group}_{mode_name}", type="primary"):
                                fallback_mode = "Default" if "Default" in st.session_state.operating_modes[selected_group] else list(st.session_state.operating_modes[selected_group].keys())[0]
                                for dm in st.session_state.device_modes.values():
                                    if group in dm["components"] and dm["components"][group] == mode_name:
                                        dm["components"][group] = fallback_mode
                                del st.session_state.operating_modes[selected_group][mode_name]
                                st.rerun()
                    elif (is_display_module_default or mode_name == "Default") and not is_default_only_mode:
                            with st.expander("🗑️ 刪除此模式", expanded=False):
                                st.info(f"無法刪除基礎模式 ('{mode_name}')。")
        
        with st.expander("➕ Add New Mode", expanded=False):
            new_mode_name = st.text_input("New Mode Name", key=f"new_mode_{selected_group}")
            if st.button("Add Mode", key=f"add_mode_btn_{selected_group}", type="secondary"):
                if new_mode_name and new_mode_name not in st.session_state.operating_modes.get(selected_group, {}):
                    st.session_state.operating_modes.setdefault(selected_group, {})[new_mode_name] = {
                        "currents_mA": {n['id']: 0.0 for n in st.session_state.power_tree_data['nodes'] 
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
        new_group = st.text_input("元件群組名稱", "New Group", key="new_comp_group")
        new_endpoint = st.text_input("電源端點名稱", "New Endpoint", key="new_comp_endpoint")
        power_sources_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source']
        power_source_options = {n['id']: n['label'] for n in power_sources_nodes}
        selected_ps_id = st.selectbox("連接到哪個電源？", options=power_source_options.keys(), format_func=lambda x: power_source_options.get(x, "N/A"), key="new_comp_source")
        
        widget_key_new = "new_comp_current_input"
        if widget_key_new not in st.session_state:
            st.session_state[widget_key_new] = 1.0

        source_label_new = power_source_options.get(selected_ps_id, 'N/A')
        st.number_input(
            f"'Default' 模式電流 (mA) ({source_label_new})", 
            min_value=0.0, 
            key=widget_key_new,
            format="%.3f"
        )
        new_current = st.session_state[widget_key_new] # 讀取電流

        if st.button("確認新增元件"):
            new_id = f"node_{st.session_state.max_id + 1}"
            new_node_data = {"id": new_id, "type": "component"}
            # 【已修改】power_consumption 欄位不再重要，設為 0
            new_node_data.update({"group": new_group, "endpoint": new_endpoint, "power_consumption": 0.0, "input_source_id": selected_ps_id})
            
            if new_group not in st.session_state.operating_modes:
                st.session_state.operating_modes[new_group] = {"Default": {"currents_mA": {}, "note": "Default operating mode."}}
                if 'component_group_notes' not in st.session_state:
                     st.session_state.component_group_notes = {}
                st.session_state.component_group_notes[new_group] = ""

            # 【已修改】儲存「電流」到 currents_mA
            st.session_state.operating_modes[new_group]["Default"]["currents_mA"][new_id] = new_current
            
            if new_group not in st.session_state.group_colors:
                st.session_state.group_colors[new_group] = next(DEFAULT_COLORS)
            for dm in st.session_state.device_modes.values():
                if new_group not in dm["components"]:
                    dm["components"][new_group] = "Default"
            
            if widget_key_new in st.session_state:
                st.session_state[widget_key_new] = 1.0

            st.session_state.power_tree_data['nodes'].append(new_node_data)
            st.session_state.max_id += 1
            st.success(f"已新增元件: {new_group} - {new_endpoint}")
            st.rerun()

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
                
                source_label = "N/A"
                if selected_ps_id_edit:
                    source_node = get_node_by_id(selected_ps_id_edit)
                    if source_node:
                        source_label = source_node.get('label', selected_ps_id_edit)
                
                widget_key_edit = f"edit_current_{selected_node_id}"
                
                # 【已修改】讀取 'Default' 模式的「電流」
                if widget_key_edit in st.session_state:
                    current_val_for_widget = st.session_state[widget_key_edit]
                else:
                    current_val_for_widget = st.session_state.operating_modes.get(original_group, {}).get("Default", {}).get("currents_mA", {}).get(selected_node_id, 0.0)
                
                new_label_text = f"'Default' 模式電流 (mA) ({source_label})"
                st.number_input(
                    new_label_text,
                    min_value=0.0,
                    value=current_val_for_widget,
                    key=widget_key_edit,
                    format="%.3f"
                )
                edited_default_current = st.session_state[widget_key_edit]

                if st.button("更新元件", key=f"update_comp_{selected_node_id}"):
                    node_to_edit['endpoint'] = edited_endpoint
                    node_to_edit['input_source_id'] = selected_ps_id_edit
                    # 【已修改】儲存「電流」
                    st.session_state.operating_modes[original_group]["Default"]["currents_mA"][selected_node_id] = edited_default_current 

                    if original_group != edited_group:
                        if edited_group not in st.session_state.operating_modes:
                            st.session_state.operating_modes[edited_group] = {"Default": {"currents_mA": {}, "note": "Default operating mode."}}
                            st.session_state.group_colors[edited_group] = next(DEFAULT_COLORS)
                        
                        #【已修改】移動「電流」
                        current_val = st.session_state.operating_modes[original_group]["Default"]["currents_mA"].pop(selected_node_id)
                        st.session_state.operating_modes[edited_group]["Default"]["currents_mA"][selected_node_id] = current_val
                        
                        for dm in st.session_state.device_modes.values():
                            if original_group in dm["components"]:
                                dm["components"][edited_group] = dm["components"].pop(original_group)
                        node_to_edit['group'] = edited_group
                    
                    if widget_key_edit in st.session_state:
                        del st.session_state[widget_key_edit]
                    st.success("已更新元件")
                    st.rerun()
        else:
            st.info("沒有可編輯的元件。")

    with st.expander("🎨 Group Color Management"):
        all_groups_for_color = sorted(list(set(n['group'] for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component')))
        for group in all_groups_for_color:
            st.session_state.group_colors[group] = st.color_picker(
                f"'{group}' 群組顏色", st.session_state.group_colors.get(group, '#CCCCCC'), key=f"color_{group}"
            )


with tabs[2]:
    st.header("Power Source Mode Management")
    all_power_sources = sorted([n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source'], key=lambda x: x['label'])
    
    if not all_power_sources:
        st.info("請先新增電源區塊。")
    else:
        ps_options = {ps['id']: ps['label'] for ps in all_power_sources}
        selected_ps_id = st.selectbox("選擇要管理的電源", options=ps_options.keys(), format_func=ps_options.get, key="psm_ps_selector")
        
        base_node = get_node_by_id(selected_ps_id)
        if base_node: 
            current_note = base_node.get("note", "")
            new_note = st.text_area(
                f"Base Note for '{base_node['label']}'", 
                value=current_note,
                key=f"base_note_ps_{selected_ps_id}"
            )
            base_node["note"] = new_note
            
        st.subheader(f"Edit Modes for '{ps_options[selected_ps_id]}'")
        
        for mode_name, params in list(st.session_state.power_source_modes.get(selected_ps_id, {}).items()):
            if 'note' not in params: params['note'] = ""
            
            with st.expander(f"{mode_name}", expanded=False):
                
                key_v = f"psm_v_{selected_ps_id}_{mode_name}"
                key_eff = f"psm_eff_{selected_ps_id}_{mode_name}"
                key_iq = f"psm_iq_{selected_ps_id}_{mode_name}"
                key_note = f"psm_note_{selected_ps_id}_{mode_name}"

                if is_off_mode := params.get('output_voltage') == 0 and params.get('efficiency') == 0:
                    
                    # --- 【START：修正點】 ---
                    # 為這兩個 disabled text_input 加上唯一的 key
                    st.text_input("Output Voltage (V)", value="0.0 (Off)", disabled=True, key=key_v)
                    st.text_input("Efficiency (%)", value="N/A", disabled=True, key=key_eff)
                    # --- 【END：修正點】 ---
                    
                    if key_iq not in st.session_state:
                        st.session_state[key_iq] = params['quiescent_current_mA']
                    st.number_input("Quiescent Current (mA)", min_value=0.0, key=key_iq, format="%.3f")
                    params['quiescent_current_mA'] = st.session_state[key_iq]

                else:
                    if key_v not in st.session_state:
                        st.session_state[key_v] = params['output_voltage']
                    st.number_input("Output Voltage (V)", key=key_v) 
                    
                    if key_eff not in st.session_state:
                        st.session_state[key_eff] = params['efficiency'] * 100.0
                    st.number_input("Efficiency (%)", min_value=0.0, max_value=100.0, key=key_eff)

                    if key_iq not in st.session_state:
                        st.session_state[key_iq] = params['quiescent_current_mA']
                    st.number_input("Quiescent Current (mA)", min_value=0.0, key=key_iq, format="%.3f")

                    params['output_voltage'] = st.session_state[key_v]
                    params['efficiency'] = st.session_state[key_eff] / 100.0
                    params['quiescent_current_mA'] = st.session_state[key_iq]
                
                if key_note not in st.session_state:
                    st.session_state[key_note] = params.get("note", "")
                st.text_area("Mode Note", key=key_note)
                params['note'] = st.session_state[key_note]
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Rename Mode", value=mode_name, key=f"rename_ps_{selected_ps_id}_{mode_name}", label_visibility="collapsed")
                with col2:
                    if st.button("Rename", key=f"rename_ps_btn_{selected_ps_id}_{mode_name}"):
                        if new_name and new_name != mode_name and new_name not in st.session_state.power_source_modes[selected_ps_id]:
                            st.session_state.power_source_modes[selected_ps_id][new_name] = st.session_state.power_source_modes[selected_ps_id].pop(mode_name)
                            for dm in st.session_state.device_modes.values():
                                if dm.get("power_sources", {}).get(selected_ps_id) == mode_name:
                                    dm["power_sources"][selected_ps_id] = new_name
                            
                            old_keys = [f"psm_v_{selected_ps_id}_{mode_name}", f"psm_eff_{selected_ps_id}_{mode_name}", f"psm_iq_{selected_ps_id}_{mode_name}", f"psm_note_{selected_ps_id}_{mode_name}"]
                            for k in old_keys:
                                if k in st.session_state: del st.session_state[k]
                            st.rerun()

                if len(st.session_state.power_source_modes[selected_ps_id]) > 1 and mode_name not in ["On", "Off"]:
                    with st.expander(f"🗑️ 刪除模式 '{mode_name}'"):
                        st.warning(f"此操作將永久刪除 '{mode_name}' 模式，無法復原。")
                        if st.button(f"確認永久刪除 '{mode_name}'", key=f"del_psm_confirm_{selected_ps_id}_{mode_name}", type="primary"):
                            fallback_mode = "On" if "On" in st.session_state.power_source_modes[selected_ps_id] else list(st.session_state.power_source_modes[selected_ps_id].keys())[0]
                            for dm in st.session_state.device_modes.values():
                                if dm.get("power_sources", {}).get(selected_ps_id) == mode_name:
                                    dm["power_sources"][selected_ps_id] = fallback_mode
                            del st.session_state.power_source_modes[selected_ps_id][mode_name]
                            
                            old_keys = [f"psm_v_{selected_ps_id}_{mode_name}", f"psm_eff_{selected_ps_id}_{mode_name}", f"psm_iq_{selected_ps_id}_{mode_name}", f"psm_note_{selected_ps_id}_{mode_name}"]
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
                        "quiescent_current_mA": 0.0,
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
        new_label = st.text_input("新電源名稱", "New Power Source", key="new_ps_label")
        ps_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source']
        ps_options = {n['id']: n['label'] for n in ps_nodes}
        ps_options_with_none = {"": "無 (設為根節點)", **ps_options}
        new_input_source_id = st.selectbox("連接到哪個上游電源？", options=ps_options_with_none.keys(), format_func=lambda x: ps_options_with_none.get(x, "N/A"), key="new_ps_source")
        new_efficiency_percent = st.number_input("'On' 模式效率 (%)", 0.0, 100.0, 90.0, step=1.0, key="new_ps_eff")
        new_output_voltage = st.number_input("'On' 模式輸出電壓 (V)", min_value=0.0, value=1.8, key="new_ps_volt")
        new_quiescent_current = st.number_input("靜態電流 (mA)", min_value=0.0, value=0.01, format="%.3f", key="new_ps_iq")
        
        if st.button("確認新增電源"):
            new_id = f"node_{st.session_state.max_id + 1}"
            new_node_data = {"id": new_id, "type": "power_source"}
            new_node_data.update({
                "label": new_label, "efficiency": new_efficiency_percent / 100.0, "output_voltage": new_output_voltage,
                "quiescent_current_mA": new_quiescent_current, "input_source_id": new_input_source_id if new_input_source_id else None
            })
            base_note = new_node_data.get("note", "")
            st.session_state.power_source_modes[new_id] = {
                "On": {"output_voltage": new_output_voltage, "efficiency": new_efficiency_percent / 100.0, "quiescent_current_mA": new_quiescent_current, "note": base_note},
                "Off": {"output_voltage": 0.0, "efficiency": 0.0, "quiescent_current_mA": new_quiescent_current, "note": "Device is off"}
            }
            for dm in st.session_state.device_modes.values():
                if new_id not in dm["power_sources"]:
                    dm["power_sources"][new_id] = "On"
            
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
                edited_label = st.text_input("名稱", node_to_edit['label'], key=f"edit_label_{selected_node_id}")
                upstream_ps = [n for n in nodes_list if n['type'] == 'power_source' and n['id'] != selected_node_id]
                ups_options = {n['id']: n['label'] for n in upstream_ps}
                ups_options_with_none = {"": "無 (設為根節點)", **ups_options}
                current_ups_id = node_to_edit.get('input_source_id') or ""
                ups_ids = list(ups_options_with_none.keys())
                default_index = ups_ids.index(current_ups_id) if current_ups_id in ups_ids else 0
                selected_ups_id_edit = st.selectbox("連接到哪個上游電源？", options=ups_ids, format_func=ups_options_with_none.get, index=default_index, key=f"edit_ps_source_{selected_node_id}")

                on_mode_params = st.session_state.power_source_modes.get(selected_node_id, {}).get("On", {})
                edited_efficiency_percent = st.number_input("'On' 模式效率 (%)", 0.0, 100.0, float(on_mode_params.get('efficiency', 0)) * 100, step=1.0, key=f"edit_eff_{selected_node_id}")
                edited_output_voltage = st.number_input("'On' 模式輸出電壓 (V)", 0.0, value=float(on_mode_params.get('output_voltage', 0)), key=f"edit_volt_{selected_node_id}")
                edited_quiescent_current = st.number_input("靜態電流 (mA)", min_value=0.0, value=float(on_mode_params.get('quiescent_current_mA', 0)), format="%.3f", key=f"edit_iq_{selected_node_id}")

                if st.button("更新電源", key=f"update_ps_{selected_node_id}"):
                    node_to_edit['label'] = edited_label
                    node_to_edit['input_source_id'] = selected_ups_id_edit if selected_ups_id_edit else None
                    
                    existing_on_note = st.session_state.power_source_modes.get(selected_node_id, {}).get("On", {}).get("note", "")
                    st.session_state.power_source_modes[selected_node_id]["On"] = {
                        "output_voltage": edited_output_voltage,
                        "efficiency": edited_efficiency_percent / 100.0,
                        "quiescent_current_mA": edited_quiescent_current,
                        "note": existing_on_note
                    }
                    
                    if "Off" in st.session_state.power_source_modes[selected_node_id]:
                        st.session_state.power_source_modes[selected_node_id]["Off"]["quiescent_current_mA"] = edited_quiescent_current
                    
                    st.success("已更新電源")
                    st.rerun()
        else:
            st.info("沒有可編輯的電源。")

# --- 【tabs[3]】 ---
with tabs[3]:
    st.header("Device Mode Management")
    
    st.subheader("Edit Device Modes")
    num_device_modes = len(st.session_state.device_modes)
    for dm_name, dm_settings in list(st.session_state.device_modes.items()):
        with st.expander(f"Device Mode: {dm_name}", expanded=False):
            
            st.markdown("#### Component Settings")
            all_comp_groups = sorted(list(st.session_state.operating_modes.keys()))
            
            for group in all_comp_groups:
                st.markdown(f"**{group}**")
                
                # --- 【已移除】 (Depends on: ...) 提示訊息 ---

                group_modes = list(st.session_state.operating_modes.get(group, {}).keys())
                
                if not group_modes:
                    st.warning(f"'{group}' 尚未在 tabs[1] 中定義任何 Component Mode。")
                    continue

                current_selected_mode = dm_settings.get("components", {}).get(group)

                try:
                    current_index = group_modes.index(current_selected_mode)
                except ValueError:
                    current_index = 0
                
                selected_mode = st.selectbox(
                    f"Select Component Mode for '{group}'",
                    options=group_modes,
                    index=current_index,
                    key=f"dm_comp_select_{dm_name}_{group}",
                    label_visibility="collapsed"
                )
                
                dm_settings["components"][group] = selected_mode

            st.markdown("---")
            st.markdown("#### Power Source Settings")
            all_ps_nodes = sorted([n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source'], key=lambda x: x['label'])
            for ps_node in all_ps_nodes:
                ps_modes = list(st.session_state.power_source_modes.get(ps_node['id'], {}).keys())
                current_ps_mode = dm_settings.get("power_sources", {}).get(ps_node['id'], "On")
                idx = ps_modes.index(current_ps_mode) if current_ps_mode in ps_modes else 0
                
                selected_ps_mode = st.selectbox(
                    f"Mode for '{ps_node['label']}'", options=ps_modes, index=idx, key=f"dm_ps_select_{dm_name}_{ps_node['id']}"
                )
                dm_settings["power_sources"][ps_node['id']] = selected_ps_mode
            
            if num_device_modes > 1:
                with st.expander(f"🗑️ 刪除設備模式 '{dm_name}'"):
                    st.warning(f"此操作將永久刪除 '{dm_name}' 設備模式，無法復原。")
                    if st.button(f"確認永久刪除 '{dm_name}'", key=f"del_dm_confirm_{dm_name}", type="primary"):
                        mode_to_delete = dm_name
                        
                        if st.session_state.active_device_mode == mode_to_delete:
                            del st.session_state.device_modes[mode_to_delete]
                            st.session_state.active_device_mode = list(st.session_state.device_modes.keys())[0]
                        else:
                            del st.session_state.device_modes[mode_to_delete]

                        for profile in st.session_state.user_profiles.values():
                            if mode_to_delete in profile:
                                del profile[mode_to_delete]
                        st.rerun()

    with st.expander("➕ Add New Device Mode", expanded=False):
        new_dm_name = st.text_input("New Device Mode Name", key="new_dm_name")
        if st.button("Add Device Mode", key="add_dm_btn", type="secondary"):
            if new_dm_name and new_dm_name not in st.session_state.device_modes:
                all_comp_groups = set(n['group'] for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'component')
                all_ps_nodes = [n for n in st.session_state.power_tree_data['nodes'] if n['type'] == 'power_source']
                
                st.session_state.device_modes[new_dm_name] = {
                    "components": {group: list(st.session_state.operating_modes.get(group, {}).keys())[0] for group in all_comp_groups if st.session_state.operating_modes.get(group)},
                    "power_sources": {ps['id']: "On" for ps in all_ps_nodes}
                }
                for profile in st.session_state.user_profiles.values():
                    profile[new_dm_name] = 0
                st.rerun()
            elif not new_dm_name:
                st.error("設備模式名稱不可為空。")
            else:
                st.error(f"設備模式 '{new_dm_name}' 已存在。")

# --- 【tabs[4]】(保持不變) ---
with tabs[4]:
    st.header("Battery Life Estimation")

    st.number_input("Battery Capacity (mAh)", min_value=0.0, value=st.session_state.battery_capacity_mAh, key="battery_capacity_input")
    st.session_state.battery_capacity_mAh = st.session_state.battery_capacity_input

    st.markdown("---")
    st.subheader("Estimation Results per Profile")

    power_per_mode = {dm: calculate_power(mode_name_override=dm) for dm in st.session_state.device_modes}
    vsys_node = get_node_by_id("battery")
    vsys_voltage = vsys_node['output_voltage'] if vsys_node else 3.85

    for profile_name, profile_data in list(st.session_state.user_profiles.items()):
        
        total_energy_mWh = sum(power_per_mode.get(dm, 0) * profile_data.get(dm, 0) for dm in profile_data)
        total_hours_in_profile = sum(profile_data.values())
        avg_power_mW = total_energy_mWh / 24 if total_hours_in_profile > 0 else 0
        avg_current_mA = avg_power_mW / vsys_voltage if vsys_voltage > 0 else 0
        
        if avg_current_mA > 0:
            battery_life_hours = st.session_state.battery_capacity_mAh / avg_current_mA
            battery_life_days = battery_life_hours / 24
            life_display_str = f"{battery_life_days:.2f} Days"
        else:
            life_display_str = "Infinite"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label=f"**{profile_name}**", value=life_display_str)
        with col2:
            st.metric(label="Avg. Power", value=f"{avg_power_mW:.2f} mW")
        with col3:
            st.metric(label="Avg. Current", value=f"{avg_current_mA:.2f} mA")
            
        with st.expander(f"編輯 '{profile_name}' 設定檔", expanded=False):
            
            for dm_name in st.session_state.device_modes:
                if dm_name not in profile_data: profile_data[dm_name] = 0
            for dm_name in list(profile_data.keys()):
                if dm_name not in st.session_state.device_modes: del profile_data[dm_name]

            total_hours = 0
            for dm_name in st.session_state.device_modes:
                hours = st.slider(
                    f"Hours in '{dm_name}'", 0, 24, 
                    value=profile_data.get(dm_name, 0), 
                    key=f"profile_{profile_name}_{dm_name}"
                )
                profile_data[dm_name] = hours
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
                st.session_state.user_profiles[profile_name] = {dm: 0 for dm in st.session_state.device_modes}
                st.rerun()
            elif not profile_name:
                st.error("設定檔名稱不可為空。")
            else:
                st.error(f"設定檔 '{profile_name}' 已存在。")


# ---
# 在所有狀態更新後，執行最終的計算與渲染
# ---
total_power = calculate_power(st.session_state.active_device_mode)

# --- 【已修改】 改用 HTML <strong> 標籤強制粗體 ---
power_placeholder.write(f"<strong>Total System Power:</strong> {total_power:.2f} mW", unsafe_allow_html=True)
vsys_node = get_node_by_id("battery")
if vsys_node and vsys_node.get('output_voltage', 0) > 0:
    current = total_power / vsys_node['output_voltage']
    # --- 【已修改】 改用 HTML <strong> 標籤強制粗體 ---
    current_placeholder.write(f"<strong>Total Vsys Current:</strong> {current:.2f} mA", unsafe_allow_html=True)

# 繪製 Power Tree (此區塊保持不變)
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
    iq_str = f"Iq: {node.get('quiescent_current_mA', 0.0):.2f}mA"
    
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
            current = power / voltage if voltage > 0 else 0
            edge_label = f"{voltage:.2f} V\n{current:.2f} mA"
            dot.edge(node['input_source_id'], node['id'], label=edge_label, tailport='e', headport='w')

graph_placeholder.graphviz_chart(dot)
