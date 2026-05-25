from analyzer import PainpointAnalyzer
import random
import json

def generate_large_dataset():
    """生成100条真实感的 Reddit 帖子数据"""
    
    # 模板数据 - 涵盖真实的 Reddit 痛点场景
    templates = [
        # Notion 相关痛点
        {"title": "I'd pay $20/month for a tool that automatically backs up my Notion pages to Google Drive",
         "text": "Notion crashed last week and I lost all my content. Is there a paid tool that does this?",
         "subreddit": "Notion", "score": 847, "comments": 156},
        {"title": "Looking for a Notion export alternative - built-in export is terrible",
         "text": "Every time I export from Notion it's a mess. Need a better way to backup my data.",
         "subreddit": "Notion", "score": 234, "comments": 45},
        {"title": "Is there a paid tool that syncs Notion to Obsidian automatically?",
         "text": "Tired of manually copying notes between the two. Would pay for this.",
         "subreddit": "Notion", "score": 543, "comments": 89},
        
        # Excel/Spreadsheet 相关痛点
        {"title": "I spend 4 hours every week manually cleaning Excel data - is there a tool for this?",
         "text": "Would pay someone to build an automator for my repetitive spreadsheet tasks.",
         "subreddit": "excel", "score": 678, "comments": 134},
        {"title": "Is there an alternative to Excel that's not Google Sheets?",
         "text": "Fed up with how slow Excel is for large datasets.",
         "subreddit": "spreadsheets", "score": 213, "comments": 67},
        {"title": "So frustrated with VLOOKUP - is there a better way to join data?",
         "text": "Every time I use VLOOKUP I want to cry. Need a simpler tool.",
         "subreddit": "excel", "score": 432, "comments": 98},
        
        # 发票/财务相关痛点
        {"title": "I'd pay for a tool that turns my calendar events into PDF invoices automatically",
         "text": "Freelance here, waste 5hrs a week on invoices. Someone please build this.",
         "subreddit": "freelance", "score": 423, "comments": 87},
        {"title": "Looking for an alternative to QuickBooks - it's way too bloated",
         "text": "Tired of paying for features I don't use. Just need basic invoicing.",
         "subreddit": "smallbusiness", "score": 345, "comments": 78},
        {"title": "Is there a tool to automatically generate receipts from photos?",
         "text": "So tedious entering expenses manually every week.",
         "subreddit": "productivity", "score": 189, "comments": 43},
        
        # 书签/阅读相关痛点
        {"title": "I hate how all bookmark tools are either too complicated or don't work",
         "text": "Tried Pocket, Raindrop, etc. Nothing sticks. Why is this so hard?",
         "subreddit": "technology", "score": 234, "comments": 45},
        {"title": "Looking for a tool to sync bookmarks across Chrome, Safari, Firefox",
         "text": "Native sync is terrible. Would pay for a good solution.",
         "subreddit": "productivity", "score": 178, "comments": 54},
        
        # 文件管理相关痛点
        {"title": "Is there a tool that organizes my downloads folder automatically?",
         "text": "My downloads is a mess. Need something that sorts files into folders.",
         "subreddit": "productivity", "score": 321, "comments": 76},
        {"title": "Fed up with Google Drive search - it never finds what I need",
         "text": "So frustrating trying to locate old files. Is there a better file organizer?",
         "subreddit": "technology", "score": 289, "comments": 65},
        {"title": "Looking for a tool to batch rename files - manual renaming takes forever",
         "text": "Would pay for something that can rename 100s of files at once with patterns.",
         "subreddit": "software", "score": 167, "comments": 43},
        
        # 邮件相关痛点
        {"title": "Tired of manually replying to the same emails - any automation tool?",
         "text": "Would pay for something that can auto-respond with canned replies to common queries.",
         "subreddit": "productivity", "score": 412, "comments": 98},
        {"title": "Looking for an alternative to Gmail's built-in filters - they're too limited",
         "text": "Need more control over my inbox automation.",
         "subreddit": "email", "score": 198, "comments": 45},
        {"title": "Is there a paid tool that unsubscribes me from all junk mail automatically?",
         "text": "So tired of this spam. Would pay for a good unsubscribe solution.",
         "subreddit": "technology", "score": 543, "comments": 123},
        
        # Trello/项目管理相关痛点
        {"title": "I hate how Trello doesn't have good reporting - any alternatives?",
         "text": "As a project manager, I need better insights. Would pay for this.",
         "subreddit": "trello", "score": 276, "comments": 54},
        {"title": "Looking for a way to auto-generate Trello cards from emails",
         "text": "Tired of manually creating cards from incoming requests.",
         "subreddit": "trello", "score": 156, "comments": 34},
        
        # 社交媒体相关痛点
        {"title": "Is there a tool that posts to multiple social platforms at once?",
         "text": "So time-consuming posting to Instagram, Twitter, LinkedIn individually.",
         "subreddit": "socialmedia", "score": 345, "comments": 76},
        {"title": "Looking for an alternative to Canva that's not so expensive",
         "text": "Canva's pricing keeps going up but I only need basic features.",
         "subreddit": "marketing", "score": 289, "comments": 67},
        
        # 其他随机高价值痛点
        {"title": "So frustrated with PDF editing - Acrobat is way too expensive",
         "text": "Just need basic PDF editing without paying a monthly fee.",
         "subreddit": "software", "score": 387, "comments": 89},
        {"title": "Looking for a tool that converts images to text accurately",
         "text": "Current OCR tools I've tried are terrible. Would pay for accurate results.",
         "subreddit": "technology", "score": 265, "comments": 54},
        {"title": "Is there a way to auto-sync photos from my phone to external hard drive?",
         "text": "Tired of manually backing up every few months.",
         "subreddit": "technology", "score": 432, "comments": 98},
        {"title": "I'd pay for a good password manager alternative - 1Password got too expensive",
         "text": "Looking for something more affordable that still has good features.",
         "subreddit": "technology", "score": 512, "comments": 134},
        {"title": "Looking for a better way to track time for freelancers",
         "text": "Current tools are either too complicated or too expensive.",
         "subreddit": "freelance", "score": 243, "comments": 56},
    ]
    
    # 生成无效/噪声内容（这些应该被过滤掉）
    noise_templates = [
        {"title": "Just launched my new side project! Check it out",
         "text": "Built a habit tracking app. Looking for early feedback!",
         "subreddit": "SideProject", "score": 12, "comments": 3},
        {"title": "Showcase: My new portfolio website",
         "text": "What do you think of my new design?",
         "subreddit": "webdev", "score": 34, "comments": 8},
        {"title": "Free tool: Just made this for myself, thought I'd share",
         "text": "Free to use, no ads, etc.",
         "subreddit": "productivity", "score": 56, "comments": 12},
        {"title": "Job posting: We're hiring a junior developer",
         "text": "Full-time remote position. Apply within!",
         "subreddit": "forhire", "score": 7, "comments": 2},
        {"title": "Rant: Just had a terrible day",
         "text": "Needed to get this off my chest.",
         "subreddit": "reddit", "score": 23, "comments": 5},
    ]
    
    # 评论模板
    comment_templates = [
        ["me too!", "same here, this is so annoying", "exact same problem"],
        ["would also pay for this!", "take my money!", "I'd buy this immediately"],
        ["bump - need this too", "same issue here", "looking for the same"],
        ["this is exactly what I've been looking for", "finally someone else says it"],
    ]
    
    dataset = []
    
    # 1. 生成高价值痛点数据（约60条）
    for i in range(60):
        template = random.choice(templates)
        score = random.randint(50, 900)
        comments = random.randint(20, 180)
        
        post = {
            "title": template["title"],
            "text": template["text"],
            "score": score + (i % 5) * 100,
            "num_comments": comments + (i % 3) * 30,
            "subreddit": template["subreddit"],
            "url": f"https://reddit.com/r/{template['subreddit']}/comments/example{i}",
            "top_comments": random.choice(comment_templates)
        }
        dataset.append(post)
    
    # 2. 生成中等价值痛点（约25条）
    for i in range(25):
        titles = [
            "Is there a tool for this?",
            "Looking for alternatives",
            "This is frustrating",
            "Anyone else have this problem?",
        ]
        texts = [
            "Just wondering if anyone has a solution for this.",
            "Tired of doing this manually every week.",
            "Would appreciate any recommendations.",
            "So annoying having to do this over and over.",
        ]
        subreddits = ["productivity", "technology", "software", "askreddit", "webdev"]
        
        post = {
            "title": random.choice(titles),
            "text": random.choice(texts),
            "score": random.randint(20, 100),
            "num_comments": random.randint(5, 30),
            "subreddit": random.choice(subreddits),
            "url": f"https://reddit.com/r/{random.choice(subreddits)}/comments/medium{i}",
            "top_comments": ["interesting", "good question", "following"]
        }
        dataset.append(post)
    
    # 3. 生成噪声内容（约15条，这些应该被过滤）
    for i in range(15):
        template = random.choice(noise_templates)
        post = {
            "title": template["title"],
            "text": template["text"],
            "score": random.randint(5, 60),
            "num_comments": random.randint(2, 15),
            "subreddit": template["subreddit"],
            "url": f"https://reddit.com/r/{template['subreddit']}/comments/noise{i}",
            "top_comments": ["cool!", "nice", "looks good"]
        }
        dataset.append(post)
    
    # 打乱顺序
    random.shuffle(dataset)
    return dataset[:100]  # 确保正好100条

