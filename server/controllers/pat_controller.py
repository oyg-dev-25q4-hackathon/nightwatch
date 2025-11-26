# server/controllers/pat_controller.py
"""
PAT 인증 컨트롤러
"""
from flask import request, jsonify
from ..services.pat_auth_service import PATAuthService

class PATController:
    """PAT 인증 컨트롤러"""
    
    def __init__(self):
        self.service = PATAuthService()
    
    def verify_pat(self):
        """PAT 검증"""
        data = request.json
        pat = data.get('pat')
        
        if not pat:
            return jsonify({
                'success': False,
                'error': 'pat is required'
            }), 400
        
        try:
            result = self.service.verify_pat(pat)
            
            if result['valid']:
                return jsonify({
                    'success': True,
                    'username': result['username'],
                    'user_id': result.get('user_id')
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Invalid token')
                }), 401
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def check_repo_access(self):
        """레포지토리 접근 권한 확인"""
        data = request.json
        pat = data.get('pat')
        repo_full_name = data.get('repo_full_name')
        
        if not pat or not repo_full_name:
            return jsonify({
                'success': False,
                'error': 'pat and repo_full_name are required'
            }), 400
        
        try:
            result = self.service.check_repo_access(pat, repo_full_name)
            
            if result['accessible']:
                return jsonify({
                    'success': True,
                    'repo_info': result['repo_info']
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Access denied')
                }), 403
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

