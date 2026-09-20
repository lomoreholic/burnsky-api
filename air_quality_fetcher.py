"""
香港空氣品質數據獲取器
支援多個數據來源：環保署 AQHI、第三方 API、模擬數據

作者: BurnSky Team
日期: 2025-07-15
"""

import requests
import json
import logging
from datetime import datetime, timedelta
import pytz

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityFetcher:
    def __init__(self):
        self.hk_tz = pytz.timezone('Asia/Hong_Kong')
        
        # 空氣品質健康指數 (AQHI) 等級對照表
        self.aqhi_levels = {
            1: {"level": "低", "color": "#00FF00", "description": "空氣品質良好"},
            2: {"level": "低", "color": "#00FF00", "description": "空氣品質良好"},
            3: {"level": "低", "color": "#00FF00", "description": "空氣品質良好"},
            4: {"level": "中", "color": "#FFFF00", "description": "空氣品質一般"},
            5: {"level": "中", "color": "#FFFF00", "description": "空氣品質一般"},
            6: {"level": "中", "color": "#FFFF00", "description": "空氣品質一般"},
            7: {"level": "高", "color": "#FF8C00", "description": "空氣品質欠佳"},
            8: {"level": "高", "color": "#FF4500", "description": "空氣品質欠佳"},
            9: {"level": "高", "color": "#FF4500", "description": "空氣品質欠佳"},
            10: {"level": "甚高", "color": "#FF0000", "description": "空氣品質很差"},
            11: {"level": "嚴重", "color": "#8B0000", "description": "空氣品質極差"}
        }
        
        # 主要監測站
        self.monitoring_stations = {
            "central": "中環",
            "causeway_bay": "銅鑼灣",
            "tsim_sha_tsui": "尖沙咀",
            "sham_shui_po": "深水埗",
            "kwun_tong": "觀塘",
            "tai_po": "大埔",
            "tuen_mun": "屯門",
            "tung_chung": "東涌",
            "tap_mun": "塔門",
            "hok_tsui": "石澳",
            "sha_tin": "沙田",
            "kwai_chung": "葵涌",
            "tsuen_wan": "荃灣",
            "yuen_long": "元朗"
        }
    
    def get_current_air_quality(self):
        """
        獲取當前空氣品質數據
        嘗試多個數據源，最後使用基於天氣的估算
        """
        # 優先嘗試 CSDI 官方 API
        try:
            return self._fetch_csdi_data()
        except Exception as e:
            logger.warning(f"CSDI API 失敗: {e}")
        
        # 嘗試環保署官方 API
        try:
            return self._fetch_epd_data()
        except Exception as e:
            logger.warning(f"環保署 API 失敗: {e}")
        
        # 嘗試第三方 API
        try:
            return self._fetch_third_party_data()
        except Exception as e:
            logger.warning(f"第三方 API 失敗: {e}")
        
        # 使用基於天氣的估算
        logger.info("使用天氣估算空氣品質")
        return self._estimate_air_quality()
    
    def _fetch_csdi_data(self):
        """
        從 CSDI (Common Spatial Data Infrastructure) 獲取空氣品質數據
        這是香港政府空間數據共享平台的官方 API
        """
        try:
            # CSDI 數據查詢 API
            csdi_url = "https://api.csdi.gov.hk/apim/dataquery/api/"
            params = {
                "id": "epd_rcd_1633316466897_94368",  # 環保署空氣品質監測網絡數據集
                "layer": "aqmn",  # Air Quality Monitoring Network
                "limit": 20,
                "offset": 0
            }
            
            response = requests.get(csdi_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # 解析監測站數據
                features = data.get('features', [])
                if not features:
                    raise Exception("CSDI API 返回空數據")
                
                # 選擇中環或銅鑼灣監測站（香港島中心區域）
                central_stations = []
                for feature in features:
                    props = feature.get('properties', {})
                    station_name = props.get('FacilityName_tc', '')
                    
                    # 優先選擇中環、銅鑼灣、中西區等香港島中心監測站
                    if any(area in station_name for area in ['中環', '銅鑼灣', '中西區', '東區']):
                        central_stations.append(feature)
                
                # 如果沒有香港島監測站，選擇第一個
                selected_station = central_stations[0] if central_stations else features[0]
                station_props = selected_station.get('properties', {})
                
                # 從監測站網址嘗試獲取實時 AQHI 數據
                aqhi_website = station_props.get('MonitoringStationCurrentAQHIWebsite', '')
                mid = None
                if 'mid=' in aqhi_website:
                    mid = aqhi_website.split('mid=')[1].split('&')[0]
                
                # 嘗試獲取實時 AQHI 數據（如果有 API）
                aqhi_data = self._fetch_aqhi_from_website(mid) if mid else None
                
                # 構建回應數據
                station_name = station_props.get('FacilityName_tc', station_props.get('FacilityName', 'unknown'))
                coordinates = selected_station.get('geometry', {}).get('coordinates', [])
                
                result = {
                    "station_name": station_name,
                    "coordinates": coordinates,
                    "timestamp": data.get('timeStamp', datetime.now(self.hk_tz).isoformat()),
                    "source": "CSDI 政府空間數據共享平台",
                    "note": "監測站位置數據來自政府官方平台"
                }
                
                # 如果獲取到實時 AQHI 數據，使用它
                if aqhi_data:
                    result.update(aqhi_data)
                else:
                    # 否則基於位置和時間估算
                    estimated_aqhi = self._estimate_aqhi_for_location(coordinates)
                    level_info = self.aqhi_levels.get(estimated_aqhi, self.aqhi_levels[4])
                    
                    result.update({
                        "aqhi": estimated_aqhi,
                        "level": level_info["level"],
                        "color": level_info["color"],
                        "description": level_info["description"],
                        "components": {
                            "pm2_5": self._estimate_pm25_for_location(coordinates),
                            "pm10": self._estimate_pm10_for_location(coordinates),
                            "no2": 25,
                            "o3": 30,
                            "so2": 8,
                            "co": 600
                        },
                        "note": result["note"] + "，空氣品質數值為基於地理位置的估算"
                    })
                
                logger.info(f"✓ CSDI API 成功獲取數據 - 監測站: {station_name}")
                return result
                
            else:
                raise Exception(f"CSDI API 返回錯誤狀態碼: {response.status_code}")
                
        except Exception as e:
            logger.error(f"CSDI API 獲取失敗: {e}")
            raise e
    
    def _fetch_aqhi_from_website(self, mid):
        """
        嘗試從環保署網站獲取實時 AQHI 數據
        """
        try:
            # 嘗試可能的 AQHI API 端點
            aqhi_endpoints = [
                f"https://www.aqhi.gov.hk/api/aqhi/current/{mid}.json",
                f"https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_{mid}.json",
                "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_Eng.json"
            ]
            
            for endpoint in aqhi_endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        # 解析 AQHI 數據（需要根據實際格式調整）
                        return self._parse_aqhi_data(data)
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"獲取實時 AQHI 數據失敗: {e}")
            return None
    
    def _parse_aqhi_data(self, data):
        """
        解析環保署 AQHI 數據格式
        """
        # 這裡需要根據實際的 API 回應格式來實現
        # 暫時返回 None，等待發現正確的 API 格式
        return None
    
    def _estimate_aqhi_for_location(self, coordinates):
        """
        基於地理位置估算 AQHI
        """
        if not coordinates or len(coordinates) != 2:
            return 4  # 預設值
        
        lon, lat = coordinates
        
        # 基於位置的簡單估算
        # 香港島通常空氣較好，新界北部較差
        if lat < 22.3:  # 香港島南部
            base_aqhi = 3
        elif lat > 22.45:  # 新界北部
            base_aqhi = 5
        else:  # 九龍和香港島北部
            base_aqhi = 4
        
        # 加入時間因素（早晚交通繁忙時間較差）
        current_hour = datetime.now(self.hk_tz).hour
        if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:
            base_aqhi += 1
        
        return max(1, min(11, base_aqhi))
    
    def _estimate_pm25_for_location(self, coordinates):
        """
        基於地理位置估算 PM2.5
        """
        if not coordinates or len(coordinates) != 2:
            return 20
        
        lon, lat = coordinates
        
        # 基於位置的 PM2.5 估算
        if lat < 22.3:  # 香港島南部，海風較多
            return 15
        elif lat > 22.45:  # 新界北部，接近內地
            return 30
        else:  # 九龍和香港島北部
            return 22
    
    def _estimate_pm10_for_location(self, coordinates):
        """
        基於地理位置估算 PM10
        """
        pm25 = self._estimate_pm25_for_location(coordinates)
        return int(pm25 * 1.5)  # PM10 通常約為 PM2.5 的 1.5 倍
    
    def _fetch_epd_data(self):
        """
        嘗試從環保署官方數據源獲取數據
        """
        # 環保署可能的 API 端點（2025年1月更新）
        endpoints = [
            # 原有端點
            "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_Eng.xml",
            "https://api.data.gov.hk/v1/datasets/hk-epd-aqhi-past24hour",
            "https://www.aqhi.gov.hk/api/aqhi/latest.json",
            
            # 新增可能的端點
            "https://www.epd.gov.hk/epd/sites/default/files/epd/english/environmentinhk/air/data/files/aqhi_current.xml",
            "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_Chi.xml",
            "https://portal.csdi.gov.hk/api/aqhi/current",
            "https://geodata.gov.hk/api/aqhi/latest",
            
            # 備用環保署數據端點
            "https://www.epd.gov.hk/api/v1/air-quality/current",
            "https://data.gov.hk/api/get-dataset?id=epd-aqhi-realtime"
        ]
        
        for endpoint in endpoints:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'application/json,text/xml,*/*'
                }
                response = requests.get(endpoint, timeout=10, headers=headers)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # 嘗試解析 XML 格式的回應
                    if 'xml' in content_type or endpoint.endswith('.xml'):
                        parsed_data = self._parse_epd_xml(response.text)
                        if parsed_data:
                            logger.info(f"成功從 {endpoint} 獲取XML數據")
                            return parsed_data
                    
                    # 嘗試解析 JSON 格式的回應
                    elif 'json' in content_type or endpoint.endswith('.json'):
                        try:
                            json_data = response.json()
                            parsed_data = self._parse_epd_json(json_data)
                            if parsed_data:
                                logger.info(f"成功從 {endpoint} 獲取JSON數據")
                                return parsed_data
                        except json.JSONDecodeError:
                            pass
                    
                    # 檢查是否為有效的數據回應（而非錯誤頁面）
                    if len(response.text) > 100 and 'aqhi' in response.text.lower():
                        logger.info(f"找到可能有效的數據端點: {endpoint}")
                        # 可以在這裡添加更多解析邏輯
                        
            except Exception as e:
                logger.debug(f"端點 {endpoint} 失敗: {e}")
                continue
        
        raise Exception("所有環保署端點都無法連接")
    
    def _parse_epd_xml(self, xml_content):
        """
        解析環保署 XML 格式數據
        """
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            # 尋找 AQHI 相關節點
            aqhi_nodes = root.findall('.//AQHI') or root.findall('.//aqhi') or root.findall('.//AirQualityHealthIndex')
            
            if aqhi_nodes:
                aqhi_value = int(aqhi_nodes[0].text or 4)
                level_info = self.aqhi_levels.get(aqhi_value, self.aqhi_levels[4])
                
                return {
                    "aqhi": aqhi_value,
                    "level": level_info["level"],
                    "color": level_info["color"],
                    "description": level_info["description"],
                    "components": self._extract_xml_components(root),
                    "timestamp": datetime.now(self.hk_tz).isoformat(),
                    "source": "環保署XML"
                }
                
        except Exception as e:
            logger.debug(f"XML解析失敗: {e}")
            
        return None
    
    def _parse_epd_json(self, json_data):
        """
        解析環保署 JSON 格式數據
        """
        try:
            # 可能的 JSON 結構
            aqhi_value = None
            
            # 直接查找 AQHI 值
            if isinstance(json_data, dict):
                aqhi_value = (json_data.get('aqhi') or 
                             json_data.get('AQHI') or 
                             json_data.get('air_quality_health_index'))
                
                # 如果是數組，取第一個
                if isinstance(aqhi_value, list) and aqhi_value:
                    aqhi_value = aqhi_value[0]
                    
            if aqhi_value and isinstance(aqhi_value, (int, float)):
                aqhi_value = int(aqhi_value)
                level_info = self.aqhi_levels.get(aqhi_value, self.aqhi_levels[4])
                
                return {
                    "aqhi": aqhi_value,
                    "level": level_info["level"],
                    "color": level_info["color"],
                    "description": level_info["description"],
                    "components": self._extract_json_components(json_data),
                    "timestamp": datetime.now(self.hk_tz).isoformat(),
                    "source": "環保署JSON"
                }
                
        except Exception as e:
            logger.debug(f"JSON解析失敗: {e}")
            
        return None
    
    def _extract_xml_components(self, root):
        """
        從 XML 中提取污染物成分
        """
        components = {
            "pm2_5": 25,
            "pm10": 40,
            "no2": 25,
            "o3": 30,
            "so2": 8,
            "co": 600
        }
        
        try:
            # 嘗試提取各種污染物數據
            for component, default in components.items():
                nodes = root.findall(f'.//{component}') or root.findall(f'.//{component.upper()}')
                if nodes and nodes[0].text:
                    components[component] = float(nodes[0].text)
        except Exception as e:
            logger.debug(f"XML成分提取失敗: {e}")
            
        return components
    
    def _extract_json_components(self, json_data):
        """
        從 JSON 中提取污染物成分
        """
        components = {
            "pm2_5": 25,
            "pm10": 40,
            "no2": 25,
            "o3": 30,
            "so2": 8,
            "co": 600
        }
        
        try:
            if isinstance(json_data, dict):
                for component in components.keys():
                    value = (json_data.get(component) or 
                            json_data.get(component.upper()) or
                            json_data.get(component.replace('_', '')))
                    if value and isinstance(value, (int, float)):
                        components[component] = float(value)
        except Exception as e:
            logger.debug(f"JSON成分提取失敗: {e}")
            
        return components
    
    def _fetch_third_party_data(self):
        """
        從第三方 API 獲取香港空氣品質數據
        """
        # 嘗試多個第三方數據源
        sources = [
            self._try_openweathermap,
            self._try_world_aqi,
            self._try_iqair,
            self._try_waqi
        ]
        
        for source_func in sources:
            try:
                result = source_func()
                if result:
                    return result
            except Exception as e:
                logger.debug(f"第三方數據源失敗: {e}")
                continue
        
        raise Exception("所有第三方 API 均無法獲取數據")
    
    def _try_openweathermap(self):
        """
        使用 OpenWeatherMap 的空氣污染 API
        """
        # Hong Kong coordinates
        lat, lon = 22.3193, 114.1694
        api_key = "demo"  # 需要真實的 API key
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return self._parse_openweather_data(data)
        return None
    
    def _try_world_aqi(self):
        """
        嘗試 World Air Quality Index API
        """
        # World AQI API - 需要 token
        url = "https://api.waqi.info/feed/hongkong/?token=demo"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok' and data.get('data'):
                return self._parse_waqi_data(data['data'])
        return None
    
    def _try_iqair(self):
        """
        嘗試 IQAir API
        """
        # IQAir API - 需要 API key
        url = "https://api.airvisual.com/v2/city?city=Hong%20Kong&state=Hong%20Kong&country=Hong%20Kong&key=demo"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('data'):
                return self._parse_iqair_data(data['data'])
        return None
    
    def _try_waqi(self):
        """
        嘗試另一個 WAQI 端點
        """
        # 備用的香港監測站
        stations = ["central", "causeway-bay", "tsim-sha-tsui", "sham-shui-po"]
        
        for station in stations:
            try:
                url = f"https://api.waqi.info/feed/{station}/?token=demo"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok' and data.get('data'):
                        return self._parse_waqi_data(data['data'])
            except:
                continue
        return None
    
    def _parse_waqi_data(self, data):
        """
        解析 World AQI 數據
        """
        try:
            aqi = data.get('aqi', 50)
            # 轉換 AQI 到 AQHI (大致換算)
            if aqi <= 50:
                aqhi = 1 + int(aqi / 16.7)  # 1-3
            elif aqi <= 100:
                aqhi = 4 + int((aqi - 50) / 16.7)  # 4-6
            elif aqi <= 150:
                aqhi = 7 + int((aqi - 100) / 16.7)  # 7-9
            else:
                aqhi = min(11, 10 + int((aqi - 150) / 50))  # 10-11
            
            iaqi = data.get('iaqi', {})
            
            return {
                "aqhi": aqhi,
                "level_info": self.aqhi_levels.get(aqhi, self.aqhi_levels[4]),
                "components": {
                    "pm2_5": iaqi.get('pm25', {}).get('v', 25),
                    "pm10": iaqi.get('pm10', {}).get('v', 40),
                    "no2": iaqi.get('no2', {}).get('v', 25),
                    "o3": iaqi.get('o3', {}).get('v', 30),
                    "so2": iaqi.get('so2', {}).get('v', 8),
                    "co": iaqi.get('co', {}).get('v', 600)
                },
                "timestamp": datetime.now(self.hk_tz).isoformat(),
                "source": "World AQI"
            }
        except Exception as e:
            logger.debug(f"WAQI數據解析失敗: {e}")
            return None
    
    def _parse_iqair_data(self, data):
        """
        解析 IQAir 數據
        """
        try:
            current = data.get('current', {})
            pollution = current.get('pollution', {})
            
            aqi = pollution.get('aqius', 50)  # US AQI
            # 轉換為 AQHI
            if aqi <= 50:
                aqhi = 1 + int(aqi / 16.7)
            elif aqi <= 100:
                aqhi = 4 + int((aqi - 50) / 16.7)
            elif aqi <= 150:
                aqhi = 7 + int((aqi - 100) / 16.7)
            else:
                aqhi = min(11, 10 + int((aqi - 150) / 50))
            
            return {
                "aqhi": aqhi,
                "level_info": self.aqhi_levels.get(aqhi, self.aqhi_levels[4]),
                "components": {
                    "pm2_5": pollution.get('p2', 25),
                    "pm10": pollution.get('p1', 40),
                    "no2": 25,  # IQAir 通常不提供這些
                    "o3": 30,
                    "so2": 8,
                    "co": 600
                },
                "timestamp": datetime.now(self.hk_tz).isoformat(),
                "source": "IQAir"
            }
        except Exception as e:
            logger.debug(f"IQAir數據解析失敗: {e}")
            return None
    
    def _parse_openweather_data(self, data):
        """
        解析 OpenWeatherMap 空氣污染數據
        """
        if not data.get("list"):
            return None
            
        current = data["list"][0]
        aqi = current.get("main", {}).get("aqi", 3)  # 1-5 scale
        components = current.get("components", {})
        
        # 轉換為香港 AQHI 格式 (1-11 scale)
        aqhi = min(int(aqi * 2.2), 11)
        
        return {
            "aqhi": aqhi,
            "level_info": self.aqhi_levels.get(aqhi, self.aqhi_levels[3]),
            "components": {
                "pm2_5": components.get("pm2_5", 0),
                "pm10": components.get("pm10", 0),
                "no2": components.get("no2", 0),
                "o3": components.get("o3", 0),
                "so2": components.get("so2", 0),
                "co": components.get("co", 0)
            },
            "timestamp": datetime.now(self.hk_tz).isoformat(),
            "source": "OpenWeatherMap"
        }
    
    def _estimate_air_quality(self):
        """
        基於天氣條件估算空氣品質
        這是備用方案，基於一般規律
        """
        try:
            # 獲取當前天氣數據來估算空氣品質
            import hko_fetcher
            weather = hko_fetcher.fetch_weather_data()
            
            # 基於天氣條件估算 AQHI
            aqhi = self._calculate_estimated_aqhi(weather)
            level_info = self.aqhi_levels.get(aqhi, self.aqhi_levels[4])
            
            return {
                "aqhi": aqhi,
                "level": level_info["level"],
                "color": level_info["color"],
                "description": level_info["description"],
                "components": {
                    "pm2_5": self._estimate_pm25(weather),
                    "pm10": self._estimate_pm10(weather),
                    "no2": 25,  # 典型城市水平
                    "o3": 30,   # 典型水平
                    "so2": 8,   # 香港通常較低
                    "co": 600   # 典型水平
                },
                "timestamp": datetime.now(self.hk_tz).isoformat(),
                "source": "天氣估算",
                "note": "基於天氣條件的估算值，非實際監測數據"
            }
        except Exception as e:
            logger.error(f"天氣估算失敗: {e}")
            return self._get_default_air_quality()
    
    def _calculate_estimated_aqhi(self, weather):
        """
        根據天氣條件估算 AQHI
        """
        base_aqhi = 4  # 基準值
        
        try:
            # 檢查降雨 - 降雨會改善空氣品質
            if weather.get("rainfall"):
                rainfall_data = weather["rainfall"].get("data", [])
                max_rainfall = max([r.get("max", 0) for r in rainfall_data if isinstance(r, dict)], default=0)
                if max_rainfall > 0:
                    base_aqhi = max(2, base_aqhi - 2)  # 降雨改善空氣
            
            # 檢查溫度 - 高溫可能加劇污染
            if weather.get("temperature"):
                temp_data = weather["temperature"].get("data", [])
                if temp_data:
                    avg_temp = sum([t.get("value", 25) for t in temp_data if isinstance(t, dict)]) / len(temp_data)
                    if avg_temp > 32:
                        base_aqhi += 1  # 高溫增加污染
                    elif avg_temp < 20:
                        base_aqhi = max(2, base_aqhi - 1)  # 低溫通常更清潔
            
            # 檢查風速 - 強風有助於擴散污染物
            if weather.get("wind"):
                wind_speed = (weather["wind"].get("speed_kmh_min", 10) + 
                             weather["wind"].get("speed_kmh_max", 20)) / 2
                if wind_speed > 25:
                    base_aqhi = max(2, base_aqhi - 1)  # 強風改善空氣
                elif wind_speed < 10:
                    base_aqhi += 1  # 弱風不利擴散
            
            # 檢查濕度 - 高濕度可能加重污染感受
            if weather.get("humidity"):
                humidity_data = weather["humidity"].get("data", [])
                if humidity_data:
                    humidity = humidity_data[0].get("value", 70)
                    if humidity > 85:
                        base_aqhi += 1  # 高濕度加重污染感受
            
        except Exception as e:
            logger.warning(f"估算 AQHI 時出錯: {e}")
        
        return max(1, min(11, base_aqhi))
    
    def _estimate_pm25(self, weather):
        """估算 PM2.5 濃度 (μg/m³)"""
        base_pm25 = 20  # 香港平均水平
        
        # 降雨會顯著降低PM2.5
        if weather.get("rainfall"):
            rainfall_data = weather["rainfall"].get("data", [])
            max_rainfall = max([r.get("max", 0) for r in rainfall_data if isinstance(r, dict)], default=0)
            if max_rainfall > 0:
                base_pm25 = max(5, base_pm25 - 10)
        
        # 風速影響
        if weather.get("wind"):
            wind_speed = (weather["wind"].get("speed_kmh_min", 10) + 
                         weather["wind"].get("speed_kmh_max", 20)) / 2
            if wind_speed > 20:
                base_pm25 = max(5, base_pm25 - 8)
            elif wind_speed < 8:
                base_pm25 += 15
        
        return max(5, min(100, base_pm25))
    
    def _estimate_pm10(self, weather):
        """估算 PM10 濃度 (μg/m³)"""
        pm25 = self._estimate_pm25(weather)
        # PM10 通常是 PM2.5 的 1.3-2 倍
        return min(150, int(pm25 * 1.6))
    
    def _get_default_air_quality(self):
        """
        返回預設的空氣品質數據
        """
        aqhi = 4  # 中等水平
        level_info = self.aqhi_levels[aqhi]
        return {
            "aqhi": aqhi,
            "level": level_info["level"],
            "color": level_info["color"], 
            "description": level_info["description"],
            "components": {
                "pm2_5": 25,
                "pm10": 40,
                "no2": 25,
                "o3": 30,
                "so2": 8,
                "co": 600
            },
            "timestamp": datetime.now(self.hk_tz).isoformat(),
            "source": "預設值",
            "note": "無法獲取實際數據時的預設值"
        }
    
    def calculate_air_quality_factor(self, air_quality_data):
        """
        計算空氣品質對燒天的影響因子
        
        Args:
            air_quality_data: 空氣品質數據
            
        Returns:
            dict: 包含分數和描述的字典
        """
        if not air_quality_data:
            return {
                "score": 10,
                "description": "無空氣品質數據",
                "impact": "未知",
                "aqhi": 4,
                "level": "中",
                "pm25": 25,
                "source": "未知"
            }
        
        aqhi = air_quality_data.get("aqhi", 4)
        level = air_quality_data.get("level", "中")
        components = air_quality_data.get("components", {})
        
        # 基於 AQHI 計算基礎分數 (滿分15分)
        if aqhi <= 3:
            base_score = 15  # 低污染，極佳燒天條件
            impact = "極佳"
            description = f"AQHI {aqhi} ({level})，空氣清澈透明"
        elif aqhi <= 6:
            base_score = 12  # 中等污染，良好燒天條件
            impact = "良好"
            description = f"AQHI {aqhi} ({level})，空氣品質一般"
        elif aqhi <= 9:
            base_score = 8   # 高污染，影響燒天品質
            impact = "一般"
            description = f"AQHI {aqhi} ({level})，空氣品質欠佳，影響色彩飽和度"
        else:
            base_score = 4   # 嚴重污染，大幅影響燒天
            impact = "差"
            description = f"AQHI {aqhi} ({level})，空氣污染嚴重，大幅影響燒天品質"
        
        # 根據具體污染物調整分數
        pm25 = components.get("pm2_5", 25)
        if pm25 > 50:
            base_score = max(2, base_score - 3)
            description += f"，PM2.5偏高({pm25}μg/m³)"
        elif pm25 < 15:
            base_score = min(15, base_score + 1)
            description += f"，PM2.5良好({pm25}μg/m³)"
        
        # 添加數據來源信息
        source = air_quality_data.get("source", "未知")
        if source != "環保署":
            description += f" [{source}]"
        
        return {
            "score": max(0, min(15, base_score)),
            "description": description,
            "impact": impact,
            "aqhi": aqhi,
            "level": level,
            "pm25": pm25,
            "source": source
        }

