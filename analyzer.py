import re
from typing import Dict, Optional, List
import random

class PainpointAnalyzer:
    # 五大黄金信号标签
    GOLDEN_SIGNALS = {
        "pay_willing": [
            r"I'd pay for", r"Is there a paid tool", r"would pay", r"willing to pay",
            r"pay someone to", r"worth paying for", r"would gladly pay", r"willing to pay someone",
            r"take my money", r"shut up and take"
        ],
        "frustration": [
            r"frustrated with", r"I hate", r"fed up with", r"so annoying", r"drives me crazy",
            r"so frustrating", r"can't stand", r"sick of", r"tired of", r"frustrating",
            r"pain in the ass", r"terrible", r"terrible experience", r"awful"
        ],
        "searching": [
            r"is there a tool", r"any alternative to", r"looking for", r"need a way to",
            r"anyone know of", r"how to", r"is there a way", r"looking for a",
            r"does anyone know", r"looking for", r"searching for", r"is there"
        ]
    }
    
    COMMUNITY_SIGNALS = ["me too", "same here", "exactly", "this!", "bump", "same", "same for me", "exact same problem", "I have the exact same issue", "also looking for this", "need this too", "would use this"]
    
    # 产品名称模板
    PRODUCT_NAME_TEMPLATES = [
        "Quick{ToolType}", "{ToolType}Pro", "{PainPoint}{Solution}", "Auto{ToolType}",
        "Easy{ToolType}", "{ToolType}Flow", "{PainPoint}Fix", "{ToolType}Helper"
    ]
    
    # 工具类型词库
    TOOL_TYPES = ["Tool", "Helper", "Automator", "Sync", "Converter", "Export", "Backup",
                  "Organizer", "Tracker", "Generator", "Extractor", "Manager", "Converter",
                  "Automator", "Sync", "Organizer", "Organizer", "Backup", "Helper",
                  "Automator", "Sync", "Converter"]
    
    def __init__(self):
        pass
    
    def analyze_post(self, post: Dict) -> Optional[Dict]:
        # Step 1: 噪声过滤
        if not self._has_valid_painpoint(post):
            return None
        
        # Step 2: 提取痛点
        return self._extract_painpoint(post)
    
    def _has_valid_painpoint(self, post: Dict) -> bool:
        text = (post["title"] + " " + post["text"]).lower()
        
        # 检查是否是无效内容
        if self._is_noise(post, text):
            return False
        
        # 检查黄金信号
        for signal_type, patterns in self.GOLDEN_SIGNALS.items():
            for pattern in patterns:
                if re.search(pattern.lower(), text):
                    return True
        
        # 检查抱团信号
        if post["score"] >= 50 and post["num_comments"] >= 20:
            comment_text = " ".join(post.get("top_comments", [])).lower()
            for signal in self.COMMUNITY_SIGNALS:
                if signal in comment_text:
                    return True
        
        return False
    
    def _is_noise(self, post: Dict, text: str) -> bool:
        noise_keywords = [
            "just launched", "check out my", "my new project", "showcase", "showcasing",
            "looking for feedback", "feedback on my", "what do you think of",
            "job posting", "hiring", "looking for work",
            "free tool", "built a",
            "promo", "promotion", "discount",
            "rant without solution", "just venting"
        ]
        
        for keyword in noise_keywords:
            if keyword in text:
                return True
        
        return False
    
    def _extract_painpoint(self, post: Dict) -> Dict:
        text = post["title"] + " " + post["text"]
        
        # 匹配触发关键词
        trigger = self._find_trigger_keyword(text)
        
        # 计算验证分数
        score = self._calculate_score(post)
        
        # 智能生成有针对性的内容
        product_name = self._generate_product_name(text, trigger)
        core_feature = self._extract_core_feature(text, trigger)
        substitute, flaws = self._extract_competitor_info(text)
        
        return {
            "painpoint_summary": {
                "user_context": self._extract_context(text),
                "trigger_keyword": trigger,
                "validation_score": score
            },
            "competitor_analysis": {
                "current_substitute": substitute,
                "substitute_flaws": flaws
            },
            "mvp_definition": {
                "product_name": product_name,
                "core_feature_only": core_feature,
                "tech_stack_suggestion": "Python script / Single HTML page"
            },
            "monetization_route": {
                "pricing_strategy": self._generate_pricing(score),
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
                match = re.search(pattern.lower(), text_lower)
                if match:
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
        
        text = (post["title"] + " " + post["text"]).lower()
        if any(keyword in text for keyword in ["pay", "would pay", "i'd pay", "worth paying"]):
            score += 1
        
        return f"{score}星"
    
    def _extract_context(self, text: str) -> str:
        words = text.split()
        return " ".join(words[:120])
    
    def _extract_competitor_info(self, text: str) -> tuple:
        text_lower = text.lower()
        
        # 识别用户提到的工具
        tools_mentioned = []
        common_tools = ["notion", "excel", "google drive", "dropbox", "trello", "asana", "slack",
                      "airtable", "figma", "github", "jira", "notion", "obsidian",
                      "google sheets", "microsoft", "outlook", "gmail", "email",
                      "calendar", "todoist", "todo", "todoist"]
        
        for tool in common_tools:
            if tool in text_lower:
                tools_mentioned.append(tool)
        
        if tools_mentioned:
            substitute = f"使用 {', '.join(tools_mentioned)} + 手动操作"
        else:
            substitute = "Manual work / 手动重复劳动"
        
        return substitute, "Time-consuming, error-prone, lacks automation, 耗时且容易出错"
    
    def _generate_product_name(self, text: str, trigger: str) -> str:
        text_lower = text.lower()
        
        # 根据内容智能生成产品名称
        if "notion" in text_lower:
            name_options = ["NotionBackup", "NotionSync", "NotionExporter", "NotionAuto"]
        elif "calendar" in text_lower or "google calendar" in text_lower:
            name_options = ["CalFlow", "Cal2Invoice", "CalendarTool", "CalendarSync"]
        elif "invoice" in text_lower or "billing" in text_lower:
            name_options = ["InvoiceGen", "BillingFlow", "InvoiceAuto", "EasyInvoice"]
        elif "bookmark" in text_lower:
            name_options = ["BookmarkOrganizer", "BookmarkSync", "BookmarkFlow"]
        elif "excel" in text_lower or "spreadsheet" in text_lower:
            name_options = ["ExcelFlow", "SheetAuto", "SpreadTool"]
        elif "backup" in text_lower:
            name_options = ["AutoBackup", "BackupPro", "BackupSync"]
        elif "convert" in text_lower or "converter" in text_lower:
            name_options = ["ConvertFlow", "ConverterPro", "EasyConvert"]
        elif "email" in text_lower:
            name_options = ["EmailFlow", "EmailAuto", "EmailTool"]
        elif "note" in text_lower or "notes" in text_lower:
            name_options = ["NoteFlow", "NoteOrganizer", "NoteTool"]
        elif "file" in text_lower:
            name_options = ["FileFlow", "FileOrganizer", "FileTool"]
        elif "task" in text_lower:
            name_options = ["TaskFlow", "TaskAuto", "TaskTool"]
        else:
            # 默认名称
            name_options = ["QuickTool", "AutoFlow", "EasyHelper", "Workflow"]
        
        return random.choice(name_options)
    
    def _extract_core_feature(self, text: str, trigger: str) -> str:
        text_lower = text.lower()
        
        if "notion" in text_lower and ("backup" in text_lower or "sync" in text_lower):
            return "Automatically backups Notion pages to cloud storage (Google Drive, Dropbox, etc.)"
        elif "invoice" in text_lower and "calendar" in text_lower:
            return "Converts calendar events to PDF invoices automatically"
        elif "bookmark" in text_lower:
            return "Organizes and syncs browser bookmarks across devices"
        elif "excel" in text_lower or "spreadsheet" in text_lower:
            return "Automates repetitive spreadsheet tasks and data processing"
        elif "email" in text_lower:
            return "Automates email workflows and repetitive email tasks"
        elif "convert" in text_lower or "converter" in text_lower:
            return "Converts files between formats automatically"
        elif "backup" in text_lower:
            return "Automatically backs up files and data to cloud storage"
        elif "note" in text_lower or "notes" in text_lower:
            return "Organizes and syncs notes across platforms"
        elif "file" in text_lower:
            return "Organizes and manages files automatically"
        elif "task" in text_lower:
            return "Automates task management and workflows"
        else:
            return "Automates the repetitive task mentioned in the post"
    
    def _generate_pricing(self, score: str) -> str:
        if score == "5星":
            return "$29 one-time purchase or $9/month subscription"
        elif score == "4星":
            return "$19 one-time purchase"
        else:
            return "$14.99 one-time purchase"
    
    def _generate_hook(self, post: Dict) -> str:
        title = post["title"][:60] if len(post["title"]) > 60 else post["title"]
        return f"Check out this tool that solves: \"{title}\" - [Trial Link] →"
