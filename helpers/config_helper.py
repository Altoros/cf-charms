import jinja2
#from charmhelpers.core.hookenv import log, WARNING, charm_dir

TEMPLATES_DIR = 'templates'

#def find_config_parameter(key, relation_environment, config_data):
    #value = relation_environment.relation_get(key)
    #if value is None and key in config_data:
        #value = config_data[key]
    #log('Try to find parameter: %s = %s' % (key, value))
    #return value


def render_template(template_name, context, template_dir=TEMPLATES_DIR):
    templates = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir))
    template = templates.get_template(template_name)
    return template.render(context)


def emit_config(config_items, context,
                template_config_file, target_config_file,
                template_dir=TEMPLATES_DIR):
    success = not bool(set(config_items).difference(set(context.keys())))

    if success:
        config_text = render_template(template_config_file, context,
                                      template_dir=template_dir)
        with open(target_config_file, 'w') as config_file:
            config_file.write(config_text)
    return success
