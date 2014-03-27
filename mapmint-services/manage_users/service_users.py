import zoo
import manage_users
import sys
import re
import json
import authenticate.service as auth

def is_connected(conf):
	return conf.keys().count("senv")>0 and conf["senv"].keys().count("loggedin")>0 and conf["senv"]["loggedin"]=="true"

def getTableContent(conf,inputs,outputs):
	c = auth.getCon(conf)
	prefix=auth.getPrefix(conf)
	if c.dbtype!="PG":
		req="PRAGMA table_info("+inputs["table"]["value"]+")"
	else:
		import datastores.postgis.pgConnection as pg
		req=pg.getDesc(c.cur,auth.getPrefix(conf)+inputs["table"]["value"])
	res1=c.cur.execute(req)
	res=c.cur.fetchall()
	print >> sys.stderr,res
	fields=[]
	pkey=0
	pfield="id"
	vfields=None
	if inputs.has_key("cols") and inputs["cols"]["value"]!="NULL":
                vfields=inputs["cols"]["value"].split(",")
	if vfields is None:
		for i in range(0,len(res)):
			fields+=[{"name": res[i][1],"type": res[i][2],"pkey": res[i][4]}]
			if res[i][4]==1:
				pkey=i
	else:
		for j in range(0,len(vfields)):
			for i in range(0,len(res)):
				if res[i][1]==vfields[j]:
					fields+=[{"name": res[i][1],"type": res[i][2],"pkey": res[i][4]}]
				if res[i][4]==1 or res[i][3]=='PRI':
					pkey=i
					pfield=res[i][1]
	req="select count(*) from "+prefix+inputs["table"]["value"]
	res1=c.cur.execute(req)
	res=c.cur.fetchall()
	if res!=False:
                total=res[0][0]
	req="select "
	if inputs.has_key("cols") and inputs["cols"]["value"]!="NULL":
                req+=inputs["cols"]["value"]
	else:
                req+="*"
	req+=" from "+prefix+inputs["table"]["value"]
	if inputs.has_key("clause") and inputs["clause"]["value"]!="NULL":
                req+=" WHERE "+inputs["clause"]["value"]
	if inputs.has_key("sortname") and inputs["sortname"]["value"]!="NULL" and inputs["sortname"]["value"]!="undefined" and inputs["sortorder"]["value"]!="undefined":
                req+=" ORDER BY "+inputs["sortname"]["value"]+" "+inputs["sortorder"]["value"]
	if inputs.has_key("limit") and inputs["limit"]["value"]!="NULL":
		req+=" LIMIT "+inputs["limit"]["value"]
                if inputs.has_key("page") and inputs["page"]["value"]!="":
			req+=" OFFSET "+str((int(inputs["page"]["value"])-1)*int(inputs["limit"]["value"]))
			page=inputs["page"]["value"]
	else:
                page=1
                req+=" LIMIT 10"
	res1=c.cur.execute(req)
	res=c.cur.fetchall()
	resId1=c.cur.execute("SELECT "+pfield+" from "+prefix+inputs["table"]["value"])
	resId=c.cur.fetchall()
	if res!=False:
                rows=[]
                for i in range(0,len(res)):
			res0=[]
			for k in range(0,len(res[i])):
				if res[i][k] is not None and fields[k]["type"].count("char")>0:
					try:
						res0+=[res[i][k].encode("utf-8")]
					except:
						res0+=[res[i][k]]
				else:
					res0+=[str(res[i][k])]
			rows+=[{"id": resId[i][0],"cell": res0}]
		outputs["Result"]["value"]=json.dumps({"page": page, "total": total,"rows": rows})
		return zoo.SERVICE_SUCCEEDED
	else:
                print >> sys.stderr,"unable to run request"
                return zoo.SERVICE_FAILED
	

