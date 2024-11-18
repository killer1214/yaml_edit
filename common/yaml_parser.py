import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

sys.path.append(str(Path(__file__).parent.parent))
from common.file_utils import FileUtils
from common.logger import get_logger

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

    def print_dependencies(self, data: Dict[str, Any]):
        """打印任务依赖关系
        
        Args:
            data: 解析后的YAML数据字典
        """
        try:
            dependencies = self.get_dependencies(data)
            
            if not dependencies:
                self.logger.info("未找到任何依赖关系")
                return
            
            self.logger.info("任务依赖关系:")
            for dep, job in dependencies:
                self.logger.info(f"{dep} -> {job}")
            
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

    def analyze_dependencies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析任务依赖关系，返回详细信息
        
        Args:
            data: 解析后的YAML数据字典
            
        Returns:
            Dict[str, Any]: 包含依赖分析结果的字典
        """
        try:
            dependencies = self.get_dependencies(data)
            jobs = data.get('jobs', [])
            
            # 初始化结果字典
            analysis = {
                'total_jobs': len(jobs),
                'total_dependencies': len(dependencies),
                'independent_jobs': [],
                'dependency_chains': [],
                'leaf_jobs': [],  # 没有被其他任务依赖的任务
                'root_jobs': []   # 没有依赖其他任务的任务
            }
            
            # 获取所有任务名称
            all_jobs = set()
            dependent_jobs = set()  # 被依赖的任务
            depending_jobs = set()  # 依赖其他任务的任务
            
            for job in jobs:
                if isinstance(job, dict):
                    job_name = job.get('name', '')
                    if job_name:
                        all_jobs.add(job_name)
                        
                    depends = job.get('depend', [])
                    if isinstance(depends, str):
                        depends = [depends]
                    if depends:
                        depending_jobs.add(job_name)
                        for dep in depends:
                            dependent_jobs.add(dep)
            
            # 找出独立任务
            analysis['independent_jobs'] = list(all_jobs - dependent_jobs - depending_jobs)
            
            # 找出叶子任务（没有被依赖的任务）
            analysis['leaf_jobs'] = list(all_jobs - dependent_jobs)
            
            # 找出根任务（没有依赖的任务）
            analysis['root_jobs'] = list(all_jobs - depending_jobs)
            
            # 记录分析结果
            self.logger.info(f"分析结果:")
            self.logger.info(f"总任务数: {analysis['total_jobs']}")
            self.logger.info(f"总依赖关系: {analysis['total_dependencies']}")
            self.logger.info(f"独立任务数: {len(analysis['independent_jobs'])}")
            self.logger.info(f"叶子任务数: {len(analysis['leaf_jobs'])}")
            self.logger.info(f"根任务数: {len(analysis['root_jobs'])}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析依赖关系时出错: {str(e)}")
            return {}


if __name__ == "__main__":
    # 测试代码
    parser = YamlParser()
    yaml_file = Path(FileUtils.get_current_path(), "example.yaml")
    
    try:
        # 解析YAML文件
        data = parser.parse_yaml(str(yaml_file))
        if data:
            # 获取依赖关系
            dependencies = parser.get_dependencies(data)
            
            # 输出依赖链表
            parser.logger.info("依赖关系链表:")
            for dep_from, dep_to in dependencies:
                parser.logger.info(f"{dep_from} -> {dep_to}")
                    
    except Exception as e:
        parser.logger.error(f"处理YAML文件时出错: {str(e)}")