def get_current_air_quality():
    """
    獲取當前空氣品質數據的主要函數
    """
    fetcher = AirQualityFetcher()
    return fetcher.get_current_air_quality()

def calculate_air_quality_impact(aqhi=None, pm25=None):
    """
    計算空氣品質對燒天預測的影響
    """
    fetcher = AirQualityFetcher()
    
    # 如果沒有提供參數，獲取當前數據
    if aqhi is None:
        air_quality_data = fetcher.get_current_air_quality()
        return fetcher.calculate_air_quality_factor(air_quality_data)
    
    # 如果提供了參數，構造數據
    fake_data = {
        "aqhi": aqhi or 4,
        "level": "中",
        "components": {
            "pm2_5": pm25 or 25
        },
        "source": "參數提供"
    }
    return fetcher.calculate_air_quality_factor(fake_data)

if __name__ == "__main__":
    # 測試空氣品質獲取
    print("=== 香港空氣品質數據測試 ===")
    
    air_quality = get_current_air_quality()
    if air_quality:
        print(f"AQHI: {air_quality['aqhi']}")
        print(f"等級: {air_quality['level']}")
        print(f"描述: {air_quality['description']}")
        print(f"PM2.5: {air_quality['components']['pm2_5']} μg/m³")
        print(f"數據來源: {air_quality['source']}")
        print()
        
        # 測試影響計算
        fetcher = AirQualityFetcher()
        impact = fetcher.calculate_air_quality_factor(air_quality)
        print("燒天影響評估:")
        print(f"分數: {impact['score']}/15")
        print(f"描述: {impact['description']}")
        print(f"影響: {impact['impact']}")
    else:
        print("無法獲取空氣品質數據")
