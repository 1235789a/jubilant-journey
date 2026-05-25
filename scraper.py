import praw
import requests
from typing import List, Dict
from config import Config

class RedditScraper:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT
        )
    
    def fetch_hot_posts(self, subreddits: List[str], limit: int = 50) -> List[Dict]:
        posts = []
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                for submission in subreddit.hot(limit=limit):
                    post = {
                        "id": submission.id,
                        "title": submission.title,
                        "text": submission.selftext,
                        "score": submission.score,
                        "num_comments": submission.num_comments,
                        "url": submission.url,
                        "subreddit": subreddit_name,
                        "created_utc": submission.created_utc,
                        "top_comments": self._get_top_comments(submission)
                    }
                    posts.append(post)
            except Exception as e:
                print(f"Error fetching from r/{subreddit_name}: {e}")
        return posts
    
    def _get_top_comments(self, submission, limit: int = 10) -> List[str]:
        submission.comments.replace_more(limit=0)
        return [comment.body for comment in submission.comments[:limit]]


class ProductHuntScraper:
    def __init__(self):
        self.base_url = "https://api.producthunt.com/v2/api/graphql"
    
    def fetch_trending_products(self, limit: int = 50) -> List[Dict]:
        # 简化版，实际需要 ProductHunt API key
        return []
