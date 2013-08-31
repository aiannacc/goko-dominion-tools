import re

import tornado.web
import tornado.template

from . import builder


class KingdomHandler(tornado.web.RequestHandler):

    def post(self):
        return NotImplemented

    def get(self):
        err = False
        logurl = self.get_argument('logurl', default='')
        if(logurl):
            try:
                m = re.match('.*/(201.*/log.*txt)', logurl)
                logurl = m.group(1)
                logurl = 'http://dominionlogs.goko.com/' + logurl
            except:
                err = True
                logurl = ''

        width = self.get_argument('width', default='100')
        try:
            wint = int(width)
        except:
            wint = 100

        if logurl:
            bbcode = builder.parse_and_build_bb(logurl, wint)
            htmlcode = tornado.escape.xhtml_unescape(
                builder.parse_and_build_html(logurl, wint))
        else:
            bbcode = None
            htmlcode = None

        loader = tornado.template.Loader(".")
        self.write(loader.load("web/kingviz.html")
                         .generate(title='Kingdom Image Builder',
                                   logurl=logurl,
                                   width=width,
                                   bbcode=bbcode,
                                   htmlcode=htmlcode,
                                   err=err))
        self.finish()

    def write_error(self, status_code, **kwargs):
        import traceback
        if self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br/>" % line for line
                                  in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br/>" %
                                    (k, self.request.__dict__[k]) for
                                    k in self.request.__dict__.keys()])
            error = exc_info[1]

            self.set_header('Content-Type', 'text/html')
            self.finish("""<html>
                             <title>%s</title>
                             <body>
                                <h2>Error</h2>
                                <p>%s</p>
                                <h2>Traceback</h2>
                                <p>%s</p>
                                <h2>Request Info</h2>
                                <p>%s</p>
                             </body>
                           </html>""" % (error, error,
                                         trace_info, request_info))