def requestGroup(conf,inputs,outputs):
	prefix=auth.getPrefix(conf)
	if inputs.has_key("id"):
		clause="id="+inputs["id"]["value"]
	if inputs["type"]["value"]=="delete":
		req="DELETE from "+prefix+"groups WHERE "+clause
		inputs["type"]["value"]="delet"
	else:
		if inputs["type"]["value"]=="update":
			if inputs.has_key("is_admin") and inputs["is_admin"]["value"]=="true":				
				req="UPDATE "+prefix+"groups set name='"+inputs["name"]["value"]+"', description='"+inputs["desc"]["value"]+"', adm=1 WHERE "+clause
			else:
				req="UPDATE "+prefix+"groups set name='"+inputs["name"]["value"]+"', description='"+inputs["desc"]["value"]+"', adm=0 WHERE "+clause
		else:
			if inputs.has_key("is_admin") and inputs["is_admin"]["value"]=="true":
				req="INSERT INTO "+prefix+"groups (name,description,adm) VALUES('"+inputs["name"]["value"]+"','"+inputs["desc"]["value"]+"',1)"
			else:
				req="INSERT INTO "+prefix+"groups (name,description,adm) VALUES('"+inputs["name"]["value"]+"','"+inputs["desc"]["value"]+"',0)"
	if inputs["type"]["value"]!="insert" and inputs.has_key("user"):
		print >> sys.stderr,inputs["user"]
	
	c = auth.getCon(conf)
	print >> sys.stderr,req
	c.cur.execute(req)
	c.conn.commit()
	c.close()
	print >> sys.stderr,dir(c)

	outputs["Result"]["value"]=zoo._("Group succcessfully "+inputs["type"]["value"]+"ed")
	return zoo.SERVICE_SUCCEEDED

def GetUsers(conf,inputs,outputs):
	if is_connected(conf):
		c = auth.getCon(conf)
		if not c.is_admin(conf["senv"]["login"]):
			conf["lenv"]["message"]= zoo._("Action not allowed")
			return 4
                if not re.match(r"(^\w+\Z)",inputs["order"]["value"]):
			conf["lenv"]["message"] = zoo._("Parameter order invalid")
			return 4
		if not re.match(r"(desc)|(asc)",inputs["sort"]["value"]):
			conf["lenv"]["message"] = zoo._("Parameter sort invalid")
			return 4
		if not re.match(r"(^\d+$)|(NULL)",inputs["offset"]["value"]):
			conf["lenv"]["message"] = zoo._("Parameter offset invalid")
			return 4
		if not re.match(r"(^\d+$)|(NULL)",inputs["number"]["value"]):
			conf["lenv"]["message"] = zoo._("Parameter number invalid")
			return 4
		if inputs["offset"]["value"] != "NULL" and inputs["number"]["value"] != "NULL":
			outputs["Result"]["value"] = json.dumps(c.get_users(inputs["order"]["value"],inputs["sort"]["value"],inputs["offset"]["value"],inputs["number"]["value"]))
		else: 
			outputs["Result"]["value"] = json.dumps(c.get_users(inputs["order"]["value"],inputs["sort"]["value"]))
		c.close()
		return 3
	else:
                conf["lenv"]["message"]=zoo._("User not authenticated")
                return 4


def GetGroups(conf,inputs,outputs):
	if is_connected(conf):
		c = auth.getCon(conf)
		if not c.is_admin(conf["senv"]["login"]):
			conf["lenv"]["message"]= zoo._("Action not permited")
			return 4
                if not re.match(r"(^\w+\Z)",inputs["order"]["value"]):
			conf["lenv"]["message"] = zoo._("Parameter order invalid")
			return 4
		if not re.match(r"(desc)|(asc)",inputs["sort"]["value"]):
			conf["lenv"]["message"] = zoo._("Parameter sort invalid")
			return 4
		if not re.match(r"(^\d+$)|(NULL)",inputs["offset"]["value"]):
			conf["lenv"]["message"] = zoo._("Parameter offset invalid")
			return 4
		if not re.match(r"(^\d+$)|(NULL)",inputs["number"]["value"]):
			conf["lenv"]["message"] = zoo._("Parameter number invalid")
			return 4
		if inputs["offset"]["value"] != "NULL" and inputs["number"]["value"] != "NULL":
			outputs["Result"]["value"] = json.dumps(c.get_groups(inputs["order"]["value"],inputs["sort"]["value"],inputs["offset"]["value"],inputs["number"]["value"]))
		else: 
			outputs["Result"]["value"] = json.dumps(c.get_groups(inputs["order"]["value"],inputs["sort"]["value"]))
		c.close()
		return 3
	else:
                conf["lenv"]["message"]=zoo._("User not authenticated")
                return 4


