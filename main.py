import datetime
import os
import tornado.httpserver
import tornado.ioloop
import tornado.web

from abcradio_api import generate_playlist

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/index.html", playlist=None, start=None, end=None)

    def post(self):
        station = self.get_argument("station")
        startdate = self.get_argument("startdate")
        enddate = self.get_argument("enddate")
        start = datetime.datetime.strptime(startdate, "%Y-%m-%d %H:%M").strftime("%Y-%m-%dT%H:%M:%S")
        end = datetime.datetime.strptime(enddate, "%Y-%m-%d %H:%M").strftime("%Y-%m-%dT%H:%M:%S")
        playlist = generate_playlist(station, start, end)
        self.render("templates/index.html", playlist=playlist, start=startdate, end=enddate)

def main():
    application = tornado.web.Application([
        (r"/static/(.+)", tornado.web.StaticFileHandler, {"path": "static/"}),
        (r".*", MainHandler),
    ], debug=True)
    http_server = tornado.httpserver.HTTPServer(application)
    port = int(os.environ.get("PORT", 5000))
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
