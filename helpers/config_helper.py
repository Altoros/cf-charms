import os
from utils import render_template
# from charmhelpers.core.hookenv import log, DEBUG, ERROR, WARNING
from charmhelpers.core.hookenv import log, WARNING, charm_dir


def find_config_parameter(key, relation_environment, config_data):
    value = relation_environment.relation_get(key)
    if value is None and key in config_data:
        value = config_data[key]
    log('Try to find parameter: %s = %s' % (key, value))
    return value


def emit_config(module_name, config_items, local_state,
                template_config_file, target_config_file):
    log('Try to emit %s config' % module_name)

    config_context = {}
    success = True

    for key in config_items:
        log('extract %s from local_state. '
            '%s = %s' % (key, key, local_state[key]))
        if local_state[key] is not None:
            config_context[key] = local_state[key]
        else:
            success = False

    local_state[module_name + '_ok'] = success
    local_state.save

    if success:
        log('Emited %s config successfully.' % module_name)
        template_dir = os.path.join(charm_dir(), 'templates')
        config_text = render_template(template_config_file,
                                      config_context, template_dir)
        log("%s config text: " % module_name)
        log(config_text)
        with open(target_config_file, 'w') as config_file:
            config_file.write(config_text)
    else:
        log('Emit %s config unsuccessfull' % module_name, WARNING)

    return success
