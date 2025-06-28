import json
import os
from typing import List, Dict, Any, Optional
import time

class KnowledgeItem:
    """知识条目模型"""
    
    def __init__(self, title: str, content: str, created_at: float = None, updated_at: float = None):
        self.title = title
        self.content = content
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeItem':
        """从字典创建知识条目"""
        return cls(
            title=data.get("title", ""),
            content=data.get("content", ""),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time())
        )

class KnowledgeBase:
    """知识库模型"""
    
    def __init__(self, items: List[KnowledgeItem] = None, kb_file: str = None):
        self.items = items or []
        self.kb_file = kb_file or os.path.join(os.path.expanduser("~"), "macOS_Copilot_knowledge.json")
        
        # 如果提供了文件路径且文件存在，则从文件加载
        if self.kb_file and os.path.exists(self.kb_file):
            self._load_from_file()
    
    def add_item(self, item: KnowledgeItem) -> None:
        """添加知识条目"""
        self.items.append(item)
        self._save_to_file()
    
    def add_item_from_values(self, title: str, content: str) -> None:
        """通过值添加知识条目"""
        item = KnowledgeItem(title, content)
        self.add_item(item)
    
    def remove_item(self, index: int) -> None:
        """删除知识条目"""
        if 0 <= index < len(self.items):
            del self.items[index]
            self._save_to_file()
    
    def update_item(self, index: int, title: str, content: str) -> bool:
        """更新知识条目"""
        if 0 <= index < len(self.items):
            item = self.items[index]
            item.title = title
            item.content = content
            item.updated_at = time.time()
            self._save_to_file()
            return True
        return False
    
    def get_item(self, index: int) -> Optional[KnowledgeItem]:
        """获取知识条目"""
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def get_all_items(self) -> List[KnowledgeItem]:
        """获取所有知识条目"""
        return self.items
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [item.to_dict() for item in self.items]
    
    @classmethod
    def from_dict_list(cls, data: List[Dict[str, Any]], kb_file: str = None) -> 'KnowledgeBase':
        """从字典列表创建知识库"""
        items = [KnowledgeItem.from_dict(item) for item in data]
        return cls(items, kb_file)
    
    def _save_to_file(self) -> None:
        """保存到文件（内部方法）"""
        if not self.kb_file:
            return
            
        try:
            with open(self.kb_file, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict_list(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存知识库失败: {e}")
    
    def _load_from_file(self) -> None:
        """从文件加载（内部方法）"""
        if not os.path.exists(self.kb_file):
            return
            
        try:
            with open(self.kb_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.items = [KnowledgeItem.from_dict(item) for item in data]
        except Exception as e:
            print(f"加载知识库失败: {e}")
    
    def save_to_file(self, filepath: str = None) -> None:
        """保存到指定文件"""
        save_path = filepath or self.kb_file
        if not save_path:
            return
            
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict_list(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存知识库失败: {e}")
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'KnowledgeBase':
        """从文件加载"""
        if not os.path.exists(filepath):
            return cls(kb_file=filepath)
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls.from_dict_list(data, filepath)
        except Exception as e:
            print(f"加载知识库失败: {e}")
            return cls(kb_file=filepath)
    
    def search(self, query: str) -> List[KnowledgeItem]:
        """简单搜索知识库"""
        results = []
        query = query.lower()
        
        for item in self.items:
            if (query in item.title.lower() or 
                query in item.content.lower()):
                results.append(item)
                
        return results
        
    def semantic_search(self, query: str, top_k: int = 3) -> List[KnowledgeItem]:
        """语义搜索知识库
        
        尝试使用语义搜索，如果没有可用的向量引擎，则回退到简单搜索
        """
        # 目前先使用简单搜索，后续可以集成向量数据库
        return self.search(query) 