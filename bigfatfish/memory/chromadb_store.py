# -*- coding: utf-8 -*-
"""
ChromaDB 向量数据库 - 长期记忆
支持 ARM64 Termux 环境
使用 chromadb>=0.4.x（轻量级版本，支持 ARM64）
"""
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

from ..config import settings

logger = logging.getLogger(__name__)


class ChromaDBStore:
    """ChromaDB 向量数据库管理器（长期记忆）"""
    
    def __init__(self):
        """初始化 ChromaDB"""
        self.client = None
        self.collection = None
        self._init_chromadb()
    
    def _init_chromadb(self):
        """初始化 ChromaDB 连接"""
        try:
            if not chromadb:
                logger.warning("⚠ chromadb 未安装，长期记忆功能不可用")
                return
            
            # 创建持久化存储目录
            db_path = Path(settings.CHROMADB_PATH)
            db_path.mkdir(parents=True, exist_ok=True)
            
            # 初始化 ChromaDB 客户端（本地持久化）
            self.client = chromadb.Client(
                Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(db_path),
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMADB_COLLECTION,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"✓ ChromaDB 初始化成功 (路径: {db_path})")
        
        except Exception as e:
            logger.error(f"❌ ChromaDB 初始化失败: {e}")
            self.client = None
    
    async def add_memory(
        self,
        user_id: str,
        content: str,
        category: str = "general",
        importance: int = 3,
        metadata: Optional[Dict] = None
    ):
        """
        添加记忆到长期存储
        
        Args:
            user_id: 用户 ID
            content: 记忆内容
            category: 分类（preference/event/emotion/fact）
            importance: 重要度（1-5）
            metadata: 额外元数据
        """
        try:
            if not self.collection:
                logger.warning("❌ ChromaDB 未初始化，无法添加记忆")
                return
            
            # 生成唯一 ID
            import hashlib
            doc_id = hashlib.md5(f"{user_id}:{content}:{datetime.now().timestamp()}".encode()).hexdigest()
            
            # 构建元数据
            meta = {
                "user_id": user_id,
                "category": category,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # 添加到集合
            self.collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[meta]
            )
            
            logger.debug(f"✓ 记忆已添加 (用户: {user_id}, 内容: {content[:50]}...)")
        
        except Exception as e:
            logger.error(f"❌ 添加记忆失败: {e}")
    
    async def search_memory(
        self,
        user_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        搜索相关记忆
        
        Args:
            user_id: 用户 ID
            query: 查询文本
            top_k: 返回最相关的 K 条记忆
            
        Returns:
            记忆列表
        """
        try:
            if not self.collection:
                return []
            
            # 查询
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"user_id": {"$eq": user_id}}
            )
            
            # 格式化结果
            memories = []
            if results and results.get("documents"):
                for doc, meta, distance in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    memories.append({
                        "content": doc,
                        "category": meta.get("category", "general"),
                        "importance": meta.get("importance", 3),
                        "timestamp": meta.get("timestamp"),
                        "similarity": 1 - distance  # 余弦距离转换为相似度
                    })
            
            logger.debug(f"✓ 检索到 {len(memories)} 条相关记忆")
            return memories
        
        except Exception as e:
            logger.error(f"❌ 搜索记忆失败: {e}")
            return []
    
    async def count_memories(self, user_id: str) -> int:
        """获取用户的记忆总数"""
        try:
            if not self.collection:
                return 0
            
            # ChromaDB 目前没有直接的 count 接口，使用 query 的长度
            results = self.collection.get(
                where={"user_id": {"$eq": user_id}}
            )
            return len(results.get("ids", []))
        
        except Exception as e:
            logger.error(f"❌ 获取记忆计数失败: {e}")
            return 0
    
    async def delete_user_memories(self, user_id: str):
        """删除用户的所有记忆"""
        try:
            if not self.collection:
                return
            
            # 获取用户的所有记忆 ID
            results = self.collection.get(
                where={"user_id": {"$eq": user_id}}
            )
            
            if results.get("ids"):
                self.collection.delete(ids=results["ids"])
                logger.info(f"✓ 已删除用户 {user_id} 的所有记忆")
        
        except Exception as e:
            logger.error(f"❌ 删除记忆失败: {e}")
