from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client


auth = v3.Password(auth_url="http://192.168.122.218:5000/v3", username="admin",
                   password="secret", project_name="admin",
                   user_domain_id="default", project_domain_id="default")

sess = session.Session(auth=auth)
keystone = client.Client(session=sess)

#from neutronclient.v2_0 import client
#from cinderclient.v3 import client
#keystone.endpoints.list()[0]
#print(keystone.projects.list())

#neutron = client.Client(session=sess)
#print(neutron.list_routers(retrieve_all=True))

#cinder = client.Client(session=sess)
#print(cinder.volumes.list())

from os_client_config import config as cloud_config
from openstackclient.common import clientmanager
from argparse import Namespace

opts=Namespace(access_token_endpoint='', auth_type='', auth_url='http://192.168.122.218:5000/v3', cacert='', client_id='', client_secret='', cloud='', debug=False, domain_id='', domain_name='', endpoint='', identity_provider='', insecure=False, os_compute_api_version='2', os_default_domain='default', os_identity_api_version='3', os_image_api_version='2', os_network_api_version='2', os_object_api_version='', os_project_id=None, os_project_name=None, os_volume_api_version='2', password='secret', project_domain_id='default', project_domain_name='', project_id='', project_name='admin', protocol='', region_name='', rest=[], scope='', timing=False, token='', trust_id='', url='', user_domain_id='default', user_domain_name='', user_id='', username='admin', verbose_level=1, verify=False)

cc = cloud_config.OpenStackConfig()

cloud = cc.get_one_cloud(cloud=opts.cloud,argparse=opts,)

api_version={}
for mod in clientmanager.PLUGIN_MODULES:
  version_opt = getattr(opts, mod.API_VERSION_OPTION, None)
  if version_opt:
    api = mod.API_NAME
    api_version[api] = version_opt

client_manager = clientmanager.ClientManager(cli_options=cloud,api_version=api_version,)
client_manager.setup_auth()
client_manager.auth_ref


'''
client_manager.identity.users.get(self, user)
client_manager.identity.users.list(self, project=None, domain=None, group=None, default_project=None, **kwargs)
client_manager.identity.users.create(self, name, domain=None, project=None, password=None, email=None, description=None, enabled=True, default_project=None, **kwargs)
client_manager.identity.users.update(self, user, name=None, domain=None, project=None, password=None, email=None, description=None, enabled=None, default_project=None, **kwargs)
client_manager.identity.users.delete(self, user)

client_manager.identity.projects.get(self, project, subtree_as_list=False, parents_as_list=False, subtree_as_ids=False, parents_as_ids=False)
client_manager.identity.projects.list(self, domain=None, user=None, **kwargs)
client_manager.identity.projects.create(self, name, domain, description=None, enabled=True, parent=None, **kwargs)
client_manager.identity.projects.update(self, project, name=None, domain=None, description=None, enabled=None, **kwargs)
client_manager.identity.projects.delete(self, project)
'''


'''
client_manager.volume.volumes.get(self, volume_id)
client_manager.volume.volumes.list(self, detailed=True, search_opts=None,
                                   marker=None, limit=None, sort_key=None,
                                   sort_dir=None, sort=None)
client_manager.volume.volumes.create(self, size, consistencygroup_id=None,
               group_id=None, snapshot_id=None,
               source_volid=None, name=None, description=None,
               volume_type=None, user_id=None,
               project_id=None, availability_zone=None,
               metadata=None, imageRef=None, scheduler_hints=None,
               source_replica=None, multiattach=False):
client_manager.volume.volumes.update(self, volume, **kwargs)
client_manager.volume.volumes.delete(self, volume, cascade=False)
client_manager.volume.volumes.attach(self, volume, instance_uuid, mountpoint, mode='rw',
               host_name=None)
client_manager.volume.volumes.detach(self, volume, attachment_uuid=None)
'''


'''
client_manager.image.images.get(self, image_id)
client_manager.image.images.list(self, **kwargs)
client_manager.image.images.create(self, **kwargs)
client_manager.image.images.update(self, image_id, remove_props=None, **kwargs)
client_manager.image.images.delete(self, image_id)
client_manager.image.images.upload(self, image_id, image_data, image_size=None)
client_manager.image.images.deactivate(self, image_id)
client_manager.image.images.reactivate(self, image_id)
'''


