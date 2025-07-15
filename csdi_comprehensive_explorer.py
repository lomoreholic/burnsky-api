#!/usr/bin/env python3
"""
探索 CSDI 門戶的實際服務目錄和數據集

作者: BurnSky Team  
日期: 2025-01-27
"""

import requests
import json
import logging
import re
from urllib.parse import urlparse, parse_qs

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSDIServiceExplorer:
    def __init__(self):
        self.base_url = "https://portal.csdi.gov.hk"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8'
        })
    
    def explore_arcgis_services(self):
        """探索 ArcGIS Server 服務目錄"""
        logger.info("=== 探索 ArcGIS Server 服務目錄 ===")
        
        # ArcGIS Server REST 端點
        arcgis_endpoints = [
            f"{self.base_url}/server/rest/services",
            f"{self.base_url}/server/rest/services?f=json",
            f"{self.base_url}/server/services",
            f"{self.base_url}/arcgis/rest/services",
        ]
        
        for endpoint in arcgis_endpoints:
            try:
                logger.info(f"測試 ArcGIS 端點: {endpoint}")
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"  ✓ 成功訪問: {response.status_code}")
                    content_type = response.headers.get('content-type', '')
                    
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            logger.info(f"  JSON 結構: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                            
                            # 查找服務列表
                            if isinstance(data, dict):
                                services = data.get('services', [])
                                folders = data.get('folders', [])
                                
                                if services:
                                    logger.info(f"  找到 {len(services)} 個服務:")
                                    for service in services[:10]:  # 只顯示前10個
                                        name = service.get('name', 'unknown')
                                        service_type = service.get('type', 'unknown')
                                        logger.info(f"    - {name} ({service_type})")
                                        
                                        # 檢查是否與空氣品質相關
                                        if any(keyword in name.lower() for keyword in ['air', 'quality', 'epd', 'environment', 'pollution']):
                                            logger.info(f"      ✓ 可能相關的服務: {name}")
                                
                                if folders:
                                    logger.info(f"  找到 {len(folders)} 個資料夾: {folders}")
                                    
                        except json.JSONDecodeError:
                            logger.info("  回應不是有效的 JSON，顯示內容預覽:")
                            content = response.text[:500]
                            logger.info(f"  內容: {content}")
                    else:
                        content = response.text[:500]
                        logger.info(f"  非 JSON 內容: {content}")
                else:
                    logger.warning(f"  ✗ 無法訪問: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"  ✗ 測試時出錯: {e}")
            
            print("-" * 60)
    
    def explore_data_query_endpoints(self):
        """探索數據查詢端點"""
        logger.info("=== 探索數據查詢端點 ===")
        
        # 根據 CSDI 文檔嘗試不同的數據查詢格式
        query_endpoints = [
            f"{self.base_url}/api/datasets",
            f"{self.base_url}/api/v1/datasets", 
            f"{self.base_url}/dqs/api",  # Data Query Service
            f"{self.base_url}/api/catalog",
            f"{self.base_url}/catalog/api",
        ]
        
        for endpoint in query_endpoints:
            try:
                logger.info(f"測試查詢端點: {endpoint}")
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"  ✓ 成功訪問: {response.status_code}")
                    
                    try:
                        data = response.json()
                        logger.info(f"  JSON 結構: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        
                        # 查找數據集
                        if isinstance(data, dict):
                            if 'datasets' in data:
                                datasets = data['datasets']
                                logger.info(f"  找到 {len(datasets)} 個數據集")
                                for dataset in datasets[:5]:
                                    title = dataset.get('title', dataset.get('name', 'unknown'))
                                    logger.info(f"    - {title}")
                            
                    except json.JSONDecodeError:
                        content = response.text[:500]
                        logger.info(f"  非 JSON 內容: {content}")
                else:
                    logger.debug(f"  ✗ 無法訪問: {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"  ✗ 測試時出錯: {e}")
    
    def search_environment_datasets(self):
        """搜索環境相關數據集"""
        logger.info("=== 搜索環境數據集 ===")
        
        # 嘗試不同的搜索端點
        search_patterns = [
            f"{self.base_url}/api/search?q=environment",
            f"{self.base_url}/api/search?q=air+quality",
            f"{self.base_url}/api/v1/search?query=EPD",
            f"{self.base_url}/search/api?keyword=air",
            f"{self.base_url}/catalog/search?q=environment",
        ]
        
        for pattern in search_patterns:
            try:
                logger.info(f"搜索: {pattern}")
                response = self.session.get(pattern, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"  ✓ 搜索成功")
                    
                    try:
                        data = response.json()
                        if isinstance(data, dict) and 'results' in data:
                            results = data['results']
                            logger.info(f"  找到 {len(results)} 個結果")
                            for result in results[:3]:
                                title = result.get('title', 'unknown')
                                description = result.get('description', '')[:100]
                                logger.info(f"    - {title}: {description}")
                        else:
                            logger.info(f"  回應結構: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    except json.JSONDecodeError:
                        logger.info("  非 JSON 回應")
                else:
                    logger.debug(f"  ✗ 搜索失敗: {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"  ✗ 搜索時出錯: {e}")
    
    def check_known_apis(self):
        """檢查已知的政府 API 端點"""
        logger.info("=== 檢查已知政府 API ===")
        
        # 檢查其他政府部門的 API
        government_apis = [
            # data.gov.hk 的實際 API 端點
            "https://api.data.gov.hk/v1/datasets",
            "https://api.data.gov.hk/v2/search?q=air+quality",
            
            # 環保署可能的端點
            "https://www.aqhi.gov.hk/api/aqhi/current.json",
            "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_Eng.json",
            "https://www.epd.gov.hk/epd/tc_chi/environmentinhk/air/data/api/aqhi.json",
            
            # OneMAP 政府地圖服務
            "https://www.onemap.gov.hk/api/common/elastic/search?searchVal=air+quality",
        ]
        
        for api_url in government_apis:
            try:
                logger.info(f"檢查: {api_url}")
                response = self.session.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"  ✓ 可訪問: {response.status_code}")
                    
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            logger.info(f"  JSON 結構: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                            
                            # 檢查是否包含空氣品質數據
                            content_str = str(data).lower()
                            air_keywords = ["aqhi", "pm2.5", "air quality", "pollution"]
                            found = [kw for kw in air_keywords if kw in content_str]
                            if found:
                                logger.info(f"    ✓ 發現空氣品質相關內容: {found}")
                                logger.info(f"    數據樣本: {str(data)[:200]}")
                        except json.JSONDecodeError:
                            content = response.text[:300]
                            logger.info(f"  非 JSON 內容: {content}")
                    else:
                        content = response.text[:300]
                        logger.info(f"  內容預覽: {content}")
                else:
                    logger.debug(f"  ✗ 無法訪問: {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"  ✗ 檢查時出錯: {e}")
            
            print("-" * 40)
    
    def run_comprehensive_exploration(self):
        """執行完整探索"""
        logger.info("開始 CSDI 服務全面探索")
        print("=" * 80)
        
        # 1. 探索 ArcGIS 服務
        self.explore_arcgis_services()
        print("=" * 80)
        
        # 2. 探索數據查詢端點
        self.explore_data_query_endpoints()
        print("=" * 80)
        
        # 3. 搜索環境數據集
        self.search_environment_datasets()
        print("=" * 80)
        
        # 4. 檢查已知政府 API
        self.check_known_apis()
        print("=" * 80)
        
        logger.info("CSDI 服務探索完成")

def main():
    """主函數"""
    explorer = CSDIServiceExplorer()
    explorer.run_comprehensive_exploration()

if __name__ == "__main__":
    main()
