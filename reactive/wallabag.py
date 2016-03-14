import os
import re
import shutil
from subprocess import check_call, Popen, PIPE

from charms.reactive import hook, when, when_not, set_state, remove_state, is_state
from charmhelpers.fetch import archiveurl, apt_install, apt_update
from charmhelpers.payload.archive import extract_tarfile
from charmhelpers.core import hookenv
from charmhelpers.core.templating import render
from charmhelpers.core.unitdata import kv

import requests

from nginxlib import configure_site

APP_PATH    = '/srv/wallabag'
VERSION     = '1.9.1-b'

@hook('install')
def install():
    apt_update()

    if not os.path.isdir(APP_PATH):
        install_wallabag()

    # Install composer & Twig
    os.makedirs('/var/lib/composer', mode=0o755, exist_ok=True)
    env = {}
    env.update(os.environ)
    env['COMPOSER_HOME'] = '/var/lib/composer'

    hookenv.status_set('maintenance', 'installing composer and twig')
    with open(os.path.join(hookenv.charm_dir(), 'composer', 'installer'), "r") as f:
        check_call(['php'], stdin=f, env=env, cwd=APP_PATH)
    check_call(['php', 'composer.phar', 'install'], cwd=APP_PATH, env=env)


def install_wallabag():
    conf = hookenv.config()
    handler = archiveurl.ArchiveUrlFetchHandler()
    hookenv.status_set('maintenance', 'downloading wallabag %s' % (VERSION))

    # Only 1.9.1-b has been tested with, and so, supported by this charm
    handler.download('https://codeload.github.com/wallabag/wallabag/tar.gz/%s' % (VERSION),
        dest='/srv/wallabag.tar.gz')

    hookenv.status_set('maintenance', 'unpacking wallabag archive')
    extract_tarfile('/srv/wallabag.tar.gz', destpath="/srv")
    os.rename('/srv/wallabag-%s' % (VERSION), APP_PATH)


def reset_wallabag():
    config_path = '/srv/wallabag/inc/poche/config.inc.php'
    if os.path.exists(config_path):
        os.unlink(config_path)
    conf = hookenv.config()
    check_call(['tar', '--strip-components=1', '-xzvf', '/srv/wallabag.tar.gz', 'wallabag-%s/install' % (VERSION)],
        cwd=APP_PATH)


@when('nginx.available')
@when_not('wallabag.installed')
def configure_webapp():
    fix_permissions()
    write_vhost()
    hookenv.status_set('maintenance', 'wallabag installation complete')
    set_state('wallabag.installed')


def fix_permissions():
    hookenv.status_set('maintenance', 'fixing wallabag permissions')
    shutil.chown(APP_PATH, user="www-data", group="www-data")
    for root, dirs, files in os.walk(APP_PATH):
        for name in dirs:
            shutil.chown(os.path.join(root, name), user="www-data", group="www-data")
        for name in files:
            shutil.chown(os.path.join(root, name), user="www-data", group="www-data")


@hook("config-changed")
def config_changed():
    conf = hookenv.config()
    if conf.changed('server_name'):
        write_vhost()
    set_state('wallabag.configured')
    set_state('wallabag.available')


def write_vhost():
    conf = hookenv.config()
    configure_site('wallabag', 'vhost.conf',
        app_path=APP_PATH,
        server_name=conf['server_name'],
    )


@when('nginx.available', 'website.available')
def configure_website(website):
    conf = hookenv.config()
    website.configure(port=conf['port'])


@when('wallabag.available')
@when_not('mysql.connected')
def setup_sqlite_via_config():
    conf = hookenv.config()
    if conf.changed('username') or conf.changed('password'):
        setup_sqlite()
    elif not is_state('wallabag.connected.sqlite'):
        setup_sqlite()
    else:
        remove_state('wallabag.available')
    hookenv.status_set('active', 'ready - sqlite database')


def setup_sqlite():
    reset_wallabag()
    setup('sqlite', None)
    set_state('wallabag.connected.sqlite')


@when('wallabag.configured', 'wallabag.connected.mysql')
@when_not('mysql.connected')
def disconnect_mysql():
    remove_state('wallabag.connected.mysql')
    setup_sqlite()


@when('wallabag.available', 'mysql.connected')
def setup_mysql_via_config(db):
    conf = hookenv.config()
    if conf.changed('username') or conf.changed('password'):
        setup_mysql(db)
    else:
        hookenv.status_set('active', 'ready - mysql database')


@when('wallabag.configured', 'mysql.available')
def setup_mysql_via_relation(db):
    setup_mysql(db)


def setup_mysql(db):
    apt_install(['php5-mysql', 'mysql-client'])
    reset_wallabag()
    setup('mysql', db)
    remove_state('mysql.available')
    remove_state('wallabag.connected.sqlite')
    set_state('wallabag.connected.mysql')


def setup(db_engine, db):
    unit_data = kv()

    conf = hookenv.config()
    payload = {
        'db_engine':      db_engine,
        'username':       conf['username'],
        'password':       conf['password'],
        'email':          '',
        'install':        'install',
    }
    if db and db_engine == 'mysql':
        payload.update({
            'mysql_server':   db.host(),
            'mysql_database': db.database(),
            'mysql_user':     db.user(),
            'mysql_password': db.password(),
        })
    r = requests.post('http://localhost', data=payload)

    salt_key = '%s-salt' % (db_engine)
    salt = unit_data.get(salt_key, None)
    if salt is None:
        salt = read_salt()
        unit_data.set(salt_key, salt)
 
    install_path = os.path.join(APP_PATH, 'install')
    if os.path.isdir(install_path):
        shutil.rmtree(install_path)

    # Go ahead and write the config PHP out. In some cases, the above POST
    # errors out before this is done properly, especially in the case where a
    # relation to a prior wallabag database is restored.
    render(source='config.inc.php',
        target=os.path.join(APP_PATH, 'inc', 'poche', 'config.inc.php'),
        owner='www-data',
        group='www-data',
        perms=0o644,
        context={
            'conf': conf,
            'db': db,
            'db_engine': db_engine,
            'salt': salt,
        })

    hookenv.status_set('active', 'ready - %s database' % (db_engine))
    remove_state('wallabag.available')


def read_salt():
    with open(os.path.join(APP_PATH, 'inc', 'poche', 'config.inc.php'), 'r', encoding='utf-8') as f:
        for l in f.readlines():
            if "'SALT'" in l:
                m = re.match(r"@define \('SALT', '(?P<salt>[^']+)'\);", l)
                return m.group('salt')
    return None
