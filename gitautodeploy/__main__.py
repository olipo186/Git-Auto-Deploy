#!/usr/bin/env python

if __name__ == '__main__':

    if __package__ != 'gitautodeploy':
        import sys
        print("Critical - GAD must be started as a python module, for example using python -m gitautodeploy")
        sys.exit()

    from gitautodeploy import main
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    main()

else:
    from gitautodeploy import main