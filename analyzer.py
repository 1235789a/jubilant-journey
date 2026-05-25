import re
from typing import Dict, Optional, List

class PainpointAnalyzer:
    # 五大黄金信号标签
    GOLDEN_SIGNALS = {
        "pay_willing": [
            r"I'd pay for", r"Is there a paid tool", r"would pay", r"willing to pay",
            r"pay someone to", r"worth paying for", r"would gladly pay"
        ],
        "frustration": [
            r"frustrated with", r"I hate", r"fed up with", r"so annoying", r"drives me crazy",
            r"so frustrating", r"can't stand", r"sick of", r"tired of"
        ],
        "searching": [
            r"is there a tool", r"any alternative to", r"looking for", r"need a way to",
            r"anyone know of", r"how to", r"is there a way", r"looking for a"
        ]
    }
    
    COMMUNITY_SIGNALS = ["me too", "same here", "exactly", "this!"]
    
    def __init__(self):
        pass
    
    def analyze_post(self, post: Dict) -> Optional[Dict]:
        # Step 1: 噪声过滤
        if not self._has_valid_painpoint(post):
            return None
        
        # Step 2: 提取痛点
        return self._extract_painpoint(post)
    
    def _has_valid_painpoint(self, post: Dict) -> bool:
        text = post["title"] + " " + post["text"]
        text = text.lower()
        
        # 检查黄金信号
        for signal_type, patterns in self.GOLDEN_SIGNALS.items():
            for pattern in patterns:
                if re.search(pattern.lower(), text):
                    return True
        
        # 检查抱团信号
        if post["score"] >= 50 and post["num_comments"] >= 20:
            # 检查评论中的抱团信号
            comment_text = " ".join(post.get("top_comments", [])).lower()
            for signal in self.COMMUNITY_SIGNALS:
                if signal in comment_text:
                    return True
        
        return False
    
    def _extract_painpoint(self, post: Dict) -> Dict:
        text = post["title"] + " " + post["text"]
        
        # 匹配触发关键词
        trigger = self._find_trigger_keyword(text)
        
        # 计算验证分数
        score = self._calculate_score(post)
        
        # 生成分析结果
        return {
            "painpoint_summary": {
                "user_context": self._extract_context(text),
                "trigger_keyword": trigger,
                "validation_score": score
            },
            "competitor_analysis": {
                "current_substitute": self._extract_substitute(text),
                "substitute_flaws": self._extract_flaws(text)
            },
            "mvp_definition": {
                "product_name": self._generate_product_name(text),
                "core_feature_only": self._extract_core_feature(text),
                "tech_stack_suggestion": "Python script / Single HTML page"
            },
            "monetization_route": {
                "pricing_strategy": "$19 one-time purchase",
                "traffic_hook": self._generate_hook(post)
            },
            "source": {
                "url": post["url"],
                "subreddit": post["subreddit"]
            }
        }
    
    def _find_trigger_keyword(self, text: str) -> str:
        text_lower = text.lower()
        for signal_type, patterns in self.GOLDEN_SIGNALS.items():
            for pattern in patterns:
                if re.search(pattern.lower(), text_lower):
                    return pattern
        return "community_signal"
    
    def _calculate_score(self, post: Dict) -> str:
        score = 1
        if post["score"] >= 100:
            score += 1
        if post["score"] >= 500:
            score += 1
        if post["num_comments"] >= 50:
            score += 1
        if "pay" in (post["title"] + post["text"]).lower():
            score += 1
        return f"{score}星"
    
    def _extract_context(self, text: str) -> str:
        # 简化版：提取前100个词
        words = text.split()
        return " ".join(words[:100])
    
    def _extract_substitute(self, text: str) -> str:
        return "Manual work / Existing tools with limitations"
    
    def _extract_flaws(self, text: str) -> str:
        return "Time-consuming, error-prone, lacks automation"
    
    def _generate_product_name(self, text: str) -> str:
        # 简化版产品名称生成
        keywords = ["Tool", "Helper", "Automator", "Simplifier"]
        return f"Quick{keywords[0]}"
    
    def _extract_core_feature(self, text: str) -> str:
        return "Automates the repetitive task mentioned in the post"
    
    def _generate_hook(self, post: Dict) -> str:
        return f"Check out this tool that solves this exact problem! [Trial Link]"
