# -*- coding: utf-8 -*-
import sys
import json
import os
from fabric.api import cd, env, run, task, require, sudo, local
from fabric.colors import green, red, white, yellow, blue
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.operations import get
from fabric import state
from fabutils import boolean

from fabutils.env import set_env_from_json_file
from fabutils.tasks import ursync_project, ulocal, urun


@task
def environment(env_name, debug=False):
    """
    Creates the configurations for the environment in which tasks will run.
    """
    schemas_dir = "chuy/json_schemas/"
    state.output['running'] = boolean(debug)
    state.output['stdout'] = boolean(debug)
    print "Establishing environment " + blue(env_name, bold=True) + "..."
    try:
        set_env_from_json_file(
            'environments.json',
            env_name,
            schemas_dir + "environment_schema.json"
        )
        env.is_vagrant = False
        if env_name == "vagrant":
            result = ulocal('vagrant ssh-config | grep IdentityFile',
                            capture=True)
            env.key_filename = result.split()[1].replace('"', '')
            env.is_vagrant = True

    except ValueError:
        print red("environments.json has wrong format.", bold=True)
        sys.exit(1)

    try:
        set_env_from_json_file(
            'settings.json',
            schema_path=schemas_dir + "settings_schema.json"
        )

    except ValueError:

        print red("settings.json has wrong format.", bold=True)
        sys.exit(1)


@task
def bootstrap():
    """
    Creates the database, test information and enables rewrite.
    """
    require('dbname', 'dbuser', 'dbpassword', 'dbhost')
    print "Creating local environment."
    # Creates database
    run("""
        echo "DROP DATABASE IF EXISTS {dbname}; CREATE DATABASE {dbname};
        "|mysql --batch --user={dbuser} --password=\"{dbpassword}\" --host={dbhost}
        """.format(**env))
    # Enables apache module
    run('sudo a2enmod rewrite')

    framework = ""
    while framework == "":
        print blue("Select project:")
        option  = raw_input( blue("0) Default\n1) CakePHP\n2) Symfony\n3) Laravel\n4) Drupal\n5) Prestashop\n>>") )

        if option == "0":
            framework = "default"
            _set_vhost(framework)

        if option == "1":
            framework = "cakephp"
            _set_vhost(framework)
            #Install new proyect
            option  = raw_input( blue("Install new project(Y/n)[default:n]:") )
            if option == "y" or option == "Y":
                _cakephp_install()

        if option == "2":
            framework = "symfony"
            _set_vhost(framework)
            #Install new proyect
            option  = raw_input( blue("Install new project(Y/n)[default:n]:") )
            if option == "y" or option == "Y":
                _symfony_install()

        if option == "3":
            framework = "laravel"
            _set_vhost(framework)
            #Install new proyect
            option  = raw_input( blue("Install new project(Y/n)[default:n]:") )
            if option == "y" or option == "Y":
                _laravel_install()
        if option == "4":
            framework = "drupal"
            _set_vhost(framework)
            #Install new proyect
            option  = raw_input( blue("Install new project(Y/n)[default:n]:") )
            if option == "y" or option == "Y":
                _drupal_install()
        if option == "5":
            framework = "prestashop"
            _set_vhost(framework)
            #Install new proyect
            option  = raw_input( blue("Install new project(Y/n)[default:n]:") )
            if option == "y" or option == "Y":
                _prestashop_install()


def _cakephp_install():
    """
    Downloads the cakephp/app (Skeleton) version specified in settings.json and installs the database.
    """
    require('cpchuy_dir', 'public_dir', 'dbname', 'dbuser', 'dbpassword', 'version')

    print "Delete project..."
    run('rm -rf {public_dir}*'.format(**env))
    run('find {public_dir} -name ".*" -delete'.format(**env))
    #Downloads Skeleton
    print "Downloading cakephp application skeleton..."
    state.output['stdout'] = True
    run('composer create-project --prefer-dist cakephp/app public_www "{version}"'.format(**env))

    run("sed -i \"218s/'username' => '.*'/'username' => '{dbuser}'/g\" {public_dir}config/app.php".format(**env))
    run("sed -i \"219s/'password' => '.*'/'password' => '{dbpassword}'/g\" {public_dir}config/app.php".format(**env))
    run("sed -i \"220s/'database' => '.*'/'database' => '{dbname}'/g\" {public_dir}config/app.php".format(**env))

    run("mkdir {public_dir}database".format(**env))


def _symfony_install():
    """
    Downloads the Symfony version specified in settings.json and installs the database.
    """
    require('cpchuy_dir', 'public_dir', 'dbname', 'dbuser', 'dbpassword', 'version')

    print "Delete project..."
    run('rm -rf {public_dir}*'.format(**env))
    run('find {public_dir} -name ".*" -delete'.format(**env))
    #Downloads Symfony
    state.output['stdout'] = True
    print "Downloading Symfony..."
    run('composer create-project symfony/framework-standard-edition public_www "{version}"'.format(**env))

    run("mkdir {public_dir}database".format(**env))


