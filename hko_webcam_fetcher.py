"""
香港天文台網路攝影機圖片獲取和分析模組
自動獲取即時天氣圖片並進行燒天預測分析
"""

import requests
import time
from datetime import datetime, timedelta
from PIL import Image
import io
import base64
import numpy as np
import cv2
from typing import Dict, List, Optional, Tuple
import logging

class HKOWebcamFetcher:
    """香港天文台網路攝影機圖片獲取器"""
    
    # 香港天文台攝影機基礎URL
    BASE_URL = "https://www.hko.gov.hk/wxinfo/aws/hko_mica"
    
    # 完整32個攝影機位置清單（根據HKO官網 https://www.hko.gov.hk/tc/wxinfo/ts/index_webcam.htm）
    WEBCAM_LOCATIONS = {
        # ========== 新界 (11個) ==========
        'HK_LFS': {
            'name': '流浮山(望向西面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/lfs/latest_LFS.jpg',
            'direction': 'West',
            'latitude': 22.4689,
            'longitude': 113.9892,
            'region': '新界',
            'priority': 'high'  # 日落西面視野佳
        },
        'HK_WLP': {
            'name': '濕地公園(望向東北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/wlp/latest_WLP.jpg',
            'direction': 'Northeast',
            'latitude': 22.4667,
            'longitude': 114.0167,
            'region': '新界',
            'priority': 'medium'
        },
        'HK_ELC': {
            'name': '上水風采中學(望向西北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/elc/latest_ELC.jpg',
            'direction': 'Northwest',
            'latitude': 22.5033,
            'longitude': 114.1283,
            'region': '新界',
            'priority': 'medium'
        },
        'HK_KFB': {
            'name': '嘉道理農場暨植物園(遠眺新界西部)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/kfb/latest_KFB.jpg',
            'direction': 'West',
            'latitude': 22.4333,
            'longitude': 114.1167,
            'region': '新界',
            'priority': 'high'  # 高地視野佳
        },
        'HK_TPK': {
            'name': '大埔滘(望向東北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/tpk/latest_TPK.jpg',
            'direction': 'Northeast',
            'latitude': 22.4333,
            'longitude': 114.1833,
            'region': '新界',
            'priority': 'medium'
        },
        'HK_TLC': {
            'name': '大欖涌(遠眺大嶼山北部)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/tlc/latest_TLC.jpg',
            'direction': 'Southwest',
            'latitude': 22.3667,
            'longitude': 114.0500,
            'region': '新界',
            'priority': 'high'  # 西南面日落視野
        },
        'HK_SK2': {
            'name': '西貢水警東警署(望向東北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/sk2/latest_SK2.jpg',
            'direction': 'Northeast',
            'latitude': 22.3833,
            'longitude': 114.2667,
            'region': '新界',
            'priority': 'medium'
        },
        'HK_SKG': {
            'name': '西貢水警東警署(望向東南面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/skg/latest_SKG.jpg',
            'direction': 'Southeast',
            'latitude': 22.3833,
            'longitude': 114.2667,
            'region': '新界',
            'priority': 'medium'
        },
        'HK_CWB': {
            'name': '清水灣(望向西南面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/cwb/latest_CWB.jpg',
            'direction': 'Southwest',
            'latitude': 22.2667,
            'longitude': 114.3000,
            'region': '新界',
            'priority': 'high'  # 西南面日落視野
        },
        'HK_CWA': {
            'name': '清水灣(望向東面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/cwa/latest_CWA.jpg',
            'direction': 'East',
            'latitude': 22.2667,
            'longitude': 114.3000,
            'region': '新界',
            'priority': 'high'  # 日出東面視野
        },
        'HK_KS2': {
            'name': '滘西洲(望向西北偏西面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/ks2/latest_KS2.jpg',
            'direction': 'Northwest',
            'latitude': 22.3667,
            'longitude': 114.3167,
            'region': '新界',
            'priority': 'high'  # 海上視野佳
        },
        
        # ========== 九龍 (2個) ==========
        'HK_KLT': {
            'name': '九龍城(望向東九龍及港島東部)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/klt/latest_KLT.jpg',
            'direction': 'East',
            'latitude': 22.3317,
            'longitude': 114.1867,
            'region': '九龍',
            'priority': 'high'  # 日出東面視野
        },
        'HK_HK2': {
            'name': '尖沙咀(望向西面)', 
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/hk2/latest_HK2.jpg',
            'direction': 'West',
            'latitude': 22.2975,
            'longitude': 114.1717,
            'region': '九龍',
            'priority': 'high'  # 日落西面視野
        },
        'HK_HKO': {
            'name': '尖沙咀(望向東面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/hko/latest_HKO.jpg',
            'direction': 'East',
            'latitude': 22.2975,
            'longitude': 114.1717,
            'region': '九龍',
            'priority': 'high'  # 日出東面視野
        },
        'HK_IC2': {
            'name': '環球貿易廣場(望向西南面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/ic2/latest_IC2.jpg',
            'direction': 'Southwest',
            'latitude': 22.3033,
            'longitude': 114.1600,
            'region': '九龍',
            'priority': 'high'  # 高空西南面日落視野
        },
        'HK_IC1': {
            'name': '環球貿易廣場(望向東南面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/ic1/latest_IC1.jpg',
            'direction': 'Southeast',
            'latitude': 22.3033,
            'longitude': 114.1600,
            'region': '九龍',
            'priority': 'high'  # 高空維港視野
        },
        
        # ========== 香港島 (7個) ==========
        'HK_CP1': {
            'name': '中環碼頭(望向維多利亞港)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/cp1/latest_CP1.jpg',
            'direction': 'North',
            'latitude': 22.2867,
            'longitude': 114.1600,
            'region': '香港島',
            'priority': 'high'  # 維港標誌性視野
        },
        'HK_HMM': {
            'name': '香港海事博物館(望向維多利亞港)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/hmm/latest_HMM.jpg',
            'direction': 'North',
            'latitude': 22.2850,
            'longitude': 114.1533,
            'region': '香港島',
            'priority': 'high'  # 維港視野
        },
        'HK_VPB': {
            'name': '太平山(望向東北偏北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/vpb/latest_VPB.jpg',
            'direction': 'Northeast',
            'latitude': 22.2703,
            'longitude': 114.1489,
            'region': '香港島',
            'priority': 'high'  # 太平山高空視野
        },
        'HK_VPA': {
            'name': '太平山(望向東面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/vpa/latest_VPA.jpg', 
            'direction': 'East',
            'latitude': 22.2703,
            'longitude': 114.1489,
            'region': '香港島',
            'priority': 'high'  # 太平山日出視野
        },
        'HK_GSI': {
            'name': '德瑞國際學校(遠眺海洋公園及香港仔)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/gsi/latest_GSI.jpg',
            'direction': 'South',
            'latitude': 22.2617,
            'longitude': 114.1917,
            'region': '香港島',
            'priority': 'medium'
        },
        'HK_SWH': {
            'name': '西灣河(望向東面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/swh/latest_SWH.jpg',
            'direction': 'East',
            'latitude': 22.2833,
            'longitude': 114.2167,
            'region': '香港島',
            'priority': 'high'  # 日出東面視野
        },
        
        # ========== 大嶼山及離島 (10個) ==========
        'HK_SLW': {
            'name': '沙螺灣(遠眺香港國際機場)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/slw/latest_SLW.jpg',
            'direction': 'North',
            'latitude': 22.3456,
            'longitude': 113.9492,
            'region': '大嶼山及離島',
            'priority': 'high'  # 機場及日落視野
        },
        'HK_DNL': {
            'name': '坪洲(遠眺竹篙灣)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/dnl/latest_DNL.jpg',
            'direction': 'West',
            'latitude': 22.2833,
            'longitude': 114.0333,
            'region': '大嶼山及離島',
            'priority': 'high'  # 西面日落視野
        },
        'HK_PE2': {
            'name': '坪洲(遠眺維多利亞港)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/pe2/latest_PE2.jpg',
            'direction': 'East',
            'latitude': 22.2833,
            'longitude': 114.0333,
            'region': '大嶼山及離島',
            'priority': 'high'  # 維港及日出視野
        },
        'HK_CS1': {
            'name': '長沙(望向西北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/cs1/latest_CS1.jpg',
            'direction': 'Northwest',
            'latitude': 22.2333,
            'longitude': 113.9500,
            'region': '大嶼山及離島',
            'priority': 'high'  # 西北日落視野
        },
        'HK_CS2': {
            'name': '長沙(望向北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/cs2/latest_CS2.jpg',
            'direction': 'North',
            'latitude': 22.2333,
            'longitude': 113.9500,
            'region': '大嶼山及離島',
            'priority': 'medium'
        },
        'HK_CCH': {
            'name': '長洲(望向北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/cch/latest_CCH.jpg',
            'direction': 'North',
            'latitude': 22.2000,
            'longitude': 114.0333,
            'region': '大嶼山及離島',
            'priority': 'medium'
        },
        'HK_CCE': {
            'name': '長洲東灣(望向東面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/cce/latest_CCE.jpg',
            'direction': 'East',
            'latitude': 22.2000,
            'longitude': 114.0333,
            'region': '大嶼山及離島',
            'priority': 'high'  # 日出東面視野
        },
        'HK_LAM': {
            'name': '南丫島(望向西北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/lam/latest_LAM.jpg',
            'direction': 'Northwest',
            'latitude': 22.2167,
            'longitude': 114.1167,
            'region': '大嶼山及離島',
            'priority': 'high'  # 西北日落視野
        },
        'HK_WL2': {
            'name': '橫瀾島(望向西北偏北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/wl2/latest_WL2.jpg',
            'direction': 'Northwest',
            'latitude': 22.1833,
            'longitude': 114.3000,
            'region': '大嶼山及離島',
            'priority': 'high'  # 海上開闊視野
        },
        'HK_WGL': {
            'name': '橫瀾島(望向西面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/wgl/latest_WGL.jpg',
            'direction': 'West',
            'latitude': 22.1833,
            'longitude': 114.3000,
            'region': '大嶼山及離島',
            'priority': 'high'  # 海上日落視野
        },
        
        # ========== 大帽山 (2個，補充) ==========
        'HK_TM2': {
            'name': '大帽山(望向西南面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/tm2/latest_TM2.jpg',
            'direction': 'Southwest',
            'latitude': 22.4055,
            'longitude': 114.1253,
            'region': '新界',
            'priority': 'high'  # 最高點西南日落視野
        },
        'HK_TM3': {
            'name': '大帽山(望向東北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/tm3/latest_TM3.jpg',
            'direction': 'Northeast',
            'latitude': 22.4055,
            'longitude': 114.1253,
            'region': '新界',
            'priority': 'medium'
        }
    }
    
    def __init__(self, timeout: int = 10, retry_attempts: int = 3):
        """
        初始化攝影機獲取器
        
        Args:
            timeout: 請求超時時間（秒）
            retry_attempts: 重試次數
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 設置日誌
        self.logger = logging.getLogger(__name__)
        
    def fetch_webcam_image(self, location_id: str, return_format: str = 'pil') -> Optional[Dict]:
        """
        獲取指定攝影機的最新圖片
        
        Args:
            location_id: 攝影機位置ID
            return_format: 返回格式 ('pil', 'base64', 'cv2', 'bytes')
            
        Returns:
            包含圖片和元數據的字典，或None（如果失敗）
        """
        if location_id not in self.WEBCAM_LOCATIONS:
            self.logger.error(f"Unknown webcam location: {location_id}")
            return None
            
        location_info = self.WEBCAM_LOCATIONS[location_id]
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.get(
                    location_info['url'], 
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # 檢查是否為有效圖片
                image_data = response.content
                if len(image_data) < 1000:  # 太小可能是錯誤頁面
                    raise ValueError("Image data too small")
                    
                # 獲取照片實際更新時間（從HTTP header）
                capture_time = datetime.now()
                if 'Last-Modified' in response.headers:
                    try:
                        from email.utils import parsedate_to_datetime
                        last_modified = response.headers['Last-Modified']
                        capture_time = parsedate_to_datetime(last_modified)
                        # 轉換為本地時區（香港時間）
                        import pytz
                        hk_tz = pytz.timezone('Asia/Hong_Kong')
                        if capture_time.tzinfo is None:
                            # 如果沒有時區信息，假設是UTC
                            capture_time = pytz.utc.localize(capture_time)
                        capture_time = capture_time.astimezone(hk_tz)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse Last-Modified header: {e}")
                        capture_time = datetime.now()
                
                # 轉換圖片格式
                pil_image = Image.open(io.BytesIO(image_data))
                
                result = {
                    'location_id': location_id,
                    'location_name': location_info['name'],
                    'direction': location_info['direction'],
                    'latitude': location_info['latitude'],
                    'longitude': location_info['longitude'],
                    'region': location_info.get('region', '其他'),  # 添加地區信息
                    'capture_time': capture_time,
                    'image_size': pil_image.size,
                    'priority': location_info['priority']
                }
                
                # 根據要求的格式返回圖片
                if return_format == 'pil':
                    result['image'] = pil_image
                elif return_format == 'base64':
                    buffer = io.BytesIO()
                    pil_image.save(buffer, format='JPEG')
                    result['image'] = base64.b64encode(buffer.getvalue()).decode()
                elif return_format == 'cv2':
                    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    result['image'] = cv_image
                elif return_format == 'bytes':
                    result['image'] = image_data
                else:
                    result['image'] = pil_image
                    
                self.logger.info(f"Successfully fetched image from {location_info['name']}")
                return result
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {location_id}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # 指數退避
                    
        self.logger.error(f"All attempts failed for {location_id}")
        return None
        
    def fetch_multiple_webcams(self, location_ids: List[str] = None, priority_filter: str = None) -> Dict[str, Dict]:
        """
        同時獲取多個攝影機的圖片
        
        Args:
            location_ids: 指定的攝影機ID列表，None表示全部
            priority_filter: 優先級過濾 ('high', 'medium', 'low')
            
        Returns:
            攝影機ID到圖片數據的映射
        """
        if location_ids is None:
            location_ids = list(self.WEBCAM_LOCATIONS.keys())
            
        if priority_filter:
            location_ids = [
                loc_id for loc_id in location_ids 
                if self.WEBCAM_LOCATIONS[loc_id]['priority'] == priority_filter
            ]
            
        results = {}
        for location_id in location_ids:
            result = self.fetch_webcam_image(location_id)
            if result:
                results[location_id] = result
                
        return results
        
    def get_best_sunset_webcams(self, current_time: datetime = None) -> List[str]:
        """
        根據當前時間和日照方向，推薦最適合觀測燒天的攝影機
        
        Args:
            current_time: 當前時間，None表示使用系統時間
            
        Returns:
            推薦的攝影機ID列表（按優先順序排列）
        """
        if current_time is None:
            current_time = datetime.now()
            
        # 根據時間和季節調整推薦
        hour = current_time.hour
        month = current_time.month
        
        # 黃昏時段（下午4點-晚上8點）
        if 16 <= hour <= 20:
            if month in [12, 1, 2]:  # 冬季，太陽偏南
                return ['HK_HKO', 'HK_VPA', 'HK_WGL', 'HK_TM2']
            elif month in [6, 7, 8]:  # 夏季，太陽偏北  
                return ['HK_HK2', 'HK_VPB', 'HK_TM3', 'HK_SLW']
            else:  # 春秋季
                return ['HK_HKO', 'HK_HK2', 'HK_VPA', 'HK_VPB']
        
        # 其他時段使用高優先級攝影機
        return [
            loc_id for loc_id, info in self.WEBCAM_LOCATIONS.items()
            if info['priority'] == 'high'
        ]


class WebcamImageAnalyzer:
    """網路攝影機圖片分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_sky_conditions(self, image: Image.Image) -> Dict:
        """
        分析天空狀況
        
        Args:
            image: PIL圖片對象
            
        Returns:
            天空分析結果
        """
        try:
            # 轉換為numpy數組進行分析
            img_array = np.array(image.convert('RGB'))
            height, width = img_array.shape[:2]
            
            # 分析天空區域（通常是圖片上半部）
            sky_region = img_array[:height//2, :]
            
            # 計算顏色統計
            mean_rgb = np.mean(sky_region.reshape(-1, 3), axis=0)
            
            # 雲覆蓋度估算（基於像素變異度）
            gray_sky = cv2.cvtColor(sky_region, cv2.COLOR_RGB2GRAY)
            cloud_variance = np.std(gray_sky)
            
            # 估算雲覆蓋度（0-100%）
            cloud_coverage = min(100, max(0, (cloud_variance - 10) * 2))
            
            # 能見度估算（基於對比度）
            visibility = self._estimate_visibility(gray_sky)
            
            # 燒天潛力評估
            sunset_potential = self._evaluate_sunset_potential(mean_rgb, cloud_coverage, visibility)
            
            return {
                'mean_color': {
                    'red': float(mean_rgb[0]),
                    'green': float(mean_rgb[1]), 
                    'blue': float(mean_rgb[2])
                },
                'cloud_coverage': float(cloud_coverage),
                'visibility': float(visibility),
                'brightness': float((mean_rgb[0] + mean_rgb[1] + mean_rgb[2]) / 3),
                'sunset_potential': sunset_potential,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Image analysis failed: {str(e)}")
            return {
                'error': str(e),
                'analysis_time': datetime.now().isoformat()
            }
            
    def _estimate_visibility(self, gray_image: np.ndarray) -> float:
        """估算能見度（基於圖片清晰度）"""
        # 使用Laplacian變異度估算清晰度
        laplacian_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()
        
        # 正規化到0-100範圍
        visibility = min(100, max(0, laplacian_var / 10))
        return visibility
        
    def _evaluate_sunset_potential(self, mean_rgb: np.ndarray, cloud_coverage: float, visibility: float) -> Dict:
        """
        評估燒天潛力（方案 B：智能混合模式）
        - 燒天時段：基於相片特徵 + 時間權重
        - 非燒天時段：基於相片特徵（日出/早晨/全天任何時間都可能有好天空）
        """
        from datetime import datetime
        
        current_time = datetime.now()
        hour = current_time.hour
        month = current_time.month
        
        red, green, blue = mean_rgb
        avg_brightness = (red + green + blue) / 3
        
        # 檢查是否為夜間圖片（整體亮度太低）
        if avg_brightness < 40:
            return {
                'score': 0.0,
                'level': 'too_dark',
                'time_period': 'night',
                'factors': {
                    'color_richness': 0.0,
                    'optimal_cloud': 0.0, 
                    'visibility': 0.0,
                    'brightness': float(avg_brightness)
                },
                'message': f'夜間照片，光線不足 (亮度: {avg_brightness:.1f})'
            }
        
        # 判斷當前時段（日出、白天、燒天、日落、夜間）
        time_period = self._get_time_period(hour, month)
        is_sunset_time = self._is_sunset_time(hour, month)
        
        # 顏色豐富度（紅色vs藍色比例）- 正規化到0-100
        red_blue_ratio = (red / (blue + 1)) if blue > 0 else 0
        # 理想的燒天照片紅藍比約1.5-3.0，正規化到0-100分
        color_richness_raw = min(100, max(0, (red_blue_ratio - 0.8) * 50))  # 0.8以下=0分，2.8以上=100分
        # 考慮亮度因素調整
        color_richness = color_richness_raw * min(1.0, avg_brightness / 100)
        
        # 最佳雲覆蓋度（30-70%為佳）- 已經是0-100分
        optimal_cloud_score = max(0, 100 - abs(cloud_coverage - 50) * 2)
        
        # 能見度評分（正規化）- 已經是0-100分
        visibility_score = min(100, visibility)
        
        # 計算時間權重（全天時都有權重，但燒天時段最高）
        time_weight = self._calculate_time_weight(hour, month)
        
        # 【方案 B 核心邏輯】根據時段調整權重
        if is_sunset_time:
            # 燒天時段：時間權重 15%
            weight_time = 0.15
            time_note = '燒天時段'
        elif time_period == 'sunrise':
            # 日出時段：時間權重 10%（降低，但仍有評分）
            weight_time = 0.10
            time_note = '日出時段'
            # 日出期間降低顏色豐富度的期望值（通常偏紅）
            color_richness = color_richness * 1.1  # 輕微加成
        elif time_period == 'morning':
            # 早晨時段：時間權重 5%
            weight_time = 0.05
            time_note = '早晨時段'
        else:
            # 其他時段（白天、日落後）：時間權重 2%
            weight_time = 0.02
            time_note = f'其他時段 ({hour}點)'
        
        # 綜合評分 - 所有因子都是0-100分，按權重加權
        base_score = (
            color_richness * 0.25 +         # 顏色豐富度 25%
            optimal_cloud_score * 0.35 +    # 雲覆蓋度 35%
            visibility_score * 0.25 +       # 能見度 25%
            time_weight * weight_time       # 時間因素（變動）
        )
        
        # 【智能混合】：始終計算分數，不再完全歸零
        # 只在燒天時段使用完整權重，其他時段按比例降低
        if is_sunset_time:
            potential_score = base_score
        else:
            # 非燒天時段：應用係數，允許有基礎分數
            # 如果有良好的顏色豐富度和雲量，即使不在燒天時段也可以得分
            feature_strength = (color_richness + optimal_cloud_score + visibility_score) / 3
            if feature_strength > 50:  # 特徵評分超過 50 分
                potential_score = base_score * 0.6  # 給予 60% 的分數
            else:
                potential_score = base_score * 0.3  # 給予 30% 的分數
        
        # 正規化到0-100
        potential_score = min(100, max(0, potential_score))
        
        # 調整等級標準
        if potential_score >= 80:
            level = 'excellent'
        elif potential_score >= 65:
            level = 'good'
        elif potential_score >= 40:
            level = 'fair'
        elif potential_score >= 20:
            level = 'poor'
        else:
            level = 'very_poor'
               
        return {
            'score': float(potential_score),
            'level': level,
            'is_sunset_time': is_sunset_time,
            'time_period': time_period,
            'current_hour': hour,
            'factors': {
                'color_richness': float(color_richness),
                'optimal_cloud': float(optimal_cloud_score), 
                'visibility': float(visibility_score),
                'time_factor': float(time_weight),
                'brightness': float(avg_brightness)
            },
            'message': time_note
        }
    
    def _is_sunset_time(self, hour: int, month: int) -> bool:
        """判斷是否在燒天時間範圍內"""
        # 根據季節調整燒天時間
        if month in [12, 1, 2]:  # 冬季
            sunset_start, sunset_end = 16, 19
        elif month in [3, 4, 5]:  # 春季
            sunset_start, sunset_end = 17, 20
        elif month in [6, 7, 8]:  # 夏季
            sunset_start, sunset_end = 18, 21
        else:  # 秋季 [9, 10, 11]
            sunset_start, sunset_end = 16, 19
            
        return sunset_start <= hour <= sunset_end
    
    def _calculate_time_weight(self, hour: int, month: int) -> float:
        """計算時間權重（距離最佳燒天時間越近，權重越高）"""
        # 定義每季節的最佳燒天時間
        if month in [12, 1, 2]:  # 冬季
            optimal_hour = 17.5
        elif month in [3, 4, 5]:  # 春季  
            optimal_hour = 18.5
        elif month in [6, 7, 8]:  # 夏季
            optimal_hour = 19.5
        else:  # 秋季
            optimal_hour = 17.5
            
        # 計算距離最佳時間的權重
        hour_diff = abs(hour - optimal_hour)
        weight = max(0, 100 - hour_diff * 20)  # 每小時相差減20分
        return weight
    
    def _get_time_period(self, hour: int, month: int) -> str:
        """
        分類當前時段
        返回: 'sunrise' (日出 5-7點), 'morning' (早晨 7-11點), 'afternoon' (下午 11-16點),
              'sunset' (燒天 見 _is_sunset_time), 'night' (夜間 20-5點)
        """
        if hour >= 5 and hour < 7:
            return 'sunrise'
        elif hour >= 7 and hour < 11:
            return 'morning'
        elif hour >= 11 and hour < 16:
            return 'afternoon'
        elif self._is_sunset_time(hour, month):
            return 'sunset'
        else:
            return 'night'


class RealTimeWebcamMonitor:
    """即時攝影機監控系統"""
    
    def __init__(self):
        self.fetcher = HKOWebcamFetcher()
        self.analyzer = WebcamImageAnalyzer()
        self.logger = logging.getLogger(__name__)
        
    def get_current_conditions(self, detailed: bool = True, all_cameras: bool = True) -> Dict:
        """
        獲取當前天氣狀況
        
        Args:
            detailed: 是否進行詳細分析
            all_cameras: 是否獲取所有32個攝影機（默認True）
            
        Returns:
            當前狀況報告
        """
        if all_cameras:
            # 獲取所有32個攝影機
            location_ids = list(self.fetcher.WEBCAM_LOCATIONS.keys())
        else:
            # 只獲取推薦的攝影機
            location_ids = self.fetcher.get_best_sunset_webcams()[:3]
        
        # 獲取圖片
        webcam_data = self.fetcher.fetch_multiple_webcams(location_ids)
        
        if not webcam_data:
            return {
                'status': 'error',
                'message': '無法獲取攝影機數據',
                'timestamp': datetime.now().isoformat()
            }
            
        # 分析結果
        analysis_results = {}
        overall_scores = []
        
        for cam_id, cam_data in webcam_data.items():
            if detailed and 'image' in cam_data:
                analysis = self.analyzer.analyze_sky_conditions(cam_data['image'])
                analysis_results[cam_id] = {
                    'location': cam_data['location_name'],
                    'direction': cam_data['direction'],
                    'region': cam_data.get('region', '其他'),  # 添加地區信息
                    'capture_time': cam_data.get('capture_time', datetime.now()).isoformat(),
                    'analysis': analysis
                }
                
                if 'sunset_potential' in analysis:
                    overall_scores.append(analysis['sunset_potential']['score'])
                    
        # 計算整體評分
        overall_score = np.mean(overall_scores) if overall_scores else 0
        
        return {
            'status': 'success',
            'overall_sunset_potential': float(overall_score),
            'webcam_count': len(webcam_data),
            'total_cameras': len(self.fetcher.WEBCAM_LOCATIONS),
            'individual_analyses': analysis_results,
            'timestamp': datetime.now().isoformat(),
            'analysis_time': datetime.now().isoformat(),
            'recommended_locations': self.fetcher.get_best_sunset_webcams()[:5]
        }


# 測試函數
def test_webcam_fetcher():
    """測試攝影機獲取功能"""
    fetcher = HKOWebcamFetcher()
    monitor = RealTimeWebcamMonitor()
    
    # 測試單個攝影機
    print("測試獲取尖沙咀攝影機...")
    result = fetcher.fetch_webcam_image('HK_HKO')
    if result:
        print(f"成功獲取: {result['location_name']}")
        print(f"圖片尺寸: {result['image_size']}")
    else:
        print("獲取失敗")
        
    # 測試即時監控
    print("\n測試即時狀況監控...")
    conditions = monitor.get_current_conditions()
    print(f"整體燒天潛力: {conditions.get('overall_sunset_potential', 'N/A')}")
    print(f"推薦地點: {conditions.get('recommended_locations', [])}")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 執行測試
    test_webcam_fetcher()
