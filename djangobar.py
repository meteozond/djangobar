from collections import Counter
from json import loads
import re
from furl import furl
from requests import get
from csv import reader
# https://code.djangoproject.com/query?&version=&format=csv&col=status

class TrackerUrl(object):
    URL_SCHEMA = 'https'
    URL_HOST = 'code.djangoproject.com'
    URL_PATH = 'query'

    def get_furl(self):
        f = furl()
        f.scheme = self.URL_SCHEMA
        f.host = self.URL_HOST
        f.path = self.URL_PATH
        return f


class Version(TrackerUrl):
    CLASSES = dict(
        new='progress-bar-danger',
        assigned='progress-bar-warning progress-striped active',
        closed='progress-bar-success',
    )
    WEIGHTS = dict(
        new=2,
        assigned=1,
        closed=0
    )

    def __init__(self, version):
        self.version = version

    def get_furl(self):
        f = super(Version, self).get_furl()
        f.args['version'] = self.version
        return f

    @property
    def url(self):
        f = self.get_furl()
        f.args['col'] = 'status'
        f.args['format'] = 'csv'
        return f.url

    @property
    def stats(self):
        csv = reader(get(self.url).content.split("\n"))
        csv.next()
        tasks = Counter([row[1] for row in csv if row])
        return tasks

    def get_status_url(self, status):
        f = self.get_furl()
        f.args['status'] = status
        return f.url

    def html(self):
        stats = self.stats
        total = sum(stats.values())
        resp = '<div class="row">' \
                   '<div class="col col-md-3 text-center">' \
                   '<h3><a href="%s">%s</a></h3>' \
                   '</div>' \
               '<div class="col col-md-9"><div class="progress" style="margin-top:25px">' % (self.get_furl().url, self.version)
        left = 100
        for status, count in sorted(self.stats.items(), key=lambda i: self.WEIGHTS.get(i[0])):
            progress = int(round(float(count) * 100 / total, 0))
            template = '%(count)s %(status)s %(progress)s%%' if progress > 20 else '<div class="sr-only">%(count)s</div> <div class="sr-only">%(status)s</div> %(progress)s%%'
            label = template % dict(status=status, progress=progress, count=count)
            resp += (
                '<div class="progress-bar %(cls)s" style="width: %(progress)s%%">'
                    '<a href="%(url)s" style="color:white">%(label)s</a>'
                '</div>'
            ) % dict(cls=self.CLASSES[status], label=label, progress=left if status == 'new' else progress, url=self.get_status_url(status))
            left -= progress
        resp += '</div></div></div>'
        return resp


class Page(TrackerUrl):

    @property
    def versions(self):
        f = self.get_furl()
        f.args['status'] = 0
        return loads(re.findall('"label":"Version","options":(\[[^\]]+\])', get(f.url).content)[0])

    def html(self):
        resp = ('<!DOCTYPE html>'
                '<html>'
                    '<head>'
                        '<title>Django development progress</title>'
                        '<link rel="stylesheet" href="http://netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">'
                    '</head>'
                    '<body>'
                    '<div class="page-header text-center">'
                        # '<div class="navbar-header">'
                            '<h1>Django development progress</h1>'
                        # '</div>'
                    '</div>'
                    '<div class="container">'
        )

        for version in self.versions[1:2]:
            resp += Version(version).html()

        resp += ("<div>Generated by: <a href='https://github.com/meteozond/djangobar'>DjangoBar</a></div>"
                 "</div>"
                 "</body>"
                 "</html>")
        return resp

print Page().html()
# print Version('1.7-alpha-2').stats
