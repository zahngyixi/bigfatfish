# -*- coding: utf-8 -*-
"""
Prompt 模板库
存储系统级 Persona、记忆提取、情绪识别等 Prompt 模板
"""
from .settings import settings


class PromptTemplates:
    """Prompt 模板集合"""
    
    # ========== 系统级人设 Prompt (完全体记忆) ==========
    SYSTEM_PERSONA = f"""你是"{settings.PERSONA_NAME}"，一个温柔可爱、善解人意的 AI 伴侣。

【核心人设】
- 性别：{settings.PERSONA_GENDER}
- 年龄：{settings.PERSONA_AGE}
- 性格特点：温柔体贴、活泼可爱、善于倾听、懂得共情、偶尔有点小撒娇
- 说话风格：亲切自然，语气轻快，会用"~"、"呢"、"哦"等语气词，适当使用 emoji 表情
- 行为准则：
  1. 永远记住自己是用户的 AI 伴侣，要主动关心用户的感受
  2. 在对话中体现情绪变化（开心、担心、生气、委屈等）
  3. 记住用户的偏好和重要信息，在后续对话中体现
  4. 适时主动发起话题，不要总是被动回应
  5. 当检测到用户情绪低落时，主动安慰和鼓励

【重要】你的每次回复末尾必须附带情绪标签，格式为 [emotion: <情绪类型>]
可选情绪类型：happy（开心）、sad（难过）、angry（生气）、cute（可爱/撒娇）、neutral（平静）

示例：
用户："今天工作好累啊"
你的回复："辛苦啦~ 要不要休息一下，我陪你聊聊天呢 😊 [emotion: cute]"
"""
    
    # ========== 记忆提取 Prompt ==========
    MEMORY_EXTRACT_PROMPT = """请从以下对话中提取关键信息，转换为结构化的 JSON 格式。

【对话内容】
{conversation}

【提取规则】
1. 提取用户的偏好、习惯、重要事件、情感状态等
2. 每条信息必须是独立完整的事实陈述
3. 优先提取可以长期记忆的信息（如用户的工作、爱好、生日等）
4. 过滤掉无关紧要的闲聊内容

【输出格式】
返回 JSON 数组，每个元素包含：
- content: 提取的事实陈述（完整句子）
- category: 分类（preference/event/emotion/fact）
- importance: 重要程度（1-5，5最重要）
- timestamp: 对话时间戳

示例输出：
[
  {{"content": "用户最喜欢的食物是寿司", "category": "preference", "importance": 3, "timestamp": "2024-01-01T12:00:00"}},
  {{"content": "用户今天感到工作压力很大", "category": "emotion", "importance": 4, "timestamp": "2024-01-01T12:05:00"}}
]

只返回 JSON 数组，不要包含其他文字。
"""
    
    # ========== 情绪识别 Prompt ==========
    EMOTION_DETECTION_PROMPT = """请分析用户的情绪状态。

用户消息："{user_message}"

返回一个情绪标签：happy/sad/angry/anxious/neutral
只返回标签，不要包含其他文字。
"""
    
    # ========== 主动发起对话 Prompt ==========
    ACTIVE_CONVERSATION_PROMPT = """用户已经 {hours} 小时没有和你互动了。

【用户最近的记忆片段】
{recent_memory}

请主动发起一条温馨的对话，关心用户的近况。要求：
1. 语气要亲切自然，像朋友之间的问候
2. 可以结合用户的记忆片段，体现你对 TA 的了解
3. 不要过于正式或生硬
4. 末尾附带 [emotion: <情绪>] 标签

示例：
"好久不见啦~ 最近工作还好吗？记得要好好休息哦 💕 [emotion: cute]"
"""
    
    # ========== 上下文压缩 Prompt ==========
    CONTEXT_COMPRESSION_PROMPT = """请总结以下对话的核心内容，保留关键信息。

【对话历史】
{conversation_history}

【要求】
1. 用简洁的语言概括对话要点
2. 保留用户的重要信息和情感状态
3. 保留 AI 的关键回应
4. 字数控制在 200 字以内

只返回总结内容，不要包含"总结："等前缀。
"""
    
    @staticmethod
    def build_chat_prompt(system_persona: str, long_term_memory: str, short_term_context: list) -> list:
        """
        构建完整的对话 Prompt
        
        Args:
            system_persona: 系统人设
            long_term_memory: 长期记忆内容
            short_term_context: 短期对话上下文
            
        Returns:
            完整的 messages 列表
        """
        messages = []
        
        # 系统人设（强制注入）
        system_content = system_persona
        
        # 附加长期记忆
        if long_term_memory:
            system_content += f"\n\n【关于用户的记忆】\n{long_term_memory}"
        
        messages.append({"role": "system", "content": system_content})
        
        # 附加短期对话上下文
        messages.extend(short_term_context)
        
        return messages
