from flash_crash import GameConfig
from flash_crash.AssetFundNetwork import AssetFundsNetwork
from flash_crash.MarketImpactCalculator import SqrtMarketImpactCalculator


def generate_rand_network(game_config: GameConfig):
    assets_num_shares = [game_config.asset_daily_volume] * game_config.num_assets
    initial_prices = [game_config.initial_asset_price] * game_config.num_assets
    volatility = [game_config.asset_volatility] * game_config.num_assets

    initial_capitals = [game_config.initial_fund_capital] * game_config.num_funds
    initial_leverages = [game_config.initial_leverage] * game_config.num_funds
    tolerances = [game_config.tolerance] * game_config.num_funds


    g = AssetFundsNetwork.generate_random_network(game_config.density,
                                                game_config.num_funds,
                                                game_config.num_assets,
                                                initial_capitals,
                                                initial_leverages, initial_prices,
                                                tolerances, assets_num_shares,
                                                volatility,
                                                SqrtMarketImpactCalculator())
    return g


def generate_and_save_rand_network(file_name, game_config: GameConfig):
    g = generate_rand_network(game_config)
    g.save_to_file(file_name)



if __name__ == "__main__":
    config = GameConfig()
    config.num_assets = 10
    config.num_funds = 10
    generate_and_save_rand_network('../../resources/ten_by_ten.json', config)
