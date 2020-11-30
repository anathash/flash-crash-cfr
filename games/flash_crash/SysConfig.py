class SysConfig:
    MIN_ORDER_VALUE = "MIN_ORDER_VALUE"
    DENSITY = "DENSITY"

    __conf = {"MIN_ORDER_VALUE": 1000,
              "MINUTE_VOLUME_LIMIT": 0.09,
              "DENSITY": 0.5,
              "STEP_ORDER_SIZE": 0.0075,
              "MAX_NUM_ORDERS": 2,
              "TIME_STEP_MINUTES": 5,
             # "DAILY_PORTION_PER_MIN": 0.002, # finish a 1.5% order in 15 minutes
              "DAILY_PORTION_PER_MIN": 0.001, # finish a 1.5% order in 15 minutes
    }

    #             "ORDER_SIZES": [0.75, 1.75],
    @staticmethod
    def get(name):
        return SysConfig.__conf[name]

    @staticmethod
    def set(name, value):
        if name in SysConfig.__conf.keys():
            SysConfig.__conf[name] = value
        else:
            raise NameError("Name not accepted in set() method")

"""

    MIN_ORDER_VALUE = "MIN_ORDER_VALUE"
    DENSITY = "DENSITY"
    INITIAL_NUM_SHARES = "INITIAL_NUM_SHARES"
    INITIAL_ASSET_PRICE = "INITIAL_ASSET_PRICE"
    INITIAL_FUND_CAPITAL = "INITIAL_FUND_CAPITAL"
    INITIAL_LEVERAGE = "INITIAL_LEVERAGE"
    TOLERANCE = "TOLERANCE"
    ATTACKER_PORTFOLIO_RATIO = "ATTACKER_PORTFOLIO_RATIO"
    NUM_FUNDS = "NUM_FUNDS"
    NUM_ASSETS = "NUM_ASSETS"
    MAX_ASSETS_IN_ACTION = "MAX_ASSETS_IN_ACTION"
    ASSET_SLICING = "ASSET_SLICING"

    __conf = {"MIN_ORDER_VALUE": 1000,
              "DENSITY": 0.5,
              "INITIAL_NUM_SHARES": 500,
              "INITIAL_ASSET_PRICE": 1000,
              "INITIAL_FUND_CAPITAL": 500000,
              "INITIAL_LEVERAGE": 2,
              "TOLERANCE": 1.01,
              "ATTACKER_PORTFOLIO_RATIO": 0.2,
              "MAX_ASSETS_IN_ACTION": 3,
              "ASSET_SLICING": 10,
              "NUM_FUNDS": 10,
              "NUM_ASSETS": 10
              }
"""