import logging
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

class ColoredFormatter(logging.Formatter):
    """自定义的彩色日志格式化器"""
    
    # 定义颜色代码
    COLORS = {
        logging.DEBUG: '\033[34m',    # 蓝色 - DEBUG (10)
        logging.INFO: '\033[33m',     # 黄色 - INFO (20)
        logging.WARNING: '\033[35m',  # 紫色 - WARNING (30)
        logging.ERROR: '\033[31m',    # 红色 - ERROR (40)
        logging.CRITICAL: '\033[41m', # 红底 - CRITICAL (50)
        15: '\033[35m',              # 紫色 - TRACE (15)
        'RESET': '\033[0m'
    }

    def format(self, record):
        record.msg = f"{self.COLORS.get(record.levelno, '')}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)

class Logger:
    """日志处理类"""
    
    def __init__(self, name: str = "app", log_dir: str = "logs"):
        """初始化日志处理器
        
        Args:
            name: 日志器名称
            log_dir: 日志文件存储目录
        """
        # 创建自定义日志级别 TRACE
        logging.TRACE = 15
        logging.addLevelName(logging.TRACE, 'TRACE')
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 确保日志目录存在
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志格式
        self.formatter = ColoredFormatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 添加控制台处理器
        self._add_console_handler()
        
        # 添加文件处理器
        self._add_file_handler()
    
    def _add_console_handler(self):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """添加文件处理器"""
        # 生成日志文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f"{timestamp}.log"
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
    
    def trace(self, message: str):
        """输出TRACE级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.log(logging.TRACE, message)
    
    def debug(self, message: str):
        """输出DEBUG级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.debug(message)
    
    def info(self, message: str):
        """输出INFO级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.info(message)
    
    def error(self, message: str):
        """输出ERROR级别日志
        
        Args:
            message: 日志消息
        """
        self.logger.error(message)
    
    @staticmethod
    def get_logger(name: str = "app", log_dir: str = "logs") -> 'Logger':
        """获取日志器实例
        
        Args:
            name: 日志器名称
            log_dir: 日志文件存储目录
            
        Returns:
            Logger: 日志器实例
        """
        return Logger(name, log_dir)

# 创建默认日志器
default_logger = Logger.get_logger()

def get_logger(name: Optional[str] = None) -> Logger:
    """获取日志器
    
    Args:
        name: 日志器名称（可选）
        
    Returns:
        Logger: 日志器实例
    """
    if name:
        return Logger.get_logger(name)
    return default_logger 

if __name__ == "__main__":
    # 创建一个测试用的日志器
    logger = Logger.get_logger("test_logger", "test_logs")
    
    # 使用不同级别记录日志
    logger.trace("这是一条跟踪日志 - 用于详细的程序执行跟踪")
    logger.debug("这是一条调试日志 - 用于调试信息")
    logger.info("这是一条信息日志 - 用于一般信息")
    logger.error("这是一条错误日志 - 用于错误信息")
    
    # 演示在不同场景下使用日志
    # 1. 程序启动
    logger.info("程序启动")
    
    # 2. 模拟配置加载
    logger.debug("正在加载配置文件...")
    try:
        # 模拟配置加载过程
        config = {"host": "localhost", "port": 8080}
        logger.info(f"配置加载成功: {config}")
    except Exception as e:
        logger.error(f"配置加载失败: {str(e)}")
    
    # 3. 模拟函数调用跟踪
    def process_data():
        logger.trace("进入 process_data 函数")
        try:
            # 模拟数据处理
            logger.debug("正在处理数据...")
            # 处理逻辑...
            logger.info("数据处理完成")
        except Exception as e:
            logger.error(f"数据处理出错: {str(e)}")
        finally:
            logger.trace("离开 process_data 函数")
    
    # 调用示例函数
    process_data()
    
    # 4. 模拟错误处理
    try:
        logger.debug("尝试执行可能出错的操作")
        raise ValueError("模拟的错误情况")
    except Exception as e:
        logger.error(f"操作失败: {str(e)}")
    
    # 5. 展示不同类型的信息
    logger.info("系统状态: 正常运行")
    logger.debug("内存使用: 1024MB")
    logger.trace("正在执行事务: TX_001")
    logger.error("发现异常: 连接超时")
    
    # 6. 模拟程序结束
    logger.info("程序正常退出")
    
    print("\n日志文件已生成在 'test_logs' 目录中") 