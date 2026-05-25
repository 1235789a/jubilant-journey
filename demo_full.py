from analyzer import PainpointAnalyzer
import json

def demo_with_realistic_data():
    analyzer = PainpointAnalyzer()
    
    print("🎯 海外痛点挖掘系统 - 完整演示")
    print("=" * 80)
    
    # 模拟真实 Reddit 帖子数据
    realistic_posts = [
        {
            "title": "I'd pay $20/month for a tool that automatically backs up my Notion pages",
            "text": "I lost 3 months of work when Notion went down last week. Is there a paid tool that automatically backs up all my Notion pages to Google Drive? I've looked at the built-in export feature but it's manual and tedious.",
            "score": 847,
            "num_comments": 156,
            "subreddit": "Notion",
            "url": "https://reddit.com/r/Notion/comments/example1",
            "top_comments": [
                "me too! Lost all my meeting notes",
                "same here, this is a huge pain",
                "I'd pay for this instantly",
                "exactly what I need",
                "please someone build this"
            ]
        },
        {
            "title": "Is there a tool that converts all my Calendar events to PDF invoices?",
            "text": "I'm a freelance consultant and I spend 4 hours every Friday manually converting my calendar events into invoices. Looking for a tool that automates this. I'd pay for something that saves me this time.",
            "score": 423,
            "num_comments": 87,
            "subreddit": "freelance",
            "url": "https://reddit.com/r/freelance/comments/example2",
            "top_comments": [
                "I do the same thing, so frustrating",
                "same here!",
                "bump - need this too",
                "would be willing to pay for this"
            ]
        },
        {
            "title": "I hate how hard it is to organize my browser bookmarks",
            "text": "I've tried everything - Pocket, Raindrop, native bookmarks. Nothing works. Every tool is either too complex or doesn't sync properly. Why is this still so hard in 2024?",
            "score": 234,
            "num_comments": 45,
            "subreddit": "technology",
            "url": "https://reddit.com/r/technology/comments/example3",
            "top_comments": [
                "exactly my problem",
                "same here for years",
                "this!"
            ]
        },
        {
            "title": "Any alternative to Notion for simple note-taking?",
            "text": "Notion is too bloated for me. I just need to write notes and sometimes share them. Is there a lightweight alternative that actually works?",
            "score": 67,
            "num_comments": 23,
            "subreddit": "productivity",
            "url": "https://reddit.com/r/productivity/comments/example4",
            "top_comments": [
                "Obsidian?",
                "I use Bear",
                "Standard Notes is good"
            ]
        },
        {
            "title": "Just launched my new side project!",
            "text": "Check out my new app for tracking habits. Looking for feedback from early users.",
            "score": 12,
            "num_comments": 3,
            "subreddit": "SideProject",
            "url": "https://reddit.com/r/SideProject/comments/example5",
            "top_comments": [
                "cool!",
                "nice design"
            ]
        }
    ]
    
    print(f"\n📥 模拟抓取 {len(realistic_posts)} 条真实 Reddit 帖子...\n")
    
    painpoints = []
    for i, post in enumerate(realistic_posts, 1):
        print(f"🔍 分析帖子 {i}/{len(realistic_posts)}: {post['title'][:50]}...")
        print(f"   评分: {post['score']} 赞, {post['num_comments']} 评论")
        
        result = analyzer.analyze_post(post)
        if result:
            painpoints.append(result)
            print(f"   ✅ 【有效痛点】评分: {result['painpoint_summary']['validation_score']}")
        else:
            print(f"   ⏭️  跳过（非有效商业痛点）")
        print()
    
    print("=" * 80)
    print(f"📊 最终统计:")
    print(f"   总帖子数: {len(realistic_posts)}")
    print(f"   有效痛点: {len(painpoints)}")
    print(f"   命中率: {len(painpoints)/len(realistic_posts)*100:.0f}%")
    
    if painpoints:
        print("\n" + "=" * 80)
        print("🏆 发现的高价值微型资产机会:")
        print("=" * 80)
        
        for i, p in enumerate(painpoints, 1):
            print(f"\n{'='*80}")
            print(f"【机会 {i}】🎯 {p['mvp_definition']['product_name']}")
            print(f"{'='*80}")
            
            print(f"\n📌 痛点摘要:")
            print(f"   用户场景: {p['painpoint_summary']['user_context'][:120]}")
            print(f"   触发关键词: {p['painpoint_summary']['trigger_keyword']}")
            print(f"   验证评分: {p['painpoint_summary']['validation_score']} ⭐")
            
            print(f"\n🔍 竞品分析:")
            print(f"   现有笨办法: {p['competitor_analysis']['current_substitute']}")
            print(f"   核心缺点: {p['competitor_analysis']['substitute_flaws']}")
            
            print(f"\n🚀 MVP 定义:")
            print(f"   产品名称: {p['mvp_definition']['product_name']}")
            print(f"   核心功能: {p['mvp_definition']['core_feature_only']}")
            print(f"   技术栈: {p['mvp_definition']['tech_stack_suggestion']}")
            
            print(f"\n💰 变现方案:")
            print(f"   定价策略: {p['monetization_route']['pricing_strategy']}")
            print(f"   引流钩子: {p['monetization_route']['traffic_hook']}")
            
            print(f"\n📍 数据来源:")
            print(f"   子版块: r/{p['source']['subreddit']}")
            print(f"   原帖: {p['source']['url']}")
            
            print(f"\n💎 JSON 输出:")
            print(json.dumps(p, indent=2, ensure_ascii=False))
    
    return painpoints

if __name__ == "__main__":
    painpoints = demo_with_realistic_data()
    
    print("\n\n" + "=" * 80)
    print("💡 系统工作原理:")
    print("=" * 80)
    print("""
1. 【噪声过滤】系统自动过滤以下无效内容：
   - 情绪发泄帖（无明确痛点）
   - 已有垄断解决方案的需求
   - 需要重度人工服务的需求
   
2. 【黄金信号检测】识别五大高价值信号：
   - 💰 愿付标签: "I'd pay for..." / "would pay"
   - 😤 崩溃标签: "frustrated with..." / "I hate..."
   - 🔍 寻找标签: "is there a tool..." / "any alternative..."
   - 👥 抱团信号: 50+赞 + 20+评论 + "me too"/"same here"
   
3. 【微型资产定义】生成可执行方案：
   - 产品名称（直击痛点）
   - 核心功能（24小时内可开发）
   - 定价策略（$19-29 单次买断）
   - 引流钩子（可直接复制的文案）
    """)
