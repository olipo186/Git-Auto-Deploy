class GitWrapper(object):

    @staticmethod
    def pull(*args, **kwargs):
        """Fake git pull"""
        return 0

    @staticmethod
    def clone(*args, **kwargs):
        """Fake git clone"""
        return 0

    @staticmethod
    def deploy(*args, **kwargs):
        """Fake deploy"""
        return 0
