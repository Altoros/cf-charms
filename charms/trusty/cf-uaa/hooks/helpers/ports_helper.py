#from charmhelpers.core.hookenv import log, WARNING

#def port_config_changed(port, hookenv):
#    '''Cheks if value of port changed close old port and open a new one'''
#    if port in local_state:
#        if local_state[port] != config_data[port]:
#            log('Stored value for {} isn\'t equal'
#                     'to config data'.format(port),
#                DEBUG)
#            log('Closing port {}'.format(str(local_state[port])), WARNING)
#            try:
#                hookenv.close_port(local_state[port])
#            except:
#                log('{} port is not closed.'.format(str(local_state[port])),
#                     WARNING)
#
#    hookenv.open_port(config_data[port])
#    local_state[port] = config_data[port]
#    local_state.save()
