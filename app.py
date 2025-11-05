import streamlit as st
import random
import time
from typing import List, Tuple, Optional, Dict
from datetime import datetime

# 初始化游戏状态
def init_game_state():
    """初始化游戏状态"""
    if 'game_state' not in st.session_state:
        st.session_state.game_state = {
            'player_hp': 100,
            'player_shield': 0,
            'current_enemy': 0,
            'selected_cards': [],
            'flipped_cards': [],  # 使用list确保兼容性
            'removed_cards': [],  # 使用list确保兼容性
            'deck': [],
            'enemy_turn': False,
            'game_over': False,
            'game_won': False,
            'revealed_cards': [],  # 方片效果揭示的卡牌
            'blocked_columns': [],  # 敌人3禁止的列
            'can_continue_turn': False,  # 是否因为匹配成功可以继续
            'waiting_for_action': False,  # 是否等待玩家操作（匹配失败时）
            'pending_new_card': False,  # 是否有待处理的新卡牌（敌人回合后处理）
            'matched_pairs': [],  # 匹配成功但还未替换的牌对 [idx1, idx2]
            'draw_deck': [],  # 抽取牌堆（用于补充空缺）
            'paired_cards': [],  # 已配对的牌（用于重新混洗）
        }

def create_deck() -> List[Dict]:
    """创建20张牌的牌组（4*5）"""
    # 需要10对牌，每对2张相同点数但不同花色
    suits = ['♠', '♥', '♣', '♦']  # 黑桃、红心、梅花、方片
    deck = []
    
    # 创建10对牌（点数1-10）
    for value in range(1, 11):
        # 每对牌选择2个不同的花色
        pair_suits = random.sample(suits, 2)
        for suit in pair_suits:
            deck.append({
                'value': value,
                'suit': suit,
                'id': f"{suit}{value}"
            })
    
    random.shuffle(deck)
    return deck

def draw_new_card(game_state: Dict) -> Optional[Dict]:
    """从抽取牌堆抽取一张新牌，如果牌堆为空则重新混洗已配对的牌"""
    # 如果抽取牌堆为空，重新混洗已配对的牌
    if not game_state['draw_deck']:
        if game_state['paired_cards']:
            # 重新混洗已配对的牌
            game_state['draw_deck'] = game_state['paired_cards'].copy()
            random.shuffle(game_state['draw_deck'])
            game_state['paired_cards'] = []
        else:
            # 如果也没有已配对的牌，返回None（不应该发生）
            return None
    
    # 从抽取牌堆抽取一张牌
    if game_state['draw_deck']:
        return game_state['draw_deck'].pop(0)
    return None

def replace_paired_cards(game_state: Dict, card_idx1: int, card_idx2: int):
    """替换配对成功的牌，从牌堆抽取新牌补上空缺"""
    # 获取配对的牌
    card1 = game_state['deck'][card_idx1]
    card2 = game_state['deck'][card_idx2]
    
    # 将配对的牌移到已配对存储
    game_state['paired_cards'].append(card1)
    game_state['paired_cards'].append(card2)
    
    # 从抽取牌堆抽取新牌补上空缺
    new_card1 = draw_new_card(game_state)
    new_card2 = draw_new_card(game_state)
    
    # 确保新牌存在，如果不存在则创建新牌
    if new_card1:
        game_state['deck'][card_idx1] = new_card1
    else:
        # 如果没有新牌，从已配对牌中重新混洗后抽取
        if game_state['paired_cards']:
            game_state['draw_deck'] = game_state['paired_cards'].copy()
            random.shuffle(game_state['draw_deck'])
            game_state['paired_cards'] = []
            new_card1 = draw_new_card(game_state)
            if new_card1:
                game_state['deck'][card_idx1] = new_card1
            else:
                # 如果还是没有，创建一张新牌
                suits = ['♠', '♥', '♣', '♦']
                suit = random.choice(suits)
                value = random.randint(1, 10)
                game_state['deck'][card_idx1] = {
                    'value': value,
                    'suit': suit,
                    'id': f"{suit}{value}"
                }
    
    if new_card2:
        game_state['deck'][card_idx2] = new_card2
    else:
        # 如果没有新牌，从已配对牌中重新混洗后抽取
        if game_state['paired_cards']:
            game_state['draw_deck'] = game_state['paired_cards'].copy()
            random.shuffle(game_state['draw_deck'])
            game_state['paired_cards'] = []
            new_card2 = draw_new_card(game_state)
            if new_card2:
                game_state['deck'][card_idx2] = new_card2
            else:
                # 如果还是没有，创建一张新牌
                suits = ['♠', '♥', '♣', '♦']
                suit = random.choice(suits)
                value = random.randint(1, 10)
                game_state['deck'][card_idx2] = {
                    'value': value,
                    'suit': suit,
                    'id': f"{suit}{value}"
                }

