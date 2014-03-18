
def port_config_changed(port):
    '''Cheks if value of port changed close old port and open a new one'''
    if port in local_state:
        if local_state[port] != config_data[port]:
            hookenv.close_port(local_state[port])
            local_state[port] = config_data[port]
    else:
        local_state[port] = config_data[port]
    local_state.save()
    hookenv.open_port(config_data[port])
