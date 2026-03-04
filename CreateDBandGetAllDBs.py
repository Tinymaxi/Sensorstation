
from influxdb import InfluxDBClient
client = client = InfluxDBClient(host='localhost', port=8086, username='grafana', password='grafana')
#client.create_database('SCD30Stats')
db_list = client.get_list_database()
print(db_list)

