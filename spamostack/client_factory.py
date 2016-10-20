#
# Copyright 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import re

from cinderclient import client as cinder_client
from glanceclient import client as glance_client
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient import client as keystone_client
from neutronclient.neutron import client as neutron_client
from novaclient import client as nova_client
from swiftclient import client as swift_client


class ClientFactory(object):
    def __init__(self, user, os_identity_api_version="3",
                 os_network_api_version="2", os_volume_api_version="2",
                 os_compute_api_version="2", os_image_api_version="2"):
        """Create instance of `ClientFactory` class

        @param user: User for client factory instance
        @type user: `dict`
        """

        self.user = user
        self.auth = v3.Password(**user)
        self.session = session.Session(auth=self.auth)
        self.os_identity_api_version = os_identity_api_version
        self.os_network_api_version = os_network_api_version
        self.os_volume_api_version = os_volume_api_version
        self.os_compute_api_version = os_compute_api_version
        self.os_image_api_version = os_image_api_version

    def cinder(self):
        """Create cinder client."""

        return Cinder(cinder_client.Client(self.os_volume_api_version,
                                           session=self.session))

    def glance(self):
        """Create glance client."""

        return Glance(glance_client.Client(self.os_image_api_version,
                                           session=self.session))

    def keystone(self):
        """Create keystone client."""

        return Keystone(keystone_client.Client(self.os_identity_api_version,
                                               session=self.session))

    def neutron(self):
        """Create neutron client."""

        return Neutron(neutron_client.Client(self.os_network_api_version,
                                             session=self.session))

    def nova(self):
        """Create nova client."""

        return Nova(nova_client.Client(self.os_compute_api_version,
                                       session=self.session))

    def swift(self):
        """Create swift client."""

        return Swift(swift_client.Connection(
            authurl=self.user["auth_url"], user=self.user["username"],
            key=self.user["password"], tenant_name=self.user["project_name"],
            auth_version=self.os_identity_api_version))


class Accessible(dict):
    def __init__(self, *args, **kwargs):
        """Create an instance of `Accessible` class.

        That class uses as a wrapper for neutron client.
        """
        super(Accessible, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.iteritems():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Accessible, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Accessible, self).__delitem__(key)
        del self.__dict__[key]


def _obj_to_accessible(component=None):
    def obj_to_accessible(func):
        def wrapper(*args, **kwargs):
            if component:
                acc_obj = Accessible(func(*args, **kwargs)[component])
            else:
                acc_obj = Accessible(func(*args, **kwargs))
            return acc_obj
        return wrapper
    return obj_to_accessible


def _lst_to_accessible(component=None):
    def lst_to_accessible(func):
        def wrapper(*args, **kwargs):
            result = []
            for el in func(*args, **kwargs):
                if component:
                    result.append(Accessible(el[component]))
                else:
                    result.append(Accessible(el))
            return result
        return wrapper
    return lst_to_accessible


def _to_body(component, **kwargs):
    body = {component: {}}

    for key, value in kwargs.iteritems():
        body[component][key] = value

    return body


class Cinder(object):
    def __init__(self, client):
        self.native = client

        for name in dir(self.native):
            if not name.startswith("__"):
                value = getattr(self.native, name)
                setattr(self, name, value)


class Glance(object):
    def __init__(self, client):
        self.native = client

        for name in dir(self.native):
            if not name.startswith("__"):
                value = getattr(self.native, name)
                setattr(self, name, value)
        self.images.find = self.find

    def find(self, **kwargs):
        return list(self.native.images.list(filters=kwargs))[0]


class Keystone(object):
    def __init__(self, client):
        self.native = client

        for name in dir(self.native):
            if not name.startswith("__") and name not in ["service_catalog"]:
                value = getattr(self.native, name)
                setattr(self, name, value)


