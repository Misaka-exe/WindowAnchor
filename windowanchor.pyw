"""无控制台启动入口。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from windowanchor.app import main

if __name__ == "__main__":
    sys.exit(main())
