"""兼容旧文件名；实现已迁移到无硬编码的完整 cross_dag pipeline demo。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.demo_corpus_dataset_tar_pipeline import main


if __name__ == "__main__":
    main()
