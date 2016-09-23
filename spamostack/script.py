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
