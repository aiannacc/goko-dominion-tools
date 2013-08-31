@staticmethod
def write_error(handler, status_code, **kwargs):
    import traceback
    if handler.settings.get("debug") and "exc_info" in kwargs:
        exc_info = kwargs["exc_info"]
        trace_info = ''.join(["%s<br/>" % line for line in traceback.format_exception(*exc_info)])
        request_info = ''.join(["<strong>%s</strong>: %s<br/>" % (k, handler.request.__dict__[k] ) for k in handler.request.__dict__.keys()])
        error = exc_info[1]
        
        handler.set_header('Content-Type', 'text/html')
        handler.finish("""<html>
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
