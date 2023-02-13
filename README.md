# Cluster test

## Prerequisite

+ Create 4 machines with ubuntu 18.04, and install two gpdb clusters(each 2 hosts) for thoes hosts.
+ Can ssh to your cluster
+ The user which used for gpdb and test can use `sudo` without password, default username is `gpadmin`
+ Install `ansible` in your local host

## Fill `config.yaml`

`config.yaml` has some fields need you to fill.

## Fill `hosts.yaml`

Fill your clusters ips in this file, hosts of all are 4 hosts ips of whole clusters, `cluster_cg` is the cluster hosts which will have cgroup io limitation, `cluster_master` is the host of master of two clusters.

## Run

Firstly, run prepare phase:
```shell
cd ansible
ansible-playbook -i hosts.yaml prepare.yaml
```
Above command will create some folders and copy some python scripts to cluster hosts.

Then, run executing phase:
```shell
cd ansible
ansible-playbook -i hosts.yaml run.yaml
```
Above command will run the testing, but it maybe not stop after the `running_time`, you can use `Ctrl + C` to terminate the run phase and then run `ansible-playbook -i hosts.yaml stop.yaml` to stop the testing.

And in default, collected datas are located at `/home/gpadmin/test-data` of cluster hosts. You can analysis those data by your way now, `datas/src/analysis.ipynb` is a sample notebook to analysis those data.

## clean collected datas and testdb
run `ansible-playbook -i hosts.yaml clean.yaml`
