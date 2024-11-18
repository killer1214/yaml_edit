import os
import shutil
from typing import List, Optional
from pathlib import Path
from .logger import get_logger

class FileUtils:
    """文件和目录处理工具类"""
    
    # 创建logger实例
    logger = get_logger("FileUtils")
    
    @staticmethod
    def get_current_path() -> str:
        """获取当前工作目录的绝对路径
        
        Returns:
            str: 当前目录的绝对路径
        """
        path = os.path.abspath(os.getcwd())
        FileUtils.logger.debug(f"获取当前工作目录: {path}")
        return path
    
    @staticmethod
    def get_script_path(file_path: str) -> str:
        """获取指定文件所在目录的绝对路径
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件所在目录的绝对路径
            
        Raises:
            FileNotFoundError: 当文件不存在时抛出
        """
        try:
            if not os.path.exists(file_path):
                FileUtils.logger.error(f"文件不存在: {file_path}")
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            # 获取文件所在目录的绝对路径
            path = os.path.dirname(os.path.abspath(file_path))
            FileUtils.logger.debug(f"获取文件所在目录: {path}")
            return path
                
        except Exception as e:
            FileUtils.logger.error(f"获取文件路径失败: {str(e)}")
            raise
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 文件存在返回True，否则返回False
        """
        exists = os.path.isfile(file_path)
        FileUtils.logger.debug(f"检查文件是否存在 {file_path}: {'存在' if exists else '不存在'}")
        return exists
    
    @staticmethod
    def dir_exists(dir_path: str) -> bool:
        """检查目录是否存在
        
        Args:
            dir_path: 目录路径
            
        Returns:
            bool: 目录存在返回True，否则返回False
        """
        exists = os.path.isdir(dir_path)
        FileUtils.logger.debug(f"检查目录是否存在 {dir_path}: {'存在' if exists else '不存在'}")
        return exists
    
    @staticmethod
    def create_dir(dir_path: str) -> bool:
        """创建目录（如果不存在）
        
        Args:
            dir_path: 要创建的目录路径
            
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        try:
            if not os.path.exists(dir_path):
                FileUtils.logger.info(f"创建目录: {dir_path}")
                os.makedirs(dir_path)
            else:
                FileUtils.logger.debug(f"目录已存在: {dir_path}")
            return True
        except Exception as e:
            FileUtils.logger.error(f"创建目录失败: {str(e)}")
            return False
    
    @staticmethod
    def copy_file(src_file: str, dst_file: str, overwrite: bool = False) -> bool:
        """复制文件
        
        Args:
            src_file: 源文件路径
            dst_file: 目标文件路径
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            bool: 复制成功返回True，失败返回False
        """
        try:
            if not os.path.exists(src_file):
                FileUtils.logger.error(f"源文件不存在: {src_file}")
                return False
                
            if os.path.exists(dst_file) and not overwrite:
                FileUtils.logger.warning(f"目标文件已存在且不允许覆盖: {dst_file}")
                return False
                
            # 确保目标目录存在
            dst_dir = os.path.dirname(dst_file)
            if not os.path.exists(dst_dir):
                FileUtils.logger.debug(f"创建目标目录: {dst_dir}")
                os.makedirs(dst_dir)
                
            FileUtils.logger.info(f"复制文件: {src_file} -> {dst_file}")
            shutil.copy2(src_file, dst_file)
            return True
        except Exception as e:
            FileUtils.logger.error(f"复制文件失败: {str(e)}")
            return False
    
    @staticmethod
    def copy_dir(src_dir: str, dst_dir: str, overwrite: bool = False) -> bool:
        """复制目录内容
        
        Args:
            src_dir: 源目录路径
            dst_dir: 目标目录路径
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            bool: 复制成功返回True，失败返回False
        """
        try:
            if not os.path.exists(src_dir):
                FileUtils.logger.error(f"源目录不存在: {src_dir}")
                return False
                
            if os.path.exists(dst_dir) and not overwrite:
                FileUtils.logger.warning(f"目标目录已存在且不允许覆盖: {dst_dir}")
                return False
                
            FileUtils.logger.info(f"复制目录: {src_dir} -> {dst_dir}")
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=overwrite)
            return True
        except Exception as e:
            FileUtils.logger.error(f"复制目录失败: {str(e)}")
            return False
    
    @staticmethod
    def list_files(dir_path: str, pattern: str = "*") -> List[str]:
        """列出目录中的文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件匹配模式（例如：*.txt）
            
        Returns:
            List[str]: 文件路径列表
        """
        try:
            files = [str(f) for f in Path(dir_path).glob(pattern) if f.is_file()]
            FileUtils.logger.debug(f"列出目录 {dir_path} 中的文件 (pattern={pattern}): 找到 {len(files)} 个文件")
            return files
        except Exception as e:
            FileUtils.logger.error(f"列出文件失败: {str(e)}")
            return []
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[int]: 文件大小（字节），失败返回None
        """
        try:
            size = os.path.getsize(file_path)
            FileUtils.logger.debug(f"获取文件大小 {file_path}: {size} 字节")
            return size
        except Exception as e:
            FileUtils.logger.error(f"获取文件大小失败: {str(e)}")
            return None
    
    @staticmethod
    def join_paths(*paths: str) -> str:
        """连接路径
        
        Args:
            *paths: 路径片段
            
        Returns:
            str: 连接后的路径
        """
        return os.path.join(*paths)
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """规范化路径（处理路径分隔符和相对路径）
        
        Args:
            path: 输入路径
            
        Returns:
            str: 规范化后的路径
        """
        return os.path.normpath(path) 