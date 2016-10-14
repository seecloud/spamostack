spamostack
==========

.. image:: https://travis-ci.org/seecloud/spamostack.svg?branch=master
    :target: https://travis-ci.org/seecloud/spamostack
.. image:: https://coveralls.io/repos/github/seecloud/spamostack/badge.svg?branch=master
    :target: https://coveralls.io/github/seecloud/spamostack?branch=master

Installation
------------

For installation just type it in the project folder ``pip install -e .``

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

Please, configure your settings by changing config file in the ``/etc/spamostack`` folder.
File ``openrc`` is needed for connecting to your cloud, and ``conf.json`` file is needed for configuring pipelines.


Configuring keystone
--------------------

Example:

.. code-block:: javascript

   {"pipe1":
     {"keystone":
       {
         "projects":
         {
          "create": [60, 1, 1],
          "update": [60, 1, 1]
         },
         "users":
         {
          "create": [60, 2, 1],
          "update": [120, 2, 2],
          "delete": [30, 1, 1]
         }
       }
     }
   }

That means, that spamostack will:

- Create 1 project in 60 seconds and do it once
- Update 1 project in 60 seconds and do it once
- Create 2 users in 60 seconds and do it once
- Update 2 users in 120 seconds and do it twice
- Delete 1 user in 30 seconds and do it once

Using spamostack
----------------

1. Run ``source /etc/spamostack/openrc``
2. Just run it with ``spamostack``. Config file with pipelines will be read from the ``/etc/spamostack/conf.json`` file.

Alternatively you could pass some arguments in the ``argparse`` form:

``spamostack --conf path/to/pipeline/file --db path/to/database``

And for cleaning that mess use ``spamostack --clean component_name`` for ex: ``spamostack --clean keystone``.