import enum

class TaskComplexity(enum.Enum):
    """任务复杂度枚举"""
    SIMPLE = 1   # 简单任务：直接查询、单一操作
    MEDIUM = 2   # 中等任务：2-3步操作，有条件判断
    COMPLEX = 3  # 复杂任务：多步骤，需要推理，系统诊断
    ADVANCED = 4 # 高级任务：创造性解决方案，复杂诊断，自适应执行

class ArchitectureType(enum.Enum):
    """架构类型枚举"""
    DIRECT = 1       # 直接响应，无思考链
    BASIC_COT = 2    # 基础思考链
    FULL_COT = 3     # 完整思考链
    REACT = 4        # Reasoning + Acting 架构
    PLANNER = 5      # 完整规划架构 