def _laravel_install():
    """
    Downloads the Laravel version specified in settings.json and installs the database.
    """
    require('cpchuy_dir', 'public_dir', 'dbname', 'dbuser', 'dbpassword', 'version')

    print "Delete project..."
    run('rm -rf {public_dir}*'.format(**env))
    run('find {public_dir} -name ".*" -delete'.format(**env))
    #Downloads Laravel
    state.output['stdout'] = True
    print "Downloading Laravel..."
    run('composer create-project --prefer-dist laravel/laravel public_www'.format(**env))

    run("mkdir {public_dir}database".format(**env))


def _drupal_install():
    """
    Downloads the Drupal version specified in settings.json and installs the database.
    """
    require('cpchuy_dir', 'public_dir', 'dbname', 'dbuser', 'dbpassword', 'version')

    print "Delete project..."
    run('rm -rf {public_dir}*'.format(**env))
    run('find {public_dir} -name ".*" -delete'.format(**env))
    #Downloads Drupal
    print "Downloading Drupal..."
    with cd(env.public_dir):
        urun('wget https://github.com/drupal/drupal/archive/{version}.tar.gz'.format(**env))
        urun('tar -xzvf {version}.tar.gz'.format(**env))
        urun('mv drupal-{version}/* .'.format(**env))
        urun('rm -rf drupal-{version}'.format(**env))

    run("mkdir {public_dir}database".format(**env))


def _prestashop_install():
    """
    Downloads the Prestashop version specified in settings.json and installs the database.
    """
    require('cpchuy_dir', 'public_dir', 'dbname', 'dbuser', 'dbpassword', 'version')

    print "Delete project..."
    run('rm -rf {public_dir}*'.format(**env))
    run('find {public_dir} -name ".*" -delete'.format(**env))
    #Downloads PrestaShop
    print "Downloading PrestaShop..."
    with cd(env.public_dir):
        urun('wget https://github.com/PrestaShop/PrestaShop/archive/{version}.tar.gz'.format(**env))
        urun('tar -xzvf {version}.tar.gz'.format(**env))
        urun('mv PrestaShop-{version}/* .'.format(**env))
        urun('rm -rf PrestaShop-{version}'.format(**env))

    run("mkdir {public_dir}database".format(**env))


def _set_vhost(template="cakephp"):
    """
    Downloads the cakephp version specified in settings.json and installs the database.
    """
    print "Update template..."

    env.template = template
    run("sudo cp /home/vagrant/templates/{template}.nginx /etc/nginx/sites-available/chuy".format(**env))
    run("sudo service nginx restart")


@task
def nodejs_install():
    """
    Install node, grount, bower
    """
    require('public_dir')

    print "Install cakephp vendor version..."
    run('sudo apt-get install software-properties-common')
    run('sudo apt-get install python-software-properties')
    run('sudo apt-add-repository ppa:chris-lea/node.js')
    run('sudo apt-get update')

    run('sudo apt-get install -y nodejs')

    run('sudo npm install -g bower')

    run('sudo npm -g install grunt')
    run('sudo npm install -g grunt-cli')
    run('sudo chown -R vagrant:vagrant /usr/lib/node_modules')
    run('sudo chown -R vagrant:vagrant /home/vagrant/.npm')

    run('sudo gem install compass')
    run('sudo gem install sass')


@task
def import_data(file_name="data.sql"):
    """
    Imports the database to given file name. database/data.sql by default.
    """
    require('dbuser', 'dbpassword', 'dbhost')

    env.file_name = file_name

    print "Importing data from file: " + blue(file_name, bold=True) + "..."
    run("""
        mysql -u {dbuser} -p\"{dbpassword}\" {dbname} --host={dbhost} <\
        {public_dir}database/{file_name} """.format(**env))


@task
def export_data(file_name="data.sql", just_data=False):
    """
    Exports the database to given file name. database/data.sql by default.
    """
    require('public_dir', 'dbuser', 'dbpassword', 'dbname', 'dbhost')

    export = True

    env.file_name = file_name
    if just_data:
        env.just_data = "--no-create-info"
    else:
        env.just_data = " "

    if exists('{public_dir}database/{file_name}'.format(**env)):
        export = confirm(
            yellow(
                '{public_dir}database/{file_name} '.format(**env)
                +
                'already exists, Do you want to overwrite it?'
            )
        )

    if export:
        print "Exporting data to file: " + blue(file_name, bold=True) + "..."
        run(
            """
            mysqldump -u {dbuser} -p\"{dbpassword}\" {dbname} --host={dbhost}\
            {just_data} > {public_dir}database/{file_name}
            """.format(**env)
        )
    else:
        print 'Export canceled by user'
        sys.exit(0)


