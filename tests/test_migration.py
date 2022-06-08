# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")

import pytest

from brownie import Wei, accounts, Contract, config
from brownie import StrategyAngleUSDC


@pytest.mark.require_network("mainnet-fork")
def test_migration(
    chain,
    vault,
    strategy,
    token,
    gov,
    strategist,
    alice,
    alice_amount,
    bob,
    bob_amount,
    tinytim,
    tinytim_amount,
    angle_token,
    angle_stable_master,
    san_token,
    san_token_gauge,
    pool_manager,
    newstrategy,
    utils,
    strategy_proxy,
    angle_voter
):
    token.approve(vault, 1_000_000_000_000, {"from": alice})
    token.approve(vault, 1_000_000_000_000, {"from": bob})
    token.approve(vault, 1_000_000_000_000, {"from": tinytim})

    # users deposit to vault
    vault.deposit(alice_amount, {"from": alice})
    vault.deposit(bob_amount, {"from": bob})
    vault.deposit(tinytim_amount, {"from": tinytim})

    utils.set_0_vault_fees()

    chain.sleep(1)
    strategy.harvest({"from": strategist})

    assert san_token_gauge.balanceOf(angle_voter) > 0
    assets_at_t = strategy.estimatedTotalAssets()

    utils.mock_angle_slp_profits()

    assets_at_t_plus_one = strategy.estimatedTotalAssets()
    assert assets_at_t_plus_one > assets_at_t

    assert san_token_gauge.balanceOf(strategy) == 0
    assert san_token_gauge.balanceOf(newstrategy) == 0
    assert san_token_gauge.balanceOf(angle_voter) > 0

    newstrategy.setStrategist(strategist)

    san_token_balance = strategy.balanceOfStake()
    assets = strategy.estimatedTotalAssets()
    assert san_token_balance > 0
    assert san_token.balanceOf(strategy) == 0
    assert san_token.balanceOf(newstrategy) == 0
    vault.migrateStrategy(strategy, newstrategy, {"from": gov})
    assert san_token.balanceOf(strategy) == 0
    assert san_token.balanceOf(newstrategy) == 0
    assert san_token.balanceOf(strategy_proxy) == 0
    assert strategy.balanceOfStake() == 0
    assert newstrategy.balanceOfStake() == 0
    strategy_proxy.approveStrategy(san_token_gauge, newstrategy.address, {"from": gov})
    strategy_proxy.approveStrategy(angle_stable_master, newstrategy.address, {"from": gov})
    assert pytest.approx(newstrategy.estimatedTotalAssets(),rel=1e-3) == assets

    newstrategy.harvest({"from": strategist})
    assert san_token.balanceOf(newstrategy) == 0
    assert san_token_gauge.balanceOf(newstrategy) == 0
    assert san_token_gauge.balanceOf(angle_voter) > 0
    assert token.balanceOf(newstrategy) == 0
