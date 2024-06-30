import os

def get_default_values():
    config = read_config()
    return (
        config.get('default_sohlenkote', 100.0),
        config.get('default_durchmesser', 0.8),
        config.get('default_hoehe', 0.8),
        config.get('default_wanddicke', 0.04),
        config.get('default_bodendicke', 0.02),
        config.get('default_rohrdicke', 0.02),
        config.get('einfaerben', False)
    )

def read_config(config_file='config.txt'):
    config = {}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_file)
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            for line in file:
                name, value = line.strip().split('=')
                name = name.strip()
                value = value.strip()
                if name in ['default_sohlenkote', 'default_durchmesser', 'default_hoehe', 'default_wanddicke', 'default_bodendicke', 'default_rohrdicke']:
                    config[name] = float(value)
                elif name == 'einfaerben':
                    config[name] = value.lower() == 'true'
    return config