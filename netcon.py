#!/usr/bin/env python
#  pip install psutil python-geoip python-geoip-geolite2

from geoip import geolite2
import json
import psutil
import socket
import urllib2

if __name__=='__main__':
	try:
		external_ip=json.loads(urllib2.urlopen('https://api.ipify.org?format=json').read())['ip']

		data={'external':{'addr':external_ip,'lat':None,'lng':None},'connections':[]}
		geo=geolite2.lookup(external_ip)
		if geo and geo.location and len(geo.location)==2:
			data['external']['lat']=geo.location[0]
			data['external']['lng']=geo.location[1]

		if not data['external']['lat'] or not data['external']['lng']:
			geo=json.loads(urllib2.urlopen('https://freegeoip.net/json/'+external_ip).read())
			data['external']['lat']=geo['latitude']
			data['external']['lng']=geo['longitude']

		local_ip=socket.gethostbyname(socket.gethostname())

		for con in psutil.net_connections():
			if con.family!=socket.AF_INET and con.family!=socket.AF_INET6:
				continue

			status=con.status.lower()
			ipv6=con.family==socket.AF_INET6

			laddr=con.laddr[0]
			lport=str(con.laddr[1])
			raddr='0.0.0.0'
			rport='0'

			if ipv6:
				raddr='::'

			if len(con.raddr)==2:
				raddr=con.raddr[0]
				rport=str(con.raddr[1])

			local=False
			if (raddr==local_ip) or (not ipv6 and raddr=='0.0.0.0') or (not ipv6 and raddr=='127.0.0.1') or (ipv6 and raddr=='::') or (ipv6 and raddr=='::1'):
				local=True

			if not local:
				geo=geolite2.lookup(raddr)
				if geo and geo.location and len(geo.location)==2:
					lat=geo.location[0]
					lng=geo.location[1]
					data['connections'].append({'laddr':laddr,'lport':lport,'raddr':raddr,'rport':rport,'lat':lat,'lng':lng,'status':status})

		with open('netcon.js','w') as file:
			file.write('data='+json.dumps(data)+';')

	except Exception as error:
		print('Error - '+str(error))
