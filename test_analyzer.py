from analyzer import PainpointAnalyzer

def test_painpoint_analyzer():
    analyzer = PainpointAnalyzer()
    
    # 测试用例 1: 包含付费意愿的帖子
    test_post_1 = {
        "title": "I'd pay for a tool that automates this tedious task",
        "text": "Every day I have to manually export data from 5 different tools and combine them in Excel. It takes 2 hours. I'd pay for a tool that does this automatically.",
        "score": 120,
        "num_comments": 45,
        "url": "https://reddit.com/test",
        "subreddit": "programming",
        "top_comments": ["me too!", "same here, this is so annoying"]
    }
    
    result = analyzer.analyze_post(test_post_1)
    print("=== 测试 1 ===")
    if result:
        print("✅ 成功检测到痛点")
        print(f"评分: {result['painpoint_summary']['validation_score']}")
        print(f"产品名称: {result['mvp_definition']['product_name']}")
    else:
        print("❌ 未检测到痛点")
    
    # 测试用例 2: 包含崩溃标签的帖子
    test_post_2 = {
        "title": "I hate this product with a passion",
        "text": "I'm so frustrated with the new interface. It's slow, buggy, and completely unusable.",
        "score": 80,
        "num_comments": 25,
        "url": "https://reddit.com/test2",
        "subreddit": "SaaS",
        "top_comments": ["exactly!", "can't stand it either"]
    }
    
    result = analyzer.analyze_post(test_post_2)
    print("\n=== 测试 2 ===")
    if result:
        print("✅ 成功检测到痛点")
        print(f"评分: {result['painpoint_summary']['validation_score']}")
        print(f"触发词: {result['painpoint_summary']['trigger_keyword']}")
    else:
        print("❌ 未检测到痛点")
    
    # 测试用例 3: 普通帖子（应该被忽略）
    test_post_3 = {
        "title": "Just wanted to share my project",
        "text": "Here's what I've been working on lately. Check it out!",
        "score": 10,
        "num_comments": 5,
        "url": "https://reddit.com/test3",
        "subreddit": "general",
        "top_comments": []
    }
    
    result = analyzer.analyze_post(test_post_3)
    print("\n=== 测试 3 ===")
    if result is None:
        print("✅ 正确忽略普通帖子")
    else:
        print("❌ 错误：不应该检测到痛点")

if __name__ == "__main__":
    test_painpoint_analyzer()
