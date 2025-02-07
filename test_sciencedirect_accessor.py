import unittest
from unittest.mock import patch, MagicMock
from plugin import ScienceDirectAccessor
import time
from bs4 import BeautifulSoup

class TestScienceDirectAccessor(unittest.TestCase):
    def setUp(self):
        self.accessor = ScienceDirectAccessor()
        
    def test_validate_url(self):
        """测试URL验证"""
        valid_url = "https://www.sciencedirect.com/science/article/abs/pii/123456"
        invalid_url = "https://example.com/paper"
        
        self.assertTrue(self.accessor._validate_url(valid_url))
        self.assertFalse(self.accessor._validate_url(invalid_url))
        
    def test_validate_credentials(self):
        """测试凭据验证"""
        # 测试有效的凭据
        self.accessor.username = "test@sjtu.edu.cn"
        self.accessor.password = "password123"
        self.assertTrue(self.accessor._validate_credentials())
        
        # 测试无效的邮箱
        self.accessor.username = "test@example.com"
        self.assertFalse(self.accessor._validate_credentials())
        
        # 测试密码太短
        self.accessor.username = "test@sjtu.edu.cn"
        self.accessor.password = "123"
        self.assertFalse(self.accessor._validate_credentials())
        
    def test_rate_limit(self):
        """测试访问频率限制"""
        start_time = time.time()
        self.accessor._enforce_rate_limit()
        self.accessor._enforce_rate_limit()
        end_time = time.time()
        
        # 验证两次请求之间的间隔是否符合要求
        self.assertGreaterEqual(end_time - start_time, self.accessor.min_request_interval)
        
    def test_session_validity(self):
        """测试会话有效性检查"""
        # 测试新会话
        self.assertTrue(self.accessor._check_session_validity())
        
        # 测试过期会话
        self.accessor.session_start_time = time.time() - (self.accessor.max_session_duration + 1)
        self.assertFalse(self.accessor._check_session_validity())
        
    def test_needs_relogin(self):
        """测试重新登录检测"""
        # 模拟需要登录的页面
        html_needs_login = '<html><body>Please sign in to access this content</body></html>'
        soup_needs_login = BeautifulSoup(html_needs_login, 'html.parser')
        self.assertTrue(self.accessor._needs_relogin(soup_needs_login))
        
        # 模拟正常页面
        html_normal = '<html><body>Welcome to ScienceDirect</body></html>'
        soup_normal = BeautifulSoup(html_normal, 'html.parser')
        self.assertFalse(self.accessor._needs_relogin(soup_normal))
        
    def test_validate_paper_content(self):
        """测试论文内容验证"""
        # 测试完整的论文信息
        valid_paper = {
            'title': 'Test Paper',
            'authors': ['Author 1', 'Author 2'],
            'abstract': 'Test abstract',
            'keywords': ['keyword1', 'keyword2'],
            'full_text': 'Test full text',
            'doi': '10.1234/test'
        }
        self.assertTrue(self.accessor._validate_paper_content(valid_paper))
        
        # 测试缺少必要字段的论文信息
        invalid_paper = {
            'title': 'Test Paper',
            'keywords': ['keyword1', 'keyword2']
        }
        self.assertFalse(self.accessor._validate_paper_content(invalid_paper))
        
    @patch('selenium.webdriver.Chrome')
    def test_login(self, mock_chrome):
        """测试登录功能"""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # 模拟成功登录
        mock_driver.get_cookies.return_value = [{'name': 'test', 'value': 'test'}]
        mock_driver.current_url = 'https://www.sciencedirect.com'
        
        self.assertTrue(self.accessor.login())
        
    def test_secure_request(self):
        """测试安全请求包装器"""
        with patch('requests.Session.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            response = self.accessor._secure_request('https://www.sciencedirect.com')
            
            # 验证请求头
            self.assertIn('User-Agent', mock_get.call_args[1]['headers'])
            self.assertIn('Sec-Fetch-Mode', mock_get.call_args[1]['headers'])
            
    def test_paper_content_extraction(self):
        """测试论文内容提取"""
        test_html = '''
        <html>
            <span class="title-text">Test Paper Title</span>
            <a class="author">John Doe</a>
            <div class="abstract">Test abstract</div>
            <div class="keyword">keyword1</div>
            <div id="body">Full text content</div>
            <a class="doi">10.1234/test</a>
        </html>
        '''
        
        with patch('requests.Session.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = test_html
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            content = self.accessor.get_paper_content(
                "https://www.sciencedirect.com/science/article/abs/pii/test"
            )
            
            self.assertEqual(content['title'], 'Test Paper Title')
            self.assertEqual(content['authors'], ['John Doe'])
            self.assertEqual(content['abstract'], 'Test abstract')
            self.assertEqual(content['keywords'], ['keyword1'])
            self.assertEqual(content['full_text'], 'Full text content')
            self.assertEqual(content['doi'], '10.1234/test')
            self.assertIn('accessed_time', content)
            self.assertIn('url', content)

if __name__ == '__main__':
    unittest.main() 