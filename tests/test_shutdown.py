import pytest


@pytest.mark.require_network("mainnet-fork")
def test_shutdown(
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
    san_token_gauge,
    san_token,
    utils,
    angle_stable_master,
    BASE_PARAMS,
    angle_fee_manager,
):
    token.approve(vault, 1_000_000_000_000, {"from": alice})
    token.approve(vault, 1_000_000_000_000, {"from": bob})
    token.approve(vault, 1_000_000_000_000, {"from": tinytim})

    vault.deposit(alice_amount, {"from": alice})
    vault.deposit(bob_amount, {"from": bob})
    vault.deposit(tinytim_amount, {"from": tinytim})

    utils.set_0_vault_fees()

    strategy.harvest({"from": strategist})

    assert san_token_gauge.balanceOf(strategy) > 0
    assets_at_t = strategy.estimatedTotalAssets()

    utils.mock_angle_slp_profits()
    strategy.harvest({"from": strategist})

    assets_at_t_plus_one = strategy.estimatedTotalAssets()
    assert assets_at_t_plus_one > assets_at_t

    strategy.setEmergencyExit({"from": gov})
    strategy.harvest({"from": strategist})
    chain.mine(1)

    vault.withdraw({"from": alice})
    assert token.balanceOf(alice) > alice_amount
    assert token.balanceOf(bob) == 0

    vault.withdraw({"from": bob})
    assert token.balanceOf(bob) > bob_amount

    vault.withdraw({"from": tinytim})
    assert token.balanceOf(tinytim) > tinytim_amount

    utils.assert_strategy_contains_no_tokens()