@task
def resetdb():
    """
    Drops the database and recreate it.
    """
    require('dbname', 'dbuser', 'dbpassword', 'dbhost')
    print "Dropping database..."
    run("""
        echo "DROP DATABASE IF EXISTS {dbname};
        CREATE DATABASE {dbname};
        "|mysql --batch --user={dbuser} --password=\"{dbpassword}\" --host={dbhost}
        """.format(**env))


@task
def reset_all():
    """
    Deletes all the cakephp installation and starts over.
    """
    require('public_dir')
    print "Deleting directory content: " + blue(env.public_dir, bold=True) + "..."
    run('rm -rf {public_dir}*'.format(**env))
    run('find {public_dir} -name ".*" -delete'.format(**env))
    resetdb()


@task
def sync_files(delete=False):
    """
    Sync modified files and establish necessary permissions in selected environment.
    """
    require('group', 'public_dir', 'src', 'exclude')

    print white("Uploading code to server...", bold=True)
    ursync_project(
        local_dir='./{src}/'.format(**env),
        remote_dir=env.public_dir,
        exclude=env.exclude,
        delete=delete,
        default_opts='-chrtvzP'
    )
    print white("Estableciendo permisos...", bold=True)
    run('chgrp -R {0} {1}'.format(env.group, env.public_dir))

    print green(u'Successfully sync.')


@task
def set_webserver(webserver="nginx"):
    """
    Changes project's web server, nginx or apache2 available, nginx by default.
    """
    require('public_dir')

    if webserver == "apache2":
        sudo("service nginx stop")
        sudo("a2enmod rewrite")
        sudo("service apache2 start", pty=False)

    else:
        sudo("service apache2 stop")
        sudo("service nginx start")

    print "Web server switched to " + blue(webserver, bold=True) + "."


@task
def backup(tarball_name='backup', just_data=False):
    """
    Generates a backup copy of database
    """
    require('public_dir')

    env.tarball_name = tarball_name

    export_data(tarball_name + '.sql', just_data)

    print 'Preparing backup directory...'

    if not os.path.exists('./backup/'):
        os.makedirs('./backup/')

    if exists('{public_dir}backup/'):
        run('rm -rf {public_dir}backup/')

    if not exists('{public_dir}backup/'.format(**env)):
        run('mkdir {public_dir}backup/'.format(**env))

    if not exists('{public_dir}backup/database/'.format(**env)):
        run('mkdir {public_dir}backup/database/'.format(**env))

    run(
        'mv {public_dir}/database/{tarball_name}.sql '.format(**env)
        +
        '{public_dir}/backup/database/'.format(**env)
    )

    print 'Creating tarball...'
    with cd(env.public_dir):
        urun('tar -czf {tarball_name}.tar.gz backup/*'.format(**env))

    print 'Downloading backup...'
    download = True
    if os.path.exists('./backup/{tarball_name}.tar.gz'.format(**env)):
        download = confirm(
            yellow(
                './backup/{tarball_name}.tar.gz'.format(**env)
                +
                ' already exists, Do you want to overwrite it?'
            )
        )

    if download:
        get(
            '{public_dir}{tarball_name}.tar.gz'.format(**env),
            './backup/{tarball_name}.tar.gz'.format(**env)
        )
    else:
        print red('Backup canceled by user')

    print 'Cleaning working directory...'
    run('rm -rf {public_dir}backup/'.format(**env))
    run('rm {public_dir}{tarball_name}.tar.gz'.format(**env))

    if download:
        print green(
            'Backup succesfully created at'
            +
            ' ./backup/{tarball_name}.tar.gz'.  format(**env)
        )


@task
def execute(command=""):
    env.command = command
    state.output['stdout'] = True
    with cd('{public_dir}'.format(**env)):
        run('{command}'.format(**env))


@task
def php_version():
    select = True
    while select:
        print blue("Select version:")
        option  = raw_input( blue("0) PHP 5.4\n1) PHP 5.5\n2) PHP 5.6\n>>") )

        if option == "0":
            select = False
            print "Installing php 5.4..."
            state.output['stdout'] = True
            run('sudo apt-get remove -y libapache2-mod-php5')
            run('sudo add-apt-repository ppa:ondrej/php5-oldstable')
        if option == "1":
            select = False
            print "Installing php 5.5..."
            state.output['stdout'] = True
            run('sudo apt-get remove -y libapache2-mod-php5')
            run('sudo add-apt-repository ppa:ondrej/php5')
        if option == "2":
            select = False
            print "Installing php 5.6..."
            state.output['stdout'] = True
            run('sudo apt-get remove -y libapache2-mod-php5')
            run('sudo add-apt-repository ppa:ondrej/php5-5.6')

    run('sudo apt-get update')
    run('sudo apt-get install php5')
    run('sudo apt-get install libapache2-mod-php5')