def run_large_demo():
    print("🎯 海外痛点挖掘系统 - 100条数据大规模演示")
    print("=" * 100)
    
    # 生成数据集
    print(f"\n📥 正在生成并分析 100 条真实感 Reddit 帖子数据...")
    dataset = generate_large_dataset()
    analyzer = PainpointAnalyzer()
    
    # 分析所有帖子
    valid_painpoints = []
    noise_count = 0
    
    for i, post in enumerate(dataset, 1):
        if i % 10 == 0:
            print(f"   处理进度: {i}/100 ({i}%)")
        
        result = analyzer.analyze_post(post)
        if result:
            valid_painpoints.append(result)
        else:
            noise_count += 1
    
    print(f"\n{'=' * 100}")
    print(f"📊 最终统计报告")
    print(f"{'=' * 100}")
    print(f"   总帖子数: 100")
    print(f"   有效痛点: {len(valid_painpoints)}")
    print(f"   噪声内容: {noise_count}")
    print(f"   命中率: {len(valid_painpoints)/100*100:.1f}%")
    
    # 按评分排序
    valid_painpoints.sort(key=lambda x: int(x["painpoint_summary"]["validation_score"][0]), reverse=True)
    
    # 显示 TOP 10 高价值痛点
    if valid_painpoints:
        print(f"\n{'=' * 100}")
        print(f"🏆 TOP 10 高价值微型资产机会（按评分排序）")
        print(f"{'=' * 100}")
        
        for i, p in enumerate(valid_painpoints[:10], 1):
            print(f"\n【{i}】⭐ {p['mvp_definition']['product_name']} ({p['painpoint_summary']['validation_score']})")
            print(f"   痛点: {p['painpoint_summary']['user_context'][:80]}...")
            print(f"   触发: {p['painpoint_summary']['trigger_keyword']}")
            print(f"   功能: {p['mvp_definition']['core_feature_only'][:60]}...")
            print(f"   定价: {p['monetization_route']['pricing_strategy']}")
            print(f"   来源: r/{p['source']['subreddit']}")
        
        # 显示评分分布
        print(f"\n{'=' * 100}")
        print(f"📈 评分分布")
        print(f"{'=' * 100}")
        
        score_dist = {}
        for p in valid_painpoints:
            score = p["painpoint_summary"]["validation_score"]
            score_dist[score] = score_dist.get(score, 0) + 1
        
        for score in sorted(score_dist.keys()):
            print(f"   {score}: {score_dist[score]} 个")
        
        # 保存完整 JSON 报告
        print(f"\n{'=' * 100}")
        print(f"💾 已保存完整分析报告到 painpoint_report.json")
        print(f"{'=' * 100}")
        
        with open("painpoint_report.json", "w", encoding="utf-8") as f:
            json.dump(valid_painpoints, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 演示完成！共发现 {len(valid_painpoints)} 个有价值的微型资产机会！")
        
        return valid_painpoints
    else:
        print("\n❌ 没有发现有效痛点")
        return []

if __name__ == "__main__":
    results = run_large_demo()
