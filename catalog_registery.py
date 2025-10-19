import cherrypy
import json
import datetime


class CatalogRegistry:
    exposed = True

    def __init__(self, filepath):
        self.filepath = filepath
        self.load_catalog()

    def load_catalog(self):
        try:
            with open(self.filepath, 'r') as f:
                self.catalog = json.load(f)
        except FileNotFoundError:
            self.catalog = {
                "projectOwner": "Group5",
                "projectName": "GasLeakDetector",
                "lastUpdate": str(datetime.datetime.now()),
                "broker": {"IP": "mqtt.eclipseprojects.io", "port": 1883},
                "admin": {"username": "admin", "password": "12345"},
                "buildings": []
            }

    def save_catalog(self):
        self.catalog["lastUpdate"] = str(datetime.datetime.now())
        with open(self.filepath, 'w') as f:
            json.dump(self.catalog, f, indent=4)

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if not uri:
            return self.catalog
        elif uri[0] == "broker":
            return self.catalog.get("broker", {})
        elif uri[0] == "buildings":
            return self.catalog["buildings"]
        elif uri[0] == "building" and len(uri) == 2:
            for b in self.catalog["buildings"]:
                if b["houseID"] == uri[1]:
                    return b
            return {"error": "Building not found"}
        elif uri[0] == "admin":
            return self.catalog.get("admin", {})
        return {"error": "Invalid GET path"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        body = cherrypy.request.json
        if uri[0] == "building":
            self.catalog["buildings"].append(body)
            self.save_catalog()
            return {"message": "Building added"}
        elif uri[0] == "device" and len(uri) == 2:
            houseID = uri[1]
            for b in self.catalog["buildings"]:
                if b["houseID"] == houseID:
                    b["devices"].append(body)
                    self.save_catalog()
                    return {"message": "Device added to building"}
            return {"error": "Building not found"}
        elif uri[0] == "admin-login":
            if body["username"] == self.catalog["admin"]["username"] and body["password"] == self.catalog["admin"]["password"]:
                return {"success": True}
            return {"success": False}
        return {"error": "Invalid POST path"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, *uri, **params):
        body = cherrypy.request.json
        if uri[0] == "device" and len(uri) == 2:
            houseID = uri[1]
            for b in self.catalog["buildings"]:
                if b["houseID"] == houseID:
                    for d in b["devices"]:
                        if d["deviceID"] == body["deviceID"]:
                            d.update(body)
                            self.save_catalog()
                            return {"message": "Device updated"}
            return {"error": "Device not found"}
        return {"error": "Invalid PUT path"}

    @cherrypy.tools.json_out()
    def DELETE(self, *uri, **params):
        if uri[0] == "device" and len(uri) == 3:
            houseID = uri[1]
            deviceID = int(uri[2])
            for b in self.catalog["buildings"]:
                if b["houseID"] == houseID:
                    before = len(b["devices"])
                    b["devices"] = [d for d in b["devices"] if d["deviceID"] != deviceID]
                    self.save_catalog()
                    return {"message": "Device removed", "count": before - len(b["devices"])}
        return {"error": "Invalid DELETE path"}

if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8080})
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')]
        }
    }
    cherrypy.quickstart(CatalogRegistry("catalog.json"), '/', conf)
