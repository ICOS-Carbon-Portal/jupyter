JUPYTER=../jupyter
DEVOPS=../../infrastructure/devops
ANSIBLE=ansible-playbook $(DEVOPS)/exploredata.yml -i$(DEVOPS)/production.inventory -lexploredata

.PHONY: pushtest pushprod

pushtest:
	$(ANSIBLE) -eexploredata_src=$(PWD)/.. -tpushtest

pushprod:
	$(ANSIBLE) -eexploredata_src=$(PWD)/.. -tpushprod
