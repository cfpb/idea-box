# Idea-Box

Collecting and surfacing ideas from everyone.

![Idea Profile](https://raw.github.com/cfpb/idea-box/master/doc/images/profile.png)

## Requirements
* django (1.4.3) - This is a django app, so you need django.
* django-haystack (1.2.7) - A mapper between django models and search
backends.
* pysolr (3.0.3) - Library for communicating with solr.
* django-taggit - A library for Tags within django
* mock - A library for creating mock objects for testing. 
* south - A library for schema and data migrations. 

* solr (and java) - A Search backend. Unfortunately, we currently require
Solr (rather than another backend) because we need specific functionality
that haystack doesn't give us direct access to. Eventually, we'll get a
pull request to haystack which will reduce our solr requirement.

## Installation

### Settings File
Modify your settings file to add the following apps:
* django.contrib.comments
* haystack
* idea

You will also need to configure haystack. See the haystack
[documentation](http://django-haystack.readthedocs.org/en/v1.2.7/tutorial.html#configuration)

If you'd prefer to take the quick route, add the following to your
settings.py:
```python
HAYSTACK_SITECONF = 'search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://localhost:8983/solr'
```

If you are going that route, make sure that you have a search_sites.py
module in the root of your project with something like the following:

```python
import haystack
haystack.autodiscover()
```

### Folder Structure

You will need to get the contents of the ```src/idea``` directory into
your django project. The simplest way to do this might be a symbolic
link.

```
mydjango_project/
  |- idea/      (includes models.py, views.py, etc.)
  |- mydjango_project/ (settings.py, url.py, etc.)
  |- manage.py
  |- etc etc etc
```

### URLs

Add the idea.urls, haystack.urls, and comments.urls to you url.py. For 
example:

```python
if 'idea' in settings.INSTALLED_APPS and \
        'django.contrib.comments' in settings.INSTALLED_APPS and\
        'haystack' in settings.INSTALLED_APPS:
    urlpatterns.append(url(r'^haystack/', include('haystack.urls')))
    urlpatterns.append(url(r'^comments/',
        include('django.contrib.comments.urls')))
    urlpatterns.append(url(r'^idea/', include('idea.urls')))
```

### Solr

You will also need to modify your solr configs. Take a look at the
configuration files included in the root's ```solr``` directory. For a
complete (but poor) implementation,

```bash
$ wget http://mirror.reverse.net/pub/apache/lucene/solr/4.1.0/solr-4.1.0.tgz
$ tar -xvzf solr-4.1.0.tgz
$ cd solr-4.1.0/example/solr/collection1/conf/
$ cp ~/idea/solr/* .
$ cd ../../../
$ java -jar start.jar &
```

### Migrations

From your project root, synchronize and migrate the new apps.

```bash
$ python ./manage.py syncdb --noinput --migrate
```

### Templates

A basic set of templates has been provided. The 'base.html' template should
probably be overwritten into something less basic for a better user experience. 

If users in the system have a profile module specified our templates will use
this to link users to a profile page.  This is specified through the
AUTH_PROFILE_MODULE setting. Your profile module will also have to specify a
get_absolute_url() method.

### Buildout
To use buildout, run the following:
```bash
$ pip install zc.buildout distribute
$ buildout
```
Then, run the django binary in the ```bin``` directory.
