import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urlparse
import logging
import random
from decorators import retry_with_backoff
from proxy_manager import ProxyManager
from selenium.webdriver.common.keys import Keys

class ScienceDirectAccessor:
    def __init__(self):
        """初始化 ScienceDirectAccessor"""
        load_dotenv()  # 加载环境变量
        self._load_credentials()
        self.driver = None
        self.cookies = None
        self.session = requests.Session()
        self.ua = UserAgent()
        self.setup_logging()
        self.last_request_time = 0
        self.min_request_interval = 5  # 最小请求间隔（秒）
        self.session_start_time = time.time()
        self.max_session_duration = 3600  # 最大会话时长（1小时）
        self.proxy_manager = ProxyManager()
        
    def _load_credentials(self):
        """安全地加载凭据"""
        try:
            self.username = os.getenv('SJTU_USERNAME')
            self.password = os.getenv('SJTU_PASSWORD')
            
            if not self.username or not self.password:
                raise ValueError("未找到必要的登录凭据")
                
            # 检查凭据格式
            if not self._validate_credentials():
                raise ValueError("登录凭据格式无效")
                
        except Exception as e:
            logging.error(f"加载登录凭据失败: {str(e)}")
            raise
            
    def _validate_credentials(self):
        """验证凭据格式"""
        if not isinstance(self.username, str) or not isinstance(self.password, str):
            return False
        # 验证邮箱格式
        if not self.username.endswith('@sjtu.edu.cn'):
            return False
        # 验证密码复杂度
        if len(self.password) < 8:
            return False
        return True
        
    def setup_driver(self):
        """设置 Selenium WebDriver 使用 Edge"""
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.service import Service
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            options = webdriver.EdgeOptions()
            
            # 基本设置
            options.add_argument('--log-level=3')
            options.add_argument('--silent')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # 增强反自动化检测
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 随机化浏览器指纹
            screen_width = random.randint(1024, 1920)
            screen_height = random.randint(768, 1080)
            options.add_argument(f'--window-size={screen_width},{screen_height}')
            
            # 设置随机时区
            timezones = ['Asia/Shanghai', 'Asia/Hong_Kong', 'Asia/Singapore']
            options.add_argument(f'--timezone={random.choice(timezones)}')
            
            # 设置随机语言
            languages = ['zh-CN,zh;q=0.9,en;q=0.8', 'en-US,en;q=0.9,zh-CN;q=0.8']
            options.add_argument(f'--lang={random.choice(languages)}')
            
            # 使用 webdriver_manager 自动管理 EdgeDriver
            service = Service(EdgeChromiumDriverManager().install())
            service.log_path = 'NUL'
            
            self.driver = webdriver.Edge(service=service, options=options)
            
            # 执行增强的反检测 JavaScript
            stealth_js = """
                // 基础 webdriver 属性隐藏
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 修改 navigator 属性
                const newProto = navigator.__proto__;
                delete newProto.webdriver;
                navigator.__proto__ = newProto;
                
                // 随机化硬件信息
                const HARDWARE_CONCURRENCY = Math.floor(Math.random() * 8) + 4;
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => HARDWARE_CONCURRENCY
                });
                
                // 随机化设备内存
                const DEVICE_MEMORY = [2, 4, 8, 16][Math.floor(Math.random() * 4)];
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => DEVICE_MEMORY
                });
                
                // 添加真实的 plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        const plugins = [
                            {name: 'PDF Viewer', filename: 'internal-pdf-viewer'},
                            {name: 'Chrome PDF Viewer', filename: 'chrome-pdf-viewer'},
                            {name: 'Microsoft Edge PDF Viewer', filename: 'edge-pdf-viewer'},
                            {name: 'WebKit built-in PDF', filename: 'webkit-pdf-viewer'}
                        ];
                        const pluginArray = [];
                        plugins.forEach(p => {
                            const plugin = {
                                name: p.name,
                                filename: p.filename,
                                description: p.name,
                                length: 1
                            };
                            pluginArray.push(plugin);
                        });
                        return pluginArray;
                    }
                });
                
                // 添加 canvas 指纹随机化
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {
                    const context = originalGetContext.apply(this, arguments);
                    if (type === '2d') {
                        const originalFillText = context.fillText;
                        context.fillText = function() {
                            context.shadowColor = `rgb(${Math.random()*255},${Math.random()*255},${Math.random()*255})`;
                            context.shadowBlur = Math.random() * 3;
                            return originalFillText.apply(this, arguments);
                        }
                    }
                    return context;
                };
            """
            
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
            
            # 设置页面加载超时时间
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logging.info("Edge WebDriver 设置成功")
            return True
        except Exception as e:
            logging.error(f"设置 Edge WebDriver 失败: {str(e)}")
            if "No module named 'webdriver_manager'" in str(e):
                logging.error("请先安装 webdriver_manager: pip install webdriver-manager")
            elif "Could not reach host" in str(e):
                logging.error("网络连接失败，请检查网络连接")
            return False

    def _handle_captcha(self):
        """处理人机验证"""
        try:
            # 检查是否存在验证码iframe
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                if "challenge" in iframe.get_attribute("src").lower():
                    logging.info("检测到人机验证，等待手动处理...")
                    # 等待用户手动处理验证码
                    while True:
                        time.sleep(5)
                        if "sciencedirect.com" in self.driver.current_url:
                            logging.info("人机验证已完成")
                            return True
                        current_url = self.driver.current_url
                        if "error" in current_url.lower() or "blocked" in current_url.lower():
                            logging.error("访问被阻止")
                            return False
            return True
        except Exception as e:
            logging.error(f"处理人机验证时出错: {str(e)}")
            return False

    def login(self):
        """登录到 ScienceDirect"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if not self.setup_driver():
                    raise Exception("WebDriver 设置失败")
                
                logging.info(f"开始登录流程... (尝试 {retry_count + 1}/{max_retries})")
                
                # 直接访问上海交大的 SSO 登录页面
                sso_url = "https://sso.sciencedirect.com/v1/login?federation=https://jaccount.sjtu.edu.cn/idp&returnUrl=https://www.sciencedirect.com"
                self.driver.get(sso_url)
                logging.info("访问 SSO 登录页面")
                time.sleep(5)
                
                # 检查是否需要处理人机验证
                if not self._handle_captcha():
                    raise Exception("人机验证失败")
                
                # 保存当前页面源码
                with open(f'sso_page_{retry_count}.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                
                try:
                    # 等待重定向到 jaccount 登录页面
                    jaccount_wait_start = time.time()
                    while time.time() - jaccount_wait_start < 30:  # 30秒超时
                        if "jaccount.sjtu.edu.cn" in self.driver.current_url:
                            break
                        # 再次检查人机验证
                        if not self._handle_captcha():
                            raise Exception("人机验证失败")
                        time.sleep(1)
                    else:
                        raise TimeoutException("等待重定向到jaccount超时")
                    
                    logging.info(f"当前页面URL: {self.driver.current_url}")
                    
                    try:
                        # 等待用户名和密码输入框出现
                        username_input = WebDriverWait(self.driver, 30).until(
                            EC.presence_of_element_located((By.ID, "user"))
                        )
                        password_input = WebDriverWait(self.driver, 30).until(
                            EC.presence_of_element_located((By.ID, "pass"))
                        )
                        
                        # 清除输入框并输入凭据
                        username_input.clear()
                        password_input.clear()
                        time.sleep(2)
                        
                        # 输入用户名和密码
                        username_input.send_keys(self.username)
                        time.sleep(1)
                        password_input.send_keys(self.password)
                        logging.info("输入用户名和密码")
                        time.sleep(2)
                        
                        # 点击登录按钮
                        login_button = WebDriverWait(self.driver, 30).until(
                            EC.element_to_be_clickable((By.ID, "submit-button"))
                        )
                        self.driver.execute_script("arguments[0].click();", login_button)
                        logging.info("点击登录按钮")
                        
                        # 等待登录成功并重定向
                        redirect_wait_start = time.time()
                        success = False
                        while time.time() - redirect_wait_start < 30:  # 30秒超时
                            current_url = self.driver.current_url
                            # 再次检查人机验证
                            if not self._handle_captcha():
                                raise Exception("人机验证失败")
                            if "sciencedirect.com" in current_url:
                                success = True
                                break
                            time.sleep(1)
                        
                        if success:
                            # 等待页面完全加载
                            time.sleep(5)
                            
                            # 保存登录后的页面源码以供调试
                            with open(f'after_login_{retry_count}.html', 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            
                            # 保存 cookies
                            self.cookies = self.driver.get_cookies()
                            self._save_cookies()
                            logging.info("登录成功，保存 cookies")
                            return True
                        else:
                            logging.error(f"登录后URL不正确: {self.driver.current_url}")
                            # 保存页面源码以供调试
                            with open(f'redirect_error_{retry_count}.html', 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            raise TimeoutException("等待重定向到ScienceDirect超时")
                        
                    except Exception as e:
                        logging.error(f"登录页面元素定位失败: {str(e)}")
                        # 保存页面源码以供调试
                        with open(f'login_error_{retry_count}.html', 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        raise
                    
                except Exception as e:
                    logging.error(f"导航到登录页面失败: {str(e)}")
                    if self.driver:
                        # 保存截图
                        self.driver.save_screenshot(f'navigation_error_{retry_count}.png')
                    raise
                    
            except Exception as e:
                logging.error(f"登录尝试 {retry_count + 1} 失败: {str(e)}")
                if self.driver:
                    # 保存截图
                    self.driver.save_screenshot(f'login_error_{retry_count}.png')
                retry_count += 1
                if retry_count < max_retries:
                    logging.info(f"等待 {retry_count * 5} 秒后重试...")
                    time.sleep(retry_count * 5)  # 递增等待时间
                    if self.driver:
                        self.driver.quit()
                        self.driver = None
                continue
            finally:
                if self.driver:
                    self.driver.quit()
                    self.driver = None
        
        logging.error("所有登录尝试都失败了")
        return False
        
    def _check_already_logged_in(self):
        """检查是否已经登录"""
        try:
            # 检查页面上是否有用户头像或其他登录状态指示器
            avatar = self.driver.find_elements(By.CSS_SELECTOR, "button[data-testid='user-profile-button']")
            if avatar:
                return True
            return False
        except Exception:
            return False

    def _save_cookies(self):
        """保存 cookies 到文件"""
        if self.cookies:
            with open('cookies.json', 'w') as f:
                json.dump(self.cookies, f)
                logging.info("Cookies已保存到文件")
                
    def _load_cookies(self):
        """从文件加载 cookies"""
        try:
            with open('cookies.json', 'r') as f:
                self.cookies = json.load(f)
                return True
        except FileNotFoundError:
            return False

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            filename='sciencedirect_access.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True  # 强制重新配置日志
        )
        # 禁用 selenium 的日志
        logging.getLogger('selenium').setLevel(logging.ERROR)
        # 禁用 urllib3 的日志
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        
    def _enforce_rate_limit(self):
        """强制执行请求频率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logging.info(f"等待 {sleep_time:.2f} 秒以遵守访问频率限制")
            time.sleep(sleep_time)
        self.last_request_time = current_time
        
    def _check_session_validity(self):
        """检查会话是否有效"""
        if time.time() - self.session_start_time > self.max_session_duration:
            logging.info("会话已过期，需要重新登录")
            self.cookies = None
            self.session_start_time = time.time()
            return False
        return True
        
    def _secure_request(self, url, method='get', **kwargs):
        """安全的请求包装器"""
        self._enforce_rate_limit()
        
        if not self._check_session_validity():
            if not self.login():
                raise Exception("会话过期后重新登录失败")
                
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        try:
            response = getattr(self.session, method)(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {str(e)}")
            raise
            
    def get_paper_content(self, url: str) -> dict:
        """获取论文内容（带重试机制）"""
        try:
            # 验证URL是否为ScienceDirect
            if not self._validate_url(url):
                raise ValueError("无效的ScienceDirect URL")
            
            # 如果没有cookies或cookies已过期，重新登录
            if not self._check_cookies_valid():
                logging.info("Cookies无效或不存在，开始重新登录")
                if not self.login():
                    raise Exception("登录失败")
            
            # 使用安全的请求方法访问论文页面
            response = self._secure_request(url)
            
            # 解析页面内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 检查是否需要重新登录
            if self._needs_relogin(soup):
                logging.info("检测到需要重新登录")
                if not self.login():
                    raise Exception("重新登录失败")
                response = self._secure_request(url)
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取论文信息
            paper_info = {
                'title': self._extract_title(soup),
                'authors': self._extract_authors(soup),
                'abstract': self._extract_abstract(soup),
                'keywords': self._extract_keywords(soup),
                'full_text': self._extract_full_text(soup),
                'doi': self._extract_doi(soup),
                'accessed_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'url': url
            }
            
            # 验证提取的内容
            if not self._validate_paper_content(paper_info):
                raise ValueError("提取的论文内容不完整或无效")
            
            logging.info(f"成功获取论文内容：{paper_info['title']}")
            return paper_info
            
        except Exception as e:
            logging.error(f"获取论文内容失败：{str(e)}")
            raise
            
    def _validate_url(self, url):
        """验证URL是否为有效的ScienceDirect链接"""
        try:
            parsed = urlparse(url)
            return parsed.netloc == 'www.sciencedirect.com'
        except:
            return False
            
    def _check_cookies_valid(self):
        """检查cookies是否有效"""
        if not self._load_cookies():
            return False
        
        # 尝试访问ScienceDirect首页验证cookies
        headers = {'User-Agent': self.ua.random}
        try:
            response = self.session.get('https://www.sciencedirect.com', headers=headers)
            return 'Sign in' not in response.text
        except:
            return False
            
    def _load_cookies_to_session(self):
        """将cookies加载到requests session中"""
        if self.cookies:
            for cookie in self.cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])
                
    def _extract_title(self, soup):
        """提取论文标题"""
        title_elem = soup.find('span', class_='title-text')
        return title_elem.text.strip() if title_elem else ''
        
    def _extract_authors(self, soup):
        """提取作者信息"""
        authors = []
        author_elems = soup.find_all('a', class_='author')
        for author in author_elems:
            authors.append(author.text.strip())
        return authors
        
    def _extract_abstract(self, soup):
        """提取摘要"""
        abstract_elem = soup.find('div', class_='abstract')
        return abstract_elem.text.strip() if abstract_elem else ''
        
    def _extract_keywords(self, soup):
        """提取关键词"""
        keywords = []
        keyword_elems = soup.find_all('div', class_='keyword')
        for keyword in keyword_elems:
            keywords.append(keyword.text.strip())
        return keywords
        
    def _extract_full_text(self, soup):
        """提取全文内容"""
        content_elem = soup.find('div', id='body')
        return content_elem.text.strip() if content_elem else ''
        
    def _extract_doi(self, soup):
        """提取DOI"""
        doi_elem = soup.find('a', class_='doi')
        return doi_elem.text.strip() if doi_elem else ''

    def test_direct_access(self):
        """测试直接访问论文"""
        try:
            url = "https://www.sciencedirect.com/science/article/abs/pii/S0927776522004507"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            # 直接访问论文页面
            response = requests.get(url, headers=headers)
            
            # 保存响应内容用于分析
            with open('direct_access.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # 打印响应状态和URL
            print(f"响应状态码: {response.status_code}")
            print(f"最终URL: {response.url}")
            
            return response.text
            
        except Exception as e:
            print(f"直接访问失败: {str(e)}")
            return None

    def _needs_relogin(self, soup):
        """检查是否需要重新登录"""
        # 检查是否存在登录按钮或其他登录指示器
        login_indicators = [
            'Sign in',
            'Please sign in',
            'Access denied',
            'Please log in',
            '请登录',
            '访问受限'
        ]
        page_text = soup.get_text().lower()
        return any(indicator.lower() in page_text for indicator in login_indicators)
        
    def _validate_paper_content(self, paper_info):
        """验证提取的论文内容是否有效"""
        required_fields = ['title', 'authors', 'abstract']
        return all(paper_info.get(field) for field in required_fields)

if __name__ == "__main__":
    accessor = ScienceDirectAccessor()
    
    # 先测试直接访问
    print("正在测试直接访问...")
    content = accessor.test_direct_access()
    
    if content:
        print("\n开始尝试自动登录...")
        try:
            paper_content = accessor.get_paper_content("https://www.sciencedirect.com/science/article/abs/pii/S0927776522004507")
            print("论文标题:", paper_content['title'])
            print("作者:", ", ".join(paper_content['authors']))
            print("摘要:", paper_content['abstract'][:200] + "...")
        except Exception as e:
            print("获取论文失败:", str(e))
