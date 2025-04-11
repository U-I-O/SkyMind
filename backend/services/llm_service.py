import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

import openai
from openai import AsyncOpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks.base import AsyncCallbackHandler

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("services.llm")

class LLMService:
    """LLM服务，封装与OpenAI API的交互"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.client = None
        self.is_initialized = False
        self.request_count = 0
        self.last_request_time = None
    
    async def initialize(self):
        """初始化LLM服务"""
        if self.is_initialized:
            return
        
        try:
            logger.info(f"初始化LLM服务，模型: {self.model}")
            
            # 设置API密钥
            os.environ["OPENAI_API_KEY"] = self.api_key
            
            # 创建异步客户端
            self.client = AsyncOpenAI(api_key=self.api_key)
            
            self.is_initialized = True
            logger.info("LLM服务初始化成功")
            
            return True
        except Exception as e:
            logger.error(f"初始化LLM服务失败: {str(e)}")
            raise
    
    async def generate_completion(self, prompt: str, 
                                 temperature: float = 0.7,
                                 max_tokens: int = 500) -> Dict[str, Any]:
        """
        生成文本补全
        
        Args:
            prompt: 提示文本
            temperature: 采样温度
            max_tokens: 最大令牌数
            
        Returns:
            生成结果字典
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            response = await self.client.completions.create(
                model=self.model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 更新统计信息
            self.request_count += 1
            self.last_request_time = datetime.utcnow()
            
            return {
                "success": True,
                "text": response.choices[0].text.strip(),
                "tokens": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"生成文本补全失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def generate_chat_completion(self, 
                                      messages: List[Dict[str, str]],
                                      temperature: float = 0.7,
                                      max_tokens: int = 500) -> Dict[str, Any]:
        """
        生成聊天补全
        
        Args:
            messages: 消息列表
            temperature: 采样温度
            max_tokens: 最大令牌数
            
        Returns:
            生成结果字典
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 更新统计信息
            self.request_count += 1
            self.last_request_time = datetime.utcnow()
            
            return {
                "success": True,
                "text": response.choices[0].message.content.strip(),
                "tokens": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"生成聊天补全失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def generate_emergency_response_plan(self, 
                                             event_data: Dict[str, Any],
                                             available_resources: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成应急响应计划
        
        Args:
            event_data: 事件数据
            available_resources: 可用资源数据
            
        Returns:
            响应计划字典
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 创建提示
            system_prompt = """你是一个智慧城市低空应急响应系统的AI专家。
            请根据事件信息生成一个详细的应急响应计划。
            你的计划应该考虑事件严重程度、可用资源和最佳应急实践。
            输出应该是结构化的JSON对象，包含以下字段：
            1. situation_assessment: 对情况的评估
            2. severity_level: 严重程度，可以是'low', 'medium', 'high'
            3. actions: 响应行动数组，每个包含：
               - action_type: 行动类型
               - priority: 优先级（1-10，10最高）
               - description: 行动描述
               - resources_needed: 所需资源数组
               - estimated_time: 预计完成时间（分钟）
            4. additional_notes: 额外说明
            """
            
            # 构建用户消息
            user_message = f"""
            事件信息:
            - 事件ID: {event_data.get('event_id', 'unknown')}
            - 标题: {event_data.get('title', 'unknown')}
            - 描述: {event_data.get('description', 'unknown')}
            - 类型: {event_data.get('type', 'unknown')}
            - 级别: {event_data.get('level', 'unknown')}
            - 位置: {json.dumps(event_data.get('location', {}), ensure_ascii=False)}
            
            可用资源:
            - 无人机: {json.dumps(available_resources.get('drones', []), ensure_ascii=False)}
            - 紧急服务: {json.dumps(available_resources.get('emergency_services', {}), ensure_ascii=False)}
            
            请生成应急响应计划。输出应为JSON对象。
            """
            
            # 创建消息列表
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # 生成响应
            response = await self.generate_chat_completion(
                messages,
                temperature=0.2,  # 低温度，提高一致性
                max_tokens=1000    # 增加最大令牌数
            )
            
            if not response["success"]:
                return response
            
            # 解析JSON响应
            try:
                plan = json.loads(response["text"])
                logger.info(f"成功生成应急响应计划，严重程度: {plan.get('severity_level')}")
                
                return {
                    "success": True,
                    "plan": plan,
                    "tokens": response["tokens"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            except json.JSONDecodeError:
                logger.error("无法解析LLM返回的JSON")
                return {
                    "success": False,
                    "error": "无法解析响应计划JSON",
                    "raw_text": response["text"],
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"生成应急响应计划失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def analyze_security_event(self, 
                                   event_data: Dict[str, Any],
                                   historical_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        分析安全事件
        
        Args:
            event_data: 事件数据
            historical_data: 历史数据列表
            
        Returns:
            分析结果字典
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 创建提示
            system_prompt = """你是一个智慧城市安防系统的AI分析专家。
            请根据事件信息和历史数据分析此次安全事件。
            你的分析应该包括事件性质、潜在风险、可能原因和建议措施。
            输出应该是结构化的JSON对象，包含以下字段：
            1. event_nature: 事件性质描述
            2. risk_assessment: 风险评估，包含风险级别和潜在影响
            3. probable_causes: 可能的原因数组
            4. recommended_actions: 建议措施数组
            5. correlation_with_history: 与历史事件的相关性分析
            """
            
            # 历史数据部分
            history_part = ""
            if historical_data and len(historical_data) > 0:
                history_part = "历史事件数据:\n"
                for i, hist in enumerate(historical_data[:5]):  # 最多包含5条历史记录
                    history_part += f"- 事件{i+1}: {hist.get('title', 'unknown')}, 类型: {hist.get('type', 'unknown')}, 时间: {hist.get('detected_at', 'unknown')}\n"
            
            # 构建用户消息
            user_message = f"""
            当前事件信息:
            - 事件ID: {event_data.get('event_id', 'unknown')}
            - 标题: {event_data.get('title', 'unknown')}
            - 描述: {event_data.get('description', 'unknown')}
            - 类型: {event_data.get('type', 'unknown')}
            - 级别: {event_data.get('level', 'unknown')}
            - 位置: {json.dumps(event_data.get('location', {}), ensure_ascii=False)}
            - 检测细节: {json.dumps(event_data.get('detection_data', {}), ensure_ascii=False)}
            
            {history_part}
            
            请分析此安全事件并提供建议。输出应为JSON对象。
            """
            
            # 创建消息列表
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # 生成响应
            response = await self.generate_chat_completion(
                messages,
                temperature=0.3,
                max_tokens=800
            )
            
            if not response["success"]:
                return response
            
            # 解析JSON响应
            try:
                analysis = json.loads(response["text"])
                logger.info(f"成功生成安全事件分析")
                
                return {
                    "success": True,
                    "analysis": analysis,
                    "tokens": response["tokens"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            except json.JSONDecodeError:
                logger.error("无法解析LLM返回的JSON")
                return {
                    "success": False,
                    "error": "无法解析分析结果JSON",
                    "raw_text": response["text"],
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"分析安全事件失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# 创建全局LLM服务实例
llm_service = LLMService()