def get_card_color(suit: str) -> str:
    """根据花色返回颜色"""
    if suit == '♥' or suit == '♦':
        return 'red'
    return 'black'

def get_enemy_info(enemy_num: int) -> Dict:
    """获取敌人信息"""
    enemies = [
        {'hp': 20, 'name': '敌人1', 'desc': '每回合造成10伤害'},
        {'hp': 40, 'name': '敌人2', 'desc': '每回合获得5护甲，造成10伤害'},
        {'hp': 60, 'name': '敌人3', 'desc': '每回合禁止一列卡牌，造成10伤害'},
    ]
    return enemies[enemy_num]

def apply_card_effect(suit: str, value: int, game_state: Dict):
    """应用卡牌效果"""
    if suit == '♠':  # 黑桃：获得护盾
        game_state['player_shield'] += value
        return f"获得 {value} 点护盾！"
    
    elif suit == '♥':  # 红心：回复生命
        old_hp = game_state['player_hp']
        game_state['player_hp'] = min(100, game_state['player_hp'] + value)
        healed = game_state['player_hp'] - old_hp
        return f"回复 {healed} 点生命！"
    
    elif suit == '♣':  # 梅花：造成伤害
        # 对当前敌人造成伤害
        enemy_num = game_state['current_enemy']
        if enemy_num < 3:
            enemy_key = f'enemy_{enemy_num}_hp'
            if enemy_key not in st.session_state:
                enemy_info = get_enemy_info(enemy_num)
                st.session_state[enemy_key] = enemy_info['hp']
            
            # 敌人2有护甲，先扣除护甲再扣生命
            if enemy_num == 1:
                enemy_shield_key = f'enemy_{enemy_num}_shield'
                enemy_shield = st.session_state.get(enemy_shield_key, 0)
                if enemy_shield > 0:
                    shield_damage = min(enemy_shield, value)
                    st.session_state[enemy_shield_key] = max(0, enemy_shield - shield_damage)
                    value -= shield_damage
                    if value <= 0:
                        return f"对敌人造成伤害，但被护甲完全抵挡！"
            
            actual_damage = min(value, st.session_state[enemy_key])
            st.session_state[enemy_key] = max(0, st.session_state[enemy_key] - value)
            return f"对敌人造成 {actual_damage} 点伤害！"
        return f"造成 {value} 点伤害！"
    
    elif suit == '♦':  # 方片：揭示一个相同点数的牌
        # 找到所有相同点数但未翻开的牌
        deck = game_state['deck']
        revealed = []
        for i, card in enumerate(deck):
            if card['value'] == value and i not in game_state['flipped_cards'] and i not in game_state['removed_cards']:
                revealed.append(i)
        
        if revealed:
            # 随机揭示一张
            reveal_idx = random.choice(revealed)
            if reveal_idx not in game_state['revealed_cards']:
                game_state['revealed_cards'].append(reveal_idx)
            return f"揭示了位置 {reveal_idx // 5 + 1} 行 {reveal_idx % 5 + 1} 列的一张 {value} 点牌！"
        return f"没有找到可揭示的 {value} 点牌"

