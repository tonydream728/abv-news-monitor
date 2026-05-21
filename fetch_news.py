import xml.etree.ElementTree as ET
import requests
import os
import json
from datetime import datetime
import google.generativeai as genai

# 設定 Gemini AI
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

THEMES = {
    1: {"title": "1. 啤酒節與酒類活動", "sub_categories": ["台灣／海外啤酒節", "精釀啤酒活動", "品飲會", "酒吧活動", "啤酒品牌聯名", "餐廳與酒類合作"], "query": "啤酒節 OR 精釀啤酒活動 OR 品酒會 OR 酒吧活動 OR 啤酒聯名"},
    2: {"title": "2. 即時行銷議題", "sub_categories": ["節慶話題", "體育賽事", "社群熱門事件", "地區型活動", "旅遊／美食新聞", "可轉化為餐廳活動的話題"], "query": "餐飲 節慶話題 OR 運動賽事 餐廳 OR 餐廳 熱門事件 OR 美食新聞"},
    3: {"title": "3. 精釀啤酒市場", "sub_categories": ["精釀啤酒品牌動態", "新酒款上市", "酒廠合作", "啤酒風味趨勢", "消費者喝酒習慣"], "query": "精釀啤酒品牌 OR 新酒款上市 OR 酒廠合作 OR 啤酒趨勢"},
    4: {"title": "4. 餐飲會員經濟", "sub_categories": ["會員制度", "點數經濟", "訂閱制", "生日禮", "集點活動", "CRM / OMO 案例"], "query": "餐飲 會員制度 OR 餐飲 點數經濟 OR 餐廳 訂閱制 OR 餐廳 CRM"},
    5: {"title": "5. LINE會員與 Ocard", "sub_categories": ["LINE官方帳號", "Ocard會員系統", "餐飲品牌會員經營", "推播策略", "會員導流案例"], "query": "餐廳 LINE官方帳號 OR Ocard會員 OR LINE 推播策略"},
    6: {"title": "6. 世界盃與大型賽事餐飲話題", "sub_categories": ["世界盃餐廳活動", "運動酒吧", "賽事轉播", "票根活動", "球迷聚餐", "大型賽事即時行銷"], "query": "世界盃 餐廳 OR 運動酒吧 轉播 OR 餐廳 賽事轉播 OR 餐廳 票根活動"},
    7: {"title": "7. 社群爆紅餐廳與內容趨勢", "sub_categories": ["Threads熱門餐廳話題", "TikTok爆紅料理", "IG Reels餐飲內容", "YouTube Shorts美食影片", "KOL / 部落客合作案例"], "query": "Threads 餐廳話題 OR TikTok 爆紅料理 OR IG Reels 餐廳"},
    8: {"title": "8. 餐飲 AI 應用", "sub_categories": ["AI點餐", "AI客服", "AI會員分眾", "AI廣告投放", "AI菜單分析", "AI自動生成社群內容", "餐飲業自動化工具"], "query": "餐飲 AI點餐 OR 餐廳 AI客服 OR AI廣告投放 餐廳 OR 餐飲 自動化工具"}
}

def main():
    print("🚀 Agent 24/7: 開始巡邏全網搜集 8 大核心新聞...")
    raw_articles = []
    seen_urls = set()

    for tid, meta in THEMES.items():
        url = f"https://news.google.com/rss/search?q={meta['query']}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall('.//item')[:3]: 
                    link = item.find('link').text if item.find('link') is not None else "#"
                    if link in seen_urls: continue
                    seen_urls.add(link)
                    
                    title_full = item.find('title').text if item.find('title') is not None else ""
                    title = title_full.split(" - ")[0] if " - " in title_full else title_full
                    source = item.find('source').text if item.find('source') is not None else "新聞媒體"
                    
                    raw_articles.append({"theme_id": tid, "title": title, "source": source, "url": link})
        except Exception as e:
            print(f"主題 {tid} 抓取失敗: {e}")

    print(f"🧠 AI 特助開始進行『ABV 實戰轉化率』過濾...")
    
    structured_themes = []
    for tid, meta in THEMES.items():
        structured_themes.append({
            "id": tid,
            "title": meta["title"],
            "sub_categories": meta["sub_categories"],
            "news_count": 0,
            "articles": []
        })

    # 對接 2026 年最新一代主力大腦
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt_template = """
    你是一位精通餐飲產業與數位行銷的 AI 戰略特助。請幫我評估以下新聞對於「ABV 餐廳集團（分店包含餐酒館、居酒屋、美式餐廳、韓式烤肉，主打世界精釀啤酒文化與世界傳統料理，消費者不吃牛羊）」的轉化價值。
    
    新聞標題: %s

    【🎯 核心過濾機制】：
    請嚴格判斷這件事能否被 ABV 用來做「即時行銷、會員活動、社群內容、廣告素材、門市活動、品牌合作或美食季企劃」。
    - 如果能高度轉化，請給予 4-5 分的高分。
    - 如果無法轉化操作或不具備實戰意義，請直接降低評分至 1-2 分。

    請嚴格依照 JSON 格式回傳，回傳的字串開頭與結尾絕對不要包含任何 ```json 或 ``` 標籤，只要純 JSON 內容：
    {
        "sub_tag": "從這組子項目中選一個最貼切的：%s",
        "score": 1-5整數,
        "summary": "60字內繁體核心摘要",
        "action_tags": ["從上述即時行銷、門市活動、社群內容、廣告素材、會員活動、品牌合作、美食季企劃中選出符合的"],
        "abv_suggestion": "高價值實戰方針。說明 ABV 門市或社群小編可以怎麼直接照著這則新聞來操作（例如：推出某某票根活動、在 Threads 發起什麼話題、在 Ocard 設定什麼活動，請精準切入）"
    }
    """

    for art in raw_articles[:12]: 
        try:
            tid = art["theme_id"]
            subs_str = ", ".join(THEMES[tid]["sub_categories"])
            prompt = prompt_template % (art['title'], subs_str)
            
            response = model.generate_content(prompt)
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            ai_res = json.loads(clean_text)
            
            idx = tid - 1
            structured_themes[idx]["articles"].append({
                "sub_tag": ai_res.get("sub_tag", "產業動態"),
                "title": art["title"],
                "source": art["source"],
                "url": art["url"],
                "score": ai_res.get("score", 3),
                "summary": ai_res.get("summary", ""),
                "action_tags": ai_res.get("action_tags", ["門市活動"]),
                "abv_suggestion": ai_res.get("abv_suggestion", "密切觀察市場動態。")
            })
            structured_themes[idx]["news_count"] += 1
        except Exception as e:
            print(f"AI 剖析失敗: {e}")

    os.makedirs('data', exist_ok=True)
    with open('data/daily_report.json', 'w', encoding='utf-8') as f:
        json.dump({"themes": structured_themes}, f, ensure_ascii=False, indent=4)
    print("🎯 【24/7 Agent 任務交付】8大主題下拉資料已順利寫入 data/daily_report.json。")

if __name__ == "__main__":
    main()
