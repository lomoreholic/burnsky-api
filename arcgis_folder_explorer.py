#!/usr/bin/env python3
"""
深入探索 CSDI ArcGIS Server 資料夾，尋找空氣品質服務

作者: BurnSky Team  
日期: 2025-01-27
"""

import requests
import json
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSDIArcGISExplorer:
    def __init__(self):
        self.base_url = "https://portal.csdi.gov.hk/server/rest/services"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def explore_folder(self, folder_name):
        """探索特定資料夾中的服務"""
        logger.info(f"=== 探索資料夾: {folder_name} ===")
        
        folder_url = f"{self.base_url}/{folder_name}?f=json"
        
        try:
            response = self.session.get(folder_url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', [])
                subfolders = data.get('folders', [])
                
                logger.info(f"資料夾 {folder_name} - 找到 {len(services)} 個服務, {len(subfolders)} 個子資料夾")
                
                # 探索服務
                for service in services:
                    service_name = service.get('name', 'unknown')
                    service_type = service.get('type', 'unknown')
                    
                    logger.info(f"  服務: {service_name} ({service_type})")
                    
                    # 檢查是否與空氣品質相關
                    air_keywords = ['air', 'quality', 'aqhi', 'epd', 'environment', 'pollution', 'monitoring']
                    if any(keyword.lower() in service_name.lower() for keyword in air_keywords):
                        logger.info(f"    ✓ 可能相關的空氣品質服務!")
                        self.explore_service(f"{folder_name}/{service_name}", service_type)
                
                # 探索子資料夾
                for subfolder in subfolders:
                    logger.info(f"  子資料夾: {subfolder}")
                    if any(keyword.lower() in subfolder.lower() for keyword in ['air', 'quality', 'epd', 'environment']):
                        logger.info(f"    ✓ 可能相關的子資料夾!")
                        self.explore_folder(f"{folder_name}/{subfolder}")
            else:
                logger.warning(f"無法訪問資料夾 {folder_name}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"探索資料夾 {folder_name} 時出錯: {e}")
    
    def explore_service(self, service_path, service_type):
        """探索特定服務的詳細資訊"""
        logger.info(f"    === 探索服務詳情: {service_path} ===")
        
        service_url = f"{self.base_url}/{service_path}?f=json"
        
        try:
            response = self.session.get(service_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 顯示服務基本資訊
                description = data.get('description', data.get('serviceDescription', ''))
                if description:
                    logger.info(f"      描述: {description}")
                
                # 檢查圖層
                layers = data.get('layers', [])
                tables = data.get('tables', [])
                
                logger.info(f"      找到 {len(layers)} 個圖層, {len(tables)} 個表格")
                
                for layer in layers:
                    layer_id = layer.get('id', 'unknown')
                    layer_name = layer.get('name', 'unknown')
                    logger.info(f"        圖層 {layer_id}: {layer_name}")
                    
                    # 檢查圖層是否與空氣品質相關
                    if any(keyword.lower() in layer_name.lower() for keyword in ['air', 'quality', 'aqhi', 'pollution']):
                        logger.info(f"          ✓ 空氣品質相關圖層!")
                        self.explore_layer(service_path, layer_id, layer_name)
                
                # 如果是 FeatureServer，檢查查詢能力
                if service_type == 'FeatureServer':
                    logger.info(f"      ✓ 這是 FeatureServer，支援數據查詢")
                    logger.info(f"      查詢 URL: {self.base_url}/{service_path}/query")
                
                # 如果是 MapServer，檢查 WFS 支援
                if service_type == 'MapServer':
                    wfs_url = f"{self.base_url}/{service_path}/WFSServer"
                    logger.info(f"      可能的 WFS URL: {wfs_url}")
                    
            else:
                logger.warning(f"      無法訪問服務: {response.status_code}")
                
        except Exception as e:
            logger.error(f"      探索服務時出錯: {e}")
    
    def explore_layer(self, service_path, layer_id, layer_name):
        """探索特定圖層的詳細資訊"""
        logger.info(f"          === 探索圖層: {layer_name} ===")
        
        layer_url = f"{self.base_url}/{service_path}/{layer_id}?f=json"
        
        try:
            response = self.session.get(layer_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 顯示圖層詳細資訊
                description = data.get('description', '')
                if description:
                    logger.info(f"            描述: {description}")
                
                # 顯示欄位資訊
                fields = data.get('fields', [])
                logger.info(f"            欄位數量: {len(fields)}")
                
                for field in fields[:10]:  # 只顯示前10個欄位
                    field_name = field.get('name', 'unknown')
                    field_type = field.get('type', 'unknown')
                    field_alias = field.get('alias', '')
                    
                    logger.info(f"              - {field_name} ({field_type}): {field_alias}")
                    
                    # 檢查欄位是否與空氣品質相關
                    if any(keyword.lower() in field_name.lower() or keyword.lower() in field_alias.lower() 
                           for keyword in ['aqhi', 'pm25', 'pm10', 'air', 'quality', 'pollution']):
                        logger.info(f"                ✓ 空氣品質相關欄位!")
                
                # 生成查詢 URL
                query_url = f"{self.base_url}/{service_path}/{layer_id}/query?where=1%3D1&outFields=*&f=json&resultRecordCount=1"
                logger.info(f"            樣本數據查詢 URL: {query_url}")
                
                # 嘗試獲取樣本數據
                self.get_sample_data(query_url)
                
            else:
                logger.warning(f"            無法訪問圖層: {response.status_code}")
                
        except Exception as e:
            logger.error(f"            探索圖層時出錯: {e}")
    
    def get_sample_data(self, query_url):
        """獲取樣本數據"""
        try:
            response = self.session.get(query_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])
                
                if features:
                    logger.info(f"            ✓ 成功獲取樣本數據 ({len(features)} 筆)")
                    
                    # 顯示第一筆數據的屬性
                    if features[0].get('attributes'):
                        attrs = features[0]['attributes']
                        logger.info("            樣本屬性:")
                        for key, value in list(attrs.items())[:5]:  # 只顯示前5個屬性
                            logger.info(f"              {key}: {value}")
                else:
                    logger.info("            無數據記錄")
            else:
                logger.warning(f"            無法獲取樣本數據: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"            獲取樣本數據時出錯: {e}")
    
    def run_comprehensive_exploration(self):
        """執行完整的資料夾探索"""
        logger.info("開始深入探索 CSDI ArcGIS Server")
        
        # 已知的資料夾
        folders = ['common', 'govt', 'Hosted', 'open', 'po', 'restrict', 'Utilities']
        
        # 優先探索最可能包含環保署數據的資料夾
        priority_folders = ['govt', 'open', 'common', 'Hosted']
        other_folders = [f for f in folders if f not in priority_folders]
        
        # 先探索優先資料夾
        for folder in priority_folders:
            self.explore_folder(folder)
            print("=" * 80)
        
        # 再探索其他資料夾
        for folder in other_folders:
            self.explore_folder(folder)
            print("=" * 80)
        
        logger.info("CSDI ArcGIS Server 探索完成")

def main():
    """主函數"""
    explorer = CSDIArcGISExplorer()
    explorer.run_comprehensive_exploration()

if __name__ == "__main__":
    main()
