#!/usr/bin/env python3
"""
解析 CSDI WFS GetCapabilities 回應，尋找空氣品質相關服務

作者: BurnSky Team  
日期: 2025-01-27
"""

import requests
import xml.etree.ElementTree as ET
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_wfs_capabilities():
    """解析 WFS GetCapabilities 回應"""
    
    # 測試已知的 WFS 端點
    test_url = "https://portal.csdi.gov.hk/server/services/common/landsd_rcd_1648571595120_89752/MapServer/WFSServer?service=WFS&request=GetCapabilities"
    
    try:
        response = requests.get(test_url, timeout=15)
        if response.status_code == 200:
            logger.info("成功獲取 WFS GetCapabilities")
            
            # 解析 XML
            root = ET.fromstring(response.text)
            
            # 定義命名空間
            namespaces = {
                'wfs': 'http://www.opengis.net/wfs/2.0',
                'ows': 'http://www.opengis.net/ows/1.1'
            }
            
            # 查找服務資訊
            service_identification = root.find('.//ows:ServiceIdentification', namespaces)
            if service_identification is not None:
                title = service_identification.find('ows:Title', namespaces)
                abstract = service_identification.find('ows:Abstract', namespaces)
                if title is not None:
                    logger.info(f"服務標題: {title.text}")
                if abstract is not None:
                    logger.info(f"服務描述: {abstract.text}")
            
            # 查找 FeatureType 列表
            feature_type_list = root.find('.//wfs:FeatureTypeList', namespaces)
            if feature_type_list is not None:
                logger.info("可用的 FeatureType:")
                for feature_type in feature_type_list.findall('.//wfs:FeatureType', namespaces):
                    name = feature_type.find('wfs:Name', namespaces)
                    title = feature_type.find('wfs:Title', namespaces)
                    if name is not None:
                        type_name = name.text
                        type_title = title.text if title is not None else "無標題"
                        logger.info(f"  - {type_name}: {type_title}")
                        
                        # 檢查是否包含空氣品質相關關鍵詞
                        air_keywords = ["air", "quality", "aqhi", "pollution", "monitoring", "epd", "environment"]
                        if any(keyword.lower() in type_name.lower() or 
                               keyword.lower() in type_title.lower() for keyword in air_keywords):
                            logger.info(f"    ✓ 可能相關的空氣品質數據: {type_name}")
            
            return True
        else:
            logger.error(f"無法獲取 GetCapabilities: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"解析 WFS GetCapabilities 時出錯: {e}")
        return False

def discover_wfs_services():
    """嘗試發現更多 WFS 服務"""
    logger.info("=== 嘗試發現其他 WFS 服務 ===")
    
    # 根據已知模式嘗試其他服務 ID
    base_pattern = "https://portal.csdi.gov.hk/server/services/common/{}/MapServer/WFSServer?service=WFS&request=GetCapabilities"
    
    # 可能的服務名稱
    potential_services = [
        "epd_air_quality",
        "epd_monitoring",
        "environment_data", 
        "air_monitoring_stations",
        "aqhi_data",
        "pollution_monitoring",
        "epd_aqhi",
        "hk_environment",
        "air_quality_index"
    ]
    
    for service_name in potential_services:
        url = base_pattern.format(service_name)
        try:
            logger.info(f"測試服務: {service_name}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"  ✓ 找到服務: {service_name}")
                
                # 快速檢查是否包含空氣品質相關內容
                content = response.text.lower()
                air_keywords = ["air", "quality", "aqhi", "pollution", "monitoring", "epd"]
                found_keywords = [kw for kw in air_keywords if kw in content]
                if found_keywords:
                    logger.info(f"    發現相關關鍵詞: {found_keywords}")
                    # 詳細解析這個服務
                    parse_specific_wfs(url, service_name)
            else:
                logger.debug(f"  ✗ 服務不存在: {service_name} (狀態碼: {response.status_code})")
                
        except Exception as e:
            logger.debug(f"  ✗ 測試 {service_name} 時出錯: {e}")

def parse_specific_wfs(url, service_name):
    """詳細解析特定的 WFS 服務"""
    try:
        response = requests.get(url, timeout=15)
        root = ET.fromstring(response.text)
        
        namespaces = {
            'wfs': 'http://www.opengis.net/wfs/2.0',
            'ows': 'http://www.opengis.net/ows/1.1'
        }
        
        logger.info(f"    === {service_name} 服務詳情 ===")
        
        # 查找所有 FeatureType
        feature_type_list = root.find('.//wfs:FeatureTypeList', namespaces)
        if feature_type_list is not None:
            for feature_type in feature_type_list.findall('.//wfs:FeatureType', namespaces):
                name = feature_type.find('wfs:Name', namespaces)
                title = feature_type.find('wfs:Title', namespaces)
                abstract = feature_type.find('wfs:Abstract', namespaces)
                
                if name is not None:
                    type_name = name.text
                    type_title = title.text if title is not None else ""
                    type_abstract = abstract.text if abstract is not None else ""
                    
                    logger.info(f"      FeatureType: {type_name}")
                    logger.info(f"      標題: {type_title}")
                    if type_abstract:
                        logger.info(f"      描述: {type_abstract}")
                    
                    # 生成測試數據查詢 URL
                    data_url = url.replace("?service=WFS&request=GetCapabilities", 
                                         f"?service=WFS&version=2.0.0&request=GetFeature&typename={type_name}&outputFormat=GeoJSON&count=1")
                    logger.info(f"      數據查詢 URL: {data_url}")
        
    except Exception as e:
        logger.error(f"    解析 {service_name} 服務時出錯: {e}")

def main():
    """主函數"""
    logger.info("開始探索 CSDI WFS 空氣品質服務")
    
    # 1. 解析已知的 WFS GetCapabilities
    if parse_wfs_capabilities():
        print("=" * 80)
        
        # 2. 嘗試發現其他 WFS 服務
        discover_wfs_services()
    
    logger.info("WFS 服務探索完成")

if __name__ == "__main__":
    main()