def enemy_turn(game_state: Dict):
    """敌人回合"""
    enemy_num = game_state['current_enemy']
    enemy_key = f'enemy_{enemy_num}_hp'
    
    if enemy_key not in st.session_state:
        enemy_info = get_enemy_info(enemy_num)
        st.session_state[enemy_key] = enemy_info['hp']
    
    # 检查敌人是否已死亡
    if st.session_state[enemy_key] <= 0:
        game_state['current_enemy'] += 1
        if game_state['current_enemy'] >= 3:
            game_state['game_won'] = True
            game_state['game_over'] = True
        else:
            # 重置卡牌状态，准备下一场战斗
            game_state['deck'] = create_deck()
            # 重新初始化抽取牌堆
            extra_deck = create_deck()
            game_state['draw_deck'] = extra_deck
            game_state['paired_cards'] = []
            game_state['flipped_cards'] = []
            game_state['removed_cards'] = []
            game_state['selected_cards'] = []
            game_state['revealed_cards'] = []
            game_state['blocked_columns'] = []
        return
    
    # 敌人行动
    if enemy_num == 0:
        # 敌人1：造成10伤害
        damage = 10
        if game_state['player_shield'] > 0:
            shield_damage = min(game_state['player_shield'], damage)
            game_state['player_shield'] -= shield_damage
            damage -= shield_damage
        game_state['player_hp'] -= damage
        if game_state['player_hp'] <= 0:
            game_state['game_over'] = True
    
    elif enemy_num == 1:
        # 敌人2：获得5护甲，造成10伤害
        st.session_state[f'enemy_{enemy_num}_shield'] = st.session_state.get(f'enemy_{enemy_num}_shield', 0) + 5
        damage = 10
        if game_state['player_shield'] > 0:
            shield_damage = min(game_state['player_shield'], damage)
            game_state['player_shield'] -= shield_damage
            damage -= shield_damage
        game_state['player_hp'] -= damage
        if game_state['player_hp'] <= 0:
            game_state['game_over'] = True
    
    elif enemy_num == 2:
        # 敌人3：禁止一列，造成10伤害
        available_columns = [col for col in range(5) if col not in game_state['blocked_columns']]
        if available_columns:
            blocked_col = random.choice(available_columns)
            if blocked_col not in game_state['blocked_columns']:
                game_state['blocked_columns'].append(blocked_col)
        
        damage = 10
        if game_state['player_shield'] > 0:
            shield_damage = min(game_state['player_shield'], damage)
            game_state['player_shield'] -= shield_damage
            damage -= shield_damage
        game_state['player_hp'] -= damage
        if game_state['player_hp'] <= 0:
            game_state['game_over'] = True
    
    game_state['enemy_turn'] = False
    # 如果有待处理的新卡牌，不清空selected_cards，保留它作为新一组的第一张
    if not game_state.get('pending_new_card', False):
        game_state['selected_cards'] = []
    game_state['pending_new_card'] = False

