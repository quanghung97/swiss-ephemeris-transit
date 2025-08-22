#!/usr/bin/env python3
"""
Swiss Ephemeris Planetary Calculator
Tính toán thông tin hành tinh theo từng giờ sử dụng Swiss Ephemeris
Xuất ra CSV và JSON giống như DrikPanchang
"""

import swisseph as swe
import datetime
import csv
import json
import os
from typing import Dict, List, Any

class SwissEphemerisCalculator:
    
    def __init__(self):
        """Khởi tạo calculator với cấu hình Swiss Ephemeris"""
        # Thiết lập đường dẫn đến ephemeris data files
        # Tải về từ: https://www.astro.com/ftp/swisseph/ephe/
        swe.set_ephe_path('./ephemeris_data')
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)  # Sidereal Lahiri Ayanamsa
        
        # Cấu hình hành tinh và symbols
        self.planets = {
            'Sun': {'id': swe.SUN, 'symbol': '☉', 'name_vi': 'Mặt Trời'},
            'Moon': {'id': swe.MOON, 'symbol': '☽', 'name_vi': 'Mặt Trăng'},
            'Mercury': {'id': swe.MERCURY, 'symbol': '☿', 'name_vi': 'Sao Thủy'},
            'Venus': {'id': swe.VENUS, 'symbol': '♀', 'name_vi': 'Sao Kim'},
            'Mars': {'id': swe.MARS, 'symbol': '♂', 'name_vi': 'Sao Hỏa'},
            'Jupiter': {'id': swe.JUPITER, 'symbol': '♃', 'name_vi': 'Sao Mộc'},
            'Saturn': {'id': swe.SATURN, 'symbol': '♄', 'name_vi': 'Sao Thổ'},
            'Uranus': {'id': swe.URANUS, 'symbol': '♅', 'name_vi': 'Sao Thiên Vương'},
            'Neptune': {'id': swe.NEPTUNE, 'symbol': '♆', 'name_vi': 'Sao Hải Vương'},
            'Pluto': {'id': swe.PLUTO, 'symbol': '♇', 'name_vi': 'Sao Diêm Vương'},
            'Rahu': {'id': swe.MEAN_NODE, 'symbol': '☊', 'name_vi': 'Rahu (Bắc Giao Điểm)'},
        }
        
        # Cung hoàng đạo
        self.zodiac_signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        
        self.zodiac_signs_vi = [
            'Bạch Dương', 'Kim Ngưu', 'Song Tử', 'Cự Giải', 'Sư Tử', 'Xử Nữ',
            'Thiên Bình', 'Thần Nông', 'Nhân Mã', 'Ma Kết', 'Bảo Bình', 'Song Ngư'
        ]

    def datetime_to_julian_day(self, dt: datetime.datetime) -> float:
        """Chuyển đổi datetime sang Julian Day"""
        return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

    def get_zodiac_info(self, longitude: float) -> Dict[str, Any]:
        """Lấy thông tin cung hoàng đạo từ kinh độ"""
        sign_index = int(longitude // 30)
        degree_in_sign = longitude % 30
        
        # Chuyển đổi degree thành độ, phút, giây
        degrees = int(degree_in_sign)
        minutes = int((degree_in_sign - degrees) * 60)
        seconds = int(((degree_in_sign - degrees) * 60 - minutes) * 60)
        
        return {
            'sign': self.zodiac_signs[sign_index],
            'sign_vi': self.zodiac_signs_vi[sign_index],
            'sign_index': sign_index,
            'degree_in_sign': degree_in_sign,
            'degree_formatted': f"{degrees}°{minutes:02d}'{seconds:02d}\"",
            'longitude': longitude
        }

    def is_retrograde(self, planet_id: int, jd: float) -> bool:
        """Kiểm tra hành tinh có nghịch hành không"""
        try:
            # Tính tốc độ hành tinh
            pos_now = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH)[0]
            pos_next = swe.calc_ut(jd + 1, planet_id, swe.FLG_SWIEPH)[0]  # 1 ngày sau
            
            # Tính tốc độ (độ/ngày)
            speed = pos_next[0] - pos_now[0]
            
            # Xử lý trường hợp băng qua 0°/360°
            if speed > 180:
                speed -= 360
            elif speed < -180:
                speed += 360
                
            return speed < 0
        except:
            return False

    def calculate_planetary_positions(self, dt: datetime.datetime) -> Dict[str, Any]:
        """Tính toán vị trí tất cả hành tinh tại một thời điểm"""
        jd = self.datetime_to_julian_day(dt)
        positions = {}
        
        for planet_name, planet_info in self.planets.items():
            try:
                # Tính vị trí hành tinh
                pos, ret = swe.calc_ut(jd, planet_info['id'], swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
                
                if ret < 0:
                    print(f"Lỗi tính toán {planet_name}: {swe.get_ayanamsa_name(ret)}")
                    continue
                
                longitude = pos[0]
                zodiac_info = self.get_zodiac_info(longitude)
                is_retro = self.is_retrograde(planet_info['id'], jd)
                # is_retro = pos[3] < 0  # trực tiếp từ speed
                
                positions[planet_name] = {
                    'longitude': longitude,
                    'latitude': pos[1],
                    'distance': pos[2],
                    'longitude_speed': pos[3],
                    'latitude_speed': pos[4],
                    'distance_speed': pos[5],
                    'zodiac_sign': zodiac_info['sign'],
                    'zodiac_sign_vi': zodiac_info['sign_vi'],
                    'sign_index': zodiac_info['sign_index'],
                    'degree_in_sign': zodiac_info['degree_in_sign'],
                    'degree_formatted': zodiac_info['degree_formatted'],
                    'retrograde': is_retro,
                    'motion': 'R' if is_retro else 'D',
                    'symbol': planet_info['symbol'],
                    'name_vi': planet_info['name_vi']
                }
                
            except Exception as e:
                print(f"Lỗi tính toán {planet_name}: {e}")
                continue
        
        # Tính Ketu (đối diện Rahu 180°)
        if 'Rahu' in positions:
            rahu_long = positions['Rahu']['longitude']
            ketu_long = (rahu_long + 180) % 360
            ketu_zodiac = self.get_zodiac_info(ketu_long)
            
            positions['Ketu'] = {
                'longitude': ketu_long,
                'latitude': -positions['Rahu']['latitude'],  # Đối diện
                'distance': positions['Rahu']['distance'],
                'longitude_speed': -positions['Rahu']['longitude_speed'],
                'latitude_speed': -positions['Rahu']['latitude_speed'],
                'distance_speed': positions['Rahu']['distance_speed'],
                'zodiac_sign': ketu_zodiac['sign'],
                'zodiac_sign_vi': ketu_zodiac['sign_vi'],
                'sign_index': ketu_zodiac['sign_index'],
                'degree_in_sign': ketu_zodiac['degree_in_sign'],
                'degree_formatted': ketu_zodiac['degree_formatted'],
                'retrograde': positions['Rahu']['retrograde'],
                'motion': positions['Rahu']['motion'],
                'symbol': '☋',
                'name_vi': 'Ketu (Nam Giao Điểm)'
            }
        
        return positions

    def calculate_monthly_data(self, year: int, month: int, timezone_offset: float = 7.0) -> List[Dict[str, Any]]:
        """Tính toán dữ liệu cho cả tháng, mỗi giờ"""
        print(f"🔄 Bắt đầu tính toán tháng {month}/{year} (UTC+{timezone_offset})")
        
        # Lấy số ngày trong tháng
        if month == 12:
            next_month = datetime.datetime(year + 1, 1, 1)
        else:
            next_month = datetime.datetime(year, month + 1, 1)
        
        current_month = datetime.datetime(year, month, 1)
        days_in_month = (next_month - current_month).days
        
        all_data = []
        total_calculations = days_in_month * 24
        current_calculation = 0
        
        aspects_all = []
        ingress_all = []
        prev_positions = None

        for day in range(1, days_in_month + 1):
            for hour in range(24):
                for minute in range(0, 60, 15):  # mỗi 15 phút
                    # Tạo datetime với timezone
                    dt_local = datetime.datetime(year, month, day, hour, minute, 0)
                    dt_utc = dt_local - datetime.timedelta(hours=timezone_offset)

                    # Tính toán vị trí hành tinh
                    positions = self.calculate_planetary_positions(dt_utc)

                    # Detect events
                    aspects = self.detect_aspects(positions)
                    ingress = self.detect_ingress(positions, prev_positions)

                    for asp in aspects:
                        aspects_all.append({'datetime': dt_local.strftime('%Y-%m-%d %H:%M:%S'), **asp})

                    for ing in ingress:
                        ingress_all.append({'datetime': dt_local.strftime('%Y-%m-%d %H:%M:%S'), **ing})

                    prev_positions = positions

                    # Tạo record dữ liệu
                    record = {
                        'date': dt_local.strftime('%Y-%m-%d'),
                        'time': dt_local.strftime('%H:%M:%S'),
                        'datetime_local': dt_local.strftime('%Y-%m-%d %H:%M:%S'),
                        'datetime_utc': dt_utc.strftime('%Y-%m-%d %H:%M:%S'),
                        'julian_day': self.datetime_to_julian_day(dt_utc),
                        'timezone_offset': timezone_offset
                    }

                    # Thêm thông tin từng hành tinh
                    planet_order = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                                    'Jupiter', 'Saturn', 'Uranus', 'Neptune', 
                                    'Pluto', 'Rahu', 'Ketu']

                    for planet in planet_order:
                        if planet in positions:
                            pos = positions[planet]
                            prefix = planet

                            record[f'{prefix}_Longitude'] = round(pos['longitude'], 6)
                            record[f'{prefix}_Latitude'] = round(pos['latitude'], 6)
                            record[f'{prefix}_Distance'] = round(pos['distance'], 6)
                            record[f'{prefix}_Sign'] = pos['zodiac_sign']
                            record[f'{prefix}_Sign_VI'] = pos['zodiac_sign_vi']
                            record[f'{prefix}_Degree'] = pos['degree_formatted']
                            record[f'{prefix}_Degree_Decimal'] = round(pos['degree_in_sign'], 6)
                            record[f'{prefix}_Motion'] = pos['motion']
                            record[f'{prefix}_Retrograde'] = pos['retrograde']
                            record[f'{prefix}_Speed'] = round(pos['longitude_speed'], 6)
                            record[f'{prefix}_Symbol'] = pos['symbol']
                            record[f'{prefix}_Name_VI'] = pos['name_vi']

                    all_data.append(record)
                    current_calculation += 1

            # Progress update mỗi ngày
            progress = (current_calculation / (days_in_month * 24 * 4)) * 100
            print(f"📊 Tiến độ: {progress:.1f}% - Ngày {day}/{days_in_month}")
        
        print(f"✅ Hoàn thành! Tổng cộng {len(all_data)} bản ghi")
        return all_data, aspects_all, ingress_all

    def export_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """Xuất dữ liệu ra file CSV"""
        if not data:
            print("❌ Không có dữ liệu để xuất")
            return
            
        print(f"📝 Đang xuất CSV: {filename}")
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ Đã xuất {len(data)} bản ghi vào {filename}")

    def export_to_json(self, data: List[Dict[str, Any]], filename: str, metadata: Dict[str, Any] = None):
        """Xuất dữ liệu ra file JSON"""
        if not data:
            print("❌ Không có dữ liệu để xuất")
            return
            
        print(f"📝 Đang xuất JSON: {filename}")
        
        export_data = {
            'metadata': metadata or {},
            'total_records': len(data),
            'data': data
        }
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Đã xuất {len(data)} bản ghi vào {filename}")


    def detect_aspects(self, positions, orb=1.0):
        aspects = []
        aspect_types = {
            'Conjunction': 0,
            'Opposition': 180,
            'Square': 90,
            'Trine': 120,
            'Sextile': 60
        }
        names = list(positions.keys())
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                p1, p2 = names[i], names[j]
                # Bỏ qua Rahu–Ketu Opposition
                if set([p1, p2]) == set(['Rahu', 'Ketu']):
                    continue

                lon1, lon2 = positions[p1]['longitude'], positions[p2]['longitude']
                diff = abs(lon1 - lon2) % 360
                if diff > 180:
                    diff = 360 - diff
                for aspect_name, angle in aspect_types.items():
                    if abs(diff - angle) <= orb:
                        aspects.append({
                            'event': 'Aspect',
                            'type': aspect_name,
                            'planet1': p1,
                            'planet1_sign': positions[p1]['zodiac_sign'],
                            'planet1_degree': positions[p1]['degree_formatted'],
                            'planet2': p2,
                            'planet2_sign': positions[p2]['zodiac_sign'],
                            'planet2_degree': positions[p2]['degree_formatted'],
                            'exact_angle': angle,
                            'difference': round(diff, 4),
                            'orb': round(abs(diff - angle), 4),
                        })
        return aspects
    

    def detect_ingress(self, positions, prev_positions=None):
        ingress_events = []
        if prev_positions:
            for planet, pos in positions.items():
                if planet in prev_positions:
                    if pos['sign_index'] != prev_positions[planet]['sign_index']:
                        ingress_events.append({
                            'event': 'Ingress',
                            'planet': planet,
                            'from_sign': prev_positions[planet]['zodiac_sign'],
                            'to_sign': pos['zodiac_sign'],
                            'degree': pos['degree_formatted'],
                            'longitude': round(pos['longitude'], 6),
                        })
        return ingress_events
    
    def export_events(self, events, csv_file, json_file):
        if not events:
            print(f"❌ Không có sự kiện cho {csv_file}")
            return
        fieldnames = events[0].keys()
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(events)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        print(f"✅ Xuất {len(events)} sự kiện vào {csv_file}, {json_file}")


