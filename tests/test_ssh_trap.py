from model.ssh_trap import SshTrap

trap = SshTrap()
print(trap.get_protocol())           
print(trap.get_type())               
trap.simulate_interaction("ls -la", "192.168.1.100")
