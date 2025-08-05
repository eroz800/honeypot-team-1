from model.ssh_trap import SshTrap

trap = SshTrap()
print(trap.get_protocol())           # אמור להחזיר "SSH"
print(trap.get_type())               # אמור להחזיר "Fake SSH Login"
trap.simulate_interaction("ls -la", "192.168.1.100")
