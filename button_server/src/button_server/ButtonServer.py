#!/usr/bin/python
# ROS specific imports
import roslib; roslib.load_manifest('button_server')
import rospy
import SimpleHTTPServer
import SocketServer
import std_msgs
import os
from string import Template

global server
server = None

class MyServer(SocketServer.TCPServer):
    allow_reuse_address = True

class MyRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        global server
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(server.page)
            self.wfile.close()
            return
        elif self.path == "/lib/jquery-1.8.2.min.js":
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.send_error(404, "requested path not available")

    def do_POST(self):
        global server
        if self.path == "/button":
            length = int(self.headers.getheader("content-length"))
            l = self.rfile.read(length).split("=")
            if l[0] != "name":
                self.send_error(404,"Invalid form field")
                return
            buttonname = l[1]
            result="<html><body> Published: <b>%s</b> </body></html>" % buttonname
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(result) 
            server.publish(buttonname)
        return



class Button:
    def __init__(self,name,text,color,style=''):
        self.name = name.lower()
        self.text = text
        self.color = color
        self.style = 'width:300px;height:100px;font:24px Arial;'+style
        if self.color!="":
            self.style=self.style+('background-color:%s;' % self.color)

    def getInput(self):
        style='style="%s"' % self.style
        return """
        <p>
            <input class="%s" type="button" value="%s" %s/> 
            <br/>
        </p>
        """ % (self.name,self.text,style)

    def getFunction(self):
        T = Template("""
        var result = $$("#result");
        $$("input.${name}").click(function () {
            // alert("Button ${name} pressed");
            $$.post("button", {name:"${name}"}, function(xml) {
                    // alert("${name}: Received '"+xml+"'");
                    result.html(xml);
                });
            setTimeout(function () {result.html("_");}, 2000);
        });
        """)
        return T.substitute(name=self.name)


class ButtonServer:
    def __init__(self):
        self.handler = MyRequestHandler
        rospy.init_node('button_server')
        self.pub = rospy.Publisher("buttons",std_msgs.msg.String)
        self.port = rospy.get_param("~port",5180)
        self.blist = []
        i=0
        while True:
            bname = rospy.get_param("~button%d"%i,"")
            btext = rospy.get_param("~button%d_text"%i,bname)
            bcolor = rospy.get_param("~button%d_color"%i,"")
            bstyle = rospy.get_param("~button%d_style"%i,"")
            if bname != "":
                self.blist.append(Button(bname,btext,bcolor,bstyle))
            else:
                break
            i = i+1
        if len(self.blist)==0:
            self.blist = [Button("test","Debug Button","lightgreen")]
        self.page = """
        <http>
          <head>
          <meta http-equiv="content-type" content="text/html; charset=windows-1250">
          <META HTTP-EQUIV="PRAGMA" CONTENT="NO-CACHE">
          <META HTTP-EQUIV="CACHE-CONTROL" CONTENT="NO-CACHE">
          <title>Button Server</title>
            <script language="javascript" type="text/javascript" src="lib/jquery-1.8.2.min.js"></script>
          </head>
          <body>
            <center>
            <h1>Button Server</h1>
            %s
            %s
            <br>
            <div id=result> _ </div>
            </center>
            <script id="source" language="javascript" type="text/javascript">
            $(document).ajaxError(function(e, xhr, settings, exception) {
                alert('error in: ' + settings.url + ' \\n'+'error:\\n' + exception + '\\nresponse:\\n' + xhr.responseText );
            });
            %s 
            </script>
          </body>
        </http>
        """ % (self.getHeader(), "<hl/>\n".join([b.getInput() for b in self.blist]),
                "\n".join([b.getFunction() for b in self.blist]))

        self.root = roslib.packages.get_pkg_dir('button_server')
        os.chdir(self.root)
        self.httpd = MyServer(("", self.port), self.handler)

    def getHeader(self):
        # To be overloaded
        return ""

    def publish(self,text):
        msg = std_msgs.msg.String()
        msg.data = text
        self.pub.publish(msg)

    def run(self):
        rospy.loginfo("serving '%s' at port %d" % (self.root,self.port))
        while not rospy.is_shutdown():
            try:
                self.httpd.handle_request()
            except:
                pass