'''
client_manager.compute.flavors.get(self, flavor)
client_manager.compute.flavors.list(self, detailed=True, is_public=True, marker=None, limit=None,
             sort_key=None, sort_dir=None)
client_manager.compute.flavors.create(self, name, ram, vcpus, disk, flavorid="auto",
               ephemeral=0, swap=0, rxtx_factor=1.0, is_public=True)
client_manager.compute.flavors.delete(self, flavor)

client_manager.compute.server.get(self, server)
client_manager.compute.server.list(self, detailed=True, search_opts=None, marker=None, limit=None,
             sort_keys=None, sort_dirs=None)
client_manager.compute.server.start(self, server)
client_manager.compute.server.pause(self, server)
client_manager.compute.server.unpause(self, server)
client_manager.compute.server.lock(self, server)
client_manager.compute.server.unlock(self, server)
client_manager.compute.server.suspend(self, server)
client_manager.compute.server.resume(self, server)
client_manager.compute.server.rescue(self, server, password=None, image=None)
client_manager.compute.server.unrescue(self, server)
client_manager.compute.server.ips(self, server)
client_manager.compute.server.create(self, name, image, flavor, meta=None, files=None,
               reservation_id=None, min_count=None,
               max_count=None, security_groups=None, userdata=None,
               key_name=None, availability_zone=None,
               block_device_mapping=None, block_device_mapping_v2=None,
               nics=None, scheduler_hints=None,
               config_drive=None, disk_config=None, admin_pass=None,
               access_ip_v4=None, access_ip_v6=None, **kwargs)
client_manager.compute.server.update(self, server, name=None, description=None)
client_manager.compute.server.delete(self, server)
client_manager.compute.server.reboot(self, server, reboot_type=REBOOT_SOFT)
client_manager.compute.server.rebuild(self, server, image, password=None, disk_config=None,
                preserve_ephemeral=False, name=None, meta=None, files=None,
                **kwargs)
client_manager.compute.server.resize(self, server, flavor, disk_config=None, **kwargs)
client_manager.compute.server.confirm_resize(self, server)
client_manager.compute.server.revert_resize(self, server)
client_manager.compute.server.migrate(self, server)
client_manager.compute.server.add_fixed_ip(self, server, network_id)
client_manager.compute.server.remove_fixed_ip(self, server, address)
client_manager.compute.server.add_floating_ip(self, server, address, fixed_address=None)
client_manager.compute.server.remove_floating_ip(self, server, address)
client_manager.compute.server.reset_network(self, server)
client_manager.compute.server.reset_state(self, server, state='error')
client_manager.compute.server.live_migrate(self, server, host, block_migration, force=None)
client_manager.compute.server.backup(self, server, backup_name, backup_type, rotation)
'''


'''
client_manager.network.get_network(self, network)
client_manager.network.networks(self, **query)
client_manager.network.find_network(self, name_or_id, ignore_missing=True)
client_manager.network.create_network(self, **attrs)
client_manager.network.update_network(self, network, **attrs)
client_manager.network.delete_network(self, network, ignore_missing=True)

client_manager.network.get_router(self, router)
client_manager.network.find_router(self, name_or_id, ignore_missing=True)
client_manager.network.routers(self, **query)
client_manager.network.create_router(self, **attrs)
client_manager.network.update_router(self, router, **attrs)
client_manager.network.delete_router(self, router, ignore_missing=True)
client_manager.network.add_interface_to_router(self, router, subnet_id=None, port_id=None)
client_manager.network.remove_interface_from_router(self, router, subnet_id=None,
                                     port_id=None)
client_manager.network.add_gateway_to_router(self, router, **body)
client_manager.network.remove_gateway_from_router(self, router, **body)

client_manager.network.get_security_group(self, security_group)
client_manager.network.security_groups(self, **query)
client_manager.network.find_security_group(self, name_or_id, ignore_missing=True)
client_manager.network.create_security_group(self, **attrs)
client_manager.network.update_security_group(self, security_group, **attrs)
client_manager.network.delete_security_group(self, security_group, ignore_missing=True)
client_manager.network.security_group_open_port(self, sgid, port, protocol='tcp')
client_manager.network.security_group_allow_ping(self, sgid)

client_manager.network.get_port(self, port)
client_manager.network.ports(self, **query)
client_manager.network.find_port(self, name_or_id, ignore_missing=True)
client_manager.network.create_port(self, **attrs)
client_manager.network.update_port(self, port, **attrs)
client_manager.network.delete_port(self, port, ignore_missing=True)
client_manager.network.add_ip_to_port(self, port, ip)
client_manager.network.remove_ip_from_port(self, ip)
'''


