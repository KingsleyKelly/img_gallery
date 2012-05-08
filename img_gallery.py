import cgi
import datetime
import urllib
import webapp2
import jinja2
import os
import wsgiref.handlers

jinja_enviroment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from google.appengine.api import oauth
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


class Picture(db.Model):
    """Models a Gallery with an author, content, and date."""
    author = db.UserProperty()
    content = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class Image(webapp.RequestHandler):
    def get(self):
        picture = db.get(self.request.get("img_id"))
        if picture.content:
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(picture.content)
        else:
            self.response.out.write("No image")

def gallery_key(gallery_name=None):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return db.Key.from_path('Gallery', gallery_name or 'default_gallery')


class MainPage(webapp2.RequestHandler):
    def get(self):
        gallery_name=self.request.get('gallery_name')
        pictures_query = Picture.all().ancestor(
            gallery_key(gallery_name)).order('-date')
        pictures = pictures_query.fetch(10)
        user = oauth.get_current_user()
        if user:
            greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                        (user.nickname(), users.create_logout_url("/")))
        else:
            
            greeting = ("<a href=\"%s\">Sign in or register</a>." %
                        users.create_login_url("/"))

        self.response.out.write("%s" % greeting)

        template_values = {
            'pictures': pictures,
            'user': user,
            
        }

        template = jinja_enviroment.get_template('img_gallery.html')
        self.response.out.write(template.render(template_values))



class Gallery(webapp2.RequestHandler):
    def post(self):
        
        gallery_name = self.request.get('gallery_name')
        picture = Picture(parent=gallery_key(gallery_name))

        if users.get_current_user():
          picture.author = users.get_current_user()

        
        content = images.resize(self.request.get("img"), 300, 300)
        picture.content = db.Blob(content)
        picture.put()
        self.redirect('/?' + urllib.urlencode({'gallery_name': gallery_name}))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/img', Image),
                               ('/sign', Gallery)],
                              debug=True)

def main():
    run_wsgi_app(app)

if __name__ == '__main__':
    main()