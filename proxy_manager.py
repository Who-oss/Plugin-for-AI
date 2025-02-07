import os
import json
import time
import random
import requests
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

class ProxyManager:
    def __init__(self):
        load_dotenv()
        self.proxy_api = os.getenv('PROXY_API')
        self.proxy_list = []
        self.last_update = 0
        self.update_interval = 300  # 5分钟更新一次代理列表
        
    def _update_proxy_list(self) -> bool:
        """更新代理列表"""
        try:
            if self.proxy_api:
                response = requests.get(self.proxy_api)
                if response.status_code == 200:
                    proxies = response.json()
                    if isinstance(proxies, list):
                        self.proxy_list = proxies
                        self.last_update = time.time()
                        logging.info(f"成功更新代理列表，获取到 {len(proxies)} 个代理")
                        return True
            return False
        except Exception as e:
            logging.error(f"更新代理列表失败: {str(e)}")
            return False
            
    def _validate_proxy(self, proxy: Dict[str, str]) -> bool:
        """验证代理是否可用"""
        try:
            test_url = "https://www.sciencedirect.com"
            response = requests.get(
                test_url,
                proxies=proxy,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            return response.status_code == 200
        except Exception:
            return False
            
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """获取一个可用的代理"""
        # 如果没有配置代理API，返回None
        if not self.proxy_api:
            return None
            
        # 如果代理列表为空或者已经过期，更新代理列表
        if not self.proxy_list or time.time() - self.last_update > self.update_interval:
            if not self._update_proxy_list():
                return None
                
        # 随机选择一个代理并验证
        for _ in range(3):  # 最多尝试3次
            if not self.proxy_list:
                break
                
            proxy = random.choice(self.proxy_list)
            if self._validate_proxy(proxy):
                logging.info(f"找到可用代理: {proxy['http']}")
                return proxy
            else:
                self.proxy_list.remove(proxy)
                
        logging.warning("没有找到可用的代理")
        return None
        
    def remove_proxy(self, proxy: Dict[str, str]):
        """从代理列表中移除无效代理"""
        if proxy in self.proxy_list:
            self.proxy_list.remove(proxy)
            logging.info(f"移除无效代理: {proxy['http']}")
            
    def get_proxy_count(self) -> int:
        """获取当前可用代理数量"""
        return len(self.proxy_list) 