def main():
    """Hàm chính"""
    print("🌟 Swiss Ephemeris Planetary Calculator")
    print("=" * 50)
    
    # Khởi tạo calculator
    calc = SwissEphemerisCalculator()
    
    # Cấu hình tính toán
    year = 2025
    month = 9
    timezone_offset = 7.0  # UTC+7 cho Việt Nam
    
    print(f"📅 Tháng: {month}/{year}")
    print(f"🌍 Múi giờ: UTC+{timezone_offset}")
    print(f"📊 Sẽ tính toán cho mỗi giờ trong tháng")
    print()
    
    # Tính toán dữ liệu
    try:
        monthly_data, aspects, ingress = calc.calculate_monthly_data(year, month, timezone_offset)
        


        # Metadata
        metadata = {
            'year': year,
            'month': month,
            'timezone_offset': timezone_offset,
            'calculation_time': datetime.datetime.now().isoformat(),
            'ephemeris_type': 'Swiss Ephemeris',
            'coordinate_system': 'Sidereal Zodiac (Lahiri)',
            'node_type': 'Mean Node',
            'description': 'Hourly planetary positions calculated using Swiss Ephemeris'
        }
        
        # Tạo tên file
        base_filename = f"output/ephemeris_{year}_{month:02d}"

        csv_filename = f"{base_filename}.csv"
        json_filename = f"{base_filename}.json"
        aspects_csv = f"{base_filename}_aspects.csv"
        aspects_json = f"{base_filename}_aspects.json"
        ingress_csv = f"{base_filename}_ingress.csv"
        ingress_json = f"{base_filename}_ingress.json"
        
        # Xuất dữ liệu
        calc.export_to_csv(monthly_data, csv_filename)
        calc.export_to_json(monthly_data, json_filename, metadata)

        calc.export_to_csv(aspects, aspects_csv)
        calc.export_to_json(aspects, aspects_json, metadata)

        calc.export_to_csv(ingress, ingress_csv)
        calc.export_to_json(ingress, ingress_json, metadata)

        
        print()
        print("🎉 HOÀN THÀNH!")
        print(f"📁 Files đã tạo:")
        print(f"   • {csv_filename} ({os.path.getsize(csv_filename) / 1024 / 1024:.2f} MB)")
        print(f"   • {json_filename} ({os.path.getsize(json_filename) / 1024 / 1024:.2f} MB)")

        # =============================
        # 📅 BỔ SUNG: Xuất file theo ngày
        # =============================
        from collections import defaultdict

        aspects_by_day = defaultdict(list)
        ingress_by_day = defaultdict(list)

        for e in aspects:
            d = e["datetime"].split(" ")[0]
            aspects_by_day[d].append(e)

        for e in ingress:
            d = e["datetime"].split(" ")[0]
            ingress_by_day[d].append(e)

        base_dir = "output"
        os.makedirs(base_dir, exist_ok=True)

        # Tạo folder cho từng ngày trong tháng
        for day in range(1, 32):
            try:
                day_str = f"{year}-{month:02d}-{day:02d}"
                folder = os.path.join(base_dir, day_str)
                os.makedirs(folder, exist_ok=True)

                calc.export_events(aspects_by_day.get(day_str, []),
                                   os.path.join(folder, "aspects.csv"),
                                   os.path.join(folder, "aspects.json"))

                calc.export_events(ingress_by_day.get(day_str, []),
                                   os.path.join(folder, "ingress.csv"),
                                   os.path.join(folder, "ingress.json"))

            except Exception:
                continue

        print("\n📂 Đã xuất thêm dữ liệu chi tiết theo ngày vào thư mục output/")
        
        # Hiển thị sample data
        if monthly_data:
            print(f"\n📋 Sample dữ liệu (bản ghi đầu tiên):")
            sample = monthly_data[0]
            print(f"   Thời gian: {sample['datetime_local']}")
            print(f"   Mặt Trời: {sample['Sun_Sign']} {sample['Sun_Degree']} ({sample['Sun_Motion']})")
            print(f"   Mặt Trăng: {sample['Moon_Sign']} {sample['Moon_Degree']} ({sample['Moon_Motion']})")
            print(f"   Rahu: {sample['Rahu_Sign']} {sample['Rahu_Degree']} ({sample['Rahu_Motion']})")
            print(f"   Ketu: {sample['Ketu_Sign']} {sample['Ketu_Degree']} ({sample['Ketu_Motion']})")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
