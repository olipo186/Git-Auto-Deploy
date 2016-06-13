#!/usr/bin/env python

if __name__ == '__main__':
    import sys
    import os
    import gitautodeploy
    sys.stderr.write("\033[1;33m[WARNING]\033[0;33m GitAutoDeploy.py is deprecated. Please use \033[1;33m'python gitautodeploy%s'\033[0;33m instead.\033[0m\n" % (' ' + ' '.join(sys.argv[1:])).rstrip())
    gitautodeploy.main()
