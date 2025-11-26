#!/usr/bin/env python3
"""
Test 테이블에 pr_title과 branch_name 컬럼 추가 마이그레이션
"""
import sys
import os
import sqlite3

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_test_table():
    """Test 테이블에 pr_title과 branch_name 컬럼 추가"""
    db_path = os.path.join(os.path.dirname(__file__), 'nightwatch.db')
    
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 기존 컬럼 확인
        cursor.execute("PRAGMA table_info(tests)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # pr_title 컬럼 추가
        if 'pr_title' not in columns:
            print("➕ pr_title 컬럼 추가 중...")
            cursor.execute("ALTER TABLE tests ADD COLUMN pr_title VARCHAR(511)")
            print("✅ pr_title 컬럼 추가 완료")
        else:
            print("ℹ️ pr_title 컬럼이 이미 존재합니다")
        
        # branch_name 컬럼 추가
        if 'branch_name' not in columns:
            print("➕ branch_name 컬럼 추가 중...")
            cursor.execute("ALTER TABLE tests ADD COLUMN branch_name VARCHAR(255)")
            print("✅ branch_name 컬럼 추가 완료")
        else:
            print("ℹ️ branch_name 컬럼이 이미 존재합니다")
        
        conn.commit()
        print("\n✅ 마이그레이션 완료!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_test_table()

