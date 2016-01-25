# Wallabag

- Author: The Wallabag Developers, see https://www.wallabag.org/
- Maintainer: Casey Marshall <casey.marshall@canonical.com>

# Overview

wallabag is a self hostable application for saving web pages. Unlike other
services, wallabag is free (as in freedom) and open source.

With this application you will not miss content anymore. Click, save, read it
when you want. It saves the content you select so that you can read it when you
have time.

(Source: https://www.wallabag.org/)

This Juju charm installs nginx and all the necessary PHP dependencies required
by the [Wallabag installation](http://doc.wallabag.org/en/Administrator/download_and_install.html).

# Deployment

Once the charm has installed, you may point a browser to the public IP address
of the deployed service and complete installation. Then your wallabag will be
ready to use.

## TLS termination

You really should protect your Wallabag server with TLS if you're hosting it on
public networks. For this, use a reverse proxy that supports TLS termination
such as [haproxy](https://jujucharms.com/q/haproxy) or
[apache2](https://jujucharms.com/q/apache2). In such a deployment, you may find
it more economical to place wallabag in an LXC container on the same machine.

For example:

```
juju deploy wallabag
juju deploy --config my-tls-conf.yaml haproxy
juju add-relation haproxy:reverseproxy wallabag
```

## Databases

By default, wallabag uses a local sqlite database. Use a MySQL database for
better performance and scale-out:

```
juju deploy wallabag
juju deploy mysql
juju add-relation wallabag mysql
```

## Config options

`server_name:` The public hostname of the web server.

`version:` The release version to download and install. Defaults to the latest
stable release at time of writing (1.9.1-b). This is used to download a release
tarball from Github.

`username:` and `password:` determine the login for the default wallabag
account.

# TODO

- Support for PostgreSQL.
- Amulet tests.

