#!/usr/bin/env python
from gitautodeploy import main

if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    main()