def GetGroupsUser(conf,inputs,outputs):
	if is_connected(conf):
		c = auth.getCon(conf)
		if not c.connect():
			conf["lenv"]["message"] = zoo._("SQL connection error")
			return 4
		if not re.match(r"(^\d+$)|(NULL)",inputs["id"]["value"]):
			conf["lenv"]["message"] = zoo._("Parameter id invalid")
			return 4
		if not re.match(r"(^\w+\Z)",inputs["order"]["value"]):
                        conf["lenv"]["message"] = zoo._("Parametre order incorrect")
                        return 4
		if not re.match(r"(desc)|(asc)",inputs["sort"]["value"]):
                        conf["lenv"]["message"] = zoo._("Parameter sort invalid")
                        return 4	
		if c.is_admin(conf["senv"]["login"]):
			if inputs["id"]["value"] == "NULL":
				outputs["Result"]["value"] = json.dumps(c.get_groups_user_by_login(conf["senv"]["login"],inputs["order"]["value"],inputs["sort"]["value"]))
			else:
				outputs["Result"]["value"] = json.dumps(c.get_groups_user_by_id(int(inputs["id"]["value"]),inputs["order"]["value"],inputs["sort"]["value"]))
		else:
			outputs["Result"]["value"] = json.dumps(c.get_groups_user_by_login(conf["senv"]["login"],inputs["order"]["value"],inputs["sort"]["value"]))
		return 3

	else:
		conf["lenv"]["message"]=zoo._("User not authenticated")
		return 4


def GetUsersGroup(conf,inputs,outputs):
	if is_connected(conf):
		c = auth.getCon(conf)
		if not re.match(r"(^\d+$)",inputs["id"]["value"]):
			conf["lenv"]["message"] = zoo._("Parametre id incorrect")
			return 4
		if c.is_admin(conf["senv"]["login"]):
			if not re.match(r"(^\w+\Z)",inputs["order"]["value"]):
				conf["lenv"]["message"] = zoo._("Parameter order invalid")
				return 4
			if not re.match(r"(desc)|(asc)",inputs["sort"]["value"]):
				conf["lenv"]["message"] = zoo._("Parameter sort incorrect")
				return 4
			outputs["Result"]["value"] = json.dumps(c.get_users_group_by_id(int(inputs["id"]["value"]),inputs["order"]["value"],inputs["sort"]["value"]))
			return 3
		else:
			conf["lenv"]["message"]= zoo._("Action not permited")
			return 4
	else:
		conf["lenv"]["message"]=zoo._("User not authenticated")
		return 4



def GetUserInfo(conf,inputs,outputs):
	if is_connected(conf):
		c = auth.getCon(conf)
		outputs["Result"]["value"] = json.dumps(c.get_user_by_login(conf["senv"]["login"]))
		return 3
	else:
		conf["lenv"]["message"]=zoo._("User not authenticated")
		return 4

def AddUser(conf,inputs,outputs):
	if is_connected(conf):
		c = auth.getCon(conf)
		prefix=auth.getPrefix(conf)
		if c.is_admin(conf["senv"]["login"]):
			try:
				user = json.loads(inputs["user"]["value"])
                	except Exception,e:
				print >> sys.stderr,inputs["user"]["value"]
                        	print >> sys.stderr,e
                        	conf["lenv"]["message"] = zoo._("invalid user parameter: ")+inputs["user"]["value"]
                        	return 4
			for (i,j) in user.items():
				if not manage_users.check_user_params(i,j):
					conf["lenv"]["message"] = 'Parametre %s incorrect'%(i)
					return 4
			if c.add_user(user):
				outputs["Result"]["value"] = inputs["user"]["value"]
				if inputs.has_key("group"):
					if inputs["group"].has_key("length"):
						for i in range(0,len(inputs["group"]["value"])):
							linkGroupToUser(c,prefix,inputs["group"]["value"],inputs["login"]["value"])
					else:
						linkGroupToUser(c,prefix,inputs["group"]["value"],user["login"])
				return 3
			else:
				conf["lenv"]["message"] = zoo._("SQL Error")
				return 4
		else:
			conf["lenv"]["message"]= zoo._("Action not permited")
			return 4
	else:
		conf["lenv"]["message"]=zoo._("User not authenticated")
                return 4

