from keystoneauth1.identity import v3
from keystoneauth1 import session
#from neutronclient.v2_0 import client
from keystoneclient.v3 import client
#from cinderclient.v3 import client

auth = v3.Password(auth_url="http://192.168.122.218:5000/v3", username="admin",
                   password="secret", project_name="admin",
                   user_domain_id="default", project_domain_id="default")

sess = session.Session(auth=auth)
keystone = client.Client(session=sess)
keystone.endpoints.list()[0]
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
