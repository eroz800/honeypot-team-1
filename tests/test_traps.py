from model.ssh_trap import SshTrap

def test_simulate_interaction_basic():
    trap = SshTrap()
    result = trap.simulate_interaction("whoami", "192.168.1.5")
    assert "whoami" in result
    assert "192.168.1.5" in result
