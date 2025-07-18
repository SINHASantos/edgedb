.. _ref_guide_deployment_bare_metal:

==========
Bare Metal
==========

:edb-alt-title: Deploying Gel to a Bare Metal Server

In this guide we show how to deploy Gel to bare metal using your system's
package manager and systemd.

.. include:: ./note_cloud.rst


Install the Gel Package
=======================

The steps for installing the Gel package will be slightly different
depending on your Linux distribution. Once you have the package installed you
can jump to :ref:`ref_guide_deployment_bare_metal_enable_unit`.


Debian/Ubuntu LTS
-----------------
Import the Gel packaging key.

.. code-block:: bash

   $ sudo mkdir -p /usr/local/share/keyrings && \
       sudo curl --proto '=https' --tlsv1.2 -sSf \
       -o /usr/local/share/keyrings/gel-keyring.gpg \
       https://packages.geldata.com/keys/gel-keyring.gpg

Add the Gel package repository.

.. code-block:: bash

   $ echo deb '[signed-by=/usr/local/share/keyrings/gel-keyring.gpg]' \
       https://packages.geldata.com/apt \
       $(grep "VERSION_CODENAME=" /etc/os-release | cut -d= -f2) main \
       | sudo tee /etc/apt/sources.list.d/gel.list

.. note::

   For non-LTS releases of Debian/Ubuntu (e.g. Ubuntu Oracular), one can install
   package for latest LTS release, because they are usually forward compatible.
   To do this, replace the ``$(grep ...)`` with the name of latest LTS release
   (e.g. ``noble``).

Install the Gel package.

.. code-block:: bash

   $ sudo apt-get update && sudo apt-get install gel-6


CentOS/RHEL 7/8
---------------
Add the Gel package repository.

.. code-block:: bash

   $ sudo curl --proto '=https' --tlsv1.2 -sSfL \
      https://packages.geldata.com/rpm/gel-rhel.repo \
      > /etc/yum.repos.d/gel.repo

Install the Gel package.

.. code-block:: bash

   $ sudo yum install gel-6

Disable SELinux.

.. code-block:: bash

   $ sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config
   $ reboot


.. _ref_guide_deployment_bare_metal_enable_unit:

Enable a systemd unit
=====================

The Gel package comes bundled with a systemd unit that is disabled by
default. You can start the server by enabling the unit.

.. code-block:: bash

   $ sudo systemctl enable --now gel-server-6

This will start the server on port 5656, and the data directory will be
``/var/lib/gel/6/data``.

.. warning::

    |gel-server| cannot be run as root.

Set environment variables
=========================

To set environment variables when running Gel with ``systemctl``,

.. code-block:: bash

   $ systemctl edit --full gel-server-6

This opens a ``systemd`` unit file. Set the desired environment variables
under the ``[Service]`` section. View the supported environment variables at
:ref:`Reference > Environment Variables <ref_reference_environment>`.

.. code-block:: toml

   [Service]
   Environment="GEL_SERVER_TLS_CERT_MODE=generate_self_signed"
   Environment="GEL_SERVER_ADMIN_UI=enabled"

Save the file and exit, then restart the service.

.. code-block:: bash

   $ systemctl restart gel-server-6


Set a password
==============
There is no default password. To set one, you will first need to get the Unix
socket directory. You can find this by looking at your system.d unit file.

.. code-block:: bash

    $ sudo systemctl cat gel-server-6

Set a password by connecting from localhost.

.. code-block:: bash

   $ echo -n "> " && read -s PASSWORD
   $ RUNSTATE_DIR=$(systemctl show gel-server-6 -P ExecStart | \
      grep -o -m 1 -- "--runstate-dir=[^ ]\+" | \
      awk -F "=" '{print $2}')
   $ sudo gel --port 5656 --tls-security insecure --admin \
      --unix-path $RUNSTATE_DIR \
      query "ALTER ROLE admin SET password := '$PASSWORD'"

The server listens on localhost by default. Changing this looks like this.

.. code-block:: bash

   $ gel --port 5656 --tls-security insecure --password query \
      "CONFIGURE INSTANCE SET listen_addresses := {'0.0.0.0'};"

The listen port can be changed from the default ``5656`` if your deployment
scenario requires a different value.

.. code-block:: bash

   $ gel --port 5656 --tls-security insecure --password query \
      "CONFIGURE INSTANCE SET listen_port := 1234;"

You may need to restart the server after changing the listen port or addresses.

.. code-block:: bash

   $ sudo systemctl restart gel-server-6


Link the instance with the CLI
==============================

The following is an example of linking a bare metal instance that is running on
``localhost``. This command assigns a name to the instance, to make it more
convenient to refer to when running CLI commands.

.. code-block:: bash

   $ gel instance link \
      --host localhost \
      --port 5656 \
      --user admin \
      --branch main \
      --trust-tls-cert \
      bare_metal_instance

This allows connecting to the instance with its name.

.. code-block:: bash

   $ gel -I bare_metal_instance


Upgrading Gel
=============

.. note::

   The command groups :gelcmd:`instance` and :gelcmd:`project` are not
   intended to manage production instances.

When you want to upgrade to the newest point release upgrade the package and
restart the ``gel-server-6`` unit.


Debian/Ubuntu LTS
-----------------

.. code-block:: bash

   $ sudo apt-get update && sudo apt-get install --only-upgrade gel-6
   $ sudo systemctl restart gel-server-6


CentOS/RHEL 7/8
---------------

.. code-block:: bash

   $ sudo yum update gel-6
   $ sudo systemctl restart gel-server-6

Health Checks
=============

Using an HTTP client, you can perform health checks to monitor the status of
your Gel instance. Learn how to use them with our :ref:`health checks guide
<ref_guide_deployment_health_checks>`.
