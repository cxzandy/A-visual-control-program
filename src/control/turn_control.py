#!/usr/bin/env python3
"""
控制管理器 - 处理自动/手动模式和左右转向控制
Turn Control Manager - Handles auto/manual modes and left/right turn control
"""

import time
import logging
import numpy as np
from typing import Dict, Optional, Tuple, Any
from enum import Enum

try:
    from config import ControlConfig, PredictionConfig
except ImportError:
    # 默认配置
    class ControlConfig:
        AUTO_MODE = "auto"
        MANUAL_MODE = "manual"
        DEFAULT_MODE = "auto"
        TURN_SPEED = 0.5
        TURN_ANGLE_STEP = 15
        MANUAL_COMMANDS = {
            'turn_left': 'LEFT',
            'turn_right': 'RIGHT', 
            'go_straight': 'STRAIGHT',
            'stop': 'STOP'
        }

class TurnDirection(Enum):
    """转向方向枚举"""
    LEFT = "left"
    RIGHT = "right"
    STRAIGHT = "straight"
    UNKNOWN = "unknown"

class ControlMode(Enum):
    """控制模式枚举"""
    AUTO = "auto"
    MANUAL = "manual"

class TurnControlManager:
    """转向控制管理器"""
    
    def __init__(self):
        """初始化控制管理器"""
        self.logger = logging.getLogger(__name__)
        
        # 控制状态
        self.current_mode = ControlMode.AUTO
        self.current_direction = TurnDirection.STRAIGHT
        self.manual_command = None
        
        # 转向检测历史
        self.turn_history = []
        self.confidence_history = []
        self.last_turn_time = 0
        
        # 统计信息
        self.stats = {
            'total_detections': 0,
            'left_turns': 0,
            'right_turns': 0,
            'straight_segments': 0,
            'mode_switches': 0,
            'average_confidence': 0.0
        }
        
        self.logger.info("转向控制管理器初始化完成")
    
    def set_control_mode(self, mode: str) -> bool:
        """设置控制模式"""
        try:
            if mode.lower() == "auto":
                old_mode = self.current_mode
                self.current_mode = ControlMode.AUTO
                if old_mode != self.current_mode:
                    self.stats['mode_switches'] += 1
                    self.logger.info("切换到自动模式")
                return True
            elif mode.lower() == "manual":
                old_mode = self.current_mode
                self.current_mode = ControlMode.MANUAL
                if old_mode != self.current_mode:
                    self.stats['mode_switches'] += 1
                    self.logger.info("切换到手动模式")
                return True
            else:
                self.logger.warning(f"无效的控制模式: {mode}")
                return False
        except Exception as e:
            self.logger.error(f"设置控制模式失败: {e}")
            return False
    
    def get_control_mode(self) -> str:
        """获取当前控制模式"""
        return self.current_mode.value
    
    def detect_turn_direction(self, line_params: Optional[list], 
                            prediction_info: Optional[Dict]) -> Tuple[TurnDirection, float]:
        """
        检测转向方向 - 专注于左右转向
        
        Args:
            line_params: 管道线参数
            prediction_info: 预测信息
            
        Returns:
            (direction, confidence): 转向方向和置信度
        """
        if not line_params or not any(p is not None for p in line_params):
            return TurnDirection.UNKNOWN, 0.0
        
        try:
            direction = TurnDirection.STRAIGHT
            confidence = 0.0
            
            # 方法1: 使用预测信息
            if prediction_info and prediction_info.get('direction'):
                pred_direction = prediction_info['direction']
                pred_confidence = prediction_info.get('confidence', 0.0)
                
                if pred_direction == 'left':
                    direction = TurnDirection.LEFT
                    confidence = pred_confidence
                elif pred_direction == 'right':
                    direction = TurnDirection.RIGHT
                    confidence = pred_confidence
                else:
                    direction = TurnDirection.STRAIGHT
                    confidence = pred_confidence * 0.8  # 直行置信度稍低
            
            # 方法2: 基于线参数分析转向
            else:
                turn_angle = self._analyze_line_curvature(line_params)
                if abs(turn_angle) > PredictionConfig.TURN_SENSITIVITY:
                    if turn_angle > 0:
                        direction = TurnDirection.RIGHT
                    else:
                        direction = TurnDirection.LEFT
                    confidence = min(abs(turn_angle) / 45.0, 1.0)  # 归一化到0-1
                else:
                    direction = TurnDirection.STRAIGHT
                    confidence = 0.7
            
            # 更新历史记录
            self._update_turn_history(direction, confidence)
            
            # 更新统计
            self._update_statistics(direction, confidence)
            
            return direction, confidence
            
        except Exception as e:
            self.logger.error(f"转向检测失败: {e}")
            return TurnDirection.UNKNOWN, 0.0
    
    def _analyze_line_curvature(self, line_params: list) -> float:
        """分析线条曲率以确定转向角度"""
        try:
            if len(line_params) < 4 or not all(p is not None for p in line_params[:4]):
                return 0.0
            
            # 假设line_params包含两条线的参数 [rho1, theta1, rho2, theta2]
            theta1, theta2 = line_params[1], line_params[3]
            
            if theta1 is None or theta2 is None:
                return 0.0
            
            # 计算两条线之间的角度差
            angle_diff = np.degrees(theta2 - theta1)
            
            # 归一化角度到 [-180, 180]
            while angle_diff > 180:
                angle_diff -= 360
            while angle_diff < -180:
                angle_diff += 360
            
            return angle_diff
            
        except Exception as e:
            self.logger.error(f"曲率分析失败: {e}")
            return 0.0
    
    def _update_turn_history(self, direction: TurnDirection, confidence: float):
        """更新转向历史"""
        current_time = time.time()
        
        # 添加到历史记录
        self.turn_history.append({
            'direction': direction,
            'confidence': confidence,
            'timestamp': current_time
        })
        
        # 保持历史记录长度
        max_history = 20
        if len(self.turn_history) > max_history:
            self.turn_history = self.turn_history[-max_history:]
        
        # 更新置信度历史
        self.confidence_history.append(confidence)
        if len(self.confidence_history) > max_history:
            self.confidence_history = self.confidence_history[-max_history:]
    
    def _update_statistics(self, direction: TurnDirection, confidence: float):
        """更新统计信息"""
        self.stats['total_detections'] += 1
        
        if direction == TurnDirection.LEFT:
            self.stats['left_turns'] += 1
        elif direction == TurnDirection.RIGHT:
            self.stats['right_turns'] += 1
        elif direction == TurnDirection.STRAIGHT:
            self.stats['straight_segments'] += 1
        
        # 更新平均置信度
        if self.confidence_history:
            self.stats['average_confidence'] = np.mean(self.confidence_history)
    
    def get_smoothed_direction(self, window_size: int = 5) -> Tuple[TurnDirection, float]:
        """获取平滑后的转向方向"""
        if len(self.turn_history) < window_size:
            if self.turn_history:
                return self.turn_history[-1]['direction'], self.turn_history[-1]['confidence']
            return TurnDirection.UNKNOWN, 0.0
        
        try:
            # 取最近的几个检测结果
            recent_turns = self.turn_history[-window_size:]
            
            # 统计各个方向的出现次数和置信度
            direction_votes = {}
            for turn in recent_turns:
                direction = turn['direction']
                confidence = turn['confidence']
                
                if direction not in direction_votes:
                    direction_votes[direction] = {'count': 0, 'total_confidence': 0.0}
                
                direction_votes[direction]['count'] += 1
                direction_votes[direction]['total_confidence'] += confidence
            
            # 找到最多票数的方向
            best_direction = TurnDirection.UNKNOWN
            best_score = 0
            best_confidence = 0.0
            
            for direction, votes in direction_votes.items():
                # 综合考虑票数和置信度
                score = votes['count'] * votes['total_confidence'] / votes['count']
                if score > best_score:
                    best_score = score
                    best_direction = direction
                    best_confidence = votes['total_confidence'] / votes['count']
            
            return best_direction, best_confidence
            
        except Exception as e:
            self.logger.error(f"方向平滑失败: {e}")
            return TurnDirection.UNKNOWN, 0.0
    
    def process_manual_command(self, command: str) -> bool:
        """处理手动控制命令"""
        if self.current_mode != ControlMode.MANUAL:
            self.logger.warning("当前不在手动模式，忽略手动命令")
            return False
        
        try:
            command = command.lower().strip()
            
            if command in ['left', 'turn_left', 'l']:
                self.manual_command = ControlConfig.MANUAL_COMMANDS['turn_left']
                self.current_direction = TurnDirection.LEFT
                self.logger.info("手动命令：左转")
                return True
            elif command in ['right', 'turn_right', 'r']:
                self.manual_command = ControlConfig.MANUAL_COMMANDS['turn_right']
                self.current_direction = TurnDirection.RIGHT
                self.logger.info("手动命令：右转")
                return True
            elif command in ['straight', 'forward', 's', 'f']:
                self.manual_command = ControlConfig.MANUAL_COMMANDS['go_straight']
                self.current_direction = TurnDirection.STRAIGHT
                self.logger.info("手动命令：直行")
                return True
            elif command in ['stop', 'halt']:
                self.manual_command = ControlConfig.MANUAL_COMMANDS['stop']
                self.current_direction = TurnDirection.UNKNOWN
                self.logger.info("手动命令：停止")
                return True
            else:
                self.logger.warning(f"未知的手动命令: {command}")
                return False
                
        except Exception as e:
            self.logger.error(f"处理手动命令失败: {e}")
            return False
    
    def get_control_output(self) -> Dict[str, Any]:
        """获取控制输出"""
        if self.current_mode == ControlMode.MANUAL:
            # 手动模式：返回手动命令
            return {
                'mode': 'manual',
                'command': self.manual_command,
                'direction': self.current_direction.value,
                'confidence': 1.0,  # 手动命令置信度为1
                'source': 'manual_input'
            }
        else:
            # 自动模式：返回检测结果
            direction, confidence = self.get_smoothed_direction()
            return {
                'mode': 'auto',
                'command': self._direction_to_command(direction),
                'direction': direction.value,
                'confidence': confidence,
                'source': 'auto_detection'
            }
    
    def _direction_to_command(self, direction: TurnDirection) -> str:
        """将方向转换为命令"""
        if direction == TurnDirection.LEFT:
            return ControlConfig.MANUAL_COMMANDS['turn_left']
        elif direction == TurnDirection.RIGHT:
            return ControlConfig.MANUAL_COMMANDS['turn_right']
        elif direction == TurnDirection.STRAIGHT:
            return ControlConfig.MANUAL_COMMANDS['go_straight']
        else:
            return ControlConfig.MANUAL_COMMANDS['stop']
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats['current_mode'] = self.current_mode.value
        stats['current_direction'] = self.current_direction.value
        stats['history_length'] = len(self.turn_history)
        
        # 计算转向比例
        total_turns = stats['left_turns'] + stats['right_turns'] + stats['straight_segments']
        if total_turns > 0:
            stats['left_turn_ratio'] = stats['left_turns'] / total_turns
            stats['right_turn_ratio'] = stats['right_turns'] / total_turns
            stats['straight_ratio'] = stats['straight_segments'] / total_turns
        else:
            stats['left_turn_ratio'] = 0.0
            stats['right_turn_ratio'] = 0.0
            stats['straight_ratio'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            'total_detections': 0,
            'left_turns': 0,
            'right_turns': 0,
            'straight_segments': 0,
            'mode_switches': 0,
            'average_confidence': 0.0
        }
        self.turn_history.clear()
        self.confidence_history.clear()
        self.logger.info("统计信息已重置")
