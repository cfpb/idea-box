# Idea-Box

[![Build Status](https://travis-ci.org/cfpb/idea-box.svg?branch=master)](https://travis-ci.org/cfpb/idea-box)

Idea-Box is a django app for collecting and surfacing ideas from users, in the vein of
IdeaScale, IdeaX, and Django Voice. Idea-Box differs from these projects in its minimal,
easily integrate-able interface. Idea-Box also takes a strong stance on transparency,
such that ideas, votes, etc. are tied to specific users.

## Features
* Idea Submission
* Tagging (via taggit)
* Voting
* Comments
* Listing by trending, likes, and recently added
* Archive/hide ideas
* Customizable challenges for specific campaigns

## Screen shot

![Idea Profile](https://raw.github.com/cfpb/idea-box/master/doc/images/profile.png)

## Requirements
* django (1.5.4) - This is a django app, so you need django.
* django-taggit - A library for Tags within django
* mock - A library for creating mock objects for testing. 
* south - A library for schema and data migrations.
* django-mptt - A library enabling nested/reply-to comments

### Optional
* [collab platform](http://github.com/cfpb/collab) - Installing idea-box as an app inside a collab platform provides several convenience features:
  * Autocomplete when adding new tags (requires elasticsearch server)
  * User can delete tags he/she created
  * Email notifications


## Installation

* Use pip to install the dependencies listed above
* If not using collab as the Django platform, you still need to install collab for `custom_comments`

```
pip install git+https://github.com/cfpb/collab.git#egg=collab
```

### Settings File
Modify your settings file to add the following to your `INSTALLED_APPS`:
```
'django.contrib.comments',
'taggit',
'south',
'mptt',
'core.custom_comments',
'idea'
```

If using a newer version of django-taggit, add the following to your settings file:
```
SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
}
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

Add the idea.urls and comments.urls to you url.py. For 
example:

```python
from mydjango_project import settings

if 'idea' in settings.INSTALLED_APPS and \
        'django.contrib.comments' in settings.INSTALLED_APPS:
    urlpatterns.append(url(r'^comments/',
        include('django.contrib.comments.urls')))
    urlpatterns.append(url(r'^idea/', include('idea.urls', namespace='idea')))
```


### Migrations

From your project root, synchronize and migrate the new apps.  Make sure to set your database settings.

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

### CSS

The default CSS style for Idea-Box is not ready for production.  This was done
intentionally so that Idea-Box's style can match the style of the platform in
which it resides (i.e. not everyone wants a green header).  The simplest way to
improve the styling is to source `src/idea/static/idea/css/sample_style.css`
in the `css_files` block in the `/src/idea/templates/idea/idea-base.html` template:

```
{% block "css_files" %}
    # ... existing code ...
    <link rel="stylesheet" href="{{ STATIC_URL }}idea/css/sample_style.css">
{% endblock %}
```

Ideally, your Django platform will provide styles that can be sourced in the
`base.html` template described in the section above so Idea-Box can match the
look and feel of your system.


### Buildout
An alternative way to install the software is to use the buildout configuration.
To use buildout to create a working project, run the following:
```bash
$ pip install zc.buildout distribute
$ buildout
```
Then, run the django binary in the ```bin``` directory.

### Campaign Banner

To create a challenge, use django's administrative page to add a Banner model object. The
text field will be displayed at the right of the Idea-Box idea listing page. The banner
will only be displayed between Start Date and End Date (or indefinitely after the Start
Date if the End Date is empty.)
