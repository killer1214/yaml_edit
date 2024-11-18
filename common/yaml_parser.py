import yaml
from typing import Dict, Any, Optional

class YamlParser:
    """YAML文件解析器"""
    
    @staticmethod
    def parse_yaml(file_path: str) -> Optional[Dict[str, Any]]:
        """解析YAML文件并返回数据
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            Dict[str, Any]: 解析后的YAML数据字典
            None: 如果解析失败
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
            yaml.YAMLError: YAML格式错误时抛出
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data
        except FileNotFoundError:
            print(f"错误: 找不到文件 {file_path}")
            raise
        except yaml.YAMLError as e:
            print(f"错误: YAML格式错误 - {str(e)}")
            raise
        except Exception as e:
            print(f"错误: 解析YAML文件时出错 - {str(e)}")
            return None 