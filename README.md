# Wallabag

- Author: The Wallabag Developers, see https://www.wallabag.org/
- Maintainer: Casey Marshall <juju@cmars.tech>

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

However, you really should protect your Wallabag server with TLS if you're
hosting on public networks. For this, use a reverse proxy that supports TLS
termination such as
[haproxy](https://jujucharms.com/q/haproxy) or
[apache2](https://jujucharms.com/q/apache2). In such a deployment, you may find
it more economical to place wallabag in an LXC container on the same machine.

## Configuration

`version:` The release version to download and install. Defaults to the latest
stable release at time of writing (1.9.1-b).

`server_name:` The public hostname of the web server.

# TODO

- Support for MySQL and PostgreSQL relations.
- Bundle deployment with reverse proxy and database.
- Amulet tests
- Scale-out testing.

