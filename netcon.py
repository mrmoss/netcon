#!/usr/bin/env python
#  pip install psutil python-geoip python-geoip-geolite2

from geoip import geolite2
import json
import psutil
import socket
import urllib2

def geo_locate(ip):
	try:
		#Geolite2 database
		geo=geolite2.lookup(ip)
		if geo and geo.location and len(geo.location)==2 and type(geo.location[0])==float and type(geo.location[1])==float:
			return (geo.location[0],geo.location[1])

		#External service's database (fallback)
		geo=json.loads(urllib2.urlopen('https://freegeoip.net/json/'+ip).read())
		if geo and type(geo['latitude'])==float and type(geo['longitude'])==float:
			return (geo['latitude'],geo['longitude'])

		raise Exception('')

	except:
		raise Exception('Could not perform ip geolocation on ip: '+ip)

if __name__=='__main__':
	try:
		#Get our external ip
		external_ip=json.loads(urllib2.urlopen('https://api.ipify.org?format=json').read())['ip']

		#Get our geocoords
		data={'external':{'addr':external_ip,'lat':None,'lng':None},'connections':[]}
		geo=geo_locate(external_ip)
		data['external']['lat']=geo[0]
		data['external']['lng']=geo[1]

		#Get local ip address for filtering connections to ourself
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

			#Only add IPs that aren't local and that we can perform geo location on
			if not local:
				try:
					geo=geo_locate(raddr)
					data['connections'].append({'laddr':laddr,'lport':lport,'raddr':raddr,'rport':rport,
						'lat':geo[0],'lng':geo[1],'status':status})
				except Exception as error:
					print(error)

		with open('netcon.js','w') as file:
			file.write('data='+json.dumps(data)+';')

	except Exception as error:
		print('Error - '+str(error))