# Old fashion



'''from cinderclient.v3.client import Client
Client.volumes.create(self, size, consistencygroup_id, group_id, snapshot_id, source_volid, name, description, volume_type, user_id, project_id, availability_zone, metadata, imageRef, scheduler_hints, source_replica, multiattach)
Client.volumes.update(self, volume)
Client.volumes.get(self, volume_id)
Client.volumes.list(self, detailed, search_opts, marker, limit, sort_key, sort_dir, sort)
Client.volumes.delete(self, volume, cascade)
Client.groups.create(self, group_type, volume_types, name, description, user_id, project_id, availability_zone)
Client.groups.update(self, group)
Client.groups.get(self, group_id)
Client.groups.list(self, detailed, search_opts)
Client.groups.delete(self, group, delete_volumes)
'''

'''from neutronclient.v2_0.client import Client'''

'''from novaclient.v2.client import Client'''

'''from glanceclient.v2.client import Client
Client.images.create(self)
Client.images.update(self, image_id, remove_props)
Client.images.get(self, image_id)
Client.images.list(self)
Client.images.delete(self, image_id)
'''

'''from keystoneclient.v3.client import Client
Client.projects.create(self, name, domain, description, enabled, parent)
Client.projects.update(self, project, name, domain, description, enabled)
Client.projects.get(self, project, subtree_as_list, parents_as_list, subtree_as_ids, parents_as_ids)
Client.projects.list(self, domain, user)
Client.projects.delete(self, project)
Client.endpoints.create(self, service, url, interface, region, enabled)
Client.endpoints.update(self, endpoint, service, url, interface, region, enabled)
Client.endpoints.get(self, endpoint)
Client.projects.find(self)
Client.endpoints.list(self, service, interface, region, enabled, region_id)
Client.endpoints.delete(self, endpoint)
Client.users.create(self, name, domain, project, password, email, description, enabled, default_project)
Client.users.update(self, user, name, domain, project, password, email, description, enabled, default_project)
Client.users.get(self, user)
Client.users.list(self, project, domain, group, default_project)
Client.users.delete(self, user)
Client.groups.create(self, name, domain, description)
Client.groups.update(self, group, name, description)
Client.groups.get(self, group)
Client.groups.list(self, user, domain)
Client.groups.delete(self, group)
'''


                '''
                native_action = action
                if action == "get":
                    native_action = "show"
                elif action == "list":
                    native_component = "networks"
                elif action == "find":
                    native_action = "list"
                else:
                    native_action = action
                    native_component = component

                component_method = getattr(
                                    self.native,
                                    "{0}_{1}".format(native_action,
                                                     native_component))
                # define methods
                if action in ["get"]:
                    setattr(self, "_{0}_{1}".format(component, action),
                            self._obj_to_accessible(component_method,
                                                    component + "s"))
                elif action in ["list", "find"]:
                    setattr(self, "_{0}_{1}".format(component, action),
                            self._lst_to_accessible(component_method,
                                                    component + "s"))
                elif action in ["create"]:
                    func = lambda **kwargs: component_method(
                                                self._to_body(component,
                                                              **kwargs))
                    setattr(self, "_{0}_{1}".format(component, action),
                            self._obj_to_accessible(func, component))
                elif action in ["update"]:
                    func = lambda id, **kwargs: component_method(
                                                    id,
                                                    self._to_body(component,
                                                                  **kwargs))
                    setattr(self, "_{0}_{1}".format(component, action),
                            self._obj_to_accessible(func, component))
                elif action in ["delete"]:
                    setattr(self, "_{0}_{1}".format(component, action),
                            lambda id: component_method(id))
                '''
