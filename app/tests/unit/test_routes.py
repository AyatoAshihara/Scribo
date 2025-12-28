"""
単体テスト: ヘルスチェック・基本ルート
"""

import pytest


class TestHealthCheck:
    """ヘルスチェックエンドポイントのテスト"""
    
    @pytest.mark.unit
    def test_health_check_returns_200(self, client):
        """ヘルスチェックが200を返すこと"""
        response = client.get("/health")
        
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_health_check_response_format(self, client):
        """ヘルスチェックのレスポンス形式が正しいこと"""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "app" in data
        assert data["app"] == "Scribo"


class TestIndexPage:
    """トップページのテスト"""
    
    @pytest.mark.unit
    def test_index_returns_200(self, client):
        """トップページが200を返すこと"""
        response = client.get("/")
        
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_index_returns_html(self, client):
        """トップページがHTMLを返すこと"""
        response = client.get("/")
        
        assert "text/html" in response.headers["content-type"]


class TestSecurityHeaders:
    """セキュリティヘッダーのテスト"""
    
    @pytest.mark.unit
    def test_x_content_type_options_header(self, client):
        """X-Content-Type-Options ヘッダーが設定されていること"""
        response = client.get("/health")
        
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
    
    @pytest.mark.unit
    def test_x_frame_options_header(self, client):
        """X-Frame-Options ヘッダーが設定されていること"""
        response = client.get("/health")
        
        assert response.headers.get("X-Frame-Options") == "DENY"
    
    @pytest.mark.unit
    def test_x_xss_protection_header(self, client):
        """X-XSS-Protection ヘッダーが設定されていること"""
        response = client.get("/health")
        
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    
    @pytest.mark.unit
    def test_referrer_policy_header(self, client):
        """Referrer-Policy ヘッダーが設定されていること"""
        response = client.get("/health")
        
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    
    @pytest.mark.unit
    def test_content_security_policy_header(self, client):
        """Content-Security-Policy ヘッダーが設定されていること"""
        response = client.get("/health")
        
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src" in csp