def handle_card_click(card_idx: int, game_state: Dict):
    """处理卡牌点击"""
    if game_state['game_over']:
        return
    
    # 如果有匹配成功的牌对还未替换，点击新卡牌时替换它们
    if game_state.get('matched_pairs') and len(game_state['matched_pairs']) == 2:
        matched_idx1, matched_idx2 = game_state['matched_pairs']
        # 如果点击的是匹配成功的牌之一，允许将其作为新一组的第一张
        if card_idx == matched_idx1 or card_idx == matched_idx2:
            # 先替换掉另一张匹配成功的牌
            other_idx = matched_idx2 if card_idx == matched_idx1 else matched_idx1
            replace_paired_cards(game_state, matched_idx1, matched_idx2)
            
            # 移除翻转状态，让新牌显示为背面
            if matched_idx1 in game_state['flipped_cards']:
                game_state['flipped_cards'].remove(matched_idx1)
            if matched_idx2 in game_state['flipped_cards']:
                game_state['flipped_cards'].remove(matched_idx2)
            # 移除揭示状态
            if matched_idx1 in game_state['revealed_cards']:
                game_state['revealed_cards'].remove(matched_idx1)
            if matched_idx2 in game_state['revealed_cards']:
                game_state['revealed_cards'].remove(matched_idx2)
            
            # 清空匹配成功的牌对标记
            game_state['matched_pairs'] = []
            # 清除匹配成功的消息
            game_state['can_continue_turn'] = False
            if 'last_effect' in st.session_state:
                del st.session_state['last_effect']
            
            # 继续处理当前点击的卡牌（作为新一组的第一张）
            # 不返回，继续执行下面的逻辑
        else:
            # 点击了新卡牌，替换匹配成功的牌
            replace_paired_cards(game_state, matched_idx1, matched_idx2)
            
            # 移除翻转状态，让新牌显示为背面
            if matched_idx1 in game_state['flipped_cards']:
                game_state['flipped_cards'].remove(matched_idx1)
            if matched_idx2 in game_state['flipped_cards']:
                game_state['flipped_cards'].remove(matched_idx2)
            # 移除揭示状态
            if matched_idx1 in game_state['revealed_cards']:
                game_state['revealed_cards'].remove(matched_idx1)
            if matched_idx2 in game_state['revealed_cards']:
                game_state['revealed_cards'].remove(matched_idx2)
            
            # 清空匹配成功的牌对标记
            game_state['matched_pairs'] = []
            # 清除匹配成功的消息
            game_state['can_continue_turn'] = False
            if 'last_effect' in st.session_state:
                del st.session_state['last_effect']
            
            # 继续处理新点击的卡牌
            # 不返回，继续执行下面的逻辑
    
    # 如果正在等待操作（匹配失败），点击新卡牌时翻回上一组牌
    if game_state['waiting_for_action']:
        # 翻回上一组匹配失败的牌
        if len(game_state['selected_cards']) == 2:
            prev_idx1, prev_idx2 = game_state['selected_cards']
            if prev_idx1 in game_state['flipped_cards']:
                game_state['flipped_cards'].remove(prev_idx1)
            if prev_idx2 in game_state['flipped_cards']:
                game_state['flipped_cards'].remove(prev_idx2)
            game_state['selected_cards'] = []
            game_state['enemy_turn'] = True
            game_state['waiting_for_action'] = False
            # 清除匹配成功的消息（如果有）
            game_state['can_continue_turn'] = False
            if 'last_effect' in st.session_state:
                del st.session_state['last_effect']
            # 执行敌人回合（但不在当前函数中执行，让主循环处理）
            # 清空后，将新点击的卡牌作为新一组的第一张
            # 先加入选中列表，然后让敌人回合处理，敌人回合后会保留它
            game_state['selected_cards'].append(card_idx)
            if card_idx not in game_state['flipped_cards']:
                game_state['flipped_cards'].append(card_idx)
            # 设置标记，表示这是新一组的第一张
            game_state['pending_new_card'] = True
            return  # 让主循环处理敌人回合，敌人回合后会保留selected_cards中的卡牌a
        else:
            # 如果还没有选中上一组牌，清空等待状态
            game_state['waiting_for_action'] = False
    
    # 敌人回合时不能点击卡牌
    if game_state['enemy_turn']:
        return
    
    # 检查是否被禁止
    if game_state['current_enemy'] == 2:
        col = card_idx % 5
        if col in game_state['blocked_columns']:
            return
    
    # 检查卡牌是否已被移除（这个检查现在可能不需要了，但保留作为保险）
    # if card_idx in game_state['removed_cards']:
    #     return
    
    # 如果已经选中，不允许取消选中（翻开的牌不能主动翻回去）
    # 注释掉原来的逻辑，翻开的牌不能翻回去
    # if card_idx in game_state['selected_cards']:
    #     game_state['selected_cards'].remove(card_idx)
    #     if card_idx in game_state['flipped_cards']:
    #         game_state['flipped_cards'].remove(card_idx)
    #     return
    
    # 如果已经翻开了（但未选中），可能是上一组匹配失败的牌，或者是敌人回合后保留的第一张牌
    # 如果当前没有选中的牌，可以将这张已翻开的牌作为新一组的第一张
    # 如果已经有1张选中的牌，可以将这张已翻开的牌作为第二张
    if card_idx in game_state['flipped_cards'] and card_idx not in game_state['selected_cards']:
        if len(game_state['selected_cards']) == 0:
            # 将这张已翻开的牌作为新一组的第一张
            game_state['selected_cards'].append(card_idx)
            # 保持翻开状态
            return
        elif len(game_state['selected_cards']) == 1:
            # 如果已经有1张选中的牌，将这张已翻开的牌作为第二张
            game_state['selected_cards'].append(card_idx)
            # 继续执行匹配检查逻辑
            # 不返回，继续执行下面的匹配检查
        else:
            # 如果已经有2张选中的牌，不应该再选择
            return
    
    # 最多选择2张牌
    if len(game_state['selected_cards']) >= 2:
        return
    
    # 添加到选中列表并立即翻开（作为第一张或第二张）
    game_state['selected_cards'].append(card_idx)
    if card_idx not in game_state['flipped_cards']:
        game_state['flipped_cards'].append(card_idx)
    
    # 如果开始新的翻牌操作，清除之前的匹配成功消息
    if len(game_state['selected_cards']) == 1:
        game_state['can_continue_turn'] = False
        if 'last_effect' in st.session_state:
            del st.session_state['last_effect']
    
    # 如果选中了2张牌，立即检查是否匹配并执行效果
    # 注意：这里需要检查selected_cards的长度，因为可能已经有第一张牌（比如敌人回合后保留的）
    if len(game_state['selected_cards']) == 2:
        idx1, idx2 = game_state['selected_cards']
        card1 = game_state['deck'][idx1]
        card2 = game_state['deck'][idx2]
        
        if card1['value'] == card2['value']:
            # 匹配成功，立即执行效果
            effect1 = apply_card_effect(card1['suit'], card1['value'], game_state)
            effect2 = apply_card_effect(card2['suit'], card2['value'], game_state)
            
            st.session_state['last_effect'] = f"{effect1} {effect2}"
            
            # 匹配成功，保持这两张牌翻开，等待玩家点击下一张牌时才替换
            # 设置标记，表示有匹配成功的牌等待替换
            game_state['matched_pairs'] = [idx1, idx2]
            game_state['can_continue_turn'] = True
            game_state['waiting_for_action'] = False
            
            # 清空选中状态，但保持翻转状态，让匹配成功的牌继续显示
            game_state['selected_cards'] = []
            # 不清空翻转状态，保持这两张牌翻开
            
            # 注意：不需要调用 st.rerun()，Streamlit 会在回调执行后自动重新运行脚本
        else:
            # 匹配失败，保持翻开状态，等待玩家点击下一组牌时翻回去
            game_state['waiting_for_action'] = True
            # 不清空selected_cards，保持这两张牌的状态

