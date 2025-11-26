#!/usr/bin/env python3
"""
기존 테스트 레코드의 PR 제목과 브랜치 정보 업데이트 (간단 버전)
"""
import sys
import os
from github import Github

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.models import init_db, get_db, Test

def update_pr_title():
    """기존 테스트 레코드의 PR 정보 업데이트"""
    init_db()
    db = next(get_db())
    
    try:
        # pr_title이나 branch_name이 없는 테스트 조회
        test = db.query(Test).filter(Test.pr_number == 1).first()
        
        if not test:
            print("❌ 테스트 레코드를 찾을 수 없습니다")
            return
        
        print(f"📋 업데이트할 테스트: PR #{test.pr_number}")
        print(f"   현재 제목: {test.pr_title}")
        print(f"   현재 브랜치: {test.branch_name}\n")
        
        # GitHub API 연결 (PAT 없이 Public 저장소 접근)
        g = Github()
        repo = g.get_repo(test.repo_full_name)
        pr = repo.get_pull(test.pr_number)
        
        print(f"✅ GitHub에서 PR 정보 가져옴:")
        print(f"   제목: {pr.title}")
        print(f"   브랜치: {pr.head.ref}\n")
        
        # 업데이트
        test.pr_title = pr.title
        test.branch_name = pr.head.ref
        db.commit()
        
        print(f"✅ 업데이트 완료!")
        print(f"   새 제목: {test.pr_title}")
        print(f"   새 브랜치: {test.branch_name}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_pr_title()

