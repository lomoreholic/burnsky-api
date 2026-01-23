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
    BASE_URL = "https://www.hko.gov.hk/wxinfo/ts/webcam"
    
    # 攝影機位置清單（根據tw.live和HKO官網整理）
    WEBCAM_LOCATIONS = {
        'HK_HKO': {
            'name': '尖沙咀(望向東面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/hko/latest_HKO.jpg',
            'direction': 'East',
            'latitude': 22.2975,
            'longitude': 114.1717,
            'priority': 'high'  # 主要觀測點
        },
        'HK_HK2': {
            'name': '尖沙咀(望向西面)', 
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/hk2/latest_HK2.jpg',
            'direction': 'West',
            'latitude': 22.2975,
            'longitude': 114.1717,
            'priority': 'high'
        },
        'HK_VPB': {
            'name': '太平山(望向東北偏北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/vpb/latest_VPB.jpg',
            'direction': 'Northeast',
            'latitude': 22.2703,
            'longitude': 114.1489,
            'priority': 'high'
        },
        'HK_VPA': {
            'name': '太平山(望向東面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/vpa/latest_VPA.jpg', 
            'direction': 'East',
            'latitude': 22.2703,
            'longitude': 114.1489,
            'priority': 'high'
        },
        'HK_TM2': {
            'name': '大帽山(望向西南面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/tm2/latest_TM2.jpg',
            'direction': 'Southwest',
            'latitude': 22.4055,
            'longitude': 114.1253,
            'priority': 'medium'
        },
        'HK_TM3': {
            'name': '大帽山(望向東北面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/tm3/latest_TM3.jpg',
            'direction': 'Northeast',
            'latitude': 22.4055,
            'longitude': 114.1253,
            'priority': 'medium'
        },
        'HK_WGL': {
            'name': '橫瀾島(望向西面)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/wgl/latest_WGL.jpg',
            'direction': 'West',
            'latitude': 22.1833,
            'longitude': 114.3000,
            'priority': 'high'  # 海上視野佳
        },
        'HK_SLW': {
            'name': '沙螺灣(遠眺香港國際機場)',
            'url': 'https://www.hko.gov.hk/wxinfo/aws/hko_mica/slw/latest_SLW.jpg',
            'direction': 'North',
            'latitude': 22.3456,
            'longitude': 113.9492,
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
        """評估燒天潛力（只在合理時段分析，夜間直接返回0分）"""
        from datetime import datetime
        
        current_time = datetime.now()
        hour = current_time.hour
        month = current_time.month
        
        red, green, blue = mean_rgb
        avg_brightness = (red + green + blue) / 3
        
        # 檢查是否為夜間時段（晚上9點到早上6點）
        if hour >= 21 or hour < 6:
            # 夜間時段，檢查圖片亮度判斷是否為舊照片
            if avg_brightness > 60:
                return {
                    'score': 0.0,
                    'level': 'outdated_image',
                    'factors': {
                        'color_richness': 0.0,
                        'optimal_cloud': 0.0, 
                        'visibility': 0.0,
                        'brightness': float(avg_brightness)
                    },
                    'message': f'夜間時段顯示白天照片 - 圖片可能未更新 (現在{hour}點，亮度{avg_brightness:.1f})'
                }
            else:
                return {
                    'score': 0.0,
                    'level': 'night_time',
                    'factors': {
                        'color_richness': 0.0,
                        'optimal_cloud': 0.0, 
                        'visibility': 0.0,
                        'brightness': float(avg_brightness)
                    },
                    'message': f'夜間時段，不適合燒天預測 (現在是 {hour}點)'
                }
        
        # 檢查是否為夜間圖片（整體亮度太低）
        if avg_brightness < 40:
            return {
                'score': 0.0,
                'level': 'too_dark',
                'factors': {
                    'color_richness': 0.0,
                    'optimal_cloud': 0.0, 
                    'visibility': 0.0,
                    'brightness': float(avg_brightness)
                },
                'message': f'光線太暗，無法分析 (平均亮度: {avg_brightness:.1f})'
            }
        
        # 計算時間權重（全天候，但燒天時段權重更高）
        time_weight = self._calculate_time_weight(hour, month)
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
        
        # 綜合評分 - 所有因子都是0-100分，按權重加權
        base_score = (
            color_richness * 0.25 +         # 顏色豐富度 25%
            optimal_cloud_score * 0.35 +    # 雲覆蓋度 35%
            visibility_score * 0.25 +       # 能見度 25%
            time_weight * 0.15              # 時間因素 15%
        )
        
        # 只在燒天時段給予滿分，其他時段直接歸零
        if is_sunset_time:
            potential_score = base_score
        else:
            potential_score = 0.0  # 非燒天時段直接歸零
        
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
            'current_hour': hour,
            'factors': {
                'color_richness': float(color_richness),
                'optimal_cloud': float(optimal_cloud_score), 
                'visibility': float(visibility_score),
                'time_factor': float(time_weight),
                'brightness': float(avg_brightness)
            },
            'message': '燒天時段' if is_sunset_time else f'非燒天時段 (分數已調整)'
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


class RealTimeWebcamMonitor:
    """即時攝影機監控系統"""
    
    def __init__(self):
        self.fetcher = HKOWebcamFetcher()
        self.analyzer = WebcamImageAnalyzer()
        self.logger = logging.getLogger(__name__)
        
    def get_current_conditions(self, detailed: bool = True) -> Dict:
        """
        獲取當前天氣狀況
        
        Args:
            detailed: 是否進行詳細分析
            
        Returns:
            當前狀況報告
        """
        # 獲取推薦的攝影機
        recommended_cams = self.fetcher.get_best_sunset_webcams()
        
        # 獲取圖片
        webcam_data = self.fetcher.fetch_multiple_webcams(recommended_cams[:3])  # 前3個
        
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
            'individual_analyses': analysis_results,
            'timestamp': datetime.now().isoformat(),
            'recommended_locations': [
                webcam_data[cam_id]['location_name'] 
                for cam_id in recommended_cams[:3] 
                if cam_id in webcam_data
            ]
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
