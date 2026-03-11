# -*- coding: utf-8 -*-
"""
로컬 SQLite 데이터베이스 관리

모든 데이터를 로컬 kis_data.db 파일에 저장
- 카탈로그 (차단기, 외함)
- 거래처
- 견적 이력
- ERP 데이터
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


# 데이터베이스 파일 경로 (프로젝트 루트)
DB_PATH = Path(__file__).parent.parent.parent.parent / "kis_data.db"


def get_connection() -> sqlite3.Connection:
    """SQLite 연결 반환"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 딕셔너리처럼 접근 가능
    return conn


def init_database():
    """데이터베이스 초기화 (테이블 생성)"""
    conn = get_connection()
    cursor = conn.cursor()

    # === 카탈로그 테이블 ===

    # 차단기 카탈로그
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS breakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            category TEXT NOT NULL,
            series TEXT,
            model TEXT NOT NULL,
            poles INTEGER NOT NULL,
            current_a INTEGER NOT NULL,
            frame_af INTEGER,
            breaking_capacity_ka REAL,
            price INTEGER NOT NULL,
            width_mm INTEGER,
            height_mm INTEGER,
            depth_mm INTEGER,
            search_keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 외함 카탈로그
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enclosures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            material TEXT NOT NULL,
            brand TEXT,
            model TEXT NOT NULL,
            width_mm INTEGER NOT NULL,
            height_mm INTEGER NOT NULL,
            depth_mm INTEGER NOT NULL,
            price INTEGER NOT NULL,
            original_category TEXT,
            search_keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # === 거래처 테이블 ===
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT NOT NULL,
            customer_type TEXT DEFAULT '일반',
            business_number TEXT,
            ceo_name TEXT,
            contact_person TEXT,
            phone TEXT,
            fax TEXT,
            email TEXT,
            address TEXT,
            memo TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # === 견적 테이블 ===
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estimates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estimate_number TEXT UNIQUE,
            customer_id INTEGER,
            project_name TEXT,
            status TEXT DEFAULT 'draft',
            total_price INTEGER,
            total_price_with_vat INTEGER,
            estimate_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # === ERP 매출 테이블 ===
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_number TEXT UNIQUE,
            sale_date DATE,
            customer_id INTEGER,
            status TEXT DEFAULT 'confirmed',
            supply_amount INTEGER,
            tax_amount INTEGER,
            total_amount INTEGER,
            memo TEXT,
            items_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # === 설정 테이블 ===
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"[OK] 데이터베이스 초기화 완료: {DB_PATH}")


