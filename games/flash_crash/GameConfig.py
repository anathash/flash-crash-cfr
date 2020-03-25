class GameConfig:
    def __init__(self, num_assets=10,
                 num_funds=10,
                 min_order_value=1000,
                 density=0.5,
                 asset_daily_volume=200000,
                 asset_volatility=1.2,
                 initial_asset_price=1000,
                 initial_fund_capital=500000,
                 initial_leverage=2,
                 tolerance=1.01,
                 attacker_portfolio_ratio=0.05,
                 attacker_max_assets_in_action=1,
                 attacker_asset_slicing=20,
                 defender_max_assets_in_action=1,
                 defender_asset_slicing=20,
                 defender_initial_capital=6000000,
                 impact_calc_constant=1.0536,
                 intraday_asset_gain_max_range=1.1,
                 attacker_max_sell_minute_volume_ratio = 2.0,
                 verbose=False):

        self.num_assets = num_assets
        self.num_funds = num_funds
        self.min_order_value = min_order_value
        self.density = density
        self.asset_daily_volume = asset_daily_volume
        self.asset_volatility = asset_volatility
        self.initial_asset_price = initial_asset_price
        self.initial_fund_capital = initial_fund_capital
        self.initial_leverage = initial_leverage
        self.tolerance = tolerance
        self.attacker_portfolio_ratio = attacker_portfolio_ratio
        self.attacker_max_assets_in_action = attacker_max_assets_in_action
        self.attacker_asset_slicing = attacker_asset_slicing
        self.defender_max_assets_in_action = defender_max_assets_in_action
        self.defender_asset_slicing = defender_asset_slicing
        self.defender_initial_capital = defender_initial_capital
        self.impact_calc_constant = impact_calc_constant
        self.intraday_asset_gain_max_range = intraday_asset_gain_max_range
        self.verbose = verbose
        self.attacker_max_sell_minute_volume_ratio = attacker_max_sell_minute_volume_ratio


