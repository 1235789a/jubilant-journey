import asyncio
from scraper import RedditScraper
from analyzer import PainpointAnalyzer
import json

async def test_fetch():
    scraper = RedditScraper()
    analyzer = PainpointAnalyzer()
    
    print("🔍 开始从 Reddit 抓取数据...")
    print("=" * 60)
    
    try:
        # 抓取热门帖子
        posts = scraper.fetch_hot_posts(
            ["programming", "SaaS", "startups", "SideProject"],
            limit=20
        )
        
        print(f"✅ 成功抓取 {len(posts)} 条帖子\n")
        
        # 分析每个帖子
        painpoints = []
        for i, post in enumerate(posts, 1):
            print(f"📝 分析帖子 {i}/{len(posts)}: {post['title'][:50]}...")
            
            result = analyzer.analyze_post(post)
            if result:
                painpoints.append(result)
                print(f"   ✅ 发现痛点！评分: {result['painpoint_summary']['validation_score']}")
            else:
                print(f"   ⏭️  跳过（无有效痛点）")
        
        print("\n" + "=" * 60)
        print(f"📊 统计结果:")
        print(f"   总帖子数: {len(posts)}")
        print(f"   有效痛点数: {len(painpoints)}")
        print(f"   命中率: {len(painpoints)/len(posts)*100:.1f}%")
        
        if painpoints:
            print("\n" + "=" * 60)
            print("🎯 TOP 3 高价值痛点:")
            print("=" * 60)
            
            # 按评分排序（简化版：按点赞数）
            painpoints.sort(key=lambda x: x.get('source', {}).get('score', 0), reverse=True)
            
            for i, p in enumerate(painpoints[:3], 1):
                print(f"\n【{i}】{p['mvp_definition']['product_name']}")
                print(f"   评分: {p['painpoint_summary']['validation_score']}")
                print(f"   痛点: {p['painpoint_summary']['user_context'][:100]}...")
                print(f"   触发词: {p['painpoint_summary']['trigger_keyword']}")
                print(f"   现有方案: {p['competitor_analysis']['current_substitute']}")
                print(f"   核心功能: {p['mvp_definition']['core_feature_only']}")
                print(f"   定价: {p['monetization_route']['pricing_strategy']}")
                print(f"   来源: {p['source']['subreddit']}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("\n💡 提示: 如果看到认证错误，请确保已配置 Reddit API 密钥")
        print("   1. 访问 https://www.reddit.com/prefs/apps")
        print("   2. 创建应用并获取 client_id 和 client_secret")
        print("   3. 在 .env 文件中配置这些密钥")

if __name__ == "__main__":
    asyncio.run(test_fetch())
