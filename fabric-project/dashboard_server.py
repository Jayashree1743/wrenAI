import http.server
import socketserver
import json
import pyodbc
import os

PORT = 8080

conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=knvsbngx4hdudhn7aj5zujzusm-o2ay44kalwoevch7kcwjplcjxi.datawarehouse.fabric.microsoft.com,1433;"
    "DATABASE=mip_lakehouse;"
    "UID=e19afae8-474c-4b24-9a5c-aa14552e1d7f;"
    "PWD=WDt8Q~qDA7GH5sfeI46BCktLd7wVg5RPEROKOaYp;"
    "Authentication=ActiveDirectoryServicePrincipal;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        c.campaign_name, 
                        SUM(f.spend_inr) as spend, 
                        SUM(f.impressions) as impressions, 
                        SUM(f.clicks) as clicks
                    FROM fact_ad_performance_daily f 
                    JOIN dim_campaign c ON f.campaign_sk = c.campaign_sk 
                    GROUP BY c.campaign_name
                    ORDER BY spend DESC
                """)
                rows = cursor.fetchall()
                data = []
                for row in rows:
                    data.append({
                        "campaign_name": row[0] or "Unknown Campaign",
                        "spend": float(row[1]) if row[1] is not None else 0.0,
                        "impressions": int(row[2]) if row[2] is not None else 0,
                        "clicks": int(row[3]) if row[3] is not None else 0
                    })
                conn.close()
                self.wfile.write(json.dumps(data).encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            # Check if requesting index.html or root
            if self.path == "/" or self.path == "":
                self.path = "/index.html"
            return super().do_GET()

# Ensure we run from the correct directory containing index.html
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Prevent address already in use error on quick restarts
socketserver.TCPServer.allow_reuse_address = True

print(f"Starting server on port {PORT}...")
with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
    print(f"Serving dashboard at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
