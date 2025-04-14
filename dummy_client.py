

class DummyExpeditionDLL:
    """
    Dummy class to simulate the Expedition DLL interface for testing purposes.
    """

    def __init__(self, expedition_location):
        pass

    def get_exp_var_value(self, var):
        """
        Simulate getting a variable from the Expedition DLL.
        """
        return 0.0

    def set_exp_var_value(self, var, value):
        """
        Simulate setting a variable in the Expedition DLL.
        """
        pass

    def get_exp_vars(self, vars):
        """
        Simulate getting multiple variables from the Expedition DLL.
        """
        return [0.0] * len(vars)

    def set_exp_user_var_name(self, var, name):
        """
        Simulate setting a user variable name in the Expedition DLL.
        """
        pass
