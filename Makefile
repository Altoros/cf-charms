CHARMS = cf-cloud-controller cf-uaa cf-dea cf-nats cf-go-router
CHARM_DIR = charms/trusty/

test: 
	@- for d in $(CHARMS); do (cd $(CHARM_DIR)/$$d; $(MAKE) test); done
