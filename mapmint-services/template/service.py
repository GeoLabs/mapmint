# -*- coding: utf-8 -*-
###############################################################################
#  Author:   Gérald Fenoy, gerald.fenoy@cartoworks.com
#  Copyright (c) 2010-2014, Cartoworks Inc. 
############################################################################### 
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
# 
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
# 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
################################################################################
import sys
from Cheetah.Template import Template
import zoo
import os
import shutil
import json
import gettext
import customize

def display(conf,inputs,outputs):
	sys.path+=[conf["main"]["templatesPath"]]
	nameSpace = {'conf': conf,'inputs': inputs, 'outputs': outputs}
	tmpName=inputs["tmpl"]["value"].split('/')
	toLoad=None
	if tmpName[0]=="load":
		tmpName[0]="public"
		print >> sys.stderr,"TMPNAME: "+str(tmpName)+str(len(tmpName)==3)
		if len(tmpName)==2:
			tmpName.remove(tmpName[0])
			inputs["tmpl"]["value"]=tmpName[0]
		else:
			if len(tmpName)==3:
				try:
					import shortInteger
					a=int(shortInteger.unShortURL(conf,tmpName[2]))
					toLoad=str(shortInteger.unShortURL(conf,tmpName[2]))
					tmpName.remove(tmpName[2])
				except Exception,e:
					print >> sys.stderr,str(e)
					tmpName.remove(tmpName[1])
					pass
			else:
				for i in range(1,len(tmpName)-1):
					tmpName.remove(tmpName[1])
				print >> sys.stderr,"TMPNAME: "+str(tmpName)
		print >> sys.stderr,"TMPNAME: "+str(tmpName)+str(len(tmpName)==3)
	if tmpName[0]=="public":
		import time
		if (conf.keys().count('senv')>0 and conf['senv'].keys().count('project')==0) or conf.keys().count('senv')==0:
			if len(tmpName)>1:
				nameSpace["project"]=tmpName[1]
			else:
				nameSpace["project"]=""
		else:
			print >> sys.stderr,conf["senv"]
			hasValue=False
			for j in range(1,len(tmpName)):
				if tmpName[1]!="":
					hasValue=True
					break
			if len(tmpName)>2 and hasValue:
				nameSpace["project"]=conf["senv"]["project"]
			else:
				if len(tmpName)>1:
					nameSpace["project"]=tmpName[1]
				else:
					nameSpace["project"]=""
		mapfile=conf["main"]["dataPath"]+"/public_maps/"+nameSpace["project"]
		lastMap=None
		try:
			os.stat(mapfile)
			if os.path.islink(mapfile):
				mapfile=os.readlink(mapfile)
			lastMap=mapfile.replace(conf["main"]["publicationPath"],"").replace("/public_maps/project_","").replace(".map","").replace("\\??\\","")
			verif=not(con.has_key("senv"))
			print >> sys.stderr,verif
			if verif:
				conf["senv"]={}
				conf["senv"]["MMID"]="MM"+str(time.time()).split(".")[0]
				conf["senv"]["loggedin"]="false"
				conf["senv"]["login"]="anonymous"
				conf["senv"]["group"]="public"
			if lastMap is not None:
				conf["senv"]["last_map"]=lastMap
			conf["senv"]["isTrial"]="true"
			if toLoad is not None:
				conf["senv"]["toLoad"]=toLoad
			conf["senv"]["project"]=nameSpace["project"]		
			if verif:
				conf["lenv"]["cookie"]="MMID="+conf["senv"]["MMID"]+"; path=/"

		except:
			if conf.keys().count('senv')>0:
				lastMap=conf['senv']['last_map']
				if toLoad is not None:
					conf["senv"]["toLoad"]=toLoad
			pass
		t=None
		try:
			tmplName=""
			for i in range(1,len(tmpName)):
				if tmplName!="":
					tmplName+="/"
				tmplName+=tmpName[i]
			t = Template(file=conf["main"]["templatesPath"]+"/preview/"+tmplName+".tmpl",searchList=nameSpace)
		except:
			if len(tmpName)>0:
				t = Template(file=conf["main"]["templatesPath"]+"/"+tmpName[0]+".tmpl",searchList=nameSpace)
			else:
				conf["lenv"]["message"]=zoo._("Error loading your template file ")+conf["main"]["templatesPath"]+"/preview/"+tmplName+".tmpl"
				return zoo.SERVICE_SUCCEEDED
			verif=not(conf.has_key("senv"))
			if verif:
				conf["senv"]={}
				conf["senv"]["MMID"]="MM"+str(time.time()).split(".")[0]
				conf["senv"]["loggedin"]="false"
				conf["senv"]["login"]="anonymous"
				conf["senv"]["group"]="public"
			if lastMap is not None:
				conf["senv"]["last_map"]=lastMap
			conf["senv"]["isTrial"]="true"
			if toLoad is not None:
				conf["senv"]["toLoad"]=toLoad
			conf["senv"]["project"]=nameSpace["project"]
			if verif:
				conf["lenv"]["cookie"]="MMID="+conf["senv"]["MMID"]+"; path=/"
		

		outputs["Result"]["value"]=t.__str__()
		if inputs["tmpl"]["value"].count('_css'):
			if conf["main"].has_key('cssCache') and conf["main"]["cssCache"]=="prod":
				import cssmin
				outputs["Result"]["value"]=cssmin.cssmin(outputs["Result"]["value"])
			outputs["Result"]["mimeType"]="text/css"
		if inputs["tmpl"]["value"].count('_js'):
			if conf["main"].has_key('jsCache') and conf["main"]["jsCache"]=="prod":
				try:
					from slimit import minify
					outputs["Result"]["value"]=minify(outputs["Result"]["value"], mangle=False, mangle_toplevel=False)
			
					if outputs["Result"]["value"][len(outputs["Result"]["value"])-1]==";":
						outputs["Result"]["value"]=outputs["Result"]["value"][:-1]
				except:
					#outputs["Result"]["value"]=str(e)
					pass
			outputs["Result"]["mimeType"]="application/json"
		if inputs["tmpl"]["value"].count('_xml'):
			outputs["Result"]["mimeType"]="text/xml"
		
		return zoo.SERVICE_SUCCEEDED
	if conf.keys().count("senv")>0 and conf["senv"].keys().count("loggedin")>0 and conf["senv"]["loggedin"]=="true" and conf["senv"].keys().count("isAdmin")>0:
		if inputs.keys().count("force")==0:
			try:
				tmpl=__import__(inputs["tmpl"]["value"].lower()+".service")
				#print >> sys.stderr,dir(tmpl)
				tmpl.service.displayHTML(conf,inputs,outputs)
				t=outputs["Result"]["value"]
			except:
				pass
			try:
				t = Template(file=conf["main"]["templatesPath"]+"/"+inputs["tmpl"]["value"]+".tmpl",searchList=nameSpace)
			except Exception,e:
				page="/error.tmpl"
				nameSpace["errorMsg"]=e
				t = Template(file=conf["main"]["templatesPath"]+page,searchList=nameSpace)
				
		else:
			t = Template(file=conf["main"]["templatesPath"]+"/"+inputs["tmpl"]["value"]+".tmpl",searchList=nameSpace)
		if conf and conf.keys().count('senv') and conf["senv"].keys().count("MMID") > 0:
			conf["lenv"]["cookie"]="MMID="+conf["senv"]["MMID"]+"; path=/"
	else:
		page="/login.tmpl"
		if inputs["tmpl"]["value"].count("_js")>0:
			page="/"+inputs["tmpl"]["value"]+".tmpl"
		t = Template(file=conf["main"]["templatesPath"]+page,searchList=nameSpace)
		if not(conf.has_key("senv")):
			import time
			conf["lenv"]["cookie"]="MMID=deleted; expires="+time.strftime("%a, %d-%b-%Y %H:%M:%S GMT",time.gmtime())+"; path=/"

	#if inputs["tmpl"]["value"]=="Distiller":
	#outputs["Result"]["value"]=t.__str__()
	try:
		#from htmlmin.minify import html_minify
		outputs["Result"]["value"]=t.__str__()
	except Exception,e:
		if conf.keys().count('senv')>0 and conf["senv"].keys().count('lastname')>0:
			page="/error.tmpl"
			nameSpace["errorMsg"]=e
			t1 = Template(file=conf["main"]["templatesPath"]+page,searchList=nameSpace)
			import time
			outputs["Result"]["value"]=t1.__str__()
		else:
			page1="/login.tmpl"
			t1 = Template(file=conf["main"]["templatesPath"]+page1,searchList=nameSpace)
			import time
			conf["lenv"]["cookie"]="MMID=deleted; expires="+time.strftime("%a, %d-%b-%Y %H:%M:%S GMT",time.gmtime())+"; path=/"
			outputs["Result"]["value"]=t1.__str__()

	if inputs["tmpl"]["value"].count('_css'):
		outputs["Result"]["mimeType"]="text/css"
		import cssmin
		outputs["Result"]["value"]=cssmin.cssmin(outputs["Result"]["value"])
	if inputs["tmpl"]["value"].count('_js'):
		if conf["main"].has_key('jsCache') and conf["main"]["jsCache"]=="prod":
			try:
				from slimit import minify
				tmp=minify(outputs["Result"]["value"], mangle=False, mangle_toplevel=False)
				outputs["Result"]["value"]=tmp
			except Exception,e:
				outputs["Result"]["value"]="/* Failed to shrink with message "+str(e)+" */\n"+outputs["Result"]["value"]
				pass
		outputs["Result"]["mimeType"]="application/json"
	if inputs["tmpl"]["value"].count('_xml'):
		outputs["Result"]["mimeType"]="text/xml"
	return zoo.SERVICE_SUCCEEDED

