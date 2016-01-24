import os
import shutil
from subprocess import check_call

from charms.reactive import hook, when
from charmhelpers.fetch import archiveurl, apt_install, apt_update
from charmhelpers.payload.archive import extract_tarfile
from charmhelpers.core import hookenv

from nginxlib import configure_site


@hook('install')
def install():
    apt_update()
    apt_install(['php5-cli'])

    if not os.path.isdir('/srv/wallabag'):
        install_wallabag()

    # Install composer & Twig
    os.makedirs('/var/lib/composer', mode=0o755, exist_ok=True)
    env = {}
    env.update(os.environ)
    env['COMPOSER_HOME'] = '/var/lib/composer'

    with open(os.path.join(hookenv.charm_dir(), 'composer', 'installer'), "r") as f:
        check_call(['php'], stdin=f, env=env, cwd='/srv/wallabag')
    check_call(['php', 'composer.phar', 'install'], cwd='/srv/wallabag', env=env)


def install_wallabag():
    conf = hookenv.config()
    version = conf.get('version')
    handler = archiveurl.ArchiveUrlFetchHandler()
    handler.download('https://codeload.github.com/wallabag/wallabag/tar.gz/%s' % (version),
        dest='/srv/wallabag.tar.gz')
    extract_tarfile('/srv/wallabag.tar.gz', destpath="/srv")
    os.rename('/srv/wallabag-%s' % (version), '/srv/wallabag')


@when('nginx.available')
def configure_webapp():
    fix_permissions()
    write_vhost()


def fix_permissions():
    for root, dirs, files in os.walk('/srv/wallabag'):
        for name in dirs:
            shutil.chown(os.path.join(root, name), user="www-data", group="www-data")
        for name in files:
            shutil.chown(os.path.join(root, name), user="www-data", group="www-data")


@hook("config-changed")
def config_changed():
    conf = hookenv.config()
    if conf.changed('server_name'):
        write_vhost()


def write_vhost():
    conf = hookenv.config()
    configure_site('wallabag', 'vhost.conf',
        app_path='/srv/wallabag',
        server_name=conf['server_name'],
    )


@when('nginx.available', 'website.available')
def configure_website(website):
    website.configure(port=config['port'])
