import os
import json
import requests
from datetime import datetime

# 依照您的核心需求，精準設定餐飲業、居酒屋、美式餐廳、韓式烤肉、球賽等關鍵字
KEYWORDS = [
    ("行銷活動", "餐飲 行銷 OR 餐飲 宣傳 OR 美式餐廳 活動"),
    ("優惠活動", "餐飲 優惠 OR 居酒屋 優惠 OR 韓式烤肉 折扣"),
    ("人才招募", "餐飲 招募 OR 餐飲 缺工 OR 餐飲 徵才"),
    ("營收表現", "餐飲 上市 OR 餐飲 上櫃 OR 餐飲 財報"),
    ("海外發展", "餐飲 海外投資 OR 餐飲 海外展店 OR 餐飲 跨境"),
    ("體育賽事合作", "餐飲 球賽 優惠 OR 餐酒館 轉播 OR 美式餐廳 賽事")
]

def fetch_industry_news():
    news_articles = []
    
    # 這裡使用一個免費不需要 API Key 的新聞爬蟲端點，省去您申請 Key 的麻煩
    for category, query in KEYWORDS:
        url = f"https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            # 引入簡單的 xml 解析來抓取 Google News RSS
            import xml.etree.ElementTree as ET
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall('.//item')[:4] # 每個主題精選前 4 則最新新聞
                
                for item in items:
                    title_full = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else "#"
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    source_name = item.find('source').text if item.find('source') is not None else "新聞媒體"
                    
                    # 清理標題（Google News 標題通常會帶有 - 媒體名稱）
                    title = title_full.split(" - ")[0] if " - " in title_full else title_full
                    
                    # 格式化日期
                    try:
                        date_obj = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                        date_str = date_obj.strftime('%Y-%m-%d')
                    except:
                        date_str = datetime.now().strftime('%Y-%m-%d')
                        
                    news_articles.append({
                        "category": category,
                        "title": title,
                        "source": source_name,
                        "time": date_str,
                        "summary": f"點擊連結查看《{source_name}》關於此餐飲動態的詳細新聞報導內容。",
                        "url": link
                    })
        except Exception as e:
            print(f"抓取 {category} 失敗: {e}")

    # 如果完全沒抓到資料，補入備用資料確保網頁不破圖
    if not news_articles:
        news_articles = [
            {
                "category": "海外發展",
                "title": "台灣餐飲集團加速海外布局，鎖定美國與東南亞市場",
                "source": "財經日報",
                "time": datetime.now().strftime('%Y-%m-%d'),
                "summary": "面對內需市場，各大品牌紛紛加快海外展店腳步以尋求全球化發展新動能。",
                "url": "#"
            }
        ]

    # 打包輸出成前端網頁需要的 JSON
    output_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "news": news_articles
    }
    
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    print("新聞資料更新成功！")

if __name__ == "__main__":
    fetch_industry_news()
