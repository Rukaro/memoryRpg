import streamlit as st
import random
from typing import List, Tuple, Optional, Dict

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
    game_state['selected_cards'] = []

def handle_card_click(card_idx: int, game_state: Dict):
    """处理卡牌点击"""
    if game_state['game_over'] or game_state['enemy_turn']:
        return
    
    # 检查是否被禁止
    if game_state['current_enemy'] == 2:
        col = card_idx % 5
        if col in game_state['blocked_columns']:
            return
    
    # 检查卡牌是否已被移除
    if card_idx in game_state['removed_cards']:
        return
    
    # 如果已经选中，则取消选中（翻回去）
    if card_idx in game_state['selected_cards']:
        game_state['selected_cards'].remove(card_idx)
        if card_idx in game_state['flipped_cards']:
            game_state['flipped_cards'].remove(card_idx)
        return
    
    # 如果已经翻开了（但未选中），说明是已匹配的牌，不能再次选中
    if card_idx in game_state['flipped_cards'] and card_idx not in game_state['selected_cards']:
        return
    
    # 最多选择2张牌
    if len(game_state['selected_cards']) >= 2:
        return
    
    # 添加到选中列表并立即翻开
    game_state['selected_cards'].append(card_idx)
    if card_idx not in game_state['flipped_cards']:
        game_state['flipped_cards'].append(card_idx)
    
    # 如果选中了2张牌，检查是否匹配
    if len(game_state['selected_cards']) == 2:
        idx1, idx2 = game_state['selected_cards']
        card1 = game_state['deck'][idx1]
        card2 = game_state['deck'][idx2]
        
        if card1['value'] == card2['value']:
            # 匹配成功（卡牌已经在flipped_cards中）
            if idx1 not in game_state['removed_cards']:
                game_state['removed_cards'].append(idx1)
            if idx2 not in game_state['removed_cards']:
                game_state['removed_cards'].append(idx2)
            
            # 应用两张牌的效果
            effect1 = apply_card_effect(card1['suit'], card1['value'], game_state)
            effect2 = apply_card_effect(card2['suit'], card2['value'], game_state)
            
            st.session_state['last_effect'] = f"{effect1} {effect2}"
            
            # 清空选中，可以继续翻牌
            game_state['selected_cards'] = []
            game_state['can_continue_turn'] = True
            
            # 检查是否所有牌都已移除
            if len(game_state['removed_cards']) == 20:
                # 重新洗牌
                game_state['deck'] = create_deck()
                game_state['flipped_cards'] = []
                game_state['removed_cards'] = []
                game_state['revealed_cards'] = []
        else:
            # 匹配失败，翻回去并轮到敌人
            if idx1 in game_state['flipped_cards']:
                game_state['flipped_cards'].remove(idx1)
            if idx2 in game_state['flipped_cards']:
                game_state['flipped_cards'].remove(idx2)
            game_state['selected_cards'] = []
            game_state['enemy_turn'] = True
            game_state['can_continue_turn'] = False

def main():
    st.set_page_config(page_title="记忆RPG", layout="wide")
    st.title("🎮 记忆RPG游戏")
    
    init_game_state()
    game_state = st.session_state.game_state
    
    # 初始化牌组
    if not game_state['deck']:
        game_state['deck'] = create_deck()
    
    # 初始化敌人生命值
    for i in range(3):
        enemy_key = f'enemy_{i}_hp'
        if enemy_key not in st.session_state:
            enemy_info = get_enemy_info(i)
            st.session_state[enemy_key] = enemy_info['hp']
    
    # 显示游戏状态
    col1, col2, col3 = st.columns(3)
    
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
            st.info("✓ 匹配成功！继续翻牌")
        if game_state['enemy_turn']:
            st.warning("敌人回合")
        if 'last_effect' in st.session_state:
            st.success(st.session_state['last_effect'])
    
    # 敌人回合处理
    if game_state['enemy_turn']:
        enemy_turn(game_state)
        if not game_state['game_over']:
            st.rerun()
    
    # 游戏结束检查
    if game_state['game_over']:
        if game_state['game_won']:
            st.balloons()
            st.success("🎉 恭喜！你击败了所有敌人！")
        else:
            st.error("💀 游戏结束！你被击败了")
        if st.button("重新开始"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return
    
    st.divider()
    
    # 显示卡牌区域
    st.subheader("卡牌区域 (4行 × 5列)")
    
    # 显示被禁止的列提示
    if game_state['current_enemy'] == 2 and game_state['blocked_columns']:
        blocked_cols = [col+1 for col in game_state['blocked_columns']]
        st.warning(f"⚠️ 第 {', '.join(map(str, blocked_cols))} 列被禁止操作")
    
    # 创建4x5的网格
    for row in range(4):
        cols = st.columns(5)
        for col in range(5):
            card_idx = row * 5 + col
            with cols[col]:
                card = game_state['deck'][card_idx]
                
                # 检查卡牌状态
                is_removed = card_idx in game_state['removed_cards']
                is_flipped = card_idx in game_state['flipped_cards']
                is_selected = card_idx in game_state['selected_cards']
                is_revealed = card_idx in game_state['revealed_cards']
                is_blocked = game_state['current_enemy'] == 2 and (card_idx % 5) in game_state['blocked_columns']
                
                if is_removed:
                    st.button("", disabled=True, key=f"card_{card_idx}")
                elif is_flipped or is_selected:
                    # 显示卡牌正面
                    color = get_card_color(card['suit'])
                    display_text = f"{card['suit']}\n{card['value']}"
                    button_style = "🔴 " if is_selected else ""
                    st.button(
                        f"{button_style}{display_text}",
                        key=f"card_{card_idx}",
                        disabled=is_flipped and not is_selected,
                        on_click=handle_card_click,
                        args=(card_idx, game_state),
                        use_container_width=True
                    )
                elif is_revealed:
                    # 被揭示的牌，显示提示（但未选中或翻开）
                    st.button(
                        f"❓\n{card['value']}",
                        key=f"card_{card_idx}",
                        on_click=handle_card_click,
                        args=(card_idx, game_state),
                        use_container_width=True,
                        help=f"这张牌是 {card['value']} 点（已被方片效果揭示）"
                    )
                else:
                    # 显示卡牌背面
                    button_label = "🚫" if is_blocked else "🂠"
                    st.button(
                        button_label,
                        key=f"card_{card_idx}",
                        disabled=is_blocked,
                        on_click=handle_card_click,
                        args=(card_idx, game_state),
                        use_container_width=True
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