def import_catalog_from_json(json_path: str = None):
    """
    ai_catalog_v1.json에서 카탈로그 데이터 가져오기
    """
    if json_path is None:
        json_path = Path(__file__).parent.parent.parent.parent / "절대코어파일" / "ai_catalog_v1.json"

    with open(json_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    conn = get_connection()
    cursor = conn.cursor()

    # 기존 데이터 삭제
    cursor.execute("DELETE FROM breakers")
    cursor.execute("DELETE FROM enclosures")

    # 차단기 가져오기
    breaker_count = 0
    for b in catalog.get('breakers', []):
        dims = b.get('dimensions', {})
        cursor.execute("""
            INSERT INTO breakers (brand, category, series, model, poles, current_a, frame_af,
                                  breaking_capacity_ka, price, width_mm, height_mm, depth_mm, search_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b.get('brand', ''),
            b.get('category', ''),
            b.get('series', ''),
            b.get('model', ''),
            b.get('poles', 0),
            b.get('current_a', 0),
            b.get('frame_af', 0),
            b.get('breaking_capacity_ka', 0),
            b.get('price', 0),
            dims.get('width_mm', 0),
            dims.get('height_mm', 0),
            dims.get('depth_mm', 0),
            json.dumps(b.get('search_keywords', []), ensure_ascii=False)
        ))
        breaker_count += 1

    # 외함 가져오기
    enclosure_count = 0
    for e in catalog.get('enclosures', []):
        cursor.execute("""
            INSERT INTO enclosures (type, material, brand, model, width_mm, height_mm, depth_mm,
                                    price, original_category, search_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            e.get('type', ''),
            e.get('material', ''),
            e.get('brand', ''),
            e.get('model', ''),
            e.get('width_mm', 0),
            e.get('height_mm', 0),
            e.get('depth_mm', 0),
            e.get('price', 0),
            e.get('original_category', ''),
            json.dumps(e.get('search_keywords', []), ensure_ascii=False)
        ))
        enclosure_count += 1

    conn.commit()
    conn.close()

    print(f"[OK] 카탈로그 가져오기 완료")
    print(f"    - 차단기: {breaker_count}개")
    print(f"    - 외함: {enclosure_count}개")


# === 차단기 조회 ===

def search_breaker(brand: str = None, category: str = None, poles: int = None,
                   current_a: int = None, series: str = None) -> list[dict]:
    """차단기 검색"""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM breakers WHERE 1=1"
    params = []

    if brand:
        query += " AND brand LIKE ?"
        params.append(f"%{brand}%")
    if category:
        query += " AND category = ?"
        params.append(category)
    if poles:
        query += " AND poles = ?"
        params.append(poles)
    if current_a:
        query += " AND current_a = ?"
        params.append(current_a)
    if series:
        query += " AND series LIKE ?"
        params.append(f"%{series}%")

    query += " ORDER BY price ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_breaker_by_spec(category: str, poles: int, current_a: int, prefer_economy: bool = True) -> dict | None:
    """스펙으로 차단기 조회 (경제형 우선)"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT * FROM breakers
        WHERE category = ? AND poles = ? AND current_a = ?
        ORDER BY price ASC
    """

    cursor.execute(query, (category, poles, current_a))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    results = [dict(row) for row in rows]

    if prefer_economy:
        # 경제형 우선
        for r in results:
            if '경제' in (r.get('series') or ''):
                return r

    return results[0]  # 가장 저렴한 것


# === 외함 조회 ===

def search_enclosure(enc_type: str = None, material: str = None,
                     width: int = None, height: int = None, depth: int = None) -> list[dict]:
    """외함 검색"""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM enclosures WHERE 1=1"
    params = []

    if enc_type:
        query += " AND type LIKE ?"
        params.append(f"%{enc_type}%")
    if material:
        query += " AND material LIKE ?"
        params.append(f"%{material}%")
    if width:
        query += " AND width_mm = ?"
        params.append(width)
    if height:
        query += " AND height_mm = ?"
        params.append(height)
    if depth:
        query += " AND depth_mm = ?"
        params.append(depth)

    query += " ORDER BY price ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_enclosure_by_size(enc_type: str, material: str, width: int, height: int, depth: int) -> dict | None:
    """크기로 외함 조회 (정확 매칭)"""
    results = search_enclosure(enc_type, material, width, height, depth)
    return results[0] if results else None


# === 거래처 관리 ===

def add_customer(name: str, **kwargs) -> int:
    """거래처 추가"""
    conn = get_connection()
    cursor = conn.cursor()

    # 거래처 코드 자동 생성 (C0001, C0002, ...)
    cursor.execute("SELECT MAX(CAST(SUBSTR(code, 2) AS INTEGER)) FROM customers WHERE code LIKE 'C%'")
    result = cursor.fetchone()[0]
    next_num = (result or 0) + 1
    code = f"C{next_num:04d}"

    cursor.execute("""
        INSERT INTO customers (code, name, customer_type, business_number, ceo_name,
                               contact_person, phone, fax, email, address, memo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code, name,
        kwargs.get('customer_type', '일반'),
        kwargs.get('business_number'),
        kwargs.get('ceo_name'),
        kwargs.get('contact_person'),
        kwargs.get('phone'),
        kwargs.get('fax'),
        kwargs.get('email'),
        kwargs.get('address'),
        kwargs.get('memo')
    ))

    customer_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return customer_id


def get_customer(customer_id: int) -> dict | None:
    """거래처 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def search_customers(keyword: str = None) -> list[dict]:
    """거래처 검색"""
    conn = get_connection()
    cursor = conn.cursor()

    if keyword:
        cursor.execute("""
            SELECT * FROM customers
            WHERE name LIKE ? OR code LIKE ? OR contact_person LIKE ?
            ORDER BY name
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    else:
        cursor.execute("SELECT * FROM customers ORDER BY name")

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# === 견적 관리 ===

def save_estimate(customer_id: int, project_name: str, estimate_data: dict,
                  total_price: int, total_price_with_vat: int) -> int:
    """견적 저장"""
    conn = get_connection()
    cursor = conn.cursor()

    # 견적 번호 자동 생성 (E2024-0001, ...)
    year = datetime.now().year
    cursor.execute(
        "SELECT MAX(CAST(SUBSTR(estimate_number, 7) AS INTEGER)) FROM estimates WHERE estimate_number LIKE ?",
        (f"E{year}-%",)
    )
    result = cursor.fetchone()[0]
    next_num = (result or 0) + 1
    estimate_number = f"E{year}-{next_num:04d}"

    cursor.execute("""
        INSERT INTO estimates (estimate_number, customer_id, project_name, status,
                               total_price, total_price_with_vat, estimate_data)
        VALUES (?, ?, ?, 'draft', ?, ?, ?)
    """, (
        estimate_number, customer_id, project_name,
        total_price, total_price_with_vat,
        json.dumps(estimate_data, ensure_ascii=False)
    ))

    estimate_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return estimate_id


def get_estimate(estimate_id: int) -> dict | None:
    """견적 조회"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM estimates WHERE id = ?", (estimate_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        result = dict(row)
        if result.get('estimate_data'):
            result['estimate_data'] = json.loads(result['estimate_data'])
        return result
    return None


def list_estimates(customer_id: int = None, limit: int = 100) -> list[dict]:
    """견적 목록"""
    conn = get_connection()
    cursor = conn.cursor()

    if customer_id:
        cursor.execute("""
            SELECT e.*, c.name as customer_name
            FROM estimates e
            LEFT JOIN customers c ON e.customer_id = c.id
            WHERE e.customer_id = ?
            ORDER BY e.created_at DESC
            LIMIT ?
        """, (customer_id, limit))
    else:
        cursor.execute("""
            SELECT e.*, c.name as customer_name
            FROM estimates e
            LEFT JOIN customers c ON e.customer_id = c.id
            ORDER BY e.created_at DESC
            LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# === 초기화 실행 ===

if __name__ == "__main__":
    print("=== 로컬 데이터베이스 초기화 ===")
    init_database()

    print("\n=== 카탈로그 가져오기 ===")
    import_catalog_from_json()

    print("\n=== 테스트 조회 ===")

    # 차단기 테스트
    breakers = search_breaker(category='MCCB', poles=4, current_a=100)
    print(f"MCCB 4P 100A: {len(breakers)}개 찾음")
    if breakers:
        print(f"  - 첫 번째: {breakers[0]['model']} ({breakers[0]['price']:,}원)")

    # 외함 테스트
    enclosures = search_enclosure(enc_type='옥외노출', material='SUS', width=700, height=1300, depth=200)
    print(f"옥외노출 SUS 700x1300x200: {len(enclosures)}개 찾음")
    if enclosures:
        print(f"  - 첫 번째: {enclosures[0]['model']} ({enclosures[0]['price']:,}원)")