def AddGroup(conf,inputs,outputs):
	if is_connected(conf):
		c = auth.getCon(conf)
		if c.is_admin(conf["senv"]["login"]):
			for i in ['name','description']:
				if not manage_users.check_group_params(i,inputs[i]['value']):
					conf['lenv']['message'] = 'Parametre %s incorrect'%(i)
					return 4
			if c.add_group(inputs['name']['value'],inputs['description']["value"]):
				outputs["Result"]["value"] = json.dumps([inputs['name']['value'],inputs['description']['value']])
				return 3
			else:
				conf["lenv"]["message"] = 'Erreur sql'
				return 4
		else:
			conf["lenv"]["message"]= zoo._("Action not permited")
			return 4
	else:
		conf["lenv"]["message"]=zoo._("User not authenticated")
                return 4

def UpdateUser(conf,inputs,outputs):
	if is_connected(conf):
		prefix=auth.getPrefix(conf)
		c = auth.getCon(conf)
		
		try:
			user = json.loads(inputs["set"]["value"])
               	except Exception,e:
			user={}
			print >> sys.stderr,inputs["set"]["value"]
                       	print >> sys.stderr,e
                       	conf["lenv"]["message"] = zoo._("invalid set parameter :")+inputs["set"]["value"]
                       	#return 4

		if inputs['id']["value"] == "NULL":
			userl=conf["senv"]["login"]
			for (i,j) in user.items():
				if not manage_users.check_user_params(i,j):
					conf["lenv"]["message"] = 'Parametre %s incorrect'%(i)
					return 4
				if i=="login":
					userl=j
			if inputs.has_key("login"):
				userl=inputs["login"]["value"]
			if inputs.has_key("type") and inputs["type"]["value"]=="delete":
				try:
					c.cur.execute("DELETE FROM "+prefix+"user_group WHERE id_user=(select id from "+prefix+"users where login='"+userl+"')")
				except Exception,e:
					print >> sys.stderr,e
					pass
				try:
					c.cur.execute("DELETE FROM "+prefix+"users WHERE login='"+userl+"'")
				except Exception,e:
					print >> sys.stderr,e
					pass
				c.conn.commit()
				outputs["Result"]["value"] = inputs["set"]["value"]
				return 3
				
			if c.update_user_by_login(user,userl):
				outputs["Result"]["value"] = inputs["set"]["value"]
				if inputs.has_key("group"):
					print >> sys.stderr,inputs["group"]
					try:
						c.cur.execute("DELETE FROM "+prefix+"user_group where id_user=(select id from "+prefix+"users where login='"+userl+"')")
						c.con.commit()
					except:
						pass
					if inputs["group"].has_key("length"):
						for i in range(0,len(inputs["group"]["value"])):
							linkGroupToUser(c,prefix,inputs["group"]["value"][i],inputs["login"]["value"])
					else:
						linkGroupToUser(c,prefix,inputs["group"]["value"],inputs["login"]["value"])
				return 3
			else:
				conf["lenv"]["message"] = zoo._("Update failed")
				return 4
		elif re.match(r"(^\d+$)",inputs["id"]["value"]):
			if c.is_admin(conf["senv"]["login"]):
				if c.update_user_by_id(user,int(inputs["id"]["value"])):
					c.conn.commit()
					c.close()
					outputs["Result"]["value"] = inputs["set"]["value"]
					return 3
				else:
					conf["lenv"]["message"] = zoo._("Update failed")
					return 4
			else:
				conf["lenv"]["message"]= zoo._("Action not permited")
				return 4
		else:
			conf["lenv"]["message"] = zoo._("Parameter id invalid")
			return 4
	else:
		conf["lenv"]["message"]=zoo._("User not authenticated")
		return 4

def linkGroupToUser(c,prefix,gname,login):
	try:
		req="INSERT INTO "+prefix+"user_group (id_user,id_group) VALUES ((SELECT id from "+prefix+"users where login='"+login+"' limit 1),(SELECT id from "+prefix+"groups where name='"+gname+"'))"
		print >> sys.stderr,req
		c.cur.execute(req)
		c.conn.commit()
		return True
	except Exception,e:
		print >> sys.stderr,e
		conf["lenv"]["message"]=zoo._("Error occured: ")+str(e)
		return False