class Neutron(object):
    def __init__(self, client):
        self.native = client

        actions = ["create", "delete", "find", "get", "list", "update"]
        components = []

        for name in dir(self.native):
            if not name.startswith("__") and name.startswith("show"):
                component = re.sub("show_", "", name)
                components.append(component)
                setattr(self, component + "s", lambda: None)

        for component in components:
            component_obj = getattr(self, component + "s")
            for action in actions:
                if ((action in ["update"] and
                    component in ["metering_label", "metering_label_rule",
                                  "qos_queue", "security_group_rule",
                                  "extension", "network_ip_availability"]) or
                    (action in ["create"] and
                    component in ["agent", "quota",
                                  "extension", "network_ip_availability"]) or
                    (action in ["delete"] and
                        component in ["extension",
                                      "network_ip_availability"])):
                    continue

                method = getattr(self, "_{0}_{1}".format(component, action))
                setattr(component_obj, action, method)

    @_obj_to_accessible("address_scope")
    def _address_scope_create(self, **kwargs):
        return self.native.create_address_scope(
            _to_body("address_scope", **kwargs))

    def _address_scope_delete(self, id):
        return self.native.delete_address_scope(id)

    @_lst_to_accessible("address_scopes")
    def _address_scope_find(self, **kwargs):
        return self._address_scope_list(**kwargs)

    @_obj_to_accessible("address_scope")
    def _address_scope_get(self, id, **kwargs):
        return self.native.show_address_scope(id, **kwargs)

    @_lst_to_accessible("address_scopes")
    def _address_scope_list(self, **kwargs):
        return self.native.list_address_scopes(**kwargs)

    @_obj_to_accessible("address_scope")
    def _address_scope_update(self, id, **kwargs):
        return self.native.update_address_scope(
            id, _to_body("address_scope", **kwargs))

    # ----------------------------------------------------------------------- #

    def _agent_delete(self, id):
        return self.native.delete_agent(id)

    @_lst_to_accessible("agents")
    def _agent_find(self, **kwargs):
        return self._agent_list(**kwargs)

    @_obj_to_accessible("agent")
    def _agent_get(self, id, **kwargs):
        return self.native.show_agent(id, **kwargs)

    @_lst_to_accessible("agents")
    def _agent_list(self, **kwargs):
        return self.native.list_agent(**kwargs)

    @_obj_to_accessible("agent")
    def _agent_update(self, id, **kwargs):
        return self.native.update_agent(
            id, _to_body("agent", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("bandwidth_limit_rule")
    def _bandwidth_limit_rule_create(self, **kwargs):
        return self.native.create_bandwidth_limit_rule(
            _to_body("bandwidth_limit_rule", **kwargs))

    def _bandwidth_limit_rule_delete(self, id):
        return self.native.delete_bandwidth_limit_rule(id)

    @_lst_to_accessible("bandwidth_limit_rules")
    def _bandwidth_limit_rule_find(self, **kwargs):
        return self._bandwidth_limit_rule_list(**kwargs)

    @_obj_to_accessible("bandwidth_limit_rule")
    def _bandwidth_limit_rule_get(self, id, **kwargs):
        return self.native.show_bandwidth_limit_rule(id, **kwargs)

    @_lst_to_accessible("bandwidth_limit_rules")
    def _bandwidth_limit_rule_list(self, **kwargs):
        return self.native.list_bandwidth_limit_rules(**kwargs)

    @_obj_to_accessible("bandwidth_limit_rule")
    def _bandwidth_limit_rule_update(self, id, **kwargs):
        return self.native.update_bandwidth_limit_rule(
            id, _to_body("bandwidth_limit_rule", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("bgp_peer")
    def _bgp_peer_create(self, **kwargs):
        return self.native.create_bgp_peer(
            _to_body("bgp_peer", **kwargs))

    def _bgp_peer_delete(self, id):
        return self.native.delete_bgp_peer(id)

    @_lst_to_accessible("bgp_peers")
    def _bgp_peer_find(self, **kwargs):
        return self._bgp_peer_list(**kwargs)

    @_obj_to_accessible("bgp_peer")
    def _bgp_peer_get(self, id, **kwargs):
        return self.native.show_bgp_peer(id, **kwargs)

    @_lst_to_accessible("bgp_peers")
    def _bgp_peer_list(self, **kwargs):
        return self.native.list_bgp_peers(**kwargs)

    @_obj_to_accessible("bgp_peer")
    def _bgp_peer_update(self, id, **kwargs):
        return self.native.update_bgp_peer(
            id, _to_body("bgp_peer", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("bgp_speaker")
    def _bgp_speaker_create(self, **kwargs):
        return self.native.create_bgp_speaker(
            _to_body("bgp_speaker", **kwargs))

    def _bgp_speaker_delete(self, id):
        return self.native.delete_bgp_speaker(id)

    @_lst_to_accessible("bgp_speakers")
    def _bgp_speaker_find(self, **kwargs):
        return self._bgp_speaker_list(**kwargs)

    @_obj_to_accessible("bgp_speaker")
    def _bgp_speaker_get(self, id, **kwargs):
        return self.native.show_bgp_speaker(id, **kwargs)

    @_lst_to_accessible("bgp_speakers")
    def _bgp_speaker_list(self, **kwargs):
        return self.native.list_bgp_speakers(**kwargs)

    @_obj_to_accessible("bgp_speaker")
    def _bgp_speaker_update(self, id, **kwargs):
        return self.native.update_bgp_speaker(
            id, _to_body("bgp_speaker", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("dscp_marking_rule")
    def _dscp_marking_rule_create(self, **kwargs):
        return self.native.create_dscp_marking_rule(
            _to_body("dscp_marking_rule", **kwargs))

    def _dscp_marking_rule_delete(self, id):
        return self.native.delete_dscp_marking_rule(id)

    @_lst_to_accessible("dscp_marking_rules")
    def _dscp_marking_rule_find(self, **kwargs):
        return self._dscp_marking_rule_list(**kwargs)

    @_obj_to_accessible("dscp_marking_rule")
    def _dscp_marking_rule_get(self, id, **kwargs):
        return self.native.show_dscp_marking_rule(id, **kwargs)

    @_lst_to_accessible("dscp_marking_rules")
    def _dscp_marking_rule_list(self, **kwargs):
        return self.native.list_dscp_marking_rules(**kwargs)

    @_obj_to_accessible("dscp_marking_rule")
    def _dscp_marking_rule_update(self, id, **kwargs):
        return self.native.update_dscp_marking_rule(
            id, _to_body("dscp_marking_rule", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("endpoint_group")
    def _endpoint_group_create(self, **kwargs):
        return self.native.create_endpoint_group(
            _to_body("endpoint_group", **kwargs))

    def _endpoint_group_delete(self, id):
        return self.native.delete_endpoint_group(id)

    @_lst_to_accessible("endpoint_groups")
    def _endpoint_group_find(self, **kwargs):
        return self._endpoint_group_list(**kwargs)

    @_obj_to_accessible("endpoint_group")
    def _endpoint_group_get(self, id, **kwargs):
        return self.native.show_endpoint_group(id, **kwargs)

    @_lst_to_accessible("endpoint_groups")
    def _endpoint_group_list(self, **kwargs):
        return self.native.list_endpoint_groups(**kwargs)

    @_obj_to_accessible("endpoint_group")
    def _endpoint_group_update(self, id, **kwargs):
        return self.native.update_endpoint_group(
            id, _to_body("endpoint_group", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("ext")
    def _ext_create(self, **kwargs):
        return self.native.create_ext(
            _to_body("ext", **kwargs))

    def _ext_delete(self, id):
        return self.native.delete_ext(id)

    @_lst_to_accessible("exts")
    def _ext_find(self, **kwargs):
        return self._ext_list(**kwargs)

    @_obj_to_accessible("ext")
    def _ext_get(self, id, **kwargs):
        return self.native.show_ext(id, **kwargs)

    @_lst_to_accessible("exts")
    def _ext_list(self, **kwargs):
        return self.native.list_exts(**kwargs)

    @_obj_to_accessible("ext")
    def _ext_update(self, id, **kwargs):
        return self.native.update_ext(
            id, _to_body("ext", **kwargs))

    # ----------------------------------------------------------------------- #

    @_lst_to_accessible("extensions")
    def _extension_find(self, **kwargs):
        return self._extension_list(**kwargs)

    @_lst_to_accessible("extensions")
    def _extension_list(self, **kwargs):
        return self.native.list_extensions(**kwargs)

    @_obj_to_accessible("extension")
    def _extension_get(self, id, **kwargs):
        return self.native.show_extension(id, **kwargs)

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("firewall")
    def _firewall_create(self, **kwargs):
        return self.native.create_firewall(
            _to_body("firewall", **kwargs))

    def _firewall_delete(self, id):
        return self.native.delete_firewall(id)

    @_lst_to_accessible("firewalls")
    def _firewall_find(self, **kwargs):
        return self._firewall_list(**kwargs)

    @_obj_to_accessible("firewall")
    def _firewall_get(self, id, **kwargs):
        return self.native.show_firewall(id, **kwargs)

    @_lst_to_accessible("firewalls")
    def _firewall_list(self, **kwargs):
        return self.native.list_firewalls(**kwargs)

    @_obj_to_accessible("firewall")
    def _firewall_update(self, id, **kwargs):
        return self.native.update_firewall(
            id, _to_body("firewall", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("firewall_policy")
    def _firewall_policy_create(self, **kwargs):
        return self.native.create_firewall_policy(
            _to_body("firewall_policy", **kwargs))

    def _firewall_policy_delete(self, id):
        return self.native.delete_firewall_policy(id)

    @_lst_to_accessible("firewall_policys")
    def _firewall_policy_find(self, **kwargs):
        return self._firewall_policy_list(**kwargs)

    @_obj_to_accessible("firewall_policy")
    def _firewall_policy_get(self, id, **kwargs):
        return self.native.show_firewall_policy(id, **kwargs)

    @_lst_to_accessible("firewall_policys")
    def _firewall_policy_list(self, **kwargs):
        return self.native.list_firewall_policys(**kwargs)

    @_obj_to_accessible("firewall_policy")
    def _firewall_policy_update(self, id, **kwargs):
        return self.native.update_firewall_policy(
            id, _to_body("firewall_policy", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("firewall_rule")
    def _firewall_rule_create(self, **kwargs):
        return self.native.create_firewall_rule(
            _to_body("firewall_rule", **kwargs))

    def _firewall_rule_delete(self, id):
        return self.native.delete_firewall_rule(id)

    @_lst_to_accessible("firewall_rules")
    def _firewall_rule_find(self, **kwargs):
        return self._firewall_rule_list(**kwargs)

    @_obj_to_accessible("firewall_rule")
    def _firewall_rule_get(self, id, **kwargs):
        return self.native.show_firewall_rule(id, **kwargs)

    @_lst_to_accessible("firewall_rules")
    def _firewall_rule_list(self, **kwargs):
        return self.native.list_firewall_rules(**kwargs)

    @_obj_to_accessible("firewall_rule")
    def _firewall_rule_update(self, id, **kwargs):
        return self.native.update_firewall_rule(
            id, _to_body("firewall_rule", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("flavor")
    def _flavor_create(self, **kwargs):
        return self.native.create_flavor(
            _to_body("flavor", **kwargs))

    def _flavor_delete(self, id):
        return self.native.delete_flavor(id)

    @_lst_to_accessible("flavors")
    def _flavor_find(self, **kwargs):
        return self._flavor_list(**kwargs)

    @_obj_to_accessible("flavor")
    def _flavor_get(self, id, **kwargs):
        return self.native.show_flavor(id, **kwargs)

    @_lst_to_accessible("flavors")
    def _flavor_list(self, **kwargs):
        return self.native.list_flavors(**kwargs)

    @_obj_to_accessible("flavor")
    def _flavor_update(self, id, **kwargs):
        return self.native.update_flavor(
            id, _to_body("flavor", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("floatingip")
    def _floatingip_create(self, **kwargs):
        return self.native.create_floatingip(
            _to_body("floatingip", **kwargs))

    def _floatingip_delete(self, id):
        return self.native.delete_floatingip(id)

    @_lst_to_accessible("floatingips")
    def _floatingip_find(self, **kwargs):
        return self._floatingip_list(**kwargs)

    @_obj_to_accessible("floatingip")
    def _floatingip_get(self, id, **kwargs):
        return self.native.show_floatingip(id, **kwargs)

    @_lst_to_accessible("floatingips")
    def _floatingip_list(self, **kwargs):
        return self.native.list_floatingips(**kwargs)

    @_obj_to_accessible("floatingip")
    def _floatingip_update(self, id, **kwargs):
        return self.native.update_floatingip(
            id, _to_body("floatingip", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("gateway_device")
    def _gateway_device_create(self, **kwargs):
        return self.native.create_gateway_device(
            _to_body("gateway_device", **kwargs))

    def _gateway_device_delete(self, id):
        return self.native.delete_gateway_device(id)

    @_lst_to_accessible("gateway_devices")
    def _gateway_device_find(self, **kwargs):
        return self._gateway_device_list(**kwargs)

    @_obj_to_accessible("gateway_device")
    def _gateway_device_get(self, id, **kwargs):
        return self.native.show_gateway_device(id, **kwargs)

    @_lst_to_accessible("gateway_devices")
    def _gateway_device_list(self, **kwargs):
        return self.native.list_gateway_devices(**kwargs)

    @_obj_to_accessible("gateway_device")
    def _gateway_device_update(self, id, **kwargs):
        return self.native.update_gateway_device(
            id, _to_body("gateway_device", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("health_monitor")
    def _health_monitor_create(self, **kwargs):
        return self.native.create_health_monitor(
            _to_body("health_monitor", **kwargs))

    def _health_monitor_delete(self, id):
        return self.native.delete_health_monitor(id)

    @_lst_to_accessible("health_monitors")
    def _health_monitor_find(self, **kwargs):
        return self._health_monitor_list(**kwargs)

    @_obj_to_accessible("health_monitor")
    def _health_monitor_get(self, id, **kwargs):
        return self.native.show_health_monitor(id, **kwargs)

    @_lst_to_accessible("health_monitors")
    def _health_monitor_list(self, **kwargs):
        return self.native.list_health_monitors(**kwargs)

    @_obj_to_accessible("health_monitor")
    def _health_monitor_update(self, id, **kwargs):
        return self.native.update_health_monitor(
            id, _to_body("health_monitor", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("ikepolicy")
    def _ikepolicy_create(self, **kwargs):
        return self.native.create_ikepolicy(
            _to_body("ikepolicy", **kwargs))

    def _ikepolicy_delete(self, id):
        return self.native.delete_ikepolicy(id)

    @_lst_to_accessible("ikepolicys")
    def _ikepolicy_find(self, **kwargs):
        return self._ikepolicy_list(**kwargs)

    @_obj_to_accessible("ikepolicy")
    def _ikepolicy_get(self, id, **kwargs):
        return self.native.show_ikepolicy(id, **kwargs)

    @_lst_to_accessible("ikepolicys")
    def _ikepolicy_list(self, **kwargs):
        return self.native.list_ikepolicys(**kwargs)

    @_obj_to_accessible("ikepolicy")
    def _ikepolicy_update(self, id, **kwargs):
        return self.native.update_ikepolicy(
            id, _to_body("ikepolicy", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("ipsec_site_connection")
    def _ipsec_site_connection_create(self, **kwargs):
        return self.native.create_ipsec_site_connection(
            _to_body("ipsec_site_connection", **kwargs))

    def _ipsec_site_connection_delete(self, id):
        return self.native.delete_ipsec_site_connection(id)

    @_lst_to_accessible("ipsec_site_connections")
    def _ipsec_site_connection_find(self, **kwargs):
        return self._ipsec_site_connection_list(**kwargs)

    @_obj_to_accessible("ipsec_site_connection")
    def _ipsec_site_connection_get(self, id, **kwargs):
        return self.native.show_ipsec_site_connection(id, **kwargs)

    @_lst_to_accessible("ipsec_site_connections")
    def _ipsec_site_connection_list(self, **kwargs):
        return self.native.list_ipsec_site_connections(**kwargs)

    @_obj_to_accessible("ipsec_site_connection")
    def _ipsec_site_connection_update(self, id, **kwargs):
        return self.native.update_ipsec_site_connection(
            id, _to_body("ipsec_site_connection", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("ipsecpolicy")
    def _ipsecpolicy_create(self, **kwargs):
        return self.native.create_ipsecpolicy(
            _to_body("ipsecpolicy", **kwargs))

    def _ipsecpolicy_delete(self, id):
        return self.native.delete_ipsecpolicy(id)

    @_lst_to_accessible("ipsecpolicys")
    def _ipsecpolicy_find(self, **kwargs):
        return self._ipsecpolicy_list(**kwargs)

    @_obj_to_accessible("ipsecpolicy")
    def _ipsecpolicy_get(self, id, **kwargs):
        return self.native.show_ipsecpolicy(id, **kwargs)

    @_lst_to_accessible("ipsecpolicys")
    def _ipsecpolicy_list(self, **kwargs):
        return self.native.list_ipsecpolicys(**kwargs)

    @_obj_to_accessible("ipsecpolicy")
    def _ipsecpolicy_update(self, id, **kwargs):
        return self.native.update_ipsecpolicy(
            id, _to_body("ipsecpolicy", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("lbaas_healthmonitor")
    def _lbaas_healthmonitor_create(self, **kwargs):
        return self.native.create_lbaas_healthmonitor(
            _to_body("lbaas_healthmonitor", **kwargs))

    def _lbaas_healthmonitor_delete(self, id):
        return self.native.delete_lbaas_healthmonitor(id)

    @_lst_to_accessible("lbaas_healthmonitors")
    def _lbaas_healthmonitor_find(self, **kwargs):
        return self._lbaas_healthmonitor_list(**kwargs)

    @_obj_to_accessible("lbaas_healthmonitor")
    def _lbaas_healthmonitor_get(self, id, **kwargs):
        return self.native.show_lbaas_healthmonitor(id, **kwargs)

    @_lst_to_accessible("lbaas_healthmonitors")
    def _lbaas_healthmonitor_list(self, **kwargs):
        return self.native.list_lbaas_healthmonitors(**kwargs)

    @_obj_to_accessible("lbaas_healthmonitor")
    def _lbaas_healthmonitor_update(self, id, **kwargs):
        return self.native.update_lbaas_healthmonitor(
            id, _to_body("lbaas_healthmonitor", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("lbaas_l7policy")
    def _lbaas_l7policy_create(self, **kwargs):
        return self.native.create_lbaas_l7policy(
            _to_body("lbaas_l7policy", **kwargs))

    def _lbaas_l7policy_delete(self, id):
        return self.native.delete_lbaas_l7policy(id)

    @_lst_to_accessible("lbaas_l7policys")
    def _lbaas_l7policy_find(self, **kwargs):
        return self._lbaas_l7policy_list(**kwargs)

    @_obj_to_accessible("lbaas_l7policy")
    def _lbaas_l7policy_get(self, id, **kwargs):
        return self.native.show_lbaas_l7policy(id, **kwargs)

    @_lst_to_accessible("lbaas_l7policys")
    def _lbaas_l7policy_list(self, **kwargs):
        return self.native.list_lbaas_l7policys(**kwargs)

    @_obj_to_accessible("lbaas_l7policy")
    def _lbaas_l7policy_update(self, id, **kwargs):
        return self.native.update_lbaas_l7policy(
            id, _to_body("lbaas_l7policy", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("lbaas_l7rule")
    def _lbaas_l7rule_create(self, **kwargs):
        return self.native.create_lbaas_l7rule(
            _to_body("lbaas_l7rule", **kwargs))

    def _lbaas_l7rule_delete(self, id):
        return self.native.delete_lbaas_l7rule(id)

    @_lst_to_accessible("lbaas_l7rules")
    def _lbaas_l7rule_find(self, **kwargs):
        return self._lbaas_l7rule_list(**kwargs)

    @_obj_to_accessible("lbaas_l7rule")
    def _lbaas_l7rule_get(self, id, **kwargs):
        return self.native.show_lbaas_l7rule(id, **kwargs)

    @_lst_to_accessible("lbaas_l7rules")
    def _lbaas_l7rule_list(self, **kwargs):
        return self.native.list_lbaas_l7rules(**kwargs)

    @_obj_to_accessible("lbaas_l7rule")
    def _lbaas_l7rule_update(self, id, **kwargs):
        return self.native.update_lbaas_l7rule(
            id, _to_body("lbaas_l7rule", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("lbaas_member")
    def _lbaas_member_create(self, **kwargs):
        return self.native.create_lbaas_member(
            _to_body("lbaas_member", **kwargs))

    def _lbaas_member_delete(self, id):
        return self.native.delete_lbaas_member(id)

    @_lst_to_accessible("lbaas_members")
    def _lbaas_member_find(self, **kwargs):
        return self._lbaas_member_list(**kwargs)

    @_obj_to_accessible("lbaas_member")
    def _lbaas_member_get(self, id, **kwargs):
        return self.native.show_lbaas_member(id, **kwargs)

    @_lst_to_accessible("lbaas_members")
    def _lbaas_member_list(self, **kwargs):
        return self.native.list_lbaas_members(**kwargs)

    @_obj_to_accessible("lbaas_member")
    def _lbaas_member_update(self, id, **kwargs):
        return self.native.update_lbaas_member(
            id, _to_body("lbaas_member", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("lbaas_pool")
    def _lbaas_pool_create(self, **kwargs):
        return self.native.create_lbaas_pool(
            _to_body("lbaas_pool", **kwargs))

    def _lbaas_pool_delete(self, id):
        return self.native.delete_lbaas_pool(id)

    @_lst_to_accessible("lbaas_pools")
    def _lbaas_pool_find(self, **kwargs):
        return self._lbaas_pool_list(**kwargs)

    @_obj_to_accessible("lbaas_pool")
    def _lbaas_pool_get(self, id, **kwargs):
        return self.native.show_lbaas_lbaas_pool(id, **kwargs)

    @_lst_to_accessible("lbaas_pools")
    def _lbaas_pool_list(self, **kwargs):
        return self.native.list_lbaas_pools(**kwargs)

    @_obj_to_accessible("lbaas_pool")
    def _lbaas_pool_update(self, id, **kwargs):
        return self.native.update_lbaas_pool(
            id, _to_body("lbaas_pool", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("listener")
    def _listener_create(self, **kwargs):
        return self.native.create_listener(
            _to_body("listener", **kwargs))

    def _listener_delete(self, id):
        return self.native.delete_listener(id)

    @_lst_to_accessible("listeners")
    def _listener_find(self, **kwargs):
        return self._listener_list(**kwargs)

    @_obj_to_accessible("listener")
    def _listener_get(self, id, **kwargs):
        return self.native.show_listener(id, **kwargs)

    @_lst_to_accessible("listeners")
    def _listener_list(self, **kwargs):
        return self.native.list_listeners(**kwargs)

    @_obj_to_accessible("listener")
    def _listener_update(self, id, **kwargs):
        return self.native.update_listener(
            id, _to_body("listener", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("loadbalancer")
    def _loadbalancer_create(self, **kwargs):
        return self.native.create_loadbalancer(
            _to_body("loadbalancer", **kwargs))

    def _loadbalancer_delete(self, id):
        return self.native.delete_loadbalancer(id)

    @_lst_to_accessible("loadbalancers")
    def _loadbalancer_find(self, **kwargs):
        return self._loadbalancer_list(**kwargs)

    @_obj_to_accessible("loadbalancer")
    def _loadbalancer_get(self, id, **kwargs):
        return self.native.show_loadbalancer(id, **kwargs)

    @_lst_to_accessible("loadbalancers")
    def _loadbalancer_list(self, **kwargs):
        return self.native.list_loadbalancers(**kwargs)

    @_obj_to_accessible("loadbalancer")
    def _loadbalancer_update(self, id, **kwargs):
        return self.native.update_loadbalancer(
            id, _to_body("loadbalancer", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("member")
    def _member_create(self, **kwargs):
        return self.native.create_member(
            _to_body("member", **kwargs))

    def _member_delete(self, id):
        return self.native.delete_member(id)

    @_lst_to_accessible("members")
    def _member_find(self, **kwargs):
        return self._member_list(**kwargs)

    @_obj_to_accessible("member")
    def _member_get(self, id, **kwargs):
        return self.native.show_member(id, **kwargs)

    @_lst_to_accessible("members")
    def _member_list(self, **kwargs):
        return self.native.list_members(**kwargs)

    @_obj_to_accessible("member")
    def _member_update(self, id, **kwargs):
        return self.native.update_member(
            id, _to_body("member", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("metering_label")
    def _metering_label_create(self, **kwargs):
        return self.native.create_metering_label(
            _to_body("metering_label", **kwargs))

    def _metering_label_delete(self, id):
        return self.native.delete_metering_label(id)

    @_lst_to_accessible("metering_labels")
    def _metering_label_find(self, **kwargs):
        return self._metering_label_list(**kwargs)

    @_obj_to_accessible("metering_label")
    def _metering_label_get(self, id, **kwargs):
        return self.native.show_metering_label(id, **kwargs)

    @_lst_to_accessible("metering_labels")
    def _metering_label_list(self, **kwargs):
        return self.native.list_metering_labels(**kwargs)

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("metering_label_rule")
    def _metering_label_rule_create(self, **kwargs):
        return self.native.create_metering_label_rule(
            _to_body("metering_label_rule", **kwargs))

    def _metering_label_rule_delete(self, id):
        return self.native.delete_metering_label_rule(id)

    @_lst_to_accessible("metering_label_rules")
    def _metering_label_rule_find(self, **kwargs):
        return self._metering_label_rule_list(**kwargs)

    @_obj_to_accessible("metering_label_rule")
    def _metering_label_rule_get(self, id, **kwargs):
        return self.native.show_metering_label_rule(id, **kwargs)

    @_lst_to_accessible("metering_label_rules")
    def _metering_label_rule_list(self, **kwargs):
        return self.native.list_metering_label_rules(**kwargs)

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("network")
    def _network_create(self, **kwargs):
        return self.native.create_network(
            _to_body("network", **kwargs))

    def _network_delete(self, id):
        return self.native.delete_network(id)

    @_lst_to_accessible("networks")
    def _network_find(self, **kwargs):
        return self._network_list(**kwargs)

    @_obj_to_accessible("network")
    def _network_get(self, id, **kwargs):
        return self.native.show_network(id, **kwargs)

    @_lst_to_accessible("networks")
    def _network_list(self, **kwargs):
        return self.native.list_networks(**kwargs)

    @_obj_to_accessible("network")
    def _network_update(self, id, **kwargs):
        return self.native.update_network(
            id, _to_body("network", **kwargs))

    # ----------------------------------------------------------------------- #

    @_lst_to_accessible("network_ip_availabilities")
    def _network_ip_availability_find(self, **kwargs):
        return self._network_ip_availability_list(**kwargs)

    @_obj_to_accessible("network_ip_availability")
    def _network_ip_availability_get(self, id, **kwargs):
        return self.native.show_network_ip_availability(id, **kwargs)

    @_lst_to_accessible("network_ip_availabilities")
    def _network_ip_availability_list(self, **kwargs):
        return self.native.list_network_ip_availabilties(**kwargs)

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("network_gateway")
    def _network_gateway_create(self, **kwargs):
        return self.native.create_network_gateway(
            _to_body("network_gateway", **kwargs))

    def _network_gateway_delete(self, id):
        return self.native.delete_network_gateway(id)

    @_lst_to_accessible("network_gateways")
    def _network_gateway_find(self, **kwargs):
        return self._network_gateway_list(**kwargs)

    @_obj_to_accessible("network_gateway")
    def _network_gateway_get(self, id, **kwargs):
        return self.native.show_network_gateway(id, **kwargs)

    @_lst_to_accessible("network_gateways")
    def _network_gateway_list(self, **kwargs):
        return self.native.list_network_gateways(**kwargs)

    @_obj_to_accessible("network_gateway")
    def _network_gateway_update(self, id, **kwargs):
        return self.native.update_network_gateway(
            id, _to_body("network_gateway", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("pool")
    def _pool_create(self, **kwargs):
        return self.native.create_pool(
            _to_body("pool", **kwargs))

    def _pool_delete(self, id):
        return self.native.delete_pool(id)

    @_lst_to_accessible("pools")
    def _pool_find(self, **kwargs):
        return self._pool_list(**kwargs)

    @_obj_to_accessible("pool")
    def _pool_get(self, id, **kwargs):
        return self.native.show_pool(id, **kwargs)

    @_lst_to_accessible("pools")
    def _pool_list(self, **kwargs):
        return self.native.list_pools(**kwargs)

    @_obj_to_accessible("pool")
    def _pool_update(self, id, **kwargs):
        return self.native.update_pool(
            id, _to_body("pool", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("port")
    def _port_create(self, **kwargs):
        return self.native.create_port(
            _to_body("port", **kwargs))

    def _port_delete(self, id):
        return self.native.delete_port(id)

    @_lst_to_accessible("ports")
    def _port_find(self, **kwargs):
        return self._port_list(**kwargs)

    @_obj_to_accessible("port")
    def _port_get(self, id, **kwargs):
        return self.native.show_port(id, **kwargs)

    @_lst_to_accessible("ports")
    def _port_list(self, **kwargs):
        return self.native.list_ports(**kwargs)

    @_obj_to_accessible("port")
    def _port_update(self, id, **kwargs):
        return self.native.update_port(
            id, _to_body("port", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("qos_policy")
    def _qos_policy_create(self, **kwargs):
        return self.native.create_qos_policy(
            _to_body("qos_policy", **kwargs))

    def _qos_policy_delete(self, id):
        return self.native.delete_qos_policy(id)

    @_lst_to_accessible("qos_policys")
    def _qos_policy_find(self, **kwargs):
        return self._qos_policy_list(**kwargs)

    @_obj_to_accessible("qos_policy")
    def _qos_policy_get(self, id, **kwargs):
        return self.native.show_qos_policy(id, **kwargs)

    @_lst_to_accessible("qos_policys")
    def _qos_policy_list(self, **kwargs):
        return self.native.list_qos_policys(**kwargs)

    @_obj_to_accessible("qos_policy")
    def _qos_policy_update(self, id, **kwargs):
        return self.native.update_qos_policy(
            id, _to_body("qos_policy", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("qos_queue")
    def _qos_queue_create(self, **kwargs):
        return self.native.create_qos_queue(
            _to_body("qos_queue", **kwargs))

    def _qos_queue_delete(self, id):
        return self.native.delete_qos_queue(id)

    @_lst_to_accessible("qos_queues")
    def _qos_queue_find(self, **kwargs):
        return self._qos_queue_list(**kwargs)

    @_obj_to_accessible("qos_queue")
    def _qos_queue_get(self, id, **kwargs):
        return self.native.show_qos_queue(id, **kwargs)

    @_lst_to_accessible("qos_queues")
    def _qos_queue_list(self, **kwargs):
        return self.native.list_qos_queues(**kwargs)

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("rbac_policy")
    def _rbac_policy_create(self, **kwargs):
        return self.native.create_rbac_policy(
            _to_body("rbac_policy", **kwargs))

    def _rbac_policy_delete(self, id):
        return self.native.delete_rbac_policy(id)

    @_lst_to_accessible("rbac_policys")
    def _rbac_policy_find(self, **kwargs):
        return self._rbac_policy_list(**kwargs)

    @_obj_to_accessible("rbac_policy")
    def _rbac_policy_get(self, id, **kwargs):
        return self.native.show_rbac_policy(id, **kwargs)

    @_lst_to_accessible("rbac_policys")
    def _rbac_policy_list(self, **kwargs):
        return self.native.list_rbac_policys(**kwargs)

    @_obj_to_accessible("rbac_policy")
    def _rbac_policy_update(self, id, **kwargs):
        return self.native.update_rbac_policy(
            id, _to_body("rbac_policy", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("router")
    def _router_create(self, **kwargs):
        return self.native.create_router(
            _to_body("router", **kwargs))

    def _router_delete(self, id):
        return self.native.delete_router(id)

    @_lst_to_accessible("routers")
    def _router_find(self, **kwargs):
        return self._router_list(**kwargs)

    @_obj_to_accessible("router")
    def _router_get(self, id, **kwargs):
        return self.native.show_router(id, **kwargs)

    @_lst_to_accessible("routers")
    def _router_list(self, **kwargs):
        return self.native.list_routers(**kwargs)

    @_obj_to_accessible("router")
    def _router_update(self, id, **kwargs):
        return self.native.update_router(
            id, _to_body("router", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("security_group")
    def _security_group_create(self, **kwargs):
        return self.native.create_security_group(
            _to_body("security_group", **kwargs))

    def _security_group_delete(self, id):
        return self.native.delete_security_group(id)

    @_lst_to_accessible("security_groups")
    def _security_group_find(self, **kwargs):
        return self._security_group_list(**kwargs)

    @_obj_to_accessible("security_group")
    def _security_group_get(self, id, **kwargs):
        return self.native.show_security_group(id, **kwargs)

    @_lst_to_accessible("security_groups")
    def _security_group_list(self, **kwargs):
        return self.native.list_security_groups(**kwargs)

    @_obj_to_accessible("security_group")
    def _security_group_update(self, id, **kwargs):
        return self.native.update_security_group(
            id, _to_body("security_group", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("security_group_rule")
    def _security_group_rule_create(self, **kwargs):
        return self.native.create_security_group_rule(
            _to_body("security_group_rule", **kwargs))

    def _security_group_rule_delete(self, id):
        return self.native.delete_security_group_rule(id)

    @_lst_to_accessible("security_group_rules")
    def _security_group_rule_find(self, **kwargs):
        return self._security_group_rule_list(**kwargs)

    @_obj_to_accessible("security_group_rule")
    def _security_group_rule_get(self, id, **kwargs):
        return self.native.show_security_group_rule(id, **kwargs)

    @_lst_to_accessible("security_group_rules")
    def _security_group_rule_list(self, **kwargs):
        return self.native.list_security_group_rules(**kwargs)

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("service_profile")
    def _service_profile_create(self, **kwargs):
        return self.native.create_service_profile(
            _to_body("service_profile", **kwargs))

    def _service_profile_delete(self, id):
        return self.native.delete_service_profile(id)

    @_lst_to_accessible("service_profiles")
    def _service_profile_find(self, **kwargs):
        return self._service_profile_list(**kwargs)

    @_obj_to_accessible("service_profile")
    def _service_profile_get(self, id, **kwargs):
        return self.native.show_service_profile(id, **kwargs)

    @_lst_to_accessible("service_profiles")
    def _service_profile_list(self, **kwargs):
        return self.native.list_service_profiles(**kwargs)

    @_obj_to_accessible("service_profile")
    def _service_profile_update(self, id, **kwargs):
        return self.native.update_service_profile(
            id, _to_body("service_profile", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("subnet")
    def _subnet_create(self, **kwargs):
        return self.native.create_subnet(
            _to_body("subnet", **kwargs))

    def _subnet_delete(self, id):
        return self.native.delete_subnet(id)

    @_lst_to_accessible("subnets")
    def _subnet_find(self, **kwargs):
        return self._subnet_list(**kwargs)

    @_obj_to_accessible("subnet")
    def _subnet_get(self, id, **kwargs):
        return self.native.show_subnet(id, **kwargs)

    @_lst_to_accessible("subnets")
    def _subnet_list(self, **kwargs):
        return self.native.list_subnets(**kwargs)

    @_obj_to_accessible("subnet")
    def _subnet_update(self, id, **kwargs):
        return self.native.update_subnet(
            id, _to_body("subnet", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("subnetpool")
    def _subnetpool_create(self, **kwargs):
        return self.native.create_subnetpool(
            _to_body("subnetpool", **kwargs))

    def _subnetpool_delete(self, id):
        return self.native.delete_subnetpool(id)

    @_lst_to_accessible("subnetpools")
    def _subnetpool_find(self, **kwargs):
        return self._subnetpool_list(**kwargs)

    @_obj_to_accessible("subnetpool")
    def _subnetpool_get(self, id, **kwargs):
        return self.native.show_subnetpool(id, **kwargs)

    @_lst_to_accessible("subnetpools")
    def _subnetpool_list(self, **kwargs):
        return self.native.list_subnetpools(**kwargs)

    @_obj_to_accessible("subnetpool")
    def _subnetpool_update(self, id, **kwargs):
        return self.native.update_subnetpool(
            id, _to_body("subnetpool", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("trunk")
    def _trunk_create(self, **kwargs):
        return self.native.create_trunk(
            _to_body("trunk", **kwargs))

    def _trunk_delete(self, id):
        return self.native.delete_trunk(id)

    @_lst_to_accessible("trunks")
    def _trunk_find(self, **kwargs):
        return self._trunk_list(**kwargs)

    @_obj_to_accessible("trunk")
    def _trunk_get(self, id, **kwargs):
        return self.native.show_trunk(id, **kwargs)

    @_lst_to_accessible("trunks")
    def _trunk_list(self, **kwargs):
        return self.native.list_trunks(**kwargs)

    @_obj_to_accessible("trunk")
    def _trunk_update(self, id, **kwargs):
        return self.native.update_trunk(
            id, _to_body("trunk", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("vip")
    def _vip_create(self, **kwargs):
        return self.native.create_vip(
            _to_body("vip", **kwargs))

    def _vip_delete(self, id):
        return self.native.delete_vip(id)

    @_lst_to_accessible("vips")
    def _vip_find(self, **kwargs):
        return self._vip_list(**kwargs)

    @_obj_to_accessible("vip")
    def _vip_get(self, id, **kwargs):
        return self.native.show_vip(id, **kwargs)

    @_lst_to_accessible("vips")
    def _vip_list(self, **kwargs):
        return self.native.list_vips(**kwargs)

    @_obj_to_accessible("vip")
    def _vip_update(self, id, **kwargs):
        return self.native.update_vip(
            id, _to_body("vip", **kwargs))

    # ----------------------------------------------------------------------- #

    @_obj_to_accessible("vpnservice")
    def _vpnservice_create(self, **kwargs):
        return self.native.create_vpnservice(
            _to_body("vpnservice", **kwargs))

    def _vpnservice_delete(self, id):
        return self.native.delete_vpnservice(id)

    @_lst_to_accessible("vpnservices")
    def _vpnservice_find(self, **kwargs):
        return self._vpnservice_list(**kwargs)

    @_obj_to_accessible("vpnservice")
    def _vpnservice_get(self, id, **kwargs):
        return self.native.show_vpnservice(id, **kwargs)

    @_lst_to_accessible("vpnservices")
    def _vpnservice_list(self, **kwargs):
        return self.native.list_vpnservices(**kwargs)

    @_obj_to_accessible("vpnservice")
    def _vpnservice_update(self, id, **kwargs):
        return self.native.update_vpnservice(
            id, _to_body("vpnservice", **kwargs))

    # ----------------------------------------------------------------------- #

    def _quota_delete(self, id):
        return self.native.delete_quota(id)

    @_lst_to_accessible("quotas")
    def _quota_find(self, **kwargs):
        return self._quota_list(**kwargs)

    @_obj_to_accessible("quota")
    def _quota_get(self, id, **kwargs):
        return self.native.show_quota(id, **kwargs)

    @_lst_to_accessible("quotas")
    def _quota_list(self, **kwargs):
        return self.native.list_quotas(**kwargs)

    @_obj_to_accessible("quota")
    def _quota_update(self, id, **kwargs):
        return self.native.update_quota(
            id, _to_body("quota", **kwargs))


class Nova(object):
    def __init__(self, client):
        self.native = client

        for name in dir(self.native):
            if not name.startswith("__"):
                value = getattr(self.native, name)
                setattr(self, name, value)


class Swift(object):
    def __init__(self, client):
        self.native = client

        actions = ["create", "delete", "find", "get", "list", "update"]
        components = ["container", "object"]

        self.containers = lambda: None
        self.objects = lambda: None

        for component in components:
            component_obj = getattr(self, component + "s")
            for action in actions:
                method = getattr(self, "_{0}_{1}".format(component, action))
                setattr(component_obj, action, method)

    def _container_create(self, name=None, headers=None, response_dict=None,
                          query_string=None):
        self.native.put_container(name, headers, response_dict, query_string)

        return self.containers.get(name)

    def _container_delete(self, container, response_dict=None,
                          query_string=None):

        if isinstance(container, str) or isinstance(container, unicode):
            to_delete = container
        elif isinstance(container, Accessible):
            to_delete = container.name
        else:
            return

        return self.native.delete_container(to_delete, response_dict,
                                            query_string)

    def _container_find(self, **kwargs):
        return self.containers.list(**kwargs)

    @_obj_to_accessible()
    def _container_get(self, container, marker=None, limit=None, prefix=None,
                       delimiter=None, end_marker=None, path=None,
                       full_listing=False, headers=None, query_string=None):

        if isinstance(container, str) or isinstance(container, unicode):
            to_get = container
        elif isinstance(container, Accessible):
            to_get = container.name
        else:
            return

        got = self.native.get_container(
            to_get, marker, limit, prefix, delimiter, end_marker, path,
            full_listing, headers, query_string)[0]
        got["id"] = got["x-trans-id"]
        got["name"] = to_get

        return got

    def _container_list(self, marker=None, limit=None, prefix=None,
                        end_marker=None, full_listing=False, **filter):

        filtered = []
        listed = self.native.get_account(marker, limit, prefix, end_marker,
                                         full_listing)[1]

        for el in listed:
            container = self.containers.get(el["name"])
            if filter.viewitems() <= container.viewitems():
                filtered.append(container)

        return filtered

    def _container_update(self, container, headers, response_dict=None):
        if isinstance(container, str) or isinstance(container, unicode):
            to_update = container
        elif isinstance(container, Accessible):
            to_update = container.name
        else:
            return

        self.native.post_container(to_update, headers, response_dict)

        return self.containers.get(to_update)

    # ----------------------------------------------------------------------- #

    def _object_create(self, container, name, content, content_length=None,
                       etag=None, chunk_size=None, content_type=None,
                       headers=None, query_string=None, response_dict=None):

        if isinstance(container, str) or isinstance(container, unicode):
            in_container = container
        elif isinstance(container, Accessible):
            in_container = container.name
        else:
            return

        self.native.put_object(
            in_container, name, content, content_length, etag, chunk_size,
            content_type, headers, query_string, response_dict)

        return self.objects.get(in_container, name)

    def _object_delete(self, container, object, query_string=None,
                       response_dict=None):

        if isinstance(container, str) or isinstance(container, unicode):
            in_container = container
        elif isinstance(container, Accessible):
            in_container = container.name
        else:
            return

        if isinstance(object, str) or isinstance(object, unicode):
            to_delete = object
        elif isinstance(object, Accessible):
            to_delete = object.name
        else:
            return

        return self.native.delete_object(in_container, to_delete, query_string,
                                         response_dict)

    def _object_find(self, container, **kwargs):
        if isinstance(container, str) or isinstance(container, unicode):
            in_container = container
        elif isinstance(container, Accessible):
            in_container = container.name
        else:
            return

        return self.objects.list(in_container, **kwargs)

    @_obj_to_accessible()
    def _object_get(self, container, object, resp_chunk_size=None,
                    query_string=None, response_dict=None, headers=None):

        if isinstance(container, str) or isinstance(container, unicode):
            in_container = container
        elif isinstance(container, Accessible):
            in_container = container.name
        else:
            return

        if isinstance(object, str) or isinstance(object, unicode):
            to_get = object
        elif isinstance(object, Accessible):
            to_get = object.name
        else:
            return

        got = self.native.get_object(in_container, to_get, resp_chunk_size,
                                     query_string, response_dict,
                                     headers)[0]
        got["id"] = got["x-trans-id"]
        got["name"] = to_get

        return got

    def _object_list(self, container, marker=None, limit=None, prefix=None,
                     delimiter=None, end_marker=None, path=None,
                     full_listing=False, headers=None, query_string=None,
                     **filter):

        if isinstance(container, str) or isinstance(container, unicode):
            in_container = container
        elif isinstance(container, Accessible):
            in_container = container.name
        else:
            return

        filtered = []
        listed = self.native.get_container(
            in_container, marker, limit, prefix, delimiter, end_marker, path,
            full_listing, headers, query_string)[1]

        for el in listed:
            object = self.objects.get(in_container, el["name"])
            if filter.viewitems() <= object.viewitems():
                filtered.append(object)

        return [self.objects.get(in_container, el["name"]) for el in filtered]

    def _object_update(self, container, object, headers, response_dict=None):
        if isinstance(container, str) or isinstance(container, unicode):
            in_container = container
        elif isinstance(container, Accessible):
            in_container = container.name
        else:
            return

        if isinstance(object, str) or isinstance(object, unicode):
            to_update = object
        elif isinstance(object, Accessible):
            to_update = object.name
        else:
            return

        self.native.post_object(in_container, to_update, headers,
                                response_dict)

        return self.objects.get(in_container, to_update)
