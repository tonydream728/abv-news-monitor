import xml.etree.ElementTree as ET
import requests
import os
import json
from datetime import datetime, timedelta
import google.generativeai as genai

# 設定 Gemini AI
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 擴大搜集來源：餐飲、生活、消費、啤酒趨勢
QUERIES = [
    "啤酒節 OR 精釀啤酒 OR 餐廳活動",
    "餐飲 節慶話題 OR 運動賽事 餐廳 OR 餐廳 熱門事件",
    "餐廳 LINE官方帳號 OR Ocard會員 OR 餐飲 會員制度",
    "Threads 餐廳話題 OR TikTok 爆紅料理 OR IG Reels 餐廳",
    "餐飲 AI OR 餐廳 自動化 OR 數位行銷 餐廳"
]

def main():
    print("🚀 [Agent 24/7] 開始巡邏全網搜集即時餐飲、生活消費情報...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 讀取現有資料（為了滾動累積歷史新聞）
    data_filepath = 'daily_report.json'
    os.makedirs('data', exist_ok=True)
    
    if os.path.exists(data_filepath):
        try:
            with open(data_filepath, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        except:
            old_data = {"today_news": [], "history_news": [], "social_actions": [], "marketing_strategies": []}
    else:
        old_data = {"today_news": [], "history_news": [], "social_actions": [], "marketing_strategies": []}

    # 1. 抓取今日最新新聞
    seen_urls = set()
    raw_articles = []
    
    for q in QUERIES:
        url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall('.//item')[:4]:
                    link = item.find('link').text if item.find('link') is not None else "#"
                    if link in seen_urls: continue
                    seen_urls.add(link)
                    title_full = item.find('title').text if item.find('title') is not None else ""
                    title = title_full.split(" - ")[0] if " - " in title_full else title_full
                    source = item.find('source').text if item.find('source') is not None else "新聞媒體"
                    raw_articles.append({"title": title, "source": source, "url": link, "date": today_str})
        except Exception as e:
            print(f"抓取失敗: {e}")

    print("🧠 [AI 戰略特助] 開始進行四大區塊重組分析...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 整合今日新聞作為 AI 上下文
    news_context = "\n".join([f"- {a['title']} ({a['source']})" for a in raw_articles[:10]])

    prompt = f"""
    你是一位精通餐飲產業與數位行銷的 AI 頂級戰略特助。
    請針對以下今日搜集到的餐飲、消費、社群即時新聞，為「ABV 餐廳集團（擁有13家分店，包含地中海餐酒館、加勒比海餐酒館、美式餐廳、日式居酒屋、韓式烤肉。主打世界精釀啤酒文化與世界傳統傳統料理。注意：消費者不吃牛羊）」進行商業情報轉化。

    今日即時新聞：
    {news_context}

    請嚴格依照以下四個區塊的需求，進行過濾與策略發想。
    
    請嚴格依照 JSON 格式回傳，開頭與結尾絕對不要包含任何 ```json 或 ``` 標籤：
    {{
        "today_news": [
            {{
                "title": "挑選出最相關的今日新聞標題",
                "source": "媒體來源",
                "url": "保留對應網址",
                "score": 1-5評分(若無法轉化為ABV操作請給低分，能高度操作給高分),
                "summary": "50字內繁體核心摘要",
                "abv_suggestion": "高價值實戰方針。說明 ABV 門市或社群小編可以怎麼直接照著這則新聞來操作（例如：推出某某票根活動、在 Threads 發起什麼話題、在 Ocard 設定什麼活動，請精準切入）"
            }}
        ],
        "social_actions": [
            {{
                "target_platform": "Threads / IG Reels / LINE / FB",
                "related_topic": "關聯的核心議題",
                "copywriting_angle": "社群切入點說明（例如：如何利用脆上的不吃牛羊多人聚餐話題）",
                "action_script": "直接可以抄去發文的草稿文案、或是影音腳本大綱（繁體中文，語氣口語、有行銷渲染力）"
            }}
        ],
        "marketing_strategies": [
            {{
                "strategy_title": "活動/企劃名稱（例如：大巨蛋觀賽票根聯動、微醺美食季企劃）",
                "type": "門市集點活動 / Ocard 會員活動 / 品牌聯名 / 主題美食季企劃",
                "target_audience": "鎖定客群",
                "execution_plan": "100字內精準門市落地執行步驟說明"
            }}
        ]
    }}
    """

    # 預防 AI 吐出錯誤 JSON 的安全機制
    today_news_processed = []
    social_actions = []
    marketing_strategies = []
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        ai_res = json.loads(clean_text)
        today_news_processed = ai_res.get("today_news", [])
        social_actions = ai_res.get("social_actions", [])
        marketing_strategies = ai_res.get("marketing_strategies", [])
    except Exception as e:
        print(f"AI 戰略大腦建構失敗: {e}")
        # 備用保底資料
        today_news_processed = [{"title": "今日暫無高價值轉化情報", "source": "系統", "url": "#", "score": 3, "summary": "無摘要", "abv_suggestion": "保持日常行銷排程。"}]

    # 2. 歷史新聞滾動管理（將昨天的今日新聞移入歷史，且只保留過去 7 天）
    history_news = old_data.get("history_news", [])
    
    # 把舊資料中，屬於昨天的今日新聞合併進歷史紀錄
    if old_data.get("today_news"):
        for old_n in old_data["today_news"]:
            if old_n.get("title") and old_n["title"] != "今日暫無高價值轉化情報":
                # 避免重複
                if old_n["title"] not in [h["title"] for h in history_news]:
                    history_news.append(old_n)

    # 篩選掉超過 7 天的歷史新聞
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    history_news = [h for h in history_news if h.get("date", today_str) >= seven_days_ago]

    # 3. 儲存最新成果
    final_output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "today_news": today_news_processed,
        "history_news": history_news,
        "social_actions": social_actions,
        "marketing_strategies": marketing_strategies
    }

    with open(data_filepath, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
    print("🎯 [24/7 Agent] 四大核心區塊資料已完美寫入 daily_report.json！")

if __name__ == "__main__":
    main()
