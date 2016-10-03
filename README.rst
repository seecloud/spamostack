spamostack
==========

.. image:: https://travis-ci.org/seecloud/spamostack.svg?branch=master
    :target: https://travis-ci.org/seecloud/spamostack
.. image:: https://coveralls.io/repos/github/seecloud/spamostack/badge.svg?branch=master
    :target: https://coveralls.io/github/seecloud/spamostack?branch=master


Installation
------------

For installation just use ``pip install -e .``

+------------------+
| Working services |
+===========+======+
| Keystone  | Done |
+-----------+------+
| Nova      | WIP  |
+-----------+------+
| Glance    | WIP  |
+-----------+------+
| Neutron   | WIP  |
+-----------+------+
| Cinder    | WIP  |
+-----------+------+

Configuring spamostack
----------------------

Please, configure your settings by changing config file in etc/ folder.
File ``openrc`` needed for connecting to your cloud, and file ``conf.json`` needed for configuring pipelines


Configuring keystone
--------------------

Example:
``{"pipe1":{"keystone":{"projects":{"create": [60, 1, 1],"update": [60, 1, 1]},"users":{"create": [60, 2, 1],"update": [120, 2, 2]}}}}``
That means, that spamostack should:

  - Create 1 project in 60 seconds and do it once
  - Update 1 project in 60 seconds and do it once
  - Create 2 users in 60 seconds and do it once
  - Update 2 users in 120 seconds and do it twice

Using spamostack
----------------

1. Run ``source /etc/openrc``
2. Just run it with ``spamostack``. Config file with pipelines will be read from etc/ folder