def docss(conf,inputs,outputs):
	import cssmin
	bcss=['body.css','layout.css','forms.css','grid.css','notification.css','paginate.css','plot.css','settings.css','toolbars.css','tooltip.css','tree.css','ui.css','upload.css','window.css','misc.css']
	ccss=['body.css','layout.css','forms.css','grid.css','icons.css','toolbars.css','progress.css','tree.css','ui.css','window.css','misc.css']
	outputs["Result"]["value"]=""
	for a in bcss:
		f = open(conf["main"]["mmPath"]+'/new-themes/themes/default/'+a, 'r')
		outputs["Result"]["value"]+=f.read()
		f.close()
	for a in ccss:
		f = open(conf["main"]["mmPath"]+'/new-themes/themes/'+inputs['color']['value']+'/'+a, 'r')
		outputs["Result"]["value"]+=f.read()
		f.close()
	if conf["main"].has_key('cssCache') and conf["main"]["cssCache"]=="prod":
		import cssmin
		outputs["Result"]["value"]=cssmin.cssmin(outputs["Result"]["value"])		
	return zoo.SERVICE_SUCCEEDED

def compress(conf,inputs,outputs):
	if inputs.has_key("filename") and inputs["filename"]["value"]!="NULL":
		filenames=inputs["filename"]["value"].split(",")
		inputs["file"]["value"]=""
			
		for i in range(0,len(filenames)):
			if inputs["type"]["value"]=="js" and inputs["filename"]["value"].count("css")==0:
				if filenames[i].count("min")==0 and filenames[i].count("ckeditor")==0 and filenames[i].count("compressed")==0:
					try:
						from slimit import minify
						inputs["file"]["value"]+=minify(open(conf["main"]["mmPath"]+"/"+inputs["type"]["value"].lower()+"/"+filenames[i]).read(), mangle=False, mangle_toplevel=True)
					except:
						try:
							from slimit import minify
							inputs["file"]["value"]+=minify(open(conf["main"]["publicationPath"]+"/"+filenames[i]).read(), mangle=False, mangle_toplevel=False)
						except Exception,e:
							try:
								inputs["file"]["value"]+="/* Failed to parse "+str(e)+"*/"+open(conf["main"]["publicationPath"]+"/"+inputs["type"]["value"].lower()+"/"+filenames[i]).read()+"/*Failed to parse*/\n"
							except:
								try:
									inputs["file"]["value"]+="/* Failed to parse */"+open(conf["main"]["mmPath"]+"/"+inputs["type"]["value"].lower()+"/"+filenames[i]).read()+"/*Failed to parse*/\n"
								except:
									pass
				else:
					try:
						inputs["file"]["value"]+=open(conf["main"]["mmPath"]+"/"+inputs["type"]["value"].lower()+"/"+filenames[i]).read()+"\n"
					except:
						try:
							inputs["file"]["value"]+=open(conf["main"]["publicationPath"]+"/"+filenames[i]).read()+"\n"
						except:
							pass

			else:
				from cssmin import cssmin
				try:
					inputs["file"]["value"]+=open(conf["main"]["mmPath"]+"/"+inputs["type"]["value"].lower()+"/"+filenames[i]).read()+"\n"
				except:
					try:
						inputs["file"]["value"]+=open(conf["main"]["publicationPath"]+"/"+filenames[i]).read()+"\n"
					except Exception,e:
						print >> sys.stderr,e
						pass
			
		
	if inputs["type"]["value"].lower()=="js" and inputs["filename"]["value"].count("css")==0:
		#from jsmin import jsmin
		
		outputs["Result"]["value"]=inputs["file"]["value"]
		outputs["Result"]["mimeType"]="application/json"
	else:
		import cssmin
		outputs["Result"]["value"]=cssmin.cssmin(inputs["file"]["value"])
		outputs["Result"]["mimeType"]="text/css"
	return zoo.SERVICE_SUCCEEDED
	