def inject_css():
    """注入CSS样式，实现卡牌翻转动画和真实比例，包含移动端适配"""
    st.markdown("""
    <style>
    /* 移动端适配 - 整体页面 */
    @media (max-width: 768px) {
        /* 主容器 */
        .main .block-container {
            padding: 1rem 0.5rem;
            max-width: 100%;
        }
        
        /* 标题 */
        h1 {
            font-size: 1.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* 副标题 */
        h2, h3 {
            font-size: 1rem !important;
            margin-bottom: 0.3rem !important;
        }
        
        /* Metric 组件 */
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }
        
        /* 列间距 */
        [data-testid="column"] {
            padding: 0.25rem !important;
        }
        
        /* 卡牌网格 */
        .stButton {
            margin: 0.1rem !important;
        }
        
        /* 按钮字体 */
        .stButton > button {
            font-size: 14px !important;
            min-height: 60px !important;
            max-height: 100px !important;
            padding: 0.2rem !important;
        }
    }
    
    /* 卡牌容器 - 宽度是高度的2/3，即宽:高 = 2:3 */
    .card-container {
        aspect-ratio: 2 / 3;
        width: 100%;
        max-width: 150px;
        margin: 0 auto;
        perspective: 1000px;
    }
    
    /* 移动端卡牌容器 */
    @media (max-width: 768px) {
        .card-container {
            max-width: 100%;
        }
    }
    
    /* 卡牌翻转容器 */
    .card-flip {
        position: relative;
        width: 100%;
        height: 100%;
        transform-style: preserve-3d;
        transition: transform 0.5s;
    }
    
    /* 翻转动画 */
    .card-flip.flipped {
        transform: rotateY(180deg);
    }
    
    /* 卡牌正面和背面 */
    .card-face {
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        border: 2px solid #333;
        font-size: 24px;
        font-weight: bold;
    }
    
    .card-back {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .card-front {
        background: white;
        transform: rotateY(180deg);
        color: #333;
    }
    
    /* 选中的卡牌高亮 */
    .card-selected {
        box-shadow: 0 0 20px rgba(255, 0, 0, 0.8);
        border-color: red !important;
    }
    
    /* 禁止的卡牌 */
    .card-blocked {
        opacity: 0.5;
        cursor: not-allowed;
    }
    
    /* Streamlit按钮样式覆盖 - 确保所有按钮都是固定的卡牌尺寸 2:3 (宽度是高度的2/3) */
    .stButton > button {
        width: 100% !important;
        aspect-ratio: 2 / 3 !important;
        height: auto !important;
        min-height: 80px !important;
        max-height: 120px !important;
        max-width: 84px !important;
        min-width: 56px !important;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        border: 2px solid #ddd;
        padding: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
        white-space: normal;
        word-wrap: break-word;
        /* 确保固定尺寸 */
        flex-shrink: 0;
        flex-grow: 0;
    }
    
    /* 卡牌正面样式 - 白色背景（primary类型，包含文本内容） */
    .stButton > button[data-baseweb="button"][kind="primary"] {
        background: white !important;
        color: #333 !important;
        border-color: #ddd !important;
    }
    
    /* 卡牌背面样式 - 灰色背景（secondary类型，空内容或只有🚫） */
    .stButton > button[data-baseweb="button"][kind="secondary"] {
        background: #e0e0e0 !important;
        color: #666 !important;
        border-color: #bbb !important;
    }
    
    /* 卡牌选中高亮 - 红色边框（选中时使用secondary类型且包含文本） */
    /* 选中状态的卡牌：secondary类型 + 包含换行符（即有卡牌内容） */
    .stButton > button[data-baseweb="button"][kind="secondary"]:not(:disabled):not(:empty) {
        border: 2px solid #ff4444 !important;
        box-shadow: 0 0 10px rgba(255, 68, 68, 0.5) !important;
        background: #fff5f5 !important;
    }
    
    /* 空按钮（背面）保持灰色 - 优先级更高 */
    .stButton > button[data-baseweb="button"][kind="secondary"]:empty,
    .stButton > button[data-baseweb="button"][kind="secondary"]:not(:has(*)):not(:has-text) {
        background: #e0e0e0 !important;
        border-color: #bbb !important;
        color: #666 !important;
    }
    
    /* 被禁止的卡牌 */
    .stButton > button[data-baseweb="button"][kind="secondary"]:disabled {
        opacity: 0.5 !important;
    }
    
    /* 卡牌悬停效果 */
    .stButton > button:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* 移动端按钮样式 - 保持固定尺寸 */
    @media (max-width: 768px) {
        .stButton > button {
            min-height: 60px !important;
            max-height: 90px !important;
            max-width: 60px !important;
            font-size: 14px !important;
            border-radius: 6px !important;
            border: 1px solid #ddd !important;
        }
    }
    
    /* 扑克牌点数显示样式 - 左上角和右下角 */
    .stButton > button.card-front-btn::before {
        content: attr(data-suit);
        position: absolute;
        top: 4px;
        left: 6px;
        font-size: 14px;
        font-weight: bold;
        line-height: 1;
    }
    
    .stButton > button.card-front-btn::after {
        content: attr(data-suit);
        position: absolute;
        bottom: 4px;
        right: 6px;
        font-size: 14px;
        font-weight: bold;
        line-height: 1;
        transform: rotate(180deg);
    }
    
    /* 扑克牌中间花色显示 */
    .card-suit-large {
        font-size: 32px !important;
        line-height: 1;
    }
    
    /* 移动端整体布局优化 */
    @media (max-width: 768px) {
        /* 限制最大宽度，居中显示 */
        .main .block-container {
            max-width: 100% !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* 减少垂直间距 */
        .element-container {
            margin-bottom: 0.5rem !important;
        }
        
        /* 警告和提示信息 */
        [data-testid="stAlert"] {
            font-size: 0.85rem !important;
            padding: 0.5rem !important;
        }
        
        /* 分隔线 */
        hr {
            margin: 0.5rem 0 !important;
        }
    }
    
    /* 移除 Streamlit 自动生成的 flex 和 width 属性 */
    /* 注意：emotion-cache 类名是动态生成的，可能需要根据实际情况调整 */
    .st-emotion-cache-1cmetgi {
        flex: none !important;
        width: auto !important;
    }
    
    /* 如果需要更通用的覆盖，可以使用属性选择器 */
    [class*="st-emotion-cache"] {
        flex: none !important;
        width: auto !important;
    }
    
    /* 卡牌正面按钮 */
    .card-front-btn {
        background: white;
        color: #333;
    }
    
    /* 翻转动画类 */
    @keyframes flip {
        from {
            transform: rotateY(0deg);
        }
        to {
            transform: rotateY(180deg);
        }
    }
    
    .card-flipping {
        animation: flip 0.5s ease-in-out;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # 移动端适配：使用 "wide" 布局但在CSS中限制最大宽度
    st.set_page_config(
        page_title="记忆RPG", 
        layout="wide",
        initial_sidebar_state="collapsed"  # 移动端默认收起侧边栏
    )
    inject_css()
    st.title("🎮 记忆RPG游戏")
    
    init_game_state()
    game_state = st.session_state.game_state
    
    # 初始化牌组
    if not game_state['deck']:
        game_state['deck'] = create_deck()
        # 初始化抽取牌堆（额外创建一些牌作为备用）
        # 创建额外的牌用于补充（例如再创建10对牌）
        extra_deck = create_deck()  # 再创建20张牌作为备用
        game_state['draw_deck'] = extra_deck
        game_state['paired_cards'] = []
    
    # 初始化敌人生命值
    for i in range(3):
        enemy_key = f'enemy_{i}_hp'
        if enemy_key not in st.session_state:
            enemy_info = get_enemy_info(i)
            st.session_state[enemy_key] = enemy_info['hp']
    
    # 显示游戏状态 - 移动端使用响应式布局
    # 使用 st.columns 的 gap 参数和响应式布局
    col1, col2, col3 = st.columns([1, 1, 1], gap="small")
    
    with col1:
        st.subheader("玩家状态")
        st.metric("生命值", f"{game_state['player_hp']}/100")
        st.metric("护盾", game_state['player_shield'])
    
    with col2:
        enemy_num = game_state['current_enemy']
        if enemy_num < 3:
            enemy_info = get_enemy_info(enemy_num)
            enemy_hp_key = f'enemy_{enemy_num}_hp'
            enemy_hp = st.session_state.get(enemy_hp_key, enemy_info['hp'])
            st.subheader(f"{enemy_info['name']}")
            st.metric("生命值", enemy_hp)
            st.caption(enemy_info['desc'])
            
            if enemy_num == 1:
                enemy_shield = st.session_state.get(f'enemy_{enemy_num}_shield', 0)
                st.metric("护甲", enemy_shield)
            elif enemy_num == 2:
                blocked_cols = list(game_state['blocked_columns'])
                if blocked_cols:
                    st.caption(f"禁止的列: {[col+1 for col in blocked_cols]}")
    
    with col3:
        st.subheader("游戏信息")
        st.caption(f"当前敌人: {enemy_num + 1}/3")
        if game_state['can_continue_turn']:
            if game_state.get('matched_pairs') and len(game_state['matched_pairs']) == 2:
                st.info("✓ 匹配成功！点击下一张牌继续...")
            else:
                st.info("✓ 匹配成功！继续翻牌")
        if game_state['enemy_turn']:
            st.warning("敌人回合")
        if game_state['waiting_for_action']:
            # 匹配失败，显示提示信息
            if len(game_state['selected_cards']) == 2:
                st.warning("✗ 匹配失败，点击下一组牌继续...")
        if 'last_effect' in st.session_state:
            st.success(st.session_state['last_effect'])
    
    # 敌人回合处理（在渲染前检查，如果enemy_turn为True，执行敌人回合）
    if game_state['enemy_turn']:
        enemy_turn(game_state)
        if not game_state['game_over']:
            st.rerun()
        # 如果游戏结束，继续执行下面的游戏结束检查，显示UI
    
    # 游戏结束检查
    if game_state['game_over']:
        # 显示游戏结束信息
        st.divider()
        if game_state['game_won']:
            st.balloons()
            st.success("🎉 恭喜！你击败了所有敌人！")
        else:
            st.error("💀 游戏结束！你被击败了")
            st.warning("你的生命值已归零，游戏失败")
        
        # 显示最终统计
        col1, col2 = st.columns(2)
        with col1:
            st.metric("最终生命值", f"{max(0, game_state['player_hp'])}/100")
        with col2:
            st.metric("击败敌人", f"{game_state['current_enemy']}/3")
        
        # 重新开始按钮
        st.divider()
        if st.button("🔄 重新开始游戏", use_container_width=True, type="primary"):
            # 清空所有session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # 游戏结束时，不显示卡牌区域
        return
    
    st.divider()
    
    # 显示卡牌区域
    st.subheader("卡牌区域 (4行 × 5列)")
    
    # 显示被禁止的列提示
    if game_state['current_enemy'] == 2 and game_state['blocked_columns']:
        blocked_cols = [col+1 for col in game_state['blocked_columns']]
        st.warning(f"⚠️ 第 {', '.join(map(str, blocked_cols))} 列被禁止操作")
    
    # 创建4x5的网格 - 移动端自动适配
    for row in range(4):
        cols = st.columns(5, gap="small")
        for col in range(5):
            card_idx = row * 5 + col
            with cols[col]:
                # 确保deck有足够的卡牌
                if card_idx >= len(game_state['deck']):
                    # 如果deck不够，创建新牌
                    suits = ['♠', '♥', '♣', '♦']
                    suit = random.choice(suits)
                    value = random.randint(1, 10)
                    game_state['deck'].append({
                        'value': value,
                        'suit': suit,
                        'id': f"{suit}{value}"
                    })
                
                # 确保deck[card_idx]存在且有效
                if card_idx >= len(game_state['deck']) or not game_state['deck'][card_idx]:
                    # 如果card不存在或无效，创建一张新牌
                    suits = ['♠', '♥', '♣', '♦']
                    suit = random.choice(suits)
                    value = random.randint(1, 10)
                    if card_idx >= len(game_state['deck']):
                        game_state['deck'].append({
                            'value': value,
                            'suit': suit,
                            'id': f"{suit}{value}"
                        })
                    else:
                        game_state['deck'][card_idx] = {
                            'value': value,
                            'suit': suit,
                            'id': f"{suit}{value}"
                        }
                
                card = game_state['deck'][card_idx]
                
                # 确保card有必需的字段
                if not isinstance(card, dict) or 'value' not in card or 'suit' not in card:
                    # 如果card结构不完整，创建一张新牌
                    suits = ['♠', '♥', '♣', '♦']
                    suit = random.choice(suits)
                    value = random.randint(1, 10)
                    card = {
                        'value': value,
                        'suit': suit,
                        'id': f"{suit}{value}"
                    }
                    game_state['deck'][card_idx] = card
                
                # 检查卡牌状态
                is_flipped = card_idx in game_state['flipped_cards']
                is_selected = card_idx in game_state['selected_cards']
                is_revealed = card_idx in game_state['revealed_cards']
                is_blocked = game_state['current_enemy'] == 2 and (card_idx % 5) in game_state['blocked_columns']
                # 检查是否是匹配成功但还未替换的牌
                is_matched = game_state.get('matched_pairs') and card_idx in game_state['matched_pairs']
                
                # 注意：现在不再有removed_cards，配对后会被新牌替换
                # 匹配成功的牌即使不在selected_cards中，也应该显示为翻开状态
                if is_flipped or is_selected or is_matched:
                    # 显示卡牌正面 - 简洁的扑克牌样式
                    color = get_card_color(card['suit'])
                    suit_color = 'red' if (card['suit'] == '♥' or card['suit'] == '♦') else 'black'
                    
                    # 翻开的牌不能主动翻回去
                    if is_selected:
                        disabled = True  # 已选中的牌不能取消选中
                    elif is_matched:
                        disabled = False  # 匹配成功的牌可以点击
                    elif game_state['waiting_for_action']:
                        disabled = False  # 等待状态下可以点击
                    elif len(game_state['selected_cards']) == 1:
                        disabled = False  # 只有一张选中时，可以点击已翻开的牌作为第二张
                    else:
                        disabled = True  # 其他情况下，已翻开的牌不能点击（不能翻回去）
                    
                    # 使用简洁的文本格式显示卡牌
                    display_text = f"{card['suit']}\n{card['value']}"
                    
                    # 选中时使用secondary类型显示红色边框，未选中使用primary类型显示白色背景
                    st.button(
                        display_text,
                        key=f"card_{card_idx}",
                        disabled=disabled,
                        on_click=handle_card_click,
                        args=(card_idx, game_state),
                        use_container_width=True,
                        help=f"{card['suit']} {card['value']}",
                        type="secondary" if is_selected else "primary"
                    )
                elif is_revealed:
                    # 被揭示的牌，显示提示（但未选中或翻开）
                    # 在等待状态下，也可以点击来继续
                    disabled = False
                    st.button(
                        f"❓\n{card['value']}",
                        key=f"card_{card_idx}",
                        disabled=disabled,
                        on_click=handle_card_click,
                        args=(card_idx, game_state),
                        use_container_width=True,
                        help=f"这张牌是 {card['value']} 点（已被方片效果揭示）"
                    )
                else:
                    # 显示卡牌背面 - 灰色背景
                    disabled = is_blocked and not game_state['waiting_for_action']
                    button_label = "🚫" if is_blocked else ""
                    st.button(
                        button_label,
                        key=f"card_{card_idx}",
                        disabled=disabled,
                        on_click=handle_card_click,
                        args=(card_idx, game_state),
                        use_container_width=True,
                        help="点击翻牌" if not is_blocked else "此列被禁止",
                        type="secondary"
                    )
    
    # 游戏说明
    with st.expander("游戏规则"):
        st.markdown("""
        ### 游戏规则：
        1. **翻牌规则**：每次可以翻开2张牌
        2. **匹配失败**：如果点数不同，翻回去并轮到敌人行动
        3. **匹配成功**：如果点数相同，执行效果并继续翻牌，直到点数不同
        
        ### 卡牌效果：
        - **♠ 黑桃**：获得点数的护盾
        - **♥ 红心**：回复点数的生命（不超过100）
        - **♣ 梅花**：对敌人造成点数的伤害
        - **♦ 方片**：揭示一张相同点数的牌的位置
        
        ### 敌人：
        1. **敌人1**：20生命，每回合造成10伤害
        2. **敌人2**：40生命，每回合获得5护甲，造成10伤害
        3. **敌人3**：60生命，每回合禁止一列卡牌，造成10伤害
        """)

if __name__ == "__main__":
    main()

