#!/usr/bin/env python3
"""
查找 2022-2025 年所有辽宁高考普通类本科批投档最低分文件的下载链接
"""
import re
import urllib3
from bs4 import BeautifulSoup
import requests

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.lnzsks.com"

def find_announcements():
    announcements = {}
    
    # 爬取前 10 页新闻列表
    for page in range(1, 11):
        url = f"{BASE_URL}/listinfo/NewsList_1104_{page}.html"
        print(f"Scraping list page {page}: {url} ...")
        try:
            r = requests.get(url, verify=False, timeout=10)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            
            # 寻找链接
            for a in soup.find_all("a", href=True):
                text = a.get_text().strip()
                href = a["href"].strip()
                
                # 检查是否包含关键词 "普通类本科批" 和 "最低分" 且是正常志愿批，排除 "征集志愿"
                if "本科批" in text and "投档最低分" in text and "普通类" in text and "征集志愿" not in text:
                    # 匹配年份
                    match_year = re.search(r"202[2-5]年", text)
                    if match_year:
                        year = match_year.group(0)[:4]
                        if year not in announcements:
                            # 拼接完整 URL
                            if href.startswith("http"):
                                full_url = href
                            elif href.startswith("../"):
                                full_url = BASE_URL + href[2:]
                            else:
                                full_url = BASE_URL + "/newsinfo/" + href
                            
                            announcements[year] = {
                                "title": text,
                                "url": full_url
                            }
                            print(f"  Found {year} announcement: {text} -> {full_url}")
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            
    return announcements

def find_download_links(announcements):
    download_links = {}
    for year, info in announcements.items():
        print(f"\nScraping announcement page for {year}: {info['url']} ...")
        try:
            r = requests.get(info["url"], verify=False, timeout=10)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            
            download_links[year] = []
            
            # 寻找下载附件的链接
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                text = a.get_text().strip()
                
                # 寻找包含物理类 or 历史类 or zip/xlsx 的下载链接
                if any(ext in href.lower() for ext in [".zip", ".xlsx", ".xls", ".rar"]):
                    # 拼接完整下载链接
                    if href.startswith("http"):
                        dl_url = href
                    elif href.startswith("../"):
                        dl_url = BASE_URL + href[2:]
                    else:
                        dl_url = BASE_URL + "/newsinfo/" + href
                        
                    # 判断分类
                    category = "未知"
                    if "物理" in text or "物理" in href:
                        category = "物理类"
                    elif "历史" in text or "历史" in href:
                        category = "历史类"
                        
                    download_links[year].append({
                        "category": category,
                        "text": text,
                        "url": dl_url
                    })
                    print(f"  Found download link ({category}): {text} -> {dl_url}")
        except Exception as e:
            print(f"Error scraping announcement page {info['url']}: {e}")
            
    return download_links

def main():
    print("==================================================")
    print(" 开始爬取 2022-2025 投档最低分官方链接 ")
    print("==================================================")
    
    announcements = find_announcements()
    download_links = find_download_links(announcements)
    
    print("\n" + "="*50)
    print(" 汇总结果 ")
    print("="*50)
    for year, links in sorted(download_links.items()):
        print(f"\n年份: {year} 年")
        for link in links:
            print(f"  - [{link['category']}] {link['text']}")
            print(f"    URL: {link['url']}")
            
if __name__ == "__main__":
    main()
