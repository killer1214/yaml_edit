import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

sys.path.append(str(Path(__file__).parent.parent))
from common.file_utils import FileUtils
from common.logger import get_logger
from common.graph_node import GraphWindow

class YamlParser:
    """YAML文件解析器"""
    
    def __init__(self):
        self.logger = get_logger("YamlParser")
    
    @staticmethod
    def parse_yaml(file_path: str) -> Optional[Dict[str, Any]]:
        """解析YAML文件并返回数据"""
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

    def get_dependencies(self, data: Dict[str, Any]) -> List[Tuple[str, str]]:
        """解析并返回任务之间的依赖关系
        
        Args:
            data: 解析后的YAML数据字典
            
        Returns:
            List[Tuple[str, str]]: 依赖关系列表，每个元素为(依赖任务, 当前任务)的元组
        """
        dependencies = []
        try:
            jobs = data.get('jobs', [])
            if not isinstance(jobs, list):
                self.logger.error("jobs必须是列表格式")
                return dependencies
            
            # 遍历所有任务
            for job in jobs:
                if not isinstance(job, dict):
                    continue
                
                current_job = job.get('name', '')
                depends = job.get('depend', [])
                
                # 确保depends是列表
                if isinstance(depends, str):
                    depends = [depends]
                elif not isinstance(depends, list):
                    depends = []
                
                # 添加依赖关系
                for dep in depends:
                    if dep and current_job:
                        dependencies.append((dep, current_job))
                        self.logger.debug(f"找到依赖关系: {dep} -> {current_job}")
            
            self.logger.info(f"共解析出 {len(dependencies)} 个依赖关系")
            return dependencies
            
        except Exception as e:
            self.logger.error(f"解析依赖关系时出错: {str(e)}")
            return dependencies

    def get_dependency_chains(self, data: Dict[str, Any]) -> List[List[str]]:
        """获取完整的依赖链路
        
        Args:
            data: 解析后的YAML数据字典
            
        Returns:
            List[List[str]]: 完整的依赖链路列表，每个元素为一个任务序列
        """
        try:
            # 获取所有依赖关系对
            dependencies = self.get_dependencies(data)
            
            # 构建邻接表
            adj_dict = {}
            for dep_from, dep_to in dependencies:
                if dep_from not in adj_dict:
                    adj_dict[dep_from] = set()
                adj_dict[dep_from].add(dep_to)
                if dep_to not in adj_dict:
                    adj_dict[dep_to] = set()
            
            # 找出所有起始节点（入度为0的节点）
            all_nodes = set(adj_dict.keys())
            end_nodes = set()
            for deps in adj_dict.values():
                end_nodes.update(deps)
            start_nodes = all_nodes - end_nodes
            
            # DFS遍历构建完整链路
            def dfs(node: str, current_path: List[str], chains: List[List[str]]):
                if node not in adj_dict or not adj_dict[node]:
                    chains.append(current_path[:])
                    return
                
                for next_node in adj_dict[node]:
                    dfs(next_node, current_path + [next_node], chains)
            
            # 从每个起始节点开始遍历
            all_chains = []
            for start_node in start_nodes:
                chains = []
                dfs(start_node, [start_node], chains)
                all_chains.extend(chains)
            
            return all_chains
                
        except Exception as e:
            self.logger.error(f"构建依赖链路时出错: {str(e)}")
            return []

    def print_dependencies(self, data: Dict[str, Any]):
        """打印任务依赖关系
        
        Args:
            data: 解析后的YAML数据字典
        """
        try:
            # 获取完整的依赖链路
            chains = self.get_dependency_chains(data)
            
            if not chains:
                self.logger.info("未找到任何依赖链路")
                return
            
            self.logger.info("完整的依赖链路:")
            for chain in chains:
                self.logger.info(" -> ".join(chain))
            
            # 打印独立任务（没有依赖的任务）
            jobs = data.get('jobs', [])
            independent_jobs = []
            for job in jobs:
                if isinstance(job, dict):
                    job_name = job.get('name', '')
                    if not job.get('depend'):
                        independent_jobs.append(job_name)
            
            if independent_jobs:
                self.logger.info("\n独立任务（无依赖）:")
                for job in independent_jobs:
                    self.logger.info(f"- {job}")
                    
        except Exception as e:
            self.logger.error(f"打印依赖关系时出错: {str(e)}")


if __name__ == "__main__":
    # 使用原来的测试代码替换当前的图形界面测试代码
    parser = YamlParser()
    yaml_file = Path(FileUtils.get_current_path(), "example.yaml")
    
    try:
        data = parser.parse_yaml(str(yaml_file))
        if data:
            # 获取并打印依赖链路
            parser.print_dependencies(data)
                    
    except Exception as e:
        parser.logger.error(f"处理YAML文件时出错: {str(e)}")
