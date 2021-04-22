####################################################################################################
#  Author : Siddesh Nayak
#  Date   : 
#
#  Title  : This is custom SDK (Software development kit) developed to implement 
#           common SD-WAN API functionalities which can be used to develop SDWAN automation scripts
#
#  NOTE : This SDK will be continuosly updated by me with newer automation requirements
#
###################################################################################################

import requests
import json
import ast
import urllib3
import time

class SDWAN_SDK:

    """
    Creating a SD-WAN SDK for re-uasble SD-WAN API's
    """

    ### Iniit function performs authentication and populate generic headers
    #### content required for future requests


    def __init__(self, login_info, verify=False):
    
        host=login_info["host"]
        port=login_info["port"]
        uname=login_info["username"]
        password=login_info["password"]
        self.base_url=f"https://{host}:{port}"
        #print (f"host ==> {host}\nport ==> {port}\nuname ==> {uname}\npassword ==> {password}\nbase url ==> {base_url}")

        ## Disable SSL warnings
        self.verify=verify
        if not self.verify:
            requests.packages.urllib3.disable_warnings()

        ##Create TCP session and perform authentication needed fo vManage

        self.session=requests.session()
        api_path_auth="j_security_check"
        url=f"{self.base_url}/{api_path_auth}"
        auth_headers={"Content-Type": "application/x-www-form-urlencoded"}
        body={"j_username":uname,"j_password":password}
        verify=self.verify
        auth_resp=self.session.post(url,headers=auth_headers,data=body,verify=verify)
        
        #If any body is present in the response, indicates failure
        if auth_resp.text:
            auth_resp.raise_for_status()
        cookies = auth_resp.headers["Set-Cookie"]
        self.jSessionid=cookies.split(";")[0]
        #print(f"jSession Id  ==> {self.jSessionid}")
        
        self.token=self.get_token()
        #print(f"Token value\n{self.token}")

        ## Populating generic header required for future requests both get/post
        self.headers={"Accept": "application/json",
                      "Content-Type": "application/json"}

    ########################################################################################
    #
    # Generic method to performs api requests operations supported - GET/POST/PUT etc
    #   
    #
    ########################################################################################

    def generic_request(self,api_path,method="get",params=None, jsonbody=None):

        url=f"{self.base_url}/{api_path}"
        if method == "post":
            headers=header = {'Content-Type': "application/json",'X-XSRF-TOKEN': self.token}
        else:
            headers=self.headers
        resp=self.session.request(
              url=url,
              method=method,
              headers=headers,
              params=params,
              json=jsonbody,
              verify=self.verify)
        resp.raise_for_status()
        return resp

    @staticmethod
    def connect_sdwan_instance_sandbox():

        with open("login_file.txt","r") as fp:
            content=fp.read()
            ##creates dict from the file contents
            login_info=ast.literal_eval(content)
        return SDWAN_SDK(login_info)

    @staticmethod
    def api_calls_exec(api_calls,file_dir="resp_logs"):
        for api in api_calls:
            #api_name=api.__name__
            api_resp=api()
            api_name=api.__name__
            print (f"Executing {api_name} api")
            with open(f"{file_dir}/{api_name}_data.json","w") as fp:
                json.dump(api_resp.json(),fp,indent=2)

    def get_device_info_all(self,model=None):

        api="dataservice/device"
        params={"device-model":model} if model else None
        return self.generic_request(api,params=params)

    def get_controllers_info(self,model=None):

        api="dataservice/system/device/controllers"
        params={"deviceModel":model} if model else None
        return self.generic_request(api,params=params)

    def get_vEdges_info(self,model=None):

        api="dataservice/system/device/vedges"
        params={"model":model} if model else None
        return self.generic_request(api,params=params)

    def get_feature_template_all(self):

        api="dataservice/template/feature"
        return self.generic_request(api)

    def create_fd_device_template_vsmart(self):
        """
        Creates factory default device templates for vsmart device
        using factory default feature template for vsmart and aaa.

        First build the factory default template by fetching existing template
        """
        api="dataservice/template/device/feature"
        fd_vsmart_template=[]

        # Fetching all the feature templates
        all_tmplt=self.get_feature_template_all()

        for tmplt in all_tmplt.json()["data"]:
            tmplt_type=tmplt["templateType"].lower()
            if tmplt["factoryDefault"] and (tmplt_type.endswith("vsmart") or tmplt=="aaa"):
                fd_vsmart_template.append(
                    {
                        "templateId":tmplt["templateId"],
                        "templateType":tmplt["templateType"],
                    }
                )

        body={
            "templateName": "vSmart_fd_Template",
            "templateDescription": "Demo device template",
            "deviceType": "vsmart",
            "configType": "template",
            "factoryDefault": False,
            "policyId": "",
            "featureTemplateUidRange": [],
            "generalTemplates": fd_vsmart_template,
        }
        return self.generic_request(api,method="post",jsonbody=body)

    def apply_device_template(self,template_id):

        ## To fetch all vsmart devices info
        vsmarts=self.get_device_info_all(model="vsmart")
        #print(json.dumps(vsmarts.json()["data"]))
        # To built list of dict of vsmart device to attach the device template
        vsmart_device_list=[]
        for device in vsmarts.json()["data"]:
            vsmart_device_info_dict={
                "csv-status": "complete",
                "csv-deviceId": device["uuid"],
                "csv-deviceIP": device["system-ip"],
                "csv-host-name": device["host-name"],
                "/0/vpn-instance/ip/route/0.0.0.0/0/next-hop/address":"10.10.20.254",
                "//system/host-name": device["host-name"],
                "//system/system-ip": device["system-ip"],
                "//system/site-id": "101",
                "csv-templateId": template_id,
                "selected": "true"
            }
            vsmart_device_list.append(vsmart_device_info_dict)
            #print (f"printing vSmart device list\n{vsmart_device_list}")
        api="dataservice/template/device/config/attachfeature"
        body={
            "deviceTemplateList": [
                 {
                   "templateId": template_id,
                   "device": vsmart_device_list,
                   "isEdited": False,
                   "isMasterEdited": False,
                 }
            ]
        }

        resp=self.generic_request(api,method="post",jsonbody=body)
        templt_apply_id=resp.json()["id"]
        return self.device_action_status(templt_apply_id)

    def device_action_status(self,templt_apply_id, interval=20):
        """
         To get the status of
        """
        while True:
            time.sleep(interval)
            api=f"dataservice/device/action/status/{templt_apply_id}"
            check = self.generic_request(api)
            if check.json()["summary"]["status"].lower() != "in_progress":
                break
        return check

    def get_token(self):
        api="dataservice/client/token"
        headers={"Cookie":self.jSessionid}
        url=f"{self.base_url}/{api}"
        resp_get=self.session.request(url=url,
                                    method="get",
                                    headers=headers,
                                    verify=self.verify
                                    )
        resp_get.raise_for_status()
        token=resp_get.text
        return token

    def fetch_alarm_count(self):

        api="dataservice/alarms/count"
        return self.generic_request(api)

    def fetch_certificate_summary(self):

        api="dataservice/certificate/stats/summary"
        return self.generic_request(api)

    def fetch_control_status(self):

        api="dataservice/device/control/count"
        return self.generic_request(api)

    def fetch_device_tunnel_stats_real_time(self,system_ip):

        #api="dataservice/device/app-route/statistics"
        api="dataservice/device/tunnel/statistics"
        return self.generic_request(api,params={"deviceId":system_ip})

    def get_valid_query_fields_data(self):

        print ("Executing func get_valid_query")
        api="dataservice/statistics/dpi/fields/"
        return self.generic_request(api)

    def get_system_stats_queried(self,query):
        api="dataservice/statistics/system/"
        return self.generic_request(api,method="post",jsonbody=query)

    def create_generic_policy_obj(self,name,type,entries):

        api=f"dataservice/template/policy/list/{type}"
        body = {
            "name": name,
            "description": "Desc Not Required",
            "type": type,
            "entries": entries,
        }

        return self.generic_request(api,method="post",jsonbody=body)

    def create_site(self,name,type,entries):
        print ("Creating Site object")
        return self.create_generic_policy_obj(name,type,entries)

    def create_vpn(self, name, type, entries):
        print ("Creating VPN object")
        return self.create_generic_policy_obj(name, type, entries)

    def define_sla(self, name, type, entries):
        print ("Creating SLA object")
        return self.create_generic_policy_obj(name, type, entries)

    def create_topology(self,topology_name,vpnObjectId="none",region_site_list="none",description="none"):

        print (f"Creating Topology ==> Topo name: {topology_name}")

        api="dataservice/template/policy/definition/mesh"
        body = {
            "name": topology_name,
            "type": "mesh",
            "description": description,
            "definition": {"vpnList": vpnObjectId, "regions": region_site_list},
        }

        return self.generic_request(api,method="post",jsonbody=body)


    def create_approute_policy(self,approute_policy_name, description, dscp_value, sla_obj_id, primary_link_pref,
                           alternate_link_pref):
        print ("Creating new approute policy")
        body = {
            "name": approute_policy_name,
            "type": "appRoute",
            "description": description,
            "sequences": [
                {
                    "sequenceId": 1,
                    "sequenceName": "App Route",
                    "sequenceType": "appRoute",
                    "match": {"entries": [{"field": "dscp", "value": str(dscp_value)}]},
                    "actions": [
                        {
                            "type": "slaClass",
                            "parameter": [
                                {"field": "name", "ref": sla_obj_id},
                                {"field": "preferredColor", "value": primary_link_pref},
                            ],
                        },
                        {
                            "type": "backupSlaPreferredColor",
                            "parameter": alternate_link_pref,
                        },
                    ],
                }
            ],
        }

        api="dataservice/template/policy/definition/approute"
        return self.generic_request(api,method="post",jsonbody=body)

    #Return all vSmart policies.
    def get_policy_vsmart(self):
        print ("Fetching all vsmart policies")

        api="dataservice/template/policy/vsmart"
        return self.generic_request(api)

    def apply_approute_policy(self,policy_name,approute_obj_id,site_obj_id,vpn_obj_id,topo_obj_id,description="none"):

        print ("Applying approute policy to vsmart")
        body = {
            "policyDescription": description,
            "policyType": "feature",
            "policyName": policy_name,
            "policyDefinition": {
                "assembly": [
                    {
                        "definitionId": approute_obj_id,
                        "type": "appRoute",
                        "entries": [
                            {
                                "siteLists": [
                                    site_obj_id
                                ],
                                "vpnLists": [
                                    vpn_obj_id
                                ]
                            }
                        ]
                    },
                    {
                        "definitionId": topo_obj_id,
                        "type": "mesh"
                    }
                ]
            },
            "isPolicyActivated": False
        }

        api="dataservice/template/policy/vsmart"
        # Policy creation does not return anything; no assignment
        self.generic_request(api,method="post",jsonbody=body)

        policies = self.get_policy_vsmart()
        for policy in policies.json()["data"]:
            if policy["policyName"] == policy_name:
                return policy
