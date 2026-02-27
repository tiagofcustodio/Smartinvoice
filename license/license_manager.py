import platform
import uuid
import hashlib
import os

def get_machine_id():
    """Gera um ID único baseado no hardware da máquina (MAC address + info do sistema)."""
    mac_num = hex(uuid.getnode())
    mac_str = '-'.join(mac_num[i:i+2] for i in range(2, 14, 2))
    
    sys_info = f"{platform.node()}_{platform.machine()}_{platform.processor()}_{mac_str}"
    
    # Faz um hash para esconder as infos reais e criar um ID fixo e curto (ex: 12 chars)
    machine_hash = hashlib.sha256(sys_info.encode()).hexdigest()
    return machine_hash[:16].upper()

if __name__ == "__main__":
    print("O seu Machine ID é:", get_machine_id())
